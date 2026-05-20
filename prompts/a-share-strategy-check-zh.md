请先使用 financial-services-skill-router。

任务：对【公司名称 / A 股 Ticker】做策略问答 / 策略检查。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `a-share-research-product-workflow`。
5. 显式声明 `analysis_mode = research` 或 `analysis_mode = decision_support`。

## Strategy Lens

请选择一个或多个策略视角：

- `trend`：复用 `technical_analysis`，覆盖日线、周线、月线的趋势、均线、量能、回撤、波动、支撑/压力和相对强弱。
- `event`：公告、财报、行业新闻、催化剂。
- `growth_quality`：增长质量、利润率、ROE/ROIC、经营现金流。
- `valuation_digestion`：估值消化、PE/PB/PS/PCF、历史与 peer context。
- `thesis_falsification`：支持证据、反证、失效条件。

## Guardrails

- 策略检查是研究框架，不是交易系统。
- 如果使用 `decision_support`，只能输出允许的 decision_state。
- 如果使用 `decision_support`，技术分析只能进入证据、触发条件、失效条件和风险控制，不能单独决定 decision_state。
- 不输出目标价、买卖评级、个性化仓位或收益承诺。

## Required Output

- 数据源、接口、参数、抓取时间和交易日
- strategy lens
- `technical_analysis`，当 lens 包含 `trend` 时必须覆盖 `daily`、`weekly`、`monthly`
- 事实、计算、推断、反证和缺口
- `report_integrity_status`
- `qa_status`
- `Not investment advice`
