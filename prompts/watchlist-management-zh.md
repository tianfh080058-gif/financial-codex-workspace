# 股票观察池管理 Prompt

请先使用 `financial-services-skill-router`，读取 `.agents/SKILLS_INDEX.md`，
然后使用 `china-market-overlay` 和 `a-share-research-product-workflow`。

任务：帮我在 Codex 桌面端配置、查看、更新或使用本地股票观察池。

## Default Path

- 默认观察池：`.research/watchlists/default.json`
- 参考规范：`.agents/references/watchlist-management.md`
- 日常决策流程：`.agents/workflows/daily_a_share_decision_pipeline.json`

## Natural Language Commands

用户可以直接说：

- “初始化默认观察池。”
- “查看我的默认观察池。”
- “把 300033.SZ 加入观察池，名称同花顺，分组金融科技，优先级 1，标签 AI/证券IT。”
- “把 300033.SZ 的状态改为 research_candidate，备注关注量能确认。”
- “300033.SZ 暂时不进每日流程。”
- “从默认观察池移除 300033.SZ。”
- “跑一下默认观察池：先筛 Top10，对 Top5 深研，证据足够再进入条件化决策支持。”

## CLI Mapping

```bash
python3 -m trading_core.cli watchlist --init
python3 -m trading_core.cli watchlist
python3 -m trading_core.cli watchlist --add 300033.SZ --name 同花顺 --group 金融科技 --priority 1 --tag AI --tag 证券IT
python3 -m trading_core.cli watchlist --update 300033.SZ --set status=research_candidate --set notes=关注量能确认
python3 -m trading_core.cli watchlist --update 300033.SZ --set review.include_in_daily_pipeline=false
python3 -m trading_core.cli watchlist --remove 300033.SZ
python3 -m trading_core.cli watchlist --format json
```

## Output

默认输出 `app_card` 风格 Markdown：

- 观察池文件与配置摘要。
- 分组、优先级、状态、周期、标签。
- Top10 初筛入口和 Top5 深研入口。
- 可复制的桌面端快捷说法。
- QA、数据缺口和 `Not investment advice`。

## Guardrails

- 观察池笔记只是用户上下文，不是已验证事实。
- 需要市场价格、公告、财务数据或买卖点时，必须先验证数据。
- 不写入券商账号、密码、API token、个人账户规模或敏感凭据。
- 不输出目标价、评级、个人仓位、收益承诺或无条件买卖指令。
