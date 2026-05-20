请先使用 financial-services-skill-router。

任务：生成 A 股自选股日报。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `a-share-research-product-workflow`。
5. 明确 `analysis_mode = research`，不要输出买卖建议、目标价、评级或个性化仓位。

## Inputs

- watchlist：`.research/watchlists/default.json` 或用户提供的 ticker 列表。
- 数据源优先级：官方公告 / iFinD / AKShare / Web verified sources。
- 输出：Markdown 日报，可选择追加 `.research/runs/*.jsonl`。

## Required Output

- `source_capability_matrix`
- `market_context`
- 每个标的的轻量 `security_master`、`market_snapshot`、`technical_analysis`、`thesis_tracker` 更新
- 每个标的的技术状态摘要：
  - 日线趋势
  - 周线确认
  - 月线背景
  - 量能与相对强弱
  - 关键缺口或 missing data
- 异动与需要复核的 thesis
- Missing data
- `report_integrity_status`
- `qa_status`
- `Not investment advice`
