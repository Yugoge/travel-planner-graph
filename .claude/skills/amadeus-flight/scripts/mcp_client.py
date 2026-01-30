#!/usr/bin/env python3
"""
Base MCP Client for Amadeus Flight MCP Server

Communicates with @amadeus/flight-search-mcp-server via JSON-RPC 2.0 over stdio.
Launches MCP server using npx and exchanges JSON-RPC messages via stdin/stdout.
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


class MCPClient:
    """JSON-RPC 2.0 client for Amadeus Flight MCP server"""

    def __init__(self, package_name: str = "@amadeus/flight-search-mcp-server"):
        """
        Initialize MCP client

        Args:
            package_name: NPM package name for MCP server
        """
        self.package_name = package_name
        self.process = None
        self.request_id = 0

    def _get_env(self) -> Dict[str, str]:
        """
        Get environment variables for MCP server

        Returns:
            Environment dictionary with API credentials
        """
        env = os.environ.copy()

        # Ensure required environment variables are set
        required_vars = ['AMADEUS_API_KEY', 'AMADEUS_API_SECRET']
        missing_vars = [var for var in required_vars if not env.get(var)]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please set them in your environment or .env file"
            )

        return env

    def _start_server(self) -> subprocess.Popen:
        """
        Launch MCP server via npx

        Returns:
            Subprocess handle for MCP server
        """
        env = self._get_env()

        try:
            process = subprocess.Popen(
                ['npx', '-y', self.package_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1
            )

            # Give server time to initialize
            time.sleep(2)

            return process

        except FileNotFoundError:
            raise RuntimeError(
                "npx not found. Please install Node.js and npm:\n"
                "https://nodejs.org/"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}")

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to MCP server

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            JSON-RPC response
        """
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        # Send request
        request_json = json.dumps(request) + '\n'
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()

        if not response_line:
            stderr_output = self.process.stderr.read()
            raise RuntimeError(
                f"No response from MCP server. Server error:\n{stderr_output}"
            )

        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {response_line}\nError: {e}")

        # Check for JSON-RPC error
        if 'error' in response:
            error = response['error']
            raise RuntimeError(
                f"MCP server error: {error.get('message', 'Unknown error')}\n"
                f"Code: {error.get('code', 'N/A')}"
            )

        return response

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize connection to MCP server

        Returns:
            Server capabilities
        """
        if not self.process:
            self.process = self._start_server()

        response = self._send_request(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "amadeus-flight-client",
                    "version": "1.0.0"
                }
            }
        )

        return response.get('result', {})

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools

        Returns:
            List of tool definitions
        """
        response = self._send_request(method="tools/list")
        return response.get('result', {}).get('tools', [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool result (parsed from content)
        """
        response = self._send_request(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )

        result = response.get('result', {})
        content = result.get('content', [])

        if not content:
            return None

        # Extract text from first content item
        first_content = content[0]
        text = first_content.get('text', '')

        # Try to parse as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return raw text if not JSON
            return text

    def close(self):
        """Close connection to MCP server"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None


def retry_with_backoff(func, max_attempts: int = 3, initial_delay: float = 1.0):
    """
    Retry function with exponential backoff

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds

    Returns:
        Function result

    Raises:
        Last exception if all attempts fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                print(f"Attempt {attempt} failed: {e}", file=sys.stderr)
                print(f"Retrying in {delay}s...", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
            else:
                print(f"All {max_attempts} attempts failed", file=sys.stderr)

    raise last_exception


if __name__ == '__main__':
    # Test basic connectivity
    client = MCPClient()

    try:
        print("Initializing MCP client...")
        capabilities = client.initialize()
        print(f"Server capabilities: {json.dumps(capabilities, indent=2)}")

        print("\nListing available tools...")
        tools = client.list_tools()
        print(f"Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', 'No description')}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()
