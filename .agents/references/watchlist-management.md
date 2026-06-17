# Watchlist Management

Use this reference when configuring or managing local stock watchlists for
productized research and decision-support workflows.

## Default Location

The default watchlist path is:

```text
.research/watchlists/default.json
```

Keep this directory local and gitignored. Do not store broker credentials,
account numbers, API keys, iFinD tokens, cookies, or personal financial data in
watchlist files.

## Preferred Schema

Use an object with `review_preferences` and structured ticker entries:

```json
{
  "schema_version": "1.2",
  "name": "default",
  "market": "a_share",
  "review_preferences": {
    "screen_top_n": 10,
    "deep_research_top_n": 5,
    "decision_horizon": "20d",
    "evidence_gate_policy": "standard",
    "data_priority": ["iFinD", "AKShare", "user_file"]
  },
  "news_preferences": {
    "enabled": false,
    "topics": ["announcements", "market_news"],
    "source_priority": ["official_disclosures", "iFinD", "AKShare"]
  },
  "source_refresh_policy": {
    "market_data": "on_demand",
    "announcements": "source_gap_until_configured",
    "stale_after_minutes": 30
  },
  "tickers": [
    {
      "ticker": "300033.SZ",
      "name": "同花顺",
      "group": "金融科技",
      "priority": 1,
      "status": "watch_only",
      "horizon": "1-4w",
      "tags": ["AI", "证券IT"],
      "notes": "关注量能确认和政策/业绩催化",
      "alert_rules": [],
      "news_preferences": {
        "enabled": false,
        "topics": ["announcements", "market_news"],
        "source_priority": ["official_disclosures", "iFinD", "AKShare"]
      },
      "source_refresh_policy": {
        "market_data": "inherit",
        "announcements": "inherit"
      },
      "last_reviewed_at": null,
      "review": {
        "enabled": true,
        "include_in_daily_pipeline": true
      }
    }
  ]
}
```

The CLI still accepts a simple array such as `["300033.SZ", "600519.SH"]`, but
the structured object is preferred because it preserves groups, notes, review
preferences, and workflow routing flags.

## Status Values

Use only these status values:

| Status | Meaning |
|---|---|
| `watch_only` | Observe and rank in daily review. |
| `research_candidate` | Prioritize for deep research. |
| `hold_monitor` | Monitor existing thesis or holding logic without storing position size. |
| `risk_control_review` | Prioritize invalidation, event, and downside-risk review. |
| `avoid_or_wait` | Keep visible but route away from decision support until evidence improves. |
| `archived` | Keep record but exclude from active daily review. |

Do not use ratings such as buy, sell, strong buy, or price targets.

## CLI Operations

```bash
python3 -m trading_core.cli search --query 同花顺
python3 -m trading_core.cli watchlist --init
python3 -m trading_core.cli watchlist
python3 -m trading_core.cli watchlist --add 300033.SZ --name 同花顺 --group 金融科技 --priority 1 --tag AI --tag 证券IT
python3 -m trading_core.cli watchlist --update 300033.SZ --set status=research_candidate --set notes=关注量能确认
python3 -m trading_core.cli watchlist --remove 300033.SZ
python3 -m trading_core.cli alerts --add 300033.SZ --condition above --level 100 --expires 90d
python3 -m trading_core.cli alerts --check --file .research/alerts/alerts.jsonl
python3 -m trading_core.cli brief --watchlist .research/watchlists/default.json --store
python3 -m trading_core.cli watchlist --format json
```

The default command uses `.research/watchlists/default.json`. Use `--file` when
you want separate pools such as `short_term.json`, `holdings.json`, or
`ai_sector.json`.

## Desktop Conversation Mapping

When the user asks in natural language, map to the same local commands:

| User phrasing | Local operation |
|---|---|
| “查看我的默认观察池” | Show `.research/watchlists/default.json`. |
| “初始化默认观察池” | Create the default watchlist template. |
| “把 300033.SZ 加入观察池，分组金融科技，优先级 1” | Upsert ticker metadata. |
| “把 300033.SZ 状态改为 research_candidate” | Update `status`. |
| “300033.SZ 暂时不进每日流程” | Set `review.include_in_daily_pipeline=false`. |
| “从观察池移除 300033.SZ” | Remove ticker. |
| “搜索同花顺并给我候选 ticker” | Run `trading_core.cli search`. |
| “给 300033.SZ 添加上穿 100 元提醒” | Add a local `alerts` rule. |
| “检查我的价格提醒” | Run `alerts --check`; triggered alerts are evidence, not orders. |
| “生成今天的观察池摘要” | Run `brief --watchlist ...`; preserve source gaps. |
| “跑一下默认观察池” | Use `daily_a_share_decision_pipeline`. |

For daily decision-support use:

```text
watchlist_daily_review -> Top10
a_share_deep_research -> default Top5
evidence_sufficiency gate
a_share_decision_support -> evidence-sufficient names only
```

## QA Rules

- Preserve `Not investment advice` in watchlist-derived outputs.
- Treat watchlist notes as user-provided context, not verified market facts.
- Verify current prices, announcements, filings, and market data before
  investment or trading conclusions.
- For six-digit A-share codes, infer common `.SH`, `.SZ`, or `.BJ` suffixes;
  reject unsupported A-share suffixes rather than silently accepting them.
- Price alerts are conditional monitoring records only. They are not target
  prices, ratings, personal position sizing, return promises, or order
  instructions.
- Do not store position size, account balance, passwords, or tokens in
  watchlists.
