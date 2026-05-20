请先使用 financial-services-skill-router。

任务：复盘【公司名称 / A 股 Ticker】的投资 thesis 是否仍然成立。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `vertical-equity-research-thesis-tracker`。
5. 按需使用 `ifind-http-api`、`akshare`、官方公告或用户文件。

## Required inputs

请先列出并标记已提供、缺失、需要核验或可作为 assumption 的输入：

- 原始 thesis 和 3-5 个 thesis pillars
- 持仓状态或 watchlist 状态
- 关键支撑证据和关键反证
- 需要跟踪的财务指标、行业指标、估值指标、价格区间
- 催化剂、风险、止损/退出条件或复盘周期
- 相关公告、财报、模型或用户笔记

## Thesis tracker requirements

请输出结构化 `thesis_tracker`：

- `core_thesis`
- `thesis_pillars`
- `supporting_evidence`
- `disconfirming_evidence`
- `catalysts`
- `risks`
- `follow_ups`
- `conviction`
- `missing_data`

不要把股价上涨/下跌直接当作 thesis 成立或失效的证据，除非有来源支持的基本面或事件解释。

## Output format

最终输出：

- Thesis 状态：strengthened / weakened / neutral / not enough data
- 每个 thesis pillar 的证据和反证
- 关键催化剂和风险
- 需要继续验证的问题
- Missing data
- Source log
- QA checks performed
- Not investment advice
