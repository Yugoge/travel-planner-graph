#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from mcp_client import MCPClient

# Test getting note content
client = MCPClient("rednote-mcp", extra_args=["--stdio"])

try:
    client.connect()
    
    # Use the URL from previous search
    url = "https://www.xiaohongshu.com/explore/67cd7359000000002900e424"
    
    print(f"Fetching content for: {url}")
    result = client.call_tool("get_note_content", {"url": url})
    
    print("\nResult type:", type(result))
    print("\nResult:", result[:500] if isinstance(result, str) else result)
    
finally:
    client.close()
