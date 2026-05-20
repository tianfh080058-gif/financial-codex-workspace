# A-Share Equity Research Schema

This reference defines the normalized schema for A-share equity research. Use
only the objects needed for the user's task. `null`, `TBD`, or explicit
`missing_data` entries are preferred over invented values.

## Object Overview

| Object | Purpose |
|---|---|
| `security_master` | Security identity, listing, industry, and currency metadata. |
| `source_log` | Data lineage for every pull, filing, or user-provided source. |
| `source_capability_matrix` | Data-source capabilities, priority, status, and fallback handling. |
| `analysis_mode` | Explicit mode selection: `research` or `decision_support`. |
| `market_context` | Market, index, sector, liquidity, and event context around the stock. |
| `market_snapshot` | Price, liquidity, market cap, and adjustment-basis data. |
| `technical_analysis` | Daily, weekly, and monthly technical calculations from sourced OHLCV data. |
| `financial_snapshot` | Period financials from disclosures or verified data tools. |
| `valuation_snapshot` | Multiples, historical percentiles, and peer valuation context. |
| `peer_set` | Confirmed, candidate, and rejected peers with reasons. |
| `thesis_tracker` | Thesis, evidence, disconfirming signals, catalysts, and risks. |
| `decision_support` | Decision-support state, evidence, triggers, invalidation, and controls. |
| `report_integrity_status` | Report completeness checks for source, date, unit, QA, and guardrails. |
| `review_history_ref` | References to local report, thesis, run, or backtest JSONL records. |
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
- Analysis mode: every productized output must set `analysis_mode.mode` to
  `research` or `decision_support`.
- Technical analysis: single-stock research and decision-support outputs with
  market data must include `technical_analysis` based on sourced OHLCV data.
- Facts, calculations, assumptions, inferences, and missing data must be
  separated.
- Investment decision support must not include personal position sizing, target
  price, buy/sell rating, return promises, unsourced consensus, or unsourced
  guidance.

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

### `analysis_mode`

Use this object before deciding output style. `research` is for institutional
research notes. `decision_support` is for decision framing and risk controls,
not personal investment advice.

