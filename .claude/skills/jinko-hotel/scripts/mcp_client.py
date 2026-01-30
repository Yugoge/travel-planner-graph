#!/usr/bin/env python3
"""
Base MCP client for JSON-RPC 2.0 communication over stdio.
Communicates with MCP servers via npx execution.
"""

import json
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """
    Base class for MCP server communication via JSON-RPC 2.0 over stdio.
    """

    def __init__(self, package: str, env_vars: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client.

        Args:
            package: NPM package name (e.g., '@jinko/hotel-booking-mcp-server')
            env_vars: Environment variables for MCP server (e.g., API keys)
        """
        self.package = package
        self.env_vars = env_vars or {}
        self.process = None
        self.request_id = 0

    def _get_next_id(self) -> int:
        """Get next request ID for JSON-RPC."""
        self.request_id += 1
        return self.request_id

    def _start_server(self) -> subprocess.Popen:
        """
        Start MCP server via npx.

        Returns:
            subprocess.Popen: MCP server process
        """
        import os

        env = os.environ.copy()
        env.update(self.env_vars)

        try:
            process = subprocess.Popen(
                ['npx', '-y', self.package],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1
            )
            return process
        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}")

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            JSON-RPC response

        Raises:
            RuntimeError: If communication fails
        """
        if not self.process:
            self.process = self._start_server()
            time.sleep(0.5)  # Give server time to start

        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("No response from MCP server")

            response = json.loads(response_line)

            # Check for JSON-RPC error
            if "error" in response:
                error = response["error"]
                raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")

            return response

        except Exception as e:
            self._cleanup()
            raise RuntimeError(f"MCP communication failed: {e}")

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize MCP connection.

        Returns:
            Server capabilities
        """
        response = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "jinko-hotel-client",
                "version": "1.0.0"
            }
        })
        return response.get("result", {})

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools.

        Returns:
            List of tool definitions
        """
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Any:
        """
        Call MCP tool with retry logic.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            max_retries: Maximum retry attempts

        Returns:
            Parsed tool result

        Raises:
            RuntimeError: If tool call fails after retries
        """
        for attempt in range(max_retries):
            try:
                response = self._send_request("tools/call", {
                    "name": tool_name,
                    "arguments": arguments
                })

                # Parse result
                result = response.get("result", {})
                content = result.get("content", [])

                if not content:
                    raise RuntimeError("Empty response from MCP tool")

                # Extract text content
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict):
                        text = first_content.get("text", "")
                        try:
                            # Try to parse as JSON
                            return json.loads(text)
                        except json.JSONDecodeError:
                            # Return as plain text
                            return text

                return content

            except RuntimeError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}", file=sys.stderr)
                    time.sleep(wait_time)
                    self._cleanup()  # Reset connection
                    continue
                raise

        raise RuntimeError(f"Tool call failed after {max_retries} attempts")

    def _cleanup(self):
        """Clean up MCP server process."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                pass
            finally:
                self.process = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup()

    def __del__(self):
        """Destructor."""
        self._cleanup()
