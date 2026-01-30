#!/usr/bin/env python3
"""List all available tools from Gaode Maps MCP server."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import MCPClient
import json

def list_tools():
    """List all available MCP tools."""
    client = MCPClient(
        package="@amap/amap-maps-mcp-server",
        env={"AMAP_MAPS_API_KEY": os.environ.get("AMAP_MAPS_API_KEY", "99e97af6fd426ce3cfc45d22d26e78e3")}
    )

    try:
        client.initialize()

        # Request tools list
        request = {
            "jsonrpc": "2.0",
            "id": client.request_id,
            "method": "tools/list",
            "params": {}
        }
        client.request_id += 1

        client.process.stdin.write(json.dumps(request) + "\n")
        client.process.stdin.flush()

        # Read response
        response_line = client.process.stdout.readline().strip()
        response = json.loads(response_line)

        if "result" in response and "tools" in response["result"]:
            print("Available Gaode Maps MCP Tools:")
            print("=" * 80)
            for tool in response["result"]["tools"]:
                print(f"\nTool Name: {tool['name']}")
                if "description" in tool:
                    print(f"Description: {tool['description']}")
                if "inputSchema" in tool and "properties" in tool["inputSchema"]:
                    params = tool["inputSchema"]["properties"]
                    print(f"Parameters: {', '.join(params.keys())}")
                    for param_name, param_info in params.items():
                        param_type = param_info.get("type", "unknown")
                        param_desc = param_info.get("description", "")
                        required = " (required)" if param_name in tool["inputSchema"].get("required", []) else ""
                        print(f"  - {param_name} ({param_type}){required}: {param_desc}")
            print("\n" + "=" * 80)
            print(f"Total tools: {len(response['result']['tools'])}")
        else:
            print("Unexpected response:")
            print(json.dumps(response, indent=2))

    finally:
        client.close()

if __name__ == "__main__":
    list_tools()
