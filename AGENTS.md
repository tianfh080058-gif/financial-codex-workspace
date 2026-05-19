# Project Agent Instructions

For any finance, financial services, accounting, investing, banking, markets,
wealth management, private equity, fund administration, KYC, valuation, or
financial modeling task, first use the
`financial-services-skill-router` skill.

The router must identify the user's domain, artifact, data needs, and risk
level before selecting the most specific financial-services skill under
`.agents/skills/`.

Before selecting downstream skills, read `.agents/SKILLS_INDEX.md` to identify
candidate skills, then read the full `SKILL.md` only for the selected router and
downstream skills.

For China market, A-share, Hong Kong-listed Chinese company, 同花顺, iFinD,
AKShare, or Chinese disclosure tasks, use `china-market-overlay` after the
router and before valuation, comps, earnings, or modeling downstream skills.

## Language and explanation policy

- Default response language: Simplified Chinese.
- For day-to-day interaction with the user, respond in Chinese unless the user
  explicitly asks for English.
- Keep file paths, code, commands, Git output, error messages, APIs, config keys,
  function names, formulas, accounting terms, financial tickers, and original
  source quotations in their original language.
- For important English finance / accounting / coding terms, include a concise
  Chinese explanation on first use. Example: `WACC（加权平均资本成本）`,
  `terminal value（终值）`, `covenant headroom（契约余量）`.
- For financial deliverables, use bilingual labels when useful. Example:
  `Executive Summary（执行摘要）`, `Key Assumptions（关键假设）`,
  `QA Checks Performed（已执行的质量检查）`.
- Do not translate source file names, sheet names, code identifiers, command
  outputs, or quoted disclosure text unless explicitly requested.
- If the user provides Chinese input, assume Chinese output is preferred.
- If the deliverable is intended for an English-speaking client, ask whether to
  produce English, Chinese, or bilingual output.
- Keep explanations concise and practical; avoid overly literal translations
  that obscure financial meaning.

Do not invent financial, market, company, client, accounting, or regulatory
data. Use user-provided materials, configured data tools, filings, or verified
sources, and clearly label assumptions and source gaps.

When current market data, laws, rules, prices, filings, or company facts are
needed, verify them before relying on them. Preserve source attribution in
models, reports, decks, and memos.
