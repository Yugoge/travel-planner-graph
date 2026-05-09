#!/bin/bash
# Diagnose what abspath gives for the bare pattern.
PATBUF='Ly5jbGF1ZGUvc2tpbGxzL2dhb2RlLW1hcHMvKio='
PAT=$(echo "$PATBUF" | base64 -d)

echo "=== Direct python trace ==="
python3 <<PYEOF
import sys
sys.path.insert(0, '/root/.claude/hooks/lib')
import os
print('cwd:', os.getcwd())
target = "$PAT"
print('target:', target)
print('abspath:', os.path.abspath(target))
print('realpath:', os.path.realpath(target))
from policy_registry import _candidate_targets, is_gaode_allowed
print('candidates:', _candidate_targets(target))
allowed, reason = is_gaode_allowed("dev", "read-path", target)
print('allowed=', allowed, 'reason=', reason)
PYEOF

echo ""
echo "=== Now with cwd=/root/travel-planner ==="
cd /root/travel-planner
python3 <<PYEOF
import sys
sys.path.insert(0, '/root/.claude/hooks/lib')
import os
print('cwd:', os.getcwd())
target = "$PAT"
print('target:', target)
print('abspath:', os.path.abspath(target))
print('realpath:', os.path.realpath(target))
from policy_registry import _candidate_targets, is_gaode_allowed
print('candidates:', _candidate_targets(target))
allowed, reason = is_gaode_allowed("dev", "read-path", target)
print('allowed=', allowed, 'reason=', reason)
PYEOF

echo ""
echo "=== Now check denied prefixes ==="
python3 -c "
import sys; sys.path.insert(0,'/root/.claude/hooks/lib')
from policy_registry import load_policy
p = load_policy()
print('gaode_denied_read_path_prefixes:', p.get('gaode_denied_read_path_prefixes'))
"
