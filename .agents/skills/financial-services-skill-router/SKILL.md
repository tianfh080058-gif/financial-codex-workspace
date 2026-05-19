---
name: financial-services-skill-router
description: >-
  Router for all financial services, accounting, investing, capital markets,
  private equity, investment banking, wealth management, fund administration,
  KYC, valuation, earnings, equity research, and financial modeling requests.
  Use when any user request involves financial analysis, financial documents,
  spreadsheets, presentations, market data, company analysis, transaction work,
  portfolio review, or regulated financial workflows, before selecting a more
  specific financial-services skill.
---

# Financial Services Skill Router

Use this router first for any financial-services task. Its job is to identify the
right domain skill, protect data integrity, and prevent unsupported financial
claims.

## Routing Workflow

1. Classify the request by domain: financial analysis, equity research,
   investment banking, private equity, wealth management, fund administration,
   KYC/operations, market data, earnings, valuation, or accounting close.
2. Identify the artifact: spreadsheet, model, deck, memo, report, checklist,
   dashboard, tracker, reconciliation, or written analysis.
3. Check data requirements. Use user-provided files, configured data providers,
   filings, or verified current sources. Do not invent financial, market,
   company, client, accounting, or regulatory data.
4. Read `references/skill-index.md` when the best downstream skill is not
   obvious, then load the most specific matching skill under `.agents/skills/`.
5. If multiple skills apply, use the narrowest domain skill first, then supporting
   authoring or audit skills such as spreadsheet, presentation, or deck QA.
6. Preserve citations, assumptions, dates, source gaps, and audit notes in the
   final artifact or response.

## Index-First Skill Selection

- Before selecting any downstream skill, read `.agents/SKILLS_INDEX.md`.
- Use the index to identify candidate downstream skills by workflow group,
  directory, name, and description.
- If the index returns too many candidates, narrow the set to the 3-7 downstream
  skills that are truly needed for the user's task.
- Do not read every skill for completeness. Read the full `SKILL.md` only for
  this router and the selected downstream skills.
- If a task lacks required data, first produce a model framework, analysis
  outline, or data request checklist. Do not invent missing financial data.

## Common Routes

| User intent | Prefer these skill families |
|---|---|
| DCF, LBO, 3-statement, comps, model QA | financial-analysis or model-builder skills |
| Earnings preview, earnings recap, model update | equity-research or earnings-reviewer skills |
| Pitch deck, CIM, teaser, buyer list, process letter | investment-banking or pitch-agent skills |
| IC memo, diligence, returns, portfolio monitoring | private-equity or valuation-reviewer skills |
| Client review, financial plan, proposal, rebalance | wealth-management or meeting-prep-agent skills |
| NAV, GL recon, close, variance commentary | fund-admin, gl-reconciler, or month-end-closer skills |
| KYC document parsing or risk rules | operations or kyc-screener skills |
| Macro, rates, bonds, FX, options | partner LSEG skills |
| Tear sheets, funding digests, S&P-backed previews | partner S&P Global skills |
| China market, A-share, 港股, 同花顺, iFinD, AKShare, Chinese disclosures | `china-market-overlay`, then `ifind-http-api` or `akshare`, then the narrow valuation, comps, earnings, or modeling skill |

## China Market Routes

For tasks involving A shares, 港股, Chinese listed companies, Chinese-language
filings, RMB financials, 同花顺, iFinD, AKShare, 巨潮资讯, 上交所, 深交所, 北交所,
港交所, or China market tickers, route in this order:

1. `financial-services-skill-router`.
2. `china-market-overlay`.
3. A data source skill, usually `ifind-http-api` for licensed 同花顺/iFinD data or
   `akshare` for public data prototypes and cross-checks.
4. The narrow downstream skill:
   - DCF or intrinsic valuation: `vertical-financial-analysis-dcf-model` plus
     `a-share-valuation-template` for A-share companies.
   - Comparable company analysis: `vertical-financial-analysis-comps-analysis`
     plus `a-share-comps-best-practice`.
   - Earnings analysis: `vertical-equity-research-earnings-analysis` with China
     disclosure mapping from `china-market-overlay`.
5. Supporting authoring or audit skills only when the artifact requires them.

Do not force SEC, EDGAR, 10-K, or 10-Q assumptions onto China market companies.
Map those requirements to annual reports, interim reports, quarterly reports,
exchange disclosures, company announcements, or clearly mark the missing source.

## Required Guardrails

- Never fabricate prices, filings, estimates, financial statements, market data,
  ownership, client facts, or regulatory requirements.
- Treat current prices, rates, macro indicators, company facts, laws, and rules as
  time-sensitive; verify them before relying on them.
- Label assumptions clearly and separate them from sourced facts.
- For spreadsheets and models, prefer formulas over hardcoded derived values and
  run the relevant audit or validation workflow before delivery.
- For client-ready decks, reports, and memos, perform a consistency pass for
  numbers, dates, source labels, and unresolved placeholders.

## Router Output Requirements

Every router response must include:

- Task classification
- Candidate skills considered
- Selected skills
- Rejected skills and reason
- Execution order
- Required inputs
- Missing data
- QA plan

For high-risk financial outputs, also include:

- Not investment advice
- Data limitations
- Assumptions
