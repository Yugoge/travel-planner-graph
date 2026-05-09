import sys, os
sys.path.insert(0, '/root/.claude/hooks/lib')
from agent_resolver import resolve_agent_type
PATBUF = 'LmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qKg=='
import base64
pat = base64.b64decode(PATBUF).decode()
print('pattern:', pat)
data = {"tool_name": "Glob", "tool_input": {"pattern": pat}, "subagent_type": "dev"}
print('resolve_agent_type result:', repr(resolve_agent_type(data)))

# Also try without subagent_type
data2 = {"tool_name": "Glob", "tool_input": {"pattern": pat}}
print('resolve_agent_type (no subagent):', repr(resolve_agent_type(data2)))
