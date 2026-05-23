#!/usr/bin/env python3
"""Validate project skill taxonomy coverage for key financial workflows."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path.cwd()
TAXONOMY_PATH = ROOT / ".agents" / "SKILL_TAXONOMY.md"
SKILLS_DIR = ROOT / ".agents" / "skills"
WORKFLOWS_DIR = ROOT / ".agents" / "workflows"
ALLOWED_TAGS = {
    "router",
    "market_overlay",
    "data_provider",
    "domain_workflow",
    "product_workflow",
    "qa_gate",
    "display",
    "artifact_tool",
    "authoring",
}
CRITICAL_SKILLS = {
    "financial-services-skill-router",
    "china-market-overlay",
    "ifind-http-api",
    "akshare",
    "a-share-equity-research-workflow",
    "a-share-research-product-workflow",
    "trading-decision-engine",
    "trade-journal-shadow-review",
    "financial-output-qa-gate",
}


@dataclass
class Finding:
    severity: str
    path: Path
    message: str


def code_spans(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def parse_pinned_skills(text: str) -> dict[str, set[str]]:
    pinned: dict[str, set[str]] = {}
    in_section = False
    for line in text.splitlines():
        if line.startswith("## Pinned Skills"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        stripped = line.strip()
        if not in_section or not stripped.startswith("|") or "---" in stripped or "Directory" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        spans = code_spans(cells[0])
        if not spans:
            continue
        skill = spans[0]
        tags = {span for span in code_spans(cells[1]) if span in ALLOWED_TAGS}
        pinned[skill] = tags
    return pinned


def workflow_skills() -> set[str]:
    skills: set[str] = set()
    for path in sorted(WORKFLOWS_DIR.glob("*.json")):
        try:
            recipe = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for key in ("required_skills", "execution_order", "qa_gates"):
            for skill in recipe.get(key, []):
                if isinstance(skill, str):
                    skills.add(skill)
    return skills


def main() -> int:
    findings: list[Finding] = []
    if not TAXONOMY_PATH.exists():
        findings.append(Finding("ERROR", TAXONOMY_PATH, "missing .agents/SKILL_TAXONOMY.md"))
        pinned: dict[str, set[str]] = {}
    else:
        text = TAXONOMY_PATH.read_text(encoding="utf-8")
        pinned = parse_pinned_skills(text)
        if not pinned:
            findings.append(Finding("ERROR", TAXONOMY_PATH, "no pinned skills found"))

    for skill in sorted(pinned):
        if not (SKILLS_DIR / skill / "SKILL.md").exists():
            findings.append(Finding("ERROR", TAXONOMY_PATH, f"pinned skill does not exist: {skill}"))
        if not pinned[skill]:
            findings.append(Finding("ERROR", TAXONOMY_PATH, f"pinned skill has no valid taxonomy tags: {skill}"))

    for skill in sorted(CRITICAL_SKILLS - set(pinned)):
        findings.append(Finding("ERROR", TAXONOMY_PATH, f"critical skill missing from taxonomy: {skill}"))

    for skill in sorted(workflow_skills() - set(pinned)):
        findings.append(Finding("WARN", TAXONOMY_PATH, f"workflow skill is not explicitly pinned: {skill}"))

    if "financial-output-qa-gate" in pinned and "qa_gate" not in pinned["financial-output-qa-gate"]:
        findings.append(Finding("ERROR", TAXONOMY_PATH, "financial-output-qa-gate must have qa_gate tag"))

    errors = [finding for finding in findings if finding.severity == "ERROR"]
    warnings = [finding for finding in findings if finding.severity == "WARN"]

    print("Skill taxonomy validation")
    print(f"Root: {ROOT}")
    print(f"Pinned skills: {len(pinned)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    for finding in findings:
        rel_path = finding.path.relative_to(ROOT) if finding.path.is_absolute() and finding.path.exists() else finding.path
        print(f"[{finding.severity}] {rel_path}: {finding.message}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
