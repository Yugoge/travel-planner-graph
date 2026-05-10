#!/usr/bin/env python3
"""Project-local gaode-maps allowlist enforcement.

Self-contained copy of gaode-related functions from
/root/.claude/hooks/lib/policy_registry.py. Read by
/root/travel-planner/.claude/hooks/pretool-gaode-policy.py.

Reads the project-local policy at
/root/travel-planner/.claude/policies/gaode-policy.json (resolved via
$CLAUDE_PROJECT_DIR when available, falling back to the absolute path
when run outside a Claude session).

Public API:
  is_gaode_allowed(role, surface, target) -> (bool, reason)
  normalize_gaode_agent_id(role) -> canonical role
  gaode_match_pattern(surface, target) -> matched pattern or None

Six matcher surfaces:
  skill              - Skill(skill="gaode-maps", ...)
  bash-token         - Bash command containing 'gaode-maps/' / 'amap_' etc.
  bash-resolved-path - Bash command with path token resolving under banned prefix
  network-host       - Bash/WebFetch/MCP URL with banned amap host
  env-var            - Bash command referencing AMAP_KEY etc.
  read-path          - Read/Glob/Grep/Edit file_path under banned prefix

Moved from global policy_registry.py per cycle-4 manual reorg
(spec-20260508-221237, 2026-05-09): the gaode harness is travel-planner-
specific and should not pollute the global hook lib.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import sys
from typing import Optional, Tuple


def _default_policy_path() -> str:
    project = os.environ.get("CLAUDE_PROJECT_DIR", "/root/travel-planner")
    return os.path.join(project, ".claude/policies/gaode-policy.json")


_CACHE: Optional[dict] = None
_CACHE_LOADED = False


def load_policy() -> Optional[dict]:
    global _CACHE, _CACHE_LOADED
    if _CACHE_LOADED:
        return _CACHE
    _CACHE_LOADED = True
    path = _default_policy_path()
    try:
        with open(path) as f:
            _CACHE = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"gaode_policy: load failed at {path} ({e})\n")
        _CACHE = None
    return _CACHE


def _reset_cache_for_tests() -> None:
    global _CACHE, _CACHE_LOADED
    _CACHE = None
    _CACHE_LOADED = False


# ----- Path normalization helpers (subset of policy_registry semantics) -----

def _project_dir() -> str:
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR", "/root"))


def _normalize_target(target: str) -> str:
    try:
        return os.path.realpath(target)
    except OSError:
        try:
            return os.path.abspath(target)
        except Exception:
            return target


def _candidate_targets(target: str) -> list:
    if not target:
        return []
    abs_t = os.path.abspath(target)
    canonical = _normalize_target(target)
    if abs_t != canonical:
        return [abs_t, canonical]
    return [abs_t]


def _path_is_prefix(prefix_path: str, target_path: str) -> bool:
    try:
        prefix_norm = os.path.normpath(prefix_path)
        target_norm = os.path.normpath(target_path)
    except (TypeError, ValueError):
        return False
    return (
        target_norm == prefix_norm
        or target_norm.startswith(prefix_norm.rstrip(os.sep) + os.sep)
    )


def _absolute_anchor_candidates(prefix: str) -> list:
    project = _project_dir()
    rel = prefix.lstrip("/")
    logical = os.path.abspath(os.path.join(project, rel))
    candidates = [logical]
    try:
        real = os.path.realpath(logical)
        if real != logical:
            candidates.append(real)
    except OSError:
        pass
    return candidates


def _absolute_anchor_match(prefix: str, target_canonical: str) -> bool:
    return any(
        _path_is_prefix(candidate, target_canonical)
        for candidate in _absolute_anchor_candidates(prefix)
    )


def _glob_match(prefix: str, target_canonical: str) -> bool:
    if prefix.endswith("*") or prefix.endswith("-") or prefix.endswith("/"):
        pattern = prefix if prefix.endswith("*") else prefix + "*"
    else:
        pattern = prefix
    return fnmatch.fnmatchcase(target_canonical, pattern)


def _prefix_matches(prefix: str, target_canonical: str) -> bool:
    if prefix == "*":
        return True
    if "*" in prefix:
        return _glob_match(prefix, target_canonical)
    if prefix.startswith("/"):
        return _absolute_anchor_match(prefix, target_canonical)
    return _absolute_anchor_match("/" + prefix, target_canonical)


def _prefix_matches_any_candidate(prefix: str, candidates: list) -> bool:
    for cand in candidates:
        if _prefix_matches(prefix, cand):
            return True
    return False


def _match_any_prefix(prefixes: list, candidates: list):
    for p in prefixes:
        if isinstance(p, str) and _prefix_matches_any_candidate(p, candidates):
            return p
    return None


# ----- Allowlist + alias canonicalization -----

def normalize_gaode_agent_id(role):
    """Canonicalize a role string via gaode_allowlist_aliases."""
    if role is None:
        return None
    policy = load_policy()
    if not policy:
        return role
    aliases = policy.get("gaode_allowlist_aliases", {}) or {}
    if not isinstance(aliases, dict) or role not in aliases:
        return role
    canonical = aliases[role]
    return canonical if isinstance(canonical, str) else role


def _gaode_allowlist() -> list:
    policy = load_policy() or {}
    allowlist = policy.get("gaode_allowlist_canonical_agent_ids", []) or []
    return [a for a in allowlist if isinstance(a, str)]


def _gaode_fail_closed() -> bool:
    policy = load_policy() or {}
    return bool(policy.get("gaode_fail_closed_on_unknown_agent", True))


# ----- Six matcher surfaces -----

def _skill_pref_match(skill_lower: str, p_lower: str) -> bool:
    if skill_lower == p_lower:
        return True
    return skill_lower.startswith(p_lower)


def _gaode_skill_match(skill):
    if not skill or not isinstance(skill, str):
        return None
    prefixes = (load_policy() or {}).get("gaode_denied_skill_prefixes", []) or []
    s_lower = skill.lower()
    for p in prefixes:
        if isinstance(p, str) and _skill_pref_match(s_lower, p.lower()):
            return p
    return None


def _gaode_bash_token_match(command):
    if not command or not isinstance(command, str):
        return None
    tokens = (load_policy() or {}).get("gaode_denied_bash_tokens", []) or []
    cmd_lower = command.lower()
    for t in tokens:
        if isinstance(t, str) and t.lower() in cmd_lower:
            return t
    return None


def _is_path_shaped(tok) -> bool:
    if not isinstance(tok, str) or tok.startswith("-"):
        return False
    return "/" in tok or tok.endswith(".sh") or tok.endswith(".py")


def _bash_path_tokens(command: str) -> list:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    return [tok for tok in tokens if _is_path_shaped(tok)]


def _resolve_token(tok: str) -> list:
    try:
        resolved = os.path.realpath(tok)
    except OSError:
        resolved = os.path.abspath(tok)
    return [resolved, os.path.abspath(tok)]


def _gaode_bash_path_match(command):
    if not command or not isinstance(command, str):
        return None
    prefixes = (load_policy() or {}).get("gaode_denied_bash_resolved_path_prefixes", []) or []
    if not prefixes:
        return None
    for tok in _bash_path_tokens(command):
        hit = _match_any_prefix(prefixes, _resolve_token(tok))
        if hit:
            return hit
    return None


def _gaode_host_glob_match(host_lower: str, text_lower: str) -> bool:
    base = host_lower.replace("*.", "").replace("*", "")
    return bool(base and base in text_lower)


def _gaode_substring_signal(text_lower: str):
    if "gaode" not in text_lower:
        return None
    if "://" in text_lower or "curl" in text_lower or "wget" in text_lower:
        return "substring:gaode"
    return None


def _host_match_one(h_lower: str, text_lower: str) -> bool:
    if "*" in h_lower:
        return _gaode_host_glob_match(h_lower, text_lower)
    return h_lower in text_lower


def _gaode_network_match(command_or_url):
    if not command_or_url or not isinstance(command_or_url, str):
        return None
    hosts = (load_policy() or {}).get("gaode_denied_network_hosts", []) or []
    text_lower = command_or_url.lower()
    for h in hosts:
        if isinstance(h, str) and _host_match_one(h.lower(), text_lower):
            return h
    return _gaode_substring_signal(text_lower)


def _env_var_regex(var: str) -> str:
    if var.endswith("*"):
        stem = var[:-1]
        return r"(?:\$\{?|\bexport\s+|\b)" + re.escape(stem) + r"[A-Z0-9_]*"
    return r"(?:\$\{?|\bexport\s+|\b)" + re.escape(var) + r"\b"


def _gaode_env_var_match(command):
    if not command or not isinstance(command, str):
        return None
    env_vars = (load_policy() or {}).get("gaode_denied_env_vars", []) or []
    for v in env_vars:
        if isinstance(v, str) and re.search(_env_var_regex(v), command):
            return v
    return None


def _gaode_read_path_match(target):
    if not target or not isinstance(target, str):
        return None
    prefixes = (load_policy() or {}).get("gaode_denied_read_path_prefixes", []) or []
    return _match_any_prefix(prefixes, _candidate_targets(target))


_GAODE_SURFACE_DISPATCH = {
    "skill": _gaode_skill_match,
    "bash-token": _gaode_bash_token_match,
    "bash-resolved-path": _gaode_bash_path_match,
    "network-host": _gaode_network_match,
    "env-var": _gaode_env_var_match,
    "read-path": _gaode_read_path_match,
}


def _gaode_decide_unknown(surface: str, matched_pattern: str) -> Tuple[bool, str]:
    if _gaode_fail_closed():
        return (
            False,
            f"gaode-policy: identity-default-deny on surface {surface} (matched {matched_pattern})",
        )
    return (True, "gaode-policy: identity-fail-open-disabled")


def _gaode_decide(matched_pattern: str, role, surface: str) -> Tuple[bool, str]:
    canonical_role = normalize_gaode_agent_id(role)
    allowlist = _gaode_allowlist()
    if not canonical_role:
        return _gaode_decide_unknown(surface, matched_pattern)
    if canonical_role in allowlist:
        return (True, f"gaode-policy: role {canonical_role} in allowlist")
    al = ", ".join(allowlist)
    return (
        False,
        f"gaode-policy: role {canonical_role} not in allowlist {{{al}}} on surface {surface} (matched {matched_pattern})",
    )


def is_gaode_allowed(role, surface: str, target) -> Tuple[bool, str]:
    """Return (allowed, reason) for a (role, surface, target) triple."""
    try:
        matcher = _GAODE_SURFACE_DISPATCH.get(surface)
        if matcher is None:
            return (True, "gaode-policy: unknown-surface")
        matched_pattern = matcher(target)
        if not matched_pattern:
            return (True, "gaode-policy: not-a-gaode-target")
        return _gaode_decide(matched_pattern, role, surface)
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"gaode_policy.is_gaode_allowed: unexpected ({e})\n")
        return (False, "gaode-policy: fail-closed-exception")


def gaode_match_pattern(surface: str, target):
    """Helper for the hook to retrieve the matched pattern for telemetry."""
    matcher = _GAODE_SURFACE_DISPATCH.get(surface)
    return None if matcher is None else matcher(target)
