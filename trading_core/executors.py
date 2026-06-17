"""Workflow executors used by both natural-language and legacy CLI entrypoints."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from tools.calculate_technical_analysis import build_technical_analysis
from tools.check_research_integrity import validate_record

from .alpha import alpha_bench_skeleton
from .alerts import add_alert_rule, check_alert_rules, list_alert_rules
from .backtest import BacktestRequest, VibeBacktestBridge, run_local_breakout_backtest
from .brief import build_market_brief, persist_market_brief
from .common import RESEARCH_ROOT, append_jsonl, write_json
from .data import IfindFirstMarketDataProvider
from .decision import build_decision_record
from .journal import analyze_journal
from .polymarket import PolymarketMacroSignalProvider, default_prediction_market_context
from .renderers import render_markdown
from .runtime import IntentRoute, WorkflowContext, WorkflowResult
from .search import search_a_share_identifier
from .watchlist import (
    init_watchlist,
    remove_watchlist_item,
    show_watchlist,
    update_watchlist_item,
    upsert_watchlist_item,
)
from .workflow_helpers import rebase_source_refs


def execute_workflow(route: IntentRoute, context: WorkflowContext) -> WorkflowResult:
    executors = {
        "watchlist_review": execute_watchlist_review,
        "decision_support": execute_decision_support,
        "deep_research": execute_deep_research,
        "journal_review": execute_journal_review,
        "strategy_validation": execute_strategy_validation,
        "factor_validation": execute_factor_validation,
    }
    executor = executors.get(route.executor)
    if executor is None:
        record = {"status": "planned", "not_investment_advice": True}
        return WorkflowResult(status="planned", display_kind="intent", machine_record=record)
    return executor(route, context)


def execute_watchlist_review(route: IntentRoute, context: WorkflowContext) -> WorkflowResult:
    if context.action == "search":
        record = search_a_share_identifier(str(context.query or ""), market=context.market)
        write_optional_output(context, record)
        return result_from_record(record, "search")
    if context.action == "watchlist":
        record = execute_watchlist_action(context)
        return result_from_record(record, "watchlist", exit_code=0 if record.get("status") == "ok" else 2)
    if context.action == "alerts":
        record = execute_alerts_action(context)
        return result_from_record(record, "alerts", exit_code=0 if record.get("status") == "ok" else 2)

    review_date = context.review_date or date.today().isoformat()
    record = build_market_brief(
        watchlist_path=context.watchlist,
        review_date=review_date,
        mode="decision_support" if route.workflow_id == "daily_a_share_decision_pipeline" else "research",
        alerts_path=context.alerts_file,
    )
    markdown = render_markdown("brief", record)
    if context.artifact_policy.store:
        record["artifact_refs"] = persist_market_brief(record, review_date, markdown)
    write_optional_output(context, record)
    return WorkflowResult(
        status=record.get("status", "ok"),
        display_kind="brief",
        machine_record=record,
        display_card=markdown,
        exit_code=0 if record.get("status") == "ok" else 2,
    )


def execute_watchlist_action(context: WorkflowContext) -> dict[str, Any]:
    payload = context.watchlist_payload
    path = context.watchlist
    if payload.get("init"):
        return init_watchlist(
            path,
            name=payload.get("name") or path.stem or "default",
            market=payload.get("market") or "a_share",
            force=bool(payload.get("force")),
        )
    if payload.get("add"):
        item = {"ticker": payload["add"], **dict(payload.get("metadata") or {})}
        return upsert_watchlist_item(path, item)
    if payload.get("remove"):
        return remove_watchlist_item(path, str(payload["remove"]))
    if payload.get("update"):
        updates = dict(payload.get("metadata") or {})
        if not updates:
            raise ValueError("watchlist --update requires metadata flags or --set field=value")
        return update_watchlist_item(path, str(payload["update"]), updates)
    return show_watchlist(path)


def execute_alerts_action(context: WorkflowContext) -> dict[str, Any]:
    payload = context.alert_payload
    path = context.alerts_file
    if payload.get("add"):
        if payload.get("condition") is None or payload.get("level") is None:
            raise ValueError("alerts --add requires --condition and --level")
        record = add_alert_rule(
            ticker=str(payload["add"]),
            condition=str(payload["condition"]),
            level=float(payload["level"]),
            path=path,
            market=context.market,
            expires=payload.get("expires"),
            note=str(payload.get("note") or ""),
        )
    elif payload.get("check"):
        record = check_alert_rules(path=path)
    elif payload.get("list"):
        record = list_alert_rules(path=path)
    else:
        raise ValueError("use exactly one alerts operation: --add, --check, or --list")
    write_optional_output(context, record)
    return record


def execute_decision_support(_route: IntentRoute, context: WorkflowContext) -> WorkflowResult:
    provider = IfindFirstMarketDataProvider()
    security = provider.get_security_master(str(context.ticker), context.market)
    ohlcv = provider.get_ohlcv(
        str(context.ticker),
        context.market,
        context.start,
        context.end,
        local_path=str(context.ohlcv) if context.ohlcv else None,
        adjustment_basis=context.adjustment_basis,
    )
    technical = None
    missing_data = [*security.missing_data, *ohlcv.missing_data]
    source_log = [*security.source_log, *ohlcv.source_log]
    capability = ohlcv.source_capability_matrix or security.source_capability_matrix or provider.capability_matrix()
    if ohlcv.status == "ok" and ohlcv.data:
        technical_source_index = len(security.source_log) + len(ohlcv.source_log) - 1
        technical = build_technical_analysis(
            ohlcv.data,
            ticker=str(context.ticker),
            adjustment_basis=context.adjustment_basis,
            source_ref=[f"source_log[{max(0, technical_source_index)}]"],
        )

    backtest_validation = run_local_breakout_backtest(context.backtest_ohlcv) if context.backtest_ohlcv else None
    prediction_market_context = default_prediction_market_context("Polymarket context was skipped or not requested.")
    if not context.skip_polymarket:
        poly = PolymarketMacroSignalProvider().fetch_context(
            ticker=str(context.ticker),
            market=context.market,
            security_master=security.data,
            query_terms=context.polymarket_query,
            max_markets=context.polymarket_max_markets,
            lookback_days=context.polymarket_lookback_days,
            snapshot_root=RESEARCH_ROOT / "polymarket",
        )
        rebase_source_refs(poly.context, len(source_log))
        prediction_market_context = poly.context
        source_log.extend(poly.source_log)
        capability = [*capability, *poly.source_capability_matrix]
        missing_data.extend(poly.missing_data)

    record = build_decision_record(
        ticker=str(context.ticker),
        market=context.market,
        horizon=context.horizon,
        mode=context.mode,
        technical_analysis=technical,
        source_log=source_log,
        source_capability_matrix=capability,
        security_master=security.data,
        missing_data=missing_data,
        backtest_validation=backtest_validation,
        prediction_market_context=prediction_market_context,
    )
    integrity = validate_record(record)
    record["report_integrity_status"] = integrity["report_integrity_status"]
    if context.artifact_policy.store:
        append_jsonl(RESEARCH_ROOT / "runs" / "decision_support.jsonl", record)
    write_optional_output(context, record)
    return WorkflowResult(
        status=record.get("status", "ok"),
        display_kind="decision",
        machine_record=record,
        display_card=render_markdown("decision", record),
        exit_code=0 if integrity["status"] == "pass" else 2,
    )


def execute_deep_research(route: IntentRoute, context: WorkflowContext) -> WorkflowResult:
    record = {
        "status": "planned",
        "ticker": context.ticker,
        "analysis_mode": {"mode": "research"},
        "research_summary": "A股深研入口已识别；请补充或允许系统检索公告、财务、行业和催化剂证据后继续。",
        "missing_data": ["financials", "announcements", "peer_set", "valuation_snapshot", "catalysts"],
        "qa_status": {"status": "warn", "checks": ["no_fabricated_financial_data"]},
        "not_investment_advice": True,
    }
    return WorkflowResult(status="planned", display_kind="intent", machine_record=record)


def execute_journal_review(_route: IntentRoute, context: WorkflowContext) -> WorkflowResult:
    record = analyze_journal(Path(str(context.file)))
    if context.artifact_policy.store or context.artifact_policy.legacy_default_write:
        output_path = RESEARCH_ROOT / "journals" / f"{Path(str(context.file)).stem}.analysis.json"
        shadow_path = RESEARCH_ROOT / "shadow" / f"{Path(str(context.file)).stem}.shadow.json"
        record["artifact_paths"] = {"journal_analysis": str(output_path), "shadow_profile": str(shadow_path)}
        record["artifact_refs"] = dict(record["artifact_paths"])
        write_json(output_path, record)
        write_json(shadow_path, record["shadow_account_profile"])
    write_optional_output(context, record)
    return WorkflowResult(status="ok", display_kind="journal", machine_record=record, display_card=render_markdown("journal", record))


def execute_strategy_validation(_route: IntentRoute, context: WorkflowContext) -> WorkflowResult:
    bridge = VibeBacktestBridge()
    prepared = bridge.prepare_run(
        BacktestRequest(
            ticker=str(context.ticker),
            strategy=str(context.strategy),
            start=str(context.start),
            end=str(context.end),
            market=context.market,
            source=context.source,
        )
    )
    record: dict[str, Any] = {
        "status": "ok",
        "prepared_vibe_run": prepared,
        "backtest_validation": run_local_breakout_backtest(context.ohlcv) if context.ohlcv else None,
        "not_investment_advice": True,
    }
    if context.run_vibe:
        record["vibe_execution"] = bridge.run(prepared["run_dir"])
    if context.artifact_policy.store or context.artifact_policy.legacy_default_write:
        append_jsonl(RESEARCH_ROOT / "backtests" / "backtest_runs.jsonl", record)
    write_optional_output(context, record)
    return WorkflowResult(status="ok", display_kind="backtest", machine_record=record, display_card=render_markdown("backtest", record))


def execute_factor_validation(_route: IntentRoute, context: WorkflowContext) -> WorkflowResult:
    record = alpha_bench_skeleton(str(context.universe), str(context.zoo), str(context.period))
    write_optional_output(context, record)
    return WorkflowResult(
        status=record.get("status", "ok"),
        display_kind="alpha_bench",
        machine_record=record,
        display_card=render_markdown("alpha_bench", record),
        exit_code=0 if record.get("status") != "fail" else 2,
    )


def result_from_record(record: dict[str, Any], display_kind: str, exit_code: int | None = None) -> WorkflowResult:
    return WorkflowResult(
        status=record.get("status", "ok"),
        display_kind=display_kind,
        machine_record=record,
        display_card=render_markdown(display_kind, record),
        exit_code=exit_code if exit_code is not None else 0,
    )


def write_optional_output(context: WorkflowContext, record: dict[str, Any]) -> None:
    if context.artifact_policy.output_path:
        write_json(context.artifact_policy.output_path, record)
