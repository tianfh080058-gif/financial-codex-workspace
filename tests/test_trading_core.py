from __future__ import annotations

import csv
import json
import math
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from io import StringIO
from pathlib import Path

from tools.calculate_technical_analysis import build_technical_analysis
from tools.check_research_integrity import validate_record
from trading_core.cli import main as cli_main
from trading_core.alerts import add_alert_rule, check_alert_rules
from trading_core.alpha import alpha_bench_skeleton
from trading_core.backtest import run_local_breakout_backtest
from trading_core.brief import build_market_brief
from trading_core.data import DataResponse
from trading_core.decision import build_decision_record
from trading_core.execution_rules import build_a_share_execution_check
from trading_core.journal import analyze_journal
from trading_core.orchestrator import RunIntentOptions, route_user_intent, run_user_intent
from trading_core.polymarket import PolymarketMacroSignalProvider
from trading_core.registry import WORKFLOW_EXECUTORS, WorkflowRegistry
from trading_core.renderers import render_markdown
from trading_core.runtime import WorkflowContext
from trading_core.search import search_a_share_identifier
from trading_core.watchlist import (
    init_watchlist,
    remove_watchlist_item,
    show_watchlist,
    update_watchlist_item,
    upsert_watchlist_item,
)


class FakeProvider:
    def __init__(self, quotes: dict[str, dict[str, object]] | None = None) -> None:
        self.quotes = quotes or {}

    def capability_matrix(self) -> list[dict[str, object]]:
        return [
            {
                "source_name": "unit_test_provider",
                "priority": 1,
                "status": "available",
            }
        ]

    def get_security_master(self, ticker: str, market: str) -> DataResponse:
        return DataResponse(
            status="partial",
            data={
                "ticker": ticker,
                "market": market,
                "exchange": ticker.rsplit(".", 1)[1] if "." in ticker else None,
                "currency": "CNY",
                "identifier_status": "unit_test",
            },
            source_log=[
                {
                    "source_name": "unit_test_provider",
                    "endpoint_or_interface": "get_security_master",
                    "parameters": {"ticker": ticker, "market": market},
                    "retrieved_at": "2026-06-17T00:00:00Z",
                    "status": "partial",
                }
            ],
            source_capability_matrix=self.capability_matrix(),
            missing_data=["unit test security master is partial"],
        )

    def get_quote(self, ticker: str, market: str) -> DataResponse:
        quote = self.quotes.get(ticker)
        if quote is None:
            return DataResponse(
                status="source_gap",
                data=None,
                source_log=[
                    {
                        "source_name": "unit_test_provider",
                        "endpoint_or_interface": "get_quote",
                        "parameters": {"ticker": ticker, "market": market},
                        "retrieved_at": "2026-06-17T00:00:00Z",
                        "status": "source_gap",
                    }
                ],
                source_capability_matrix=self.capability_matrix(),
                missing_data=[f"{ticker} quote missing"],
            )
        return DataResponse(
            status="ok",
            data=quote,
            source_log=[
                {
                    "source_name": "unit_test_provider",
                    "endpoint_or_interface": "get_quote",
                    "parameters": {"ticker": ticker, "market": market},
                    "retrieved_at": "2026-06-17T00:00:00Z",
                    "trade_date": quote.get("trade_date"),
                    "status": "ok",
                }
            ],
            source_capability_matrix=self.capability_matrix(),
        )


def sample_rows(count: int = 90) -> list[dict[str, float | str]]:
    start = date(2026, 1, 1)
    rows: list[dict[str, float | str]] = []
    for index in range(count):
        close = 20 + index * 0.08 + math.sin(index / 5) * 0.2
        rows.append(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": round(close - 0.05, 4),
                "high": round(close + 0.2, 4),
                "low": round(close - 0.2, 4),
                "close": round(close, 4),
                "volume": 100000 + index * 100,
            }
        )
    return rows


