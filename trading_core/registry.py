"""Workflow recipe registry and intent routing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import PROJECT_ROOT
from .runtime import IntentRoute, MissingInput, WorkflowContext


WORKFLOWS_DIR = PROJECT_ROOT / ".agents" / "workflows"
DEFAULT_WORKFLOW_ID = "daily_a_share_decision_pipeline"
WORKFLOW_EXECUTORS = {
    "daily_a_share_decision_pipeline": "watchlist_review",
    "watchlist_daily_review": "watchlist_review",
    "a_share_decision_support": "decision_support",
    "a_share_deep_research": "deep_research",
    "trade_journal_shadow_review": "journal_review",
    "vibe_backtest_validation": "strategy_validation",
    "alpha_factor_bench": "factor_validation",
}


class WorkflowRegistry:
    def __init__(self, workflows_dir: Path = WORKFLOWS_DIR) -> None:
        self.workflows_dir = workflows_dir
        self.recipes = load_workflow_recipes(workflows_dir)

    def route_intent(self, context: WorkflowContext, workflow_id: str | None = None) -> IntentRoute:
        selected_id = workflow_id or self._score_intent(context)
        recipe = self.recipes[selected_id]
        entry = user_entry(recipe)
        return IntentRoute(
            workflow_id=selected_id,
            scenario_id=str(entry.get("scenario_id") or selected_id),
            executor=str(entry.get("executor") or WORKFLOW_EXECUTORS.get(selected_id, selected_id)),
            confidence=self._confidence(selected_id, context),
            matched_terms=self._matched_terms(recipe, context.intent),
            recipe=recipe,
        )

    def missing_inputs(self, route: IntentRoute, context: WorkflowContext) -> list[MissingInput]:
        if context.command != "run" and context.action in {"search", "watchlist", "alerts"}:
            return []
        missing: list[MissingInput] = []
        for item in user_entry(route.recipe).get("required_inputs_ui", []):
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or "")
            if not field or input_is_satisfied(field, context):
                continue
            missing.append(MissingInput(field=field, question=question_for(item, field)))
        return missing

    def _score_intent(self, context: WorkflowContext) -> str:
        scores: list[tuple[float, str]] = []
        lowered = context.intent.lower()
        for workflow_id, recipe in self.recipes.items():
            matched = self._matched_terms(recipe, context.intent)
            score = len(matched) * 2.0
            if workflow_id == "a_share_decision_support" and context.ticker:
                score += 1.5
            if workflow_id == "alpha_factor_bench" and any(term in lowered for term in ("alpha", "因子", "ic", "ir", "gtja")):
                score += 5.0
            if workflow_id == "vibe_backtest_validation" and any(term in lowered for term in ("回测", "backtest", "策略")):
                score += 4.0
            if workflow_id == "trade_journal_shadow_review" and any(term in lowered for term in ("交易记录", "成交", "券商", "shadow")):
                score += 5.0
            if workflow_id == "a_share_deep_research" and any(term in lowered for term in ("深研", "基本面", "公司研究", "thesis")):
                score += 4.0
            if workflow_id == "a_share_decision_support" and any(term in lowered for term in ("买卖点", "决策", "这只票", "分析这只票")):
                score += 4.0
            if workflow_id == "daily_a_share_decision_pipeline" and any(term in lowered for term in ("每日", "今天", "看盘", "摘要")):
                score += 4.0
            scores.append((score, workflow_id))
        scores.sort(reverse=True)
        best_score, best_id = scores[0] if scores else (0.0, DEFAULT_WORKFLOW_ID)
        if best_score <= 0 and context.ticker:
            return "a_share_decision_support"
        if best_score <= 0:
            return DEFAULT_WORKFLOW_ID
        return best_id

    def _confidence(self, workflow_id: str, context: WorkflowContext) -> float:
        matched = self._matched_terms(self.recipes[workflow_id], context.intent)
        base = len(matched) * 2.0
        if workflow_id == "a_share_decision_support" and context.ticker:
            base += 1.5
        if base <= 0:
            base = 1.0
        return min(0.95, round(base / 8.0, 2))

    def _matched_terms(self, recipe: dict[str, Any], intent: str) -> list[str]:
        lowered = intent.lower()
        terms = collect_match_terms(recipe)
        matched = [term for term in terms if term and term.lower() in lowered]
        return list(dict.fromkeys(matched))[:8]


def load_workflow_recipes(workflows_dir: Path = WORKFLOWS_DIR) -> dict[str, dict[str, Any]]:
    recipes: dict[str, dict[str, Any]] = {}
    for path in sorted(workflows_dir.glob("*.json")):
        try:
            recipe = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        workflow_id = recipe.get("workflow_id")
        if isinstance(workflow_id, str):
            recipes[workflow_id] = recipe
    return recipes


def user_entry(recipe: dict[str, Any]) -> dict[str, Any]:
    entry = recipe.get("user_entry")
    return entry if isinstance(entry, dict) else {}


def collect_match_terms(recipe: dict[str, Any]) -> list[str]:
    entry = user_entry(recipe)
    terms: list[str] = []
    for key in ("label_zh", "primary_action"):
        value = entry.get(key)
        if isinstance(value, str):
            terms.append(value)
    for values in (recipe.get("intent_triggers"), entry.get("example_utterances"), entry.get("match_terms")):
        if isinstance(values, list):
            terms.extend([item for item in values if isinstance(item, str)])
    return list(dict.fromkeys(terms))


def input_is_satisfied(field: str, context: WorkflowContext) -> bool:
    if field in {"watchlist_file", "review_date", "analysis_mode", "market"}:
        return True
    if field in {"ticker", "company_name_or_security_master"}:
        return bool(context.ticker)
    if field == "broker_export_file":
        return bool(context.file)
    if field == "strategy":
        return bool(context.strategy)
    if field == "start_date":
        return bool(context.start)
    if field == "end_date":
        return bool(context.end)
    if field == "universe":
        return bool(context.universe)
    if field == "zoo":
        return bool(context.zoo)
    if field == "period":
        return bool(context.period)
    return True


def question_for(item: dict[str, Any], field: str) -> str:
    question = item.get("question_zh")
    if isinstance(question, str) and question:
        return question
    defaults = {
        "ticker": "请告诉我要分析的 A股 ticker 或公司名称。",
        "broker_export_file": "请提供券商成交导出文件路径，例如 CSV 或 Excel。",
        "strategy": "请提供策略名称，例如 technical_breakout。",
        "start_date": "请提供回测开始日期，例如 2024-01-01。",
        "end_date": "请提供回测结束日期，例如 2026-05-23。",
        "universe": "请提供因子评估 universe，例如 csi300。",
        "zoo": "请提供因子库名称，例如 gtja191。",
        "period": "请提供评估区间，例如 2021-2026。",
    }
    return defaults.get(field, f"请补充 {field}。")
