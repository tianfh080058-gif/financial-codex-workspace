"""Trade journal parsing, behavioral diagnostics, and shadow profile summaries."""

from __future__ import annotations

import csv
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

from .common import utc_now


FIELD_ALIASES = {
    "datetime": ("datetime", "date", "trade_date", "成交时间", "交易时间", "日期"),
    "symbol": ("symbol", "ticker", "code", "证券代码", "代码"),
    "side": ("side", "direction", "买卖方向", "操作", "方向"),
    "quantity": ("quantity", "qty", "shares", "成交数量", "数量"),
    "price": ("price", "成交均价", "成交价格", "价格"),
    "amount": ("amount", "成交金额", "金额"),
    "fee": ("fee", "commission", "手续费", "费用"),
    "market": ("market", "市场"),
}


def analyze_journal(path: Path) -> dict[str, Any]:
    trades = load_trades(path)
    roundtrips = pair_trades_fifo(trades)
    profile = build_profile(trades, roundtrips)
    behavior = diagnose_behavior(trades, roundtrips)
    shadow = extract_shadow_profile(roundtrips)
    analyzed_at = utc_now()
    return {
        "status": "ok",
        "analysis_mode": {"mode": "journal_review"},
        "analyzed_at": analyzed_at,
        "input_path": str(path),
        "trade_count": len(trades),
        "roundtrip_count": len(roundtrips),
        "profile": profile,
        "behavior_diagnostics": behavior,
        "shadow_account_profile": shadow,
        "source_log": [
            {
                "source_name": "user_file",
                "endpoint_or_interface": "broker_export_file",
                "parameters": {"path": str(path), "suffix": path.suffix.lower()},
                "retrieved_at": analyzed_at,
                "status": "ok",
                "missing_fields": [],
            }
        ],
        "qa_status": {
            "status": "not_checked",
            "not_investment_advice_included": True,
            "checks_pending": ["financial-output-qa-gate"],
        },
        "not_investment_advice": True,
        "limitations": [
            "Journal parsing depends on exported broker fields and may require manual column mapping for unusual templates.",
            "Behavior diagnostics are descriptive and do not determine future returns.",
        ],
    }


def load_trades(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            raw_rows = list(csv.DictReader(handle))
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            import pandas as pd  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Excel journal parsing requires pandas/openpyxl in the environment.") from exc
        raw_rows = pd.read_excel(path).to_dict(orient="records")
    else:
        raise ValueError("journal file must be .csv, .xlsx, or .xls")
    trades = [normalize_trade(row) for row in raw_rows]
    return sorted(trades, key=lambda item: item["datetime"])


def normalize_trade(row: dict[str, Any]) -> dict[str, Any]:
    side = str(pick(row, "side") or "").strip().lower()
    if side in {"买入", "buy", "b", "证券买入"}:
        normalized_side = "buy"
    elif side in {"卖出", "sell", "s", "证券卖出"}:
        normalized_side = "sell"
    else:
        raise ValueError(f"unsupported trade side: {side!r}")
    quantity = to_float(pick(row, "quantity"))
    price = to_float(pick(row, "price"))
    if quantity is None or price is None:
        raise ValueError("trade quantity and price are required")
    return {
        "datetime": parse_datetime(pick(row, "datetime")),
        "symbol": str(pick(row, "symbol") or "").strip(),
        "side": normalized_side,
        "quantity": quantity,
        "price": price,
        "amount": to_float(pick(row, "amount")) or quantity * price,
        "fee": to_float(pick(row, "fee")) or 0.0,
        "market": str(pick(row, "market") or "unknown"),
    }


def pick(row: dict[str, Any], field: str) -> Any:
    lower = {str(key).lower(): value for key, value in row.items()}
    for name in FIELD_ALIASES[field]:
        if name in row:
            return row[name]
        if name.lower() in lower:
            return lower[name.lower()]
    return None


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(",", "").strip())


def parse_datetime(value: Any) -> datetime:
    text = str(value or "").strip().replace("/", "-")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    if len(text) >= 10:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            pass
    if len(text) >= 8 and text[:8].isdigit():
        try:
            return datetime.strptime(text[:8], "%Y%m%d")
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"unsupported datetime: {value!r}") from exc


