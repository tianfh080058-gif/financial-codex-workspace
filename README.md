# Financial Services Codex Skills Workspace

This repository is a project-scoped Codex workspace for financial-services
workflows. It packages migrated financial-services skills, a router-first policy,
prompt templates, and validation tools so Codex can route finance tasks without
reading every skill in full.

## Directory Structure

- `AGENTS.md`  
  Project-level instructions for Codex. Financial tasks must start with
  `financial-services-skill-router`, read `.agents/SKILLS_INDEX.md`, and only
  load the selected downstream skills.

- `.agents/SKILLS_INDEX.md`  
  Lightweight index of all installed skills. Codex uses this before reading full
  `SKILL.md` files.

- `.agents/workflows/`  
  Productized workflow recipes. Each JSON recipe declares triggers, required
  skills, execution order, inputs, outputs, QA gates, display profile, and
  artifact paths.

- `.agents/references/`  
  Shared contracts for cross-skill output, data capability registry, display
  profiles, and local research artifacts.

- `.agents/SKILL_TAXONOMY.md`  
  Non-breaking taxonomy tags for skill routing and governance. Tags classify
  skills as router, market overlay, data provider, product workflow, QA gate,
  display, artifact tool, or authoring.

- `.agents/skills/`  
  Codex-compatible skill directories migrated from `upstream/financial-services`.
  Each skill has a `SKILL.md` with `name` and `description` frontmatter.

- `.agents/skills/financial-services-skill-router/`  
  Router skill for financial-services tasks. It classifies the task, considers
  candidate skills, selects downstream skills, identifies missing data, and
  defines the QA plan.

- `.agents/skills/financial-output-qa-gate/`  
  Final checker for productized financial outputs. It verifies source logs,
  timestamps, missing data, `Not investment advice`, artifact references, and
  forbidden investment-output guardrails.

- `prompts/`  
  Copyable prompt templates for common workflows such as DCF, comps, earnings
  review, IC memo, credit memo, and client reporting. Use
  `prompts/start-financial-task.md` as the generic starting template.
  `prompts/PROMPTS_INDEX.md` maps productized prompts to workflow recipes,
  skills, CLI commands, and display profiles.

- `tools/`  
  Validation and audit scripts for skills and workspace structure.

- `vendor/vibe-trading/`  
  Isolated HKUDS/Vibe-Trading source snapshot used for backtest, Alpha Zoo,
  trade journal, Shadow Account, swarm/preset, MCP/API reference, and future
  bridge workflows. Upstream source should remain unmodified.

- `trading_core/`  
  Native adapter layer that connects Vibe-Trading-inspired capabilities to this
  workspace's financial router, A-share schema, iFinD/AKShare data governance,
  conditional decision cards, and CLI workflows.

- `third_party_licenses/`  
  Snapshot and license notices for vendored third-party source.

- `upstream/`  
  Local checkout area for source repositories such as
  `upstream/financial-services`. It is ignored by `.gitignore` because it is a
  source mirror, not part of this workspace package; only migrated Codex-ready
  files under `.agents/` are committed.

## Daily Workflow

1. Open the Codex desktop app.
2. Select this project folder:
   `/Users/tianfenghua/Desktop/financial-codex-workspace`
3. Start from `prompts/start-financial-task.md`, or use a more specific prompt
   under `prompts/`.
4. Let Codex follow `AGENTS.md`: use the router first, read
   `.agents/SKILLS_INDEX.md`, then load only the selected downstream skills.

## Validation

Run these from the project root:

```bash
python3 tools/audit_skills.py
python3 tools/validate_workflow_recipes.py
python3 tools/validate_prompt_skill_sync.py
python3 tools/validate_skill_taxonomy.py
python3 tools/validate_financial_workspace.py
```

Expected healthy state:

