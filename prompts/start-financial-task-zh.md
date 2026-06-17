请先使用 financial-services-skill-router。

这是中文优先的自然语言入口模板。你不需要先选择 prompt、workflow、skill 或 CLI；直接描述你想完成的事情，系统会把目标路由到合适的场景入口，并只在必要时追问缺失输入。

## 你可以这样说

- 帮我看今天观察池
- 分析 300033.SZ 这只票，给我条件化决策辅助
- 帮我深研这家公司，但不要编造缺失数据
- 复盘我的券商成交导出文件
- 回测 300033.SZ 的 technical_breakout 策略
- 评估 CSI300 的 GTJA191 因子

## 系统应如何处理

1. 先读取 `AGENTS.md` 和 `.agents/SKILLS_INDEX.md`。
2. 使用 `financial-services-skill-router` 判断任务类型、产物、数据需求和风险。
3. 优先匹配 `.agents/workflows/*.json` 中的 `user_entry` 场景。
4. 只读取真正需要的 downstream skills，不要为了“全面”读取所有 skills。
5. 如果缺少必要输入，先返回 `needs_input` 和一个明确追问，不要直接失败。
6. 默认输出用户可读卡片；只有在我要求 JSON、审计或调试时才展示完整 internal route。
7. 输出中文，除非我明确要求英文或交付物面向英文客户。
8. 保留代码、路径、命令、ticker、source quote 原文。
9. 不要编造任何金融、市场、公司、客户、会计、监管、consensus、guidance 或 price reaction 数据。

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

## QA requirements（质量检查要求）

最后必须说明：

- 是否使用了 router-first workflow
- 是否读取了 `.agents/SKILLS_INDEX.md`
- 是否只读取了 selected downstream skills
- 是否避免编造数据
- 是否保留代码、路径、命令、ticker、source quote 原文
- 是否标记 Not investment advice、Data limitations、Assumptions
