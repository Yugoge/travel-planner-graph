#!/usr/bin/env python3
"""
MCP Client for Yelp Fusion AI MCP Server

Communicates with @yelp/yelp-mcp-server via JSON-RPC 2.0 over stdio.
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """Base MCP client for JSON-RPC 2.0 communication over stdio."""

    def __init__(self, package: str, env: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client.

        Args:
            package: NPM package name (e.g., '@yelp/yelp-mcp-server')
            env: Environment variables for MCP server
        """
        self.package = package
        self.env = env or {}
        self.process = None
        self.request_id = 0

    def __enter__(self):
        """Start MCP server process."""
        # Merge with current environment
        full_env = os.environ.copy()
        full_env.update(self.env)

        # Launch MCP server via npx
        self.process = subprocess.Popen(
            ['npx', '-y', self.package],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
            text=True,
            bufsize=1
        )

        # Initialize connection
        self._send_request('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {
                'name': 'yelp-mcp-client',
                'version': '1.0.0'
            }
        })

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Response data
        """
        if not self.process:
            raise RuntimeError("MCP server not started")

        self.request_id += 1
        request = {
            'jsonrpc': '2.0',
            'id': self.request_id,
            'method': method,
            'params': params
        }

        # Send request
        request_json = json.dumps(request) + '\n'
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")

        response = json.loads(response_line)

        # Check for errors
        if 'error' in response:
            error = response['error']
            raise RuntimeError(f"MCP error {error.get('code')}: {error.get('message')}")

        return response.get('result', {})

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools.

        Returns:
            List of tool definitions
        """
        result = self._send_request('tools/list', {})
        return result.get('tools', [])

    def call_tool(self, name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Any:
        """
        Call MCP tool with retry logic.

        Args:
            name: Tool name
            arguments: Tool arguments
            max_retries: Maximum retry attempts

        Returns:
            Tool result
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                result = self._send_request('tools/call', {
                    'name': name,
                    'arguments': arguments
                })

                # Extract content from result
                content = result.get('content', [])
                if content and len(content) > 0:
                    text = content[0].get('text', '')
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return text

                return result

            except Exception as e:
                last_error = e

                # Don't retry permanent errors
                if 'Unauthorized' in str(e) or 'Bad Request' in str(e):
                    raise

                # Exponential backoff for transient errors
                if attempt < max_retries:
                    delay = 2 ** (attempt - 1)
                    time.sleep(delay)
                    continue

                break

        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")


def format_error(error: Exception) -> str:
    """Format error message for user display."""
    error_str = str(error)

    if 'Unauthorized' in error_str or '401' in error_str:
        return "Error: Invalid API key. Check YELP_API_KEY environment variable."
    elif 'Too Many Requests' in error_str or '429' in error_str:
        return "Error: Rate limit exceeded. Please try again later."
    elif 'Bad Request' in error_str or '400' in error_str:
        return f"Error: Invalid request parameters. {error_str}"
    elif 'Not Found' in error_str or '404' in error_str:
        return "Error: Business not found."
    else:
        return f"Error: {error_str}"
