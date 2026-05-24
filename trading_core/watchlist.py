"""Watchlist management helpers for trading_core."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import read_json, utc_now, write_json


WATCHLIST_SCHEMA_VERSION = "1.1"
VALID_STATUSES = {
    "watch_only",
    "research_candidate",
    "hold_monitor",
    "risk_control_review",
    "avoid_or_wait",
    "archived",
}
DEFAULT_REVIEW_PREFERENCES: dict[str, Any] = {
    "screen_top_n": 10,
    "deep_research_top_n": 5,
    "decision_horizon": "20d",
    "evidence_gate_policy": "standard",
    "data_priority": ["iFinD", "AKShare", "user_file"],
}
SETTABLE_FIELDS = {
    "name",
    "market",
    "group",
    "priority",
    "status",
    "horizon",
    "tags",
    "notes",
    "review.enabled",
    "review.include_in_daily_pipeline",
}


def default_watchlist(name: str = "default", market: str = "a_share") -> dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": WATCHLIST_SCHEMA_VERSION,
        "name": name,
        "market": market,
        "created_at": now,
        "updated_at": now,
        "review_preferences": dict(DEFAULT_REVIEW_PREFERENCES),
        "tickers": [],
        "notes": "Managed by trading_core watchlist CLI. Do not store credentials here.",
    }


def init_watchlist(path: Path, name: str = "default", market: str = "a_share", force: bool = False) -> dict[str, Any]:
    if path.exists() and not force:
        return build_watchlist_result(
            path=path,
            payload=normalize_payload(read_json(path))[0],
            action="init",
            operation_status="exists",
            warnings=["watchlist file already exists; use --force to overwrite"],
        )
    payload = default_watchlist(name=name, market=market)
    write_json(path, payload)
    return build_watchlist_result(path=path, payload=payload, action="init", operation_status="created")


def show_watchlist(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "action": "show",
            "watchlist_file": str(path),
            "message": "watchlist file does not exist; run watchlist --init first",
            "suggested_cli_commands": [
                f"python3 -m trading_core.cli watchlist --file {path} --init",
                f"python3 -m trading_core.cli watchlist --file {path} --add 300033.SZ --name 同花顺 --group 金融科技",
            ],
            "conversation_commands": default_conversation_commands(),
            "not_investment_advice": True,
        }
    payload, warnings = normalize_payload(read_json(path))
    return build_watchlist_result(path=path, payload=payload, action="show", warnings=warnings)


def upsert_watchlist_item(path: Path, item: dict[str, Any]) -> dict[str, Any]:
    payload = read_or_default(path)
    payload, warnings = normalize_payload(payload)
    ticker = normalize_ticker(item.get("ticker"))
    if not ticker:
        raise ValueError("ticker is required")

    now = utc_now()
    existing_index = find_ticker_index(payload["tickers"], ticker)
    item["ticker"] = ticker
    item = expand_flat_review_fields(compact_dict(item))
    if existing_index is None:
        new_item = normalize_item(item, payload.get("market", "a_share"), now=now)
        payload["tickers"].append(new_item)
        operation_status = "added"
    else:
        existing = dict(payload["tickers"][existing_index])
        merged = {**existing, **item, "updated_at": now}
        merged.setdefault("created_at", existing.get("created_at") or now)
        payload["tickers"][existing_index] = normalize_item(merged, payload.get("market", "a_share"), now=now)
        operation_status = "updated"

    payload["updated_at"] = now
    write_json(path, payload)
    return build_watchlist_result(
        path=path,
        payload=payload,
        action="upsert",
        operation_status=operation_status,
        focus_ticker=ticker,
        warnings=warnings,
    )


def remove_watchlist_item(path: Path, ticker: str) -> dict[str, Any]:
    payload = read_or_default(path)
    payload, warnings = normalize_payload(payload)
    normalized = normalize_ticker(ticker)
    original_count = len(payload["tickers"])
    payload["tickers"] = [item for item in payload["tickers"] if item.get("ticker") != normalized]
    operation_status = "removed" if len(payload["tickers"]) < original_count else "not_found"
    if operation_status == "removed":
        payload["updated_at"] = utc_now()
        write_json(path, payload)
    return build_watchlist_result(
        path=path,
        payload=payload,
        action="remove",
        operation_status=operation_status,
        focus_ticker=normalized,
        warnings=warnings,
    )


def update_watchlist_item(path: Path, ticker: str, updates: dict[str, Any]) -> dict[str, Any]:
    payload = read_or_default(path)
    payload, warnings = normalize_payload(payload)
    normalized = normalize_ticker(ticker)
    index = find_ticker_index(payload["tickers"], normalized)
    if index is None:
        return build_watchlist_result(
            path=path,
            payload=payload,
            action="update",
            operation_status="not_found",
            focus_ticker=normalized,
            warnings=warnings,
        )

    item = dict(payload["tickers"][index])
    apply_updates(item, updates)
    item["updated_at"] = utc_now()
    payload["tickers"][index] = normalize_item(item, payload.get("market", "a_share"), now=item["updated_at"])
    payload["updated_at"] = item["updated_at"]
    write_json(path, payload)
    return build_watchlist_result(
        path=path,
        payload=payload,
        action="update",
        operation_status="updated",
        focus_ticker=normalized,
        warnings=warnings,
    )


def expand_flat_review_fields(item: dict[str, Any]) -> dict[str, Any]:
    expanded = {key: value for key, value in item.items() if not key.startswith("review.")}
    review_updates = {key.split(".", 1)[1]: value for key, value in item.items() if key.startswith("review.")}
    if review_updates:
        review = expanded.get("review") if isinstance(expanded.get("review"), dict) else {}
        expanded["review"] = {**review, **review_updates}
    return expanded


def parse_set_pairs(pairs: list[str] | None) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"--set must use field=value syntax: {pair}")
        field, raw_value = pair.split("=", 1)
        field = field.strip()
        if field not in SETTABLE_FIELDS:
            raise ValueError(f"unsupported watchlist field: {field}")
        updates[field] = coerce_field_value(field, raw_value.strip())
    return updates


def metadata_updates_from_args(args: Any) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for field in ("name", "market", "group", "priority", "status", "horizon"):
        value = getattr(args, field, None)
        if value is not None:
            updates[field] = coerce_field_value(field, value)
    if getattr(args, "note", None) is not None:
        updates["notes"] = args.note
    if getattr(args, "tag", None):
        updates["tags"] = normalize_tags(args.tag)
    if getattr(args, "enable_review", False):
        updates["review.enabled"] = True
    if getattr(args, "disable_review", False):
        updates["review.enabled"] = False
    if getattr(args, "include_daily", False):
        updates["review.include_in_daily_pipeline"] = True
    if getattr(args, "exclude_daily", False):
        updates["review.include_in_daily_pipeline"] = False
    return updates


def read_or_default(path: Path) -> dict[str, Any]:
    if path.exists():
        payload = read_json(path)
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list):
            return {"tickers": payload}
        raise ValueError("watchlist must be a JSON array or an object with tickers")
    return default_watchlist(name=path.stem or "default")


def normalize_payload(raw: Any) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if isinstance(raw, list):
        payload = default_watchlist()
        payload["tickers"] = raw
    elif isinstance(raw, dict):
        payload = default_watchlist(name=str(raw.get("name") or "default"), market=str(raw.get("market") or "a_share"))
        payload.update(raw)
        review_preferences = dict(DEFAULT_REVIEW_PREFERENCES)
        if isinstance(raw.get("review_preferences"), dict):
            review_preferences.update(raw["review_preferences"])
        payload["review_preferences"] = review_preferences
    else:
        raise ValueError("watchlist must be a JSON array or an object with tickers")

    payload["schema_version"] = str(payload.get("schema_version") or WATCHLIST_SCHEMA_VERSION)
    payload["name"] = str(payload.get("name") or "default")
    payload["market"] = str(payload.get("market") or "a_share")
    payload.setdefault("created_at", utc_now())
    payload.setdefault("updated_at", payload["created_at"])

    raw_items = payload.get("tickers")
    if not isinstance(raw_items, list):
        raise ValueError("watchlist tickers must be a list")

    seen: set[str] = set()
    normalized_items: list[dict[str, Any]] = []
    for raw_item in raw_items:
        item = normalize_item(raw_item, payload["market"])
        ticker = item["ticker"]
        if ticker in seen:
            warnings.append(f"duplicate ticker ignored: {ticker}")
            continue
        seen.add(ticker)
        normalized_items.append(item)
        if "." not in ticker:
            warnings.append(f"ticker suffix missing or ambiguous: {ticker}")
    payload["tickers"] = sorted(normalized_items, key=lambda item: (item.get("priority", 5), item.get("ticker", "")))
    return payload, warnings


def normalize_item(raw_item: Any, default_market: str, now: str | None = None) -> dict[str, Any]:
    timestamp = now or utc_now()
    if isinstance(raw_item, str):
        item: dict[str, Any] = {"ticker": raw_item}
    elif isinstance(raw_item, dict):
        item = dict(raw_item)
    else:
        raise ValueError("watchlist item must be a ticker string or an object")

    ticker = normalize_ticker(item.get("ticker"))
    if not ticker:
        raise ValueError("watchlist item ticker is required")
    item["ticker"] = ticker
    item["market"] = str(item.get("market") or default_market or "a_share")
    item["group"] = str(item.get("group") or "default")
    item["priority"] = coerce_priority(item.get("priority", 5))
    item["status"] = normalize_status(item.get("status"))
    item["horizon"] = str(item.get("horizon") or "1-4w")
    item["tags"] = normalize_tags(item.get("tags"))
    item["notes"] = str(item.get("notes") or "")
    item.setdefault("created_at", timestamp)
    item.setdefault("updated_at", item["created_at"])
    review = item.get("review") if isinstance(item.get("review"), dict) else {}
    item["review"] = {
        "enabled": bool(review.get("enabled", True)),
        "include_in_daily_pipeline": bool(review.get("include_in_daily_pipeline", True)),
    }
    return item


def normalize_ticker(value: Any) -> str:
    if value is None:
        return ""
    ticker = str(value).strip()
    if not ticker:
        return ""
    if "." in ticker:
        code, suffix = ticker.rsplit(".", 1)
        return f"{code.strip().upper()}.{suffix.strip().upper()}"
    return ticker.upper()


def normalize_status(value: Any) -> str:
    status = str(value or "watch_only").strip()
    return status if status in VALID_STATUSES else "watch_only"


def normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_tags = value.replace("，", ",").replace("/", ",").split(",")
    elif isinstance(value, list):
        raw_tags = value
    else:
        raw_tags = [str(value)]
    return [str(tag).strip() for tag in raw_tags if str(tag).strip()]


def coerce_priority(value: Any) -> int:
    try:
        priority = int(value)
    except (TypeError, ValueError):
        priority = 5
    return max(1, min(priority, 99))


def coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "是", "启用"}


def coerce_field_value(field: str, value: Any) -> Any:
    if field == "priority":
        return coerce_priority(value)
    if field == "status":
        return normalize_status(value)
    if field == "tags":
        return normalize_tags(value)
    if field in {"review.enabled", "review.include_in_daily_pipeline"}:
        return coerce_bool(value)
    return value


def apply_updates(item: dict[str, Any], updates: dict[str, Any]) -> None:
    for field, value in updates.items():
        if field not in SETTABLE_FIELDS:
            raise ValueError(f"unsupported watchlist field: {field}")
        if field.startswith("review."):
            review = item.setdefault("review", {})
            if not isinstance(review, dict):
                review = {}
                item["review"] = review
            review[field.split(".", 1)[1]] = value
            continue
        item[field] = value


def find_ticker_index(items: list[dict[str, Any]], ticker: str) -> int | None:
    for index, item in enumerate(items):
        if item.get("ticker") == ticker:
            return index
    return None


def compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def build_watchlist_result(
    path: Path,
    payload: dict[str, Any],
    action: str,
    operation_status: str = "ok",
    focus_ticker: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    items = payload.get("tickers") if isinstance(payload.get("tickers"), list) else []
    prefs = payload.get("review_preferences") if isinstance(payload.get("review_preferences"), dict) else {}
    active_items = [
        item
        for item in items
        if item.get("status") != "archived"
        and isinstance(item.get("review"), dict)
        and item["review"].get("enabled", True)
        and item["review"].get("include_in_daily_pipeline", True)
    ]
    screen_top_n = int(prefs.get("screen_top_n", 10))
    deep_top_n = int(prefs.get("deep_research_top_n", 5))
    dynamic_screening = prefs.get("ranking_policy") == "dynamic_screening_first"
    top_watchlist = active_items[:screen_top_n]
    deep_research = [] if dynamic_screening else top_watchlist[:deep_top_n]
    deep_selection_status = "pending_daily_screening" if dynamic_screening else "static_watchlist_order"
    deep_selection_note = (
        "Top5 深研需在每日 Top10 证据排序后确定，不按人工录入顺序或静态观察池顺序产生。"
        if dynamic_screening
        else "Top5 is derived from the current static watchlist order."
    )
    group_summary = summarize_groups(items)
    qa_warnings = list(warnings or [])
    if not items:
        qa_warnings.append("watchlist has no tickers yet")

    return {
        "status": "ok" if operation_status not in {"not_found", "exists"} else "warn",
        "action": action,
        "operation_status": operation_status,
        "focus_ticker": focus_ticker,
        "watchlist_file": str(path),
        "watchlist": payload,
        "summary": {
            "name": payload.get("name"),
            "market": payload.get("market"),
            "total_count": len(items),
            "active_count": len(active_items),
            "group_count": len(group_summary),
            "screen_top_n": screen_top_n,
            "deep_research_top_n": deep_top_n,
            "decision_horizon": prefs.get("decision_horizon"),
            "evidence_gate_policy": prefs.get("evidence_gate_policy"),
            "ranking_policy": prefs.get("ranking_policy", "static_watchlist_order"),
            "top10_selection": prefs.get("top10_selection"),
            "top5_selection": prefs.get("top5_selection"),
            "manual_priority_usage": prefs.get("manual_priority_usage"),
        },
        "items": [display_item(item) for item in items],
        "group_summary": group_summary,
        "top_watchlist": [display_item(item) for item in top_watchlist],
        "deep_research_candidates": [display_item(item) for item in deep_research],
        "deep_research_selection_status": deep_selection_status,
        "deep_research_selection_note": deep_selection_note,
        "suggested_cli_commands": suggested_cli_commands(path),
        "conversation_commands": default_conversation_commands(),
        "source_log": [
            {
                "source_name": "user_watchlist_file",
                "endpoint_or_interface": "local_json",
                "path": str(path),
                "retrieved_at": utc_now(),
                "status": "ok",
            }
        ],
        "qa_status": {"status": "warn" if qa_warnings else "pass", "warnings": qa_warnings},
        "artifact_refs": {"watchlist_file": str(path)},
        "not_investment_advice": True,
    }


def display_item(item: dict[str, Any]) -> dict[str, Any]:
    review = item.get("review") if isinstance(item.get("review"), dict) else {}
    return {
        "ticker": item.get("ticker"),
        "name": item.get("name", ""),
        "market": item.get("market"),
        "group": item.get("group"),
        "priority": item.get("priority"),
        "status": item.get("status"),
        "horizon": item.get("horizon"),
        "tags": item.get("tags") or [],
        "notes": item.get("notes", ""),
        "review_enabled": bool(review.get("enabled", True)),
        "include_in_daily_pipeline": bool(review.get("include_in_daily_pipeline", True)),
        "next_action": next_action(item),
    }


def next_action(item: dict[str, Any]) -> str:
    status = item.get("status")
    if status == "research_candidate":
        return "纳入深度研究候选，证据足够后进入条件化决策"
    if status == "hold_monitor":
        return "监控持有逻辑、风险线和复盘触发条件"
    if status == "risk_control_review":
        return "优先复核风险、失效条件和事件暴露"
    if status == "avoid_or_wait":
        return "等待证据改善或移出活跃流程"
    if status == "archived":
        return "归档，不进入每日流程"
    return "进入观察池初筛，等待数据和证据排序"


def summarize_groups(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for item in items:
        group_name = str(item.get("group") or "default")
        group = groups.setdefault(group_name, {"group": group_name, "count": 0, "active_count": 0})
        group["count"] += 1
        review = item.get("review") if isinstance(item.get("review"), dict) else {}
        if item.get("status") != "archived" and review.get("enabled", True) and review.get("include_in_daily_pipeline", True):
            group["active_count"] += 1
    return sorted(groups.values(), key=lambda item: (-item["active_count"], item["group"]))


def suggested_cli_commands(path: Path) -> list[str]:
    return [
        f"python3 -m trading_core.cli watchlist --file {path}",
        f"python3 -m trading_core.cli watchlist --file {path} --add 300033.SZ --name 同花顺 --group 金融科技 --priority 1 --tag AI --tag 证券IT",
        f"python3 -m trading_core.cli watchlist --file {path} --update 300033.SZ --set status=research_candidate --set priority=1",
        f"python3 -m trading_core.cli watchlist --file {path} --remove 300033.SZ",
    ]


def default_conversation_commands() -> list[str]:
    return [
        "查看我的默认观察池",
        "把 300033.SZ 加入默认观察池，名称同花顺，分组金融科技，优先级 1，标签 AI/证券IT",
        "把 300033.SZ 的状态改为 research_candidate，并备注关注量能确认",
        "从默认观察池移除 300033.SZ",
        "跑一下默认观察池：先筛 Top10，对 Top5 深研，证据足够再进入条件化决策支持",
    ]
