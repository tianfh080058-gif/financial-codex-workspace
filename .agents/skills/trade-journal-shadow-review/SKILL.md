---
name: trade-journal-shadow-review
description: >-
  Use when users need broker trade journal parsing, trading behavior diagnostics, FIFO roundtrip analysis, Shadow Account profile extraction, or post-trade review for 同花顺, 东方财富, 富途, generic CSV, or Excel exports. This skill uses trading_core journal adapters and Vibe-Trading-inspired Shadow Account concepts to produce win rate, profit/loss ratio, holding days, drawdown, overtrading, disposition effect, chasing momentum, anchoring, local .research artifacts, and Not investment advice without predicting returns or creating live trades.
---

# Trade Journal Shadow Review

Use this skill when the user asks to review personal trading records, parse a
broker export, diagnose behavior patterns, or create a Shadow Account profile
for simulation.

## Required Order

1. `financial-services-skill-router`
2. `.agents/SKILLS_INDEX.md`
3. `china-market-overlay` when the records include A-share, 港股, iFinD,
   同花顺, or AKShare context
4. This skill
5. `financial-output-qa-gate` before delivery or persistence

## Workflow Recipes And References

- Use `.agents/workflows/trade_journal_shadow_review.json` for productized
  broker journal review.
- Use `.agents/references/output-contract.md` for shared output fields.
- Use `.agents/references/display-profiles.md` for App/CLI/JSON presentation.
- Use `.agents/references/local-research-artifacts.md` for `.research/`
  artifact paths.

## Core Command

```bash
python3 -m trading_core.cli journal --file uploads/trades.xlsx
```

Supported inputs: `.csv`, `.xlsx`, `.xls`.

CLI output defaults to a Markdown review card for readability. Add
`--format json` when the full normalized object is needed for automation.

## App Conversation Display

When presenting results directly in the Codex app conversation, read
`references/app-conversation-display.md` and use the card-style Markdown layout:
one-line orientation, review card, behavior diagnostics table, Shadow Account
table, next review checklist, and compact data/QA section. Keep parser
assumptions, evidence gaps, and `Not investment advice`; do not show raw JSON
unless the user asks for it.

## Output Objects

- `profile`: trade count, closed roundtrips, average holding days, trade
  frequency, win rate, profit/loss ratio, total PnL, and top symbols.
- `behavior_diagnostics`: disposition effect, overtrading, chasing momentum,
  anchoring, and evidence or source gaps.
- `shadow_account_profile`: extracted rules from profitable closed roundtrips
  for simulation and review only.
- Local artifacts:
  - `.research/journals/*.analysis.json`
  - `.research/shadow/*.shadow.json`
- QA gate:
  - `financial-output-qa-gate`
  - `python3 tools/check_research_integrity.py --input path/to/journal.json --profile journal_shadow`

## Guardrails

- Do not infer missing trades, fees, prices, or quantities.
- Do not promise future performance from historical behavior.
- Do not generate personal position sizing or live order instructions.
- Label parsing limitations and any missing broker columns.
