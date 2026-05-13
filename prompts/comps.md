请先使用 financial-services-skill-router。

任务：为【公司名称 / Ticker / 行业】创建上市公司可比公司分析。

请先读取 `.agents/SKILLS_INDEX.md`，再只读取本任务真正需要的 router 和 downstream `SKILL.md`。不要为了“全面”读取所有 skills。

## Required inputs

请先列出完成 comps 所需输入，并标记哪些已提供、哪些缺失：

- 目标公司名称、Ticker、交易所、行业、业务描述、地区和币种
- 候选 peer universe，或选择 peers 的标准
- 目标公司与 peers 的市值、EV、股价、净债务、少数股权、优先股
- 历史和预测收入、EBITDA、EBIT、EPS、FCF 等指标
- 估值倍数口径：EV/Revenue、EV/EBITDA、EV/EBIT、P/E、FCF yield 等
- 是否使用 NTM、CY、FY、LTM 或多年度预测
- 数据来源、日期、链接或文件名

## Missing data handling

不要编造金融数据。如果缺少市场数据、预测数据或 peers：

- 先输出数据请求清单和 peer selection criteria
- 可以先搭建 comps 表格框架、公式、筛选逻辑和 source log
- 对缺失公司、缺失倍数、缺失预测统一标记 `TBD`
- 不得输出未经数据支持的 implied valuation、目标价或投资判断

## Required routing output

请明确列出：

- Task classification
- Candidate skills considered
- Selected skills
- Rejected skills and reason
- Execution order

## Execution requirements

- 使用 selected skills 按 execution order 执行
- 说明 peer 选择理由和排除理由
- 对所有 market data 和 estimates 标记日期
- 对高风险金融输出标记：Not investment advice、Data limitations、Assumptions

## Final output format

最终请输出：

- Comparable company analysis 文件路径或框架说明
- Peer universe 和筛选理由
- 输入数据与来源摘要
- 缺失数据清单
- 倍数表、统计摘要、implied valuation 框架
- 异常值和口径差异说明
- QA checks performed
