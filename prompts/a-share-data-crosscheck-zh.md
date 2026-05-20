请先使用 financial-services-skill-router。

任务：对【公司名称 / A 股 Ticker】做 iFinD 与 AKShare 数据交叉验证。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `ifind-http-api` 和 `akshare`，分别记录接口、参数、抓取时间、
   交易日、字段和行数。

## Cross-check scope

请比较以下项目，缺失则明确标记：

- ticker、公司名、交易所、板块
- 最新价 / 收盘价 / 前收盘
- 开盘、最高、最低
- 成交量、成交量单位、成交额、换手率
- 市值、流通市值
- 历史行情日期覆盖和行数
- 复权口径

## Difference handling

如果 iFinD 和 AKShare 数据不同，请按以下原因解释：

- 时间戳不同：实时、盘中、日终
- 交易日不同
- 单位不同：股、手、元、万元、亿元
- 复权口径不同：不复权、前复权、后复权、未知
- endpoint/interface 不同
- 上游来源、授权、网络或字段缺失限制

## Output format

最终输出：

- 数据源对比表
- 字段级差异说明
- 可采用的主口径和原因
- 不可下结论的数据缺口
- `source_log`
- `qa_status.cross_source_check`
- QA checks performed
- Not investment advice
