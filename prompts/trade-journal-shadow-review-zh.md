# 交易日志复盘与 Shadow Account Prompt

请先使用 `financial-services-skill-router`。如交易记录涉及 A 股、港股、同花顺、iFinD 或 AKShare，请继续使用 `china-market-overlay` 和 `trade-journal-shadow-review`。

任务：解析 `{file}`，输出交易画像、行为诊断和 Shadow Account 复盘摘要。

要求：

- 正常 app 对话使用 `trade-journal-shadow-review/references/app-conversation-display.md` 的卡片式 Markdown；不要默认贴完整 JSON。
- 标准化同花顺、东方财富、富途或 generic CSV/XLSX 字段。
- FIFO 配对闭合交易，计算胜率、盈亏比、平均持仓天数、交易频率、总 PnL、回撤。
- 诊断处置效应、过度交易、追涨、锚定；证据不足时标明 source gap。
- 从盈利闭合交易中提取 Shadow Account 规则，仅用于模拟和复盘。
- 禁止预测收益、个性化仓位或实盘交易指令。

可用 CLI：

```bash
python3 -m trading_core.cli journal --file {file}
```

默认终端输出为 Markdown 复盘卡；需要完整 JSON 时添加 `--format json`。