class TradingCoreTests(unittest.TestCase):
    def test_technical_analysis_includes_extended_fields(self) -> None:
        technical = build_technical_analysis(sample_rows(), ticker="300033.SZ", adjustment_basis="qfq")
        self.assertIn("atr14", technical["daily"])
        self.assertIn("trend_slope_20", technical["daily"])
        self.assertIn("clusters", technical["daily"]["support_resistance"])
        self.assertIn("alignment", technical["cross_timeframe_summary"])

    def test_conditional_decision_passes_integrity(self) -> None:
        technical = build_technical_analysis(sample_rows(), ticker="300033.SZ", adjustment_basis="qfq")
        record = build_decision_record(
            ticker="300033.SZ",
            market="a_share",
            horizon="20d",
            mode="conditional_strong",
            technical_analysis=technical,
            source_log=[
                {
                    "source_name": "unit_test",
                    "endpoint_or_interface": "sample_rows",
                    "retrieved_at": "2026-05-23T00:00:00Z",
                    "status": "ok",
                }
            ],
            source_capability_matrix=[],
            missing_data=["unit test has no financial/event evidence"],
        )
        result = validate_record(record)
        self.assertEqual(result["status"], "pass", result)

    def test_decision_markdown_renderer_keeps_key_fields_visible(self) -> None:
        technical = build_technical_analysis(sample_rows(), ticker="300033.SZ", adjustment_basis="qfq")
        record = build_decision_record(
            ticker="300033.SZ",
            market="a_share",
            horizon="20d",
            mode="conditional_strong",
            technical_analysis=technical,
            source_log=[
                {
                    "source_name": "unit_test",
                    "endpoint_or_interface": "sample_rows",
                    "retrieved_at": "2026-05-23T00:00:00Z",
                    "status": "ok",
                }
            ],
            source_capability_matrix=[],
        )
        record["report_integrity_status"] = validate_record(record)["report_integrity_status"]
        markdown = render_markdown("decision", record)
        self.assertIn("交易决策卡", markdown)
        self.assertIn("条件化计划", markdown)
        self.assertIn("A股执行可行性", markdown)
        self.assertIn("Polymarket 宏观/事件预期", markdown)
        self.assertIn("Not investment advice", markdown)

    def test_decision_record_includes_professional_research_scaffolding(self) -> None:
        technical = build_technical_analysis(sample_rows(), ticker="300033.SZ", adjustment_basis="qfq")
        record = build_decision_record(
            ticker="300033.SZ",
            market="a_share",
            horizon="20d",
            mode="conditional_strong",
            technical_analysis=technical,
            source_log=[
                {
                    "source_name": "unit_test",
                    "endpoint_or_interface": "sample_rows",
                    "retrieved_at": "2026-06-17T00:00:00Z",
                    "status": "ok",
                }
            ],
            source_capability_matrix=[],
        )
        self.assertIn("evidence_matrix", record)
        self.assertEqual(record["evidence_sufficiency_gate"]["status"], "research_only")
        self.assertFalse(record["evidence_sufficiency_gate"]["decision_support_allowed"])
        self.assertIn("tear_sheet", record["research_artifacts"])
        markdown = render_markdown("decision", record)
        self.assertIn("证据矩阵", markdown)
        self.assertIn("专业研究产物", markdown)

    def test_polymarket_provider_keeps_macro_markets_and_tracks_snapshot_delta(self) -> None:
        state = {"probability": "0.62", "volume": "1000", "liquidity": "500"}

        def transport(_url: str, _timeout: float) -> dict[str, object]:
            return {
                "markets": [
                    {
                        "id": "fed-cut-june",
                        "question": "Will the Federal Reserve cut interest rates by June 2026?",
                        "slug": "fed-cut-june-2026",
                        "outcomes": '["Yes", "No"]',
                        "outcomePrices": f'["{state["probability"]}", "0.38"]',
                        "volume": state["volume"],
                        "liquidity": state["liquidity"],
                        "openInterest": "250",
                        "endDate": "2026-06-30",
                        "active": True,
                        "closed": False,
                        "resolutionSource": "Federal Reserve",
                        "category": "Economy",
                    }
                ]
            }

        provider = PolymarketMacroSignalProvider(transport=transport)
        with tempfile.TemporaryDirectory() as tmp:
            first = provider.fetch_context(
                ticker="300033.SZ",
                market="a_share",
                query_terms=["Federal Reserve"],
                max_markets=1,
                snapshot_root=Path(tmp),
            )
            state["probability"] = "0.72"
            state["volume"] = "1300"
            state["liquidity"] = "700"
            second = provider.fetch_context(
                ticker="300033.SZ",
                market="a_share",
                query_terms=["Federal Reserve"],
                max_markets=1,
                snapshot_root=Path(tmp),
            )

        self.assertEqual(first.context["status"], "available")
        self.assertEqual(first.context["selected_markets"][0]["relevance_tier"], "macro_regime")
        change = second.context["selected_markets"][0]["change"]
        self.assertEqual(change["baseline_status"], "matched_local_history")
        self.assertAlmostEqual(change["probability_delta"], 0.10)
        self.assertEqual(change["volume_delta"], 300.0)

    def test_polymarket_provider_filters_low_signal_markets(self) -> None:
        def transport(_url: str, _timeout: float) -> dict[str, object]:
            return {
                "markets": [
                    {
                        "id": "nba-finals",
                        "question": "Will the Lakers win the NBA finals?",
                        "slug": "lakers-finals",
                        "outcomes": '["Yes", "No"]',
                        "outcomePrices": '["0.55", "0.45"]',
                        "volume": "10000",
                        "active": True,
                        "closed": False,
                    }
                ]
            }

        provider = PolymarketMacroSignalProvider(transport=transport)
        result = provider.fetch_context(
            ticker="300033.SZ",
            market="a_share",
            query_terms=["basketball"],
            max_markets=3,
        )
        self.assertEqual(result.context["status"], "no_related_markets")
        self.assertEqual(result.context["selected_markets"], [])

    def test_decision_record_with_polymarket_context_passes_integrity(self) -> None:
        def transport(_url: str, _timeout: float) -> dict[str, object]:
            return {
                "markets": [
                    {
                        "id": "tariff-policy",
                        "question": "Will US tariff policy against China tighten before July 2026?",
                        "slug": "us-china-tariffs-july-2026",
                        "outcomes": '["Yes", "No"]',
                        "outcomePrices": '["0.41", "0.59"]',
                        "volume": "2100",
                        "liquidity": "900",
                        "active": True,
                        "closed": False,
                        "category": "Politics",
                    }
                ]
            }

        technical = build_technical_analysis(sample_rows(), ticker="300033.SZ", adjustment_basis="qfq")
        poly = PolymarketMacroSignalProvider(transport=transport).fetch_context(
            ticker="300033.SZ",
            market="a_share",
            query_terms=["tariffs China"],
            max_markets=1,
        )
        record = build_decision_record(
            ticker="300033.SZ",
            market="a_share",
            horizon="20d",
            mode="conditional_strong",
            technical_analysis=technical,
            source_log=[
                {
                    "source_name": "unit_test",
                    "endpoint_or_interface": "sample_rows",
                    "retrieved_at": "2026-05-23T00:00:00Z",
                    "status": "ok",
                },
                *poly.source_log,
            ],
            source_capability_matrix=poly.source_capability_matrix,
            prediction_market_context=poly.context,
        )
        result = validate_record(record)
        self.assertEqual(result["status"], "pass", result)
        markdown = render_markdown("decision", record)
        self.assertIn("Polymarket 宏观/事件预期", markdown)
        self.assertIn("tariff", markdown.lower())

    def test_integrity_blocks_unconditional_trade_phrase(self) -> None:
        technical = build_technical_analysis(sample_rows(), ticker="300033.SZ", adjustment_basis="qfq")
        record = build_decision_record(
            ticker="300033.SZ",
            market="a_share",
            horizon="20d",
            mode="conditional_strong",
            technical_analysis=technical,
            source_log=[
                {
                    "source_name": "unit_test",
                    "endpoint_or_interface": "sample_rows",
                    "retrieved_at": "2026-05-23T00:00:00Z",
                    "status": "ok",
                }
            ],
            source_capability_matrix=[],
        )
        record["decision_support"]["trigger_conditions"].append("立即买入")
        result = validate_record(record)
        self.assertEqual(result["status"], "fail")

    def test_a_share_execution_rules(self) -> None:
        check = build_a_share_execution_check(
            ticker="300033.SZ",
            board="创业板",
            latest_close=100.0,
            trigger_level=110.0,
        )
        self.assertEqual(check["price_limit_pct"], 0.20)
        self.assertTrue(check["trigger_level_within_next_day_limit_reference"])
        self.assertTrue(check["t_plus_one"])

    def test_journal_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trades.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["date", "symbol", "side", "quantity", "price", "fee"])
                writer.writeheader()
                writer.writerow({"date": "2026-01-01", "symbol": "300033.SZ", "side": "buy", "quantity": 100, "price": 10, "fee": 5})
                writer.writerow({"date": "2026-01-10", "symbol": "300033.SZ", "side": "sell", "quantity": 100, "price": 12, "fee": 5})
            result = analyze_journal(path)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["profile"]["total_roundtrips"], 1)
        self.assertEqual(result["shadow_account_profile"]["status"], "ok")
        self.assertIn("post_trade_review", result)
        self.assertEqual(result["rule_consistency_review"]["status"], "needs_plan_reference")

    def test_local_backtest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ohlcv.json"
            path.write_text(json.dumps(sample_rows(90)), encoding="utf-8")
            result = run_local_breakout_backtest(path)
        self.assertEqual(result["status"], "ok")
        self.assertIn("metrics", result)
        self.assertIn("professional_validation", result)
        self.assertIn("untradable_reasons", result)

    def test_alpha_bench_skeleton_includes_professional_factor_diagnostics(self) -> None:
        result = alpha_bench_skeleton("csi300", "gtja191", "2021-2026")
        diagnostics = result["professional_factor_diagnostics"]
        self.assertEqual(diagnostics["required_metrics"]["ic"], "source_gap")
        self.assertIn("turnover", diagnostics["required_metrics"])
        markdown = render_markdown("alpha_bench", result)
        self.assertIn("专业因子诊断", markdown)

    def test_watchlist_management_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "default.json"
            created = init_watchlist(path)
            self.assertEqual(created["operation_status"], "created")

            added = upsert_watchlist_item(
                path,
                {
                    "ticker": "300033.sz",
                    "name": "同花顺",
                    "group": "金融科技",
                    "priority": 1,
                    "tags": ["AI", "证券IT"],
                    "research_state": "research_candidate",
                },
            )
            self.assertEqual(added["operation_status"], "added")
            self.assertEqual(added["items"][0]["ticker"], "300033.SZ")
            self.assertEqual(added["items"][0]["research_state"], "research_candidate")

            updated = update_watchlist_item(path, "300033.SZ", {"status": "research_candidate", "review.include_in_daily_pipeline": False})
            self.assertEqual(updated["operation_status"], "updated")
            self.assertFalse(updated["items"][0]["include_in_daily_pipeline"])

            shown = show_watchlist(path)
            markdown = render_markdown("watchlist", shown)
            self.assertIn("观察池配置卡", markdown)
            self.assertIn("桌面端快捷说法", markdown)

            removed = remove_watchlist_item(path, "300033.SZ")
            self.assertEqual(removed["operation_status"], "removed")
            self.assertEqual(removed["summary"]["total_count"], 0)

    def test_search_normalizes_a_share_candidates(self) -> None:
        ticker_result = search_a_share_identifier("300033", provider=FakeProvider())
        self.assertEqual(ticker_result["status"], "ok")
        self.assertEqual(ticker_result["search_candidates"][0]["ticker"], "300033.SZ")

        alias_result = search_a_share_identifier("同花顺", provider=FakeProvider())
        self.assertEqual(alias_result["search_candidates"][0]["ticker"], "300033.SZ")

        missing_result = search_a_share_identifier("不存在的测试证券", market="hk", provider=FakeProvider())
        self.assertEqual(missing_result["status"], "source_gap")
        self.assertIn("missing_data", missing_result)

    def test_watchlist_schema_adds_openstock_style_fields_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "default.json"
            added = upsert_watchlist_item(path, {"ticker": "300033", "status": "watch_only"})
            item = added["watchlist"]["tickers"][0]
            self.assertEqual(item["ticker"], "300033.SZ")
            self.assertIn("alert_rules", item)
            self.assertIn("news_preferences", item)
            self.assertIn("source_refresh_policy", item)
            self.assertIn("last_reviewed_at", item)

            with self.assertRaises(ValueError):
                upsert_watchlist_item(path, {"ticker": "300033.US"})
            with self.assertRaises(ValueError):
                upsert_watchlist_item(path, {"ticker": "300033.SZ", "status": "buy_now"})

    def test_alert_rules_trigger_once_and_track_source_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alerts.jsonl"
            add_result = add_alert_rule(ticker="300033.SZ", condition="above", level=100, path=path, expires="90d")
            self.assertEqual(add_result["summary"]["active_count"], 1)

            provider = FakeProvider({"300033.SZ": {"latest": 101.0, "trade_date": "2026-06-17"}})
            checked = check_alert_rules(path=path, provider=provider)
            self.assertEqual(checked["alert_check_result"]["triggered_count"], 1)
            self.assertEqual(checked["alert_rules"][0]["status"], "triggered")

            checked_again = check_alert_rules(path=path, provider=provider)
            self.assertEqual(checked_again["alert_check_result"]["triggered_count"], 0)
            self.assertEqual(checked_again["alert_check_result"]["checks"][0]["status"], "already_triggered")

            gap_path = Path(tmp) / "gap_alerts.jsonl"
            add_alert_rule(ticker="000001.SZ", condition="below", level=10, path=gap_path)
            gap = check_alert_rules(path=gap_path, provider=FakeProvider())
            self.assertEqual(gap["qa_status"]["status"], "warn")
            self.assertEqual(gap["alert_check_result"]["checks"][0]["status"], "source_gap")

    def test_market_brief_aggregates_watchlist_alerts_and_qa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            watchlist_path = Path(tmp) / "default.json"
            alerts_path = Path(tmp) / "alerts.jsonl"
            upsert_watchlist_item(watchlist_path, {"ticker": "300033.SZ", "name": "同花顺", "priority": 1})
            upsert_watchlist_item(watchlist_path, {"ticker": "000001.SZ", "name": "平安银行", "priority": 2})
            add_alert_rule(ticker="300033.SZ", condition="above", level=100, path=alerts_path)

            record = build_market_brief(
                watchlist_path=watchlist_path,
                alerts_path=alerts_path,
                review_date="2026-06-17",
                provider=FakeProvider({"300033.SZ": {"latest": 101.0, "trade_date": "2026-06-17"}}),
            )
            self.assertEqual(record["market_brief"]["summary"]["reviewed_count"], 2)
            self.assertEqual(record["market_brief"]["summary"]["quote_available_count"], 1)
            self.assertEqual(record["market_brief"]["summary"]["triggered_alert_count"], 1)
            self.assertEqual(record["market_brief"]["summary"]["dynamic_ranking"], "enabled")
            self.assertIn("morning_brief", record)
            self.assertIn("market_context", record["morning_brief"])
            self.assertEqual(record["qa_status"]["status"], "warn")
            markdown = render_markdown("brief", record)
            self.assertIn("每日观察池摘要", markdown)
            self.assertIn("Morning Brief", markdown)
            self.assertIn("触发提醒", markdown)

    def test_orchestrator_routes_chinese_intent_to_daily_watchlist(self) -> None:
        route = route_user_intent("帮我看今天观察池", RunIntentOptions(intent="帮我看今天观察池"))
        self.assertEqual(route.workflow_id, "daily_a_share_decision_pipeline")
        self.assertEqual(route.scenario_id, "daily_watchlist_pipeline")

    def test_workflow_registry_loads_all_productized_workflows_with_executors(self) -> None:
        registry = WorkflowRegistry()
        self.assertEqual(set(WORKFLOW_EXECUTORS), set(registry.recipes))
        for workflow_id, executor in WORKFLOW_EXECUTORS.items():
            route = registry.route_intent(WorkflowContext(intent="", ticker="300033.SZ"), workflow_id)
            self.assertEqual(route.workflow_id, workflow_id)
            self.assertEqual(route.executor, executor)

    def test_orchestrator_missing_ticker_returns_needs_input(self) -> None:
        result = run_user_intent(RunIntentOptions(intent="分析这只票"))
        self.assertEqual(result["status"], "needs_input")
        self.assertEqual(result["workflow_id"], "a_share_decision_support")
        self.assertEqual(result["missing_inputs"][0]["field"], "ticker")
        self.assertIn("要分析哪只 A股", result["next_question"])

    def test_cli_run_dry_run_returns_plan_without_machine_record(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            status = cli_main(["run", "--intent", "分析这只票", "--ticker", "300033.SZ", "--dry-run"])
        self.assertEqual(status, 0)
        text = output.getvalue()
        self.assertIn("执行计划", text)
        self.assertIn("single_stock_decision", text)
        self.assertNotIn("internal_route", text)

    def test_cli_decision_and_run_use_same_workflow_executor(self) -> None:
        registry = WorkflowRegistry()
        run_route = route_user_intent("分析这只票", RunIntentOptions(intent="分析这只票", ticker="300033.SZ"))
        legacy_route = registry.route_intent(WorkflowContext(intent="decision 300033.SZ", ticker="300033.SZ"), "a_share_decision_support")
        self.assertEqual(run_route.workflow_id, legacy_route.workflow_id)
        self.assertEqual(run_route.executor, legacy_route.executor)


if __name__ == "__main__":
    unittest.main()
