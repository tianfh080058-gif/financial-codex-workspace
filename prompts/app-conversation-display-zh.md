# App 端对话展示 Prompt

用于在 Codex app 正常对话中展示交易决策、回测、因子筛选、交易日志复盘结果。目标是更直观，但不降低输出质量、证据密度或 QA 要求。

请先使用 `financial-services-skill-router`。如涉及中国市场、A 股、港股、同花顺、iFinD 或 AKShare，请继续使用 `china-market-overlay`。如涉及条件化交易决策，请使用 `trading-decision-engine` 并读取 `references/app-conversation-display.md`。如涉及交易日志复盘，请使用 `trade-journal-shadow-review` 并读取 `references/app-conversation-display.md`。

展示要求：

- 正常对话不要默认贴完整 JSON。
- 用 Markdown 卡片展示：一句话结论、核心表格、证据矩阵、风险/缺口、下一步检查、数据与 QA。
- 保留 `source_log`、`source_capability_matrix`、`qa_status`、`Not investment advice` 的要点。
- 需要完整 JSON 时，提示用户可使用 `--format json` 或要求“展开完整 JSON”。
- 禁止目标价、评级、个性化仓位、收益承诺和无条件交易指令。

推荐结构：

```md
**结论：** ...

**决策卡**
| 项目 | 内容 |
|---|---|
| 标的 | `...` |
| 周期 | `...` |
| 状态 | `...` |
| 置信度 | `...` |
| QA | `...` |

**条件化交易计划**
| 类型 | 价位 | 使用条件 |
|---|---:|---|
| 触发观察 | ... | ... |
| 失效 | ... | ... |
| 风控 | ... | ... |

**证据矩阵**
| 维度 | 结论 | 证据/缺口 |
|---|---|---|
| 技术 | ... | ... |
| 基本面 | ... | ... |
| 事件 | ... | ... |
| 回测/因子 | ... | ... |

<details>
<summary>数据与QA</summary>

- Source priority: ...
- Missing data: ...
- Not investment advice: true

</details>
```