def pair_trades_fifo(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queues: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    roundtrips: list[dict[str, Any]] = []
    for trade in trades:
        if trade["side"] == "buy":
            queues[trade["symbol"]].append(dict(trade))
            continue
        remaining = trade["quantity"]
        queue = queues[trade["symbol"]]
        while remaining > 1e-9 and queue:
            lot = queue[0]
            take = min(lot["quantity"], remaining)
            gross = (trade["price"] - lot["price"]) * take
            buy_fee = lot["fee"] * take / lot["quantity"] if lot["quantity"] else 0
            sell_fee = trade["fee"] * take / trade["quantity"] if trade["quantity"] else 0
            pnl = gross - buy_fee - sell_fee
            cost = lot["price"] * take
            roundtrips.append(
                {
                    "symbol": trade["symbol"],
                    "buy_dt": lot["datetime"].isoformat(),
                    "sell_dt": trade["datetime"].isoformat(),
                    "qty": take,
                    "buy_price": lot["price"],
                    "sell_price": trade["price"],
                    "hold_days": round((trade["datetime"] - lot["datetime"]).total_seconds() / 86400, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl / cost, 4) if cost else 0,
                }
            )
            lot["quantity"] -= take
            remaining -= take
            if lot["quantity"] <= 1e-9:
                queue.popleft()
    return roundtrips


def build_profile(trades: list[dict[str, Any]], roundtrips: list[dict[str, Any]]) -> dict[str, Any]:
    wins = [item for item in roundtrips if item["pnl"] > 0]
    losses = [item for item in roundtrips if item["pnl"] < 0]
    avg_win = sum(item["pnl"] for item in wins) / len(wins) if wins else 0
    avg_loss = abs(sum(item["pnl"] for item in losses) / len(losses)) if losses else 0
    span_days = max(1, (trades[-1]["datetime"] - trades[0]["datetime"]).days) if trades else 1
    symbol_counts: dict[str, int] = defaultdict(int)
    for trade in trades:
        symbol_counts[trade["symbol"]] += 1
    return {
        "total_trades": len(trades),
        "total_roundtrips": len(roundtrips),
        "avg_holding_days": round(sum(item["hold_days"] for item in roundtrips) / len(roundtrips), 2) if roundtrips else 0,
        "trade_frequency_per_week": round(len(trades) / span_days * 7, 2),
        "win_rate": round(len(wins) / len(roundtrips), 4) if roundtrips else 0,
        "profit_loss_ratio": round(avg_win / avg_loss, 2) if avg_loss else None,
        "total_pnl": round(sum(item["pnl"] for item in roundtrips), 2),
        "top_symbols": sorted(symbol_counts.items(), key=lambda item: item[1], reverse=True)[:10],
    }


def diagnose_behavior(trades: list[dict[str, Any]], roundtrips: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "disposition_effect": disposition_effect(roundtrips),
        "overtrading": overtrading(trades, roundtrips),
        "chasing_momentum": {
            "severity": "needs_price_context",
            "evidence": "Requires pre-trade market data to test whether entries followed sharp short-term rises.",
        },
        "anchoring": {
            "severity": "needs_review_notes",
            "evidence": "Requires user notes or reference prices to test anchoring behavior.",
        },
    }


def disposition_effect(roundtrips: list[dict[str, Any]]) -> dict[str, Any]:
    wins = [item for item in roundtrips if item["pnl"] > 0]
    losses = [item for item in roundtrips if item["pnl"] < 0]
    if not wins or not losses:
        return {"severity": "low", "evidence": "Not enough winning and losing closed trades to compare holding time."}
    win_hold = sum(item["hold_days"] for item in wins) / len(wins)
    loss_hold = sum(item["hold_days"] for item in losses) / len(losses)
    ratio = loss_hold / win_hold if win_hold else float("inf")
    severity = "high" if ratio >= 1.5 else "medium" if ratio >= 1.2 else "low"
    return {
        "severity": severity,
        "ratio_loss_to_win_hold": round(ratio, 2),
        "avg_winner_hold_days": round(win_hold, 2),
        "avg_loser_hold_days": round(loss_hold, 2),
        "evidence": "Losing closed trades were held longer than winning trades." if ratio > 1 else "Holding times do not show a clear hold-losers-longer pattern.",
    }


def overtrading(trades: list[dict[str, Any]], roundtrips: list[dict[str, Any]]) -> dict[str, Any]:
    if len(trades) < 10 or not roundtrips:
        return {"severity": "low", "evidence": "Insufficient trade count for overtrading diagnosis."}
    frequency = len(trades) / max(1, (trades[-1]["datetime"] - trades[0]["datetime"]).days) * 7
    severity = "high" if frequency >= 20 else "medium" if frequency >= 8 else "low"
    return {
        "severity": severity,
        "trade_frequency_per_week": round(frequency, 2),
        "evidence": "High activity should be compared with realized roundtrip results and fees.",
    }


def extract_shadow_profile(roundtrips: list[dict[str, Any]]) -> dict[str, Any]:
    winners = [item for item in roundtrips if item["pnl"] > 0]
    if not winners:
        return {"status": "insufficient_data", "rules": [], "profile_text": "No profitable closed trades to extract rules from."}
    avg_hold = sum(item["hold_days"] for item in winners) / len(winners)
    avg_gain = sum(item["pnl_pct"] for item in winners) / len(winners)
    return {
        "status": "ok",
        "profitable_roundtrips": len(winners),
        "total_roundtrips": len(roundtrips),
        "typical_holding_days": [round(max(0, avg_hold * 0.5), 1), round(avg_hold * 1.5, 1)],
        "rules": [
            {
                "rule_id": "shadow_rule_1",
                "human_text": "Prior profitable trades tended to close after a moderate holding period; test similar setups in shadow mode before real use.",
                "support_count": len(winners),
                "avg_profitable_pnl_pct": round(avg_gain, 4),
            }
        ],
        "profile_text": "Shadow profile extracted from profitable closed roundtrips; use for simulation and review only.",
    }
