#!/usr/bin/env python3
"""Audit project-local Codex skills for frontmatter and portability."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SKILLS_DIR = Path(".agents/skills")

BANNED_PATTERNS = [
    ("Claude platform term", re.compile(r"\bClaude(?:\s+Code|\s+Desktop|\s+Cowork)?\b", re.I)),
    ("Anthropic platform term", re.compile(r"\bAnthropic\b", re.I)),
    ("slash command term", re.compile(r"\bslash[- ]commands?\b", re.I)),
    ("managed agent term", re.compile(r"\bmanaged[- ]agents?\b", re.I)),
    ("Claude home path", re.compile(r"/home/claude\b", re.I)),
    ("Claude plugin path", re.compile(r"\.claude(?:-plugin)?", re.I)),
    ("Claude Office MCP tool name", re.compile(r"\bmcp__office__", re.I)),
    ("CMA mode term", re.compile(r"\bCMA mode\b", re.I)),
]

GENERIC_DESCRIPTIONS = {
    "financial skill",
    "finance skill",
    "financial services skill",
    "use this skill for financial services",
    "guide for finance tasks",
    "helps with finance",
}

ACTIVATION_HINTS = ("use when", "triggers on", "triggered for", "trigger this", "when users")


@dataclass
class Finding:
    severity: str
    path: Path
    message: str


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    if not text.startswith("---"):
        return {}, "missing YAML frontmatter"

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "frontmatter must start with --- on its own line"

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, "frontmatter is missing closing ---"

    fields: dict[str, str] = {}
    fm_lines = lines[1:end_index]
    index = 0
    while index < len(fm_lines):
        line = fm_lines[index]
        if not line.strip() or line.startswith((" ", "\t")):
            index += 1
            continue
        if ":" not in line:
            index += 1
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

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


def is_probably_text(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\x00" in data[:2048]:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def audit_skill_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    fields, error = parse_frontmatter(text)
    if error:
        findings.append(Finding("ERROR", path, error))
        return findings

    for required in ("name", "description"):
        if not fields.get(required, "").strip():
            findings.append(Finding("ERROR", path, f"missing required frontmatter field: {required}"))

    description = fields.get("description", "").strip()
    normalized = re.sub(r"\s+", " ", description.lower()).strip()
    word_count = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'/-]*", description))

    if description:
        if len(description) < 100 or word_count < 14:
            findings.append(Finding("WARN", path, "description is too short to route reliably"))
        if normalized in GENERIC_DESCRIPTIONS:
            findings.append(Finding("WARN", path, "description is too generic"))
        if not any(hint in normalized for hint in ACTIVATION_HINTS):
            findings.append(Finding("WARN", path, "description does not include clear activation guidance"))

    return findings


def audit_banned_terms(skill_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(p for p in skill_dir.rglob("*") if p.is_file()):
        if not is_probably_text(path):
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BANNED_PATTERNS:
            for match in pattern.finditer(text):
                line_number = text.count("\n", 0, match.start()) + 1
                findings.append(Finding("WARN", path, f"{label} at line {line_number}: {match.group(0)!r}"))
    return findings


def run_audit(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    skills_dir = root / SKILLS_DIR
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))

    if not skill_files:
        return [Finding("ERROR", skills_dir, "no .agents/skills/*/SKILL.md files found")]

    for skill_file in skill_files:
        findings.extend(audit_skill_file(skill_file))
        findings.extend(audit_banned_terms(skill_file.parent))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Codex financial-services skills.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root to audit")
    args = parser.parse_args()

    root = args.root.resolve()
    findings = run_audit(root)
    skill_count = len(sorted((root / SKILLS_DIR).glob("*/SKILL.md")))
    errors = [finding for finding in findings if finding.severity == "ERROR"]
    warnings = [finding for finding in findings if finding.severity == "WARN"]

    print("Financial services skills audit")
    print(f"Root: {root}")
    print(f"Skill files: {skill_count}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    for finding in findings:
        rel_path = finding.path.relative_to(root) if finding.path.is_absolute() else finding.path
        print(f"[{finding.severity}] {rel_path}: {finding.message}")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
