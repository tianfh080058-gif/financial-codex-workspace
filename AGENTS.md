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

Do not invent financial, market, company, client, accounting, or regulatory
data. Use user-provided materials, configured data tools, filings, or verified
sources, and clearly label assumptions and source gaps.

When current market data, laws, rules, prices, filings, or company facts are
needed, verify them before relying on them. Preserve source attribution in
models, reports, decks, and memos.
