#!/usr/bin/env python3
"""Search RedNote (小红书) for travel content via MCP.

Uses rednote-mcp server to search for notes by keyword.
Requires: npm install -g rednote-mcp && rednote-mcp init
"""
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for mcp_client import
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient, format_json_output


def search_notes(keywords, limit=10):
    """Search RedNote notes by keyword.

    Args:
        keywords: Search keyword (Chinese recommended, e.g., "北京旅游")
        limit: Number of results to return (default: 10)

    Returns:
        dict: Search results with notes
    """
    client = MCPClient("rednote-mcp", extra_args=["--stdio"])

    try:
        # Connect to MCP server
        client.connect()

        # Call search_notes tool
        result = client.call_tool("search_notes", {
            "keywords": keywords,
            "limit": limit
        })

        return {
            "status": "success",
            "keywords": keywords,
            "limit": limit,
            "data": result
        }

    except Exception as e:
        return {
            "status": "error",
            "keywords": keywords,
            "error": str(e)
        }
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Search RedNote for travel content'
    )
    parser.add_argument(
        'keywords',
        help='Search keywords (Chinese recommended, e.g., "北京旅游")'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of results (default: 10)'
    )

    args = parser.parse_args()

    result = search_notes(args.keywords, args.limit)
    print(format_json_output(result))

    # Exit with error code if search failed
    if result.get('status') == 'error':
        sys.exit(1)


if __name__ == '__main__':
    main()
