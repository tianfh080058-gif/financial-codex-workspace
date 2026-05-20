#!/usr/bin/env python3
"""Create post-review checklists for decision-support JSONL records."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_HORIZONS = {5, 20, 60}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: JSONL records must be objects")
        records.append(value)
    return records


def mode_value(record: dict[str, Any]) -> str | None:
    value = record.get("analysis_mode")
    if isinstance(value, dict):
        value = value.get("mode")
    return value if isinstance(value, str) else None


def decision_support_value(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("decision_support")
    return value if isinstance(value, dict) else {}


def ticker_value(record: dict[str, Any]) -> str | None:
    ticker = record.get("ticker")
    if isinstance(ticker, str):
        return ticker
    security = record.get("security_master")
    if isinstance(security, dict) and isinstance(security.get("ticker"), str):
        return security["ticker"]
    return None


def summarize_record(record: dict[str, Any], horizon: int) -> dict[str, Any]:
    decision = decision_support_value(record)
    return {
        "record_id": record.get("run_id") or record.get("record_id") or record.get("_stored_at_utc"),
        "ticker": ticker_value(record),
        "created_at": record.get("created_at") or record.get("_stored_at_utc"),
        "review_horizon_trading_days": horizon,
        "decision_state": decision.get("decision_state"),
        "confidence": decision.get("confidence"),
        "review_status": "requires_refreshed_market_and_thesis_data",
        "review_checklist": {
            "supporting_evidence_to_recheck": decision.get("supporting_evidence") or [],
            "disconfirming_evidence_to_recheck": decision.get("disconfirming_evidence") or [],
            "trigger_conditions_to_check": decision.get("trigger_conditions") or [],
            "invalidation_conditions_to_check": decision.get("invalidation_conditions") or [],
            "risk_controls_to_check": decision.get("risk_controls") or [],
        },
        "missing_for_outcome_review": [
            "refreshed market data for the horizon",
            "updated filings or announcements",
            "updated thesis evidence and disconfirming evidence",
        ],
        "guardrail": "No buy/sell advice, target price, personal position sizing, or return promise is produced.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Review historical decision-support records without trade advice.")
    parser.add_argument("--input", required=True, help="Decision-support JSONL file")
    parser.add_argument("--horizon", type=int, default=20, choices=sorted(ALLOWED_HORIZONS))
    parser.add_argument("--ticker", help="Optional ticker filter")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    try:
        records = read_jsonl(Path(args.input))
        decision_records = []
        for record in records:
            if mode_value(record) != "decision_support":
                continue
            if args.ticker and ticker_value(record) != args.ticker:
                continue
            decision_records.append(record)
        if args.limit >= 0:
            decision_records = decision_records[-args.limit :]
        reviews = [summarize_record(record, args.horizon) for record in decision_records]
        result = {
            "status": "ok",
            "reviewed_at": utc_now(),
            "input": args.input,
            "horizon_trading_days": args.horizon,
            "record_count": len(reviews),
            "reviews": reviews,
            "not_investment_advice": True,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
