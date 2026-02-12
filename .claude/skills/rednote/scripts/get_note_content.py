#!/usr/bin/env python3
"""Get detailed content from a RedNote (小红书) note via HTTP scraping.

Fallback implementation due to MCP get_note_content timeout issues.
Uses simple HTTP request + regex to extract image URLs from note page.

Usage:
    Step 1: Search for notes to get note URL
    Step 2: Pass note URL to this script to extract images
    Step 3: Parse HTML to extract image CDN URLs

Example:
    python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123"
    python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123" --timeout 60

Exit codes:
    0 - Success (found images)
    1 - Error (network, timeout, parsing failure, or no images found)
"""
import sys
import json
import argparse
import re
from pathlib import Path


def get_note_content(url, timeout=45):
    """Get image URLs from a RedNote note via HTTP scraping.

    Root cause (commit afce9d9): search_notes only returns metadata text,
    not actual images. MCP get_note_content has timeout issues.

    Fallback approach: Fetch page HTML and extract image CDN URLs.

    Args:
        url: Note URL (e.g., "https://www.xiaohongshu.com/explore/abc123")
        timeout: Timeout in seconds (default: 45)

    Returns:
        dict: Note content with images, or error
            {
                "status": "success",
                "url": "...",
                "data": {"images": ["url1", "url2", ...]}
            }
    """
    import urllib.request
    import urllib.error

    try:
        # Fetch page HTML
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Extract image URLs from HTML using regex
        # Xiaohongshu CDN patterns: xhscdn.com, ci.xiaohongshu.com, picasso-static.xiaohongshu.com
        cdn_patterns = [
            r'(https?://[^"\s\']*?xhscdn\.com/[^"\s\']+)',
            r'(https?://[^"\s\']*?ci\.xiaohongshu\.com/[^"\s\']+)',
            r'(https?://[^"\s\']*?picasso-static\.xiaohongshu\.com/[^"\s\']+)',
        ]

        image_urls = []
        for pattern in cdn_patterns:
            matches = re.findall(pattern, html)
            image_urls.extend(matches)

        # Deduplicate and filter out thumbnails
        unique_urls = []
        seen = set()
        for url in image_urls:
            # Clean URL (remove trailing quotes, etc)
            url_clean = url.rstrip('\'"\\')
            if url_clean not in seen:
                # Filter thumbnails/avatars
                if not any(thumb in url_clean.lower() for thumb in ['thumbnail', 'thumb', 'avatar', 'user']):
                    unique_urls.append(url_clean)
                    seen.add(url_clean)

        if unique_urls:
            return {
                "status": "success",
                "url": url,
                "data": {"images": unique_urls}
            }
        else:
            return {
                "status": "error",
                "url": url,
                "error": "No images found in note"
            }

    except urllib.error.URLError as e:
        return {
            "status": "error",
            "url": url,
            "error": f"Network error: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description='Get images from RedNote note',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123"
  python3 get_note_content.py "https://www.xiaohongshu.com/explore/abc123" --timeout 30
        '''
    )
    parser.add_argument(
        'url',
        help='Note URL (e.g., "https://www.xiaohongshu.com/explore/abc123")'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Timeout in seconds (default: 30)'
    )

    args = parser.parse_args()

    result = get_note_content(args.url, args.timeout)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit with error code if fetch failed
    if result.get('status') == 'error':
        sys.exit(1)


if __name__ == '__main__':
    main()
