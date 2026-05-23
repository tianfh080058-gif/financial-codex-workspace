---
name: trading-decision-engine
description: >-
  Use when users need productized trading decision support, conditional buy/sell-point style planning, Vibe-Trading backtest validation, Alpha Zoo factor screening, or full-market stock monitoring through this workspace. This skill routes through financial-services-skill-router, china-market-overlay for China securities, and trading_core CLI adapters to produce source-backed decision_card, conditional_trade_plan, execution feasibility checks, source logs, QA status, and Not investment advice without target prices, ratings, personal position sizing, return promises, or unconditional trade instructions.
---

# Trading Decision Engine

Use this skill for daily trading decision-support workflows that need the
project-native `trading_core` adapter, including HKUDS/Vibe-Trading bridge
capabilities.

## Required Order

1. `financial-services-skill-router`
2. `.agents/SKILLS_INDEX.md`
3. `china-market-overlay` when the security is A-share, 港股, China-linked, iFinD,
   同花顺, or AKShare related
4. `a-share-equity-research-workflow` for A-share single-stock schema rules
5. `a-share-research-product-workflow` for decision-support packaging
6. This skill
7. `financial-output-qa-gate` before delivery or persistence

## Workflow Recipes And References

- Use `.agents/workflows/a_share_decision_support.json` for conditional decision
  cards.
- Use `.agents/workflows/vibe_backtest_validation.json` for backtest validation.
- Use `.agents/workflows/alpha_factor_bench.json` for Alpha Zoo screening.
- Use `.agents/references/output-contract.md` for shared output fields.
- Use `.agents/references/data-capability-registry.md` for source priority and
  fallback disclosure.
- Use `.agents/references/display-profiles.md` for App/CLI/JSON presentation.
- Use `.agents/references/local-research-artifacts.md` for `.research/` paths.

## Core Commands

Use these commands from the project root when deterministic artifacts are
needed:

```bash
python3 -m trading_core.cli decision --ticker 300033.SZ --market a_share --horizon 20d --mode conditional_strong
python3 -m trading_core.cli backtest --ticker 300033.SZ --strategy technical_breakout --start 2024-01-01 --end 2026-05-23
python3 -m trading_core.cli alpha-bench --universe csi300 --zoo gtja191 --period 2021-2026
python3 -m trading_core.cli review --path .research/runs/decision_support.jsonl --horizon 20
```

For local OHLCV files, add `--ohlcv path/to/ohlcv.csv` or
`--ohlcv path/to/ohlcv.json`.

CLI output defaults to Markdown cards for human review. Add `--format json` for
the full machine-readable schema, and add `--output path.json` when the full
record should be saved while the terminal remains readable.

## App Conversation Display

When presenting results directly in the Codex app conversation, read
`references/app-conversation-display.md` and use the card-style Markdown layout:
one-line orientation, decision card, conditional plan table, evidence matrix,
execution constraints, next checks, and compact data/QA section. Keep the same
source quality and guardrails as the JSON schema; do not show raw JSON unless
the user asks for it.

## Output Rules

- `decision_card` is the concise user-facing summary.
- `conditional_trade_plan` may include concrete `trigger_level`,
  `invalidation_level`, and `risk_control_level`, but each level must be
  conditional, source-backed, and marked as not a target price.
- A-share outputs should include `execution_feasibility` for T+1, price limits,
  100-share lots, costs, and slippage assumptions.
- `backtest_validation` is evidence only. Do not convert factor or backtest
  results into standalone buy/sell recommendations.
- Every investment-related output must include `Not investment advice`, source
  logs, missing data, and QA status.
- Run the final record through `financial-output-qa-gate` or
  `tools/check_research_integrity.py --profile a_share_decision` before treating
  it as productized output.

## Guardrails

- Do not invent market prices, financials, events, factors, or backtest results.
- Do not output target prices, buy/sell ratings, personal position sizing, or
  return promises.
- Do not issue unconditional trade instructions. Use conditional review language
  with triggers, invalidation, and risk controls.
- If current market data is unavailable, output source gaps and a framework
  rather than filling values.