```json
{
  "mode": "research",
  "requested_by_user": true,
  "allowed_values": ["research", "decision_support"],
  "mode_notes": [
    "research mode does not output decision_state",
    "decision_support mode uses decision states, evidence, triggers, and risk controls"
  ]
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

### `source_capability_matrix`

Use this when source choice, source failure, or fallback affects the conclusion.

```json
[
  {
    "source_name": "同花顺/iFinD HTTP API",
    "source_type": "licensed_data_tool",
    "priority": 1,
    "capabilities": [
      "real_time_quote",
      "historical_quote",
      "valuation_fields",
      "announcements_when_entitled"
    ],
    "status": "available",
    "last_checked_at": null,
    "fallback_to": ["AKShare", "official_disclosure"],
    "limitations": []
  },
  {
    "source_name": "AKShare",
    "source_type": "public_data_tool",
    "priority": 2,
    "capabilities": [
      "public_market_data",
      "public_financial_snapshot",
      "cross_check"
    ],
    "status": "available",
    "last_checked_at": null,
    "fallback_to": ["official_disclosure"],
    "limitations": [
      "Upstream public interfaces can be delayed, unavailable, or proxy-limited."
    ]
  },
  {
    "source_name": "official_disclosure",
    "source_type": "official_filing_or_exchange_disclosure",
    "priority": 0,
    "capabilities": ["financial_facts", "events", "announcements"],
    "status": "preferred_for_facts",
    "last_checked_at": null,
    "fallback_to": [],
    "limitations": [
      "May require manual retrieval or link verification."
    ]
  }
]
```

### `market_context`

Use for watchlist daily reviews, market reviews, and single-stock notes that
need broader context before drawing stock-specific conclusions.

```json
{
  "trade_date": null,
  "retrieved_at": null,
  "indices": [
    {
      "name": "创业板指",
      "ticker": "399006.SZ",
      "close": null,
      "pct_change": null,
      "source_ref": []
    }
  ],
  "sector_context": {
    "sector_name": null,
    "relative_strength": null,
    "breadth": null,
    "turnover_heat": null,
    "source_ref": []
  },
  "risk_appetite": {
    "summary": null,
    "evidence": [],
    "missing_data": []
  },
  "event_context": {
    "news_or_events": [],
    "source_ref": []
  },
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

### `technical_analysis`

Use this for source-backed calculations from OHLCV data. Keep raw market data in
`market_snapshot`; use this object for calculated daily, weekly, and monthly
signals. Default interpretation weight is daily as primary, weekly as
confirmation, and monthly as long-term background and risk filter.

Allowed technical status labels:

- `constructive`
- `neutral`
- `deteriorating`
- `mixed`
- `insufficient_data`

```json
{
  "trade_date": "2026-05-20",
  "retrieved_at": "2026-05-20T13:38:52+08:00",
  "adjustment_basis": "qfq",
  "calculation_basis": "source_ohlcv",
  "timeframe_weights": {
    "daily": "primary",
    "weekly": "confirmation",
    "monthly": "long_term_background_risk_filter"
  },
  "daily": {
    "status": "mixed",
    "calculation_basis": "source_period_data",
    "bar_count": 242,
    "moving_averages": {
      "ma5": null,
      "ma10": null,
      "ma20": null,
      "ma60": null,
      "ma120": null,
      "trend_summary": null
    },
    "momentum": {
      "macd": {
        "fast": 12,
        "slow": 26,
        "signal": 9,
        "dif": null,
        "dea": null,
        "histogram": null
      },
      "rsi14": null
    },
    "volatility": {
      "bollinger_20_2": {
        "upper": null,
        "middle": null,
        "lower": null,
        "position": null
      },
      "drawdown_20": null,
      "drawdown_60": null
    },
    "volume_price": {
      "volume_ma5": null,
      "volume_ma20": null,
      "volume_ratio": null,
      "volume_price_summary": null
    },
    "relative_strength": {
      "benchmark": null,
      "lookback_days": null,
      "relative_return": null,
      "summary": null
    },
    "support_resistance": {
      "support": [],
      "resistance": [],
      "method": "recent_swing_high_low"
    },
    "missing_data": []
  },
  "weekly": {
    "status": "insufficient_data",
    "calculation_basis": "resampled_from_daily",
    "bar_count": null,
    "trend_summary": null,
    "momentum_summary": null,
    "volume_price_summary": null,
    "support_resistance": {
      "support": [],
      "resistance": [],
      "method": "recent_swing_high_low"
    },
    "missing_data": []
  },
  "monthly": {
    "status": "insufficient_data",
    "calculation_basis": "resampled_from_daily",
    "bar_count": null,
    "long_term_ma_direction": null,
    "trend_summary": null,
    "major_support_resistance": {
      "support": [],
      "resistance": []
    },
    "long_term_drawdown_position": null,
    "missing_data": []
  },
  "cross_timeframe_summary": {
    "overall_status": "mixed",
    "daily_signal": null,
    "weekly_confirmation": null,
    "monthly_background": null,
    "evidence_use": [
      "Technical analysis is a calculation layer, not a standalone investment conclusion."
    ]
  },
  "source_ref": ["source_log[0]"],
  "limitations": [
    "Technical calculations require refreshed OHLCV data before each new conclusion."
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

### `decision_support`

Use only when `analysis_mode.mode` is `decision_support`. This object supports
decision framing and risk control, not individualized investment advice.

Allowed `decision_state` values:

- `watch_only`
- `research_candidate`
- `hold_monitor`
- `risk_control_review`
- `avoid_or_wait`

```json
{
  "decision_state": "watch_only",
  "state_as_of": null,
  "decision_time_horizon": "not_specified",
  "supporting_evidence": [],
  "disconfirming_evidence": [],
  "trigger_conditions": [],
  "invalidation_conditions": [],
  "risk_controls": [],
  "confidence": "low",
  "confidence_reason": null,
  "not_allowed_outputs": [
    "personal position sizing",
    "target price",
    "buy/sell rating",
    "return promise",
    "unsourced consensus",
    "unsourced guidance"
  ],
  "missing_data": [],
  "source_ref": []
}
```

### `report_integrity_status`

Use this for memo QA and productized outputs. A failed integrity check should be
reported before relying on the memo.

```json
{
  "status": "not_checked",
  "checked_at": null,
  "required_checks": {
    "analysis_mode_present": false,
    "source_log_present": false,
    "trade_date_present": false,
    "retrieved_at_present": false,
    "unit_present": false,
    "adjustment_basis_present": false,
    "technical_analysis_present": false,
    "technical_analysis_timeframes_present": false,
    "qa_status_present": false,
    "not_investment_advice_present": false
  },
  "mode_checks": {
    "research_has_no_decision_state": null,
    "decision_support_has_required_evidence": null,
    "decision_support_has_technical_evidence": null,
    "unsupported_outputs_blocked": null
  },
  "errors": [],
  "warnings": []
}
```

### `review_history_ref`

Use this to connect current analysis with local JSONL records. Store personal or
proprietary notes under `.research/`, which should remain gitignored.

```json
{
  "run_id": null,
  "report_path": null,
  "watchlist_path": null,
  "runs_jsonl": ".research/runs/default.jsonl",
  "thesis_jsonl": ".research/thesis/default.jsonl",
  "backtest_jsonl": ".research/backtests/default.jsonl",
  "previous_reviews": [],
  "limitations": [
    "Local history may be incomplete or unavailable on another machine."
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
    "personal position sizing",
    "return promise",
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

For `technical_analysis`, normalize OHLCV before calculating indicators:

- Use the same `adjustment_basis` across daily, weekly, and monthly periods.
- Prefer native weekly/monthly bars from the source. If unavailable, resample
  from daily bars and set period `calculation_basis` to
  `resampled_from_daily`.
- Always state missing bars, insufficient lookback windows, and source
  differences before interpreting a technical signal.

## Missing Data Policy

- If financial statements are missing, output the framework and data request
  checklist; do not invent `financial_snapshot`.
- If consensus or guidance is missing, mark it missing; do not infer from price
  action or analyst-style language.
- If peer data is missing, use `candidate_peers` and explain selection criteria;
  do not present medians or percentiles.
- If technical OHLCV data is missing or the lookback window is insufficient,
  mark the relevant timeframe `insufficient_data`; do not invent indicators.
- If iFinD and AKShare disagree, report both values and explain likely causes
  before drawing conclusions.
- If `analysis_mode.mode` is `research`, leave `decision_support` absent or
  `null`; do not output a decision state.
- If `analysis_mode.mode` is `decision_support`, use the allowed decision states
  and include evidence, disconfirming evidence, trigger conditions,
  invalidation conditions, risk controls, source gaps, QA, and
  `Not investment advice`.
- In `decision_support`, technical analysis can support or weaken evidence,
  triggers, invalidation conditions, and confidence, but it must not be the
  sole basis for a decision state.
