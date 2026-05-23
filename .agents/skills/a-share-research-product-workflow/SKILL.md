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
- Daily watchlist-to-decision pipelines that first screen Top10, deep-research
  the default Top5, and send only evidence-sufficient names into conditional
  decision support.
- Market context reviews before single-stock analysis.
- Daily, weekly, and monthly technical analysis in watchlists, research, and
  decision-support outputs.
- Explicit `research` mode versus `decision_support` mode routing.
- Investment decision-support framing without target prices, ratings, personal
  position sizing, or buy/sell recommendations.
- Conditional strong planning with concrete trigger, invalidation, and
  risk-control levels when the user asks for buy/sell-point style support,
  while preserving the no target-price/rating/personal-sizing guardrails.
- Vibe-Trading adapter workflows for backtest validation, Alpha Zoo screening,
  trade journal review, and Shadow Account summaries through `trading_core`.
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

- Prefer a matching workflow recipe in `.agents/workflows/` before assembling a
  productized output manually.
- Use `.agents/workflows/daily_a_share_decision_pipeline.json` when the user
  wants the full watchlist -> deep research -> evidence gate -> decision support
  loop while preserving the individual sub-workflows.
- Read `.agents/references/output-contract.md` for shared cross-skill output
  fields.
- Read `.agents/references/data-capability-registry.md` before selecting iFinD,
  AKShare, local files, or Vibe fallback sources.
- Read `.agents/references/display-profiles.md` for App, CLI, JSON, or audit
  presentation rules.
- Read `.agents/references/local-research-artifacts.md` before writing
  `.research/` artifacts.
- Read `.agents/references/watchlist-management.md` when the task involves
  creating, editing, grouping, or using local watchlists from Codex desktop
  conversations.
- Read `references/product-workflow.md` for watchlist, market context,
  decision-support, strategy-check, and historical-review paths.
- Read `references/local-artifacts.md` before writing or reading `.research/`
  JSONL files or local Markdown reports.
- When the output will be shown directly in the Codex app conversation and
  `trading-decision-engine` is selected, use that skill's
  `references/app-conversation-display.md` for the final readable layout.
- Use the tools under `tools/` when deterministic JSONL storage, report
  integrity checks, or post-review summaries are needed.
- Use `financial-output-qa-gate` before delivering or storing high-risk
  decision-support, backtest, alpha, journal, or valuation-adjacent outputs.

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
- `conditional_trade_plan` is allowed only in `decision_support` mode and must
  be conditional, sourced, and paired with invalidation and risk-control logic.
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
- `decision_card` only in `decision_support` mode when productized decision
  packaging is requested
- `conditional_trade_plan` only in `decision_support` mode when the user asks
  for conditional trigger/risk levels
- `backtest_validation` when a Vibe bridge or local validation run is sourced
- `report_integrity_status`
- `review_history_ref` when local JSONL or report files are used
- `qa_status`
