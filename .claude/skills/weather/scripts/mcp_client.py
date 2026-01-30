#!/usr/bin/env python3
"""
Base MCP client for communicating with MCP servers via JSON-RPC 2.0 over stdio.

This module provides the MCPClient class that handles:
- Launching MCP server via npx
- JSON-RPC 2.0 protocol communication
- Tool listing and invocation
- Error handling with retries
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """Base client for MCP server communication via JSON-RPC 2.0 over stdio."""

    def __init__(self, package: str, env_vars: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client.

        Args:
            package: NPM package name (e.g., "@dangahagan/weather-mcp")
            env_vars: Environment variables to pass to MCP server
        """
        self.package = package
        self.env_vars = env_vars or {}
        self.process = None
        self.request_id = 0

    def _get_env(self) -> Dict[str, str]:
        """Get environment variables for MCP server process."""
        env = os.environ.copy()
        env.update(self.env_vars)
        return env

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Optional method parameters

        Returns:
            JSON-RPC response

        Raises:
            RuntimeError: If request fails
        """
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode('utf-8'))
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline().decode('utf-8')
        if not response_line:
            stderr_output = self.process.stderr.read().decode('utf-8')
            raise RuntimeError(f"No response from MCP server. stderr: {stderr_output}")

        response = json.loads(response_line)

        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"MCP error: {error.get('message', error)}")

        return response

    def connect(self) -> None:
        """Launch MCP server and initialize connection."""
        try:
            self.process = subprocess.Popen(
                ["npx", "-y", self.package],
                env=self._get_env(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )

            # Give server time to start
            time.sleep(2)

            # Initialize connection
            self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-client",
                    "version": "1.0.0"
                }
            })

        except Exception as e:
            if self.process:
                self.process.kill()
            raise RuntimeError(f"Failed to connect to MCP server: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], retries: int = 3) -> Any:
        """
        Call MCP tool with retry logic.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
            retries: Number of retry attempts for transient errors

        Returns:
            Tool result (parsed from response)

        Raises:
            RuntimeError: If tool call fails after all retries
        """
        last_error = None

        for attempt in range(retries):
            try:
                response = self._send_request("tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                })

                # Extract result from response
                result = response.get("result", {})
                content = result.get("content", [])

                if not content:
                    return result

                # Parse content based on type
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict):
                        if first_content.get("type") == "text":
                            text = first_content.get("text", "")
                            # Try to parse as JSON if possible
                            try:
                                return json.loads(text)
                            except json.JSONDecodeError:
                                return text
                        else:
                            return first_content

                return content

            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Tool call failed after {retries} attempts: {last_error}")

    def close(self) -> None:
        """Close connection and terminate MCP server process."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
                self.process.kill()
                self.process.wait(timeout=5)
            except Exception:
                pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def format_json_output(data: Any) -> str:
    """Format data as JSON for output."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def main():
    """Test MCP client connection and list available tools."""
    if len(sys.argv) < 2:
        print("Usage: python3 mcp_client.py <package> [env_var=value ...]")
        print("Example: python3 mcp_client.py @dangahagan/weather-mcp")
        sys.exit(1)

    package = sys.argv[1]
    env_vars = {}

    for arg in sys.argv[2:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            env_vars[key] = value

    try:
        with MCPClient(package, env_vars) as client:
            print(f"Connected to {package}")
            print("\nAvailable tools:")
            tools = client.list_tools()
            for tool in tools:
                print(f"  - {tool.get('name')}: {tool.get('description', 'No description')[:100]}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
