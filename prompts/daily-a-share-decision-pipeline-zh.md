# 每日 A 股观察池到条件化决策 Prompt

请先使用 `financial-services-skill-router`，读取 `.agents/SKILLS_INDEX.md`，
并使用 `.agents/workflows/daily_a_share_decision_pipeline.json`。

目标：保留 `watchlist_daily_review`、`a_share_deep_research`、
`a_share_decision_support` 三个子 workflow 的独立边界，同时把它们组合成
每日决策闭环。

## 默认流程

1. 用 `watchlist_daily_review` 对观察池初筛，默认输出 Top10。
2. 对 Top10 中的前 Top5 执行 `a_share_deep_research`。
3. 生成 `evidence_sufficiency`：
   - `sufficient`：可进入 `a_share_decision_support`。
   - `insufficient`：进入 `wait_or_data_gap`，列出补数据清单。
   - `blocked`：进入 `avoid_or_wait`，说明阻断原因。
   - Polymarket 宏观/强相关事件证据作为辅助维度；若无相关市场或 API 不可用，明确记录 `no_related_markets` 或 `source_gap`。
4. 仅对 `evidence_sufficiency.status = sufficient` 的标的执行
   `a_share_decision_support`。
5. 使用 `financial-output-qa-gate` 做最终检查。

## 默认参数

- `screen_top_n`: 10
- `deep_research_top_n`: 5
- `decision_horizon`: `20d`
- `analysis_mode`: `decision_support`
- `display_profile`: `app_card`

## 输出结构

请用卡片式 Markdown 展示，不要默认贴完整 JSON：

- 今日 Top10 观察池排序。
- Top5 深研摘要。
- `evidence_sufficiency` 表格。
- 决策候选清单。
- 等待/补数据清单。
- 条件化交易计划：触发条件、失效条件、风控线、减仓/离场条件。
- Polymarket 宏观/事件预期：相关层级、隐含概率、24h/7d 变化、成交/流动性、本地快照变化和限制。
- 数据与 QA：source log、missing data、qa status、Not investment advice。

## Guardrails

- 不输出目标价、买卖评级、个性化仓位、收益承诺。
- 不输出无条件立即买入/卖出指令。
- 不把技术信号、因子结果或回测结果单独作为交易计划依据。
- 不把 Polymarket 概率当作确定性预测或单独决策依据。
- 缺数据时输出等待或补数据清单，不强行生成条件化交易计划。
