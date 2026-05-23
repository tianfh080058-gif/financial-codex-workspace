"""Execution feasibility rules for conditional plans."""

from __future__ import annotations

from typing import Any


def infer_a_share_price_limit_pct(board: str | None = None, name: str | None = None, ticker: str | None = None) -> float:
    text = " ".join(part for part in (board, name, ticker) if part).lower()
    if "st" in text:
        return 0.05
    if "科创" in text or "star" in text or (ticker or "").startswith("688"):
        return 0.20
    if "创业" in text or "chinext" in text or (ticker or "").startswith("300"):
        return 0.20
    if "北交" in text or (ticker or "").endswith(".BJ"):
        return 0.30
    return 0.10


def build_a_share_execution_check(
    *,
    ticker: str,
    board: str | None,
    latest_close: float | None,
    trigger_level: float | None,
) -> dict[str, Any]:
    limit_pct = infer_a_share_price_limit_pct(board=board, ticker=ticker)
    limit_up = round(latest_close * (1 + limit_pct), 4) if latest_close else None
    limit_down = round(latest_close * (1 - limit_pct), 4) if latest_close else None
    return {
        "market": "a_share",
        "rules_source": "Vibe-Trading ChinaAEngine pattern absorbed into trading_core feasibility checks",
        "t_plus_one": True,
        "short_selling_allowed": False,
        "lot_size_shares": 100,
        "price_limit_pct": limit_pct,
        "estimated_limit_up": limit_up,
        "estimated_limit_down": limit_down,
        "trigger_level_within_next_day_limit_reference": (
            None if latest_close is None or trigger_level is None else limit_down <= trigger_level <= limit_up
        ),
        "cost_model": {
            "commission_min_cny": 5,
            "stamp_tax_side": "sell_side",
            "transfer_fee": "exchange_specific",
            "slippage_model": "fixed_or_sqrt_impact_to_be_selected_by_backtest_config",
        },
        "limitations": [
            "Price-limit feasibility uses the latest close as a reference and must be refreshed before any real order workflow.",
            "This check does not determine personal order size or execute trades.",
        ],
    }
