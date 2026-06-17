"""Local price alert rules for A-share monitoring workflows."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .common import RESEARCH_ROOT, utc_now
from .data import IfindFirstMarketDataProvider
from .watchlist import normalize_ticker

ALERTS_PATH = RESEARCH_ROOT / "alerts" / "alerts.jsonl"
VALID_CONDITIONS = {"above", "below"}


def add_alert_rule(
    *,
    ticker: str,
    condition: str,
    level: float,
    path: Path = ALERTS_PATH,
    market: str = "a_share",
    expires: str | None = None,
    note: str = "",
) -> dict[str, Any]:
    normalized_ticker = normalize_ticker(ticker)
    normalized_condition = str(condition).strip().lower()
    if normalized_condition not in VALID_CONDITIONS:
        raise ValueError("condition must be one of: above, below")
    expires_at = expiry_from_duration(expires) if expires else None
    created_at = utc_now()
    rule = {
        "id": build_alert_id(normalized_ticker, normalized_condition, level, created_at),
        "ticker": normalized_ticker,
        "market": market,
        "condition": normalized_condition,
        "level": float(level),
        "currency": "CNY" if market == "a_share" else None,
        "status": "active",
        "created_at": created_at,
        "updated_at": created_at,
        "expires_at": expires_at,
        "triggered_at": None,
        "last_checked_at": None,
        "last_observed_price": None,
        "note": note,
        "not_investment_advice": True,
    }
    rules = read_alert_rules(path)
    rules.append(rule)
    write_alert_rules(path, rules)
    return build_alert_result("add", rules=[rule], path=path, operation_status="added")


def list_alert_rules(path: Path = ALERTS_PATH) -> dict[str, Any]:
    rules = read_alert_rules(path)
    return build_alert_result("list", rules=rules, path=path)


def check_alert_rules(
    *,
    path: Path = ALERTS_PATH,
    provider: IfindFirstMarketDataProvider | None = None,
    quotes: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    provider = provider or IfindFirstMarketDataProvider()
    rules = read_alert_rules(path)
    now = utc_now()
    source_log: list[dict[str, Any]] = []
    capability = provider.capability_matrix()
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    triggered_count = 0

    for rule in rules:
        if rule.get("status") == "triggered":
            checks.append({"id": rule.get("id"), "ticker": rule.get("ticker"), "status": "already_triggered"})
            continue
        if is_expired(rule, now):
            rule["status"] = "expired"
            rule["updated_at"] = now
            checks.append({"id": rule.get("id"), "ticker": rule.get("ticker"), "status": "expired"})
            continue

        ticker = str(rule.get("ticker") or "")
        quote_data = quotes.get(ticker) if quotes else None
        quote_status = "ok" if quote_data else "source_gap"
        quote_log: list[dict[str, Any]] = []
        quote_missing: list[str] = []
        if quote_data is None:
            response = provider.get_quote(ticker, str(rule.get("market") or "a_share"))
            quote_data = response.data if isinstance(response.data, dict) else None
            quote_status = response.status
            source_log.extend(response.source_log)
            quote_log = response.source_log
            quote_missing = response.missing_data

        price = latest_price(quote_data)
        rule["last_checked_at"] = now
        rule["last_observed_price"] = price
        if price is None:
            message = f"{ticker} quote unavailable for alert check"
            warnings.append(message)
            checks.append(
                {
                    "id": rule.get("id"),
                    "ticker": ticker,
                    "condition": rule.get("condition"),
                    "level": rule.get("level"),
                    "status": "source_gap",
                    "missing_data": quote_missing or [message],
                    "source_ref": quote_log[:1],
                }
            )
            continue

        triggered = is_triggered(str(rule.get("condition")), price, float(rule.get("level")))
        if triggered:
            rule["status"] = "triggered"
            rule["triggered_at"] = now
            rule["updated_at"] = now
            triggered_count += 1
        checks.append(
            {
                "id": rule.get("id"),
                "ticker": ticker,
                "condition": rule.get("condition"),
                "level": rule.get("level"),
                "latest_price": price,
                "status": "triggered" if triggered else quote_status,
                "triggered": triggered,
                "is_trade_instruction": False,
            }
        )

    write_alert_rules(path, rules)
    result = build_alert_result("check", rules=rules, path=path, operation_status="checked")
    result["alert_check_result"] = {
        "checked_at": now,
        "checked_count": len(checks),
        "triggered_count": triggered_count,
        "checks": checks,
        "warnings": warnings,
    }
    result["source_log"] = source_log or [
        {
            "source_name": "local_alert_rules",
            "source_type": "local_jsonl",
            "endpoint_or_interface": str(path),
            "parameters": {},
            "retrieved_at": now,
            "status": "ok",
        }
    ]
    result["source_capability_matrix"] = capability
    result["qa_status"] = {
        "status": "warn" if warnings else "pass",
        "warnings": warnings,
        "checks": ["not_investment_advice_included", "no_order_execution", "no_target_price_or_rating"],
    }
    return result


def read_alert_rules(path: Path = ALERTS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rules: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            rules.append(value)
    return rules


def write_alert_rules(path: Path, rules: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(rule, ensure_ascii=False, sort_keys=True) + "\n" for rule in rules)
    path.write_text(text, encoding="utf-8")


def build_alert_result(
    action: str,
    *,
    rules: list[dict[str, Any]],
    path: Path,
    operation_status: str = "ok",
) -> dict[str, Any]:
    active = [rule for rule in rules if rule.get("status") == "active"]
    triggered = [rule for rule in rules if rule.get("status") == "triggered"]
    expired = [rule for rule in rules if rule.get("status") == "expired"]
    return {
        "status": "ok",
        "action": action,
        "operation_status": operation_status,
        "alerts_file": str(path),
        "alert_rules": rules,
        "summary": {
            "total_count": len(rules),
            "active_count": len(active),
            "triggered_count": len(triggered),
            "expired_count": len(expired),
        },
        "source_log": [
            {
                "source_name": "local_alert_rules",
                "source_type": "local_jsonl",
                "endpoint_or_interface": str(path),
                "parameters": {"action": action},
                "retrieved_at": utc_now(),
                "status": "ok",
            }
        ],
        "qa_status": {"status": "pass", "checks": ["not_investment_advice_included", "no_order_execution"]},
        "artifact_refs": {"alerts_file": str(path)},
        "not_investment_advice": True,
    }


def build_alert_id(ticker: str, condition: str, level: float, created_at: str) -> str:
    digest = hashlib.sha1(f"{ticker}|{condition}|{level}|{created_at}".encode("utf-8")).hexdigest()
    return digest[:12]


def expiry_from_duration(value: str) -> str:
    text = str(value).strip().lower()
    if not text.endswith("d"):
        raise ValueError("expires must use day duration syntax, for example 90d")
    days = int(text[:-1])
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def is_expired(rule: dict[str, Any], now: str) -> bool:
    expires_at = rule.get("expires_at")
    return bool(expires_at and str(expires_at) <= now)


def latest_price(quote: dict[str, Any] | None) -> float | None:
    if not isinstance(quote, dict):
        return None
    price = quote.get("latest")
    if price is None and isinstance(quote.get("price"), dict):
        price = quote["price"].get("latest") or quote["price"].get("close")
    if isinstance(price, (int, float)):
        return float(price)
    try:
        return float(str(price).replace(",", ""))
    except (TypeError, ValueError):
        return None


def is_triggered(condition: str, latest: float, level: float) -> bool:
    if condition == "above":
        return latest >= level
    if condition == "below":
        return latest <= level
    raise ValueError("condition must be one of: above, below")
