请先使用 financial-services-skill-router。

任务：为【公司名称 / Ticker】创建上市公司 DCF 估值模型。

请先读取 `.agents/SKILLS_INDEX.md`，再只读取本任务真正需要的 router 和 downstream `SKILL.md`。不要为了“全面”读取所有 skills。

## Required inputs

请先列出完成 DCF 所需输入，并标记哪些已提供、哪些缺失：

- 公司名称、Ticker、交易所、报告币种、财年结束月份
- 最近 3-5 年收入、毛利、EBIT/EBITDA、税率、D&A、CapEx、营运资本变化
- 现金、债务、少数股权、优先股、非经营资产或负债
- 稀释股数、当前股价、净债务或净现金
- 收入增长、利润率、税率、D&A、CapEx、NWC 等预测假设
- WACC 输入：无风险利率、Beta、股权风险溢价、税前债务成本、资本结构、税率
- 终值假设：terminal growth 或 exit multiple
- 所有数据来源、日期、链接或文件名

## Missing data handling

不要编造金融数据。如果只有公司名称或部分数据：

- 先输出数据请求清单和建议来源
- 可以先搭建空白 DCF 框架、公式结构、source log 和 checks tab
- 所有缺失输入必须保留为 `TBD` 或明确标记为缺失
- 不得输出未经数据支持的估值结论、目标价或投资判断

## Required routing output

请明确列出：

- Task classification
- Candidate skills considered
- Selected skills
- Rejected skills and reason
- Execution order

## Execution requirements

- 使用 selected skills 按 execution order 执行
- 每个假设都要区分 source-backed input 与 assumption
- 模型公式优先，避免在计算单元格硬编码结果
- 对高风险金融输出标记：Not investment advice、Data limitations、Assumptions

## Final output format

最终请输出：

- DCF 模型文件路径或可执行模型框架说明
- 输入数据与来源摘要
- 缺失数据清单
- 关键假设表
- 估值桥：Enterprise Value 到 Equity Value 到 Per Share Value
- WACC / terminal value / sensitivity 表说明
- QA checks performed
