# Display Profiles

Use display profiles to keep App and CLI output readable without weakening the
machine-readable record, sources, or QA checks.

## `app_card`

Default for Codex app conversations.

- Lead with one concise orientation line.
- Show compact Markdown tables for the decision card, conditional plan, evidence
  matrix, execution constraints, and next checks.
- Put data provenance and QA in a compact section or `<details>` block.
- Do not paste full JSON unless the user asks.

## `cli_markdown`

Default for `trading_core.cli` when `--format markdown` is used.

- Use stable headings and tables that fit terminal output.
- Include the same decision, evidence, risk, source, and QA essentials as
  `app_card`.
- Tell the user that `--format json` exposes the full machine record.

## `machine_json`

Default for automation, persistence, and replay.

- Emit the full JSON object with no display-only truncation.
- Preserve all source logs, missing data, QA fields, assumptions, and artifact
  references.
- Use stable field names from `.agents/references/output-contract.md`.

## `audit_appendix`

Use when a report, memo, or stored artifact needs a compliance-style appendix.

- Include source capability matrix, source log, missing data, QA checks, failed
  checks, assumptions, and artifact references.
- Keep investment guardrails visible.
- Avoid conversational summaries.
