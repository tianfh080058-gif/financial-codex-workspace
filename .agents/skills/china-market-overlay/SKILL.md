---
name: china-market-overlay
description: "Use when a financial task involves China market securities, A shares, Hong Kong-listed Chinese companies, China market data, RMB financials, Chinese disclosures, iFinD, 同花顺, AKShare, 巨潮资讯, 上交所, 深交所, 北交所, 港交所, industry classifications, adjustment basis, trading calendars, or China-specific data integrity requirements before downstream valuation, DCF, comps, earnings, equity research, or financial modeling skills."
---

# China Market Overlay

Use this skill after `financial-services-skill-router` and before downstream
valuation, DCF, comps, earnings, or modeling skills when a task involves China
market securities or Chinese-language financial disclosures.

This skill does not replace the downstream workflow. It adapts the workflow so
the generic financial-services skills use China market data, disclosure names,
units, identifiers, and QA checks correctly.

## Standard Routing

1. Read `.agents/SKILLS_INDEX.md` through the router workflow.
2. Select this overlay when the request mentions A shares, 港股, 中概股, 沪深,
   北交所, 科创板, 创业板, 同花顺, iFinD, AKShare, 巨潮资讯, 上交所, 深交所,
   港交所, RMB/CNY, Chinese company names, or China market tickers.
3. Pair this overlay with the narrow downstream skill:
   - DCF or intrinsic value: `vertical-financial-analysis-dcf-model` plus
     `a-share-valuation-template` when the company is A-share listed.
   - Comparable company analysis: `vertical-financial-analysis-comps-analysis`
     plus `a-share-comps-best-practice`.
   - Earnings review: `vertical-equity-research-earnings-analysis` with China
     disclosure mapping and China-specific required inputs.
   - Data retrieval: `ifind-http-api` for licensed 同花顺/iFinD data or
     `akshare` for public data prototypes and cross-checks.
4. Do not read every skill for completeness. Read only this overlay, the data
   source skill, and the selected downstream skill.

## Market And Identifier Checks

Before fetching or analyzing data, identify and report:

- Security name and ticker, using original ticker format when known.
- Market: A share, 港股, 中概股, 北交所, ETF, fund, bond, futures, or other.
- Exchange suffix: `.SH`, `.SZ`, `.BJ`, `.HK`, or another verified convention.
- Board: 主板, 科创板, 创业板, 北交所, or unknown.
- Currency and reporting unit: RMB/CNY, HKD, USD, 万元, 百万元, 亿元, or other.
- Fiscal period and disclosure date.
- Trading date and data retrieval timestamp for market data.
- Price adjustment basis: unadjusted, 前复权, 后复权, or unknown.

If the name-to-ticker mapping is ambiguous, ask for confirmation or return a
candidate list. Do not silently choose one company.

## China Disclosure Mapping

When a generic skill expects US-style filings or earnings materials, map them
to China market sources:

| Generic reference | China market equivalent |
|---|---|
| 10-K | 年报 |
| 10-Q | 一季报, 半年报, 三季报 |
| Earnings release | 业绩快报, 业绩预告, 定期报告, 投资者关系活动记录表 |
| SEC EDGAR | 巨潮资讯, 上交所, 深交所, 北交所, 港交所披露易 |
| Consensus source | iFinD, Wind, Bloomberg, FactSet, broker consensus, or user-provided source |
| Guidance | 管理层指引, 业绩预告, 经营展望, investor relations disclosure |

If a China market source is not available, state the gap. Do not replace it with
US filings or inferred data.

## Data Source Priority

For China market workflows, use this source hierarchy unless the user specifies
otherwise:

1. User-provided filings, models, extracts, or source files.
2. Official company and exchange disclosures.
3. Licensed data tools configured in this workspace, especially `ifind-http-api`.
4. Public data tools such as `akshare`, with upstream source and interface name
   documented.
5. Web or other verified sources only when the above are unavailable or
   insufficient.

For high-risk valuation, trading, portfolio, or credit outputs, cross-check
critical values against a filing, official disclosure, or a second data source
when feasible.

## Output Requirements

China market deliverables must include:

- Task classification.
- Selected skills and execution order.
- Data sources, endpoint/interface names, parameters, retrieval timestamp, and
  trading date where applicable.
- Currency, unit, fiscal period, exchange, and adjustment basis.
- Missing data and source limitations.
- Assumptions separated from facts.
- `Not investment advice` for valuation, trading, portfolio, or investment
  conclusions.
- QA checks performed.

## Guardrails

- Do not fabricate financial statements, market prices, consensus, guidance,
  announcement content, industry classification, peer membership, or target
  prices.
- Do not infer company guidance from price movement or analyst commentary unless
  a cited source explicitly supports it.
- Do not mix A-share, 港股, ADS, or offshore financial statement units without
  clearly reconciling currency, share count, and listing line.
- Mark any unverified peer set as candidate peers until confirmed.
