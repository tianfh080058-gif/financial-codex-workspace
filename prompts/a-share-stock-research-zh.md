请先使用 financial-services-skill-router。

任务：对【公司名称 / A 股 Ticker】做 A 股单票投研或股票深度分析。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 按需调用 `ifind-http-api`、`akshare`、`a-share-valuation-template`、
   `a-share-comps-best-practice`、`vertical-equity-research-thesis-tracker`
   和 `vertical-equity-research-catalyst-calendar`。
5. 不要编造金融、市场、公司、consensus、guidance、target price 或评级数据。

## Required inputs

请先列出并标记已提供、缺失、需要核验或可作为 assumption 的输入：

- 公司名称、A 股 ticker、交易所、板块、行业分类
- 分析目标：走势快评、单票深度、估值、财报、thesis check 或催化剂跟踪
- 时间范围、复权口径、币种、单位
- 数据源偏好：iFinD、AKShare、官方公告、用户文件或交叉验证
- 是否需要输出 research memo、数据请求清单、表格、Excel 或 PPT

## Schema requirements

请使用 A 股投研 schema，并至少输出：

- `security_master`
- `source_log`
- `qa_status`

如有来源支持，再补充：

- `market_snapshot`
- `financial_snapshot`
- `valuation_snapshot`
- `peer_set`
- `thesis_tracker`

## Output format

最终输出：

- `Executive Summary（执行摘要）`
- 数据源、接口、参数、抓取时间和交易日
- 行情与流动性
- 财务与披露快照
- 行业与 peer set
- 估值与历史分位
- thesis、催化剂、风险和反证
- Missing data
- QA checks performed
- Not investment advice
