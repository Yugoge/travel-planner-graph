#!/usr/bin/env python3
import sys
import json
sys.path.insert(0, '.')
from mcp_client import MCPClient

# Test raw search response
client = MCPClient("rednote-mcp", extra_args=["--stdio"])

try:
    client.connect()
    
    # Call search_notes and get raw response
    response = client._send_request("tools/call", {
        "name": "search_notes",
        "arguments": {
            "keywords": "重庆洪崖洞",
            "limit": 1
        }
    })
    
    print("Raw response:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
finally:
    client.close()
