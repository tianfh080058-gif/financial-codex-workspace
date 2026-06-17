# Local Research Artifacts

Use `.research/` for local research, decision-support history, backtests,
journals, and shadow-account outputs. These files may contain personal notes,
watchlists, broker exports, or proprietary analysis and should remain gitignored
unless the user explicitly asks otherwise.

## Directory Convention

| Path | Purpose |
|---|---|
| `.research/watchlists/` | Watchlist definitions, groups, notes, review preferences, and desktop conversation-managed pools. |
| `.research/alerts/` | Local conditional price alert rules and alert check JSONL; never an order blotter. |
| `.research/briefs/` | Daily watchlist market briefs in JSON/Markdown with source gaps and QA status. |
| `.research/runs/` | Decision cards, source logs, QA records, and run-level JSONL. |
| `.research/backtests/` | Backtest run records, validation summaries, and post-review JSONL. |
| `.research/journals/` | Parsed broker trade journals and behavior diagnostics. |
| `.research/shadow/` | Shadow Account profiles, rule summaries, and simulation outputs. |
| `.research/vibe_runs/` | Generated Vibe-Trading run directories and configs. |
| `.research/reviews/` | 5/20/60-day decision reviews and follow-up notes. |
| `.research/sources/` | Local copies or metadata for user-provided source files when permitted. |

## JSONL Minimum Fields

Each JSONL line should be one object with:

```json
{
  "record_id": null,
  "record_type": null,
  "created_at": null,
  "schema_version": "1.0",
  "ticker": null,
  "universe": null,
  "analysis_mode": null,
  "source_log": [],
  "qa_status": {},
  "artifact_refs": {}
}
```

## Security Rules

- Do not store iFinD tokens, API keys, passwords, broker login data, or cookies.
- Keep uploaded broker and personal data local unless the user explicitly asks
  for export.
- Redact sensitive account identifiers in human-facing output.
- Record `source_gap` rather than inventing missing prices, fees, quantities, or
  fills.
