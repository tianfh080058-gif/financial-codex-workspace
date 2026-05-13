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

- `.agents/skills/`  
  Codex-compatible skill directories migrated from `upstream/financial-services`.
  Each skill has a `SKILL.md` with `name` and `description` frontmatter.

- `.agents/skills/financial-services-skill-router/`  
  Router skill for financial-services tasks. It classifies the task, considers
  candidate skills, selects downstream skills, identifies missing data, and
  defines the QA plan.

- `prompts/`  
  Copyable prompt templates for common workflows such as DCF, comps, earnings
  review, IC memo, credit memo, and client reporting. Use
  `prompts/start-financial-task.md` as the generic starting template.

- `tools/`  
  Validation and audit scripts for skills and workspace structure.

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
python3 tools/validate_financial_workspace.py
```

Expected healthy state:

- `audit_skills.py`: `Errors: 0`, `Warnings: 0`
- `validate_financial_workspace.py`: no `FAIL`; warnings are acceptable only if
  they are understood and documented

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
