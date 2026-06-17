"""Professional A-share research artifact builders."""

from __future__ import annotations

from typing import Any

from .common import utc_now


EVIDENCE_DIMENSIONS = (
    "market",
    "technical",
    "financials",
    "valuation",
    "announcements_news",
    "sector_peers",
    "capital_flow",
    "risk_events",
)


def build_company_profile(
    security_master: dict[str, Any],
    *,
    market_snapshot: dict[str, Any] | None = None,
    missing_data: list[str] | None = None,
) -> dict[str, Any]:
    missing = list(missing_data or [])
    return {
        "ticker": security_master.get("ticker"),
        "name": security_master.get("name") or security_master.get("company_name"),
        "market": security_master.get("market"),
        "exchange": security_master.get("exchange"),
        "board": security_master.get("board") or infer_board(security_master.get("ticker")),
        "currency": security_master.get("currency") or "CNY",
        "business_summary": security_master.get("business_summary"),
        "industry": security_master.get("industry"),
        "sector": security_master.get("sector"),
        "listing_status": security_master.get("listing_status", "unknown"),
        "float_market_cap": ((market_snapshot or {}).get("capitalization") or {}).get("float_market_cap"),
        "recent_catalysts": [],
        "key_risks": [
            "公告、财务、估值和行业证据未完整接入时，公司画像只能作为研究框架。",
            "需刷新交易状态、ST/停牌、涨跌停和复权口径后再进入高置信决策。",
        ],
        "source_ref": security_master.get("source_ref") or ["source_log[0]"],
        "missing_data": unique(
            [
                *missing,
                "business summary not sourced",
                "industry/board/listing status may require security master refresh",
                "recent catalysts not sourced",
            ]
        ),
    }


