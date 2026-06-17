"""Human-readable renderers for trading_core CLI outputs."""

from __future__ import annotations

import json
from typing import Any


def render_markdown(kind: str, payload: dict[str, Any]) -> str:
    if kind == "intent":
        return render_intent_markdown(payload)
    if kind == "decision":
        return render_decision_markdown(payload)
    if kind == "backtest":
        return render_backtest_markdown(payload)
    if kind == "alpha_bench":
        return render_alpha_markdown(payload)
    if kind == "journal":
        return render_journal_markdown(payload)
    if kind == "review":
        return render_review_markdown(payload)
    if kind == "watchlist":
        return render_watchlist_markdown(payload)
    if kind == "search":
        return render_search_markdown(payload)
    if kind == "alerts":
        return render_alerts_markdown(payload)
    if kind == "brief":
        return render_brief_markdown(payload)
    return fenced_json_notice(payload)


def render_intent_markdown(payload: dict[str, Any]) -> str:
    entry = payload.get("user_entry") if isinstance(payload.get("user_entry"), dict) else {}
    missing_inputs = payload.get("missing_inputs") if isinstance(payload.get("missing_inputs"), list) else []
    machine_record = payload.get("machine_record") if isinstance(payload.get("machine_record"), dict) else {}
    lines = [
        f"# {entry.get('label_zh') or '用户场景'}",
        "",
        f"- 状态：`{payload.get('status', 'unknown')}`",
        f"- 目标：{payload.get('user_goal', '')}",
        f"- 识别场景：`{payload.get('scenario_id', 'unknown')}`",
    ]
    if missing_inputs:
        lines.extend(["", "## 还需要你补充", ""])
        for item in missing_inputs:
            if isinstance(item, dict):
                lines.append(f"- {item.get('question', item.get('field', '缺少输入'))}")
            else:
                lines.append(f"- {item}")
    else:
        lines.extend(
            [
                "",
                "## 执行计划",
                "",
                f"- 工作流：{entry.get('primary_action') or payload.get('workflow_id', 'unknown')}",
                f"- 默认输出：`{entry.get('default_display_profile') or payload.get('display_profile', 'app_card')}`",
                "- 保留 source log、missing data、QA 和 Not investment advice。",
            ]
        )
    if machine_record.get("missing_data"):
        lines.extend(["", "## 数据缺口", ""])
        for item in machine_record.get("missing_data") or []:
            lines.append(f"- {item}")
    lines.extend(["", "- Not investment advice: true"])
    return "\n".join(lines).strip() + "\n"


