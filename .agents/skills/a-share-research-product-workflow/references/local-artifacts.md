# Local Research Artifacts

Use `.research/` for local productized research history. These files can contain
personal notes, watchlists, and thesis history, so `.research/` should remain
gitignored by default.

## Directory Convention

| Path | Purpose |
|---|---|
| `.research/watchlists/*.json` | Watchlist definitions and groupings. |
| `.research/reports/YYYY-MM-DD/*.md` | Daily reviews and single-stock memos. |
| `.research/runs/*.jsonl` | Run records, sources, mode, output path, and QA status. |
| `.research/thesis/*.jsonl` | Thesis evidence, disconfirming signals, catalysts, and state changes. |
| `.research/backtests/*.jsonl` | Post-review records for decision-support outputs. |

## Watchlist Shape

```json
{
  "name": "default",
  "created_at": null,
  "groups": [
    {
      "name": "AI算力",
      "tickers": [
        {"ticker": "300308.SZ", "company_name": "中际旭创"}
      ]
    }
  ],
  "notes": []
}
```

## JSONL Record Minimums

Each JSONL line should be a JSON object. Prefer these common fields:

```json
{
  "record_type": "run",
  "run_id": null,
  "created_at": null,
  "analysis_mode": "research",
  "tickers": [],
  "source_log": [],
  "output_path": null,
  "qa_status": {},
  "summary": null
}
```

For `decision_support` records, include:

```json
{
  "record_type": "decision_support",
  "analysis_mode": "decision_support",
  "ticker": null,
  "decision_support": {
    "decision_state": "watch_only",
    "supporting_evidence": [],
    "disconfirming_evidence": [],
    "trigger_conditions": [],
    "invalidation_conditions": [],
    "risk_controls": [],
    "confidence": "low"
  },
  "not_investment_advice": true
}
```

## Tooling

- Use `tools/research_jsonl_store.py` to append, list, get latest, or replay
  local JSONL records.
- Use `tools/check_research_integrity.py` before treating a schema record as a
  productized output.
- Use `tools/review_decision_support.py` for post-review checklists. It should
  not output buy/sell advice or return promises.
