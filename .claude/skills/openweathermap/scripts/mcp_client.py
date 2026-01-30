#!/usr/bin/env python3
"""
Base MCP Client for JSON-RPC 2.0 communication with MCP servers over stdio.
"""

import json
import subprocess
import sys
import time
from typing import Dict, List, Any, Optional


class MCPClient:
    """JSON-RPC 2.0 client for MCP server communication via stdio."""

    def __init__(self, package: str, env_vars: Optional[Dict[str, str]] = None, max_retries: int = 3):
        """
        Initialize MCP client.

        Args:
            package: NPM package name (e.g., '@openweathermap/openweathermap-mcp-server')
            env_vars: Environment variables for MCP server (e.g., {'OPENWEATHER_API_KEY': 'xxx'})
            max_retries: Maximum retry attempts for transient errors
        """
        self.package = package
        self.env_vars = env_vars or {}
        self.max_retries = max_retries
        self.process = None
        self.request_id = 0

    def _get_next_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self.request_id += 1
        return self.request_id

    def _start_server(self) -> subprocess.Popen:
        """
        Launch MCP server via npx.

        Returns:
            subprocess.Popen: Running MCP server process
        """
        import os
        env = os.environ.copy()
        env.update(self.env_vars)

        cmd = ['npx', '-y', self.package]

        process = subprocess.Popen(
            cmd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        return process

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to MCP server.

        Args:
            method: JSON-RPC method name (e.g., 'tools/call')
            params: Method parameters

        Returns:
            Dict containing response data

        Raises:
            Exception: If request fails after retries
        """
        request = {
            'jsonrpc': '2.0',
            'id': self._get_next_id(),
            'method': method,
            'params': params
        }

        for attempt in range(self.max_retries):
            try:
                if self.process is None or self.process.poll() is not None:
                    self.process = self._start_server()
                    time.sleep(0.5)  # Give server time to start

                # Send request
                request_json = json.dumps(request) + '\n'
                self.process.stdin.write(request_json)
                self.process.stdin.flush()

                # Read response
                response_line = self.process.stdout.readline()
                if not response_line:
                    raise Exception("No response from MCP server")

                response = json.loads(response_line.strip())

                # Check for errors
                if 'error' in response:
                    error = response['error']
                    raise Exception(f"MCP error: {error.get('message', 'Unknown error')}")

                return response

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s: {str(e)}",
                          file=sys.stderr)
                    time.sleep(wait_time)

                    # Restart server on failure
                    if self.process:
                        self.process.terminate()
                        self.process = None
                else:
                    raise Exception(f"Failed after {self.max_retries} attempts: {str(e)}")

        raise Exception("Failed to send request")

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize MCP connection.

        Returns:
            Server initialization response
        """
        params = {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {
                'name': 'openweathermap-client',
                'version': '1.0.0'
            }
        }

        return self._send_request('initialize', params)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        response = self._send_request('tools/list', {})
        return response.get('result', {}).get('tools', [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call MCP tool with arguments.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Parsed tool response
        """
        params = {
            'name': tool_name,
            'arguments': arguments
        }

        response = self._send_request('tools/call', params)

        # Parse result content
        result = response.get('result', {})
        content = result.get('content', [])

        if not content:
            return None

        # Return first content item text
        if isinstance(content, list) and len(content) > 0:
            return content[0].get('text', '')

        return str(content)

    def close(self):
        """Close MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
