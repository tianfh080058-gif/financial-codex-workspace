"""Human-readable renderers for trading_core CLI outputs."""

from __future__ import annotations

import json
from typing import Any


def render_markdown(kind: str, payload: dict[str, Any]) -> str:
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
    return fenced_json_notice(payload)


def render_decision_markdown(record: dict[str, Any]) -> str:
    card = record.get("decision_card") or {}
    plan = record.get("conditional_trade_plan") or {}
    decision = record.get("decision_support") or {}
    technical = record.get("technical_analysis") or {}
    market = record.get("market_snapshot") or {}
    price = market.get("price") if isinstance(market.get("price"), dict) else {}
    integrity = record.get("report_integrity_status") or {}
    feasibility = record.get("execution_feasibility") or {}

    lines = [
        f"# 交易决策卡：{card.get('ticker') or ticker_from_record(record)}",
        "",
        "| 项目 | 内容 |",
        "|---|---|",
        f"| 决策状态 | `{card.get('decision_state', 'unknown')}` |",
        f"| 周期 | {card.get('horizon', 'unknown')} |",
        f"| 设定质量 | {card.get('setup_quality', 'unknown')} |",
        f"| 置信度 | {decision.get('confidence', 'unknown')} |",
        f"| 最新价/收盘 | {format_number(price.get('latest') or price.get('close'))} {price.get('currency') or ''} |",
        f"| 交易日 | {market.get('trade_date', 'unknown')} |",
        f"| QA | `{integrity.get('status', 'unknown')}` |",
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


def render_backtest_markdown(payload: dict[str, Any]) -> str:
    prepared = payload.get("prepared_vibe_run") or {}
    validation = payload.get("backtest_validation") or {}
    metrics = validation.get("metrics") if isinstance(validation.get("metrics"), dict) else {}
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
        "",
        "## 验证状态",
        *bullet_list(validation.get("validation")),
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


def render_alpha_markdown(payload: dict[str, Any]) -> str:
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
        f"| 每日流程 | 先筛 Top{summary.get('screen_top_n', 10)}，默认深研 Top{summary.get('deep_research_top_n', 5)} |",
        f"| 决策周期 | {summary.get('decision_horizon', '20d')} |",
        f"| 证据闸门 | `{summary.get('evidence_gate_policy', 'standard')}` |",
        "",
        "## 标的列表",
        "",
        "| 优先级 | Ticker | 名称 | 分组 | 状态 | 周期 | 标签 | 下一步 |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for item in payload.get("items") or []:
        tags = ", ".join(item.get("tags") or [])
        lines.append(
            "| {priority} | {ticker} | {name} | {group} | `{status}` | {horizon} | {tags} | {next_action} |".format(
                priority=item.get("priority", ""),
                ticker=item.get("ticker", "unknown"),
                name=item.get("name") or "",
                group=item.get("group") or "",
                status=item.get("status") or "",
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
            f"| Top{summary.get('deep_research_top_n', 5)} 深研 | {ticker_list(payload.get('deep_research_candidates'))} |",
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
