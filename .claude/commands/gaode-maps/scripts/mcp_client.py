#!/usr/bin/env python3
"""
Base MCP client for communicating with MCP servers via JSON-RPC 2.0 over stdio.

This module provides the MCPClient class that handles:
- Launching MCP servers via npx
- JSON-RPC 2.0 protocol communication over stdin/stdout
- Tool discovery and invocation
- Error handling with retry logic
"""

import json
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """Base client for MCP server communication via JSON-RPC 2.0."""

    def __init__(self, package: str, env: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client.

        Args:
            package: NPM package name (e.g., "@amap/amap-maps-mcp-server")
            env: Environment variables (e.g., {"AMAP_MAPS_API_KEY": "key"})
        """
        self.package = package
        self.env = env or {}
        self.process = None
        self.request_id = 0

    def _get_next_id(self) -> int:
        """Get next request ID for JSON-RPC."""
        self.request_id += 1
        return self.request_id

    def _launch_server(self) -> subprocess.Popen:
        """
        Launch MCP server via npx.

        Returns:
            subprocess.Popen: Server process

        Raises:
            RuntimeError: If server fails to launch
        """
        import os

        # Merge environment variables
        full_env = os.environ.copy()
        full_env.update(self.env)

        try:
            process = subprocess.Popen(
                ['npx', '-y', self.package],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env,
                text=True,
                bufsize=1
            )
            return process
        except Exception as e:
            raise RuntimeError(f"Failed to launch MCP server: {e}")

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Dict containing response data

        Raises:
            RuntimeError: If request fails
        """
        if not self.process:
            self.process = self._launch_server()

        request_id = self._get_next_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        try:
            # Send request
            request_json = json.dumps(request) + '\n'
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                stderr_output = self.process.stderr.read()
                raise RuntimeError(f"No response from MCP server. Stderr: {stderr_output}")

            response = json.loads(response_line)

            # Check for JSON-RPC error
            if "error" in response:
                error = response["error"]
                raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")

            return response

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}")

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize connection with MCP server.

        Returns:
            Dict containing server capabilities
        """
        response = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "gaode-maps-client",
                "version": "1.0.0"
            }
        })

        # Send initialized notification
        self._send_request("notifications/initialized", {})

        return response.get("result", {})

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        response = self._send_request("tools/list", {})
        return response.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Any:
        """
        Call an MCP tool with retry logic.

        Args:
            name: Tool name
            arguments: Tool arguments
            max_retries: Maximum retry attempts

        Returns:
            Tool result (parsed from response)

        Raises:
            RuntimeError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self._send_request("tools/call", {
                    "name": name,
                    "arguments": arguments
                })

                result = response.get("result", {})
                content = result.get("content", [])

                if not content:
                    raise RuntimeError("Empty response from tool")

                # Extract text from first content item
                if isinstance(content[0], dict):
                    return content[0].get("text", "")

                return str(content[0])

            except RuntimeError as e:
                last_error = e
                error_msg = str(e).lower()

                # Don't retry on permanent errors
                if any(code in error_msg for code in ['401', '403', '400', '404', 'invalid']):
                    raise

                # Retry on transient errors
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue

        raise RuntimeError(f"Tool call failed after {max_retries} retries: {last_error}")

    def close(self):
        """Clean up resources and terminate server process."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            finally:
                self.process = None


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response from MCP tool.

    Args:
        response: Raw response string

    Returns:
        Parsed JSON object
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Response might be plain text
        return {"text": response}


def format_output(data: Any, pretty: bool = True) -> str:
    """
    Format output data as JSON.

    Args:
        data: Data to format
        pretty: Whether to pretty-print JSON

    Returns:
        Formatted JSON string
    """
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return json.dumps(data, ensure_ascii=False)
