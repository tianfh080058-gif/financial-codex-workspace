---
name: ifind-http-api
description: "Use the iFinD / 同花顺 HTTP API for authenticated, source-backed retrieval of licensed financial market data, including access-token checks, real-time quotation, historical quotation, basic data, date sequence, EDB, announcements, and code conversion workflows. Use when users provide iFinD HTTP API credentials, refresh_token, access_token, or an iFinD API manual and ask to install, test, validate, or use 同花顺 data interfaces while protecting secrets, recording endpoint names, parameters, timestamps, missing data, and strict no-fabrication controls."
---

# iFinD HTTP API

Use this skill when a financial workflow needs 同花顺 / iFinD HTTP API access through the project-local Python client.

## Secret handling

- Never write `refresh_token`, `access_token`, account passwords, or API credentials into Git-tracked files.
- Prefer environment variables for one-off tests:
  - `IFIND_REFRESH_TOKEN`
  - `IFIND_ACCESS_TOKEN`
- Prefer macOS Keychain for local persistence:
  - `financial-codex-workspace.ifind.refresh_token`
  - `financial-codex-workspace.ifind.access_token`
  - `financial-codex-workspace.ifind.login`
- Do not print tokens. When reporting tests, show only whether credentials were found, endpoint status, error codes, response keys, and row/table counts.

## Standard workflow

1. Read `financial-services-skill-router` and `.agents/SKILLS_INDEX.md` before using this skill.
2. Confirm the requested data task and endpoint family:
   - `get_access_token` for current `access_token`.
   - `update_access_token` only when the user explicitly asks to rotate the token because it invalidates older tokens.
   - `real_time_quotation` for real-time quote fields.
   - `cmd_history_quotation` for daily/weekly/monthly historical quote fields.
   - Other endpoint families only after checking the uploaded manual or user-provided protocol.
3. Run the local environment check:
   ```bash
   python3 .agents/skills/ifind-http-api/scripts/ifind_http_api.py check-env
   ```
4. For a minimal connectivity test, prefer:
   ```bash
   python3 .agents/skills/ifind-http-api/scripts/ifind_http_api.py smoke-test --codes 300033.SZ --indicators open,high,low,latest
   ```
5. For historical quote validation, use explicit dates and indicators:
   ```bash
   python3 .agents/skills/ifind-http-api/scripts/ifind_http_api.py history --codes 300033.SZ --indicators open,close,volume --startdate 2024-01-01 --enddate 2024-01-05
   ```
6. Report the endpoint, parameters, timestamp, response status, source limitations, missing data, and QA checks performed.

## Data integrity rules

- Do not fabricate market data, fundamentals, estimates, or identifiers.
- Treat API output as licensed data from 同花顺 / iFinD and preserve attribution.
- If authentication, entitlement, IP binding, rate limit, network, or endpoint errors occur, report the exact failure class without filling gaps.
- For valuation, trading, portfolio, credit, or investment outputs, label `Not investment advice`, data limitations, and assumptions.

## Local client

Use `.agents/skills/ifind-http-api/scripts/ifind_http_api.py` instead of retyping raw HTTP code. It:

- Reads tokens from environment variables or macOS Keychain.
- Calls the documented iFinD HTTP API endpoints.
- Sanitizes output so tokens are not printed.
- Supports `check-env`, `get-access-token`, `smoke-test`, `history`, and `request` commands.
