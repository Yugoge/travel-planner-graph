#!/usr/bin/env python3
import json, os, subprocess, sys, time
from typing import Any, Dict, List, Optional

class MCPClient:
    def __init__(self, package: str, env_vars: Optional[Dict[str, str]] = None):
        self.package = package
        self.env_vars = env_vars or {}
        self.process = None
        self.request_id = 0

    def _get_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env.update(self.env_vars)
        return env

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.request_id += 1
        request = {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params or {}}
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode('utf-8'))
        self.process.stdin.flush()
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
        try:
            self.process = subprocess.Popen(
                ["npx", "-y", self.package],
                env=self._get_env(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            time.sleep(2)
            self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-client", "version": "1.0.0"}
            })
        except Exception as e:
            if self.process:
                self.process.kill()
            raise RuntimeError(f"Failed to connect to MCP server: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], retries: int = 3) -> Any:
        last_error = None
        for attempt in range(retries):
            try:
                response = self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
                result = response.get("result", {})
                content = result.get("content", [])
                if not content:
                    return result
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict):
                        if first_content.get("type") == "text":
                            text = first_content.get("text", "")
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
                    time.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"Tool call failed after {retries} attempts: {last_error}")

    def close(self) -> None:
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
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def format_json_output(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