def render_decision_markdown(record: dict[str, Any]) -> str:
    card = record.get("decision_card") or {}
    plan = record.get("conditional_trade_plan") or {}
    decision = record.get("decision_support") or {}
    company = record.get("company_profile") if isinstance(record.get("company_profile"), dict) else {}
    evidence = record.get("evidence_matrix") if isinstance(record.get("evidence_matrix"), dict) else {}
    gate = record.get("evidence_sufficiency_gate") if isinstance(record.get("evidence_sufficiency_gate"), dict) else {}
    artifacts = record.get("research_artifacts") if isinstance(record.get("research_artifacts"), dict) else {}
    technical = record.get("technical_analysis") or {}
    market = record.get("market_snapshot") or {}
    price = market.get("price") if isinstance(market.get("price"), dict) else {}
    integrity = record.get("report_integrity_status") or {}
    feasibility = record.get("execution_feasibility") or {}
    prediction_market = record.get("prediction_market_context") if isinstance(record.get("prediction_market_context"), dict) else {}

    lines = [
        f"# 交易决策卡：{card.get('ticker') or ticker_from_record(record)}",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        f"| 决策状态 | `{card.get('decision_state', 'unknown')}` |",
        f"| 周期 | {card.get('horizon', 'unknown')} |",
        f"| 设定质量 | {card.get('setup_quality', 'unknown')} |",
        f"| 证据闸门 | `{gate.get('status', decision.get('evidence_sufficiency', 'unknown'))}` |",
        f"| 置信度 | {decision.get('confidence', 'unknown')} |",
        f"| 最新价/收盘 | {format_number(price.get('latest') or price.get('close'))} {price.get('currency') or ''} |",
        f"| 交易日 | {market.get('trade_date', 'unknown')} |",
        f"| QA | `{integrity.get('status', 'unknown')}` |",
        "",
        "## 公司画像",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        f"| 名称 | {company.get('name') or 'N/A'} |",
        f"| 板块/交易所 | {company.get('board') or 'unknown'} / {company.get('exchange') or 'unknown'} |",
        f"| 行业/主题 | {company.get('industry') or company.get('sector') or 'source_gap'} |",
        f"| 上市状态 | {company.get('listing_status', 'unknown')} |",
        "",
        "## 证据矩阵",
        "",
        "| 维度 | 状态 | 摘要 |",
        "|---|---|---|",
        *evidence_matrix_rows(evidence),
        "",
        "## 证据闸门",
        "",
        f"- 状态：`{gate.get('status', 'unknown')}`",
        f"- 是否允许高置信决策支持：{yes_no(gate.get('decision_support_allowed'))}",
        *bullet_list((gate.get("blocking_gaps") or [])[:4] if isinstance(gate.get("blocking_gaps"), list) else []),
        "",
        "## 条件化计划",
        "",
        "| 类型 | 价位 | 条件 |",
        "|---|---:|---|",
        f"| 触发观察 | {format_level(plan.get('trigger_level'))} | {plan.get('trigger_condition', '未生成')} |",
        f"| 失效 | {format_level(plan.get('invalidation_level'))} | {plan.get('invalidation_condition', '未生成')} |",
        f"| 风控 | {format_level(plan.get('risk_control_level'))} | {plan.get('exit_or_reduce_condition', '未生成')} |",
        "",
        "## 技术状态",
        "",
        "| 周期 | 状态 | 趋势 | ATR14 | 量能/背景 |",
        "|---|---|---|---:|---|",
    ]
    for timeframe, label in (("daily", "日线"), ("weekly", "周线"), ("monthly", "月线")):
        period = technical.get(timeframe) if isinstance(technical.get(timeframe), dict) else {}
        lines.append(
            "| {label} | `{status}` | {trend} | {atr} | {volume} |".format(
                label=label,
                status=period.get("status", "missing"),
                trend=trend_text(period),
                atr=format_number(period.get("atr14")),
                volume=volume_text(period),
            )
        )

    lines.extend(
        [
            "",
            "## 关键证据",
            *bullet_list(decision.get("supporting_evidence")),
            "",
            "## 主要风险与缺口",
            *bullet_list((decision.get("disconfirming_evidence") or []) + (decision.get("missing_data") or [])),
        ]
    )
    lines.extend(render_research_artifacts_section(artifacts))
    lines.extend(render_prediction_market_section(prediction_market))
    if feasibility:
        lines.extend(
            [
                "",
                "## A股执行可行性",
                "",
                "| 检查项 | 结果 |",
                "|---|---|",
                f"| T+1 | {yes_no(feasibility.get('t_plus_one'))} |",
                f"| 不允许做空 | {yes_no(not feasibility.get('short_selling_allowed'))} |",
                f"| 整数手 | {feasibility.get('lot_size_shares', 'unknown')} 股 |",
                f"| 涨跌停参考 | {format_percent(feasibility.get('price_limit_pct'))} |",
                f"| 触发价在次日涨跌停参考内 | {yes_no(feasibility.get('trigger_level_within_next_day_limit_reference'))} |",
            ]
        )

    lines.extend(
        [
            "",
            "<details>",
            "<summary>数据与 QA</summary>",
            "",
            *source_summary(record.get("source_capability_matrix")),
            f"- QA status: `{integrity.get('status', 'unknown')}`",
            f"- Not investment advice: {yes_no(record.get('not_investment_advice'))}",
            "- 完整 JSON：使用 `--format json` 查看；使用 `--output path.json` 保存。",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def evidence_matrix_rows(evidence: dict[str, Any]) -> list[str]:
    rows = evidence.get("dimensions") if isinstance(evidence.get("dimensions"), list) else []
    lines: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {label} | `{status}` | {summary} |".format(
                label=row.get("label") or row.get("dimension") or "unknown",
                status=row.get("status", "unknown"),
                summary=escape_table_text(row.get("summary", "")),
            )
        )
    return lines or ["| N/A | `source_gap` | 未生成证据矩阵 |"]


