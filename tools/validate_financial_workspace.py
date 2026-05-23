#!/usr/bin/env python3
"""Validate the financial-services Codex workspace layout."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path.cwd()
SKILLS_DIR = ROOT / ".agents" / "skills"
PROMPTS_DIR = ROOT / "prompts"
WORKFLOWS_DIR = ROOT / ".agents" / "workflows"
REFERENCES_DIR = ROOT / ".agents" / "references"

INCOMPATIBLE_PATTERNS = [
    ("Claude Code", re.compile(r"\bClaude Code\b", re.IGNORECASE)),
    ("slash command", re.compile(r"\bslash[- ]command\b", re.IGNORECASE)),
    ("managed agent", re.compile(r"\bmanaged[- ]agent\b", re.IGNORECASE)),
]


@dataclass
class Result:
    status: str
    check: str
    detail: str


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    if not text.startswith("---"):
        return {}, "missing opening frontmatter delimiter"

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "opening frontmatter delimiter must be on its own line"

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, "missing closing frontmatter delimiter"

    fields: dict[str, str] = {}
    fm_lines = lines[1:end_index]
    index = 0
    while index < len(fm_lines):
        line = fm_lines[index]
        if not line.strip() or line.startswith((" ", "\t")):
            index += 1
            continue
        if ":" not in line:
            return fields, f"invalid frontmatter line: {line!r}"

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            return fields, f"empty frontmatter key in line: {line!r}"

        if raw_value in {">", ">-", "|", "|-"}:
            block: list[str] = []
            index += 1
            while index < len(fm_lines):
                next_line = fm_lines[index]
                if next_line and not next_line.startswith((" ", "\t")) and ":" in next_line:
                    break
                block.append(next_line.strip())
                index += 1
            fields[key] = " ".join(part for part in block if part).strip()
            continue

        fields[key] = raw_value.strip("\"'")
        index += 1

    return fields, None


def add(results: list[Result], status: str, check: str, detail: str) -> None:
    results.append(Result(status=status, check=check, detail=detail))


def check_required_file(results: list[Result], path: Path, label: str) -> None:
    if path.exists():
        add(results, "PASS", label, f"found {path.relative_to(ROOT)}")
    else:
        add(results, "FAIL", label, f"missing {path.relative_to(ROOT)}")


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def main() -> int:
    results: list[Result] = []

    if (ROOT / ".git").is_dir():
        add(results, "PASS", "git root marker", "found .git")
    else:
        add(results, "FAIL", "git root marker", "missing .git")

    check_required_file(results, ROOT / "AGENTS.md", "AGENTS.md")
    check_required_file(results, ROOT / ".codex" / "config.toml", ".codex/config.toml")
    check_required_file(results, ROOT / ".agents" / "SKILLS_INDEX.md", ".agents/SKILLS_INDEX.md")
    check_required_file(results, ROOT / ".agents" / "SKILL_TAXONOMY.md", ".agents/SKILL_TAXONOMY.md")
    check_required_file(results, PROMPTS_DIR / "PROMPTS_INDEX.md", "prompts/PROMPTS_INDEX.md")
    check_required_file(
        results,
        SKILLS_DIR / "financial-services-skill-router" / "SKILL.md",
        "financial-services-skill-router",
    )
    check_required_file(
        results,
        SKILLS_DIR / "financial-output-qa-gate" / "SKILL.md",
        "financial-output-qa-gate",
    )
    for reference_name in (
        "output-contract.md",
        "data-capability-registry.md",
        "display-profiles.md",
        "local-research-artifacts.md",
        "watchlist-management.md",
    ):
        check_required_file(results, REFERENCES_DIR / reference_name, f".agents/references/{reference_name}")

    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if skill_files:
        add(results, "PASS", "skill count", f"found {len(skill_files)} .agents/skills/*/SKILL.md files")
    else:
        add(results, "FAIL", "skill count", "found 0 .agents/skills/*/SKILL.md files")

    for skill_file in skill_files:
        rel_path = skill_file.relative_to(ROOT)
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        fields, error = parse_frontmatter(text)
        if error:
            add(results, "FAIL", "skill frontmatter", f"{rel_path}: {error}")
            continue

        add(results, "PASS", "skill frontmatter", f"{rel_path}: valid frontmatter")

        for required in ("name", "description"):
            if fields.get(required, "").strip():
                add(results, "PASS", "required frontmatter fields", f"{rel_path}: has {required}")
            else:
                add(results, "FAIL", "required frontmatter fields", f"{rel_path}: missing {required}")

        description = fields.get("description", "").strip()
        if description and len(description) < 40:
            add(results, "WARN", "description length", f"{rel_path}: description is under 40 characters")

        for label, pattern in INCOMPATIBLE_PATTERNS:
            for match in pattern.finditer(text):
                add(
                    results,
                    "WARN",
                    "incompatible terms",
                    f"{rel_path}:{line_number(text, match.start())}: contains {label!r}",
                )

    prompt_files = sorted(PROMPTS_DIR.glob("*.md"))
    if prompt_files:
        add(results, "PASS", "prompts", f"found {len(prompt_files)} prompts/*.md files")
    else:
        add(results, "WARN", "prompts", "no prompts/*.md files found")

    workflow_files = sorted(WORKFLOWS_DIR.glob("*.json"))
    if len(workflow_files) >= 6:
        add(results, "PASS", "workflow recipes", f"found {len(workflow_files)} .agents/workflows/*.json files")
    else:
        add(results, "FAIL", "workflow recipes", f"found {len(workflow_files)} workflow recipes; expected at least 6")

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        counts[result.status] += 1

    print("Financial workspace validation")
    print(f"Root: {ROOT}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    print()

    for status in ("FAIL", "WARN", "PASS"):
        matching = [result for result in results if result.status == status]
        if not matching:
            continue
        print(f"{status}")
        for result in matching:
            print(f"- [{result.check}] {result.detail}")
        print()

    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
