#!/usr/bin/env python3
"""Get images from a Xiaohongshu note URL."""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp_client import MCPClient, format_json_output


def get_note_images(url):
    """Get images from a Xiaohongshu note.
    
    Args:
        url: Xiaohongshu note URL
        
    Returns:
        dict: Note content with images
    """
    client = MCPClient("rednote-mcp", extra_args=["--stdio"])
    
    try:
        client.connect()
        
        # Get note content
        result = client.call_tool("get_note_content", {"url": url})
        
        # Parse result to extract images
        # If result is a dict with images, return them
        if isinstance(result, dict):
            return {
                "status": "success",
                "url": url,
                "data": result
            }
        
        # If result is text, try to parse it
        if isinstance(result, str):
            # Check if it's an error
            if "Timeout" in result or "Error" in result:
                return {
                    "status": "error",
                    "url": url,
                    "error": result
                }
            
            return {
                "status": "success",
                "url": url,
                "data": {"text": result}
            }
            
        return {
            "status": "error",
            "url": url,
            "error": "Unknown result format"
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
    parser = argparse.ArgumentParser(description='Get images from Xiaohongshu note')
    parser.add_argument('url', help='Xiaohongshu note URL')
    args = parser.parse_args()
    
    result = get_note_images(args.url)
    print(format_json_output(result))


if __name__ == "__main__":
    main()
