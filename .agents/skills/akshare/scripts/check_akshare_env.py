#!/usr/bin/env python3
"""Check whether AKShare is available in the current Python environment."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone


def main() -> int:
    result: dict[str, object] = {
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "akshare_installed": False,
        "akshare_version": None,
        "status": "missing",
    }

    spec = importlib.util.find_spec("akshare")
    if spec is None:
        result["message"] = "AKShare is not installed in this Python environment."
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    import akshare as ak  # type: ignore[import-not-found]

    result.update(
        {
            "akshare_installed": True,
            "akshare_version": getattr(ak, "__version__", "unknown"),
            "status": "ok",
            "message": "AKShare import succeeded.",
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
