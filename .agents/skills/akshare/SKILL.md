---
name: akshare
description: "Use AKShare, the Python open-source financial data interface library, for source-backed retrieval of public market data, Chinese A-share data, funds, bonds, futures, macroeconomic indicators, financial statements, and other finance datasets. Use when users ask to fetch, validate, refresh, or prototype analysis with publicly available financial data through AKShare, especially for China market workflows, while preserving source citations, interface names, parameters, timestamps, missing-data notes, and strict no-fabrication controls."
---

# AKShare

Use this skill when a financial workflow needs public data retrieval or a reproducible data-ingestion prototype through the `akshare` Python package.

## Core rules

- Do not fabricate financial, market, company, accounting, consensus, guidance, or price reaction data.
- Treat AKShare as a data access layer, not as an authoritative source by itself. Record the upstream data source shown by AKShare or the function documentation whenever available.
- Verify that the requested dataset exists in the installed AKShare version before claiming it can be fetched.
- If an interface returns empty data, stale data, malformed columns, rate-limit errors, or network errors, report the failure and ask for alternative sources or permission to retry. Do not fill gaps with estimates unless the user explicitly asks for assumptions.
- For investment, valuation, trading, credit, or portfolio outputs, label data limitations and include `Not investment advice`.
- Keep raw ticker symbols, exchange codes, function names, parameters, column names, commands, and error messages in their original language.

## Standard workflow

1. Read the task context from `financial-services-skill-router` and selected downstream skills.
2. Define the data request:
   - Company/security name and ticker, if known.
   - Market and exchange.
   - Dataset type: prices, fundamentals, financial statements, macro, fund, bond, futures, options, or news/events.
   - Date range, frequency, currency, adjustment basis, and required output format.
3. Check environment readiness:
   - Run `python3 .agents/skills/akshare/scripts/check_akshare_env.py`.
   - If AKShare is missing and live retrieval is required, ask before installing packages or using network access.
4. Inspect available AKShare interfaces:
   - Prefer local package introspection with `import akshare as ak`, `ak.__version__`, `dir(ak)`, and `help(ak.<function>)`.
   - If local docs are insufficient, consult official AKShare documentation or GitHub before relying on function signatures.
5. Retrieve data with a small, explicit script:
   - Use named parameters.
   - Print or save the query metadata: function name, parameters, AKShare version, execution timestamp, row count, column names, and any warnings.
   - Save raw pulls separately from transformed outputs when producing files.
6. Validate the data:
   - Confirm non-empty output, expected columns, date coverage, duplicate rows, numeric parsing, units, currency, and obvious outliers.
   - Cross-check critical facts against user-provided filings or another source when the analysis is high risk.
7. Report results:
   - Show what was fetched and what was not fetched.
   - Separate facts, assumptions, inferred transformations, and missing data.
   - Include QA checks performed.

## Environment handling

Use the bundled script first:

```bash
python3 .agents/skills/akshare/scripts/check_akshare_env.py
```

If AKShare is not installed, ask for approval before running package installation. Prefer the user's active project environment. Typical commands are:

```bash
python3 -m pip install akshare --upgrade
```

For users in China who ask for a mirror, use the official mirror-style install command only after approval:

```bash
python3 -m pip install akshare -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com --upgrade
```

## Output requirements

When this skill is used, include:

- Selected AKShare interfaces.
- Query parameters and date/time of retrieval.
- Data sources and source limitations.
- Missing data and failed pulls.
- Transformations applied.
- QA checks performed.
- `Not investment advice` for high-risk financial outputs.

## Common pairings

- DCF or valuation: pair with `vertical-financial-analysis-dcf-model`, `agent-model-builder-dcf-model`, or relevant valuation skills.
- Earnings review: pair with `vertical-equity-research-earnings-analysis` or `agent-earnings-reviewer-earnings-analysis`.
- Comps: pair with `vertical-financial-analysis-comps-analysis` or relevant comps skills.
- Spreadsheet output: pair with an `xlsx-author` skill or `spreadsheets` when producing Excel artifacts.
