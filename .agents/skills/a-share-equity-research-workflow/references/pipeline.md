# A-Share Single-Stock Research Pipeline

Use this pipeline for A-share single-stock research, quick notes, thesis
checks, and deeper stock reviews. Select the lightest path that satisfies the
user's request.

## Path Selection

| User intent | Path | Required objects |
|---|---|---|
| Stock trend / technical review | Light market path | `security_master`, `source_log`, `market_snapshot`, `technical_analysis`, `qa_status` |
| Single-stock deep dive | Full research path | All schema objects where source-backed |
| Investment decision support | Decision-support path | `analysis_mode`, `security_master`, `source_log`, `market_context`, `market_snapshot`, `technical_analysis`, `decision_support`, `qa_status`, `report_integrity_status` |
| Thesis check | Thesis path | `security_master`, `source_log`, `thesis_tracker`, `qa_status` |
| Catalyst calendar | Catalyst path | `security_master`, `source_log`, `thesis_tracker.catalysts`, `qa_status` |
| Data-source comparison | Cross-check path | `security_master`, two or more `source_log` entries, `qa_status.cross_source_check` |
| Watchlist daily review | Product watchlist path | `source_capability_matrix`, `market_context`, per-stock minimum objects, `report_integrity_status` |

## Mode Selection

- Require explicit `analysis_mode.mode` for productized outputs.
- Use `research` for stock deep dives, trend reviews, earnings analysis,
  valuation frameworks, peer work, thesis checks, and catalyst tracking.
- Use `decision_support` only when the user asks for investment decision support
  or explicitly selects that mode.
- In `research`, do not output `decision_support.decision_state`, buy/sell
  language, personal position sizing, target prices, or return promises.
- In `decision_support`, use only `watch_only`, `research_candidate`,
  `hold_monitor`, `risk_control_review`, or `avoid_or_wait`.
- For single-stock research and decision-support outputs with market data,
  include `technical_analysis` across daily, weekly, and monthly timeframes.

## Nine-Step Full Research Path

1. **Security identification**
   - Confirm company name, ticker, exchange, board, listing status, industry,
     currency, and reporting unit.
   - If name-to-ticker mapping is ambiguous, ask for confirmation or return
     candidates.

2. **Data-source selection**
   - Use user-provided files and official disclosures for facts.
   - Use `ifind-http-api` for licensed iFinD market, financial, valuation, and
     announcement data when available.
   - Use `akshare` for public data prototypes and cross-checks.
   - Record every pull in `source_log`.
   - Populate `source_capability_matrix` when fallback, failed pulls, delayed
     public data, entitlement gaps, or source priority affect the analysis.

3. **Market, liquidity, and technical analysis**
   - Populate `market_snapshot`.
   - Include price, volume, turnover amount, turnover rate, market cap, one-year
     range, and adjustment basis when sourced.
   - Populate `technical_analysis` from sourced OHLCV data. Default timeframes
     are daily, weekly, and monthly; daily is primary, weekly confirms, and
     monthly provides long-term trend background and large-level risk filters.
   - Include MA5/10/20/60/120, MACD(12,26,9), RSI(14), Bollinger(20,2),
     20/60-day drawdown, volume MA5/20, volume ratio, relative strength, and
     support/resistance when the lookback is sufficient.
   - Prefer source-native weekly/monthly bars; if unavailable, resample from
     daily bars and label `calculation_basis = resampled_from_daily`.
   - Populate `market_context` when the stock move should be interpreted against
     indices, sector strength, liquidity heat, risk appetite, or current events.
   - Label calculations as calculations, not raw facts.

4. **Financial and disclosure snapshot**
   - Populate `financial_snapshot` from annual, interim, quarterly reports,
     official disclosures, user files, or verified data tools.
   - Record period, disclosure date, currency, unit, and source.
   - Missing filings or statement items must remain missing.

5. **Industry and peer universe**
   - Use `a-share-comps-best-practice`.
   - Classify confirmed peers, candidate peers, and rejected peers with reasons.
   - Apply ST, suspension, negative denominator, and outlier handling.

6. **Valuation and historical percentile**
   - Use `a-share-valuation-template`.
   - Populate `valuation_snapshot` only with source-backed denominators.
   - Do not output target price unless user-provided or source-backed inputs are
     sufficient.

7. **Thesis, catalysts, risks, and disconfirming evidence**
   - Use `vertical-equity-research-thesis-tracker` and
     `vertical-equity-research-catalyst-calendar` when needed.
   - Make the thesis falsifiable.
   - Track both supporting and disconfirming evidence.
   - For `decision_support`, convert the thesis and technical analysis into
     evidence, trigger conditions, invalidation conditions, risk controls, and
     confidence. Technical analysis can constrain or support the state but must
     not be the sole basis for `decision_state`.

8. **Output assembly**
   - Choose the right artifact:
     - Quick note for trend or event response.
     - Markdown memo for single-stock research.
     - Data request checklist when data is insufficient.
     - Excel or PPT only when explicitly requested.
   - Separate facts, calculations, assumptions, inferences, and missing data.
   - In single-stock research, place `Technical Analysis（技术分析）` after
     `行情与流动性`, ordered as daily trend, weekly confirmation, monthly
     background, volume-price structure, momentum/volatility, relative strength,
     key risk levels, and missing data.

9. **QA and source-log finalization**
   - Populate `qa_status`.
   - Populate `report_integrity_status` for productized reports, watchlist
     daily reviews, and decision-support outputs.
   - Link local JSONL records with `review_history_ref` when a report, thesis,
     run, or backtest record is saved under `.research/`.
   - Include `Not investment advice` for investment, valuation, trading,
     portfolio, or thesis outputs.
   - Report data limitations and unsupported conclusions.

## Productized Local Artifacts

When using the product-layer workflow, store local artifacts under `.research/`
unless the user asks for another location:

- `.research/watchlists/*.json`: watchlist definitions and grouping.
- `.research/reports/YYYY-MM-DD/*.md`: daily and single-stock Markdown reports.
- `.research/runs/*.jsonl`: run summaries, mode, sources, output references,
  and QA status.
- `.research/thesis/*.jsonl`: thesis evidence, disconfirming signals,
  catalysts, and state changes.
- `.research/backtests/*.jsonl`: post-review records for 5/20/60 trading-day
  horizons.

These local artifacts can contain proprietary or personal notes and should not
be committed by default.

## Cross-Source Difference Handling

When iFinD and AKShare differ, explain differences before analysis:

- Timestamp: real-time, intraday, or end-of-day.
- Trade date: different latest trading day or suspended day.
- Unit: shares, lots, yuan, ten-thousand yuan, or other.
- Adjustment basis: unadjusted, qfq, hfq, or unknown.
- Endpoint/interface: historical quote vs real-time quote vs snapshot.
- Upstream source limitation: license entitlement, network failure, stale data,
  missing field, or public data delay.

## Minimum Output Checklist

Every A-share research output should include:

- Selected skills and execution order.
- Source names, endpoint/interface names, parameters, and retrieval timestamp.
- Trading date, currency, unit, exchange, and adjustment basis.
- Technical analysis timeframe coverage, calculation basis, and source refs when
  price work is part of the request.
- Missing data and source limitations.
- Assumptions separated from facts.
- QA checks performed.
- `Not investment advice` when the output relates to investment conclusions.
