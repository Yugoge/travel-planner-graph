#!/usr/bin/env python3
"""Route optimization script for travel planner.

Reads GPS coordinates from agent outputs, calculates haversine distances,
detects inefficient routing patterns (A→B→A), and optimizes activity order
using greedy nearest-neighbor TSP approximation.

Usage:
    python optimize-route.py <destination-slug>

Exit codes:
    0: Optimization successful
    1: Missing coordinates (non-blocking, continues with available data)
    2: File read errors
"""

import sys
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates using haversine formula.

    Args:
        lat1, lon1: First point coordinates (decimal degrees)
        lat2, lon2: Second point coordinates (decimal degrees)

    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def extract_locations_for_day(day: int, agent_data: Dict) -> List[Dict]:
    """Extract all locations with coordinates for a specific day from agent output.

    Args:
        day: Day number (1-indexed)
        agent_data: Parsed JSON from agent file

    Returns:
        List of location dicts with name, coordinates, category
    """
    locations = []

    # Handle different agent JSON structures - check for data.days or days
    days_array = None
    if "data" in agent_data and "days" in agent_data["data"]:
        days_array = agent_data["data"]["days"]
    elif "days" in agent_data:
        days_array = agent_data["days"]

    if days_array:
        day_data = next((d for d in days_array if d.get("day") == day), None)
        if not day_data:
            return locations

        # Extract locations based on agent type
        for key in ["breakfast", "lunch", "dinner"]:
            if key in day_data and day_data[key]:
                item = day_data[key]
                if isinstance(item, dict) and "coordinates" in item:
                    coords = item["coordinates"]
                    if isinstance(coords, dict) and "latitude" in coords and "longitude" in coords:
                        locations.append({
                            "name": item.get("name", key.capitalize()),
                            "category": "meal",
                            "subcategory": key,
                            "coordinates": coords
                        })

        # Attractions, entertainment, shopping
        for category in ["attractions", "entertainment", "shopping"]:
            if category in day_data and isinstance(day_data[category], list):
                for item in day_data[category]:
                    if isinstance(item, dict) and "coordinates" in item:
                        coords = item["coordinates"]
                        if isinstance(coords, dict) and "latitude" in coords and "longitude" in coords:
                            locations.append({
                                "name": item.get("name", "Unknown"),
                                "category": category[:-1] if category != "shopping" else "shopping",
                                "coordinates": coords
                            })

    return locations


def calculate_distance_matrix(locations: List[Dict]) -> List[List[float]]:
    """Calculate distance matrix for all locations.

    Args:
        locations: List of location dicts with coordinates

    Returns:
        NxN distance matrix where matrix[i][j] is distance from location i to j
    """
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            coords_i = locations[i]["coordinates"]
            coords_j = locations[j]["coordinates"]

            dist = haversine_distance(
                coords_i["latitude"], coords_i["longitude"],
                coords_j["latitude"], coords_j["longitude"]
            )

            matrix[i][j] = dist
            matrix[j][i] = dist

    return matrix


def calculate_total_distance(order: List[int], distance_matrix: List[List[float]]) -> float:
    """Calculate total distance for a given visiting order.

    Args:
        order: List of location indices in visiting order
        distance_matrix: Distance matrix

    Returns:
        Total distance in kilometers
    """
    total = 0.0
    for i in range(len(order) - 1):
        total += distance_matrix[order[i]][order[i + 1]]
    return total


def greedy_nearest_neighbor_tsp(distance_matrix: List[List[float]], start_idx: int = 0) -> List[int]:
    """Optimize route using greedy nearest-neighbor TSP approximation.

    Args:
        distance_matrix: NxN distance matrix
        start_idx: Starting location index (usually accommodation)

    Returns:
        Optimized order as list of location indices
    """
    n = len(distance_matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]

    visited = [False] * n
    order = [start_idx]
    visited[start_idx] = True

    current = start_idx

    for _ in range(n - 1):
        nearest_dist = float('inf')
        nearest_idx = -1

        for j in range(n):
            if not visited[j] and distance_matrix[current][j] < nearest_dist:
                nearest_dist = distance_matrix[current][j]
                nearest_idx = j

        if nearest_idx == -1:
            break

        order.append(nearest_idx)
        visited[nearest_idx] = True
        current = nearest_idx

    return order


def detect_aba_pattern(order: List[int], locations: List[Dict], distance_matrix: List[List[float]], threshold_km: float = 1.0) -> List[str]:
    """Detect A→B→A inefficiency patterns.

    Args:
        order: Current visiting order (indices)
        locations: Location data
        distance_matrix: Distance matrix
        threshold_km: Distance threshold to consider locations as "same area"

    Returns:
        List of warning strings describing inefficiencies
    """
    warnings = []
    n = len(order)

    for i in range(n - 2):
        for j in range(i + 2, n):
            # Check if location at order[j] is close to location at order[i]
            if distance_matrix[order[i]][order[j]] < threshold_km:
                # Check if intermediate locations are far from this area
                max_intermediate_dist = 0.0
                for k in range(i + 1, j):
                    dist_to_i = distance_matrix[order[i]][order[k]]
                    dist_to_j = distance_matrix[order[j]][order[k]]
                    max_intermediate_dist = max(max_intermediate_dist, min(dist_to_i, dist_to_j))

                if max_intermediate_dist > threshold_km * 2:
                    loc_i_name = locations[order[i]]["name"]
                    loc_j_name = locations[order[j]]["name"]
                    warnings.append(
                        f"A→B→A pattern detected: Visit {loc_i_name}, then travel far away, then return to nearby {loc_j_name} "
                        f"({distance_matrix[order[i]][order[j]]:.1f}km apart)"
                    )

    return warnings


