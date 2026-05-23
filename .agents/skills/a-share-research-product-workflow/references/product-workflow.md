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
| Conditional strong plan | Decision-support path | `decision_support` | `decision_card`, `conditional_trade_plan`, `technical_analysis`, source logs, invalidation, risk controls, `qa_status` |
| Vibe backtest bridge | Backtest-validation path | `decision_support` or `research` | `backtest_validation`, Vibe `run_dir`, metrics, validation limitations |
| Trade journal / Shadow Account | Journal-review path | `research` | journal profile, behavior diagnostics, shadow profile, source limitations |
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
5. When the user asks for buy/sell points, use `conditional_trade_plan` rather
   than ratings or unconditional trade instructions. Levels must be concrete,
   source-backed, conditional, and labeled as not target prices.
6. Do not produce target prices, buy/sell ratings, personal position sizing, or
   return promises.

## Conditional Strong Plan Path

Use this path when the user explicitly asks for actionable buy/sell-point style
decision support.

1. Start with sourced market data and `technical_analysis` across daily, weekly,
   and monthly timeframes.
2. Build `decision_card` with the allowed `decision_state`, horizon, setup
   quality, evidence, risks, and next review.
3. Build `conditional_trade_plan` with:
   `action_type`, `trigger_level`, `trigger_condition`,
   `invalidation_level`, `risk_control_level`,
   `exit_or_reduce_condition`, `time_validity`, `source_ref`, and
   `assumptions`.
4. For A shares, include an execution-feasibility check for T+1, price limits,
   100-share lots, costs, and slippage assumptions.
5. Run the integrity checker. A failed check must be treated as a blocking QA
   issue, not hidden.

## Backtest-Validation Path

Use the project `trading_core` adapter for Vibe-Trading integration.

1. Generate a Vibe-compatible `run_dir` under `.research/vibe_runs/`.
2. Write `config.json` and `code/signal_engine.py` through the adapter.
3. Prefer iFinD-sourced OHLCV panels. Use Vibe original loaders only as
   fallback or cross-check.
4. Map Vibe or local bridge metrics into `backtest_validation`, including
   Sharpe, max drawdown, win rate, Monte Carlo, Bootstrap, and Walk-Forward
   status where available.
5. Treat backtests as validation evidence only; never convert a backtest result
   into a standalone security-level recommendation.

## Journal-Review Path

1. Parse broker CSV/XLSX exports into normalized trades.
2. Pair closed trades FIFO and compute win rate, profit/loss ratio, holding
   days, total PnL, and drawdown.
3. Diagnose behavior patterns: disposition effect, overtrading, chasing
   momentum, anchoring, and source gaps.
4. Extract Shadow Account rules from profitable roundtrips for simulation and
   review only.
5. Store local artifacts under `.research/journals/` and `.research/shadow/`.

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