def render_research_artifacts_section(artifacts: dict[str, Any]) -> list[str]:
    if not artifacts:
        return []
    tear = artifacts.get("tear_sheet") if isinstance(artifacts.get("tear_sheet"), dict) else {}
    thesis = artifacts.get("thesis_tracker") if isinstance(artifacts.get("thesis_tracker"), dict) else {}
    catalysts = artifacts.get("catalyst_calendar") if isinstance(artifacts.get("catalyst_calendar"), dict) else {}
    comps = artifacts.get("comps_snapshot") if isinstance(artifacts.get("comps_snapshot"), dict) else {}
    return [
        "",
        "## 专业研究产物",
        "",
        "| 产物 | 状态 | 下一步 |",
        "|---|---|---|",
        f"| A-share tear sheet | `{tear.get('technical_snapshot', {}).get('status', tear.get('status', 'framework'))}` | 补齐估值、催化剂、风险事件后可用于一页纸速览 |",
        f"| Thesis tracker | `{thesis.get('status', 'framework')}` | 录入核心假设、验证指标和反证信号 |",
        f"| Catalyst calendar | `{catalysts.get('status', 'source_gap')}` | 接入财报、股东会、解禁、重大公告和行业政策 |",
        f"| 简版 comps | `{comps.get('status', 'source_gap')}` | 确认同业集合并补估值/增长/盈利/交易活跃度 |",
    ]


def render_prediction_market_section(context: dict[str, Any]) -> list[str]:
    status = context.get("status", "missing")
    lines = [
        "",
        "## Polymarket 宏观/事件预期",
        "",
        f"- 状态：`{status}`",
    ]
    if context.get("retrieved_at"):
        lines.append(f"- 获取时间：{context.get('retrieved_at')}")
    if status == "available":
        lines.extend(
            [
                "",
                "| 相关层级 | 市场 | 最高概率结果 | 隐含概率 | 本地概率变化 | 24h/7d变化 | 成交/流动性 |",
                "|---|---|---|---:|---:|---:|---|",
            ]
        )
        markets = context.get("selected_markets") if isinstance(context.get("selected_markets"), list) else []
        for market in markets[:5]:
            if not isinstance(market, dict):
                continue
            change = market.get("change") if isinstance(market.get("change"), dict) else {}
            question = market.get("question") or market.get("slug") or "unknown"
            if market.get("url"):
                question = f"[{escape_table_text(question)}]({market.get('url')})"
            else:
                question = escape_table_text(question)
            lines.append(
                "| {tier} | {question} | {outcome} | {prob} | {delta} | {short} / {week} | {volume} / {liquidity} |".format(
                    tier=market.get("relevance_tier", "unknown"),
                    question=question,
                    outcome=escape_table_text(market.get("top_outcome") or "N/A"),
                    prob=format_percent(market.get("implied_probability")),
                    delta=format_percent_delta(change.get("probability_delta")),
                    short=format_percent_delta(market.get("probability_change_24h")),
                    week=format_percent_delta(market.get("probability_change_7d")),
                    volume=format_number(market.get("volume")),
                    liquidity=format_number(market.get("liquidity")),
                )
            )
    limitations = context.get("limitations")
    if limitations:
        lines.extend(["", "### 主要限制", *bullet_list(limitations[:3] if isinstance(limitations, list) else limitations)])
    return lines


