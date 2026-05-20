# A-Share Single-Stock Research Pipeline

Use this pipeline for A-share single-stock research, quick notes, thesis
checks, and deeper stock reviews. Select the lightest path that satisfies the
user's request.

## Path Selection

| User intent | Path | Required objects |
|---|---|---|
| Stock trend / technical review | Light market path | `security_master`, `source_log`, `market_snapshot`, `qa_status` |
| Single-stock deep dive | Full research path | All schema objects where source-backed |
| Thesis check | Thesis path | `security_master`, `source_log`, `thesis_tracker`, `qa_status` |
| Catalyst calendar | Catalyst path | `security_master`, `source_log`, `thesis_tracker.catalysts`, `qa_status` |
| Data-source comparison | Cross-check path | `security_master`, two or more `source_log` entries, `qa_status.cross_source_check` |

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

3. **Market and liquidity analysis**
   - Populate `market_snapshot`.
   - Include price, volume, turnover amount, turnover rate, market cap, one-year
     range, moving averages, drawdown, volatility, and adjustment basis when
     sourced or calculated from sourced data.
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

8. **Output assembly**
   - Choose the right artifact:
     - Quick note for trend or event response.
     - Markdown memo for single-stock research.
     - Data request checklist when data is insufficient.
     - Excel or PPT only when explicitly requested.
   - Separate facts, calculations, assumptions, inferences, and missing data.

9. **QA and source-log finalization**
   - Populate `qa_status`.
   - Include `Not investment advice` for investment, valuation, trading,
     portfolio, or thesis outputs.
   - Report data limitations and unsupported conclusions.

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
- Missing data and source limitations.
- Assumptions separated from facts.
- QA checks performed.
- `Not investment advice` when the output relates to investment conclusions.
