# OpenStock-style A 股本地研究工作区

用于把 OpenStock 式的搜索、观察池、价格提醒和每日摘要体验，映射到本项目的
A 股/iFinD 优先本地工作流。不要复制 OpenStock 代码；只借鉴产品能力并使用
`trading_core` 重新实现。

## 路由

1. 先使用 `financial-services-skill-router`。
2. A 股或中国市场任务继续使用 `china-market-overlay`。
3. 观察池、提醒、摘要使用 `a-share-research-product-workflow`。
4. 条件化决策卡使用 `trading-decision-engine`。
5. 交付或持久化前执行 `financial-output-qa-gate`。

## 常用说法

- “搜索同花顺并给我候选 ticker”
- “把 300033.SZ 加入观察池，分组金融科技，优先级 1”
- “给 300033.SZ 添加上穿 100 元提醒，有效期 90 天”
- “检查我的价格提醒”
- “生成今天的观察池摘要”

## CLI

```bash
python3 -m trading_core.cli search --query 同花顺
python3 -m trading_core.cli watchlist --file .research/watchlists/default.json --add 300033.SZ --name 同花顺 --group 金融科技 --priority 1
python3 -m trading_core.cli alerts --add 300033.SZ --condition above --level 100 --expires 90d
python3 -m trading_core.cli alerts --check --file .research/alerts/alerts.jsonl
python3 -m trading_core.cli brief --watchlist .research/watchlists/default.json --store
```

## 输出要求

- 必须包含 `source_log`、`source_capability_matrix`、`qa_status` 和
  `not_investment_advice`。
- 行情、公告、新闻不可用时，输出 `source_gap`，不要补造数据。
- 价格提醒只是条件触发记录，不是 target price（目标价）、评级、个人仓位建议、
  收益承诺或无条件买卖指令。
