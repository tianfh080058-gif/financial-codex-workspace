#!/usr/bin/env python3
"""Calculate A-share technical_analysis from sourced OHLCV data."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume")
STATUS_INSUFFICIENT = "insufficient_data"
FIELD_ALIASES = {
    "date": ("date", "trade_date", "日期", "时间"),
    "open": ("open", "开盘", "开盘价"),
    "high": ("high", "最高", "最高价"),
    "low": ("low", "最低", "最低价"),
    "close": ("close", "收盘", "收盘价"),
    "volume": ("volume", "成交量", "vol"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> int:
    print(json.dumps({"status": "fail", "error": message}, ensure_ascii=False, indent=2))
    return 1


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    return float(text)


def normalize_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("/", "-")
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    raise ValueError(f"unsupported date format: {value!r}")


def pick(row: dict[str, Any], field: str) -> Any:
    lower_map = {str(key).lower(): value for key, value in row.items()}
    for name in FIELD_ALIASES[field]:
        if name in row:
            return row[name]
        lower_name = name.lower()
        if lower_name in lower_map:
            return lower_map[lower_name]
    return None


def normalize_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(raw_rows, start=1):
        normalized = {
            "date": normalize_date(pick(row, "date")),
            "open": to_float(pick(row, "open")),
            "high": to_float(pick(row, "high")),
            "low": to_float(pick(row, "low")),
            "close": to_float(pick(row, "close")),
            "volume": to_float(pick(row, "volume")),
        }
        missing = [key for key in REQUIRED_COLUMNS if normalized.get(key) in (None, "")]
        if missing:
            raise ValueError(f"row {index} missing required OHLCV fields: {', '.join(missing)}")
        rows.append(normalized)
    return sorted(rows, key=lambda item: item["date"])


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return normalize_rows(list(csv.DictReader(handle)))
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        raw_rows = value.get("records") or value.get("data") or value.get("rows")
    else:
        raw_rows = value
    if not isinstance(raw_rows, list) or not all(isinstance(row, dict) for row in raw_rows):
        raise ValueError("input must be a JSON array, a JSON object with records/data/rows, or a CSV")
    return normalize_rows(raw_rows)


def sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def ema_series(values: list[float], window: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (window + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(value * alpha + result[-1] * (1 - alpha))
    return result


def macd(values: list[float]) -> dict[str, Any]:
    if len(values) < 35:
        return {"fast": 12, "slow": 26, "signal": 9, "dif": None, "dea": None, "histogram": None}
    ema12 = ema_series(values, 12)
    ema26 = ema_series(values, 26)
    dif_series = [fast - slow for fast, slow in zip(ema12, ema26)]
    dea_series = ema_series(dif_series, 9)
    dif = dif_series[-1]
    dea = dea_series[-1]
    return {
        "fast": 12,
        "slow": 26,
        "signal": 9,
        "dif": round(dif, 4),
        "dea": round(dea, 4),
        "histogram": round(dif - dea, 4),
    }


def rsi(values: list[float], window: int = 14) -> float | None:
    if len(values) <= window:
        return None
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    recent = changes[-window:]
    gains = [max(change, 0) for change in recent]
    losses = [abs(min(change, 0)) for change in recent]
    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def bollinger(values: list[float], window: int = 20, width: float = 2.0) -> dict[str, Any]:
    middle = sma(values, window)
    if middle is None:
        return {"upper": None, "middle": None, "lower": None, "position": None}
    recent = values[-window:]
    variance = sum((value - middle) ** 2 for value in recent) / window
    stddev = math.sqrt(variance)
    upper = middle + width * stddev
    lower = middle - width * stddev
    close = values[-1]
    if close > upper:
        position = "above_upper"
    elif close < lower:
        position = "below_lower"
    elif close >= middle:
        position = "upper_half"
    else:
        position = "lower_half"
    return {
        "upper": round(upper, 4),
        "middle": round(middle, 4),
        "lower": round(lower, 4),
        "position": position,
    }


def drawdown(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    peak = max(values[-window:])
    if peak == 0:
        return None
    return round(values[-1] / peak - 1, 4)


def support_resistance(rows: list[dict[str, Any]], window: int = 20) -> dict[str, Any]:
    if not rows:
        return {"support": [], "resistance": [], "method": "recent_swing_high_low"}
    recent = rows[-min(window, len(rows)) :]
    support = min(row["low"] for row in recent)
    resistance = max(row["high"] for row in recent)
    return {
        "support": [round(support, 4)],
        "resistance": [round(resistance, 4)],
        "method": "recent_swing_high_low",
    }


def trend_status(close: float, ma20: float | None, ma60: float | None, macd_histogram: float | None, min_bars_ok: bool) -> str:
    if not min_bars_ok:
        return STATUS_INSUFFICIENT
    if ma20 is None or ma60 is None or macd_histogram is None:
        return "mixed"
    if close > ma20 > ma60 and macd_histogram > 0:
        return "constructive"
    if close < ma20 < ma60 and macd_histogram < 0:
        return "deteriorating"
    if close > ma20 and macd_histogram >= 0:
        return "neutral"
    return "mixed"


def resample(rows: list[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for row in rows:
        date = datetime.fromisoformat(row["date"][:10])
        if period == "weekly":
            year, week, _ = date.isocalendar()
            key = f"{year}-W{week:02d}"
        elif period == "monthly":
            key = f"{date.year}-{date.month:02d}"
        else:
            raise ValueError(f"unsupported resample period: {period}")
        groups.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for period_rows in groups.values():
        output.append(
            {
                "date": period_rows[-1]["date"],
                "open": period_rows[0]["open"],
                "high": max(row["high"] for row in period_rows),
                "low": min(row["low"] for row in period_rows),
                "close": period_rows[-1]["close"],
                "volume": sum(row["volume"] for row in period_rows),
            }
        )
    return output


def period_analysis(rows: list[dict[str, Any]], timeframe: str, calculation_basis: str) -> dict[str, Any]:
    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]
    close = closes[-1] if closes else None
    ma_values = {f"ma{window}": sma(closes, window) for window in (5, 10, 20, 60, 120)}
    macd_value = macd(closes)
    status = trend_status(
        close or 0,
        ma_values["ma20"],
        ma_values["ma60"],
        macd_value.get("histogram"),
        len(rows) >= (20 if timeframe == "daily" else 6),
    )
    rounded_ma = {key: (round(value, 4) if value is not None else None) for key, value in ma_values.items()}
    missing_data = []
    if len(rows) < 20:
        missing_data.append("Need at least 20 bars for the standard short-term technical set.")
    if len(rows) < 60:
        missing_data.append("Need at least 60 bars for medium-term MA and drawdown context.")
    if len(rows) < 120:
        missing_data.append("Need at least 120 bars for MA120.")

    volume_ma5 = sma(volumes, 5)
    volume_ma20 = sma(volumes, 20)
    volume_ratio = volumes[-1] / volume_ma5 if volumes and volume_ma5 else None
    trend_summary = summarize_trend(close, rounded_ma, status)

    common = {
        "status": status,
        "calculation_basis": calculation_basis,
        "bar_count": len(rows),
        "missing_data": missing_data,
    }
    if timeframe == "monthly":
        return {
            **common,
            "long_term_ma_direction": long_term_ma_direction(rounded_ma),
            "trend_summary": trend_summary,
            "major_support_resistance": support_resistance(rows),
            "long_term_drawdown_position": {
                "drawdown_20": drawdown(closes, 20),
                "drawdown_60": drawdown(closes, 60),
            },
        }
    if timeframe == "weekly":
        return {
            **common,
            "trend_summary": trend_summary,
            "momentum_summary": summarize_momentum(macd_value, rsi(closes)),
            "volume_price_summary": summarize_volume(volume_ratio),
            "support_resistance": support_resistance(rows),
        }
    return {
        **common,
        "moving_averages": {
            **rounded_ma,
            "trend_summary": trend_summary,
        },
        "momentum": {
            "macd": macd_value,
            "rsi14": rsi(closes),
        },
        "volatility": {
            "bollinger_20_2": bollinger(closes),
            "drawdown_20": drawdown(closes, 20),
            "drawdown_60": drawdown(closes, 60),
        },
        "volume_price": {
            "volume_ma5": round(volume_ma5, 4) if volume_ma5 is not None else None,
            "volume_ma20": round(volume_ma20, 4) if volume_ma20 is not None else None,
            "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
            "volume_price_summary": summarize_volume(volume_ratio),
        },
        "relative_strength": {
            "benchmark": None,
            "lookback_days": None,
            "relative_return": None,
            "summary": "Benchmark data not provided.",
        },
        "support_resistance": support_resistance(rows),
    }


def summarize_trend(close: float | None, ma_values: dict[str, float | None], status: str) -> str:
    if close is None or status == STATUS_INSUFFICIENT:
        return "Insufficient bars for trend summary."
    ma20 = ma_values.get("ma20")
    ma60 = ma_values.get("ma60")
    if ma20 is None or ma60 is None:
        return "Short-term trend is calculable, medium-term MA context is incomplete."
    if close > ma20 > ma60:
        return "Close is above MA20 and MA20 is above MA60."
    if close < ma20 < ma60:
        return "Close is below MA20 and MA20 is below MA60."
    return "Moving averages are mixed."


def summarize_momentum(macd_value: dict[str, Any], rsi_value: float | None) -> str:
    parts = []
    histogram = macd_value.get("histogram")
    if histogram is None:
        parts.append("MACD window is insufficient.")
    elif histogram > 0:
        parts.append("MACD histogram is positive.")
    elif histogram < 0:
        parts.append("MACD histogram is negative.")
    else:
        parts.append("MACD histogram is near zero.")
    if rsi_value is None:
        parts.append("RSI window is insufficient.")
    else:
        parts.append(f"RSI14 is {rsi_value}.")
    return " ".join(parts)


def summarize_volume(volume_ratio: float | None) -> str:
    if volume_ratio is None:
        return "Volume ratio is unavailable."
    if volume_ratio >= 1.5:
        return "Latest volume is materially above recent volume average."
    if volume_ratio <= 0.7:
        return "Latest volume is below recent volume average."
    return "Latest volume is near recent volume average."


def long_term_ma_direction(ma_values: dict[str, float | None]) -> str:
    ma20 = ma_values.get("ma20")
    ma60 = ma_values.get("ma60")
    if ma20 is None or ma60 is None:
        return "insufficient_data"
    if ma20 > ma60:
        return "upward_or_constructive"
    if ma20 < ma60:
        return "downward_or_deteriorating"
    return "flat_or_neutral"


def overall_status(statuses: list[str]) -> str:
    known = [status for status in statuses if status != STATUS_INSUFFICIENT]
    if not known:
        return STATUS_INSUFFICIENT
    if all(status == "constructive" for status in known):
        return "constructive"
    if all(status == "deteriorating" for status in known):
        return "deteriorating"
    if "constructive" in known and "deteriorating" not in known:
        return "neutral"
    return "mixed"


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    rows = load_rows(Path(args.input))
    if not rows:
        raise ValueError("input has no OHLCV rows")
    daily = period_analysis(rows, "daily", "source_period_data")
    weekly_rows = resample(rows, "weekly")
    monthly_rows = resample(rows, "monthly")
    weekly = period_analysis(weekly_rows, "weekly", "resampled_from_daily")
    monthly = period_analysis(monthly_rows, "monthly", "resampled_from_daily")
    statuses = [daily["status"], weekly["status"], monthly["status"]]

    result = {
        "trade_date": rows[-1]["date"],
        "retrieved_at": args.retrieved_at or utc_now(),
        "adjustment_basis": args.adjustment_basis,
        "calculation_basis": "source_ohlcv",
        "timeframe_weights": {
            "daily": "primary",
            "weekly": "confirmation",
            "monthly": "long_term_background_risk_filter",
        },
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "cross_timeframe_summary": {
            "overall_status": overall_status(statuses),
            "daily_signal": daily.get("moving_averages", {}).get("trend_summary"),
            "weekly_confirmation": weekly.get("trend_summary"),
            "monthly_background": monthly.get("trend_summary"),
            "evidence_use": [
                "Technical analysis is a calculation layer, not a standalone investment conclusion."
            ],
        },
        "source_ref": args.source_ref or ["source_log[0]"],
        "limitations": [
            "Weekly and monthly bars are resampled from daily data unless a source-native period pull is supplied separately.",
            "No target price, buy/sell rating, personal position sizing, or return promise is produced.",
        ],
    }
    if args.ticker:
        result["ticker"] = args.ticker
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calculate technical_analysis from sourced OHLCV data.")
    parser.add_argument("--input", required=True, help="JSON/CSV file with OHLCV rows")
    parser.add_argument("--ticker", help="Optional normalized ticker")
    parser.add_argument("--adjustment-basis", default="unknown", choices=["unadjusted", "qfq", "hfq", "unknown"])
    parser.add_argument("--retrieved-at", help="Source retrieval timestamp. Defaults to current UTC time.")
    parser.add_argument("--source-ref", action="append", help="Schema source_ref entry")
    parser.add_argument("--output", help="Optional output JSON path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = build_result(args)
        text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
