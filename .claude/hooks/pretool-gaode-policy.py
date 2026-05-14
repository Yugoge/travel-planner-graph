#!/usr/bin/env python3
"""PreToolUse:* hook — project-local gaode-maps allowlist enforcement.

Standalone hook reading
/root/travel-planner/.claude/policies/gaode-policy.json via
lib.gaode_policy.is_gaode_allowed(). Independent of /root/.claude/hooks/*.

Behavior summary:
  Identity unresolved + gaode-target hit -> exit 2 (gaode-only fail-CLOSED).
  Resolved role + gaode-target hit -> allow only if role is in
    gaode_allowlist_canonical_agent_ids (timeline, transportation).
  Non-gaode tool calls -> exit 0 (global tool-policy hook still handles
    standard role-table checks like allowed_tools / write paths).

Six matcher surfaces (skill, bash-token, bash-resolved-path, network-host,
env-var, read-path) are dispatched via lib.gaode_policy.

Project-local move per cycle-4 manual reorg (spec-20260508-221237,
2026-05-09): gaode harness is travel-planner-specific. Reverted from
/root/.claude/hooks/pretool-tool-policy.py + lib/policy_registry.py.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.gaode_policy import (  # noqa: E402
    gaode_match_pattern,
    is_gaode_allowed,
)
from lib.heredoc_extract import extract_heredoc_bodies  # noqa: E402

GAODE_BASH_SURFACES = ("bash-token", "bash-resolved-path", "network-host", "env-var")
URL_RE = re.compile(r"https?://[^\s'\"`<>]+")

# (tool_name, field_name, surface) whitelist. Content fields
# (Edit.old_string, Write.content, MultiEdit.edits[].old_string,
# NotebookEdit.new_source) are intentionally absent.
GAODE_FIELD_WHITELIST = (
    ("Read", "file_path", "read-path"),
    ("Glob", "path", "read-path"),
    ("Glob", "pattern", "read-path"),
    ("Grep", "path", "read-path"),
    ("Grep", "glob", "read-path"),
    ("NotebookEdit", "notebook_path", "read-path"),
    ("Write", "file_path", "read-path"),
    ("Edit", "file_path", "read-path"),
    ("MultiEdit", "file_path", "read-path"),
    ("mcp__playwright__browser_take_screenshot", "filename", "read-path"),
    ("mcp__playwright__browser_snapshot", "filename", "read-path"),
    ("mcp__playwright__browser_console_messages", "filename", "read-path"),
    ("mcp__playwright__browser_network_requests", "filename", "read-path"),
    ("WebFetch", "url", "network-host"),
    ("mcp__playwright__browser_navigate", "url", "network-host"),
)

GAODE_URL_SUBSTRING_FIELDS = (
    ("mcp__playwright__browser_evaluate", "function"),
    ("mcp__playwright__browser_run_code", "code"),
)

GAODE_PATH_LIST_FIELDS = (
    ("mcp__playwright__browser_file_upload", "paths", "read-path"),
)

GAODE_GMAIL_FIELDS = ("body", "subject", "html", "text")


def _read_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _resolve_role(data: dict):
    sub = data.get("subagent_type")
    if isinstance(sub, str) and sub:
        return sub
    aid = data.get("agent_id")
    if isinstance(aid, str) and aid:
        return aid
    return None


def _emit_gaode_block(role, tool, surface: str, target, reason: str) -> None:
    matched = gaode_match_pattern(surface, target, tool_name=tool)
    payload = {
        "role": role,
        "tool": tool,
        "surface": surface,
        "matched_pattern": matched,
        "deny_reason": reason,
    }
    sys.stderr.write(
        f"BLOCKED by tool-policy.v1: {json.dumps(payload, separators=(',', ':'))}\n"
    )


def _check_gaode_one(role, tool_name: str, surface: str, target) -> None:
    if target is None or target == "":
        return
    allowed, reason = is_gaode_allowed(role, surface, target, tool_name=tool_name)
    if not allowed:
        _emit_gaode_block(role, tool_name, surface, target, reason)
        sys.exit(2)


def _scan_composed_glob_grep(role, tool_name: str, tool_input: dict) -> None:
    if tool_name == "Glob":
        p, pat = tool_input.get("path"), tool_input.get("pattern")
    elif tool_name == "Grep":
        p, pat = tool_input.get("path"), tool_input.get("glob")
    else:
        return
    if not isinstance(p, str) or not isinstance(pat, str) or not p or not pat:
        return
    stripped = pat.replace("**", "").replace("*", "")
    composed = os.path.realpath(os.path.join(p, stripped))
    _check_gaode_one(role, tool_name, "read-path", composed)


def _scan_field_whitelist(role, tool_name: str, tool_input: dict) -> None:
    for t_name, field, surface in GAODE_FIELD_WHITELIST:
        if t_name != tool_name:
            continue
        target = tool_input.get(field)
        if isinstance(target, str):
            _check_gaode_one(role, tool_name, surface, target)


def _scan_text_for_urls(role, tool_name: str, text) -> None:
    if not isinstance(text, str):
        return
    for url in URL_RE.findall(text):
        _check_gaode_one(role, tool_name, "network-host", url)


def _scan_url_substring_fields(role, tool_name: str, tool_input: dict) -> None:
    for t_name, field in GAODE_URL_SUBSTRING_FIELDS:
        if t_name == tool_name:
            _scan_text_for_urls(role, tool_name, tool_input.get(field))


def _scan_path_items(role, tool_name: str, surface: str, items) -> None:
    if not isinstance(items, list):
        return
    for item in items:
        if isinstance(item, str):
            _check_gaode_one(role, tool_name, surface, item)


def _scan_path_list_fields(role, tool_name: str, tool_input: dict) -> None:
    for t_name, field, surface in GAODE_PATH_LIST_FIELDS:
        if t_name == tool_name:
            _scan_path_items(role, tool_name, surface, tool_input.get(field))


def _scan_one_gmail_field(role, tool_name: str, text) -> None:
    if not isinstance(text, str):
        return
    _check_gaode_one(role, tool_name, "env-var", text)
    _scan_text_for_urls(role, tool_name, text)


def _scan_gmail_fields(role, tool_name: str, tool_input: dict) -> None:
    if tool_name != "mcp__claude_ai_Gmail__send":
        return
    for field in GAODE_GMAIL_FIELDS:
        _scan_one_gmail_field(role, tool_name, tool_input.get(field))


def _gaode_scan_tool_input(role, tool_name: str, tool_input: dict) -> None:
    if not isinstance(tool_input, dict):
        return
    _scan_field_whitelist(role, tool_name, tool_input)
    _scan_composed_glob_grep(role, tool_name, tool_input)
    _scan_url_substring_fields(role, tool_name, tool_input)
    _scan_path_list_fields(role, tool_name, tool_input)
    _scan_gmail_fields(role, tool_name, tool_input)


def _check_gaode_skill(role, tool_name: str, tool_input: dict) -> None:
    if tool_name != "Skill":
        return
    skill = tool_input.get("skill") or ""
    allowed, reason = is_gaode_allowed(role, "skill", skill)
    if not allowed:
        _emit_gaode_block(role, tool_name, "skill", skill, reason)
        sys.exit(2)


def _check_one_bash_string(role, command: str) -> None:
    if not command:
        return
    for surface in GAODE_BASH_SURFACES:
        allowed, reason = is_gaode_allowed(role, surface, command)
        if not allowed:
            _emit_gaode_block(role, "Bash", surface, command, reason)
            sys.exit(2)


def _check_gaode_bash(role, command: str) -> None:
    if not command:
        return
    _check_one_bash_string(role, command)
    for body in extract_heredoc_bodies(command):
        _check_one_bash_string(role, body)


def _gaode_pre_check(role, tool_name: str, tool_input: dict) -> None:
    _check_gaode_skill(role, tool_name, tool_input)
    if tool_name == "Bash":
        _check_gaode_bash(role, tool_input.get("command") or "")
    _gaode_scan_tool_input(role, tool_name, tool_input)


def main() -> None:
    data = _read_payload()
    if not data:
        sys.exit(0)
    tool_name = data.get("tool_name")
    if not isinstance(tool_name, str):
        sys.exit(0)
    tool_input = data.get("tool_input") or {}
    role = _resolve_role(data)
    _gaode_pre_check(role, tool_name, tool_input)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"pretool-gaode-policy: unexpected ({e})\n")
        sys.exit(0)
