"""iFinD endpoint registry used by the market-data adapter."""

from __future__ import annotations

IFIND_ENDPOINT_REGISTRY = {
    "real_time_quote": {
        "endpoint": "real_time_quotation",
        "required": ["codes", "indicators"],
        "typical_indicators": ["open", "high", "low", "latest", "volume", "amount"],
    },
    "historical_quote": {
        "endpoint": "cmd_history_quotation",
        "required": ["codes", "indicators", "startdate", "enddate"],
        "typical_indicators": ["open", "high", "low", "close", "volume", "amount"],
    },
    "security_master": {
        "endpoint": "basic_data",
        "required": ["codes", "indicators"],
        "typical_indicators": ["thscode", "sec_name", "exchange", "listed_date"],
    },
    "valuation": {
        "endpoint": "basic_data",
        "required": ["codes", "indicators"],
        "typical_indicators": ["pe_ttm", "pb_lf", "ps_ttm", "total_mv", "float_mv"],
    },
    "announcements": {
        "endpoint": "announcement",
        "required": ["codes"],
        "typical_indicators": ["title", "publish_time", "url"],
    },
    "trading_calendar": {
        "endpoint": "date_sequence",
        "required": ["market", "startdate", "enddate"],
        "typical_indicators": ["trade_date", "is_open"],
    },
}
