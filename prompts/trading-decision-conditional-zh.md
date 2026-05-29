# 全市场条件化决策支持 Prompt

请先使用 `financial-services-skill-router`。如涉及 A 股、港股、中国市场、iFinD、同花顺或 AKShare，请继续使用 `china-market-overlay`、`a-share-equity-research-workflow`、`a-share-research-product-workflow` 和 `trading-decision-engine`。

任务：对 `{ticker}` 做 `{horizon}` 周期的 `decision_support` 分析，输出 `decision_card` 和 `conditional_trade_plan`。

要求：

- 正常 app 对话使用 `trading-decision-engine/references/app-conversation-display.md` 的卡片式 Markdown；不要默认贴完整 JSON。
- 优先使用 iFinD；如 iFinD 不可用，记录 `source_gap`，再使用 AKShare/yfinance/OKX/CCXT/Vibe loader fallback。
- 默认尝试拉取 Polymarket 宏观与强相关事件证据，只保留 `macro_regime`、`sector_linked`、`ticker_or_company_linked` 三类相关市场；若无相关市场或 API 不可用，输出 `prediction_market_context.status = no_related_markets/source_gap`。
- Polymarket 只作为辅助证据，展示隐含概率、24h/7d 概率变化、volume、liquidity、openInterest 和本地快照差异；不得替代行情、财报、公告或风险控制。
- 包含日/周/月 `technical_analysis`，并说明 adjustment basis、trade date、retrieved_at。
- 允许输出条件化触发价、失效价、风控线、减仓/离场条件。
- 禁止目标价、评级、个性化仓位、收益承诺和无条件交易指令。
- 输出 `source_log`、`source_capability_matrix`、`qa_status`、`Not investment advice`。

可用 CLI：

```bash
python3 -m trading_core.cli decision --ticker {ticker} --market {market} --horizon {horizon} --mode conditional_strong
```

默认终端输出为 Markdown 决策卡；需要完整 JSON 时添加 `--format json`，需要保存完整记录时添加 `--output path.json`。
如需跳过 Polymarket 辅助证据，添加 `--skip-polymarket`；如需补充主题词，添加一个或多个 `--polymarket-query`。
