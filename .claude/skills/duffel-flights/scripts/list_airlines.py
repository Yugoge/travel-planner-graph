#!/usr/bin/env python3
"""List airlines with optional filters."""
import sys
import os
import json
import argparse
import requests

def parse_args():
    parser = argparse.ArgumentParser(description="List airlines")
    parser.add_argument("--iata-code", help="Filter by IATA code (e.g., 'UA', 'BA')")
    parser.add_argument("--name", help="Filter by name (e.g., 'United')")
    parser.add_argument("--limit", type=int, default=50, help="Maximum results (default: 50)")
    return parser.parse_args()

def main():
    args = parse_args()

    # Get API key from environment
    api_key = os.environ.get("DUFFEL_API_KEY") or os.environ.get("DUFFEL_API_KEY_LIVE")
    if not api_key:
        print("Error: DUFFEL_API_KEY or DUFFEL_API_KEY_LIVE environment variable not set", file=sys.stderr)
        print("Set it with: export DUFFEL_API_KEY='your_api_key_here'", file=sys.stderr)
        sys.exit(1)

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Duffel-Version": "v2"
        }

        params = {"limit": args.limit}
        if args.iata_code:
            params["iata_code"] = args.iata_code.upper()
        if args.name:
            params["name"] = args.name

        response = requests.get(
            "https://api.duffel.com/air/airlines",
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        # Format results
        results = []
        for airline in data.get("data", []):
            results.append({
                "iata_code": airline.get("iata_code"),
                "name": airline.get("name"),
                "logo_url": airline.get("logo_symbol_url"),
                "id": airline.get("id")
            })

        print(json.dumps({"count": len(results), "airlines": results}, indent=2, ensure_ascii=False))

    except requests.exceptions.HTTPError as e:
        error_data = e.response.json() if e.response.text else {}
        print(json.dumps({
            "error": error_data.get("errors", [{}])[0].get("message", str(e)) if error_data.get("errors") else str(e),
            "type": "HTTPError",
            "status_code": e.response.status_code
        }, indent=2), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}, indent=2), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
