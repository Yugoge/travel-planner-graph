#!/usr/bin/env python3
"""
MCP client for 12306 Node.js based MCP server.

This client launches the Node.js MCP server via npx and communicates
using JSON-RPC 2.0 over stdio.
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """Client for 12306 MCP server (Node.js based)."""

    def __init__(self, server_path: str):
        """
        Initialize MCP client for Node.js server.

        Args:
            server_path: Path to the built MCP server (e.g., /tmp/12306-mcp/build/index.js)
        """
        self.server_path = server_path
        self.process = None
        self.request_id = 0

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
        """Launch MCP server via npx and initialize connection."""
        try:
            self.process = subprocess.Popen(
                ["npx", self.server_path],
                env=os.environ.copy(),
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
