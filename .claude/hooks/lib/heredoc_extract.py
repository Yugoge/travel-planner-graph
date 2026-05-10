#!/usr/bin/env python3
"""Project-local heredoc-body extractor for the gaode hook.

Self-contained copy of extract_heredoc_bodies (and supporting parsers)
from the global lib/bash_write_targets.py. Used by pretool-gaode-policy.py
to scan tokens hidden inside `bash <<EOF ... EOF` payloads that the outer
parser would otherwise miss.

Moved here from /root/.claude/hooks/lib/bash_write_targets.py per cycle-4
manual reorg (spec-20260508-221237, 2026-05-09): the gaode harness is a
travel-planner-specific concern and should not depend on global hook lib.

Public API:
  extract_heredoc_bodies(command: str) -> list[str]
      Return heredoc PAYLOAD strings, one per heredoc opener.
"""

from __future__ import annotations

import re
from typing import List, Tuple

# Heredoc opener pattern. Captures three groups:
#   1: dash flag (- means tab-stripped form)
#   2: optional quote (' or ")
#   3: delimiter token
_HEREDOC_OPENER_RE = re.compile(r"<<(-?)\s*([\"'])?([A-Za-z_][A-Za-z0-9_]*)\2?")


def _detect_heredoc_opener(line: str) -> Tuple[bool, str, bool]:
    """Return (found, delimiter, dash_form) for the right-most opener."""
    matches = list(_HEREDOC_OPENER_RE.finditer(line))
    if not matches:
        return (False, "", False)
    m = matches[-1]
    return (True, m.group(3), m.group(1) == "-")


def _is_heredoc_closer(payload_line: str, delim: str, dash: bool) -> bool:
    stripped = payload_line.lstrip("\t") if dash else payload_line
    return stripped.strip() == delim


def _collect_heredoc_body(lines: List[str], start: int, delim: str, dash: bool):
    body: List[str] = []
    i = start
    while i < len(lines):
        if _is_heredoc_closer(lines[i], delim, dash):
            return (body, i + 1)
        body.append(lines[i])
        i += 1
    return (body, i)


def _walk_heredoc_bodies(lines: List[str]) -> List[str]:
    bodies: List[str] = []
    i = 0
    while i < len(lines):
        found, delim, dash = _detect_heredoc_opener(lines[i])
        if not found:
            i += 1
            continue
        body, next_i = _collect_heredoc_body(lines, i + 1, delim, dash)
        if body:
            bodies.append("\n".join(body))
        i = next_i
    return bodies


def extract_heredoc_bodies(command: str) -> List[str]:
    """Return heredoc PAYLOAD strings in a shell command (one per heredoc).

    >>> extract_heredoc_bodies('echo X')
    []
    >>> extract_heredoc_bodies('bash <<EOF\\npython3 /x/y/poi.py\\nEOF')
    ['python3 /x/y/poi.py']
    """
    if not isinstance(command, str) or "<<" not in command:
        return []
    return _walk_heredoc_bodies(command.split("\n"))


if __name__ == "__main__":
    import doctest
    failures, _ = doctest.testmod(verbose=True)
    raise SystemExit(0 if failures == 0 else 1)
