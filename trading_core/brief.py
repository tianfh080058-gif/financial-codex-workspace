"""Daily local market brief aggregation for watchlists."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .alerts import check_alert_rules
from .common import RESEARCH_ROOT, utc_now, write_json
from .data import IfindFirstMarketDataProvider
from .research_artifacts import build_market_context_layer
from .watchlist import normalize_payload, read_or_default


def build_market_brief(
    *,
    watchlist_path: Path,
    review_date: str,
    mode: str = "research",
    provider: IfindFirstMarketDataProvider | None = None,
    alerts_path: Path | None = None,
    quotes: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    provider = provider or IfindFirstMarketDataProvider()
    payload, watchlist_warnings = normalize_payload(read_or_default(watchlist_path))
    items = [
        item
        for item in payload.get("tickers", [])
        if item.get("status") != "archived"
        and isinstance(item.get("review"), dict)
        and item["review"].get("enabled", True)
        and item["review"].get("include_in_daily_pipeline", True)
    ]
    source_log: list[dict[str, Any]] = [
        {
            "source_name": "user_watchlist_file",
            "source_type": "local_json",
            "endpoint_or_interface": str(watchlist_path),
            "parameters": {"review_date": review_date, "mode": mode},
            "retrieved_at": utc_now(),
            "status": "ok",
        }
    ]

    rows: list[dict[str, Any]] = []
    missing_data = list(watchlist_warnings)
    for item in items:
        ticker = item["ticker"]
        quote_data = quotes.get(ticker) if quotes else None
        quote_status = "ok" if quote_data else "source_gap"
        quote_missing: list[str] = []
        if quote_data is None:
            quote = provider.get_quote(ticker, item.get("market", "a_share"))
            quote_data = quote.data if isinstance(quote.data, dict) else None
            quote_status = quote.status
            source_log.extend(quote.source_log)
            quote_missing = quote.missing_data
        latest = extract_latest(quote_data)
        if latest is None:
            missing_data.extend(quote_missing or [f"{ticker} quote unavailable for brief"])
        rows.append(
            {
                "ticker": ticker,
                "name": item.get("name", ""),
                "group": item.get("group"),
                "priority": item.get("priority"),
                "status": item.get("status"),
                "research_state": item.get("research_state"),
                "latest_price": latest,
                "quote_status": quote_status,
                "last_reviewed_at": item.get("last_reviewed_at"),
                "news_status": "source_gap",
                "next_action": "refresh_sources" if latest is None else "review_evidence",
                "missing_data": quote_missing,
            }
        )

    alert_result = check_alert_rules(path=alerts_path or (RESEARCH_ROOT / "alerts" / "alerts.jsonl"), provider=provider, quotes=quotes)
    source_log.extend(alert_result.get("source_log") or [])
    alert_checks = (alert_result.get("alert_check_result") or {}).get("checks") or []
    triggered = [check for check in alert_checks if check.get("triggered")]
    triggered_by_ticker = {str(check.get("ticker")) for check in triggered if isinstance(check, dict)}
    for row in rows:
        score, reasons = dynamic_rank_score(row, triggered_by_ticker)
        row["dynamic_rank_score"] = score
        row["dynamic_rank_reasons"] = reasons
        row["workflow_stage"] = stage_from_status(
            str(row.get("status") or "watch_only"),
            bool(row.get("latest_price") is not None),
            str(row.get("research_state") or ""),
        )
        row["next_action"] = next_action_for_row(row)
    dynamic_rows = sorted(rows, key=lambda row: (-float(row.get("dynamic_rank_score") or 0), int(row.get("priority") or 99), row.get("ticker") or ""))
    top10 = dynamic_rows[:10]
    deep_top5 = [row for row in top10 if row.get("workflow_stage") in {"research_candidate", "evidence_sufficient", "decision_support"}][:5]
    qa_warnings = list(dict.fromkeys([*missing_data, *((alert_result.get("qa_status") or {}).get("warnings") or [])]))
    brief = {
        "status": "ok",
        "analysis_mode": {"mode": mode, "allowed_values": ["research", "decision_support"]},
        "review_date": review_date,
        "watchlist_file": str(watchlist_path),
        "morning_brief": {
            "title": "Morning Brief（晨会简报）",
            "review_date": review_date,
            "market_context": build_market_context_layer(),
            "watchlist_anomalies": [
                {
                    "ticker": row.get("ticker"),
                    "reason": ", ".join(row.get("dynamic_rank_reasons") or []),
                    "dynamic_rank_score": row.get("dynamic_rank_score"),
                }
                for row in top10
            ],
            "deep_research_top5": deep_top5,
            "risk_alerts": triggered,
            "today_todos": build_today_todos(top10, deep_top5, qa_warnings),
        },
        "market_brief": {
            "summary": {
                "watchlist_name": payload.get("name"),
                "market": payload.get("market"),
                "reviewed_count": len(rows),
                "quote_available_count": len([row for row in rows if row.get("latest_price") is not None]),
                "triggered_alert_count": len(triggered),
                "news_status": "source_gap",
                "dynamic_ranking": "enabled",
                "top10_candidates": [row.get("ticker") for row in top10],
                "deep_research_top5": [row.get("ticker") for row in deep_top5],
            },
            "rows": dynamic_rows,
            "triggered_alerts": triggered,
            "dynamic_top10": top10,
            "deep_research_top5": deep_top5,
            "source_refresh_policy": payload.get("source_refresh_policy"),
            "news_preferences": payload.get("news_preferences"),
        },
        "source_capability_matrix": provider.capability_matrix(),
        "source_log": source_log,
        "missing_data": qa_warnings,
        "qa_status": {
            "status": "warn" if qa_warnings else "pass",
            "warnings": qa_warnings,
            "checks": ["source_log_included", "not_investment_advice_included", "no_trade_instruction"],
        },
        "not_investment_advice": True,
    }
    return brief


def persist_market_brief(record: dict[str, Any], review_date: str, markdown: str | None = None) -> dict[str, str]:
    directory = RESEARCH_ROOT / "briefs" / review_date
    json_path = directory / "market_brief.json"
    refs = {"brief_json": str(json_path)}
    if markdown is not None:
        md_path = directory / "market_brief.md"
        refs["brief_markdown"] = str(md_path)
    record["artifact_refs"] = refs
    write_json(json_path, record)
    if markdown is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    return refs


def extract_latest(quote: dict[str, Any] | None) -> float | None:
    if not isinstance(quote, dict):
        return None
    value = quote.get("latest")
    if value is None and isinstance(quote.get("price"), dict):
        value = quote["price"].get("latest") or quote["price"].get("close")
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def dynamic_rank_score(row: dict[str, Any], triggered_by_ticker: set[str]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    priority = row.get("priority")
    if isinstance(priority, int):
        score += max(0, 12 - priority)
        reasons.append(f"priority={priority}")
    if row.get("latest_price") is not None:
        score += 5
        reasons.append("quote_available")
    if row.get("ticker") in triggered_by_ticker:
        score += 10
        reasons.append("alert_triggered")
    status = str(row.get("status") or "")
    status_boost = {
        "research_candidate": 8,
        "hold_monitor": 7,
        "risk_control_review": 9,
        "watch_only": 3,
        "avoid_or_wait": 1,
    }.get(status, 0)
    if status_boost:
        score += status_boost
        reasons.append(f"status={status}")
    if row.get("quote_status") != "ok":
        score -= 2
        reasons.append("quote_source_gap")
    return round(score, 2), reasons


def stage_from_status(status: str, has_quote: bool, research_state: str = "") -> str:
    if research_state in {"new", "watch_only", "research_candidate", "evidence_sufficient", "decision_support", "review_due"}:
        return research_state
    if status == "research_candidate" and has_quote:
        return "evidence_sufficient"
    if status == "hold_monitor":
        return "decision_support"
    if status == "risk_control_review":
        return "review_due"
    if status in {"avoid_or_wait", "archived"}:
        return "avoid_or_wait"
    return status or "watch_only"


def next_action_for_row(row: dict[str, Any]) -> str:
    if row.get("quote_status") != "ok":
        return "补行情/交易状态数据"
    if row.get("ticker") and "alert_triggered" in (row.get("dynamic_rank_reasons") or []):
        return "复核提醒触发、公告和风险线"
    stage = row.get("workflow_stage")
    if stage == "evidence_sufficient":
        return "补财务/公告/估值后进入深研"
    if stage == "decision_support":
        return "复核持有逻辑和风险控制"
    if stage == "review_due":
        return "优先做风险复核"
    return "纳入观察池初筛"


def build_today_todos(top10: list[dict[str, Any]], deep_top5: list[dict[str, Any]], warnings: list[str]) -> list[str]:
    todos = [
        f"复核 Top10 动态排序：{', '.join(str(row.get('ticker')) for row in top10) or 'N/A'}",
        f"对 Top5 深研候选补证据：{', '.join(str(row.get('ticker')) for row in deep_top5) or 'N/A'}",
        "补市场环境层：指数、成交额、北向/融资、行业热度、汇率/利率/外盘。",
    ]
    if warnings:
        todos.append("处理 source_gap 和 QA warnings 后再进入条件化决策支持。")
    return todos
