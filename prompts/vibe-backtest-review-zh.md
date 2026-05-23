# Vibe 回测桥接 Prompt

请先使用 `financial-services-skill-router`，再使用 `trading-decision-engine`。如标的是 A 股，请继续使用 `china-market-overlay` 和 A 股工作流。

任务：为 `{ticker}` 的 `{strategy}` 生成 Vibe-Trading `run_dir`，并在有本地 OHLCV 或可用数据源时输出 `backtest_validation`。

要求：

- `run_dir` 写入 `.research/vibe_runs/`。
- 生成 Vibe 兼容的 `config.json` 和 `code/signal_engine.py`。
- 映射 Sharpe、max drawdown、win rate、Monte Carlo、Bootstrap、Walk-Forward。
- 回测只作为验证证据，不构成收益承诺或直接交易建议。

可用 CLI：

```bash
python3 -m trading_core.cli backtest --ticker {ticker} --strategy {strategy} --start {start} --end {end}
```

默认终端输出为 Markdown 回测验证卡；需要完整 JSON 时添加 `--format json`。