def optimize_day(day_number: int, day_date: str, location_name: str, data_dir: Path) -> Optional[Dict]:
    """Optimize route for a single day.

    Args:
        day_number: Day number (1-indexed)
        day_date: Date string
        location_name: City/location name
        data_dir: Path to data directory

    Returns:
        Optimization result dict or None if no locations with coordinates
    """
    # Read agent outputs
    agent_files = ["meals.json", "attractions.json", "entertainment.json", "shopping.json"]
    all_locations = []

    for agent_file in agent_files:
        file_path = data_dir / agent_file
        if not file_path.exists():
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
                locations = extract_locations_for_day(day_number, agent_data)
                all_locations.extend(locations)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to read {agent_file}: {e}", file=sys.stderr)

    if len(all_locations) < 2:
        return {
            "day": day_number,
            "date": day_date,
            "location": location_name,
            "optimized_order": [],
            "distance_comparison": {
                "original_km": 0.0,
                "optimized_km": 0.0,
                "savings_km": 0.0,
                "savings_percent": 0.0
            },
            "warnings": [f"Insufficient locations with GPS coordinates for optimization (found {len(all_locations)})"]
        }

    # Calculate distance matrix
    distance_matrix = calculate_distance_matrix(all_locations)

    # Original order distance
    original_order = list(range(len(all_locations)))
    original_distance = calculate_total_distance(original_order, distance_matrix)

    # Optimize using greedy TSP
    optimized_order = greedy_nearest_neighbor_tsp(distance_matrix, start_idx=0)
    optimized_distance = calculate_total_distance(optimized_order, distance_matrix)

    # Detect A→B→A patterns in original order
    aba_warnings = detect_aba_pattern(original_order, all_locations, distance_matrix)

    # Calculate savings
    savings_km = original_distance - optimized_distance
    savings_percent = (savings_km / original_distance * 100) if original_distance > 0 else 0.0

    # Build result
    warnings = []
    if savings_km > 0.5:  # Threshold for meaningful savings
        warnings.append(f"Route optimization reduced travel distance by {savings_km:.1f}km ({savings_percent:.1f}%)")
    warnings.extend(aba_warnings)

    return {
        "day": day_number,
        "date": day_date,
        "location": location_name,
        "optimized_order": [all_locations[i]["name"] for i in optimized_order],
        "distance_comparison": {
            "original_km": round(original_distance, 2),
            "optimized_km": round(optimized_distance, 2),
            "savings_km": round(savings_km, 2),
            "savings_percent": round(savings_percent, 1)
        },
        "warnings": warnings if warnings else ["No significant optimization opportunities found"]
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python optimize-route.py <destination-slug>", file=sys.stderr)
        sys.exit(2)

    destination_slug = sys.argv[1]
    data_dir = Path(__file__).parent.parent / "data" / destination_slug

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        sys.exit(2)

    # Read plan skeleton to get days
    plan_skeleton_path = data_dir / "plan-skeleton.json"
    if not plan_skeleton_path.exists():
        print(f"Error: plan-skeleton.json not found: {plan_skeleton_path}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(plan_skeleton_path, 'r', encoding='utf-8') as f:
            plan_skeleton = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Failed to read plan-skeleton.json: {e}", file=sys.stderr)
        sys.exit(2)

    if "days" not in plan_skeleton or not isinstance(plan_skeleton["days"], list):
        print("Error: Invalid plan-skeleton.json structure", file=sys.stderr)
        sys.exit(2)

    # Optimize each day
    results = []
    missing_coordinates_count = 0

    for day_data in plan_skeleton["days"]:
        day_number = day_data.get("day")
        day_date = day_data.get("date", "")
        location_name = day_data.get("location", "")

        if not day_number:
            continue

        result = optimize_day(day_number, day_date, location_name, data_dir)
        if result:
            results.append(result)
            if "Insufficient locations" in result["warnings"][0]:
                missing_coordinates_count += 1

    # Write output
    output_data = {
        "agent": "route-optimizer",
        "status": "complete",
        "note": "Route optimization using haversine distance and greedy nearest-neighbor TSP approximation",
        "days": results
    }

    output_path = data_dir / "route-optimization.json"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error: Failed to write route-optimization.json: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"Route optimization complete: {output_path}")
    print(f"Optimized {len(results)} days")

    if missing_coordinates_count > 0:
        print(f"Warning: {missing_coordinates_count} days had insufficient GPS coordinates", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
