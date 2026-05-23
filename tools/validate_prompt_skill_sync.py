#!/usr/bin/env python3
"""Validate prompt index links to recipes, skills, CLI commands, and contracts."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path.cwd()
PROMPT_INDEX = ROOT / "prompts" / "PROMPTS_INDEX.md"
SKILLS_DIR = ROOT / ".agents" / "skills"
WORKFLOWS_DIR = ROOT / ".agents" / "workflows"
DISPLAY_PROFILES = {"app_card", "cli_markdown", "machine_json", "audit_appendix"}


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


def code_spans(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def parse_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) == 5 and cells[0] != "Prompt":
            rows.append(cells)
    return rows


def validate_cli(command: str, path: Path, subcommands: set[str], findings: list[Finding]) -> None:
    parts = command.split()
    if len(parts) >= 4 and parts[:3] == ["python3", "-m", "trading_core.cli"]:
        subcommand = parts[3]
        if subcommand not in subcommands:
            findings.append(Finding("ERROR", path, f"missing trading_core CLI subcommand: {subcommand}"))
        return
    if command.startswith("tools/"):
        if not (ROOT / command.split()[0]).exists():
            findings.append(Finding("ERROR", path, f"missing tool: {command}"))
        return
    if len(parts) >= 2 and parts[0] == "python3" and parts[1].startswith("tools/"):
        if not (ROOT / parts[1]).exists():
            findings.append(Finding("ERROR", path, f"missing tool: {parts[1]}"))
        return
    if command == "trading_core.renderers":
        if not (ROOT / "trading_core" / "renderers.py").exists():
            findings.append(Finding("ERROR", path, "missing trading_core/renderers.py"))
        return
    findings.append(Finding("WARN", path, f"unrecognized CLI/tooling reference: {command}"))


def workflow_prompts() -> set[str]:
    prompts: set[str] = set()
    for path in sorted(WORKFLOWS_DIR.glob("*.json")):
        try:
            recipe = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for prompt in recipe.get("prompts", []):
            if isinstance(prompt, str):
                prompts.add(prompt)
    return prompts


def main() -> int:
    findings: list[Finding] = []
    if not PROMPT_INDEX.exists():
        findings.append(Finding("ERROR", PROMPT_INDEX, "missing prompts/PROMPTS_INDEX.md"))
    else:
        text = PROMPT_INDEX.read_text(encoding="utf-8")
        rows = parse_table_rows(text)
        if not rows:
            findings.append(Finding("ERROR", PROMPT_INDEX, "prompt index table has no rows"))

        indexed_prompts: set[str] = set()
        subcommands = load_cli_subcommands()
        for prompt_cell, workflow_cell, skills_cell, cli_cell, display_cell in rows:
            for prompt in code_spans(prompt_cell):
                indexed_prompts.add(prompt)
                if prompt.startswith("prompts/") and not (ROOT / prompt).exists():
                    findings.append(Finding("ERROR", PROMPT_INDEX, f"missing prompt: {prompt}"))

            for workflow in code_spans(workflow_cell):
                if workflow.startswith(".agents/") and not (ROOT / workflow).exists():
                    findings.append(Finding("ERROR", PROMPT_INDEX, f"missing workflow recipe: {workflow}"))

            for skill in code_spans(skills_cell):
                if not (SKILLS_DIR / skill / "SKILL.md").exists():
                    findings.append(Finding("ERROR", PROMPT_INDEX, f"missing skill: {skill}"))

            for command in code_spans(cli_cell):
                validate_cli(command, PROMPT_INDEX, subcommands, findings)

            for item in code_spans(display_cell):
                if item in DISPLAY_PROFILES:
                    continue
                if item.startswith(".agents/") and not (ROOT / item).exists():
                    findings.append(Finding("ERROR", PROMPT_INDEX, f"missing display/contract reference: {item}"))

        for prompt in sorted(workflow_prompts() - indexed_prompts):
            findings.append(Finding("WARN", PROMPT_INDEX, f"workflow prompt not indexed: {prompt}"))

    errors = [finding for finding in findings if finding.severity == "ERROR"]
    warnings = [finding for finding in findings if finding.severity == "WARN"]

    print("Prompt/skill sync validation")
    print(f"Root: {ROOT}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    for finding in findings:
        rel_path = finding.path.relative_to(ROOT) if finding.path.is_absolute() and finding.path.exists() else finding.path
        print(f"[{finding.severity}] {rel_path}: {finding.message}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
