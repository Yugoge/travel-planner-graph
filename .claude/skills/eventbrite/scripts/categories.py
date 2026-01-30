#!/usr/bin/env python3
"""Get Eventbrite categories."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output

try:
    with MCPClient("@mseep/eventbrite-mcp") as client:
        result = client.call_tool("get_categories", {})
        print(format_json_output(result))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
