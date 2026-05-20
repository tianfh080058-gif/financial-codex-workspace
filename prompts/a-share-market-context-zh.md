请先使用 financial-services-skill-router。

任务：生成 A 股市场/板块上下文，用于后续单票投研。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `a-share-research-product-workflow`。
5. 明确 `analysis_mode = research`。

## Required Output

- 数据源、接口、参数、抓取时间和交易日
- `source_capability_matrix`
- `market_context`
  - 主要指数表现
  - 行业/板块强弱
  - 成交热度和风险偏好
  - 新闻/事件线索
- 对后续单票分析的影响
- Missing data
- `report_integrity_status`
- `qa_status`
- `Not investment advice`
