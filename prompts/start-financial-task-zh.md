请先使用 financial-services-skill-router。

这是中文优先的金融任务启动模板。

任务：【在这里描述金融工作流，例如 DCF、earnings review、comps、credit memo、IC memo、client report】

请按当前工作区配置执行：

1. 先读取 `AGENTS.md`
2. 再读取 `.agents/SKILLS_INDEX.md`
3. 使用 `financial-services-skill-router`
4. 从索引中选择真正需要的 downstream skills，不要为了“全面”读取所有 skills
5. 明确列出 selected skills 和 execution order
6. 明确列出 rejected skills and reason
7. 输出中文，除非我明确要求英文或交付物面向英文客户
8. 关键英文术语首次出现时附中文释义，例如 `WACC（加权平均资本成本）`、`terminal value（终值）`、`covenant headroom（契约余量）`
9. 保留代码、路径、命令、ticker、source quote 原文，不要翻译源文件名、sheet names、code identifiers 或 quoted disclosure text
10. 不要编造任何金融、市场、公司、客户、会计、监管、consensus、guidance 或 price reaction 数据

## Required inputs（所需输入）

请列出完成任务所需的输入，并标记：

- 已提供
- 缺失
- 需要核验
- 可作为 assumption（假设）但必须由用户确认

## Missing data handling（缺失数据处理）

如果数据不足，请先输出：

- 数据请求清单
- 可先搭建的分析框架或模型框架
- 所有 `TBD` 项
- 不能得出的结论

不要把缺失数据补成看似真实的数字、consensus、guidance、market reaction 或管理层表述。

## Final output format（最终输出格式）

请说明最终产物格式，例如：

- Markdown memo
- Excel model
- PowerPoint deck
- DOCX report
- 数据请求清单
- QA checklist

金融交付物可使用中英双语标题，例如：

- `Executive Summary（执行摘要）`
- `Key Assumptions（关键假设）`
- `QA Checks Performed（已执行的质量检查）`

## QA requirements（质量检查要求）

最后必须输出 `QA checks performed（已执行的质量检查）`，并说明：

- 是否使用了 router-first workflow
- 是否读取了 `.agents/SKILLS_INDEX.md`
- 是否只读取了 selected downstream skills
- 是否避免编造数据
- 是否保留代码、路径、命令、ticker、source quote 原文
- 是否标记 Not investment advice、Data limitations、Assumptions
