请先使用 financial-services-skill-router。

任务：为【公司名称 / Ticker】做 earnings review，分析最新财报、电话会和模型影响。

请先读取 `.agents/SKILLS_INDEX.md`，再只读取本任务真正需要的 router 和 downstream `SKILL.md`。不要为了“全面”读取所有 skills。

## Required inputs

请先列出完成 earnings review 所需输入，并标记哪些已提供、哪些缺失：

- 公司名称、Ticker、财报季度或财年期间
- Earnings release、10-Q/10-K/6-K/20-F、investor presentation
- Earnings call transcript 或 management prepared remarks
- 共识预期或买方/卖方预期
- 现有模型、历史 KPI、segment 数据和 guidance
- 股价反应、盘前/盘后时间点、市场基准
- 关注问题：收入、margin、guidance、KPI、cash flow、capital allocation
- 数据来源、日期、链接或文件名

## Missing data handling

不要编造金融数据。如果缺少财报、transcript、consensus 或模型：

- 先输出数据请求清单和可先分析的范围
- 可以先搭建 earnings review memo 框架、KPI 表格、variance bridge 和 source log
- 所有缺失数值、共识、guidance 或 transcript 内容标记为 `TBD`
- 不得声称公司“beat/miss/raise/lower”除非数据已提供或已核验

## Required routing output

请明确列出：

- Task classification
- Candidate skills considered
- Selected skills
- Rejected skills and reason
- Execution order

## Execution requirements

- 使用 selected skills 按 execution order 执行
- 分离 reported facts、management commentary、consensus variance 和 analyst interpretation
- 对高风险金融输出标记：Not investment advice、Data limitations、Assumptions

## Final output format

最终请输出：

- Earnings review memo 或模型更新框架
- Key takeaways
- Reported vs consensus / prior period variance 表
- Guidance changes 和 management commentary 摘要
- Model impact 与待更新项
- Missing data 清单
- QA checks performed
