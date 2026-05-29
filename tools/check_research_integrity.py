#!/usr/bin/env python3
"""Validate productized A-share research schema records."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_MODES = {"research", "decision_support"}
ALLOWED_GENERAL_MODES = {
    "research",
    "decision_support",
    "journal_review",
    "backtest_validation",
    "alpha_bench",
}
ALLOWED_DECISION_STATES = {
    "watch_only",
    "research_candidate",
    "hold_monitor",
    "risk_control_review",
    "avoid_or_wait",
}
ALLOWED_TECHNICAL_STATUSES = {
    "constructive",
    "neutral",
    "deteriorating",
    "mixed",
    "insufficient_data",
}
TECHNICAL_TIMEFRAMES = ("daily", "weekly", "monthly")
FORBIDDEN_KEYS = {
    "target_price",
    "price_target",
    "rating",
    "buy_rating",
    "sell_rating",
    "buy_signal",
    "sell_signal",
    "entry_price",
    "take_profit",
    "stop_loss",
    "position_size",
    "position_sizing",
    "return_promise",
}
CONDITIONAL_TRADE_PLAN_FIELDS = {
    "action_type",
    "trigger_level",
    "trigger_condition",
    "invalidation_level",
    "risk_control_level",
    "exit_or_reduce_condition",
    "time_validity",
    "source_ref",
    "assumptions",
}
ALLOWED_CONDITIONAL_ACTION_TYPES = {
    "conditional_watch",
    "conditional_entry_review",
    "conditional_hold_monitor",
    "conditional_reduce_or_exit_review",
    "conditional_avoid_or_wait",
}
FORBIDDEN_PHRASES = {
    "目标价",
    "买入评级",
    "卖出评级",
    "建议买入",
    "建议卖出",
    "买入信号",
    "卖出信号",
    "开仓",
    "止盈",
    "止损",
    "个性化仓位",
    "收益承诺",
}
UNCONDITIONAL_TRADE_PHRASES = {
    "立即买入",
    "马上买入",
    "现在买入",
    "直接买入",
    "立即卖出",
    "马上卖出",
    "现在卖出",
    "直接卖出",
    "全仓",
    "满仓",
    "梭哈",
}
TECHNICAL_REFERENCE_TERMS = (
    "technical",
    "技术",
    "日线",
    "周线",
    "月线",
    "MA",
    "均线",
    "MACD",
    "RSI",
    "Bollinger",
    "布林",
    "量价",
    "相对强弱",
)
ALLOWED_PREDICTION_MARKET_STATUSES = {"available", "no_related_markets", "source_gap"}
ALLOWED_PREDICTION_RELEVANCE_TIERS = {"macro_regime", "sector_linked", "ticker_or_company_linked"}
PREDICTION_MARKET_DETERMINISTIC_PHRASES = {
    "确定会",
    "必然会",
    "一定会",
    "guaranteed",
    "certain to",
    "must happen",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_record(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Input JSON must be an object")
    return value


def mode_value(record: dict[str, Any]) -> str | None:
    value = record.get("analysis_mode")
    if isinstance(value, dict):
        value = value.get("mode")
    return value if isinstance(value, str) else None


def has_text(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value
    if isinstance(value, dict):
        return any(has_text(item, needle) for item in value.values())
    if isinstance(value, list):
        return any(has_text(item, needle) for item in value)
    return False


def find_forbidden(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_KEYS:
                findings.append(f"{path}.{key_text}: forbidden key")
            for phrase in FORBIDDEN_PHRASES:
                if phrase in key_text:
                    findings.append(f"{path}.{key_text}: forbidden phrase in key")
            findings.extend(find_forbidden(item, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(find_forbidden(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        for phrase in FORBIDDEN_PHRASES:
            if phrase in value:
                findings.append(f"{path}: forbidden phrase {phrase!r}")
        for phrase in UNCONDITIONAL_TRADE_PHRASES:
            if phrase in value:
                findings.append(f"{path}: unconditional trade phrase {phrase!r}")
    return findings


def non_empty_list(record: dict[str, Any], key: str) -> bool:
    value = record.get(key)
    return isinstance(value, list) and len(value) > 0


def nested_non_empty_list(record: dict[str, Any], object_key: str, field_key: str) -> bool:
    value = record.get(object_key)
    if not isinstance(value, dict):
        return False
    return non_empty_list(value, field_key)


def technical_timeframes_present(record: dict[str, Any]) -> bool:
    technical = record.get("technical_analysis")
    return isinstance(technical, dict) and all(isinstance(technical.get(name), dict) for name in TECHNICAL_TIMEFRAMES)


def decision_support_references_technical(record: dict[str, Any]) -> bool:
    decision = record.get("decision_support")
    if not isinstance(decision, dict):
        return False
    fields = {
        key: decision.get(key)
        for key in (
            "supporting_evidence",
            "disconfirming_evidence",
            "trigger_conditions",
            "invalidation_conditions",
            "risk_controls",
            "confidence_reason",
        )
    }
    return any(has_text(fields, term) for term in TECHNICAL_REFERENCE_TERMS)


def not_investment_advice_present(record: dict[str, Any]) -> bool:
    if record.get("not_investment_advice") is True:
        return True
    qa_status = record.get("qa_status")
    if isinstance(qa_status, dict) and qa_status.get("not_investment_advice_included") is True:
        return True
    return has_text(record, "Not investment advice")


def validate_source_log(record: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    source_log = record.get("source_log")
    if not isinstance(source_log, list) or not source_log:
        errors.append("source_log must be a non-empty list")
        return
    for index, entry in enumerate(source_log):
        if not isinstance(entry, dict):
            errors.append(f"source_log[{index}] must be an object")
            continue
        if not entry.get("source_name"):
            errors.append(f"source_log[{index}].source_name is required")
        if not entry.get("retrieved_at"):
            warnings.append(f"source_log[{index}].retrieved_at is missing")
        if not entry.get("endpoint_or_interface"):
            warnings.append(f"source_log[{index}].endpoint_or_interface is missing")


def qa_status_present(record: dict[str, Any]) -> bool:
    return isinstance(record.get("qa_status"), dict) or isinstance(record.get("report_integrity_status"), dict)


def artifact_refs_present(record: dict[str, Any]) -> bool:
    return isinstance(record.get("artifact_refs"), dict) or isinstance(record.get("artifact_paths"), (dict, list))


def validate_market_snapshot(record: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    market = record.get("market_snapshot")
    if market is None:
        warnings.append("market_snapshot is missing; market checks were skipped")
        return
    if not isinstance(market, dict):
        errors.append("market_snapshot must be an object")
        return
    if not market.get("trade_date"):
        errors.append("market_snapshot.trade_date is required")
    if not market.get("retrieved_at"):
        errors.append("market_snapshot.retrieved_at is required")

    price = market.get("price")
    if not isinstance(price, dict):
        errors.append("market_snapshot.price must be an object")
    else:
        if not price.get("adjustment_basis"):
            errors.append("market_snapshot.price.adjustment_basis is required")
        if not (price.get("currency") or price.get("unit")):
            errors.append("market_snapshot.price.currency or unit is required")

    liquidity = market.get("liquidity")
    market_cap = market.get("market_cap")
    has_unit = False
    if isinstance(liquidity, dict):
        has_unit = has_unit or bool(liquidity.get("volume_unit") or liquidity.get("turnover_amount_unit"))
    if isinstance(market_cap, dict):
        has_unit = has_unit or bool(market_cap.get("unit"))
    if not has_unit:
        warnings.append("market_snapshot has no liquidity or market-cap unit")


def validate_technical_analysis(record: dict[str, Any], mode: str | None, errors: list[str], warnings: list[str]) -> None:
    technical = record.get("technical_analysis")
    market = record.get("market_snapshot")
    required = mode == "decision_support" or (mode == "research" and isinstance(market, dict))

    if technical is None:
        if required:
            errors.append("technical_analysis is required for single-stock research with market data and decision_support mode")
        return
    if not isinstance(technical, dict):
        errors.append("technical_analysis must be an object")
        return

    for field in ("trade_date", "retrieved_at", "adjustment_basis", "calculation_basis"):
        if not technical.get(field):
            errors.append(f"technical_analysis.{field} is required")

    source_ref = technical.get("source_ref")
    if not isinstance(source_ref, list) or not source_ref:
        errors.append("technical_analysis.source_ref must be a non-empty list")

    for timeframe in TECHNICAL_TIMEFRAMES:
        period = technical.get(timeframe)
        if not isinstance(period, dict):
            errors.append(f"technical_analysis.{timeframe} must be an object")
            continue
        status = period.get("status")
        if status not in ALLOWED_TECHNICAL_STATUSES:
            errors.append(
                f"technical_analysis.{timeframe}.status must be one of {sorted(ALLOWED_TECHNICAL_STATUSES)}"
            )
        if not period.get("calculation_basis"):
            errors.append(f"technical_analysis.{timeframe}.calculation_basis is required")
        if period.get("bar_count") in (0, None) and status != "insufficient_data":
            warnings.append(f"technical_analysis.{timeframe} has no bar_count but status is not insufficient_data")

    monthly = technical.get("monthly")
    if isinstance(monthly, dict):
        for field in ("long_term_ma_direction", "trend_summary", "long_term_drawdown_position"):
            if field not in monthly:
                warnings.append(f"technical_analysis.monthly.{field} is missing")


def validate_decision_support(record: dict[str, Any], errors: list[str]) -> None:
    decision = record.get("decision_support")
    if not isinstance(decision, dict):
        errors.append("decision_support mode requires decision_support object")
        return
    state = decision.get("decision_state")
    if state not in ALLOWED_DECISION_STATES:
        errors.append(f"decision_support.decision_state must be one of {sorted(ALLOWED_DECISION_STATES)}")
    for field in (
        "supporting_evidence",
        "disconfirming_evidence",
        "trigger_conditions",
        "invalidation_conditions",
        "risk_controls",
    ):
        if not nested_non_empty_list(record, "decision_support", field):
            errors.append(f"decision_support.{field} must be a non-empty list")
    if not decision.get("confidence"):
        errors.append("decision_support.confidence is required")


def source_log_has_polymarket(record: dict[str, Any]) -> bool:
    source_log = record.get("source_log")
    if not isinstance(source_log, list):
        return False
    for entry in source_log:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("source_name", "")).lower()
        endpoint = str(entry.get("endpoint_or_interface", ""))
        params = entry.get("parameters")
        if "polymarket" in name and endpoint and isinstance(params, dict):
            return True
    return False


def has_deterministic_prediction_language(value: Any) -> bool:
    if isinstance(value, str):
        lower = value.lower()
        return any(phrase in value or phrase in lower for phrase in PREDICTION_MARKET_DETERMINISTIC_PHRASES)
    if isinstance(value, dict):
        return any(has_deterministic_prediction_language(item) for item in value.values())
    if isinstance(value, list):
        return any(has_deterministic_prediction_language(item) for item in value)
    return False


def validate_prediction_market_context(
    record: dict[str, Any],
    mode: str | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    if mode != "decision_support":
        return
    context = record.get("prediction_market_context")
    if not isinstance(context, dict):
        errors.append("decision_support mode requires prediction_market_context object")
        return
    status = context.get("status")
    if status not in ALLOWED_PREDICTION_MARKET_STATUSES:
        errors.append(f"prediction_market_context.status must be one of {sorted(ALLOWED_PREDICTION_MARKET_STATUSES)}")
    if not context.get("retrieved_at"):
        errors.append("prediction_market_context.retrieved_at is required")
    if not isinstance(context.get("query_terms"), list):
        errors.append("prediction_market_context.query_terms must be a list")
    markets = context.get("selected_markets")
    if not isinstance(markets, list):
        errors.append("prediction_market_context.selected_markets must be a list")
        return
    if status == "available" and not markets:
        errors.append("prediction_market_context.selected_markets must be non-empty when status is available")
    if status in {"no_related_markets", "source_gap"} and markets:
        warnings.append("prediction_market_context has selected_markets despite non-available status")
    if status == "available" and not source_log_has_polymarket(record):
        errors.append("available prediction_market_context requires a Polymarket source_log entry with endpoint and query parameters")
    if has_deterministic_prediction_language(context):
        errors.append("prediction_market_context must not present probabilities as deterministic forecasts")

    for index, market in enumerate(markets):
        if not isinstance(market, dict):
            errors.append(f"prediction_market_context.selected_markets[{index}] must be an object")
            continue
        tier = market.get("relevance_tier")
        if tier not in ALLOWED_PREDICTION_RELEVANCE_TIERS:
            errors.append(
                f"prediction_market_context.selected_markets[{index}].relevance_tier must be one of {sorted(ALLOWED_PREDICTION_RELEVANCE_TIERS)}"
            )
        if market.get("implied_probability") is None:
            warnings.append(f"prediction_market_context.selected_markets[{index}].implied_probability is missing")
        if not market.get("source_ref"):
            warnings.append(f"prediction_market_context.selected_markets[{index}].source_ref is missing")


def validate_conditional_trade_plan(record: dict[str, Any], mode: str | None, errors: list[str], warnings: list[str]) -> None:
    plan = record.get("conditional_trade_plan")
    if plan is None:
        if mode == "decision_support":
            warnings.append("conditional_trade_plan is missing; decision output has no conditional levels")
        return
    if mode != "decision_support":
        errors.append("conditional_trade_plan is only allowed in decision_support mode")
        return
    if not isinstance(plan, dict):
        errors.append("conditional_trade_plan must be an object")
        return
    missing = sorted(field for field in CONDITIONAL_TRADE_PLAN_FIELDS if field not in plan)
    if missing:
        errors.append(f"conditional_trade_plan missing fields: {', '.join(missing)}")
    action_type = plan.get("action_type")
    if action_type not in ALLOWED_CONDITIONAL_ACTION_TYPES:
        errors.append(
            f"conditional_trade_plan.action_type must be one of {sorted(ALLOWED_CONDITIONAL_ACTION_TYPES)}"
        )
    for level_field in ("trigger_level", "invalidation_level", "risk_control_level"):
        level = plan.get(level_field)
        if not isinstance(level, dict):
            errors.append(f"conditional_trade_plan.{level_field} must be an object")
            continue
        if "value" not in level:
            errors.append(f"conditional_trade_plan.{level_field}.value is required, use null when unavailable")
        if level.get("is_target_price") is True:
            errors.append(f"conditional_trade_plan.{level_field} must not be marked as target price")
        if not level.get("derivation"):
            warnings.append(f"conditional_trade_plan.{level_field}.derivation is missing")
    for text_field in ("trigger_condition", "exit_or_reduce_condition", "time_validity"):
        if not plan.get(text_field):
            errors.append(f"conditional_trade_plan.{text_field} is required")
    source_ref = plan.get("source_ref")
    if not isinstance(source_ref, list) or not source_ref:
        errors.append("conditional_trade_plan.source_ref must be a non-empty list")
    assumptions = plan.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        warnings.append("conditional_trade_plan.assumptions should be a non-empty list")


def validate_general_finance_record(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    mode = mode_value(record)
    if mode is not None and mode not in ALLOWED_GENERAL_MODES:
        errors.append(f"analysis_mode must be one of {sorted(ALLOWED_GENERAL_MODES)} when present")

    validate_source_log(record, errors, warnings)

    if not qa_status_present(record):
        errors.append("qa_status or report_integrity_status must be present")

    if not not_investment_advice_present(record):
        errors.append("Not investment advice must be present")

    if not artifact_refs_present(record):
        warnings.append("artifact_refs or artifact_paths is missing; stored output may be hard to audit")

    forbidden = find_forbidden(record)
    if forbidden:
        errors.extend(forbidden)

    status = "pass" if not errors else "fail"
    return {
        "status": status,
        "profile": "general_finance",
        "checked_at": utc_now(),
        "errors": errors,
        "warnings": warnings,
        "report_integrity_status": {
            "status": status,
            "checked_at": utc_now(),
            "required_checks": {
                "source_log_present": isinstance(record.get("source_log"), list) and bool(record.get("source_log")),
                "qa_status_present": qa_status_present(record),
                "not_investment_advice_present": not_investment_advice_present(record),
                "artifact_refs_present": artifact_refs_present(record),
            },
            "mode_checks": {
                "unsupported_outputs_blocked": not forbidden,
            },
            "errors": errors,
            "warnings": warnings,
        },
    }


def validate_journal_shadow_record(record: dict[str, Any]) -> dict[str, Any]:
    result = validate_general_finance_record(record)
    errors = result["errors"]
    warnings = result["warnings"]

    if not isinstance(record.get("profile"), dict):
        errors.append("profile must be present for journal_shadow profile")
    if not isinstance(record.get("behavior_diagnostics"), dict):
        errors.append("behavior_diagnostics must be present for journal_shadow profile")
    if not isinstance(record.get("shadow_account_profile"), dict):
        errors.append("shadow_account_profile must be present for journal_shadow profile")
    if record.get("trade_count") is None and not isinstance(record.get("profile"), dict):
        warnings.append("trade_count is missing")

    status = "pass" if not errors else "fail"
    result["status"] = status
    result["profile"] = "journal_shadow"
    result["report_integrity_status"]["status"] = status
    result["report_integrity_status"]["errors"] = errors
    result["report_integrity_status"]["warnings"] = warnings
    result["report_integrity_status"]["required_checks"].update(
        {
            "journal_profile_present": isinstance(record.get("profile"), dict),
            "behavior_diagnostics_present": isinstance(record.get("behavior_diagnostics"), dict),
            "shadow_account_profile_present": isinstance(record.get("shadow_account_profile"), dict),
        }
    )
    return result


def validate_a_share_decision_record(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    mode = mode_value(record)
    if mode not in ALLOWED_MODES:
        errors.append("analysis_mode.mode must be research or decision_support")

    validate_source_log(record, errors, warnings)

    validate_market_snapshot(record, errors, warnings)
    validate_technical_analysis(record, mode, errors, warnings)

    if not isinstance(record.get("qa_status"), dict):
        errors.append("qa_status must be present")

    if not not_investment_advice_present(record):
        errors.append("Not investment advice must be present")

    if mode == "research":
        decision = record.get("decision_support")
        if isinstance(decision, dict) and decision.get("decision_state"):
            errors.append("research mode must not include decision_support.decision_state")

    if mode == "decision_support":
        validate_decision_support(record, errors)
        if not decision_support_references_technical(record):
            errors.append(
                "decision_support must map technical_analysis into evidence, triggers, invalidation, or risk controls"
            )
        validate_prediction_market_context(record, mode, errors, warnings)

    validate_conditional_trade_plan(record, mode, errors, warnings)

    forbidden = find_forbidden(record)
    if forbidden:
        errors.extend(forbidden)

    status = "pass" if not errors else "fail"
    return {
        "status": status,
        "checked_at": utc_now(),
        "errors": errors,
        "warnings": warnings,
        "report_integrity_status": {
            "status": status,
            "checked_at": utc_now(),
            "required_checks": {
                "analysis_mode_present": mode in ALLOWED_MODES,
                "source_log_present": isinstance(record.get("source_log"), list) and bool(record.get("source_log")),
                "trade_date_present": bool((record.get("market_snapshot") or {}).get("trade_date"))
                if isinstance(record.get("market_snapshot"), dict)
                else False,
                "retrieved_at_present": bool((record.get("market_snapshot") or {}).get("retrieved_at"))
                if isinstance(record.get("market_snapshot"), dict)
                else False,
                "unit_present": "unit" not in " ".join(errors),
                "adjustment_basis_present": "adjustment_basis is required" not in " ".join(errors),
                "technical_analysis_present": isinstance(record.get("technical_analysis"), dict),
                "technical_analysis_timeframes_present": technical_timeframes_present(record),
                "prediction_market_context_present": isinstance(record.get("prediction_market_context"), dict),
                "qa_status_present": isinstance(record.get("qa_status"), dict),
                "not_investment_advice_present": not_investment_advice_present(record),
            },
            "mode_checks": {
                "research_has_no_decision_state": mode != "research"
                or "research mode must not include decision_support.decision_state" not in errors,
                "decision_support_has_required_evidence": mode != "decision_support"
                or not any(error.startswith("decision_support.") for error in errors),
                "decision_support_has_technical_evidence": mode != "decision_support"
                or decision_support_references_technical(record),
                "decision_support_has_prediction_market_context": mode != "decision_support"
                or isinstance(record.get("prediction_market_context"), dict),
                "unsupported_outputs_blocked": not forbidden,
            },
            "errors": errors,
            "warnings": warnings,
        },
    }


def validate_record(record: dict[str, Any], profile: str = "a_share_decision") -> dict[str, Any]:
    if profile == "general_finance":
        return validate_general_finance_record(record)
    if profile == "journal_shadow":
        return validate_journal_shadow_record(record)
    if profile == "a_share_decision":
        return validate_a_share_decision_record(record)
    raise ValueError(f"unknown integrity profile: {profile}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a financial research JSON record.")
    parser.add_argument("--input", required=True, help="Path to a JSON object")
    parser.add_argument(
        "--profile",
        default="a_share_decision",
        choices=["general_finance", "a_share_decision", "journal_shadow"],
        help="Integrity profile to apply",
    )
    args = parser.parse_args()

    try:
        record = load_record(Path(args.input))
        result = validate_record(record, args.profile)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "checked_at": utc_now(), "errors": [str(exc)], "warnings": []}

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
