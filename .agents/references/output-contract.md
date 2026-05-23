# Financial Output Contract

Use this shared contract when multiple skills contribute to one financial
workflow. Domain skills may add their own fields, but high-risk financial output
should still map back to these objects so routing, QA, display, and local
artifacts stay consistent.

## Core Objects

| Object | Purpose | Required When |
|---|---|---|
| `analysis_mode` | Declares `research`, `decision_support`, `journal_review`, `backtest_validation`, or `alpha_bench`. | Every productized workflow. |
| `security_master` | Identifiers, exchange, board, currency, company name, and listing status. | Security-level market or company analysis. |
| `source_log` | Source name, endpoint/interface, parameters, retrieval time, source status, and gaps. | Every financial output using external or user data. |
| `source_capability_matrix` | Data provider coverage, priority, fallback, known limits, and field coverage. | Data retrieval, cross-check, trading, factor, and backtest workflows. |
| `evidence_matrix` | Structured evidence by dimension, conclusion, source reference, and missing data. | Research, decision support, journal review, and validation outputs. |
| `decision_card` | Concise human-facing decision-support summary. | `decision_support` workflows only. |
| `conditional_trade_plan` | Conditional trigger, invalidation, risk-control, exit/reduce condition, time validity, source refs, and assumptions. | Only when the user asks for buy/sell-point style decision support. |
| `qa_status` | Pass/warn/fail status, checks performed, unresolved gaps, and guardrail result. | Every productized financial output. |
| `display_card` | App/CLI presentation-friendly subset, without dropping source or QA essentials. | App or CLI human-facing output. |
| `machine_record` | Full JSON object used for persistence, replay, audit, or automation. | Stored or automated workflows. |
| `artifact_refs` | Paths to saved JSON, JSONL, Markdown, backtest, journal, or shadow-account artifacts. | Any workflow that writes `.research/` files. |

## Minimum High-Risk Fields

Any trading, investment, valuation, portfolio, credit, or client-facing output
must include:

- `source_log` with source names, retrieval timestamps, and explicit gaps.
- `qa_status` with guardrail checks performed.
- `not_investment_advice: true` or equivalent QA flag.
- `missing_data` or an explicit statement that no material data gaps were found.
- `retrieved_at` or source-specific timestamp for market data and filings.
- Clear separation between sourced facts, assumptions, and model output.

## Decision Support Guardrails

`conditional_trade_plan` may include concrete trigger, invalidation, and
risk-control levels only when each level is conditional, source-backed, and
marked as not being a target price. Do not output:

- Target prices or price targets.
- Buy/sell ratings.
- Personal position sizing.
- Return promises.
- Unconditional instructions such as immediate buy or immediate sell.

## A-Share Mapping

A-share workflows keep their existing schema fields, including
`market_snapshot`, `technical_analysis`, `decision_support`,
`execution_feasibility`, and `backtest_validation`. Map them to this contract as
follows:

| A-share Field | Shared Contract Mapping |
|---|---|
| `market_snapshot`, `security_master` | `security_master` and `evidence_matrix.market` |
| `technical_analysis` | `evidence_matrix.technical` |
| `decision_support` | `decision_card` and `evidence_matrix` |
| `conditional_trade_plan` | `conditional_trade_plan` |
| `report_integrity_status`, `qa_status` | `qa_status` |
| `review_history_ref`, local paths | `artifact_refs` |

## Display Boundary

Human-facing output should use `display_card` and the relevant display profile.
Raw `machine_record` JSON should be shown only when the user asks for full JSON
or when a CLI command uses `--format json`.
