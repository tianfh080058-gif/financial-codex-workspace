#!/usr/bin/env python3
"""Small JSONL store for local A-share research artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(".research")
SAFE_PART_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> int:
    print(json.dumps({"status": "fail", "error": message}, ensure_ascii=False, indent=2))
    return 1


def safe_part(value: str, label: str) -> str:
    if not value or any(char not in SAFE_PART_CHARS for char in value):
        raise ValueError(f"{label} must use only letters, digits, '.', '_', or '-'")
    if value in {".", ".."}:
        raise ValueError(f"{label} is not allowed")
    return value


def resolve_path(args: argparse.Namespace) -> Path:
    if getattr(args, "path", None):
        path = Path(args.path)
        if path.suffix != ".jsonl":
            raise ValueError("--path must point to a .jsonl file")
        return path

    root = Path(args.root)
    collection = safe_part(args.collection, "collection")
    stream = safe_part(args.stream, "stream")
    return root / collection / f"{stream}.jsonl"


def load_json_arg(record_json: str | None, record_file: str | None) -> Any:
    if record_json and record_file:
        raise ValueError("Use either --record-json or --record-file, not both")
    if record_json:
        return json.loads(record_json)
    if record_file:
        return json.loads(Path(record_file).read_text(encoding="utf-8"))
    raise ValueError("Provide --record-json or --record-file")


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: JSONL records must be objects")
        records.append(value)
    return records


def matches(record: dict[str, Any], args: argparse.Namespace) -> bool:
    ticker = getattr(args, "ticker", None)
    if ticker:
        tickers = record.get("tickers")
        record_ticker = record.get("ticker")
        if isinstance(tickers, list):
            if ticker not in tickers and not any(isinstance(item, dict) and item.get("ticker") == ticker for item in tickers):
                return False
        elif record_ticker != ticker:
            return False

    mode = getattr(args, "mode", None)
    if mode:
        analysis_mode = record.get("analysis_mode")
        record_mode = analysis_mode.get("mode") if isinstance(analysis_mode, dict) else analysis_mode
        if record_mode != mode:
            return False

    record_type = getattr(args, "record_type", None)
    if record_type and record.get("record_type") != record_type:
        return False

    return True


def command_append(args: argparse.Namespace) -> int:
    path = resolve_path(args)
    payload = load_json_arg(args.record_json, args.record_file)
    values = payload if isinstance(payload, list) else [payload]
    if not all(isinstance(value, dict) for value in values):
        return fail("append payload must be a JSON object or an array of objects")

    path.parent.mkdir(parents=True, exist_ok=True)
    stored_at = utc_now()
    with path.open("a", encoding="utf-8") as handle:
        for value in values:
            record = dict(value)
            record.setdefault("_stored_at_utc", stored_at)
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    print(
        json.dumps(
            {
                "status": "ok",
                "path": str(path),
                "records_appended": len(values),
                "stored_at_utc": stored_at,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def filtered_records(args: argparse.Namespace) -> tuple[Path, list[dict[str, Any]]]:
    path = resolve_path(args)
    records = [record for record in read_records(path) if matches(record, args)]
    limit = getattr(args, "limit", None)
    if limit is not None and limit >= 0:
        records = records[-limit:]
    return path, records


def command_list(args: argparse.Namespace) -> int:
    path, records = filtered_records(args)
    print(json.dumps({"status": "ok", "path": str(path), "records": records}, ensure_ascii=False, indent=2))
    return 0


def command_latest(args: argparse.Namespace) -> int:
    path, records = filtered_records(args)
    latest = records[-1] if records else None
    print(json.dumps({"status": "ok", "path": str(path), "latest": latest}, ensure_ascii=False, indent=2))
    return 0


def command_replay(args: argparse.Namespace) -> int:
    path, records = filtered_records(args)
    replay = []
    for index, record in enumerate(records, start=1):
        replay.append(
            {
                "sequence": index,
                "record_type": record.get("record_type"),
                "analysis_mode": record.get("analysis_mode"),
                "ticker": record.get("ticker"),
                "tickers": record.get("tickers"),
                "created_at": record.get("created_at") or record.get("_stored_at_utc"),
                "summary": record.get("summary"),
                "output_path": record.get("output_path"),
                "qa_status": record.get("qa_status"),
            }
        )
    print(json.dumps({"status": "ok", "path": str(path), "replay": replay}, ensure_ascii=False, indent=2))
    return 0


def add_common_read_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Research root directory")
    parser.add_argument("--collection", default="runs", help="Collection directory under root")
    parser.add_argument("--stream", default="default", help="JSONL stream name without suffix")
    parser.add_argument("--path", help="Explicit .jsonl path")
    parser.add_argument("--ticker", help="Filter by ticker")
    parser.add_argument("--mode", choices=["research", "decision_support"], help="Filter by analysis mode")
    parser.add_argument("--record-type", help="Filter by record_type")
    parser.add_argument("--limit", type=int, default=50, help="Maximum records to return")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and write local A-share research JSONL records.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append", help="Append one JSON object or an array of objects")
    append.add_argument("--root", default=str(DEFAULT_ROOT), help="Research root directory")
    append.add_argument("--collection", default="runs", help="Collection directory under root")
    append.add_argument("--stream", default="default", help="JSONL stream name without suffix")
    append.add_argument("--path", help="Explicit .jsonl path")
    append.add_argument("--record-json", help="JSON object or array to append")
    append.add_argument("--record-file", help="Path to JSON object or array to append")
    append.set_defaults(func=command_append)

    list_cmd = subparsers.add_parser("list", help="List records")
    add_common_read_args(list_cmd)
    list_cmd.set_defaults(func=command_list)

    latest = subparsers.add_parser("latest", help="Show latest matching record")
    add_common_read_args(latest)
    latest.set_defaults(func=command_latest)

    replay = subparsers.add_parser("replay", help="Summarize records in chronological order")
    add_common_read_args(replay)
    replay.set_defaults(func=command_replay)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
