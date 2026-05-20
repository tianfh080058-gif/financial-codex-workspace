---
name: a-share-equity-research-workflow
description: "Use when users need A-share single-stock equity research, stock deep dives, China A-share thesis checks, iFinD and AKShare cross-checks, catalyst tracking, watchlist updates, or standardized A-share research data schemas that connect market data, financial disclosures, valuation, peers, thesis evidence, source logs, and QA without inventing financial, market, company, consensus, guidance, or target-price data."
---

# A-Share Equity Research Workflow

Use this skill after `financial-services-skill-router` and
`china-market-overlay` for China A-share equity research workflows.

This skill is an orchestration layer. It does not replace `ifind-http-api`,
`akshare`, `a-share-valuation-template`, `a-share-comps-best-practice`, or
`vertical-equity-research-*`; it tells Codex how to connect them using a
consistent A-share schema and a repeatable single-stock workflow.

## When To Use

Use for requests such as:

- A-share single-stock deep dives, quick takes, or stock trend reviews.
- iFinD / AKShare cross-checks for the same A-share security.
- A-share thesis checks, catalyst calendars, watchlist updates, or evidence logs.
- Requests to standardize A-share research outputs, data schemas, source logs,
  or QA checks.

Do not use for non-China securities unless the user explicitly wants to reuse
the schema pattern outside A shares.

## Required Skill Order

1. `financial-services-skill-router`
2. `.agents/SKILLS_INDEX.md`
3. `china-market-overlay`
4. This skill
5. Data source skills:
   - `ifind-http-api` for licensed 同花顺/iFinD data.
   - `akshare` for public data prototypes or cross-checks.
6. Downstream analysis skills only when needed:
   - `a-share-valuation-template`
   - `a-share-comps-best-practice`
   - `vertical-equity-research-earnings-analysis`
   - `vertical-equity-research-model-update`
   - `vertical-equity-research-thesis-tracker`
   - `vertical-equity-research-catalyst-calendar`

## Reference Files

- Read `references/schema.md` when normalizing A-share research data, designing
  outputs, or comparing iFinD and AKShare.
- Read `references/pipeline.md` when the user asks for a single-stock deep dive,
  full A-share research workflow, thesis review, catalyst tracking, or a
  watchlist-style update.
- Use `references/example-minimal-yunlu.json` as a structure example only; do
  not reuse the numbers without refreshing data.
- Use `references/example-missing-financials.json` to model missing-data
  handling without fabricating financials.

## Core Workflow

1. Identify the security and confirm ticker, exchange, board, industry,
   currency, unit, fiscal period, trading date, and price adjustment basis.
2. Select data sources. Prefer user files and official disclosures for facts,
   iFinD for licensed data, and AKShare for public-data prototypes or
   cross-checks.
3. Populate the schema objects needed for the request. At minimum include
   `security_master`, `source_log`, and `qa_status`; include `market_snapshot`
   for price work and `financial_snapshot` / `valuation_snapshot` only when
   sourced.
4. For single-stock research, follow the nine-step pipeline in
   `references/pipeline.md`.
5. Separate sourced facts, calculations, assumptions, inferences, and missing
   data. Do not fill gaps with estimates unless the user explicitly labels them
   as assumptions.
6. For investment, valuation, trading, portfolio, or thesis outputs, include
   `Not investment advice`, data limitations, assumptions, and QA checks.

## Required Output Notes

Every output using this skill must show:

- Selected skills and execution order.
- Data sources, endpoint/interface names, parameters, retrieval timestamp, and
  trading date where applicable.
- Currency, unit, fiscal period, exchange, and adjustment basis.
- Missing data and source limitations.
- QA checks performed.

## Guardrails

- Do not invent market prices, financial statements, consensus, guidance,
  target prices, peer membership, announcement content, or thesis evidence.
- Do not silently mix iFinD and AKShare values. Explain differences by source,
  timestamp, unit, adjustment basis, endpoint, or missing data.
- Do not output a rating, target price, or buy/sell recommendation unless the
  required source-backed inputs or user-confirmed assumptions are present.
