请先使用 financial-services-skill-router。

任务：为【客户 / 账户 / 投资组合】创建 client report 或 portfolio review。

请先读取 `.agents/SKILLS_INDEX.md`，再只读取本任务真正需要的 router 和 downstream `SKILL.md`。不要为了“全面”读取所有 skills。

## Required inputs

请先列出完成 client report 所需输入，并标记哪些已提供、哪些缺失：

- 客户名称或匿名 ID、报告期间、基准、币种和账户范围
- 投资组合 holdings、交易、现金流、费用、贡献/赎回
- 起始和期末市值、收益率、benchmark return、risk metrics
- Asset allocation、sector、region、currency、duration、credit quality 等暴露
- Performance attribution、top contributors、top detractors
- 客户目标、限制、IPS、税务或流动性约束
- 市场回顾、经理评论、建议操作和 follow-ups
- 数据来源、日期、链接或文件名

## Missing data handling

不要编造金融数据。如果缺少 holdings、performance、benchmark 或客户约束：

- 先输出数据请求清单和 client report 框架
- 可以先搭建报告结构、图表占位、source log 和 QA checklist
- 缺失收益、资产配置、benchmark、风险指标和建议标记为 `TBD`
- 不得输出具体投资建议，除非输入数据和适用限制已明确

## Required routing output

请明确列出：

- Task classification
- Candidate skills considered
- Selected skills
- Rejected skills and reason
- Execution order

## Execution requirements

- 使用 selected skills 按 execution order 执行
- 区分 portfolio facts、market commentary、client constraints 和 assumptions
- 对高风险金融输出标记：Not investment advice、Data limitations、Assumptions

## Final output format

最终请输出：

- Client report 或 portfolio review 文档/幻灯片框架
- Performance summary
- Allocation、risk、benchmark 和 attribution 分析
- Key observations、recommendations 或 follow-ups
- Missing data 清单
- QA checks performed
