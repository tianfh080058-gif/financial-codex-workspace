"""User-centered workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .executors import execute_workflow
from .registry import WorkflowRegistry
from .renderers import render_markdown
from .runtime import ArtifactPolicy, WorkflowContext, WorkflowResult


@dataclass
class RunIntentOptions:
    intent: str
    ticker: str | None = None
    file: Path | None = None
    watchlist: Path | None = None
    alerts_file: Path | None = None
    horizon: str = "20d"
    review_date: str | None = None
    market: str = "a_share"
    mode: str = "conditional_strong"
    dry_run: bool = False
    store: bool = False
    strategy: str | None = None
    start: str | None = None
    end: str | None = None
    universe: str | None = None
    zoo: str | None = None
    period: str | None = None
    ohlcv: Path | None = None
    backtest_ohlcv: Path | None = None
    adjustment_basis: str = "unknown"
    skip_polymarket: bool = False
    polymarket_query: list[str] | None = None
    polymarket_lookback_days: int = 7
    polymarket_max_markets: int = 5


def run_user_intent(options: RunIntentOptions, registry: WorkflowRegistry | None = None) -> dict[str, Any]:
    context = context_from_run_options(options)
    registry = registry or WorkflowRegistry()
    route = registry.route_intent(context)
    missing = registry.missing_inputs(route, context)
    if missing:
        result = WorkflowResult(status="needs_input", display_kind="intent", missing_inputs=missing)
        return build_envelope(context=context, route=route, result=result)
    if context.dry_run:
        result = WorkflowResult(status="planned", display_kind="intent")
        return build_envelope(context=context, route=route, result=result)
    result = execute_workflow(route, context)
    return build_envelope(context=context, route=route, result=result)


def route_user_intent(intent: str, options: RunIntentOptions | None = None) -> Any:
    context = context_from_run_options(options or RunIntentOptions(intent=intent))
    context.intent = intent
    return WorkflowRegistry().route_intent(context)


def context_from_run_options(options: RunIntentOptions) -> WorkflowContext:
    context = WorkflowContext(
        intent=options.intent,
        ticker=options.ticker,
        file=options.file,
        horizon=options.horizon,
        review_date=options.review_date,
        market=options.market,
        mode=options.mode,
        dry_run=options.dry_run,
        artifact_policy=ArtifactPolicy(store=options.store),
        strategy=options.strategy,
        start=options.start,
        end=options.end,
        universe=options.universe,
        zoo=options.zoo,
        period=options.period,
        ohlcv=options.ohlcv,
        backtest_ohlcv=options.backtest_ohlcv,
        adjustment_basis=options.adjustment_basis,
        skip_polymarket=options.skip_polymarket,
        polymarket_query=options.polymarket_query,
        polymarket_lookback_days=options.polymarket_lookback_days,
        polymarket_max_markets=options.polymarket_max_markets,
    )
    if options.watchlist is not None:
        context.watchlist = options.watchlist
    if options.alerts_file is not None:
        context.alerts_file = options.alerts_file
    return context


def build_envelope(*, context: WorkflowContext, route: Any, result: WorkflowResult) -> dict[str, Any]:
    missing = result.missing_as_dicts()
    envelope: dict[str, Any] = {
        "status": result.status,
        "user_goal": context.intent,
        "scenario_id": route.scenario_id,
        "workflow_id": route.workflow_id,
        "confidence": route.confidence,
        "missing_inputs": missing,
        "next_question": missing[0]["question"] if missing else None,
        "display_card": result.display_card,
        "machine_record": result.machine_record,
        "internal_route": {
            "selected_skills": route.recipe.get("required_skills", []),
            "execution_order": route.recipe.get("execution_order", []),
            "display_profile": route.recipe.get("display_profile"),
            "executor": route.executor,
            "matched_terms": route.matched_terms,
            "dry_run": context.dry_run,
        },
        "not_investment_advice": True,
    }
    if envelope["display_card"] is None:
        envelope["display_card"] = render_markdown(
            "intent",
            {
                **envelope,
                "user_entry": route.recipe.get("user_entry", {}),
                "display_profile": route.recipe.get("display_profile"),
            },
        )
    return envelope
