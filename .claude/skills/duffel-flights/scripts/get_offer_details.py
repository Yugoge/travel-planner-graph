#!/usr/bin/env python3
"""Get detailed information about a specific flight offer using REST API."""
import sys
import os
import json
import argparse
import requests

def parse_args():
    parser = argparse.ArgumentParser(description="Get details for a specific flight offer")
    parser.add_argument("offer_id", help="Flight offer ID from search results")
    return parser.parse_args()

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

def format_offer_details(offer):
    """Format detailed offer information."""
    result = {
        "offer_id": offer["id"],
        "price": {
            "amount": offer["total_amount"],
            "currency": offer["total_currency"],
            "base_amount": offer.get("base_amount"),
            "tax_amount": offer.get("tax_amount")
        },
        "expires_at": offer.get("expires_at"),
        "live_mode": offer.get("live_mode"),
        "passengers": [],
        "slices": [],
        "conditions": {
            "refundable": offer.get("refundable_before_departure"),
            "changeable": offer.get("changeable_before_departure"),
            "passenger_identity_documents_required": offer.get("passenger_identity_documents_required")
        },
        "payment_requirements": offer.get("payment_requirements", {}),
        "supported_loyalty_programmes": offer.get("supported_loyalty_programmes", [])
    }

    # Add passenger information
    for passenger in offer.get("passengers", []):
        result["passengers"].append({
            "id": passenger["id"],
            "type": passenger.get("type"),
            "age": passenger.get("age")
        })

    # Add detailed slice information
    for slice_data in offer["slices"]:
        slice_info = {
            "origin": {
                "iata_code": slice_data["origin"]["iata_code"],
                "name": slice_data["origin"]["name"],
                "city_name": slice_data["origin"].get("city_name")
            },
            "destination": {
                "iata_code": slice_data["destination"]["iata_code"],
                "name": slice_data["destination"]["name"],
                "city_name": slice_data["destination"].get("city_name")
            },
            "departure": slice_data["segments"][0]["departing_at"],
            "arrival": slice_data["segments"][-1]["arriving_at"],
            "duration": format_duration(slice_data.get("duration")),
            "stops": len(slice_data["segments"]) - 1,
            "fare_brand_name": slice_data.get("fare_brand_name"),
            "segments": []
        }

        for segment in slice_data["segments"]:
            seg_info = {
                "carrier": {
                    "name": segment["marketing_carrier"]["name"],
                    "iata_code": segment["marketing_carrier"]["iata_code"],
                    "flight_number": segment.get("marketing_carrier_flight_number")
                },
                "operating_carrier": {
                    "name": segment.get("operating_carrier", {}).get("name"),
                    "iata_code": segment.get("operating_carrier", {}).get("iata_code")
                } if segment.get("operating_carrier") else None,
                "aircraft": segment.get("aircraft", {}).get("name"),
                "origin": {
                    "iata_code": segment["origin"]["iata_code"],
                    "terminal": segment.get("origin_terminal")
                },
                "destination": {
                    "iata_code": segment["destination"]["iata_code"],
                    "terminal": segment.get("destination_terminal")
                },
                "departure": segment["departing_at"],
                "arrival": segment["arriving_at"],
                "duration": format_duration(segment.get("duration")),
                "distance": segment.get("distance")
            }

            # Add baggage information if available
            if segment.get("passengers"):
                seg_info["baggage"] = []
                for pax in segment["passengers"]:
                    baggage_info = {"passenger_id": pax.get("passenger_id")}
                    if pax.get("baggages"):
                        baggage_info["allowances"] = [
                            {"type": bag.get("type"), "quantity": bag.get("quantity")}
                            for bag in pax["baggages"]
                        ]
                    seg_info["baggage"].append(baggage_info)

            slice_info["segments"].append(seg_info)

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

    try:
        # Make API request
        print(f"Fetching details for offer {args.offer_id}...", file=sys.stderr)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Duffel-Version": "v2"
        }

        response = requests.get(
            f"https://api.duffel.com/air/offers/{args.offer_id}",
            headers=headers,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        # Format and display
        offer = data.get("data", {})
        result = format_offer_details(offer)
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
