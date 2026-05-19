---
name: a-share-comps-best-practice
description: "Use when building or reviewing China A-share comparable company analysis, peer sets, relative valuation, trading multiples, industry benchmarking, percentile analysis, and peer rejection logs with iFinD, AKShare, filings, RMB units, industry classification, ST or suspension filters, negative denominator handling, and strict source-backed QA."
---

# A-Share Comps Best Practice

Use this skill for A-share comparable company analysis after
`financial-services-skill-router`, `china-market-overlay`, and before or
alongside `vertical-financial-analysis-comps-analysis`.

## Peer Selection Workflow

1. Define the target company:
   - Company name and ticker.
   - Exchange and board.
   - Business description.
   - Industry classification, such as 申万, 中信, CSRC, or user-provided
     classification.
   - Revenue mix, market capitalization range, growth profile, profitability,
     and business model.
2. Build a broad candidate universe from source-backed data.
3. Classify peers into:
   - Confirmed peers（已确认可比公司）.
   - Candidate peers（候选可比公司）.
   - Rejected peers（剔除公司）.
4. For every rejected peer, provide a short reason.

Do not silently drop companies from the peer set.

## Peer Selection Criteria

Prefer companies with:

- Same or adjacent industry classification.
- Similar product, end-market, or value chain exposure.
- Similar revenue scale or market capitalization.
- Similar growth stage and profitability profile.
- Comparable listing market and currency.
- Available, source-backed financial and market data.

Flag or consider excluding:

- ST or *ST companies.
- Suspended securities.
- Recently listed companies with insufficient history.
- Companies with materially different revenue mix.
- Companies with negative denominators that make PE, EV/EBITDA, or PCF not
  meaningful.
- Extreme outliers caused by one-off earnings, restructuring, asset sales, or
  accounting changes.

If an outlier is retained, explain why.

## Metrics And Multiples

Use source-backed values only:

- Latest price or close price.
- Total market capitalization.
- Free-float market capitalization.
- Enterprise value, if debt, cash, and minority interest are available.
- Revenue.
- Net profit attributable to parent.
- EBITDA only when consistently defined and sourced.
- Operating cash flow and free cash flow where available.
- Revenue growth, margin, ROE, and ROIC where relevant.
- `PE_TTM`, forward PE when estimates are sourced, `PB`, `PS`, `PCF`, and
  `EV/EBITDA` where meaningful.

Always report currency, unit, fiscal period, trading date, retrieval timestamp,
and adjustment basis.

## Statistics

For each valid multiple, show:

- Count of valid peers.
- Mean.
- Median.
- 25th percentile.
- 75th percentile.
- Minimum and maximum.
- Target company percentile rank, if the target data is available.

Do not include negative or not meaningful multiples in summary statistics unless
the output explicitly labels how they were handled.

## Output Format

Recommended sections:

- Peer universe summary.
- Confirmed peers.
- Candidate peers.
- Rejected peers and reason.
- Market data snapshot.
- Operating metrics.
- Trading multiples.
- Summary statistics.
- Target company positioning.
- Data limitations.
- QA checks performed.

## QA Checks

Before delivery, verify:

- Target ticker and peer tickers are correctly mapped.
- Peer inclusion and exclusion reasons are documented.
- Data sources and timestamps are shown.
- Units and currencies are consistent.
- Negative denominators and not meaningful multiples are flagged.
- Extreme outliers are explained.
- No peer, multiple, consensus, or valuation conclusion is fabricated.
- `Not investment advice` is included for investment or valuation outputs.
