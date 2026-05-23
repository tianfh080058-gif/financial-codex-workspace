"""Shared helpers for trading_core."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = PROJECT_ROOT / ".research"
VIBE_VENDOR_ROOT = PROJECT_ROOT / "vendor" / "vibe-trading"
VIBE_SNAPSHOT_COMMIT = "a74bca22c1a415c5cd4e6bda6d01e77c7e1746e9"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
