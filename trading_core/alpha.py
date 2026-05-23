"""Alpha Zoo classification adapter."""

from __future__ import annotations

from typing import Any


ALPHA_ZOOS = {"alpha101", "gtja191", "qlib158", "academic"}


def classify_alpha(ic_mean: float | None, ic_positive_ratio: float | None, t_stat: float | None) -> str:
    if ic_mean is None or ic_positive_ratio is None or t_stat is None:
        return "insufficient_data"
    if ic_mean > 0.02 and ic_positive_ratio >= 0.55 and abs(t_stat) > 2:
        return "alive"
    if ic_mean < -0.02 and abs(t_stat) > 2:
        return "reversed"
    return "dead"


def alpha_bench_skeleton(universe: str, zoo: str, period: str) -> dict[str, Any]:
    if zoo not in ALPHA_ZOOS:
        return {
            "status": "fail",
            "error": f"unsupported zoo {zoo!r}; expected one of {sorted(ALPHA_ZOOS)}",
        }
    return {
        "status": "source_gap",
        "universe": universe,
        "zoo": zoo,
        "period": period,
        "classification_thresholds": {
            "alive": "ic_mean > 0.02, ic_positive_ratio >= 0.55, |t_stat| > 2",
            "reversed": "ic_mean < -0.02 and |t_stat| > 2",
            "dead": "otherwise",
        },
        "source_priority": ["iFinD OHLCV panel", "Vibe original loaders as fallback"],
        "missing_data": [
            "iFinD panel loader for this universe was not supplied in the command.",
            "No factor result is converted into a direct security-level trade recommendation.",
        ],
        "not_investment_advice": True,
    }