def build_evidence_matrix(
    *,
    market_snapshot: dict[str, Any] | None,
    technical_analysis: dict[str, Any] | None,
    financial_snapshot: dict[str, Any] | None = None,
    valuation_snapshot: dict[str, Any] | None = None,
    announcements: list[dict[str, Any]] | None = None,
    peer_set: dict[str, Any] | None = None,
    capital_flow: dict[str, Any] | None = None,
    risk_events: list[dict[str, Any]] | None = None,
    source_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = [
        evidence_row(
            "market",
            "行情与流动性",
            "available" if market_snapshot else "source_gap",
            market_summary(market_snapshot),
            source_refs_from_obj(market_snapshot),
            [] if market_snapshot else ["market snapshot missing"],
        ),
        evidence_row(
            "technical",
            "K线与趋势",
            "available" if technical_analysis else "source_gap",
            technical_summary(technical_analysis),
            source_refs_from_obj(technical_analysis),
            [] if technical_analysis else ["technical analysis missing"],
        ),
        evidence_row(
            "financials",
            "财务摘要",
            "available" if financial_snapshot else "source_gap",
            snapshot_summary(financial_snapshot, "financial_summary"),
            source_refs_from_obj(financial_snapshot),
            [] if financial_snapshot else ["financial statements/indicators not sourced"],
        ),
        evidence_row(
            "valuation",
            "估值分位",
            "available" if valuation_snapshot else "source_gap",
            snapshot_summary(valuation_snapshot, "valuation_summary"),
            source_refs_from_obj(valuation_snapshot),
            [] if valuation_snapshot else ["valuation multiples/percentiles not sourced"],
        ),
        evidence_row(
            "announcements_news",
            "公告与新闻",
            "available" if announcements else "source_gap",
            list_summary(announcements, "headline"),
            source_refs_from_list(announcements),
            [] if announcements else ["announcements/news not sourced"],
        ),
        evidence_row(
            "sector_peers",
            "行业与同业",
            "available" if peer_set else "source_gap",
            snapshot_summary(peer_set, "peer_summary"),
            source_refs_from_obj(peer_set),
            [] if peer_set else ["sector and peer set not sourced"],
        ),
        evidence_row(
            "capital_flow",
            "资金面",
            "available" if capital_flow else "source_gap",
            snapshot_summary(capital_flow, "flow_summary"),
            source_refs_from_obj(capital_flow),
            [] if capital_flow else ["capital flow data not sourced"],
        ),
        evidence_row(
            "risk_events",
            "风险事件",
            "available" if risk_events else "source_gap",
            list_summary(risk_events, "event"),
            source_refs_from_list(risk_events),
            [] if risk_events else ["risk events not sourced"],
        ),
    ]
    available_count = sum(1 for row in rows if row["status"] == "available")
    source_gap_count = len(rows) - available_count
    has_market = any(row["dimension"] == "market" and row["status"] == "available" for row in rows)
    has_technical = any(row["dimension"] == "technical" and row["status"] == "available" for row in rows)
    non_technical_count = available_count - int(has_market) - int(has_technical)
    sufficiency = "decision_ready" if has_market and has_technical and non_technical_count >= 2 else "research_only"
    blocking_gaps = [
        gap
        for row in rows
        if row["status"] != "available"
        for gap in row.get("missing_data", [])
    ]
    if sufficiency != "decision_ready":
        blocking_gaps.insert(0, "Evidence gate blocks high-confidence conditional decision support until non-technical evidence improves.")
    return {
        "generated_at": utc_now(),
        "dimensions": rows,
        "summary": {
            "available_count": available_count,
            "source_gap_count": source_gap_count,
            "evidence_sufficiency": sufficiency,
            "decision_support_allowed": sufficiency == "decision_ready",
            "non_technical_available_count": non_technical_count,
            "source_log_count": len(source_log or []),
        },
        "blocking_gaps": unique(blocking_gaps),
        "policy": {
            "technical_only_decision_blocked": True,
            "no_target_price_or_rating": True,
            "not_investment_advice_required": True,
        },
    }


def build_research_artifacts(
    *,
    ticker: str,
    horizon: str,
    company_profile: dict[str, Any],
    evidence_matrix: dict[str, Any],
    technical_analysis: dict[str, Any] | None,
    missing_data: list[str] | None = None,
) -> dict[str, Any]:
    gaps = unique([*(missing_data or []), *evidence_matrix.get("blocking_gaps", [])])
    company_name = company_profile.get("name") or ticker
    return {
        "tear_sheet": {
            "title": f"{company_name} A-share tear sheet",
            "ticker": ticker,
            "company_profile": company_profile,
            "valuation_snapshot": {
                "status": "source_gap",
                "missing_data": ["valuation multiples and percentile data not sourced"],
            },
            "technical_snapshot": {
                "status": "available" if technical_analysis else "source_gap",
                "summary": technical_summary(technical_analysis),
                "source_ref": source_refs_from_obj(technical_analysis),
            },
            "catalysts": [],
            "risks": company_profile.get("key_risks", []),
            "missing_data": gaps,
        },
        "thesis_tracker": {
            "status": "framework",
            "ticker": ticker,
            "core_thesis": [],
            "validation_indicators": [
                "price/volume confirmation",
                "financial trend confirmation",
                "announcement or catalyst confirmation",
                "peer/sector relative strength confirmation",
            ],
            "disconfirming_signals": [
                "technical invalidation",
                "source data contradicts setup",
                "risk event or disclosure weakens thesis",
            ],
            "next_review_horizon": horizon,
            "missing_data": gaps,
        },
        "catalyst_calendar": {
            "status": "source_gap",
            "events": [],
            "required_event_types": ["earnings", "shareholder_meeting", "lockup_expiry", "major_announcement", "industry_policy"],
            "missing_data": ["catalyst calendar not sourced from disclosures or data provider"],
        },
        "comps_snapshot": {
            "status": "source_gap",
            "peer_set_status": "candidate_peers_required",
            "metrics": ["valuation", "growth", "profitability", "trading_activity"],
            "missing_data": ["peer set and comparable metrics not sourced"],
        },
    }


def build_market_context_layer() -> dict[str, Any]:
    return {
        "status": "source_gap",
        "dimensions": {
            "indices": "source_gap",
            "turnover": "source_gap",
            "northbound_flow": "source_gap",
            "margin_financing": "source_gap",
            "sector_heat": "source_gap",
            "fx_rates": "source_gap",
            "rates": "source_gap",
            "offshore_markets": "source_gap",
        },
        "missing_data": [
            "Market context layer requires index, turnover, northbound, margin financing, sector, FX/rates, and offshore market feeds.",
        ],
        "source_ref": [],
    }


def evidence_gate_status(evidence_matrix: dict[str, Any] | None) -> str:
    if not isinstance(evidence_matrix, dict):
        return "research_only"
    summary = evidence_matrix.get("summary") if isinstance(evidence_matrix.get("summary"), dict) else {}
    return str(summary.get("evidence_sufficiency") or "research_only")


def evidence_row(
    dimension: str,
    label: str,
    status: str,
    summary: str,
    source_ref: list[str],
    missing_data: list[str],
) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "label": label,
        "status": status,
        "summary": summary,
        "source_ref": source_ref,
        "missing_data": missing_data,
    }


