#!/usr/bin/env python3
"""Fetch A-share financial indicators through AKShare without silent empty pulls."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


SINA_FINANCIAL_GUIDELINE_URL = (
    "https://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/"
    "stockid/{symbol}/ctrl/{year}/displaytype/4.phtml"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("status") != "fail" else 1


def normalize_sina_symbol(symbol: str) -> str:
    value = symbol.strip()
    upper = value.upper()

    if re.fullmatch(r"[A-Z]{2}\d{6}", upper):
        value = upper[2:]
    elif re.fullmatch(r"\d{6}\.[A-Z]{2}", upper):
        value = upper.split(".", 1)[0]

    if not re.fullmatch(r"\d{6}", value):
        raise ValueError(
            "symbol must be a 6-digit A-share code or a common form like 300308.SZ, SZ300308, SH600519"
        )
    return value


def fetch_sina_years(symbol: str, timeout: float) -> tuple[list[str], str]:
    url = SINA_FINANCIAL_GUIDELINE_URL.format(symbol=symbol, year="2020")
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, features="lxml")
    container = soup.find(attrs={"id": "con02-1"})
    if container is None:
        raise RuntimeError("Sina financial guideline page did not contain id='con02-1'")

    table = container.find("table")
    if table is None:
        raise RuntimeError("Sina financial guideline page did not contain the year selector table")

    years = []
    for item in table.find_all("a"):
        text = item.text.strip()
        if re.fullmatch(r"\d{4}", text):
            years.append(text)

    if not years:
        raise RuntimeError("No reporting years were found on the Sina financial guideline page")
    return years, url


def resolve_start_year(requested: str | None, available_years: list[str]) -> str:
    if not requested or requested in {"auto", "oldest", "all"}:
        return available_years[-1]
    if requested == "latest":
        return available_years[0]
    if requested not in available_years:
        raise ValueError(
            f"start_year={requested!r} is not available. Available years: {', '.join(available_years)}"
        )
    return requested


def dataframe_preview(df: Any, limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return json.loads(df.head(limit).to_json(orient="records", force_ascii=False, date_format="iso"))


def command_fetch(args: argparse.Namespace) -> int:
    try:
        import akshare as ak  # type: ignore[import-not-found]
    except ImportError as exc:
        return emit(
            {
                "status": "fail",
                "retrieved_at_utc": utc_now(),
                "error_type": type(exc).__name__,
                "error": "AKShare is not installed in this Python environment.",
            }
        )

    requested_symbol = args.symbol
    normalized_symbol = normalize_sina_symbol(requested_symbol)

    try:
        available_years, discovery_url = fetch_sina_years(normalized_symbol, timeout=args.timeout)
        resolved_start_year = resolve_start_year(args.start_year, available_years)
        akshare_log_buffer = io.StringIO()
        with contextlib.redirect_stdout(akshare_log_buffer), contextlib.redirect_stderr(akshare_log_buffer):
            df = ak.stock_financial_analysis_indicator(symbol=normalized_symbol, start_year=resolved_start_year)
        akshare_logs = akshare_log_buffer.getvalue().strip()
    except Exception as exc:  # noqa: BLE001 - CLI should preserve the failure class in JSON.
        return emit(
            {
                "status": "fail",
                "retrieved_at_utc": utc_now(),
                "akshare_version": getattr(ak, "__version__", "unknown"),
                "interface": "stock_financial_analysis_indicator",
                "upstream": "Sina Finance",
                "requested_symbol": requested_symbol,
                "normalized_symbol": normalized_symbol,
                "requested_start_year": args.start_year,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )

    if df.empty:
        return emit(
            {
                "status": "fail",
                "retrieved_at_utc": utc_now(),
                "akshare_version": getattr(ak, "__version__", "unknown"),
                "interface": "stock_financial_analysis_indicator",
                "upstream": "Sina Finance",
                "requested_symbol": requested_symbol,
                "normalized_symbol": normalized_symbol,
                "requested_start_year": args.start_year,
                "resolved_start_year": resolved_start_year,
                "available_years": available_years,
                "source_url": discovery_url,
                "row_count": 0,
                "column_count": 0,
                "error": "AKShare returned an empty DataFrame after resolving a valid start_year.",
            }
        )

    output_csv = None
    if args.output_csv:
        output_path = Path(args.output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        output_csv = str(output_path)

    date_values = df["日期"].dropna() if "日期" in df.columns else []
    result = {
        "status": "ok",
        "retrieved_at_utc": utc_now(),
        "akshare_version": getattr(ak, "__version__", "unknown"),
        "interface": "stock_financial_analysis_indicator",
        "upstream": "Sina Finance",
        "requested_symbol": requested_symbol,
        "normalized_symbol": normalized_symbol,
        "requested_start_year": args.start_year,
        "resolved_start_year": resolved_start_year,
        "available_years": available_years,
        "source_url": discovery_url,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [str(column) for column in df.columns],
        "first_period": str(date_values.min()) if len(date_values) else None,
        "latest_period": str(date_values.max()) if len(date_values) else None,
        "output_csv": output_csv,
        "records_preview": dataframe_preview(df, args.preview_rows),
        "akshare_logs_suppressed": bool(akshare_logs),
        "qa_status": {
            "symbol_normalized": True,
            "available_years_checked": True,
            "start_year_resolved": True,
            "non_empty_dataframe": True,
            "silent_1900_default_avoided": True,
        },
        "source_limitations": [
            "This uses AKShare's Sina Finance financial-indicator page scraper, not iFinD.",
            "Sina page structure changes can break parsing; cross-check important financials with filings or iFinD.",
        ],
    }
    return emit(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch A-share financial indicators via AKShare's Sina interface while "
            "auto-resolving start_year to avoid the upstream default empty DataFrame."
        )
    )
    parser.add_argument("--symbol", required=True, help="A-share code, e.g. 300308, 300308.SZ, or SZ300308")
    parser.add_argument(
        "--start-year",
        default="oldest",
        help="Reporting year to start from; use oldest/all/auto, latest, or an explicit year such as 2025",
    )
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")
    parser.add_argument("--preview-rows", type=int, default=3, help="Rows to include in JSON preview")
    parser.add_argument("--output-csv", help="Optional path to write the full DataFrame as CSV")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return command_fetch(args)
    except ValueError as exc:
        return emit({"status": "fail", "retrieved_at_utc": utc_now(), "error_type": "ValueError", "error": str(exc)})


if __name__ == "__main__":
    sys.exit(main())
