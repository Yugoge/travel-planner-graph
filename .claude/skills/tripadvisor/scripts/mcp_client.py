#!/usr/bin/env python3
"""
Base MCP client for communicating with TripAdvisor MCP server via JSON-RPC 2.0 over stdio.
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """Base class for MCP server communication via JSON-RPC 2.0."""

    def __init__(self, package: str, env_vars: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client.

        Args:
            package: NPM package name (e.g., "@tripadvisor/tripadvisor-mcp-server")
            env_vars: Environment variables to pass to MCP server
        """
        self.package = package
        self.env_vars = env_vars or {}
        self.process = None
        self.request_id = 0

    def _get_next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id

    def _start_server(self) -> subprocess.Popen:
        """
        Start MCP server via npx.

        Returns:
            subprocess.Popen object
        """
        # Prepare environment
        env = os.environ.copy()
        env.update(self.env_vars)

        # Launch MCP server
        cmd = ['npx', '-y', self.package]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1
        )

        return process

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to MCP server.

        Args:
            method: JSON-RPC method name (e.g., "tools/list", "tools/call")
            params: Method parameters

        Returns:
            Response dict

        Raises:
            RuntimeError: If communication fails
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }

        try:
            # Write request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                stderr = self.process.stderr.read()
                raise RuntimeError(f"No response from MCP server. stderr: {stderr}")

            response = json.loads(response_line)

            # Check for JSON-RPC error
            if "error" in response:
                error = response["error"]
                raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")

            return response

        except json.JSONDecodeError as e:
            stderr = self.process.stderr.read()
            raise RuntimeError(f"Invalid JSON response: {e}. stderr: {stderr}")
        except BrokenPipeError:
            stderr = self.process.stderr.read()
            raise RuntimeError(f"MCP server connection broken. stderr: {stderr}")

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize connection to MCP server.

        Returns:
            Server capabilities
        """
        self.process = self._start_server()

        # Send initialize request
        response = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "tripadvisor-skill",
                "version": "1.0.0"
            }
        })

        return response.get("result", {})

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Any:
        """
        Call a tool with retry logic.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed tool result

        Raises:
            RuntimeError: If all retries fail
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = self._send_request("tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                })

                # Parse result
                result = response.get("result", {})
                content = result.get("content", [])

                if not content:
                    return None

                # Extract text from first content item
                text_content = content[0].get("text", "")

                # Try to parse as JSON
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    return text_content

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** (attempt - 1)
                    print(f"Attempt {attempt} failed: {e}. Retrying in {wait_time}s...", file=sys.stderr)
                    time.sleep(wait_time)
                else:
                    print(f"All {max_retries} attempts failed.", file=sys.stderr)

        raise RuntimeError(f"Tool call failed after {max_retries} attempts: {last_error}")

    def close(self):
        """Close connection to MCP server."""
        if self.process:
            self.process.stdin.close()
            self.process.stdout.close()
            self.process.stderr.close()
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
