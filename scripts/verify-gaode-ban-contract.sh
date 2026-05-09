#!/usr/bin/env bash
# Description: T3 contract verifier — validates every MCP tool in the catalog
#              gets a banned-role denial when fed a gaode-target string in its
#              path/url/code/filename field. Catches MCP enumeration drift.
# Usage: verify-gaode-ban-contract.sh
# Exit codes: 0=all PASS, 1=one or more FAIL, 2=harness invocation error
#
# Cycle-3 redev (spec-20260508-221237 M1 REVISION-2). Catalog at
# /root/travel-planner/scripts/lib/mcp-tool-catalog.json. When a new MCP server
# is added, the maintainer updates the catalog file; T3 then enforces every
# entry is wired through the gaode-policy field-whitelist scanner.

set -euo pipefail

PYTHON="${PYTHON:-python3}"
HOOK="${HOOK:-/root/.claude/hooks/pretool-tool-policy.py}"
CATALOG="${CATALOG:-/root/travel-planner/scripts/lib/mcp-tool-catalog.json}"
PROJECT="${CLAUDE_PROJECT_DIR:-/root/travel-planner}"

if [[ ! -f "$HOOK" ]]; then
  echo "Error: hook not found at $HOOK" >&2
  exit 2
fi
if [[ ! -f "$CATALOG" ]]; then
  echo "Error: catalog not found at $CATALOG" >&2
  exit 2
fi

export CLAUDE_PROJECT_DIR="$PROJECT"
export HOOK PYTHON CATALOG

"$PYTHON" - <<'PYEOF'
import base64
import json
import os
import subprocess
import sys

HOOK = os.environ["HOOK"]
PYTHON = os.environ["PYTHON"]
PROJECT = os.environ["CLAUDE_PROJECT_DIR"]
CATALOG = os.environ["CATALOG"]

G = base64.b64decode("Z2FvZGUtbWFwcw==").decode()  # "gaode-maps"
AMAP = base64.b64decode("YW1hcA==").decode()  # "amap"

SKILL_PATH = f"{PROJECT}/.claude/skills/{G}/skill.md"
AMAP_URL = f"https://restapi.{AMAP}.com/v3/place"


def make_payload(tool, field, kind):
    """Build a tool_input dict that exercises the (tool, field, kind) entry."""
    if kind == "direct":
        if field in ("filename",):
            return {field: SKILL_PATH}
        if field == "url":
            return {field: AMAP_URL}
        if field == "file_path":
            return {field: SKILL_PATH}
        return {field: SKILL_PATH}
    if kind == "url-substring":
        return {field: f"async () => {{ await fetch('{AMAP_URL}'); }}"}
    if kind == "list-item":
        return {field: [SKILL_PATH]}
    if kind == "gmail-body":
        return {"to": "x@y.z", "subject": "k", field: "AMAP_KEY=$AMAP_KEY"}
    raise ValueError(f"unknown kind: {kind}")


def run_hook(payload):
    env = {"PATH": "/usr/bin:/bin", "HOME": "/root", "CLAUDE_PROJECT_DIR": PROJECT}
    r = subprocess.run(
        [PYTHON, HOOK],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        timeout=10,
    )
    return r.returncode, r.stderr.strip()


def main():
    with open(CATALOG) as f:
        catalog = json.load(f)
    tools = catalog.get("tools", [])
    fails = 0
    for entry in tools:
        tool = entry["tool"]
        field = entry["field"]
        kind = entry["expected_match_kind"]
        expected_surface = entry["surface"]
        tool_input = make_payload(tool, field, kind)
        payload = {"tool_name": tool, "tool_input": tool_input, "subagent_type": "user"}
        code, stderr = run_hook(payload)
        if code != 2:
            fails += 1
            print(f"FAIL: {tool}.{field} ({kind}): expected exit=2 actual={code} stderr={stderr[:160]}")
            continue
        # Verify surface matches catalog entry.
        sj = None
        if stderr.startswith("BLOCKED by tool-policy.v1: "):
            try:
                sj = json.loads(stderr.split(": ", 1)[1].split("\n")[0])
            except (ValueError, IndexError):
                pass
        actual_surface = (sj or {}).get("surface")
        if actual_surface != expected_surface:
            fails += 1
            print(f"FAIL: {tool}.{field}: expected surface={expected_surface} actual={actual_surface}")
            continue
        print(f"PASS: {tool}.{field} ({kind}) -> surface={actual_surface}")
    total = len(tools)
    if fails:
        print(f"\nFAIL {fails}/{total}")
        sys.exit(1)
    print(f"\nPASS {total}/{total}")
    sys.exit(0)


main()
PYEOF