- `audit_skills.py`: `Errors: 0`, `Warnings: 0`
- `validate_workflow_recipes.py`: `Errors: 0`
- `validate_prompt_skill_sync.py`: `Errors: 0`
- `validate_skill_taxonomy.py`: `Errors: 0`
- `validate_financial_workspace.py`: no `FAIL`; warnings are acceptable only if
  they are understood and documented

## Workflow Recipes

Use workflow recipes when a task is repeatable or combines multiple skills:

- `.agents/workflows/daily_a_share_decision_pipeline.json`
- `.agents/workflows/a_share_decision_support.json`
- `.agents/workflows/watchlist_daily_review.json`
- `.agents/workflows/trade_journal_shadow_review.json`
- `.agents/workflows/vibe_backtest_validation.json`
- `.agents/workflows/alpha_factor_bench.json`
- `.agents/workflows/a_share_deep_research.json`

The router should match a recipe first, then load only the skills named by that
recipe.

`daily_a_share_decision_pipeline` is the parent daily workflow. It preserves the
standalone sub-workflows while orchestrating them as:

```text
watchlist_daily_review -> Top10
a_share_deep_research -> default Top5
evidence_sufficiency gate
a_share_decision_support -> only evidence-sufficient names
```

## Output Contract And QA Gate

Cross-skill output follows `.agents/references/output-contract.md`. High-risk
financial output must include source logs, missing data, QA status, timestamps
where applicable, and `Not investment advice`.

Run the QA gate through the skill or the CLI checker when JSON is available:

```bash
python3 tools/check_research_integrity.py --input path/to/record.json --profile a_share_decision
python3 tools/check_research_integrity.py --input path/to/record.json --profile general_finance
python3 tools/check_research_integrity.py --input path/to/record.json --profile journal_shadow
```

## Display Profiles

Human-facing output uses `.agents/references/display-profiles.md`:

- `app_card`: default Codex app conversation card.
- `cli_markdown`: terminal-readable Markdown.
- `machine_json`: complete automation/persistence JSON.
- `audit_appendix`: source and QA appendix for reports.

Normal app and CLI output should be readable by default; full JSON remains
available with `--format json` or saved artifacts.

## Research Artifacts

Local artifacts follow `.agents/references/local-research-artifacts.md`:

- `.research/watchlists/`
- `.research/runs/`
- `.research/backtests/`
- `.research/journals/`
- `.research/shadow/`
- `.research/vibe_runs/`
- `.research/reviews/`
- `.research/sources/`

Do not store tokens, API keys, broker credentials, or account passwords in
`.research/`.

## Watchlist Management

The default stock watchlist is managed at:

```text
.research/watchlists/default.json
```

Use `.agents/references/watchlist-management.md` for the schema, allowed status
values, desktop conversation mapping, and QA rules. The preferred schema stores
review preferences plus ticker metadata such as group, priority, horizon, tags,
notes, and whether the ticker enters the daily pipeline.

Common operations:

```bash
python3 -m trading_core.cli watchlist --init
python3 -m trading_core.cli watchlist
python3 -m trading_core.cli watchlist --add 300033.SZ --name 同花顺 --group 金融科技 --priority 1 --tag AI --tag 证券IT
python3 -m trading_core.cli watchlist --update 300033.SZ --set status=research_candidate --set notes=关注量能确认
python3 -m trading_core.cli watchlist --update 300033.SZ --set review.include_in_daily_pipeline=false
python3 -m trading_core.cli watchlist --remove 300033.SZ
```

In normal Codex desktop conversations, you can say things like “查看我的默认观察池”,
“把 300033.SZ 加入观察池，分组金融科技，优先级 1”, or “跑一下默认观察池”. The
assistant should map those requests to the same local watchlist commands and,
for daily usage, route through `daily_a_share_decision_pipeline`.

## Trading Decision Support CLI

The Vibe-Trading fusion layer is exposed through `trading_core`:

```bash
python3 -m trading_core.cli decision --ticker 300033.SZ --market a_share --horizon 20d --mode conditional_strong
python3 -m trading_core.cli backtest --ticker 300033.SZ --strategy technical_breakout --start 2024-01-01 --end 2026-05-23
python3 -m trading_core.cli alpha-bench --universe csi300 --zoo gtja191 --period 2021-2026
python3 -m trading_core.cli journal --file uploads/trades.xlsx
python3 -m trading_core.cli review --path .research/runs/decision_support.jsonl --horizon 20
```

Use `--ohlcv path/to/file.csv` or `--ohlcv path/to/file.json` when you want to
run against a local sourced OHLCV file. Live data retrieval is iFinD-first; free
or upstream loaders are fallback only and must be disclosed in `source_log`.

CLI commands default to Markdown cards for readability. Use `--format json` for
machine-readable full output, and use `--output path.json` to persist the full
record while still viewing the Markdown card in the terminal.

For normal Codex app conversations, the trading workflows use a card-style
Markdown layout by default: one-line conclusion, key tables, evidence matrix,
next checks, and a compact data/QA section. This keeps the answer readable while
preserving source gaps, QA, and `Not investment advice`.

Readable decision-card example:

```bash
python3 -m trading_core.cli decision \
  --ticker 300033.SZ \
  --market a_share \
  --horizon 20d \
  --mode conditional_strong \
  --ohlcv data/300033_ohlcv.csv
```

Machine-readable equivalent:

```bash
python3 -m trading_core.cli decision \
  --ticker 300033.SZ \
  --market a_share \
  --horizon 20d \
  --mode conditional_strong \
  --ohlcv data/300033_ohlcv.csv \
  --format json \
  --output .research/runs/300033_decision.json
```

This repository provides research, simulation, and decision-support tooling. It
does not execute real trades and does not produce target prices, ratings,
personal position sizing, return promises, or unconditional trade instructions.

## Updating Upstream Skills

When the source financial-services repository changes:

```bash
cd upstream/financial-services
git pull
cd ../..
```

Then rerun the migration workflow from `upstream/financial-services` into
`.agents/skills/`, regenerate `.agents/SKILLS_INDEX.md`, and run:

```bash
python3 tools/audit_skills.py
python3 tools/validate_workflow_recipes.py
python3 tools/validate_prompt_skill_sync.py
python3 tools/validate_skill_taxonomy.py
python3 tools/validate_financial_workspace.py
```

Do not commit `upstream/`; it remains ignored. Commit only the migrated
Codex-ready workspace files.

## Data Integrity Rules

- Do not invent financial, market, company, client, accounting, regulatory,
  consensus, guidance, or price-reaction data.
- Separate facts, assumptions, inferences, and missing data.
- Preserve source names, dates, links, file names, and source gaps.
- For high-risk financial outputs, include `Not investment advice`.
- If data is missing, build a framework or data request checklist first.

## Test Task Examples

DCF:

```text
请先使用 financial-services-skill-router。
我要为一家上市公司创建 DCF 估值模型，但目前只有公司名称。请列出 selected skills、execution order、required inputs、missing data handling、final output format 和 QA checks performed。不要编造金融数据。
```

Earnings review:

```text
请先使用 financial-services-skill-router。
我要分析一家上市公司的最新季度 earnings，但目前只有公司名称，没有 release、10-Q、transcript、consensus 或股价反应数据。请先搭建分析框架和数据请求清单。不要编造任何财务数据。
```

Comps:

```text
请先使用 financial-services-skill-router。
我要为一家上市公司做 comparable company analysis。请先说明候选 skills、selected skills、execution order、peer selection criteria、required inputs、missing data 和 QA checks performed。
```

Credit memo:

```text
请先使用 financial-services-skill-router。
我要为一个发行人创建 credit memo，但还没有债务条款、covenants、评级、spread 或财务数据。请先输出框架、required inputs、missing data handling 和 QA plan。不要编造数据。
```
