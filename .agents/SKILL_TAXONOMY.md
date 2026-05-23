# Skill Taxonomy

This taxonomy adds routing metadata without moving or renaming existing skill
directories. Validators should treat explicitly listed skills as pinned; other
skills inherit a default tag from naming patterns until they are promoted into a
workflow recipe.

## Tags

| Tag | Meaning |
|---|---|
| `router` | Classifies requests and selects downstream skills. |
| `market_overlay` | Adapts generic workflows to market-specific rules. |
| `data_provider` | Retrieves, validates, or cross-checks data. |
| `domain_workflow` | Performs a focused analytical workflow. |
| `product_workflow` | Orchestrates repeatable productized flows. |
| `qa_gate` | Checks output integrity and guardrails. |
| `display` | Defines human-facing presentation behavior. |
| `artifact_tool` | Creates, stores, validates, or reviews local artifacts. |
| `authoring` | Produces spreadsheets, decks, documents, or templates. |

## Pinned Skills

| Directory | Tags | Notes |
|---|---|---|
| `financial-services-skill-router` | `router`, `qa_gate` | Required first for financial tasks. |
| `china-market-overlay` | `market_overlay`, `qa_gate` | Required for A-share, 港股, iFinD, AKShare, and China disclosures. |
| `ifind-http-api` | `data_provider` | Licensed 同花顺/iFinD data source. |
| `akshare` | `data_provider` | Public data fallback and prototype source. |
| `a-share-equity-research-workflow` | `domain_workflow`, `qa_gate` | A-share single-stock schema and research workflow. |
| `a-share-research-product-workflow` | `product_workflow`, `artifact_tool` | Productized A-share reviews and decision-support workflows. |
| `trading-decision-engine` | `product_workflow`, `artifact_tool`, `display` | Conditional decision cards, Vibe bridge, alpha bench, and CLI workflows. |
| `trade-journal-shadow-review` | `domain_workflow`, `artifact_tool`, `display` | Broker journal parsing and Shadow Account review. |
| `financial-output-qa-gate` | `qa_gate` | Final output checker for source, QA, and investment guardrails. |
| `a-share-valuation-template` | `domain_workflow`, `qa_gate` | A-share valuation framework. |
| `a-share-comps-best-practice` | `domain_workflow`, `qa_gate` | A-share comps and peer selection. |
| `vertical-equity-research-thesis-tracker` | `domain_workflow`, `artifact_tool` | Thesis evidence and review tracking. |
| `vertical-equity-research-catalyst-calendar` | `domain_workflow` | Catalyst tracking. |

## Inheritance Rules

| Pattern | Default Tags |
|---|---|
| `vertical-*-xlsx-author`, `agent-*-xlsx-author`, `*-pptx-author` | `authoring`, `artifact_tool` |
| `*-audit-xls`, `*-ib-check-deck` | `qa_gate`, `artifact_tool` |
| `*-comps-analysis`, `*-dcf-model`, `*-lbo-model`, `*-earnings-*` | `domain_workflow` |
| `partner-*` | `data_provider`, `domain_workflow` |
| `vertical-operations-kyc-*`, `agent-kyc-*` | `domain_workflow`, `qa_gate` |

## Governance

- Prefer adding taxonomy tags and workflow recipes over renaming skill
  directories.
- Every workflow recipe must reference only existing skill directories.
- High-risk workflows should include at least one `qa_gate` skill.
- New productized workflows should define a display profile and artifact policy.
