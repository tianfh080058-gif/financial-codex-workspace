# A-Share Equity Research Schema

This reference defines the normalized schema for A-share equity research. Use
only the objects needed for the user's task. `null`, `TBD`, or explicit
`missing_data` entries are preferred over invented values.

## Object Overview

| Object | Purpose |
|---|---|
| `security_master` | Security identity, listing, industry, and currency metadata. |
| `source_log` | Data lineage for every pull, filing, or user-provided source. |
| `market_snapshot` | Price, liquidity, market cap, and adjustment-basis data. |
| `financial_snapshot` | Period financials from disclosures or verified data tools. |
| `valuation_snapshot` | Multiples, historical percentiles, and peer valuation context. |
| `peer_set` | Confirmed, candidate, and rejected peers with reasons. |
| `thesis_tracker` | Thesis, evidence, disconfirming signals, catalysts, and risks. |
| `qa_status` | Data-quality checks, limitations, and investment-output guardrails. |

## Required Conventions

- Ticker: use exchange suffix where available, such as `000807.SZ`,
  `600519.SH`, or `833000.BJ`.
- Currency: use `CNY` for A-share market data and RMB financials unless a
  source states otherwise.
- Units: market prices are normally `CNY/share`; financial statement values must
  state `元`, `万元`, `百万元`, or `亿元`.
- Trading date: market data must include `trade_date`.
- Retrieval timestamp: every pull must include `retrieved_at`.
- Price basis: price fields must include `adjustment_basis` as `unadjusted`,
  `qfq`, `hfq`, or `unknown`.
- Facts, calculations, assumptions, inferences, and missing data must be
  separated.

## Schema Objects

### `security_master`

```json
{
  "company_name": "云铝股份",
  "ticker": "000807.SZ",
  "exchange": "SZSE",
  "board": "主板",
  "market": "A share",
  "currency": "CNY",
  "listing_status": "listed",
  "industry": {
    "csrs": null,
    "sw": null,
    "citic": null,
    "source": null
  },
  "identifier_status": "verified",
  "identifier_notes": []
}
```

### `source_log`

Create one entry per data pull, filing, source file, or user-provided input.

```json
{
  "source_name": "同花顺/iFinD HTTP API",
  "source_type": "licensed_data_tool",
  "endpoint_or_interface": "cmd_history_quotation",
  "parameters": {
    "codes": "000807.SZ",
    "indicators": "open,high,low,close,volume",
    "startdate": "2025-05-20",
    "enddate": "2026-05-20"
  },
  "retrieved_at": "2026-05-20T12:47:37+08:00",
  "trade_date": "2026-05-19",
  "row_count": 242,
  "fields": ["open", "high", "low", "close", "volume"],
  "status": "ok",
  "limitations": []
}
```

### `market_snapshot`

Use this for trend, liquidity, market cap, and valuation entry points.

```json
{
  "trade_date": "2026-05-20",
  "retrieved_at": "2026-05-20T13:38:52+08:00",
  "price": {
    "latest": 30.49,
    "close": 30.49,
    "previous_close": 30.01,
    "open": 30.0,
    "high": 30.79,
    "low": 29.83,
    "currency": "CNY",
    "adjustment_basis": "unadjusted"
  },
  "liquidity": {
    "volume": 502118,
    "volume_unit": "lot",
    "turnover_amount": 1523758557.39,
    "turnover_amount_unit": "CNY",
    "turnover_rate_pct": 1.45
  },
  "market_cap": {
    "total_market_cap": 105738021278.45,
    "free_float_market_cap": 105736914369.49,
    "unit": "CNY"
  },
  "range": {
    "one_year_high": 38.23,
    "one_year_low": 14.29
  },
  "source_ref": ["source_log[0]"],
  "limitations": [
    "Refresh current prices before making a new research conclusion."
  ]
}
```

### `financial_snapshot`

Use only source-backed financials from filings, user files, or verified data
tools.

