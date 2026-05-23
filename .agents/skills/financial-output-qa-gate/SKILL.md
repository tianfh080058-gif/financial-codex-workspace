---
name: financial-output-qa-gate
description: >-
  Use when financial, investment, trading, valuation, accounting, market-data, broker-journal, or client-facing outputs need a final QA gate before delivery or persistence. This skill checks source logs, timestamps, missing data, Not investment advice, forbidden target-price/rating/position-sizing/return-promise language, unconditional trade instructions, artifact references, and output-contract compliance without performing new analysis or inventing data.
---

# Financial Output QA Gate

Use this skill after the domain workflow has produced a draft output and before
the result is delivered as a productized financial artifact or stored under
`.research/`.

This skill is a checker, not an analyst. Do not add new market views, valuation
judgments, recommendations, or trade ideas while using it.

## Required Inputs

- Draft output or machine-readable record.
- Expected workflow recipe from `.agents/workflows/` when available.
- Shared contract from `.agents/references/output-contract.md`.
- Data registry from `.agents/references/data-capability-registry.md` when
  market data is used.
- Display profile from `.agents/references/display-profiles.md` when the output
  will be shown in App or CLI.

## Checks

- `source_log` exists and records source name, endpoint/interface, parameters,
  retrieval time, status, and missing fields.
- Market data includes trading date, retrieval timestamp, unit/currency, and
  adjustment basis when relevant.
- `qa_status` exists and records pass/warn/fail checks.
- `Not investment advice` is present for investment, trading, valuation,
  portfolio, credit, or client-facing conclusions.
- Missing data and source gaps are explicit.
- Artifact references exist when the workflow writes `.research/` outputs.
- The output does not contain target prices, buy/sell ratings, personal
  position sizing, return promises, or unconditional buy/sell instructions.
- Technical analysis, factors, or backtests are not presented as a standalone
  reason to trade.
- App or CLI display uses the selected display profile without hiding material
  source gaps or failed QA checks.

## Tooling

Use `tools/check_research_integrity.py` when a JSON record is available:

```bash
python3 tools/check_research_integrity.py --input path/to/record.json --profile a_share_decision
python3 tools/check_research_integrity.py --input path/to/record.json --profile general_finance
python3 tools/check_research_integrity.py --input path/to/record.json --profile journal_shadow
```

## Output

Return a compact QA result:

- `status`: `pass`, `warn`, or `fail`.
- `blocking_issues`: issues that must be fixed before delivery.
- `warnings`: non-blocking limitations.
- `checks_performed`: checklist summary.
- `source_gaps`: unresolved data gaps.
- `guardrail_status`: whether unsupported financial outputs were blocked.
