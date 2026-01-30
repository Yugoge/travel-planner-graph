#!/usr/bin/env python3
"""Check NOAA and Open-Meteo service status."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output

with MCPClient("@dangahagan/weather-mcp") as client:
    result = client.call_tool("check_service_status", {})
    print(format_json_output(result))
