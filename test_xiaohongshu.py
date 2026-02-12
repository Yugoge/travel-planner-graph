#!/usr/bin/env python3
"""Test script for Xiaohongshu image extraction."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_xiaohongshu_search(search_name: str, city: str) -> Optional[str]:
    """Test Xiaohongshu image extraction (copied from fetch-images-batch.py)."""
    import re

    base_dir = Path(__file__).parent
    venv_python = str(base_dir / "venv/bin/python3")

    try:
        # Step 1: Search for notes to get note URLs
        search_script = base_dir / ".claude/skills/rednote/scripts/search.py"
        if not search_script.exists():
            logger.warning("Xiaohongshu skill not found at .claude/skills/rednote/scripts/search.py")
            return None

        # Search for "城市名 + POI名"
        query = f"{city} {search_name}" if city else search_name
        logger.debug(f"Xiaohongshu search: {query}")

        # Use xvfb-run for headless browser support
        xvfb_available = subprocess.run(["which", "xvfb-run"], capture_output=True).returncode == 0

        if xvfb_available:
            cmd = ["xvfb-run", "-a", venv_python, str(search_script), query, "--limit", "1"]
            env = os.environ.copy()
            env["DISPLAY"] = ":99"
        else:
            cmd = [venv_python, str(search_script), query, "--limit", "1"]
            env = os.environ.copy()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=search_script.parent,
            env=env
        )

        if result.returncode != 0:
            logger.debug(f"Xiaohongshu search failed for {query}")
            logger.debug(f"stderr: {result.stderr}")
            return None

        # Step 2: Extract note URL from search results
        search_data = json.loads(result.stdout)
        if search_data.get("status") != "success" or not search_data.get("data"):
            logger.debug(f"No Xiaohongshu results for {query}")
            return None

        text_data = search_data["data"]
        urls = re.findall(r'链接: (https://www\.xiaohongshu\.com/explore/[a-zA-Z0-9?=&_]+)', text_data)

        if not urls:
            logger.debug(f"No note URLs found in Xiaohongshu search results")
            return None

        note_url = urls[0]
        logger.debug(f"Found note URL: {note_url[:60]}...")

        # Step 3: Get detailed note content with images (increased timeout for browser automation)
        content_script = base_dir / ".claude/skills/rednote/scripts/get_note_content.py"
        if not content_script.exists():
            logger.warning("get_note_content.py not found at .claude/skills/rednote/scripts/")
            return None

        if xvfb_available:
            cmd = ["xvfb-run", "-a", venv_python, str(content_script), note_url, "--timeout", "60"]
            env = os.environ.copy()
            env["DISPLAY"] = ":99"
        else:
            cmd = [venv_python, str(content_script), note_url, "--timeout", "60"]
            env = os.environ.copy()

        # Increased timeout to 60s for get_note_content (browser automation is slow)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=content_script.parent,
            env=env
        )

        if result.returncode != 0:
            logger.warning(f"get_note_content failed for {note_url}")
            logger.debug(f"stderr: {result.stderr}")
            return None

        # Step 4: Parse content to extract image URLs
        content_data = json.loads(result.stdout)
        if content_data.get("status") != "success" or not content_data.get("data"):
            logger.warning(f"No content returned from get_note_content")
            return None

        content = content_data["data"]

        # Convert content to string for regex parsing (handle both text and JSON formats)
        if isinstance(content, dict):
            content_str = json.dumps(content)
        else:
            content_str = str(content)

        # Step 5: Extract image URLs from CDN patterns
        # Xiaohongshu CDN patterns: xhscdn.com, ci.xiaohongshu.com, picasso-static.xiaohongshu.com
        cdn_patterns = [
            r'(https?://[^"\s]*?xhscdn\.com/[^"\s]+)',
            r'(https?://[^"\s]*?ci\.xiaohongshu\.com/[^"\s]+)',
            r'(https?://[^"\s]*?picasso-static\.xiaohongshu\.com/[^"\s]+)',
        ]

        image_urls = []
        for pattern in cdn_patterns:
            matches = re.findall(pattern, content_str)
            image_urls.extend(matches)

        # Filter out thumbnails and get full-size images
        full_size_images = [
            url for url in image_urls
            if not any(thumb in url for thumb in ['thumbnail', 'thumb', 'avatar'])
        ]

        if full_size_images:
            image_url = full_size_images[0]
            logger.info(f"Extracted Xiaohongshu image: {image_url[:80]}...")
            return image_url

        logger.info(f"No images found in Xiaohongshu note content")
        return None

    except subprocess.TimeoutExpired:
        logger.warning(f"Xiaohongshu timeout for {search_name} (consider increasing timeout)")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"Xiaohongshu JSON parse error for {search_name}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Xiaohongshu error for {search_name}: {e}")
        return None


if __name__ == '__main__':
    print('='*60)
    print('Testing Xiaohongshu image extraction')
    print('='*60)
    print('POI: 洪崖洞')
    print('City: 重庆')
    print('='*60)

    result = test_xiaohongshu_search('洪崖洞', '重庆')

    print('='*60)
    if result:
        print(f'✓ SUCCESS: Extracted image URL')
        print(f'URL: {result}')
        sys.exit(0)
    else:
        print('✗ FAILED: No image URL extracted')
        sys.exit(1)
    print('='*60)
