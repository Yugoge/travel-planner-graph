#!/usr/bin/env python3
"""Get detailed content from a RedNote (小红书) note via MCP.

Uses rednote-mcp server to fetch detailed note content including images.
Requires: npm install -g rednote-mcp && rednote-mcp init

Usage:
    Step 1: Search for notes to get note URL
    Step 2: Pass note URL to this script to get detailed content with images
    Step 3: Extract image URLs from the returned content

Example:
    python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123"
    python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123" --timeout 60

Exit codes:
    0 - Success
    1 - Error (network, timeout, parsing failure)
"""
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for mcp_client import
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient, format_json_output


def get_note_content(url, timeout=45):
    """Get detailed content from a RedNote note.

    Root cause (commit afce9d9): search_notes only returns metadata text,
    not actual images. Need to call get_note_content to fetch full content.

    Args:
        url: Note URL (e.g., "https://www.xiaohongshu.com/explore/abc123")
        timeout: Timeout in seconds (default: 45, increased from default 30)

    Returns:
        dict: Note content with images, or error
            {
                "status": "success",
                "url": "...",
                "data": "note content text or JSON with images"
            }
    """
    client = MCPClient("rednote-mcp", extra_args=["--stdio"])

    try:
        # Connect to MCP server
        client.connect()

        # Call get_note_content tool with increased timeout
        # MCP server may need more time for browser automation
        result = client.call_tool("get_note_content", {
            "url": url
        })

        return {
            "status": "success",
            "url": url,
            "data": result
        }

    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "error": str(e)
        }
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Get detailed content from RedNote note',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123"
  python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123" --timeout 60
        '''
    )
    parser.add_argument(
        'url',
        help='Note URL (e.g., "https://www.xiaohongshu.com/explore/abc123")'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=45,
        help='Timeout in seconds (default: 45, increased from 30 due to MCP browser automation)'
    )

    args = parser.parse_args()

    result = get_note_content(args.url, args.timeout)
    print(format_json_output(result))

    # Exit with error code if fetch failed
    if result.get('status') == 'error':
        sys.exit(1)


if __name__ == '__main__':
    main()
