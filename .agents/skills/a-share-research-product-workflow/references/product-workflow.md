# A-Share Research Product Workflow Reference

Use this reference for productized A-share workflows that combine market context,
watchlists, single-stock research, decision support, strategy checks, local
history, and report integrity checks.

## Workflow Selection

| User intent | Product path | Mode | Required outputs |
|---|---|---|---|
| Watchlist daily review | Watchlist daily path | `research` | `source_capability_matrix`, `market_context`, per-stock summary with `technical_analysis`, `report_integrity_status`, `qa_status` |
| Market context review | Market context path | `research` | `market_context`, `source_log`, `qa_status` |
| Single-stock research | Single-stock research path | `research` | delegate to `a-share-equity-research-workflow` |
| Investment decision support | Decision-support path | `decision_support` | `technical_analysis`, `decision_support`, `market_context`, evidence, triggers, invalidation, risk controls, `qa_status` |
| Strategy check | Strategy-check path | `research` or `decision_support` | selected strategy lens, `technical_analysis` for trend lens, evidence,反证, source gaps |
| Historical review | Post-review path | `decision_support` records only | prior decision state, hindsight facts, validation notes, no return promise |
| Report integrity check | Integrity path | selected mode | `report_integrity_status` |

## Watchlist Daily Path

1. Read the watchlist definition from `.research/watchlists/*.json` when the user
   points to one. If no watchlist exists, ask for tickers or produce a template.
2. Build `market_context` first: broad index context, sector or theme context,
   liquidity heat, risk appetite, and notable events.
3. For each security, run the lightest A-share single-stock path needed:
   - trend, liquidity, and daily/weekly/monthly technical state for daily
     monitoring;
   - thesis changes when a tracked thesis exists;
   - catalyst update when a catalyst calendar exists.
4. Output a concise Markdown daily review and optionally append a run record
   under `.research/runs/`.

## Decision-Support Path

1. Confirm `analysis_mode.mode = decision_support`.
2. Populate only decision-support states:
   `watch_only`, `research_candidate`, `hold_monitor`,
   `risk_control_review`, or `avoid_or_wait`.
3. Require supporting evidence, disconfirming evidence, trigger conditions,
   invalidation conditions, risk controls, confidence, missing data, source
   references, and `Not investment advice`.
4. Include `technical_analysis`; map technical signals into evidence, trigger
   conditions, invalidation conditions, and risk controls. Do not allow
   technical analysis to be the sole basis for `decision_state`.
5. Do not produce target prices, buy/sell ratings, personal position sizing, or
   return promises.

## Strategy-Check Path

Supported strategy lenses:

- `trend`: reuse `technical_analysis` for daily, weekly, and monthly trend,
  moving averages, drawdown, volatility, volume, support/resistance, and
  relative strength.
- `event`: filings, announcements, earnings, industry news, catalyst timing.
- `growth_quality`: revenue growth, margin, ROE/ROIC, operating cash flow, data
  gaps.
- `valuation_digestion`: PE/PB/PS/PCF, historical context, peer context when
  sourced.
- `thesis_falsification`: strongest supporting and disconfirming evidence.

Use these lenses as research frameworks, not trading systems.

## Historical Review Path

Historical review checks whether earlier decision-support evidence and triggers
were later confirmed, weakened, or contradicted. It does not claim trading skill
or simulate personalized returns unless the user provides a separate portfolio
framework.

Recommended horizons:

- 5 trading days: short-term trigger check.
- 20 trading days: thesis drift and risk-control check.
- 60 trading days: medium-term thesis validation.

## Report Integrity Path

Run the integrity checker for productized reports or schema records before
relying on them. A failed check should be disclosed and fixed or treated as a
data limitation.
