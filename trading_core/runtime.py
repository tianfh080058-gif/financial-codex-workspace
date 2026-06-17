"""Runtime models shared by workflow routing, CLI, and executors."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .common import RESEARCH_ROOT


DEFAULT_WATCHLIST = RESEARCH_ROOT / "watchlists" / "default.json"
DEFAULT_ALERTS = RESEARCH_ROOT / "alerts" / "alerts.jsonl"


@dataclass
class MissingInput:
    field: str
    question: str

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "question": self.question}


@dataclass
class ArtifactPolicy:
    store: bool = False
    legacy_default_write: bool = False
    output_path: Path | None = None


@dataclass
class WorkflowContext:
    intent: str = ""
    command: str = "run"
    action: str | None = None
    ticker: str | None = None
    query: str | None = None
    file: Path | None = None
    watchlist: Path = DEFAULT_WATCHLIST
    alerts_file: Path = DEFAULT_ALERTS
    horizon: str = "20d"
    review_date: str | None = None
    market: str = "a_share"
    mode: str = "conditional_strong"
    dry_run: bool = False
    artifact_policy: ArtifactPolicy = field(default_factory=ArtifactPolicy)
    strategy: str | None = None
    start: str | None = None
    end: str | None = None
    source: str = "auto"
    run_vibe: bool = False
    universe: str | None = None
    zoo: str | None = None
    period: str | None = None
    ohlcv: Path | None = None
    backtest_ohlcv: Path | None = None
    adjustment_basis: str = "unknown"
    skip_polymarket: bool = False
    polymarket_query: list[str] | None = None
    polymarket_lookback_days: int = 7
    polymarket_max_markets: int = 5
    watchlist_payload: dict[str, Any] = field(default_factory=dict)
    alert_payload: dict[str, Any] = field(default_factory=dict)
    output_format: str = "markdown"


@dataclass
class IntentRoute:
    workflow_id: str
    scenario_id: str
    executor: str
    confidence: float
    matched_terms: list[str]
    recipe: dict[str, Any]


@dataclass
class WorkflowResult:
    status: str
    display_kind: str
    machine_record: dict[str, Any] | None = None
    display_card: str | None = None
    missing_inputs: list[MissingInput] = field(default_factory=list)
    exit_code: int = 0

    def missing_as_dicts(self) -> list[dict[str, str]]:
        return [item.to_dict() for item in self.missing_inputs]
