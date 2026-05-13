请先使用 financial-services-skill-router。

任务：为【公司 / 标的 / 交易】创建 private equity investment committee memo。

请先读取 `.agents/SKILLS_INDEX.md`，再只读取本任务真正需要的 router 和 downstream `SKILL.md`。不要为了“全面”读取所有 skills。

## Required inputs

请先列出完成 IC memo 所需输入，并标记哪些已提供、哪些缺失：

- 公司名称、业务描述、行业、地区、所有权结构
- 交易类型、purchase price、EV、equity check、资本结构、融资条件
- 历史财务、LTM、预算、管理层预测和质量调整
- 市场规模、竞争格局、客户/供应商集中度
- 商业、财务、法律、税务、运营、技术 diligence 发现
- 投资 thesis、value creation plan、100-day plan
- Returns case：base / downside / upside 的 MOIC、IRR 和关键假设
- 主要风险、mitigants、deal-breaker issues
- 数据来源、日期、链接或文件名

## Missing data handling

不要编造金融数据。如果缺少交易条款、财务、diligence 或 returns：

- 先输出数据请求清单和 IC memo 空白框架
- 可以先创建章节结构、问题清单、diligence tracker 和 assumptions log
- 缺失数值、风险证据、returns 指标和 deal terms 标记为 `TBD`
- 不得输出 proceed/pass recommendation，除非有足够数据支持

## Required routing output

请明确列出：

- Task classification
- Candidate skills considered
- Selected skills
- Rejected skills and reason
- Execution order

## Execution requirements

- 使用 selected skills 按 execution order 执行
- 区分 sourced diligence findings、management claims 和投资团队 assumptions
- 对高风险金融输出标记：Not investment advice、Data limitations、Assumptions

## Final output format

最终请输出：

- IC memo 文档或结构化 Markdown memo
- Executive summary
- Investment thesis 和 value creation plan
- Deal terms / sources & uses / returns analysis
- Risk register 和 mitigants
- Missing data 清单
- QA checks performed
