"""Decision-card and conditional trade-plan generation."""

from __future__ import annotations

from typing import Any

from .common import utc_now
from .execution_rules import build_a_share_execution_check
from .polymarket import default_prediction_market_context


ALLOWED_DECISION_STATES = {
    "watch_only",
    "research_candidate",
    "hold_monitor",
    "risk_control_review",
    "avoid_or_wait",
}


def build_decision_record(
    *,
    ticker: str,
    market: str,
    horizon: str,
    mode: str,
    technical_analysis: dict[str, Any] | None,
    source_log: list[dict[str, Any]],
    source_capability_matrix: list[dict[str, Any]],
    security_master: dict[str, Any] | None = None,
    market_snapshot: dict[str, Any] | None = None,
    missing_data: list[str] | None = None,
    backtest_validation: dict[str, Any] | None = None,
    prediction_market_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    missing_data = missing_data or []
    prediction_market_context = prediction_market_context or default_prediction_market_context()
    security = security_master or {
        "ticker": ticker,
        "market": market,
        "currency": "CNY" if market == "a_share" else None,
        "identifier_status": "ticker_provided_by_user",
        "identifier_notes": ["Security master was not refreshed."],
    }
    market_snapshot = market_snapshot or build_market_snapshot_from_technical(technical_analysis)
    state = choose_decision_state(technical_analysis, missing_data)
    plan = build_conditional_trade_plan(
        ticker=ticker,
        market=market,
        horizon=horizon,
        decision_state=state,
        technical_analysis=technical_analysis,
        security_master=security,
    )
    primary_evidence = summarize_primary_evidence(technical_analysis)
    prediction_evidence = summarize_prediction_market_evidence(prediction_market_context)
    prediction_gaps = prediction_market_gaps(prediction_market_context)
    record = {
        "created_at": utc_now(),
        "analysis_mode": {
            "mode": "decision_support",
            "requested_by_user": True,
            "allowed_values": ["research", "decision_support"],
            "mode_notes": [
                "decision_support mode uses evidence, trigger conditions, invalidation, and risk controls",
                "conditional_trade_plan is not a target price, rating, personal position sizing, or return promise",
            ],
        },
        "security_master": security,
        "source_capability_matrix": source_capability_matrix,
        "source_log": source_log,
        "market_snapshot": market_snapshot,
        "technical_analysis": technical_analysis,
        "prediction_market_context": prediction_market_context,
        "decision_card": {
            "ticker": ticker,
            "market": market,
            "horizon": horizon,
            "mode": mode,
            "decision_state": state,
            "setup_quality": summarize_setup_quality(technical_analysis, missing_data),
            "primary_evidence": [*primary_evidence, *prediction_evidence],
            "primary_risks": [
                "Financial, announcement, and sector evidence may be incomplete unless sourced in this run.",
                "Technical levels must be refreshed with current market data before use.",
                "Polymarket probabilities are auxiliary event evidence, not deterministic forecasts or trading instructions.",
            ],
            "next_review": "Refresh market data and source gaps before relying on this decision card.",
        },
        "conditional_trade_plan": plan,
        "decision_support": {
            "decision_state": state,
            "supporting_evidence": [*primary_evidence, *prediction_evidence],
            "disconfirming_evidence": [
                "Non-technical evidence is not complete unless financials, announcements, and sector context were sourced.",
                "A technical deterioration against the invalidation/risk-control level would weaken this setup.",
                *prediction_market_counterpoints(prediction_market_context),
            ],
            "trigger_conditions": [plan["trigger_condition"]],
            "invalidation_conditions": [
                plan["invalidation_condition"],
                "If refreshed source data contradicts the technical setup, move to avoid_or_wait or risk_control_review.",
            ],
            "risk_controls": [
                plan["exit_or_reduce_condition"],
                "No personal position size is generated; any sizing framework must be supplied separately and reviewed.",
            ],
            "confidence": confidence_bucket(technical_analysis, missing_data),
            "confidence_reason": confidence_reason(technical_analysis, missing_data, prediction_market_context),
            "missing_data": [*missing_data, *prediction_gaps],
        },
        "backtest_validation": backtest_validation,
        "review_horizons": [5, 20, 60],
        "qa_status": {
            "not_investment_advice_included": True,
            "target_price_blocked": True,
            "rating_blocked": True,
            "personal_position_sizing_blocked": True,
            "return_promise_blocked": True,
            "prediction_market_context_checked": prediction_market_context.get("status") in {
                "available",
                "no_related_markets",
                "source_gap",
            },
            "prediction_market_context_status": prediction_market_context.get("status"),
            "source_gaps": [*missing_data, *prediction_gaps],
        },
        "not_investment_advice": True,
        "limitations": [
            "Not investment advice. This output is research and decision support only.",
            "No live order is created or executed.",
            "Levels are conditional calculations from sourced OHLCV and must be refreshed before use.",
            "Polymarket context is read-only prediction-market evidence and does not replace market data, filings, or announcements.",
        ],
    }
    if market == "a_share":
        latest_close = latest_close_from_technical(technical_analysis)
        trigger_value = plan.get("trigger_level", {}).get("value") if isinstance(plan.get("trigger_level"), dict) else None
        record["execution_feasibility"] = build_a_share_execution_check(
            ticker=ticker,
            board=security.get("board"),
            latest_close=latest_close,
            trigger_level=trigger_value,
        )
    return record


def choose_decision_state(technical: dict[str, Any] | None, missing_data: list[str]) -> str:
    if not technical:
        return "avoid_or_wait"
    overall = (technical.get("cross_timeframe_summary") or {}).get("overall_status")
    alignment = (technical.get("cross_timeframe_summary") or {}).get("alignment")
    if overall == "constructive" and alignment == "constructive_alignment":
        return "research_candidate"
    if overall == "constructive":
        return "watch_only" if missing_data else "research_candidate"
    if overall == "deteriorating":
        return "risk_control_review"
    if overall == "insufficient_data":
        return "avoid_or_wait"
    return "watch_only"


def latest_close_from_technical(technical: dict[str, Any] | None) -> float | None:
    if not isinstance(technical, dict):
        return None
    latest = ((technical.get("daily") or {}).get("latest_bar") or {}).get("close")
    return float(latest) if isinstance(latest, (int, float)) else None


def build_market_snapshot_from_technical(technical: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(technical, dict):
        return None
    latest = (technical.get("daily") or {}).get("latest_bar")
    if not isinstance(latest, dict):
        return None
    return {
        "trade_date": latest.get("date") or technical.get("trade_date"),
        "retrieved_at": technical.get("retrieved_at"),
        "price": {
            "latest": latest.get("close"),
            "close": latest.get("close"),
            "open": latest.get("open"),
            "high": latest.get("high"),
            "low": latest.get("low"),
            "currency": "CNY",
            "adjustment_basis": technical.get("adjustment_basis", "unknown"),
        },
        "liquidity": {"volume": latest.get("volume"), "volume_unit": "shares_or_source_unit"},
        "source_ref": technical.get("source_ref") or ["source_log[0]"],
        "limitations": ["Market snapshot is derived from the OHLCV rows used for technical analysis."],
    }


def build_conditional_trade_plan(
    *,
    ticker: str,
    market: str,
    horizon: str,
    decision_state: str,
    technical_analysis: dict[str, Any] | None,
    security_master: dict[str, Any],
) -> dict[str, Any]:
    close = latest_close_from_technical(technical_analysis)
    support, resistance = nearest_levels(technical_analysis, close)
    atr14 = ((technical_analysis or {}).get("daily") or {}).get("atr14")
    risk_level = derive_risk_level(close, support, atr14)
    trigger_level = derive_trigger_level(close, resistance, atr14)
    source_ref = (technical_analysis or {}).get("source_ref") or ["source_log[0]"]
    action_type = action_type_for_state(decision_state)
    return {
        "action_type": action_type,
        "trigger_level": level_object(trigger_level, market, "trigger_level_from_resistance_or_atr"),
        "trigger_condition": trigger_condition(action_type, trigger_level),
        "invalidation_level": level_object(support or risk_level, market, "nearest_support_or_risk_reference"),
        "invalidation_condition": invalidation_condition(support or risk_level),
        "risk_control_level": level_object(risk_level, market, "support_minus_atr_buffer_when_available"),
        "exit_or_reduce_condition": exit_condition(risk_level),
        "time_validity": horizon,
        "source_ref": source_ref,
        "assumptions": [
            "Levels are calculated from sourced OHLCV, not from a valuation target.",
            "No personal position sizing is included.",
            "Financial, event, and liquidity checks should be refreshed before any real-world action.",
        ],
        "security_context": {
            "ticker": ticker,
            "market": market,
            "board": security_master.get("board"),
        },
    }


def nearest_levels(technical: dict[str, Any] | None, close: float | None) -> tuple[float | None, float | None]:
    if not isinstance(technical, dict):
        return None, None
    sr = ((technical.get("daily") or {}).get("support_resistance") or {})
    supports = extract_levels(sr.get("clusters", {}).get("support")) or extract_levels(sr.get("support"))
    resistances = extract_levels(sr.get("clusters", {}).get("resistance")) or extract_levels(sr.get("resistance"))
    if close is None:
        support = max(supports) if supports else None
        resistance = min(resistances) if resistances else None
    else:
        below = [level for level in supports if level <= close]
        above = [level for level in resistances if level >= close]
        support = max(below) if below else (max(supports) if supports else None)
        resistance = min(above) if above else (max(resistances) if resistances else None)
    return support, resistance


def extract_levels(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    levels: list[float] = []
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("level"), (int, float)):
            levels.append(float(item["level"]))
        elif isinstance(item, (int, float)):
            levels.append(float(item))
    return levels


def derive_trigger_level(close: float | None, resistance: float | None, atr14: Any) -> float | None:
    if resistance:
        return round(resistance * 1.003, 4)
    if close and isinstance(atr14, (int, float)):
        return round(close + 0.5 * float(atr14), 4)
    return close


def derive_risk_level(close: float | None, support: float | None, atr14: Any) -> float | None:
    if support and isinstance(atr14, (int, float)):
        return round(support - 0.5 * float(atr14), 4)
    if support:
        return round(support, 4)
    if close and isinstance(atr14, (int, float)):
        return round(close - float(atr14), 4)
    return close


def level_object(value: float | None, market: str, derivation: str) -> dict[str, Any]:
    return {
        "value": value,
        "unit": "CNY/share" if market == "a_share" else "source_currency_per_unit",
        "derivation": derivation,
        "is_target_price": False,
    }


def action_type_for_state(state: str) -> str:
    return {
        "research_candidate": "conditional_entry_review",
        "hold_monitor": "conditional_hold_monitor",
        "risk_control_review": "conditional_reduce_or_exit_review",
        "avoid_or_wait": "conditional_avoid_or_wait",
        "watch_only": "conditional_watch",
    }.get(state, "conditional_watch")


def trigger_condition(action_type: str, trigger_level: float | None) -> str:
    if trigger_level is None:
        return "No trigger level is usable until refreshed OHLCV data is available."
    if action_type == "conditional_entry_review":
        return f"Review only if the close holds above {trigger_level} with volume confirmation and no contrary event evidence."
    if action_type == "conditional_reduce_or_exit_review":
        return f"Do not reclassify constructively unless price recovers above {trigger_level} with improved technical breadth."
    return f"Keep on watch; re-evaluate if price closes above {trigger_level} and source gaps are resolved."


def invalidation_condition(level: float | None) -> str:
    if level is None:
        return "Invalidation cannot be set until support/risk levels are refreshed."
    return f"Invalidate the constructive setup if price closes below {level} or refreshed evidence contradicts the thesis."


def exit_condition(level: float | None) -> str:
    if level is None:
        return "Risk-control review is required because no usable level is available."
    return f"Review reduction or exit if price closes below {level}, especially when weekly status also deteriorates."


def summarize_setup_quality(technical: dict[str, Any] | None, missing_data: list[str]) -> str:
    if not technical:
        return "source_gap"
    overall = (technical.get("cross_timeframe_summary") or {}).get("overall_status")
    if missing_data:
        return f"{overall}_with_source_gaps"
    return str(overall or "unknown")


def summarize_primary_evidence(technical: dict[str, Any] | None) -> list[str]:
    if not technical:
        return ["No technical_analysis is available; decision support should wait for sourced market data."]
    cross = technical.get("cross_timeframe_summary") or {}
    daily = technical.get("daily") or {}
    evidence = [
        f"technical_analysis overall_status={cross.get('overall_status')} and alignment={cross.get('alignment')}.",
        f"Daily status={daily.get('status')} with trend summary: {(daily.get('moving_averages') or {}).get('trend_summary')}.",
    ]
    volume = ((daily.get("volume_price") or {}).get("volume_confirmation"))
    if volume:
        evidence.append(f"Volume confirmation state: {volume}.")
    return evidence


def summarize_prediction_market_evidence(context: dict[str, Any] | None) -> list[str]:
    if not isinstance(context, dict) or context.get("status") != "available":
        return []
    markets = context.get("selected_markets")
    if not isinstance(markets, list) or not markets:
        return []
    evidence: list[str] = []
    for market in markets[:3]:
        if not isinstance(market, dict):
            continue
        question = market.get("question") or market.get("slug") or "unknown market"
        tier = market.get("relevance_tier") or "unknown_relevance"
        probability = format_probability(market.get("implied_probability"))
        change = market.get("change") if isinstance(market.get("change"), dict) else {}
        delta_text = format_delta(change.get("probability_delta"))
        evidence.append(
            "Polymarket auxiliary evidence "
            f"({tier}): {question}; top_outcome={market.get('top_outcome') or 'N/A'}, "
            f"implied_probability={probability}, local_probability_delta={delta_text}."
        )
    return evidence


def prediction_market_counterpoints(context: dict[str, Any] | None) -> list[str]:
    if not isinstance(context, dict):
        return ["Polymarket macro/strongly-linked context is missing from this record."]
    status = context.get("status")
    if status == "available":
        limitations = context.get("limitations")
        if isinstance(limitations, list) and limitations:
            return [f"Polymarket limitation: {limitations[0]}"]
        return []
    if status == "no_related_markets":
        return ["No macro or strongly related Polymarket market passed the relevance filter."]
    if status == "source_gap":
        return ["Polymarket macro/strongly-linked evidence is unavailable and should be treated as a source gap."]
    return [f"Polymarket context has unknown status={status}."]


def prediction_market_gaps(context: dict[str, Any] | None) -> list[str]:
    if not isinstance(context, dict):
        return ["prediction_market_context missing"]
    status = context.get("status")
    if status == "available":
        return []
    if status == "no_related_markets":
        return ["No macro or strongly related Polymarket markets were found."]
    if status == "source_gap":
        limitations = context.get("limitations")
        if isinstance(limitations, list) and limitations:
            return [f"Polymarket source gap: {limitations[0]}"]
        return ["Polymarket source gap"]
    return [f"Polymarket status is not recognized: {status}"]


def confidence_reason(
    technical: dict[str, Any] | None,
    missing_data: list[str],
    prediction_market_context: dict[str, Any],
) -> str:
    base = "Technical analysis is included." if technical else "Technical analysis is unavailable."
    if missing_data:
        base += " Non-technical source gaps limit confidence."
    status = prediction_market_context.get("status")
    if status == "available":
        return base + " Polymarket macro/strongly-linked event probabilities are available as auxiliary evidence only."
    if status == "no_related_markets":
        return base + " No related Polymarket macro/event market was found, so confidence does not benefit from this evidence layer."
    return base + " Polymarket macro/event evidence is a disclosed source gap."


def confidence_bucket(technical: dict[str, Any] | None, missing_data: list[str]) -> str:
    if not technical:
        return "low"
    if missing_data:
        return "low_to_medium"
    alignment = (technical.get("cross_timeframe_summary") or {}).get("alignment")
    return "medium" if alignment in {"constructive_alignment", "deteriorating_alignment"} else "low_to_medium"


def format_probability(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    return "N/A"


def format_delta(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:+.2f}pp"
    return "N/A"