```json
{
  "period": "2026Q1",
  "period_type": "quarter",
  "disclosure_date": null,
  "currency": "CNY",
  "unit": "亿元",
  "income_statement": {
    "revenue": null,
    "gross_profit": null,
    "operating_profit": null,
    "net_profit_attributable_to_parent": null
  },
  "cash_flow": {
    "operating_cash_flow": null,
    "capex": null,
    "free_cash_flow": null
  },
  "balance_sheet": {
    "cash": null,
    "debt": null,
    "equity_attributable_to_parent": null
  },
  "source_ref": [],
  "missing_data": [
    "Latest financial disclosure not provided or fetched."
  ]
}
```

### `valuation_snapshot`

Use sourced denominators only. Mark negative or unavailable denominators as not
meaningful.

```json
{
  "trade_date": null,
  "retrieved_at": null,
  "currency": "CNY",
  "multiples": {
    "pe_ttm": null,
    "pb": null,
    "ps": null,
    "pcf": null,
    "ev_ebitda": null
  },
  "historical_percentiles": {
    "pe_ttm_1y": null,
    "pb_3y": null
  },
  "peer_context": {
    "peer_median_pe_ttm": null,
    "peer_median_pb": null,
    "valid_peer_count": null
  },
  "not_meaningful": [],
  "missing_data": [
    "Valuation denominators and peer set not sourced."
  ],
  "source_ref": []
}
```

### `peer_set`

Do not silently drop peers.

```json
{
  "industry_classification": {
    "system": "SW",
    "level": null,
    "name": null,
    "source_ref": []
  },
  "confirmed_peers": [],
  "candidate_peers": [],
  "rejected_peers": [
    {
      "ticker": null,
      "company_name": null,
      "reason": "Not evaluated yet."
    }
  ],
  "selection_criteria": [
    "Same or adjacent industry classification",
    "Comparable listing market and currency",
    "Similar business model, revenue mix, scale, growth, and profitability"
  ]
}
```

### `thesis_tracker`

Use this for watchlists, thesis checks, and follow-up logs.

```json
{
  "position_context": "watchlist",
  "core_thesis": null,
  "thesis_pillars": [],
  "supporting_evidence": [],
  "disconfirming_evidence": [],
  "catalysts": [],
  "risks": [],
  "follow_ups": [],
  "conviction": "not_assessed",
  "last_reviewed_at": null,
  "source_ref": [],
  "missing_data": [
    "No user-provided thesis or source-backed catalyst list."
  ]
}
```

### `qa_status`

```json
{
  "ticker_verified": true,
  "exchange_verified": true,
  "currency_unit_checked": true,
  "adjustment_basis_checked": true,
  "trade_date_present": true,
  "retrieved_at_present": true,
  "source_log_present": true,
  "cross_source_check": {
    "performed": false,
    "sources": [],
    "differences": []
  },
  "missing_data": [],
  "assumptions": [],
  "not_investment_advice_included": true,
  "unsupported_outputs_blocked": [
    "target price",
    "rating",
    "buy/sell recommendation",
    "unsourced consensus",
    "unsourced guidance"
  ]
}
```

## iFinD / AKShare Normalization Notes

| Topic | iFinD | AKShare | Normalized Handling |
|---|---|---|---|
| Ticker | Often `000807.SZ` | Often `000807` | Store normalized ticker with suffix plus raw symbol. |
| Volume | API-field dependent | Often lots for Eastmoney A-share daily data | Always set `volume_unit`. |
| Dates | May appear in table metadata | Usually `日期` column | Map to `trade_date`. |
| Adjustment | Endpoint parameter dependent | `adjust=""`, `qfq`, `hfq` | Map to `adjustment_basis`. |
| Source | Licensed iFinD | Public AKShare upstream source | Record source type and limitations. |

## Missing Data Policy

- If financial statements are missing, output the framework and data request
  checklist; do not invent `financial_snapshot`.
- If consensus or guidance is missing, mark it missing; do not infer from price
  action or analyst-style language.
- If peer data is missing, use `candidate_peers` and explain selection criteria;
  do not present medians or percentiles.
- If iFinD and AKShare disagree, report both values and explain likely causes
  before drawing conclusions.
