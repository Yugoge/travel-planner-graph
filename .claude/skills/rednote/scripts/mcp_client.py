#!/usr/bin/env python3
"""
Base MCP Client for communicating with MCP servers via JSON-RPC 2.0 over stdio.

This module provides the core functionality for launching MCP servers via npx
and communicating with them using JSON-RPC 2.0 protocol over stdin/stdout.
"""

import json
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """Base client for MCP server communication via JSON-RPC 2.0 over stdio."""

    def __init__(self, package: str, env_vars: Optional[Dict[str, str]] = None, extra_args: Optional[List[str]] = None):
        """
        Initialize MCP client.

        Args:
            package: NPM package name (e.g., "@openbnb/mcp-server-airbnb", "rednote-mcp")
            env_vars: Optional environment variables for the MCP server
            extra_args: Extra command line arguments (e.g., ["--stdio"] for rednote-mcp)
        """
        self.package = package
        self.env_vars = env_vars or {}
        self.extra_args = extra_args or []
        self.process = None
        self.request_id = 0

    def _get_next_id(self) -> int:
        """Get next request ID for JSON-RPC."""
        self.request_id += 1
        return self.request_id

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            JSON-RPC response
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }

        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline().decode().strip()
        if not response_line:
            raise RuntimeError("No response from MCP server")

        response = json.loads(response_line)

        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"MCP Error: {error.get('message', str(error))}")

        return response

    def connect(self, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """
        Connect to MCP server by launching via npx.

        Args:
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retries in seconds
        """
        import os

        env = os.environ.copy()
        env.update(self.env_vars)

        for attempt in range(max_retries):
            try:
                cmd = ["npx", "-y", self.package] + self.extra_args
                self.process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=False
                )

                # Initialize connection
                self._send_request("initialize", {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "airbnb-skill",
                        "version": "1.0.0"
                    }
                })

                return

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"Failed to connect to MCP server after {max_retries} attempts: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Parsed tool result
        """
        response = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        result = response.get("result", {})
        content = result.get("content", [])

        if not content:
            return None

        # Parse first content item
        first_content = content[0]
        if first_content.get("type") == "text":
            text = first_content.get("text", "")
            # Try to parse as JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

        return first_content

    def close(self) -> None:
        """Close connection to MCP server."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None


def format_json_output(data: Any) -> str:
    """
    Format data as pretty-printed JSON.

    Args:
        data: Data to format

    Returns:
        Pretty-printed JSON string
    """
    return json.dumps(data, indent=2, ensure_ascii=False)
