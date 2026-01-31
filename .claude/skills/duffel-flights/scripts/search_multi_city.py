#!/usr/bin/env python3
"""Search for multi-city flight itineraries using REST API."""
import sys
import os
import json
import argparse
import requests

def parse_args():
    parser = argparse.ArgumentParser(
        description="Search for multi-city flights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 3-city trip
  %(prog)s --segment JFK LAX 2026-03-01 \\
            --segment LAX SFO 2026-03-05 \\
            --segment SFO JFK 2026-03-10

  # European tour
  %(prog)s --segment LHR CDG 2026-04-15 \\
            --segment CDG FRA 2026-04-18 \\
            --segment FRA AMS 2026-04-22 \\
            --segment AMS LHR 2026-04-25 \\
            --cabin-class business
        """
    )
    parser.add_argument("--segment", action="append", nargs=3,
                        metavar=("ORIGIN", "DEST", "DATE"),
                        required=True,
                        help="Flight segment: ORIGIN DEST DATE (can be repeated)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adult passengers (default: 1)")
    parser.add_argument("--children", type=int, default=0, help="Number of children")
    parser.add_argument("--infants", type=int, default=0, help="Number of infants")
    parser.add_argument("--cabin-class", choices=["economy", "premium_economy", "business", "first"],
                        default="economy", help="Cabin class (default: economy)")
    parser.add_argument("--max-connections", type=int, default=2,
                        help="Maximum connections per segment (default: 2)")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of offers to return")
    return parser.parse_args()

def create_passengers(adults, children, infants):
    """Create passenger list."""
    passengers = []
    for _ in range(adults):
        passengers.append({"type": "adult"})
    for _ in range(children):
        passengers.append({"type": "child"})
    for _ in range(infants):
        passengers.append({"type": "infant_without_seat"})
    return passengers

def format_duration(iso_duration):
    """Convert ISO 8601 duration to human readable format."""
    if not iso_duration or not iso_duration.startswith("PT"):
        return iso_duration

    duration = iso_duration[2:]
    hours = minutes = 0

    if "H" in duration:
        h_parts = duration.split("H")
        hours = int(h_parts[0])
        duration = h_parts[1] if len(h_parts) > 1 else ""

    if "M" in duration:
        minutes = int(duration.replace("M", ""))

    return f"{hours}h {minutes}m"

def format_offer(offer):
    """Format offer for display."""
    result = {
        "offer_id": offer["id"],
        "price": {
            "amount": offer["total_amount"],
            "currency": offer["total_currency"]
        },
        "slices": []
    }

    for slice_data in offer["slices"]:
        slice_info = {
            "origin": slice_data["origin"]["iata_code"],
            "origin_name": slice_data["origin"]["name"],
            "destination": slice_data["destination"]["iata_code"],
            "destination_name": slice_data["destination"]["name"],
            "departure": slice_data["segments"][0]["departing_at"],
            "arrival": slice_data["segments"][-1]["arriving_at"],
            "duration": format_duration(slice_data.get("duration")),
            "stops": len(slice_data["segments"]) - 1,
            "segments": []
        }

        for segment in slice_data["segments"]:
            aircraft = segment.get("aircraft")
            slice_info["segments"].append({
                "carrier": segment["marketing_carrier"]["name"],
                "carrier_code": segment["marketing_carrier"]["iata_code"],
                "flight_number": segment.get("marketing_carrier_flight_number"),
                "aircraft": aircraft.get("name") if aircraft else None,
                "origin": segment["origin"]["iata_code"],
                "destination": segment["destination"]["iata_code"],
                "departure": segment["departing_at"],
                "arrival": segment["arriving_at"],
                "duration": format_duration(segment.get("duration"))
            })

        result["slices"].append(slice_info)

    return result

def main():
    args = parse_args()

    # Get API key from environment
    api_key = os.environ.get("DUFFEL_API_KEY") or os.environ.get("DUFFEL_API_KEY_LIVE")
    if not api_key:
        print("Error: DUFFEL_API_KEY or DUFFEL_API_KEY_LIVE environment variable not set", file=sys.stderr)
        print("Set it with: export DUFFEL_API_KEY='your_api_key_here'", file=sys.stderr)
        sys.exit(1)

    if len(args.segment) < 2:
        print("Error: At least 2 segments required for multi-city search", file=sys.stderr)
        sys.exit(1)

    try:
        # Create slices from segments
        slices = []
        for origin, destination, date in args.segment:
            slices.append({
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": date
            })

        # Create passengers
        passengers = create_passengers(args.adults, args.children, args.infants)

        # Display search info
        route = " → ".join([s["origin"] for s in slices] + [slices[-1]["destination"]])
        print(f"Searching multi-city itinerary: {route}", file=sys.stderr)
        print(f"Dates: {', '.join([s['departure_date'] for s in slices])}", file=sys.stderr)

        # Create request payload
        payload = {
            "data": {
                "slices": slices,
                "passengers": passengers,
                "cabin_class": args.cabin_class
            }
        }

        if args.max_connections is not None:
            payload["data"]["max_connections"] = args.max_connections

        # Make API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Duffel-Version": "v2"
        }

        response = requests.post(
            "https://api.duffel.com/air/offer_requests",
            json=payload,
            headers=headers,
            params={"return_offers": "true"},
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        # Format and display offers
        offers = data.get("data", {}).get("offers", [])[:args.max_results]

        if not offers:
            print(json.dumps({"error": "No flights found", "search_parameters": vars(args)}, indent=2))
            sys.exit(0)

        result = {
            "request_id": data.get("data", {}).get("id"),
            "route": route,
            "total_offers": len(data.get("data", {}).get("offers", [])),
            "displayed_offers": len(offers),
            "offers": [format_offer(offer) for offer in offers]
        }

        print(json.dumps(result, indent=2, ensure_ascii=False))

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
