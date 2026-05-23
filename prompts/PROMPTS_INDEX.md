# Prompts Index

This index links prompt templates to workflow recipes, skills, CLI commands, and
output/display contracts. Keep it updated when adding prompts, recipes, or
productized CLI flows.

| Prompt | Workflow Recipe | Primary Skills | CLI / Tooling | Display / Contract |
|---|---|---|---|---|
| `prompts/daily-a-share-decision-pipeline-zh.md` | `.agents/workflows/daily_a_share_decision_pipeline.json` | `financial-services-skill-router`, `china-market-overlay`, `a-share-equity-research-workflow`, `a-share-research-product-workflow`, `trading-decision-engine`, `financial-output-qa-gate` | `python3 -m trading_core.cli watchlist`, `python3 -m trading_core.cli decision`, `tools/check_research_integrity.py --profile a_share_decision` | `app_card`, `.agents/references/output-contract.md` |
| `prompts/watchlist-management-zh.md` | `.agents/workflows/watchlist_daily_review.json` | `financial-services-skill-router`, `china-market-overlay`, `a-share-research-product-workflow`, `financial-output-qa-gate` | `python3 -m trading_core.cli watchlist` | `app_card`, `.agents/references/watchlist-management.md` |
| `prompts/trading-decision-conditional-zh.md` | `.agents/workflows/a_share_decision_support.json` | `financial-services-skill-router`, `china-market-overlay`, `a-share-research-product-workflow`, `trading-decision-engine`, `financial-output-qa-gate` | `python3 -m trading_core.cli decision`, `tools/check_research_integrity.py --profile a_share_decision` | `app_card`, `.agents/references/output-contract.md` |
| `prompts/a-share-watchlist-daily-review-zh.md` | `.agents/workflows/watchlist_daily_review.json` | `financial-services-skill-router`, `china-market-overlay`, `a-share-research-product-workflow`, `financial-output-qa-gate` | `python3 -m trading_core.cli watchlist` | `app_card`, `.agents/references/output-contract.md` |
| `prompts/trade-journal-shadow-review-zh.md` | `.agents/workflows/trade_journal_shadow_review.json` | `financial-services-skill-router`, `trade-journal-shadow-review`, `financial-output-qa-gate` | `python3 -m trading_core.cli journal`, `tools/check_research_integrity.py --profile journal_shadow` | `app_card`, `.agents/references/output-contract.md` |
| `prompts/vibe-backtest-review-zh.md` | `.agents/workflows/vibe_backtest_validation.json` | `financial-services-skill-router`, `a-share-research-product-workflow`, `trading-decision-engine`, `financial-output-qa-gate` | `python3 -m trading_core.cli backtest` | `cli_markdown`, `.agents/references/output-contract.md` |
| `prompts/alpha-factor-bench-zh.md` | `.agents/workflows/alpha_factor_bench.json` | `financial-services-skill-router`, `a-share-research-product-workflow`, `trading-decision-engine`, `financial-output-qa-gate` | `python3 -m trading_core.cli alpha-bench` | `cli_markdown`, `.agents/references/output-contract.md` |
| `prompts/a-share-stock-research-zh.md` | `.agents/workflows/a_share_deep_research.json` | `financial-services-skill-router`, `china-market-overlay`, `a-share-equity-research-workflow`, `a-share-research-product-workflow`, `financial-output-qa-gate` | `tools/check_research_integrity.py --profile a_share_decision` | `audit_appendix`, `.agents/references/output-contract.md` |
| `prompts/a-share-thesis-check-zh.md` | `.agents/workflows/a_share_deep_research.json` | `financial-services-skill-router`, `china-market-overlay`, `a-share-equity-research-workflow`, `a-share-research-product-workflow`, `financial-output-qa-gate` | `tools/check_research_integrity.py --profile a_share_decision` | `audit_appendix`, `.agents/references/output-contract.md` |
| `prompts/a-share-report-integrity-check-zh.md` | `.agents/workflows/a_share_deep_research.json` | `financial-services-skill-router`, `china-market-overlay`, `a-share-equity-research-workflow`, `a-share-research-product-workflow`, `financial-output-qa-gate` | `tools/check_research_integrity.py --profile a_share_decision` | `audit_appendix`, `.agents/references/output-contract.md` |
| `prompts/app-conversation-display-zh.md` | Shared display guidance | `trading-decision-engine`, `trade-journal-shadow-review`, `financial-output-qa-gate` | `trading_core.renderers` | `.agents/references/display-profiles.md` |

## Governance Rules

- Every productized prompt should map to one workflow recipe.
- Every mapped workflow recipe should include `financial-output-qa-gate` when
  output is investment, trading, valuation, portfolio, credit, or client-facing.
- CLI references must point to existing `trading_core.cli` subcommands or tools.
- App display prompts must preserve source logs, missing data, QA, and
  `Not investment advice`.