def market_summary(snapshot: dict[str, Any] | None) -> str:
    if not isinstance(snapshot, dict):
        return "行情快照未取得。"
    price = snapshot.get("price") if isinstance(snapshot.get("price"), dict) else {}
    return "latest={latest}, trade_date={trade_date}, adjustment_basis={adjustment}".format(
        latest=price.get("latest") or price.get("close"),
        trade_date=snapshot.get("trade_date", "unknown"),
        adjustment=price.get("adjustment_basis", "unknown"),
    )


def technical_summary(technical: dict[str, Any] | None) -> str:
    if not isinstance(technical, dict):
        return "技术分析未取得。"
    cross = technical.get("cross_timeframe_summary") if isinstance(technical.get("cross_timeframe_summary"), dict) else {}
    daily = technical.get("daily") if isinstance(technical.get("daily"), dict) else {}
    return "overall={overall}, alignment={alignment}, daily={daily_status}".format(
        overall=cross.get("overall_status", "unknown"),
        alignment=cross.get("alignment", "unknown"),
        daily_status=daily.get("status", "unknown"),
    )


def snapshot_summary(snapshot: dict[str, Any] | None, preferred_key: str) -> str:
    if not isinstance(snapshot, dict):
        return "未取得。"
    value = snapshot.get(preferred_key) or snapshot.get("summary")
    return str(value or "已取得结构化数据，需查看 JSON 明细。")


def list_summary(items: list[dict[str, Any]] | None, key: str) -> str:
    if not items:
        return "未取得。"
    first = items[0] if isinstance(items[0], dict) else {}
    return str(first.get(key) or first.get("summary") or f"{len(items)} items sourced")


def source_refs_from_obj(value: dict[str, Any] | None) -> list[str]:
    if not isinstance(value, dict):
        return []
    refs = value.get("source_ref")
    return refs if isinstance(refs, list) else []


def source_refs_from_list(values: list[dict[str, Any]] | None) -> list[str]:
    refs: list[str] = []
    for item in values or []:
        if not isinstance(item, dict):
            continue
        item_refs = item.get("source_ref")
        if isinstance(item_refs, list):
            refs.extend(str(ref) for ref in item_refs)
    return unique(refs)


def infer_board(ticker: Any) -> str | None:
    text = str(ticker or "")
    code = text.split(".", 1)[0]
    if code.startswith("688"):
        return "科创板"
    if code.startswith("30"):
        return "创业板"
    if code.startswith(("43", "83", "87", "88", "92")):
        return "北交所"
    if code.startswith(("60", "00")):
        return "主板"
    return None


def unique(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        key = str(item)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
