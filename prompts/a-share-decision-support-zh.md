请先使用 financial-services-skill-router。

任务：对【公司名称 / A 股 Ticker】做投资决策支持。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `a-share-research-product-workflow`。
5. 明确 `analysis_mode = decision_support`。
6. 不要输出目标价、买入/卖出评级、个性化仓位、收益承诺、未经来源支持的 consensus 或 guidance。

## Allowed Decision States

只允许输出以下 `decision_state`：

- `watch_only`
- `research_candidate`
- `hold_monitor`
- `risk_control_review`
- `avoid_or_wait`

## Required Output

- `source_capability_matrix`
- `market_context`
- `security_master`
- `market_snapshot`
- `technical_analysis`
  - 必须覆盖 `daily`、`weekly`、`monthly`
  - 日线为主、周线确认、月线用于长期趋势背景和大级别风险过滤
  - 技术信号只能进入证据、触发条件、失效条件和风险控制，不能单独决定 `decision_state`
- `financial_snapshot` 和 `valuation_snapshot`，仅在有来源支持时输出
- `decision_support`
  - decision_state
  - supporting_evidence
  - disconfirming_evidence
  - trigger_conditions
  - invalidation_conditions
  - risk_controls
  - confidence
  - missing_data
- `report_integrity_status`
- `qa_status`
- `Not investment advice`

禁止把技术分析表述为买入/卖出信号、目标价、个性化仓位、收益承诺或单一决策依据。
