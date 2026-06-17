"""A-share identifier search helpers for the local market workspace."""

from __future__ import annotations

from typing import Any

from .common import utc_now
from .data import IfindFirstMarketDataProvider
from .watchlist import normalize_ticker


LOCAL_A_SHARE_ALIASES: dict[str, dict[str, Any]] = {
    "同花顺": {
        "ticker": "300033.SZ",
        "name": "同花顺",
        "market": "a_share",
        "exchange": "SZ",
        "currency": "CNY",
        "identifier_status": "local_alias",
        "identifier_notes": ["Matched by local A-share alias map; refresh iFinD security master before high-risk use."],
    }
}


def search_a_share_identifier(
    query: str,
    market: str = "a_share",
    provider: IfindFirstMarketDataProvider | None = None,
) -> dict[str, Any]:
    provider = provider or IfindFirstMarketDataProvider()
    query_text = str(query or "").strip()
    capability = provider.capability_matrix()
    source_log: list[dict[str, Any]] = [
        {
            "source_name": "local_identifier_parser",
            "source_type": "deterministic_parser",
            "endpoint_or_interface": "trading_core.search.search_a_share_identifier",
            "parameters": {"query": query_text, "market": market},
            "retrieved_at": utc_now(),
            "status": "ok",
            "limitations": ["Ticker inference is deterministic; name search requires iFinD, AKShare, or local aliases."],
        }
    ]
    candidates: list[dict[str, Any]] = []
    missing_data: list[str] = []
    if not query_text:
        return {
            "status": "source_gap",
            "query": query_text,
            "market": market,
            "search_candidates": [],
            "security_master": None,
            "source_capability_matrix": capability,
            "source_log": source_log,
            "missing_data": ["query is required for A-share identifier search"],
            "qa_status": {
                "status": "warn",
                "checks": ["query_present", "source_log_included", "no_target_price_or_rating"],
                "warnings": ["query is required for A-share identifier search"],
            },
            "not_investment_advice": True,
        }

    ticker = normalize_ticker(query_text)
    if is_a_share_ticker(ticker):
        security = provider.get_security_master(ticker, market)
        source_log.extend(security.source_log)
        missing_data.extend(security.missing_data)
        candidates.append(
            {
                **(security.data or {}),
                "ticker": ticker,
                "market": market,
                "match_type": "ticker_exact",
                "confidence": "high",
            }
        )
    elif query_text in LOCAL_A_SHARE_ALIASES:
        candidate = dict(LOCAL_A_SHARE_ALIASES[query_text])
        candidate["match_type"] = "local_alias_exact"
        candidate["confidence"] = "medium"
        candidates.append(candidate)
        source_log.append(
            {
                "source_name": "local_a_share_alias_map",
                "source_type": "curated_workspace_reference",
                "endpoint_or_interface": "LOCAL_A_SHARE_ALIASES",
                "parameters": {"query": query_text},
                "retrieved_at": utc_now(),
                "status": "partial",
                "limitations": ["Small curated alias map; not a complete security master."],
            }
        )
    else:
        ak_candidates, ak_log, ak_missing = search_akshare_name(query_text, market)
        source_log.extend(ak_log)
        missing_data.extend(ak_missing)
        candidates.extend(ak_candidates)

    security_master = candidates[0] if len(candidates) == 1 else None
    status = "ok" if candidates else "source_gap"
    if not candidates:
        missing_data.append("No security candidate was found; provide a ticker with .SH/.SZ/.BJ suffix or configure a security master source.")

    return {
        "status": status,
        "query": query_text,
        "market": market,
        "search_candidates": candidates,
        "security_master": security_master,
        "source_capability_matrix": capability,
        "source_log": source_log,
        "missing_data": missing_data,
        "qa_status": {
            "status": "pass" if candidates else "warn",
            "checks": ["a_share_suffix_checked", "source_log_included", "no_target_price_or_rating"],
            "warnings": missing_data,
        },
        "not_investment_advice": True,
    }


def search_akshare_name(query: str, market: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    if market != "a_share":
        return [], [], [f"AKShare A-share name search is not configured for market={market}."]
    log_base = {
        "source_name": "AKShare",
        "source_type": "public_data_tool",
        "endpoint_or_interface": "stock_info_a_code_name",
        "parameters": {"query": query},
        "retrieved_at": utc_now(),
    }
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return [], [{**log_base, "status": "source_gap", "limitations": ["AKShare import failed."], "error": repr(exc)}], [
            "AKShare is not importable for name search."
        ]
    try:
        df = ak.stock_info_a_code_name()
    except Exception as exc:  # noqa: BLE001
        return [], [{**log_base, "status": "source_gap", "limitations": ["AKShare security list request failed."], "error": repr(exc)}], [
            "AKShare security list request failed."
        ]

    raw_rows = df.to_dict(orient="records")
    candidates: list[dict[str, Any]] = []
    for row in raw_rows:
        code = str(row.get("code") or row.get("证券代码") or "").strip()
        name = str(row.get("name") or row.get("证券简称") or "").strip()
        if not code or not name:
            continue
        if query and query not in name and query not in code:
            continue
        ticker = normalize_ticker(code)
        if not is_a_share_ticker(ticker):
            continue
        candidates.append(
            {
                "ticker": ticker,
                "name": name,
                "market": "a_share",
                "exchange": ticker.rsplit(".", 1)[1],
                "currency": "CNY",
                "identifier_status": "akshare_candidate",
                "match_type": "akshare_name_or_code",
                "confidence": "medium",
                "identifier_notes": ["Public security list candidate; cross-check with iFinD or exchange disclosure before high-risk use."],
            }
        )
        if len(candidates) >= 10:
            break

    status = "ok" if candidates else "no_match"
    missing = [] if candidates else ["AKShare security list returned no matching A-share candidates."]
    return candidates, [{**log_base, "status": status, "candidate_count": len(candidates)}], missing


def is_a_share_ticker(ticker: str) -> bool:
    if "." not in ticker:
        return False
    code, suffix = ticker.rsplit(".", 1)
    return len(code) == 6 and code.isdigit() and suffix in {"SH", "SZ", "BJ"}
