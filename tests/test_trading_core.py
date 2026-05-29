from __future__ import annotations

import csv
import json
import math
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from tools.calculate_technical_analysis import build_technical_analysis
from tools.check_research_integrity import validate_record
from trading_core.backtest import run_local_breakout_backtest
from trading_core.decision import build_decision_record
from trading_core.execution_rules import build_a_share_execution_check
from trading_core.journal import analyze_journal
from trading_core.polymarket import PolymarketMacroSignalProvider
from trading_core.renderers import render_markdown
from trading_core.watchlist import (
    init_watchlist,
    remove_watchlist_item,
    show_watchlist,
    update_watchlist_item,
    upsert_watchlist_item,
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

    def test_local_backtest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ohlcv.json"
            path.write_text(json.dumps(sample_rows(90)), encoding="utf-8")
            result = run_local_breakout_backtest(path)
        self.assertEqual(result["status"], "ok")
        self.assertIn("metrics", result)

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
                },
            )
            self.assertEqual(added["operation_status"], "added")
            self.assertEqual(added["items"][0]["ticker"], "300033.SZ")

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


if __name__ == "__main__":
    unittest.main()
