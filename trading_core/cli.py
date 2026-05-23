"""CLI entry point for the Vibe-Trading fusion layer."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.calculate_technical_analysis import build_technical_analysis
from tools.check_research_integrity import validate_record
from tools.review_decision_support import read_jsonl, summarize_record

from .alpha import alpha_bench_skeleton
from .backtest import BacktestRequest, VibeBacktestBridge, run_local_breakout_backtest
from .common import RESEARCH_ROOT, append_jsonl, print_json, write_json
from .data import IfindFirstMarketDataProvider
from .decision import build_decision_record
from .journal import analyze_journal
from .renderers import render_markdown
from .watchlist import (
    init_watchlist,
    metadata_updates_from_args,
    parse_set_pairs,
    remove_watchlist_item,
    show_watchlist,
    update_watchlist_item,
    upsert_watchlist_item,
)


def emit_result(kind: str, payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print_json(payload)
        return
    print(render_markdown(kind, payload), end="")


def command_decision(args: argparse.Namespace) -> int:
    provider = IfindFirstMarketDataProvider()
    start = args.start
    end = args.end
    security = provider.get_security_master(args.ticker, args.market)
    ohlcv = provider.get_ohlcv(
        args.ticker,
        args.market,
        start,
        end,
        local_path=args.ohlcv,
        adjustment_basis=args.adjustment_basis,
    )
    technical = None
    missing_data = [*security.missing_data, *ohlcv.missing_data]
    source_log = [*security.source_log, *ohlcv.source_log]
    capability = ohlcv.source_capability_matrix or security.source_capability_matrix or provider.capability_matrix()
    if ohlcv.status == "ok" and ohlcv.data:
        technical = build_technical_analysis(
            ohlcv.data,
            ticker=args.ticker,
            adjustment_basis=args.adjustment_basis,
            source_ref=["source_log[1]"] if security.source_log else ["source_log[0]"],
        )
    backtest_validation = None
    if args.backtest_ohlcv:
        backtest_validation = run_local_breakout_backtest(Path(args.backtest_ohlcv))
    record = build_decision_record(
        ticker=args.ticker,
        market=args.market,
        horizon=args.horizon,
        mode=args.mode,
        technical_analysis=technical,
        source_log=source_log,
        source_capability_matrix=capability,
        security_master=security.data,
        missing_data=missing_data,
        backtest_validation=backtest_validation,
    )
    integrity = validate_record(record)
    record["report_integrity_status"] = integrity["report_integrity_status"]
    if args.output:
        write_json(Path(args.output), record)
    if args.store:
        append_jsonl(RESEARCH_ROOT / "runs" / "decision_support.jsonl", record)
    emit_result("decision", record, args.format)
    return 0 if integrity["status"] == "pass" else 2


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

    if args.init:
        result = init_watchlist(path, name=args.name or path.stem or "default", market=args.market or "a_share", force=args.force)
    elif args.add:
        item = {"ticker": args.add, **metadata_updates_from_args(args)}
        result = upsert_watchlist_item(path, item)
    elif args.remove:
        result = remove_watchlist_item(path, args.remove)
    elif args.update:
        updates = {**metadata_updates_from_args(args), **parse_set_pairs(args.set)}
        if not updates:
            raise ValueError("watchlist --update requires metadata flags or --set field=value")
        result = update_watchlist_item(path, args.update, updates)
    else:
        result = show_watchlist(path)
    emit_result("watchlist", result, args.format)
    return 0 if result.get("status") == "ok" else 2


def command_backtest(args: argparse.Namespace) -> int:
    bridge = VibeBacktestBridge()
    prepared = bridge.prepare_run(
        BacktestRequest(
            ticker=args.ticker,
            strategy=args.strategy,
            start=args.start,
            end=args.end,
            market=args.market,
            source=args.source,
        )
    )
    result: dict[str, Any] = {
        "status": "ok",
        "prepared_vibe_run": prepared,
        "backtest_validation": None,
        "not_investment_advice": True,
    }
    if args.ohlcv:
        result["backtest_validation"] = run_local_breakout_backtest(Path(args.ohlcv))
    if args.run_vibe:
        result["vibe_execution"] = bridge.run(prepared["run_dir"])
    if args.output:
        write_json(Path(args.output), result)
    append_jsonl(RESEARCH_ROOT / "backtests" / "backtest_runs.jsonl", result)
    emit_result("backtest", result, args.format)
    return 0


def command_alpha_bench(args: argparse.Namespace) -> int:
    result = alpha_bench_skeleton(args.universe, args.zoo, args.period)
    if args.output:
        write_json(Path(args.output), result)
    emit_result("alpha_bench", result, args.format)
    return 0 if result.get("status") != "fail" else 2


def command_journal(args: argparse.Namespace) -> int:
    result = analyze_journal(Path(args.file))
    output_path = RESEARCH_ROOT / "journals" / f"{Path(args.file).stem}.analysis.json"
    shadow_path = RESEARCH_ROOT / "shadow" / f"{Path(args.file).stem}.shadow.json"
    result["artifact_paths"] = {"journal_analysis": str(output_path), "shadow_profile": str(shadow_path)}
    result["artifact_refs"] = dict(result["artifact_paths"])
    write_json(output_path, result)
    write_json(shadow_path, result["shadow_account_profile"])
    emit_result("journal", result, args.format)
    return 0


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Financial workspace trading decision support CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

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
