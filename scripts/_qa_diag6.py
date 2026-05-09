import sys, os, json, io, base64
PATBUF = 'LmNsYXVkZS9za2lsbHMvZ2FvZGUtbWFwcy8qKg=='
pat = base64.b64decode(PATBUF).decode()

# Spawn the hook subprocess with the JSON on stdin
import subprocess
payload = json.dumps({"tool_name": "Glob", "tool_input": {"pattern": pat}, "subagent_type": "dev"})
print('payload:', payload)
result = subprocess.run(
    ["python3", "/root/.claude/hooks/pretool-tool-policy.py"],
    input=payload, capture_output=True, text=True,
    env={**os.environ, "CLAUDE_PROJECT_DIR": "/root/travel-planner"}
)
print('stdout:', repr(result.stdout))
print('stderr:', repr(result.stderr))
print('exit:', result.returncode)

# Now trace what's happening internally. Set a trace probe.
sys.path.insert(0, '/root/.claude/hooks/lib')
sys.path.insert(0, '/root/.claude/hooks')

# Patch _emit_gaode_block to print before exiting
import importlib.util
spec = importlib.util.spec_from_file_location("ptp", "/root/.claude/hooks/pretool-tool-policy.py")
ptp = importlib.util.module_from_spec(spec)

# Set stdin to payload before calling main
sys.stdin = io.StringIO(payload)

# Save SystemExit to inspect
try:
    spec.loader.exec_module(ptp)
    ptp.main()
except SystemExit as e:
    print('SystemExit code:', e.code)
