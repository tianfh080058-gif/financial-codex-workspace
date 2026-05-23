# Data Capability Registry

This registry is the human-readable counterpart to
`trading_core/endpoint_registry.py`. Skills should use it to explain provider
priority, fallback behavior, and source gaps before producing high-risk market
or investment output.

## Provider Priority

| Priority | Provider | Use Case | Fallback Rule |
|---:|---|---|---|
| 1 | iFinD / 同花顺 HTTP API | Licensed China market quotes, historical bars, security master, valuation, announcements, and calendars. | Use first when credentials and endpoint coverage are available. |
| 2 | User-provided files | Broker exports, OHLCV panels, models, filings, watchlists, or manually verified data. | Use when live provider is unavailable or user wants a controlled sample. |
| 3 | AKShare | Public China market prototypes and cross-checks. | Use only with interface name, parameters, retrieval time, and source limitations. |
| 4 | yfinance / OKX / CCXT / Vibe loader | Non-China or upstream Vibe-Trading fallback workflows. | Use when iFinD and local files cannot provide the field, and disclose fallback in `source_log`. |

## Coverage Matrix

| Capability | iFinD | User File | AKShare | Vibe Loader |
|---|---|---|---|---|
| Security master | Primary for supported markets. | Allowed when provided by user. | Fallback for public China data. | Limited by upstream loader. |
| Real-time quote | Primary when licensed. | Snapshot only if timestamped. | Fallback prototype. | Limited. |
| Historical OHLCV | Primary for supported markets. | Preferred for reproducible tests. | Fallback prototype. | Supported for Vibe-compatible assets. |
| Fundamentals | Primary when licensed. | Allowed when sourced. | Partial fallback. | Not primary. |
| Valuation | Primary when licensed. | Allowed when sourced. | Partial fallback. | Not primary. |
| Announcements | Primary when endpoint is available. | Allowed for uploaded disclosures. | Public fallback when interface is identified. | Not primary. |
| Trading calendar | Primary for China markets. | Allowed for test fixtures. | Public fallback. | Limited. |

## Required Source Log Fields

Each data pull or user file must record:

- `source_name`
- `endpoint_or_interface`
- `parameters`
- `retrieved_at`
- `trade_date` or source document date when applicable
- `status`
- `missing_fields`
- `fallback_reason` when a lower-priority source is used

## Data Quality Rules

- Do not mix adjusted and unadjusted price series without labeling
  `adjustment_basis`.
- Do not mix RMB, HKD, USD, shares, lots, 万元, 百万元, or 亿元 without explicit
  unit fields.
- If iFinD is unavailable, unauthorized, or missing fields, record a source gap
  before using fallback data.
- For high-risk output, cross-check critical market data or state why a
  cross-check was not possible.
