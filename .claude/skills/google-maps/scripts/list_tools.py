#!/usr/bin/env python3
"""List all available tools from Google Maps MCP server."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import MCPClient
import json

def list_tools():
    """List all available MCP tools."""
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set", file=sys.stderr)
        print("\nUsage:")
        print("  export GOOGLE_MAPS_API_KEY='your-api-key'")
        print("  python3 list_tools.py")
        sys.exit(1)

    client = MCPClient(
        package="@modelcontextprotocol/server-google-maps",
        env_vars={"GOOGLE_MAPS_API_KEY": api_key}
    )

    try:
        client.connect()

        # Request tools list using the client's built-in method
        response = client._send_request("tools/list")

        if "result" in response and "tools" in response["result"]:
            print("Available Google Maps MCP Tools:")
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

            # Output tool names for grep
            print("\nTool names only (for grep):")
            for tool in response["result"]["tools"]:
                print(tool['name'])
        else:
            print("Unexpected response:")
            print(json.dumps(response, indent=2))

    finally:
        client.close()

if __name__ == "__main__":
    list_tools()
