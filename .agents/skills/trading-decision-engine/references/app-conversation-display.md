# App Conversation Display Standard

Use this reference when presenting `trading-decision-engine` results directly in
the Codex app conversation. The goal is to make the answer easier to scan
without reducing evidence quality, source traceability, or guardrails.

## Core Principle

The app response is a human-readable view over the same decision object. Do not
remove source logs, QA status, missing data, or guardrails from the analysis;
move detailed audit fields into compact sections or `<details>` blocks when the
main answer would otherwise become hard to read.

Do not show the full JSON by default. Offer or provide full JSON only when the
user asks for it, when saving artifacts, or when an automation/integration needs
machine-readable output.

## Recommended Decision-Support Layout

Use this order for normal app dialogue:

1. One-line orientation:
   - Format: `结论：...`
   - Must be conditional and evidence-scoped.
   - Do not use unconditional buy/sell instructions.
2. `决策卡` table:
   - Ticker / company
   - Horizon
   - `decision_state`
   - Confidence
   - Latest price / trade date / retrieved_at
   - QA status
3. `条件化交易计划` table:
   - Trigger level
   - Invalidation level
   - Risk-control level
   - Exit/reduce condition
   - Time validity
4. `证据矩阵` table:
   - Technical evidence
   - Fundamentals / valuation evidence when sourced
   - Event / announcement evidence when sourced
   - Backtest / factor evidence when sourced
   - Data gaps
5. `执行约束` table for A shares:
   - T+1
   - Price limits
   - 100-share lots
   - No shorting
   - Cost / slippage assumptions
6. `下一步检查清单`:
   - Refresh market data
   - Check announcements / financials
   - Re-run integrity checker
   - Review 5/20/60 trading-day horizons
7. Compact `数据与QA` section:
   - Source priority and fallback status
   - Missing data
   - `Not investment advice`
   - Guardrails blocked

## Markdown Pattern

```md
**结论：** 当前仅能归类为 `watch_only`，触发价、失效价和风控线可用于后续观察，但需先刷新行情与事件证据。

**决策卡**
| 项目 | 内容 |
|---|---|
| 标的 | `300033.SZ` |
| 周期 | `20d` |
| 状态 | `watch_only` |
| 置信度 | `low_to_medium` |
| 交易日 | `2026-03-31` |
| QA | `pass` |

**条件化交易计划**
| 类型 | 价位 | 使用条件 |
|---|---:|---|
| 触发观察 | 27.05 CNY/share | 收盘站上且量能确认，同时无反向公告/财务证据 |
| 失效 | 26.57 CNY/share | 收盘跌破或证据被证伪 |
| 风控 | 26.37 CNY/share | 跌破后进入减仓/离场复核 |

**证据矩阵**
| 维度 | 结论 | 证据/缺口 |
|---|---|---|
| 技术 | mixed | 日线强于中期均线，周/月未完全确认 |
| 基本面 | 缺口 | 本轮未刷新财务与估值 |
| 事件 | 缺口 | 本轮未刷新公告 |
| 回测 | 未运行 | 可用 Vibe bridge 补充 |

<details>
<summary>数据与QA</summary>

- Source priority: iFinD first, fallback only after source gap.
- Missing data: security master / financials / announcements.
- Not investment advice: true.
- Blocked: target price, rating, personal position sizing, return promise, unconditional trade instruction.

</details>
```

## Style Rules

- Prefer short tables for state, levels, evidence, and QA.
- Keep the opening conclusion to one or two sentences.
- Use backticks for schema values such as `watch_only` and `risk_control_review`.
- Keep detailed source logs in a compact section unless the user asks for all
  raw details.
- If evidence is missing, write `缺口` instead of hiding the row.
- Do not use decorative symbols that may distract from risk language.
- Do not end with an unconditional trade instruction.

## Required Guardrails

- Always include `Not investment advice` for investment-related outputs.
- Always show data timestamp or state that refreshed data is missing.
- Always show missing data and QA state.
- Technical analysis must not be the sole basis for a high-conviction state.
- Backtests and factors are evidence only, not direct trade recommendations.