def render_backtest_markdown(payload: dict[str, Any]) -> str:
    prepared = payload.get("prepared_vibe_run") or {}
    validation = payload.get("backtest_validation") or {}
    metrics = validation.get("metrics") if isinstance(validation.get("metrics"), dict) else {}
    professional = validation.get("professional_validation") if isinstance(validation.get("professional_validation"), dict) else {}
    lines = [
        "# 回测验证卡",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        f"| 状态 | `{payload.get('status', 'unknown')}` |",
        f"| Vibe run_dir | `{prepared.get('run_dir', 'not_prepared')}` |",
        f"| 策略 | `{validation.get('strategy') or 'unknown'}` |",
        f"| 引擎 | `{validation.get('engine') or 'not_run'}` |",
        f"| Sharpe | {format_number(metrics.get('sharpe'))} |",
        f"| 最大回撤 | {format_percent(metrics.get('max_drawdown'))} |",
        f"| 胜率 | {format_percent(metrics.get('win_rate'))} |",
        f"| 交易次数 | {metrics.get('trade_count', 'unknown')} |",
        f"| 专业验证 | `{professional.get('status', 'not_run')}` |",
        "",
        "## 验证状态",
        *bullet_list(validation.get("validation")),
        "",
        "## 专业交易约束",
        "",
        "| 检查项 | 状态 | 限制 |",
        "|---|---|---|",
        *professional_check_rows(professional),
        "",
        "## 不可交易/需补证原因",
        *bullet_list(validation.get("untradable_reasons")),
        "",
        "<details>",
        "<summary>限制与 QA</summary>",
        "",
        *bullet_list(validation.get("limitations")),
        "- Not investment advice: true",
        "",
        "</details>",
    ]
    return "\n".join(lines).strip() + "\n"


def professional_check_rows(professional: dict[str, Any]) -> list[str]:
    checks = professional.get("checks") if isinstance(professional.get("checks"), list) else []
    rows: list[str] = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        limitations = check.get("limitations") if isinstance(check.get("limitations"), list) else []
        rows.append(
            "| {name} | `{status}` | {limitations} |".format(
                name=check.get("name", "unknown"),
                status=check.get("status", "unknown"),
                limitations=escape_table_text("; ".join(str(item) for item in limitations) or "N/A"),
            )
        )
    return rows or ["| N/A | `not_run` | N/A |"]


def render_alpha_markdown(payload: dict[str, Any]) -> str:
    diagnostics = payload.get("professional_factor_diagnostics") if isinstance(payload.get("professional_factor_diagnostics"), dict) else {}
    metrics = diagnostics.get("required_metrics") if isinstance(diagnostics.get("required_metrics"), dict) else {}
    lines = [
        "# Alpha 因子筛选卡",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        f"| 状态 | `{payload.get('status', 'unknown')}` |",
        f"| Universe | `{payload.get('universe', 'unknown')}` |",
        f"| Zoo | `{payload.get('zoo', 'unknown')}` |",
        f"| Period | `{payload.get('period', 'unknown')}` |",
        "",
        "## 分类阈值",
        *bullet_list(payload.get("classification_thresholds")),
        "",
        "## 专业因子诊断",
        "",
        "| 指标 | 状态 |",
        "|---|---|",
        *[f"| {key} | `{value}` |" for key, value in metrics.items()],
        "",
        "## 不可交易/需补证原因",
        *bullet_list(diagnostics.get("untradable_reasons")),
        "",
        "<details>",
        "<summary>数据缺口与 QA</summary>",
        "",
        *bullet_list(payload.get("missing_data")),
        "- 因子结果只作为研究证据，不直接转为买卖建议。",
        "",
        "</details>",
    ]
    return "\n".join(lines).strip() + "\n"


