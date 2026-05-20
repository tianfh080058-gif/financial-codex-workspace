请先使用 financial-services-skill-router。

任务：为【公司列表 / A 股 Ticker / 行业】创建 A 股催化剂日历。

请按当前工作区规则执行：

1. 读取 `.agents/SKILLS_INDEX.md`。
2. 使用 `china-market-overlay`。
3. 使用 `a-share-equity-research-workflow`。
4. 使用 `vertical-equity-research-catalyst-calendar`。
5. 按需调用 `ifind-http-api`、`akshare`、官方公告、交易所披露或用户文件。

## Catalyst scope

请覆盖并标记来源：

- 定期报告：年报、一季报、半年报、三季报
- 业绩预告、业绩快报、分红、股东大会、投资者关系活动记录表
- 限售解禁、定增、回购、股权激励
- 行业数据、商品价格、政策事件、监管事项
- 公司特定重大事项、产能投放、项目进展、管理层变动

## Required fields

催化剂日历至少包含：

- 日期或预计日期
- 公司 / ticker
- 事件类型
- 事件描述
- 影响方向：positive / negative / neutral / unknown
- 影响强度：high / medium / low / unknown
- 来源和链接/文件名/接口
- 是否已验证
- 跟踪动作

## Output format

最终输出：

- Calendar view
- This week / next month preview
- 高影响事件清单
- 未验证事件和缺失数据
- Source log
- QA checks performed
- Not investment advice
