"""Market data provider abstractions with iFinD-first routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from tools.calculate_technical_analysis import load_rows

from .common import utc_now
from .endpoint_registry import IFIND_ENDPOINT_REGISTRY
from .ifind_client import IfindHttpClient


@dataclass
class DataResponse:
    status: str
    data: Any = None
    source_log: list[dict[str, Any]] = field(default_factory=list)
    source_capability_matrix: list[dict[str, Any]] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class MarketDataProvider(Protocol):
    def get_security_master(self, ticker: str, market: str) -> DataResponse: ...
    def get_quote(self, ticker: str, market: str) -> DataResponse: ...
    def get_ohlcv(self, ticker: str, market: str, start: str | None, end: str | None, **kwargs: Any) -> DataResponse: ...
    def get_fundamentals(self, ticker: str, market: str) -> DataResponse: ...
    def get_valuation(self, ticker: str, market: str) -> DataResponse: ...
    def get_announcements(self, ticker: str, market: str) -> DataResponse: ...
    def get_trading_calendar(self, market: str, start: str, end: str) -> DataResponse: ...


class IfindFirstMarketDataProvider:
    """Provider that records iFinD priority and falls back only after a gap."""

    def __init__(self, ifind_client: IfindHttpClient | None = None) -> None:
        self.ifind_client = ifind_client or IfindHttpClient()

    def capability_matrix(self) -> list[dict[str, Any]]:
        checked_at = utc_now()
        credential_status = self.ifind_client.credential_status()
        return [
            {
                "source_name": "同花顺/iFinD HTTP API",
                "source_type": "licensed_data_tool",
                "priority": 1,
                "capabilities": sorted(IFIND_ENDPOINT_REGISTRY),
                "status": "available" if credential_status["access_token_found"] else "credential_gap",
                "last_checked_at": checked_at,
                "fallback_to": ["AKShare", "yfinance", "OKX/CCXT", "Vibe loader"],
                "limitations": [] if credential_status["access_token_found"] else ["iFinD access token not found."],
            },
            {
                "source_name": "AKShare/yfinance/OKX/CCXT/Vibe loader",
                "source_type": "fallback_public_or_upstream_loader",
                "priority": 2,
                "capabilities": ["public_market_data", "cross_check", "prototype_backtest_panel"],
                "status": "fallback_only",
                "last_checked_at": checked_at,
                "fallback_to": [],
                "limitations": ["Use only after iFinD is unavailable, unauthorized, missing fields, or failed."],
            },
        ]

    def _gap(self, method: str, ticker: str | None = None, reason: str | None = None) -> DataResponse:
        reason = reason or f"{method} adapter is not configured for this endpoint yet."
        return DataResponse(
            status="source_gap",
            data=None,
            source_capability_matrix=self.capability_matrix(),
            missing_data=[reason],
            source_log=[
                {
                    "source_name": "同花顺/iFinD HTTP API",
                    "source_type": "licensed_data_tool",
                    "endpoint_or_interface": method,
                    "parameters": {"ticker": ticker} if ticker else {},
                    "retrieved_at": utc_now(),
                    "status": "source_gap",
                    "limitations": [reason],
                }
            ],
        )

    def get_security_master(self, ticker: str, market: str) -> DataResponse:
        exchange = ticker.split(".")[-1] if "." in ticker else None
        return DataResponse(
            status="partial",
            data={
                "ticker": ticker,
                "exchange": exchange,
                "market": market,
                "currency": "CNY" if market == "a_share" else None,
                "identifier_status": "ticker_provided_by_user",
                "identifier_notes": ["Name, board, industry, and listing status require a refreshed security master pull."],
            },
            source_capability_matrix=self.capability_matrix(),
            missing_data=["security master details not fetched in this run"],
            source_log=[
                {
                    "source_name": "user_input",
                    "source_type": "user_provided_identifier",
                    "endpoint_or_interface": "ticker argument",
                    "parameters": {"ticker": ticker, "market": market},
                    "retrieved_at": utc_now(),
                    "status": "partial",
                    "limitations": ["Only ticker and market are known from user input."],
                }
            ],
        )

    def get_quote(self, ticker: str, market: str) -> DataResponse:
        if market != "a_share":
            return self._gap("real_time_quotation", ticker, f"quote retrieval is not configured for market={market}")
        ifind = self.ifind_client.request_raw(
            "real_time_quotation",
            {"codes": ticker, "indicators": "open,high,low,latest,volume,amount"},
        )
        quote = parse_ifind_quote(ifind.get("response"), ticker)
        if ifind.get("status") == "ok" and quote:
            return DataResponse(
                status="ok",
                data=quote,
                source_capability_matrix=self.capability_matrix(),
                source_log=[
                    {
                        "source_name": "同花顺/iFinD HTTP API",
                        "source_type": "licensed_data_tool",
                        "endpoint_or_interface": "real_time_quotation",
                        "parameters": {"codes": ticker, "indicators": "open,high,low,latest,volume,amount"},
                        "retrieved_at": utc_now(),
                        "trade_date": quote.get("trade_date"),
                        "fields": ["open", "high", "low", "latest", "volume", "amount"],
                        "status": "ok",
                        "limitations": [],
                    }
                ],
            )
        reason = ifind.get("missing") or ifind.get("error") or "iFinD returned no parseable quote"
        return DataResponse(
            status="source_gap",
            data=None,
            source_capability_matrix=self.capability_matrix(),
            missing_data=[str(reason)],
            source_log=[
                {
                    "source_name": "同花顺/iFinD HTTP API",
                    "source_type": "licensed_data_tool",
                    "endpoint_or_interface": "real_time_quotation",
                    "parameters": {"codes": ticker, "indicators": "open,high,low,latest,volume,amount"},
                    "retrieved_at": utc_now(),
                    "status": "source_gap",
                    "limitations": [str(reason)],
                }
            ],
        )

    def get_ohlcv(
        self,
        ticker: str,
        market: str,
        start: str | None,
        end: str | None,
        **kwargs: Any,
    ) -> DataResponse:
        local_path = kwargs.get("local_path")
        adjustment_basis = kwargs.get("adjustment_basis", "unknown")
        if local_path:
            path = Path(local_path)
            rows = load_rows(path)
            return DataResponse(
                status="ok",
                data=rows,
                source_capability_matrix=self.capability_matrix(),
                source_log=[
                    {
                        "source_name": "user_provided_ohlcv_file",
                        "source_type": "user_file",
                        "endpoint_or_interface": str(path),
                        "parameters": {
                            "ticker": ticker,
                            "market": market,
                            "adjustment_basis": adjustment_basis,
                        },
                        "retrieved_at": utc_now(),
                        "trade_date": rows[-1]["date"] if rows else None,
                        "row_count": len(rows),
                        "fields": ["date", "open", "high", "low", "close", "volume"],
                        "status": "ok",
                        "limitations": ["User-provided OHLCV file was not independently verified against iFinD."],
                    }
                ],
            )

        if start and end:
            ifind = self.ifind_client.history_quote(
                codes=ticker,
                indicators="open,high,low,close,volume",
                startdate=start,
                enddate=end,
            )
            rows = parse_ifind_history_rows(ifind.get("response"))
            if ifind.get("status") == "ok" and rows:
                return DataResponse(
                    status="ok",
                    data=rows,
                    source_capability_matrix=self.capability_matrix(),
                    source_log=[
                        {
                            "source_name": "同花顺/iFinD HTTP API",
                            "source_type": "licensed_data_tool",
                            "endpoint_or_interface": "cmd_history_quotation",
                            "parameters": {
                                "codes": ticker,
                                "indicators": "open,high,low,close,volume",
                                "startdate": start,
                                "enddate": end,
                            },
                            "retrieved_at": utc_now(),
                            "trade_date": rows[-1]["date"],
                            "row_count": len(rows),
                            "fields": ["date", "open", "high", "low", "close", "volume"],
                            "status": "ok",
                            "limitations": [],
                        }
                    ],
                )
            gap_reason = ifind.get("missing") or ifind.get("error") or "iFinD returned no parseable OHLCV rows"
        else:
            gap_reason = "start and end are required for live iFinD OHLCV retrieval"

        fallback = self._fetch_akshare_daily(ticker, market, start, end)
        if fallback.status == "ok":
            fallback.source_capability_matrix = self.capability_matrix()
            fallback.source_log.insert(
                0,
                {
                    "source_name": "同花顺/iFinD HTTP API",
                    "source_type": "licensed_data_tool",
                    "endpoint_or_interface": "cmd_history_quotation",
                    "parameters": {"codes": ticker, "startdate": start, "enddate": end},
                    "retrieved_at": utc_now(),
                    "status": "fallback_triggered",
                    "limitations": [str(gap_reason)],
                },
            )
            return fallback

        return DataResponse(
            status="source_gap",
            data=None,
            source_capability_matrix=self.capability_matrix(),
            missing_data=[str(gap_reason), *fallback.missing_data],
            errors=fallback.errors,
            source_log=[
                {
                    "source_name": "同花顺/iFinD HTTP API",
                    "source_type": "licensed_data_tool",
                    "endpoint_or_interface": "cmd_history_quotation",
                    "parameters": {"codes": ticker, "startdate": start, "enddate": end},
                    "retrieved_at": utc_now(),
                    "status": "source_gap",
                    "limitations": [str(gap_reason)],
                },
                *fallback.source_log,
            ],
        )

    def _fetch_akshare_daily(self, ticker: str, market: str, start: str | None, end: str | None) -> DataResponse:
        if market != "a_share":
            return self._gap("fallback_loader", ticker, f"AKShare daily fallback not configured for market={market}")
        try:
            import akshare as ak  # type: ignore
        except Exception as exc:  # noqa: BLE001
            return DataResponse(
                status="source_gap",
                missing_data=["AKShare is not importable in this environment."],
                errors=[repr(exc)],
                source_log=[
                    {
                        "source_name": "AKShare",
                        "source_type": "public_data_tool",
                        "endpoint_or_interface": "stock_zh_a_hist",
                        "parameters": {"symbol": ticker, "start_date": start, "end_date": end},
                        "retrieved_at": utc_now(),
                        "status": "source_gap",
                        "limitations": ["AKShare import failed."],
                    }
                ],
            )
        symbol = ticker.split(".")[0]
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=(start or "").replace("-", ""), end_date=(end or "").replace("-", ""), adjust="")
        except Exception as exc:  # noqa: BLE001
            return DataResponse(status="source_gap", missing_data=["AKShare OHLCV fallback failed."], errors=[repr(exc)])
        raw_rows = df.to_dict(orient="records")
        rows = load_rows_from_dicts(raw_rows)
        return DataResponse(
            status="ok",
            data=rows,
            source_log=[
                {
                    "source_name": "AKShare",
                    "source_type": "public_data_tool",
                    "endpoint_or_interface": "stock_zh_a_hist",
                    "parameters": {"symbol": symbol, "period": "daily", "start_date": start, "end_date": end, "adjust": ""},
                    "retrieved_at": utc_now(),
                    "trade_date": rows[-1]["date"] if rows else None,
                    "row_count": len(rows),
                    "status": "ok",
                    "limitations": ["Public fallback source; cross-check against iFinD before high-confidence use."],
                }
            ],
        )

    def get_fundamentals(self, ticker: str, market: str) -> DataResponse:
        return self._gap("basic_data", ticker, "fundamentals retrieval is registered but not yet mapped to normalized fields")

    def get_valuation(self, ticker: str, market: str) -> DataResponse:
        return self._gap("basic_data", ticker, "valuation retrieval is registered but not yet mapped to normalized fields")

    def get_announcements(self, ticker: str, market: str) -> DataResponse:
        return self._gap("announcement", ticker, "announcement retrieval requires iFinD entitlement and endpoint field mapping")

    def get_trading_calendar(self, market: str, start: str, end: str) -> DataResponse:
        return self._gap("date_sequence", None, "trading calendar retrieval is registered but not yet mapped to normalized fields")


def parse_ifind_history_rows(response: Any) -> list[dict[str, Any]]:
    if not isinstance(response, dict):
        return []
    tables = response.get("tables")
    if not isinstance(tables, list) or not tables:
        return []
    table = tables[0]
    if not isinstance(table, dict):
        return []
    payload = table.get("table") or table.get("data")
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        rows = [row for row in payload if isinstance(row, dict)]
    elif isinstance(payload, dict):
        date_values = payload.get("time") or payload.get("date") or payload.get("trade_date")
        if isinstance(date_values, list):
            for index, value in enumerate(date_values):
                row = {"date": value}
                for field in ("open", "high", "low", "close", "volume"):
                    values = payload.get(field)
                    if isinstance(values, list) and index < len(values):
                        row[field] = values[index]
                rows.append(row)
    return load_rows_from_dicts(rows)


def parse_ifind_quote(response: Any, ticker: str) -> dict[str, Any] | None:
    if not isinstance(response, dict):
        return None
    tables = response.get("tables")
    if not isinstance(tables, list) or not tables:
        return None
    table = tables[0]
    if not isinstance(table, dict):
        return None
    payload = table.get("table") or table.get("data")
    row: dict[str, Any] | None = None
    if isinstance(payload, list):
        row = next((item for item in payload if isinstance(item, dict)), None)
    elif isinstance(payload, dict):
        row = {}
        for field in ("open", "high", "low", "latest", "close", "volume", "amount", "time", "date", "trade_date"):
            value = payload.get(field)
            if isinstance(value, list):
                row[field] = value[0] if value else None
            else:
                row[field] = value
    if not row:
        return None
    latest = to_float(row.get("latest") if row.get("latest") is not None else row.get("close"))
    return {
        "ticker": ticker,
        "latest": latest,
        "open": to_float(row.get("open")),
        "high": to_float(row.get("high")),
        "low": to_float(row.get("low")),
        "close": to_float(row.get("close")),
        "volume": to_float(row.get("volume")),
        "amount": to_float(row.get("amount")),
        "currency": "CNY",
        "trade_date": row.get("trade_date") or row.get("date") or row.get("time"),
        "adjustment_basis": "real_time_unadjusted",
    }


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def load_rows_from_dicts(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from tools.calculate_technical_analysis import normalize_rows

    if not raw_rows:
        return []
    return normalize_rows(raw_rows)
