"""Shared workflow helper functions."""

from __future__ import annotations

from typing import Any


def rebase_source_refs(context: dict[str, Any], offset: int) -> None:
    """Adjust provider-local source_log refs after appending to a record log."""

    def rebase(value: Any) -> Any:
        if not isinstance(value, str) or not value.startswith("source_log[") or not value.endswith("]"):
            return value
        try:
            index = int(value[len("source_log[") : -1])
        except ValueError:
            return value
        return f"source_log[{index + offset}]"

    refs = context.get("source_ref")
    if isinstance(refs, list):
        context["source_ref"] = [rebase(ref) for ref in refs]
    markets = context.get("selected_markets")
    if isinstance(markets, list):
        for market in markets:
            if isinstance(market, dict) and isinstance(market.get("source_ref"), list):
                market["source_ref"] = [rebase(ref) for ref in market["source_ref"]]
