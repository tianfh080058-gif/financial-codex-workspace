# App Conversation Display Standard

Use this reference when presenting trade journal or Shadow Account review results
directly in the Codex app conversation.

## Recommended Journal-Review Layout

1. One-line orientation:
   - State the dominant behavior pattern or the main limitation.
   - Do not predict future returns.
2. `复盘卡` table:
   - Trade count
   - Closed roundtrips
   - Win rate
   - Profit/loss ratio
   - Average holding days
   - Trade frequency
   - Total PnL when sourced
3. `行为诊断` table:
   - Disposition effect
   - Overtrading
   - Chasing momentum
   - Anchoring
   - Evidence or source gap
4. `Shadow Account` table:
   - Profile status
   - Profitable roundtrips
   - Extracted rules
   - Holding-day range
5. `下一步复盘清单`:
   - Add missing broker columns
   - Add market context around entries
   - Re-run shadow backtest
   - Review rule drift after 20/60 trading days
6. Compact `数据与QA` section:
   - Parser assumptions
   - Local artifact paths
   - `Not investment advice`

## Markdown Pattern

```md
**结论：** 当前样本能形成初步交易画像，但追涨和锚定需要补充入场前行情与交易备注后才能判断。

**复盘卡**
| 指标 | 数值 |
|---|---:|
| 交易笔数 | 42 |
| 闭合交易 | 18 |
| 胜率 | 55.6% |
| 盈亏比 | 1.35 |
| 平均持仓天数 | 8.2 |

**行为诊断**
| 模式 | 强度 | 证据 |
|---|---|---|
| 处置效应 | medium | 亏损单平均持仓长于盈利单 |
| 过度交易 | low | 每周交易频率未明显偏高 |
| 追涨 | 缺口 | 需要入场前行情 |
| 锚定 | 缺口 | 需要交易备注或参考价 |

<details>
<summary>数据与QA</summary>

- Parser assumptions: generic CSV/XLSX mapping.
- Not investment advice: true.
- No future return prediction or live order instruction.

</details>
```

## Style Rules

- Prefer tables for metrics and diagnostics.
- Use `缺口` when evidence is insufficient.
- Keep behavior labels descriptive, not judgmental.
- Do not promise that a Shadow Account rule will work in the future.
- Keep local artifact paths in the QA section unless the user asks for files.
