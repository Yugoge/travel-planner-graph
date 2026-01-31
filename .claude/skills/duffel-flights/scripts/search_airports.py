#!/usr/bin/env python3
"""Search for airports by name or location."""
import sys
import os
import json
import argparse
import requests

# API configuration
DUFFEL_API_BASE = os.environ.get("DUFFEL_API_BASE_URL", "https://api.duffel.com")

def parse_args():
    parser = argparse.ArgumentParser(description="Search for airports")
    parser.add_argument("query", help="Search query (e.g., 'London', 'JFK')")
    parser.add_argument("--limit", type=int, default=20, help="Maximum results (default: 20)")
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

        params = {
            "query": args.query,
            "limit": args.limit
        }

        response = requests.get(
            "https://api.duffel.com/places/suggestions",
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        # Format results
        results = []
        for place in data.get("data", []):
            if place.get("type") == "airport":
                results.append({
                    "iata_code": place.get("iata_code"),
                    "icao_code": place.get("icao_code"),
                    "name": place.get("name"),
                    "city": place.get("city_name"),
                    "country": place.get("iata_country_code"),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                    "time_zone": place.get("time_zone")
                })

        print(json.dumps({"query": args.query, "count": len(results), "airports": results}, indent=2, ensure_ascii=False))

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
