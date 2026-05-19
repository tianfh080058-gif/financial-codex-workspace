---
name: a-share-valuation-template
description: "Use when building or reviewing A-share public company valuation workflows that need market snapshot, trading multiples, historical valuation percentiles, DCF framework, equity value bridge, RMB units, disclosure mapping, iFinD or AKShare data sourcing, missing data handling, and strict no-fabrication QA before producing an investment memo, model framework, or Excel valuation output."
---

# A-Share Valuation Template

Use this skill for A-share public company valuation after
`financial-services-skill-router` and `china-market-overlay`.

Pair with:

- `ifind-http-api` or `akshare` for data retrieval.
- `vertical-financial-analysis-dcf-model` for DCF methodology.
- `vertical-financial-analysis-comps-analysis` and
  `a-share-comps-best-practice` for relative valuation.
- `vertical-financial-analysis-xlsx-author` only when the user asks for an Excel
  artifact.

## Required Inputs

Classify each input as provided, missing, needs verification, or assumption
requiring user confirmation:

- Company name and A-share ticker.
- Exchange and board.
- Reporting currency and units.
- Latest trading date and price source.
- Total market capitalization and free-float market capitalization.
- Shares outstanding and diluted share count.
- Cash, debt, minority interest, and non-operating assets.
- Historical financials: revenue, gross profit, EBIT, net profit attributable to
  parent, operating cash flow, capex, depreciation and amortization, working
  capital.
- Latest annual, interim, and quarterly disclosures.
- Consensus estimates, guidance, or user-provided forecast assumptions.
- Peer set and industry classification.

If required inputs are missing, build a framework and data request checklist
instead of producing a target price.

## Valuation Output Structure

### 1. Market Snapshot

Include, when source-backed:

- Company name and ticker.
- Exchange and board.
- Trading date and retrieval timestamp.
- Latest price or close price.
- Total market capitalization.
- Free-float market capitalization.
- Volume, turnover, and liquidity notes.
- 52-week or one-year price range.
- Currency, unit, and adjustment basis.

### 2. Trading Multiples

Include only sourced or derived-from-sourced metrics:

- `PE_TTM`.
- Forward PE only when forecast EPS is sourced.
- `PB`.
- `PS`.
- `PCF`.
- `EV/EBITDA` only when enterprise value and EBITDA are both reliable.
- One-year, three-year, and five-year percentile ranks when historical data are
  available and comparable.
- Peer median, quartiles, and target percentile only when the peer group is
  documented.

Label negative, not meaningful, or unavailable denominators instead of forcing a
multiple.

### 3. DCF Framework

Use formulas rather than hardcoded derived values when producing a model:

```text
FCFF = EBIT * (1 - tax rate) + D&A - CapEx - change in net working capital
Enterprise Value = present value of explicit FCFF + present value of terminal value
Equity Value = Enterprise Value + cash - debt - minority interest +/- other adjustments
Per Share Value = Equity Value / diluted shares
```

DCF assumptions should cover:

- Revenue growth by segment where available.
- Gross margin.
- Operating expense ratio.
- EBIT margin.
- Tax rate.
- D&A.
- CapEx.
- Working capital.
- WACC（加权平均资本成本）.
- terminal value（终值） using perpetual growth or exit multiple.
- Sensitivity ranges for WACC, terminal growth, exit multiple, or margin.

Do not invent WACC, beta, growth, terminal value, consensus, or capex
assumptions. If assumptions are user-provided, label them as assumptions.

### 4. Valuation Summary

Provide:

- Method used.
- Data sources.
- Implied equity value and per-share value only when inputs are sufficient.
- Valuation range rather than a single point estimate when appropriate.
- Key drivers.
- Key risks.
- Missing data and unsupported conclusions.

For high-risk outputs, include `Not investment advice`.

## QA Checks

Before delivery, verify:

- Ticker, exchange, and company name match.
- Currency and unit are consistent.
- Latest market data has a trading date and retrieval timestamp.
- Financial statement periods are aligned.
- Market capitalization reconciles to price and share count when both are
  available.
- Net debt and equity bridge are sourced or clearly marked missing.
- Multiples with negative or missing denominators are flagged.
- No fabricated financials, guidance, consensus, or target price are included.
- All assumptions are separate from facts.
