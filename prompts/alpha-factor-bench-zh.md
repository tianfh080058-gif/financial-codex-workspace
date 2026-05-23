# Alpha 因子筛选 Prompt

请先使用 `financial-services-skill-router`，再使用 `trading-decision-engine`。如 universe 涉及中国市场，请使用 `china-market-overlay`。

任务：对 `{universe}` 在 `{period}` 周期运行 `{zoo}` 因子筛选，输出 IC、IR、正 IC 占比和 `alive/reversed/dead` 分类。

要求：

- iFinD OHLCV panel 优先；Vibe 原 loader 仅作 fallback 或交叉验证。
- 因子结果只能作为研究证据，不得直接转为买入/卖出建议。
- 输出 source log、缺失数据、QA 状态和 `Not investment advice`。

可用 CLI：

```bash
python3 -m trading_core.cli alpha-bench --universe {universe} --zoo {zoo} --period {period}
```

默认终端输出为 Markdown 因子筛选卡；需要完整 JSON 时添加 `--format json`。
