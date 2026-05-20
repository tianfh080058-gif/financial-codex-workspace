请先使用 financial-services-skill-router。

任务：检查一份 A 股投研 memo 或 schema 记录的完整性。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `a-share-research-product-workflow`。
5. 如输入是 JSON schema 记录，优先运行：
   `python3 tools/check_research_integrity.py --input <path>`

## Required Checks

- `analysis_mode` 是否存在且为 `research` 或 `decision_support`
- `source_log` 是否存在
- 市场数据是否包含 `trade_date`、`retrieved_at`、`unit`、`adjustment_basis`
- 单票 `research` 且包含 `market_snapshot` 时，是否包含 `technical_analysis`
- `decision_support` 模式是否包含 `technical_analysis`
- `technical_analysis` 是否包含 `trade_date`、`retrieved_at`、`adjustment_basis`、`source_ref`、`calculation_basis`
- `technical_analysis` 是否覆盖 `daily`、`weekly`、`monthly`，并标注周期计算口径和缺失 bars
- `qa_status` 是否存在
- 是否包含 `Not investment advice`
- `research` 模式是否误输出 `decision_state`
- `decision_support` 模式是否包含证据、反证、触发条件、失效条件和风险控制
- 是否存在目标价、买卖评级、个性化仓位、收益承诺、无来源 consensus/guidance
- 是否把技术分析表述为买入/卖出信号或单一决策依据

## Output

- `report_integrity_status`
- failed checks
- warnings
- 修复建议
