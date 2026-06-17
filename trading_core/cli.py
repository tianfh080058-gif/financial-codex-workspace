"""CLI entry point for the Vibe-Trading fusion layer."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.review_decision_support import read_jsonl, summarize_record

from .common import RESEARCH_ROOT, print_json, write_json
from .executors import execute_workflow
from .orchestrator import RunIntentOptions, run_user_intent
from .registry import WorkflowRegistry
from .renderers import render_markdown
from .runtime import ArtifactPolicy, WorkflowContext, WorkflowResult
from .watchlist import metadata_updates_from_args, parse_set_pairs


def emit_result(kind: str, payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print_json(payload)
        return
    print(render_markdown(kind, payload), end="")


def emit_workflow_result(result: WorkflowResult, output_format: str) -> None:
    record = result.machine_record or {}
    if output_format == "json":
        print_json(record)
        return
    print(result.display_card or render_markdown(result.display_kind, record), end="")


def run_fixed_workflow(workflow_id: str, context: WorkflowContext) -> WorkflowResult:
    route = WorkflowRegistry().route_intent(context, workflow_id=workflow_id)
    return execute_workflow(route, context)


def command_decision(args: argparse.Namespace) -> int:
    result = run_fixed_workflow(
        "a_share_decision_support",
        WorkflowContext(
            command="decision",
            intent=f"decision {args.ticker}",
            ticker=args.ticker,
            market=args.market,
            horizon=args.horizon,
            mode=args.mode,
            start=args.start,
            end=args.end,
            ohlcv=Path(args.ohlcv) if args.ohlcv else None,
            backtest_ohlcv=Path(args.backtest_ohlcv) if args.backtest_ohlcv else None,
            adjustment_basis=args.adjustment_basis,
            skip_polymarket=args.skip_polymarket,
            polymarket_query=args.polymarket_query,
            polymarket_lookback_days=args.polymarket_lookback_days,
            polymarket_max_markets=args.polymarket_max_markets,
            artifact_policy=ArtifactPolicy(store=args.store, output_path=Path(args.output) if args.output else None),
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_watchlist(args: argparse.Namespace) -> int:
    path = Path(args.file)
    operations = [bool(args.init), bool(args.add), bool(args.remove), bool(args.update)]
    if sum(operations) > 1:
        raise ValueError("use only one watchlist operation at a time: --init, --add, --remove, or --update")
    if args.set and not args.update:
        raise ValueError("--set can only be used with --update")
    if args.enable_review and args.disable_review:
        raise ValueError("use only one of --enable-review or --disable-review")
    if args.include_daily and args.exclude_daily:
        raise ValueError("use only one of --include-daily or --exclude-daily")
    metadata = {**metadata_updates_from_args(args), **parse_set_pairs(args.set)}
    result = run_fixed_workflow(
        "watchlist_daily_review",
        WorkflowContext(
            command="watchlist",
            action="watchlist",
            intent="watchlist",
            watchlist=path,
            watchlist_payload={
                "init": args.init,
                "force": args.force,
                "add": args.add,
                "remove": args.remove,
                "update": args.update,
                "name": args.name,
                "market": args.market,
                "metadata": metadata,
            },
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_search(args: argparse.Namespace) -> int:
    result = run_fixed_workflow(
        "watchlist_daily_review",
        WorkflowContext(
            command="search",
            action="search",
            intent=f"search {args.query}",
            query=args.query,
            market=args.market,
            artifact_policy=ArtifactPolicy(output_path=Path(args.output) if args.output else None),
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_alerts(args: argparse.Namespace) -> int:
    operations = [bool(args.add), bool(args.check), bool(args.list)]
    if sum(operations) != 1:
        raise ValueError("use exactly one alerts operation: --add, --check, or --list")
    result = run_fixed_workflow(
        "watchlist_daily_review",
        WorkflowContext(
            command="alerts",
            action="alerts",
            intent="alerts",
            alerts_file=Path(args.file),
            market=args.market,
            alert_payload={
                "add": args.add,
                "condition": args.condition,
                "level": args.level,
                "expires": args.expires,
                "note": args.note,
                "check": args.check,
                "list": args.list,
            },
            artifact_policy=ArtifactPolicy(output_path=Path(args.output) if args.output else None),
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_brief(args: argparse.Namespace) -> int:
    result = run_fixed_workflow(
        "watchlist_daily_review",
        WorkflowContext(
            command="brief",
            action="brief",
            intent="brief",
            watchlist=Path(args.watchlist),
            alerts_file=Path(args.alerts_file),
            review_date=args.date,
            mode=args.mode,
            artifact_policy=ArtifactPolicy(store=args.store, output_path=Path(args.output) if args.output else None),
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_backtest(args: argparse.Namespace) -> int:
    result = run_fixed_workflow(
        "vibe_backtest_validation",
        WorkflowContext(
            command="backtest",
            intent=f"backtest {args.ticker}",
            ticker=args.ticker,
            market=args.market,
            strategy=args.strategy,
            start=args.start,
            end=args.end,
            source=args.source,
            ohlcv=Path(args.ohlcv) if args.ohlcv else None,
            run_vibe=args.run_vibe,
            artifact_policy=ArtifactPolicy(legacy_default_write=True, output_path=Path(args.output) if args.output else None),
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_alpha_bench(args: argparse.Namespace) -> int:
    result = run_fixed_workflow(
        "alpha_factor_bench",
        WorkflowContext(
            command="alpha-bench",
            intent=f"alpha {args.universe} {args.zoo}",
            universe=args.universe,
            zoo=args.zoo,
            period=args.period,
            artifact_policy=ArtifactPolicy(output_path=Path(args.output) if args.output else None),
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_journal(args: argparse.Namespace) -> int:
    result = run_fixed_workflow(
        "trade_journal_shadow_review",
        WorkflowContext(
            command="journal",
            intent=f"journal {args.file}",
            file=Path(args.file),
            artifact_policy=ArtifactPolicy(legacy_default_write=True),
        ),
    )
    emit_workflow_result(result, args.format)
    return result.exit_code


def command_review(args: argparse.Namespace) -> int:
    records = read_jsonl(Path(args.path))
    reviews = [summarize_record(record, args.horizon) for record in records if record.get("analysis_mode", {}).get("mode") == "decision_support"]
    result = {
        "status": "ok",
        "path": args.path,
        "horizon": args.horizon,
        "record_count": len(reviews),
        "reviews": reviews[-args.limit :] if args.limit >= 0 else reviews,
        "not_investment_advice": True,
    }
    emit_result("review", result, args.format)
    return 0


def command_check_ifind(args: argparse.Namespace) -> int:
    script = Path(".agents/skills/ifind-http-api/scripts/ifind_http_api.py")
    proc = subprocess.run([sys.executable, str(script), "check-env"], capture_output=True, text=True, check=False)
    print(proc.stdout, end="")
    return proc.returncode


def command_run(args: argparse.Namespace) -> int:
    result = run_user_intent(
        RunIntentOptions(
            intent=args.intent,
            ticker=args.ticker,
            file=Path(args.file) if args.file else None,
            watchlist=Path(args.watchlist),
            alerts_file=Path(args.alerts_file),
            horizon=args.horizon,
            review_date=args.date,
            market=args.market,
            mode=args.mode,
            dry_run=args.dry_run,
            store=args.store,
            strategy=args.strategy,
            start=args.start,
            end=args.end,
            universe=args.universe,
            zoo=args.zoo,
            period=args.period,
            ohlcv=Path(args.ohlcv) if args.ohlcv else None,
            backtest_ohlcv=Path(args.backtest_ohlcv) if args.backtest_ohlcv else None,
            adjustment_basis=args.adjustment_basis,
            skip_polymarket=args.skip_polymarket,
            polymarket_query=args.polymarket_query,
            polymarket_lookback_days=args.polymarket_lookback_days,
            polymarket_max_markets=args.polymarket_max_markets,
        )
    )
    if args.output:
        write_json(Path(args.output), result)
    if args.format == "json":
        print_json(result)
    else:
        print(result.get("display_card", ""), end="")
    return 1 if result.get("status") in {"fail", "error"} else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Financial workspace trading decision support CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Route a natural-language user goal to the right workflow")
    run.add_argument("--intent", required=True, help="Natural-language user goal, for example 帮我看今天观察池")
    run.add_argument("--dry-run", action="store_true", help="Return only the routed execution plan")
    run.add_argument("--ticker", help="Ticker for single-stock decision, research, or backtest workflows")
    run.add_argument("--file", help="Input file for journal review workflows")
    run.add_argument("--watchlist", default=str(RESEARCH_ROOT / "watchlists" / "default.json"))
    run.add_argument("--alerts-file", default=str(RESEARCH_ROOT / "alerts" / "alerts.jsonl"))
    run.add_argument("--horizon", default="20d")
    run.add_argument("--date", help="Review date in YYYY-MM-DD")
    run.add_argument("--market", default="a_share")
    run.add_argument("--mode", default="conditional_strong")
    run.add_argument("--store", action="store_true", help="Persist workflow artifacts when supported")
    run.add_argument("--strategy", help="Backtest strategy, for example technical_breakout")
    run.add_argument("--start", help="Backtest start date")
    run.add_argument("--end", help="Backtest end date")
    run.add_argument("--universe", help="Alpha bench universe, for example csi300")
    run.add_argument("--zoo", help="Alpha Zoo name, for example gtja191")
    run.add_argument("--period", help="Alpha bench period, for example 2021-2026")
    run.add_argument("--ohlcv", help="Optional local OHLCV JSON/CSV file")
    run.add_argument("--backtest-ohlcv", help="Optional OHLCV file for decision validation")
    run.add_argument("--adjustment-basis", default="unknown", choices=["unadjusted", "qfq", "hfq", "unknown"])
    run.add_argument("--skip-polymarket", action="store_true", help="Skip Polymarket macro/event evidence retrieval")
    run.add_argument("--polymarket-query", action="append", help="Additional Polymarket macro or strongly linked query term")
    run.add_argument("--polymarket-lookback-days", type=int, default=7)
    run.add_argument("--polymarket-max-markets", type=int, default=5)
    run.add_argument("--output")
    run.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    run.set_defaults(func=command_run)

    decision = subparsers.add_parser("decision", help="Build decision_card and conditional_trade_plan")
    decision.add_argument("--ticker", required=True)
    decision.add_argument("--market", default="a_share")
    decision.add_argument("--horizon", default="20d")
    decision.add_argument("--mode", default="conditional_strong")
    decision.add_argument("--start")
    decision.add_argument("--end")
    decision.add_argument("--ohlcv", help="Optional local OHLCV JSON/CSV file")
    decision.add_argument("--backtest-ohlcv", help="Optional OHLCV file for lightweight local validation")
    decision.add_argument("--adjustment-basis", default="unknown", choices=["unadjusted", "qfq", "hfq", "unknown"])
    decision.add_argument("--skip-polymarket", action="store_true", help="Skip Polymarket macro/event evidence retrieval")
    decision.add_argument("--polymarket-query", action="append", help="Additional Polymarket macro or strongly linked query term")
    decision.add_argument("--polymarket-lookback-days", type=int, default=7, help="Local snapshot change window label for Polymarket context")
    decision.add_argument("--polymarket-max-markets", type=int, default=5, help="Maximum related Polymarket markets to keep")
    decision.add_argument("--output")
    decision.add_argument("--store", action="store_true")
    decision.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    decision.set_defaults(func=command_decision)

    watchlist = subparsers.add_parser("watchlist", help="Create, edit, and show local watchlists")
    watchlist.add_argument("--file", default=str(RESEARCH_ROOT / "watchlists" / "default.json"))
    watchlist.add_argument("--init", action="store_true", help="Create a watchlist template")
    watchlist.add_argument("--force", action="store_true", help="Overwrite an existing file when used with --init")
    watchlist.add_argument("--add", metavar="TICKER", help="Add or update one ticker")
    watchlist.add_argument("--remove", metavar="TICKER", help="Remove one ticker")
    watchlist.add_argument("--update", metavar="TICKER", help="Update metadata for one ticker")
    watchlist.add_argument("--set", action="append", help="Set a field on --update, for example status=research_candidate")
    watchlist.add_argument("--name", help="Watchlist name for --init or security name for --add/--update")
    watchlist.add_argument("--market", help="Market, for example a_share")
    watchlist.add_argument("--group", help="Watchlist group or theme")
    watchlist.add_argument("--priority", type=int, help="Lower numbers rank earlier in daily review")
    watchlist.add_argument("--status", choices=["watch_only", "research_candidate", "hold_monitor", "risk_control_review", "avoid_or_wait", "archived"])
    watchlist.add_argument("--horizon", help="Review horizon, for example 1-4w or 20d")
    watchlist.add_argument("--tag", action="append", help="Repeatable tag")
    watchlist.add_argument("--note", help="Free-form local note; do not store credentials")
    watchlist.add_argument("--enable-review", action="store_true")
    watchlist.add_argument("--disable-review", action="store_true")
    watchlist.add_argument("--include-daily", action="store_true")
    watchlist.add_argument("--exclude-daily", action="store_true")
    watchlist.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    watchlist.set_defaults(func=command_watchlist)

    search = subparsers.add_parser("search", help="Search or normalize an A-share ticker/name")
    search.add_argument("--query", required=True)
    search.add_argument("--market", default="a_share")
    search.add_argument("--output")
    search.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    search.set_defaults(func=command_search)

    alerts = subparsers.add_parser("alerts", help="Create, list, or check local price alerts")
    alerts.add_argument("--file", default=str(RESEARCH_ROOT / "alerts" / "alerts.jsonl"))
    alerts.add_argument("--add", metavar="TICKER", help="Add one alert rule")
    alerts.add_argument("--condition", choices=["above", "below"])
    alerts.add_argument("--level", type=float)
    alerts.add_argument("--expires", help="Day duration, for example 90d")
    alerts.add_argument("--market", default="a_share")
    alerts.add_argument("--note", help="Free-form local note; do not store credentials")
    alerts.add_argument("--check", action="store_true", help="Check all active rules against available quotes")
    alerts.add_argument("--list", action="store_true", help="List rules")
    alerts.add_argument("--output")
    alerts.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    alerts.set_defaults(func=command_alerts)

    brief = subparsers.add_parser("brief", help="Build a daily watchlist market brief")
    brief.add_argument("--watchlist", default=str(RESEARCH_ROOT / "watchlists" / "default.json"))
    brief.add_argument("--alerts-file", default=str(RESEARCH_ROOT / "alerts" / "alerts.jsonl"))
    brief.add_argument("--date", help="Review date in YYYY-MM-DD; defaults to today")
    brief.add_argument("--mode", default="research", choices=["research", "decision_support"])
    brief.add_argument("--store", action="store_true", help="Persist JSON and Markdown artifacts under .research/briefs")
    brief.add_argument("--output")
    brief.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    brief.set_defaults(func=command_brief)

    backtest = subparsers.add_parser("backtest", help="Prepare a Vibe run_dir and optional local validation")
    backtest.add_argument("--ticker", required=True)
    backtest.add_argument("--market", default="a_share")
    backtest.add_argument("--strategy", required=True)
    backtest.add_argument("--start", required=True)
    backtest.add_argument("--end", required=True)
    backtest.add_argument("--source", default="auto", choices=["tushare", "okx", "yfinance", "akshare", "ccxt", "auto"])
    backtest.add_argument("--ohlcv", help="Optional local OHLCV JSON/CSV for lightweight validation")
    backtest.add_argument("--run-vibe", action="store_true", help="Actually invoke vendor/vibe-trading backtest runner")
    backtest.add_argument("--output")
    backtest.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    backtest.set_defaults(func=command_backtest)

    alpha = subparsers.add_parser("alpha-bench", help="Build Alpha Zoo bench request envelope")
    alpha.add_argument("--universe", required=True)
    alpha.add_argument("--zoo", required=True)
    alpha.add_argument("--period", required=True)
    alpha.add_argument("--output")
    alpha.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    alpha.set_defaults(func=command_alpha_bench)

    journal = subparsers.add_parser("journal", help="Analyze broker trade journal and extract shadow profile")
    journal.add_argument("--file", required=True)
    journal.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    journal.set_defaults(func=command_journal)

    review = subparsers.add_parser("review", help="Review stored decision_support JSONL records")
    review.add_argument("--path", required=True)
    review.add_argument("--horizon", type=int, default=20, choices=[5, 20, 60])
    review.add_argument("--limit", type=int, default=50)
    review.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Terminal output format")
    review.set_defaults(func=command_review)

    check_ifind = subparsers.add_parser("check-ifind", help="Run token-safe iFinD environment check")
    check_ifind.set_defaults(func=command_check_ifind)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - CLI should return structured diagnostics.
        print_json({"status": "fail", "error_type": type(exc).__name__, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
