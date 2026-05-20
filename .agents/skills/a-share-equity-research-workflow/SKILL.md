---
name: a-share-equity-research-workflow
description: "Use when users need A-share single-stock equity research, stock deep dives, China A-share thesis checks, technical analysis across daily/weekly/monthly OHLCV data, explicit research or decision_support modes, iFinD and AKShare cross-checks, catalyst tracking, watchlist inputs, market context, standardized A-share schemas, source capability matrices, decision support guardrails, report integrity checks, or historical thesis references without inventing financial, market, company, consensus, guidance, target-price, rating, or buy/sell data."
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
- Technical analysis across daily, weekly, and monthly OHLCV data.
- Explicit `research` mode or `decision_support` mode analysis.
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
7. Product-layer skill only when needed:
   - `a-share-research-product-workflow` for watchlist daily reviews, market
     context, historical report references, strategy checks, decision-support
     packaging, or report integrity checks.

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
   Also confirm `analysis_mode` explicitly as `research` or
   `decision_support`; default to `research` only when the user did not ask for
   investment decision support.
2. Select data sources. Prefer user files and official disclosures for facts,
   iFinD for licensed data, and AKShare for public-data prototypes or
   cross-checks. Populate `source_capability_matrix` when source availability,
   failures, or fallback paths affect the analysis.
3. Populate the schema objects needed for the request. At minimum include
   `security_master`, `source_log`, and `qa_status`; include `market_snapshot`
   and `technical_analysis` for price work and
   `financial_snapshot` / `valuation_snapshot` only when sourced. Include
   `market_context`, `decision_support`,
   `report_integrity_status`, or `review_history_ref` only when relevant.
4. For single-stock research, follow the nine-step pipeline in
   `references/pipeline.md`.
5. Separate sourced facts, calculations, assumptions, inferences, and missing
   data. Do not fill gaps with estimates unless the user explicitly labels them
   as assumptions.
6. In `research` mode, include a `Technical Analysis（技术分析）` section when
   market data is available, but do not output `decision_support.decision_state`,
   buy/sell language, personal position sizing, or target prices.
7. In `decision_support` mode, include `technical_analysis` and map technical
   signals into evidence, trigger conditions, invalidation conditions, and risk
   controls. Technical analysis must not be the sole basis for `decision_state`.
8. In `decision_support` mode, output only decision-support states, evidence,
   disconfirming evidence, trigger conditions, invalidation conditions, risk
   controls, confidence, data gaps, `Not investment advice`, assumptions, and
   QA checks.

## Required Output Notes

Every output using this skill must show:

- Selected skills and execution order.
- Data sources, endpoint/interface names, parameters, retrieval timestamp, and
  trading date where applicable.
- Currency, unit, fiscal period, exchange, and adjustment basis.
- Missing data and source limitations.
- Explicit `analysis_mode`.
- `technical_analysis` with daily, weekly, and monthly timeframes when market
  data is used for single-stock research or decision support.
- QA checks performed.

## Guardrails

- Do not invent market prices, financial statements, consensus, guidance,
  target prices, peer membership, announcement content, or thesis evidence.
- Do not silently mix iFinD and AKShare values. Explain differences by source,
  timestamp, unit, adjustment basis, endpoint, or missing data.
- Do not output a rating, target price, buy/sell recommendation, personal
  position size, or return promise. In `decision_support` mode, use only the
  allowed decision states defined in `references/schema.md`.