def render_journal_markdown(payload: dict[str, Any]) -> str:
    profile = payload.get("profile") or {}
    behavior = payload.get("behavior_diagnostics") or {}
    rule_review = payload.get("rule_consistency_review") if isinstance(payload.get("rule_consistency_review"), dict) else {}
    post_trade = payload.get("post_trade_review") if isinstance(payload.get("post_trade_review"), dict) else {}
    shadow = payload.get("shadow_account_profile") or {}
    lines = [
        "# 交易日志复盘卡",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| 交易笔数 | {profile.get('total_trades', 0)} |",
        f"| 闭合交易 | {profile.get('total_roundtrips', 0)} |",
        f"| 胜率 | {format_percent(profile.get('win_rate'))} |",
        f"| 盈亏比 | {format_number(profile.get('profit_loss_ratio'))} |",
        f"| 平均持仓天数 | {format_number(profile.get('avg_holding_days'))} |",
        f"| 每周交易频率 | {format_number(profile.get('trade_frequency_per_week'))} |",
        f"| 总 PnL | {format_number(profile.get('total_pnl'))} |",
        "",
        "## 行为诊断",
    ]
    for key, value in behavior.items():
        if isinstance(value, dict):
            lines.append(f"- `{key}`：{value.get('severity', 'unknown')}。{value.get('evidence', '')}")
    lines.extend(
        [
            "",
            "## 规则一致性复盘",
            f"- 状态：`{rule_review.get('status', 'unknown')}`",
            *bullet_list(rule_review.get("missing_data")),
            "",
            "## Post-Trade Review（交易后复盘）",
            f"- 状态：`{post_trade.get('status', 'unknown')}`",
            f"- 规则一致性：`{post_trade.get('rule_consistency_status', 'unknown')}`",
            *bullet_list(post_trade.get("improvement_actions")),
            "",
            "## Shadow Account",
            f"- 状态：`{shadow.get('status', 'unknown')}`",
            f"- 盈利闭合交易数：{shadow.get('profitable_roundtrips', 0)}",
            f"- 摘要：{shadow.get('profile_text', '未生成')}",
            "",
            "## 产物",
            *bullet_list(payload.get("artifact_paths")),
            "",
            "<details>",
            "<summary>数据与 QA</summary>",
            "",
            *bullet_list(payload.get("limitations")),
            "- Not investment advice: true",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 决策复盘卡",
        "",
        f"- 复盘周期：{payload.get('horizon')} trading days",
        f"- 记录数量：{payload.get('record_count')}",
        "",
        "| Ticker | 状态 | 置信度 | Review Status |",
        "|---|---|---|---|",
    ]
    for review in payload.get("reviews") or []:
        lines.append(
            f"| {review.get('ticker', 'unknown')} | `{review.get('decision_state', 'unknown')}` | "
            f"{review.get('confidence', 'unknown')} | {review.get('review_status', 'unknown')} |"
        )
    lines.append("\n- Not investment advice: true")
    return "\n".join(lines).strip() + "\n"


def render_watchlist_markdown(payload: dict[str, Any]) -> str:
    if payload.get("status") == "missing":
        lines = [
            "# 观察池配置卡",
            "",
            f"- 状态：`missing`",
            f"- 文件：`{payload.get('watchlist_file', 'unknown')}`",
            f"- 提示：{payload.get('message', '请先初始化观察池')}",
            "",
            "## 建议命令",
            *bullet_list(payload.get("suggested_cli_commands")),
            "",
            "## 桌面端快捷说法",
            *bullet_list(payload.get("conversation_commands")),
            "",
            "- Not investment advice: true",
        ]
        return "\n".join(lines).strip() + "\n"

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    qa = payload.get("qa_status") if isinstance(payload.get("qa_status"), dict) else {}
    deep_selection_pending = payload.get("deep_research_selection_status") == "pending_daily_screening"
    deep_selection_value = (
        payload.get("deep_research_selection_note") or "待每日筛选后确定"
        if deep_selection_pending
        else ticker_list(payload.get("deep_research_candidates"))
    )
    daily_flow = (
        f"先筛 Top{summary.get('screen_top_n', 10)}，再按每日证据排序确定 Top{summary.get('deep_research_top_n', 5)} 深研"
        if deep_selection_pending
        else f"先筛 Top{summary.get('screen_top_n', 10)}，默认深研 Top{summary.get('deep_research_top_n', 5)}"
    )
    lines = [
        "# 观察池配置卡",
        "",
        f"- 操作：`{payload.get('action', 'show')}` / `{payload.get('operation_status', 'ok')}`",
        f"- 文件：`{payload.get('watchlist_file', 'unknown')}`",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        f"| 名称 | {summary.get('name', 'default')} |",
        f"| 市场 | `{summary.get('market', 'unknown')}` |",
        f"| 标的数 | {summary.get('total_count', 0)} 个，其中活跃 {summary.get('active_count', 0)} 个 |",
        f"| 分组数 | {summary.get('group_count', 0)} |",
        f"| 每日流程 | {daily_flow} |",
        f"| 决策周期 | {summary.get('decision_horizon', '20d')} |",
        f"| 证据闸门 | `{summary.get('evidence_gate_policy', 'standard')}` |",
        f"| 排序策略 | `{summary.get('ranking_policy', 'static_watchlist_order')}` |",
        f"| 新闻偏好 | {'启用' if summary.get('news_enabled') else '未启用'} |",
        f"| 数据刷新 | `{(summary.get('source_refresh_policy') or {}).get('market_data', 'unknown')}` |",
        "",
        "## 标的列表",
        "",
        "| 优先级 | Ticker | 名称 | 分组 | 状态 | 研究阶段 | 周期 | 标签 | 下一步 |",
        "|---:|---|---|---|---|---|---|---|---|",
    ]
    for item in payload.get("items") or []:
        tags = ", ".join(item.get("tags") or [])
        lines.append(
            "| {priority} | {ticker} | {name} | {group} | `{status}` | `{research_state}` | {horizon} | {tags} | {next_action} |".format(
                priority=item.get("priority", ""),
                ticker=item.get("ticker", "unknown"),
                name=item.get("name") or "",
                group=item.get("group") or "",
                status=item.get("status") or "",
                research_state=item.get("research_state") or "new",
                horizon=item.get("horizon") or "",
                tags=tags,
                next_action=item.get("next_action") or "",
            )
        )

    lines.extend(
        [
            "",
            "## 每日流程入口",
            "",
            "| 阶段 | 默认候选 |",
            "|---|---|",
            f"| Top{summary.get('screen_top_n', 10)} 初筛 | {ticker_list(payload.get('top_watchlist'))} |",
            f"| Top{summary.get('deep_research_top_n', 5)} 深研 | {deep_selection_value} |",
            "",
            "## 桌面端快捷说法",
            *bullet_list(payload.get("conversation_commands")),
            "",
            "<details>",
            "<summary>CLI、分组与 QA</summary>",
            "",
            "### CLI",
            *bullet_list(payload.get("suggested_cli_commands")),
            "",
            "### 分组",
            *bullet_list([f"{item.get('group')}: {item.get('active_count')} active / {item.get('count')} total" for item in payload.get("group_summary") or []]),
            "",
            f"- QA status: `{qa.get('status', 'unknown')}`",
            *([] if not qa.get("warnings") else bullet_list(qa.get("warnings"))),
            "- Not investment advice: true",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_search_markdown(payload: dict[str, Any]) -> str:
    candidates = payload.get("search_candidates") if isinstance(payload.get("search_candidates"), list) else []
    qa = payload.get("qa_status") if isinstance(payload.get("qa_status"), dict) else {}
    lines = [
        f"# A股搜索卡：{payload.get('query', '')}",
        "",
        f"- 状态：`{payload.get('status', 'unknown')}`",
        f"- 市场：`{payload.get('market', 'a_share')}`",
        "",
        "| Ticker | 名称 | 匹配方式 | 置信度 | 标识状态 |",
        "|---|---|---|---|---|",
    ]
    for item in candidates:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| {ticker} | {name} | {match} | {confidence} | {status} |".format(
                ticker=item.get("ticker", "unknown"),
                name=item.get("name", ""),
                match=item.get("match_type", "unknown"),
                confidence=item.get("confidence", "unknown"),
                status=item.get("identifier_status", "unknown"),
            )
        )
    lines.extend(
        [
            "",
            "<details>",
            "<summary>数据与 QA</summary>",
            "",
            *source_summary(payload.get("source_capability_matrix")),
            f"- QA status: `{qa.get('status', 'unknown')}`",
            *([] if not payload.get("missing_data") else bullet_list(payload.get("missing_data"))),
            "- Not investment advice: true",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_alerts_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    checks = ((payload.get("alert_check_result") or {}).get("checks") if isinstance(payload.get("alert_check_result"), dict) else None) or []
    qa = payload.get("qa_status") if isinstance(payload.get("qa_status"), dict) else {}
    lines = [
        "# 价格提醒卡",
        "",
        f"- 操作：`{payload.get('action', 'unknown')}` / `{payload.get('operation_status', 'ok')}`",
        f"- 文件：`{payload.get('alerts_file', 'unknown')}`",
        "",
        "| 项目 | 数量 |",
        "|---|---:|",
        f"| 全部规则 | {summary.get('total_count', 0)} |",
        f"| 活跃 | {summary.get('active_count', 0)} |",
        f"| 已触发 | {summary.get('triggered_count', 0)} |",
        f"| 已过期 | {summary.get('expired_count', 0)} |",
        "",
        "## 规则",
        "",
        "| Ticker | 条件 | 阈值 | 状态 | 最近价格 |",
        "|---|---|---:|---|---:|",
    ]
    for rule in payload.get("alert_rules") or []:
        if not isinstance(rule, dict):
            continue
        lines.append(
            "| {ticker} | `{condition}` | {level} | `{status}` | {price} |".format(
                ticker=rule.get("ticker", "unknown"),
                condition=rule.get("condition", "unknown"),
                level=format_number(rule.get("level")),
                status=rule.get("status", "unknown"),
                price=format_number(rule.get("last_observed_price")),
            )
        )
    if checks:
        lines.extend(["", "## 检查结果", "", "| Ticker | 状态 | 最新价 | 触发 |", "|---|---|---:|---|"])
        for check in checks:
            if isinstance(check, dict):
                lines.append(
                    f"| {check.get('ticker', 'unknown')} | `{check.get('status', 'unknown')}` | {format_number(check.get('latest_price'))} | {yes_no(check.get('triggered'))} |"
                )
    lines.extend(
        [
            "",
            "<details>",
            "<summary>数据与 QA</summary>",
            "",
            f"- QA status: `{qa.get('status', 'unknown')}`",
            *([] if not qa.get("warnings") else bullet_list(qa.get("warnings"))),
            "- 不创建、不发送、不执行订单。",
            "- Not investment advice: true",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_brief_markdown(payload: dict[str, Any]) -> str:
    market_brief = payload.get("market_brief") if isinstance(payload.get("market_brief"), dict) else {}
    morning = payload.get("morning_brief") if isinstance(payload.get("morning_brief"), dict) else {}
    market_context = morning.get("market_context") if isinstance(morning.get("market_context"), dict) else {}
    summary = market_brief.get("summary") if isinstance(market_brief.get("summary"), dict) else {}
    qa = payload.get("qa_status") if isinstance(payload.get("qa_status"), dict) else {}
    lines = [
        f"# Morning Brief（晨会简报）：{payload.get('review_date', 'unknown')}",
        "",
        "- 每日观察池摘要：已升级为 Morning Brief。",
        f"- 模式：`{(payload.get('analysis_mode') or {}).get('mode', 'research')}`",
        f"- 文件：`{payload.get('watchlist_file', 'unknown')}`",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        f"| 观察池 | {summary.get('watchlist_name', 'default')} |",
        f"| 市场 | `{summary.get('market', 'unknown')}` |",
        f"| 覆盖标的 | {summary.get('reviewed_count', 0)} |",
        f"| 有行情标的 | {summary.get('quote_available_count', 0)} |",
        f"| 触发提醒 | {summary.get('triggered_alert_count', 0)} |",
        f"| 新闻状态 | `{summary.get('news_status', 'unknown')}` |",
        f"| 动态排序 | `{summary.get('dynamic_ranking', 'disabled')}` |",
        f"| Top10 | {', '.join(summary.get('top10_candidates') or []) or 'N/A'} |",
        f"| 深研 Top5 | {', '.join(summary.get('deep_research_top5') or []) or 'N/A'} |",
        "",
        "## 市场环境层",
        "",
        f"- 状态：`{market_context.get('status', 'source_gap')}`",
        *bullet_list((market_context.get("missing_data") or [])[:3] if isinstance(market_context.get("missing_data"), list) else []),
        "",
        "## 标的快照",
        "",
        "| 动态分 | 优先级 | Ticker | 名称 | 分组 | 最新价 | 阶段 | 下一步 |",
        "|---:|---:|---|---|---|---:|---|---|",
    ]
    for row in market_brief.get("rows") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {score} | {priority} | {ticker} | {name} | {group} | {price} | `{stage}` | {next_action} |".format(
                score=format_number(row.get("dynamic_rank_score")),
                priority=row.get("priority", ""),
                ticker=row.get("ticker", "unknown"),
                name=row.get("name", ""),
                group=row.get("group", ""),
                price=format_number(row.get("latest_price")),
                stage=row.get("workflow_stage", row.get("quote_status", "unknown")),
                next_action=row.get("next_action", ""),
            )
        )
    triggered = market_brief.get("triggered_alerts") if isinstance(market_brief.get("triggered_alerts"), list) else []
    if triggered:
        lines.extend(["", "## 触发提醒", *bullet_list([f"{item.get('ticker')}: {item.get('condition')} {item.get('level')}" for item in triggered if isinstance(item, dict)])])
    todos = morning.get("today_todos") if isinstance(morning.get("today_todos"), list) else []
    if todos:
        lines.extend(["", "## 今日待办", *bullet_list(todos)])
    lines.extend(
        [
            "",
            "<details>",
            "<summary>数据与 QA</summary>",
            "",
            *source_summary(payload.get("source_capability_matrix")),
            f"- QA status: `{qa.get('status', 'unknown')}`",
            *([] if not qa.get("warnings") else bullet_list(qa.get("warnings"))),
            "- Not investment advice: true",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def format_level(level: Any) -> str:
    if not isinstance(level, dict):
        return "N/A"
    value = format_number(level.get("value"))
    unit = level.get("unit") or ""
    return f"{value} {unit}".strip()


def format_number(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def format_percent(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    return str(value)


def format_percent_delta(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value * 100:+.2f}pp"
    return str(value)


def escape_table_text(value: Any) -> str:
    return str(value).replace("|", "\\|")


def yes_no(value: Any) -> str:
    if value is True:
        return "是"
    if value is False:
        return "否"
    return "未知"


def ticker_from_record(record: dict[str, Any]) -> str:
    security = record.get("security_master") if isinstance(record.get("security_master"), dict) else {}
    return security.get("ticker") or record.get("ticker") or "unknown"


def trend_text(period: dict[str, Any]) -> str:
    moving = period.get("moving_averages") if isinstance(period.get("moving_averages"), dict) else {}
    return moving.get("trend_summary") or period.get("trend_summary") or "N/A"


def volume_text(period: dict[str, Any]) -> str:
    volume = period.get("volume_price") if isinstance(period.get("volume_price"), dict) else {}
    return volume.get("volume_confirmation") or period.get("volume_confirmation") or period.get("cross_period_use") or "N/A"


def bullet_list(value: Any) -> list[str]:
    if not value:
        return ["- N/A"]
    if isinstance(value, dict):
        return [f"- `{key}`: {item}" for key, item in value.items()]
    if isinstance(value, list):
        return [f"- {item}" for item in value]
    return [f"- {value}"]


def ticker_list(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "N/A"
    tickers = [str(item.get("ticker")) for item in value if isinstance(item, dict) and item.get("ticker")]
    return ", ".join(tickers) if tickers else "N/A"


def source_summary(matrix: Any) -> list[str]:
    if not isinstance(matrix, list) or not matrix:
        return ["- 数据源：N/A"]
    lines = []
    for item in matrix[:3]:
        if not isinstance(item, dict):
            continue
        lines.append(
            "- 数据源 `{name}`：priority={priority}, status={status}".format(
                name=item.get("source_name", "unknown"),
                priority=item.get("priority", "unknown"),
                status=item.get("status", "unknown"),
            )
        )
    return lines or ["- 数据源：N/A"]


def fenced_json_notice(payload: dict[str, Any]) -> str:
    return "```json\n" + json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n"
