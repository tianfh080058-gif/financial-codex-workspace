#!/usr/bin/env python3
"""Validate workflow recipe references and required fields."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
WORKFLOWS_DIR = ROOT / ".agents" / "workflows"
SKILLS_DIR = ROOT / ".agents" / "skills"
DISPLAY_PROFILES = {"app_card", "cli_markdown", "machine_json", "audit_appendix"}
EXPECTED_WORKFLOWS = {
    "daily_a_share_decision_pipeline",
    "a_share_decision_support",
    "watchlist_daily_review",
    "trade_journal_shadow_review",
    "vibe_backtest_validation",
    "alpha_factor_bench",
    "a_share_deep_research",
}
REQUIRED_FIELDS = {
    "workflow_id",
    "title",
    "intent_triggers",
    "required_skills",
    "execution_order",
    "required_inputs",
    "optional_inputs",
    "required_references",
    "prompts",
    "cli_commands",
    "outputs",
    "qa_gates",
    "display_profile",
    "artifact_paths",
}


@dataclass
class Finding:
    severity: str
    path: Path
    message: str


def load_cli_subcommands() -> set[str]:
    cli_path = ROOT / "trading_core" / "cli.py"
    if not cli_path.exists():
        return set()
    text = cli_path.read_text(encoding="utf-8")
    return set(re.findall(r"add_parser\([\"']([^\"']+)[\"']", text))


def add(findings: list[Finding], severity: str, path: Path, message: str) -> None:
    findings.append(Finding(severity, path, message))


def require_list(recipe: dict[str, Any], path: Path, key: str, findings: list[Finding]) -> list[Any]:
    value = recipe.get(key)
    if not isinstance(value, list) or not value:
        add(findings, "ERROR", path, f"{key} must be a non-empty list")
        return []
    return value


def validate_cli_command(command: str, path: Path, subcommands: set[str], findings: list[Finding]) -> None:
    parts = command.split()
    if len(parts) >= 5 and parts[:4] == ["python3", "-m", "trading_core.cli", parts[3]]:
        subcommand = parts[3]
        if subcommand not in subcommands:
            add(findings, "ERROR", path, f"CLI subcommand does not exist: {subcommand}")
        return
    if len(parts) >= 2 and parts[0] == "python3" and parts[1].startswith("tools/"):
        tool_path = ROOT / parts[1]
        if not tool_path.exists():
            add(findings, "ERROR", path, f"tool path does not exist: {parts[1]}")
        return
    add(findings, "WARN", path, f"CLI command was not recognized for deep validation: {command}")


def validate_recipe(path: Path, subcommands: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    try:
        recipe = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding("ERROR", path, f"cannot load JSON: {exc}")]

    if not isinstance(recipe, dict):
        return [Finding("ERROR", path, "workflow recipe must be a JSON object")]

    missing = sorted(REQUIRED_FIELDS - set(recipe))
    if missing:
        add(findings, "ERROR", path, f"missing fields: {', '.join(missing)}")

    workflow_id = recipe.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id:
        add(findings, "ERROR", path, "workflow_id must be a non-empty string")
    elif path.stem != workflow_id:
        add(findings, "ERROR", path, f"filename must match workflow_id {workflow_id!r}")

    for key in ("intent_triggers", "required_inputs", "outputs", "artifact_paths"):
        require_list(recipe, path, key, findings)

    skills = require_list(recipe, path, "required_skills", findings)
    execution_order = require_list(recipe, path, "execution_order", findings)
    qa_gates = require_list(recipe, path, "qa_gates", findings)

    for skill in [*skills, *execution_order, *qa_gates]:
        if not isinstance(skill, str):
            add(findings, "ERROR", path, "skill references must be strings")
            continue
        if not (SKILLS_DIR / skill / "SKILL.md").exists():
            add(findings, "ERROR", path, f"missing skill: {skill}")

    if "financial-output-qa-gate" not in qa_gates:
        add(findings, "WARN", path, "workflow has no financial-output-qa-gate")

    for ref in require_list(recipe, path, "required_references", findings):
        if not isinstance(ref, str) or not (ROOT / ref).exists():
            add(findings, "ERROR", path, f"missing reference file: {ref}")

    for prompt in require_list(recipe, path, "prompts", findings):
        if not isinstance(prompt, str) or not (ROOT / prompt).exists():
            add(findings, "ERROR", path, f"missing prompt file: {prompt}")

    display_profile = recipe.get("display_profile")
    if display_profile not in DISPLAY_PROFILES:
        add(findings, "ERROR", path, f"display_profile must be one of {sorted(DISPLAY_PROFILES)}")

    for command in require_list(recipe, path, "cli_commands", findings):
        if isinstance(command, str):
            validate_cli_command(command, path, subcommands, findings)
        else:
            add(findings, "ERROR", path, "cli_commands entries must be strings")

    return findings


def main() -> int:
    findings: list[Finding] = []
    if not WORKFLOWS_DIR.is_dir():
        findings.append(Finding("ERROR", WORKFLOWS_DIR, "missing .agents/workflows directory"))
    else:
        paths = sorted(WORKFLOWS_DIR.glob("*.json"))
        found_ids = {path.stem for path in paths}
        for missing in sorted(EXPECTED_WORKFLOWS - found_ids):
            findings.append(Finding("ERROR", WORKFLOWS_DIR, f"missing expected workflow: {missing}"))
        subcommands = load_cli_subcommands()
        for path in paths:
            findings.extend(validate_recipe(path, subcommands))

    errors = [finding for finding in findings if finding.severity == "ERROR"]
    warnings = [finding for finding in findings if finding.severity == "WARN"]

    print("Workflow recipe validation")
    print(f"Root: {ROOT}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    for finding in findings:
        rel_path = finding.path.relative_to(ROOT) if finding.path.is_absolute() and finding.path.exists() else finding.path
        print(f"[{finding.severity}] {rel_path}: {finding.message}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
