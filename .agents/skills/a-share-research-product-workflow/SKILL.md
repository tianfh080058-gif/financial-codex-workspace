---
name: a-share-research-product-workflow
description: "Use when users need productized A-share research workflows in Codex, including watchlist daily reviews, market context reviews, daily/weekly/monthly technical analysis, explicit research versus decision_support mode routing, investment decision-support framing, strategy checks, local JSONL history, thesis review logs, backtest-style post reviews, report integrity checks, or .research artifact conventions while preserving source logs, QA, and no target-price/rating/buy-sell guardrails."
---

# A-Share Research Product Workflow

Use this product-layer skill after `financial-services-skill-router`,
`.agents/SKILLS_INDEX.md`, `china-market-overlay`, and
`a-share-equity-research-workflow` when the user asks for a productized A-share
research workflow rather than a one-off single-stock note.

This skill orchestrates existing skills. It does not replace the single-stock
workflow, `ifind-http-api`, `akshare`, valuation, comps, thesis, or catalyst
skills.

## When To Use

Use for requests such as:

- A-share watchlist daily reviews, daily stock analysis, or research dashboards.
- Market context reviews before single-stock analysis.
- Daily, weekly, and monthly technical analysis in watchlists, research, and
  decision-support outputs.
- Explicit `research` mode versus `decision_support` mode routing.
- Investment decision-support framing without target prices, ratings, personal
  position sizing, or buy/sell recommendations.
- Strategy checks such as trend, event-driven, growth quality, valuation
  digestion, or thesis falsification.
- Historical report references, thesis JSONL logs, and post-review/backtest
  style evaluations.
- Report integrity checks for source, date, unit, QA, and guardrails.

## Required Skill Order

1. `financial-services-skill-router`
2. `.agents/SKILLS_INDEX.md`
3. `china-market-overlay`
4. `a-share-equity-research-workflow`
5. This skill
6. Data and downstream skills as needed:
   - `ifind-http-api`
   - `akshare`
   - `a-share-valuation-template`
   - `a-share-comps-best-practice`
   - `vertical-equity-research-thesis-tracker`
   - `vertical-equity-research-catalyst-calendar`

## Reference Files

- Read `references/product-workflow.md` for watchlist, market context,
  decision-support, strategy-check, and historical-review paths.
- Read `references/local-artifacts.md` before writing or reading `.research/`
  JSONL files or local Markdown reports.
- Use the tools under `tools/` when deterministic JSONL storage, report
  integrity checks, or post-review summaries are needed.

## Core Rules

- Require explicit `analysis_mode`: `research` or `decision_support`.
- Default to `research` only when the user has not explicitly asked for
  investment decision support.
- In `research`, never output a `decision_state`.
- In `decision_support`, use only:
  - `watch_only`
  - `research_candidate`
  - `hold_monitor`
  - `risk_control_review`
  - `avoid_or_wait`
- Do not output target prices, buy/sell ratings, personal position sizing,
  return promises, unsourced consensus, or unsourced guidance.
- Technical analysis can support evidence, trigger conditions, invalidation
  conditions, and confidence, but it must not be the sole basis for a
  `decision_state`.
- Store proprietary or personal local history under `.research/`, which should
  remain gitignored.
- Every productized output must include source logs, data limitations, QA checks,
  and `Not investment advice` when it relates to investment decisions.

## Output Requirements

Productized outputs should include the objects relevant to the task:

- `analysis_mode`
- `source_capability_matrix`
- `market_context`
- `security_master`
- `source_log`
- `market_snapshot`
- `technical_analysis` when market data is used for stock research or decision
  support
- `financial_snapshot` when sourced
- `valuation_snapshot` when sourced
- `peer_set` when evaluated
- `thesis_tracker` when thesis evidence is tracked
- `decision_support` only in `decision_support` mode
- `report_integrity_status`
- `review_history_ref` when local JSONL or report files are used
- `qa_status`
