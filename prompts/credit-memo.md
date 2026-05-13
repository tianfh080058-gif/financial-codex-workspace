请先使用 financial-services-skill-router。

任务：为【借款人 / 发行人 / 交易】创建 credit memo 或 debt investment memo。

请先读取 `.agents/SKILLS_INDEX.md`，再只读取本任务真正需要的 router 和 downstream `SKILL.md`。不要为了“全面”读取所有 skills。

## Required inputs

请先列出完成 credit memo 所需输入，并标记哪些已提供、哪些缺失：

- 借款人或发行人名称、行业、地区、资本结构和债务工具类型
- 历史财务、LTM、预测、EBITDA adjustments、cash flow
- Debt schedule、maturity profile、interest rate、amortization、security、ranking
- Leverage、coverage、liquidity、free cash flow、fixed charge coverage
- Covenants、basket、restricted payments、collateral、guarantees
- Ratings、spread、yield、market comps、secondary trading levels
- Business risk、financial risk、management、sponsor、event risk
- Recovery assumptions、downside case、default risk indicators
- 数据来源、日期、链接或文件名

## Missing data handling

不要编造金融数据。如果缺少债务条款、covenants、财务或市场数据：

- 先输出数据请求清单和 credit memo 框架
- 可以先搭建 leverage / coverage / liquidity 模型框架和 covenant checklist
- 所有缺失 spreads、ratings、debt terms、covenants 和财务指标标记 `TBD`
- 不得输出 credit recommendation 或 risk rating，除非有足够数据支持

## Required routing output

请明确列出：

- Task classification
- Candidate skills considered
- Selected skills
- Rejected skills and reason
- Execution order

## Execution requirements

- 使用 selected skills 按 execution order 执行
- 区分 reported financials、adjusted metrics、market data 和 analyst assumptions
- 对高风险金融输出标记：Not investment advice、Data limitations、Assumptions

## Final output format

最终请输出：

- Credit memo 或 debt investment memo
- Borrower overview 和 capital structure
- Leverage / coverage / liquidity 分析
- Covenant 和 debt terms 摘要
- Downside / recovery / key risks
- Missing data 清单
- QA checks performed
