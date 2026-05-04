#!/usr/bin/env python3
"""Lightweight RedNote search via MCP search_notes_light."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output


def search_notes_light(keywords):
    client = MCPClient("rednote-mcp", extra_args=["--stdio"])
    try:
        client.connect()
        data = client.call_tool("search_notes_light", {"keywords": keywords})
        return {"status": "success", "keywords": keywords, "data": data}
    except Exception as exc:
        return {"status": "error", "keywords": keywords, "error": str(exc)}
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description="Lightweight RedNote list-card search")
    parser.add_argument("keywords", help='Search keywords, e.g. "北京旅游"')
    result = search_notes_light(parser.parse_args().keywords)
    print(format_json_output(result))
    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
