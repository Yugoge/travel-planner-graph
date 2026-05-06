#!/usr/bin/env python3
"""PreToolUse hook: write-time strict-schema + cross-ref enforcement.

Implements spec-20260506-092951 §5.1, §5.3, §5.7. Reads JSON hook payload
from stdin, simulates the post-edit content of the target file, runs
verify-plan-integrity.py --strict-schema --cross-ref against the simulated
content, and exits 2 on FAIL.

Fail-open: if verifier is missing or jsonschema unavailable, prints
"[validator-unavailable]" to stderr and exits 0 (per dev.md Defensive).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_BLOCK = 2

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '/root/travel-planner'))
VERIFIER = PROJECT_ROOT / 'scripts' / 'verify-plan-integrity.py'
DATA_PATH_RE = re.compile(r'^data/[^/]+/[^/]+\.json$')

DATA_AGENT_TYPES = {
    'meals', 'accommodation', 'transportation', 'attractions',
    'entertainment', 'shopping', 'cafe', 'timeline', 'budget',
}


def _read_payload():
    try:
        return json.load(sys.stdin)
    except Exception:
        return None


def _is_data_path(file_path: str) -> bool:
    try:
        rel = os.path.relpath(file_path, PROJECT_ROOT)
    except Exception:
        return False
    return bool(DATA_PATH_RE.match(rel))


def _agent_type():
    return os.environ.get('CLAUDE_AGENT_TYPE', '').strip()


def _bypass():
    return os.environ.get('BYPASS_DAY_GUARD', '') == '1'


def _block_raw_data_write(file_path, tool_name):
    """Spec §5.3: agents may not raw-Write/Edit data/**/*.json."""
    agent = _agent_type()
    if not agent or agent not in DATA_AGENT_TYPES:
        return False
    if _bypass():
        return False
    sys.stderr.write(
        f"BLOCKED: raw {tool_name} to data/**/*.json forbidden (spec 5.3).\n"
        f"  file: {file_path}\n"
        f"  agent: {agent}\n"
        "  Use: source venv/bin/activate && python scripts/save.py "
        "--trip <slug> --agent <agent> --input <json> --day N\n"
        "  Override (user only): set BYPASS_DAY_GUARD=1 (agents must NOT).\n"
    )
    return True


def _block_replace_all(tool_input):
    if tool_input.get('replace_all'):
        sys.stderr.write(
            "BLOCKED: Edit replace_all:true on data/**/*.json forbidden "
            "(spec 5.3). Use scripts/save.py --day N for per-day edits.\n"
        )
        return True
    return False


def _simulated_post_content(file_path, tool_name, tool_input):
    if tool_name == 'Write':
        return tool_input.get('content', '') or ''
    if tool_name != 'Edit':
        return None
    try:
        current = Path(file_path).read_text(encoding='utf-8')
    except Exception:
        return None
    old = tool_input.get('old_string', '')
    new = tool_input.get('new_string', '')
    if not old or old not in current:
        return current
    if tool_input.get('replace_all'):
        return current.replace(old, new)
    return current.replace(old, new, 1)


def _verifier_cmd(tempfile_path):
    return [
        sys.executable, str(VERIFIER),
        '--target-file', str(tempfile_path),
        '--strict-schema', '--cross-ref', '--cross-ref-warn-only',
    ]


def _exec_verifier(tempfile_path):
    if not VERIFIER.exists():
        sys.stderr.write(
            f"[validator-unavailable] verifier not at {VERIFIER}; skip.\n")
        return None
    try:
        return subprocess.run(
            _verifier_cmd(tempfile_path),
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        sys.stderr.write("[validator-unavailable] python not found; skip.\n")
        return None
    except subprocess.TimeoutExpired:
        sys.stderr.write("[validator-unavailable] verifier timeout; skip.\n")
        return None


def _emit_block(target_file, result):
    sys.stderr.write(f"BLOCKED: schema violation in {target_file}\n")
    if result.stdout:
        sys.stderr.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)


def _run_verifier(target_file, tempfile_path):
    result = _exec_verifier(tempfile_path)
    if result is None:
        return EXIT_OK
    if result.returncode != 0:
        _emit_block(target_file, result)
        return EXIT_BLOCK
    return EXIT_OK


def _write_tempfile(file_path, post_content):
    """Create a tempfile that PRESERVES the original stem so the verifier's
    AGENT_SCHEMA_MAP lookup (timeline / meals / ...) hits.

    Layout: data/<trip>/.precheck-<pid>/<original-name>
    """
    target_dir = Path(file_path).resolve().parent
    target_name = Path(file_path).name
    tmp_dir = target_dir / f'.precheck-{os.getpid()}'
    try:
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / target_name
        tmp_path.write_text(post_content, encoding='utf-8')
        return tmp_path
    except Exception as exc:
        sys.stderr.write(
            f"[validator-unavailable] tempfile write {target_dir}: {exc}; skip.\n")
        return None


def _validate_post_content(file_path, post_content):
    tmp_path = _write_tempfile(file_path, post_content)
    if tmp_path is None:
        return EXIT_OK
    try:
        return _run_verifier(file_path, tmp_path)
    finally:
        try:
            tmp_path.unlink()
            tmp_path.parent.rmdir()
        except Exception:
            pass


def _spec_5_3_blocks(file_path, tool_name, tool_input):
    if _block_replace_all(tool_input):
        return EXIT_BLOCK
    if _block_raw_data_write(file_path, tool_name):
        return EXIT_BLOCK
    return None


def main():
    payload = _read_payload()
    if not payload:
        return EXIT_OK
    tool_name = payload.get('tool_name', '')
    if tool_name not in ('Write', 'Edit'):
        return EXIT_OK
    tool_input = payload.get('tool_input', {}) or {}
    file_path = tool_input.get('file_path', '')
    if not file_path or not _is_data_path(file_path):
        return EXIT_OK
    blocked = _spec_5_3_blocks(file_path, tool_name, tool_input)
    if blocked is not None:
        return blocked
    # One-time migration bypass for M5 plan_label cleanup (spec 5.6).
    # Documented in docs/dev/specs/spec-20260506-092951.md §5.6 implementation
    # note: "add a temporary one-time bypass for the M5 cleanup write itself".
    if os.environ.get('DEV_MIGRATION_BYPASS', '') == 'spec-20260506-092951':
        sys.stderr.write(
            "[validator-bypass] DEV_MIGRATION_BYPASS=spec-20260506-092951 "
            "set; skipping schema check for this write.\n")
        return EXIT_OK
    post_content = _simulated_post_content(file_path, tool_name, tool_input)
    if post_content is None:
        return EXIT_OK
    return _validate_post_content(file_path, post_content)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        sys.stderr.write(f"[validator-unavailable] unexpected: {exc}; skip.\n")
        sys.exit(EXIT_OK)
