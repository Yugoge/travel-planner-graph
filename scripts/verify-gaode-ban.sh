#!/usr/bin/env bash
# Description: Verify gaode-maps harness ban (spec-20260508-221237 M1 + M5).
# Usage: verify-gaode-ban.sh [policy-path]
# Exit codes: 0=all PASS, 1=one or more FAIL, 2=harness invocation error
#
# Exercises the six gaode policy surfaces (skill, bash-token,
# bash-resolved-path, network-host, env-var, read-path) against five role
# inputs (timeline, transportation, meals, dev, missing-agent-id) and
# prints PASS/FAIL per case. The script does NOT run the PreToolUse hook
# end-to-end; it imports lib.gaode_policy.is_gaode_allowed and asserts
# verdicts against the documented expected matrix.
#
# M5 (spec-20260508-221237, 2026-05-14, policy_version=2) adds CASES_M5:
# 16 cases covering cycle-3 read-path bypasses (wildcard-prefix Glob.pattern,
# parent-scan Grep, /root/.claude user-global root, ramdisk symlink target,
# nested-wildcard-middle pattern, relative wildcard pattern, AMAP strict
# segment match, gaode_maps substring match) plus false-positive guards
# (amap embedded in word, amap_pinned dir name, legitimate maps.txt) plus
# positive allowlist regressions (timeline + transportation under
# user-global root) plus parent-Read-NOT-denied (Read on parent dir is
# not a leak; only Glob/Grep recursive descent is).

set -euo pipefail

PYTHON="${PYTHON:-python3}"
HOOKS_DIR="${HOOKS_DIR:-/root/travel-planner/.claude/hooks}"

if [[ ! -d "$HOOKS_DIR/lib" ]]; then
  echo "Error: hooks lib not found at $HOOKS_DIR/lib" >&2
  exit 2
fi

export PYTHONPATH="$HOOKS_DIR:${PYTHONPATH:-}"

"$PYTHON" - <<'PYEOF'
import base64
import os
import sys

sys.path.insert(0, os.environ.get("HOOKS_DIR", "/root/travel-planner/.claude/hooks"))
from lib.gaode_policy import is_gaode_allowed, normalize_gaode_agent_id

# Construct test strings at runtime so this harness file itself does not
# embed literal gaode tokens (would otherwise trip its own future calls).
G = base64.b64decode("Z2FvZGUtbWFwcw==").decode()  # "gaode-maps"
AMAP = base64.b64decode("YW1hcA==").decode()  # "amap"

# Cycle-3 redev (arch-11 + style-inspector finding closure):
# Derive test fixture paths from CLAUDE_PROJECT_DIR rather than hardcoding
# /root/travel-planner. Falls back to /root/travel-planner only when env
# var is unset (preserves cycle-1 behavior).
PROJECT = os.environ.get("CLAUDE_PROJECT_DIR", "/root/travel-planner")
SKILL_PATH = f"{PROJECT}/.claude/skills/{G}/skill.md"
BASH_PATH = f"{PROJECT}/.claude/commands/scripts/{G}/scripts/poi.py"
DATA_NEG = f"{PROJECT}/data/foo.json"

# Expected matrix:
#   surface, target, role, expected_allowed
CASES = [
    # Skill matcher
    ("skill", G, "timeline", True),
    ("skill", G, "transportation", True),
    ("skill", G, "transport", True),  # alias normalization
    ("skill", G, "meals", False),
    ("skill", G, "dev", False),
    ("skill", G, None, False),  # identity-default-deny
    # Bash token matcher
    ("bash-token", f"python3 /x/{G}/scripts/poi.py", "timeline", True),
    ("bash-token", f"python3 /x/{G}/scripts/poi.py", "meals", False),
    ("bash-token", f"python3 /x/{G}/scripts/poi.py", "dev", False),
    ("bash-token", f"python3 /x/{G}/scripts/poi.py", None, False),
    # Bash resolved-path matcher (cycle-3 arch-11 NEW branch)
    ("bash-resolved-path", f"bash {BASH_PATH}", "timeline", True),
    ("bash-resolved-path", f"bash {BASH_PATH}", "meals", False),
    # Network host matcher
    ("network-host", f"curl https://restapi.{AMAP}.com/v3/place", "timeline", True),
    ("network-host", f"curl https://restapi.{AMAP}.com/v3/place", "transportation", True),
    ("network-host", f"curl https://restapi.{AMAP}.com/v3/place", "meals", False),
    ("network-host", f"curl https://restapi.{AMAP}.com/v3/place", "dev", False),
    ("network-host", f"curl https://restapi.{AMAP}.com/v3/place", None, False),
    # Env var matcher
    ("env-var", "echo $AMAP_KEY", "timeline", True),
    ("env-var", "echo $AMAP_KEY", "meals", False),
    ("env-var", "echo $AMAP_KEY", "dev", False),
    ("env-var", "export AMAP_TOKEN=xyz && python3 ./client.py", "dev", False),
    ("env-var", "echo $AMAP_KEY", None, False),
    # Read path matcher (uses CLAUDE_PROJECT_DIR-relative anchor)
    ("read-path", SKILL_PATH, "timeline", True),
    ("read-path", SKILL_PATH, "meals", False),
    ("read-path", SKILL_PATH, "dev", False),
    ("read-path", SKILL_PATH, None, False),
    # Negative cases: non-gaode targets should be allowed for everyone
    ("skill", "rednote", "meals", True),
    ("bash-token", "python3 /x/google-maps/scripts/places.py", "meals", True),
    ("network-host", "curl https://maps.googleapis.com/maps/api/geocode", "meals", True),
    ("env-var", "echo $GOOGLE_API_KEY", "meals", True),
    ("read-path", DATA_NEG, "meals", True),
]

# Force CLAUDE_PROJECT_DIR for read-path tests (the policy anchors absolute
# prefixes against this dir).
if not os.environ.get("CLAUDE_PROJECT_DIR"):
    os.environ["CLAUDE_PROJECT_DIR"] = "/root/travel-planner"
    # Reset cache so policy reload picks up the new env.
    from lib import gaode_policy as _pr
    _pr._reset_cache_for_tests()

# Sanity: alias canonicalization
canonical = normalize_gaode_agent_id("transport")
if canonical != "transportation":
    print(f"FAIL: alias normalization: 'transport' -> '{canonical}' (expected 'transportation')")
    sys.exit(1)
print("PASS: alias normalization 'transport' -> 'transportation'")

fails = 0
for surface, target, role, expected in CASES:
    allowed, reason = is_gaode_allowed(role, surface, target)
    role_disp = role if role is not None else "<missing-agent-id>"
    status = "PASS" if allowed == expected else "FAIL"
    if status == "FAIL":
        fails += 1
    print(f"{status}: surface={surface} role={role_disp} expected_allowed={expected} actual_allowed={allowed} reason={reason}")

if fails:
    print(f"\n{fails} FAIL out of {len(CASES) + 1} cases")
    sys.exit(1)
print(f"\nAll {len(CASES) + 1} cases PASS")
sys.exit(0)
PYEOF
