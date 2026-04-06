#!/usr/bin/env python3
"""Validate schema references in agent definition files and plan.md.

Checks that all 6 agent .md files and plan.md contain schema validation
instructions with correct absolute paths, referenced schema files exist,
and Save to: lines are intact.
Request ID: dev-20260406-020003
Priority: high
Type: unit
"""
import argparse
import json
import sys
from pathlib import Path

AGENTS = ["meals", "accommodation", "attractions", "entertainment", "shopping", "transportation"]
VALIDATION_STRING = "Validate output against schema"


def read_file(path):
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def check_instruction_present(content, rel_path, violations):
    if VALIDATION_STRING not in content:
        violations.append({"file": rel_path, "issue": f"Missing validation instruction in {rel_path}", "severity": "major"})


def check_absolute_path(content, agent, rel_path, violations):
    expected = f"/root/travel-planner/schemas/{agent}.schema.json"
    if expected not in content:
        violations.append({"file": rel_path, "issue": f"Absolute path '{expected}' not found", "severity": "major"})


def check_agent_files(project_root, violations, total_checks):
    for agent in AGENTS:
        total_checks += 1
        rel_path = f".claude/agents/{agent}.md"
        content = read_file(project_root / rel_path)
        if content is None:
            violations.append({"file": rel_path, "issue": f"File missing: {rel_path}", "severity": "critical"})
            total_checks += 1
            continue
        check_instruction_present(content, rel_path, violations)
        total_checks += 1
        check_absolute_path(content, agent, rel_path, violations)
    return total_checks


def find_next_nonempty(lines, start):
    """Return text of first non-empty line after start, or empty string."""
    for j in range(start + 1, min(start + 5, len(lines))):
        stripped = lines[j].strip()
        if stripped:
            return stripped
    return ""


def check_save_follows_validation(lines, violations):
    for i, line in enumerate(lines):
        if VALIDATION_STRING not in line or "meals.schema.json" not in line:
            continue
        next_text = find_next_nonempty(lines, i)
        if next_text and "Save to:" not in next_text:
            violations.append({"file": "plan.md", "issue": f"Line after schema validation is not 'Save to:'. Found: '{next_text}'", "severity": "major"})


def check_plan_md(project_root, violations, total_checks):
    total_checks += 1
    content = read_file(project_root / ".claude/commands/plan.md")
    if content is None:
        violations.append({"file": "plan.md", "issue": "plan.md not found", "severity": "critical"})
        return total_checks
    if content.count(VALIDATION_STRING) < 1:
        violations.append({"file": "plan.md", "issue": "plan.md has 0 validation instructions", "severity": "major"})
    total_checks += 1
    check_save_follows_validation(content.splitlines(), violations)
    return total_checks


def check_schema_files_exist(project_root, violations, total_checks):
    for agent in AGENTS:
        total_checks += 1
        schema_path = project_root / "schemas" / f"{agent}.schema.json"
        if not schema_path.exists():
            violations.append({"file": str(schema_path), "issue": f"Schema file missing: {schema_path}", "severity": "critical"})
    return total_checks


def main():
    parser = argparse.ArgumentParser(description="Validate schema references in agent files")
    parser.add_argument("--project-root", required=True, help="Project root path")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    violations = []
    total_checks = 0

    total_checks = check_agent_files(project_root, violations, total_checks)
    total_checks = check_plan_md(project_root, violations, total_checks)
    total_checks = check_schema_files_exist(project_root, violations, total_checks)

    result = {
        "validator": "validate-schema-references",
        "status": "pass" if not violations else "fail",
        "violations": violations,
        "summary": {"total_checks": total_checks, "violations_found": len(violations)},
    }

    print(json.dumps(result, indent=2))
    sys.exit(0 if not violations else 1)


if __name__ == "__main__":
    main()
