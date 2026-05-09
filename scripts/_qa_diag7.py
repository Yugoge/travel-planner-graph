import sys, os, base64
sys.path.insert(0, '/root/.claude/hooks/lib')
from policy_registry import is_gaode_allowed, _candidate_targets, load_policy

# What does the policy actually have for read-path prefixes?
p = load_policy()
print('gaode_denied_read_path_prefixes:', p.get('gaode_denied_read_path_prefixes'))

# Check the realpath of /root/.claude
import os
print('os.path.realpath("/root/.claude"):', os.path.realpath("/root/.claude"))
print('os.path.realpath("/root/.claude/skills"):', os.path.realpath("/root/.claude/skills"))

# Check that bonus claim 6 path
target = base64.b64decode('L3Jvb3QvLmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy9TS0lMTC5tZA==').decode()
print('target:', target)
print('candidates:', _candidate_targets(target))
allowed, reason = is_gaode_allowed("dev", "read-path", target)
print('allowed=', allowed, 'reason=', reason)

# What if we check with CLAUDE_PROJECT_DIR
os.environ['CLAUDE_PROJECT_DIR'] = '/root/travel-planner'
allowed2, reason2 = is_gaode_allowed("dev", "read-path", target)
print('with PROJECT_DIR allowed=', allowed2, 'reason=', reason2)
