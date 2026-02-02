#!/usr/bin/env python3
"""
Check if budget overage exceeds thresholds requiring day-by-day review.
Usage: check-budget-overage.py <budget_json_path> [overage_threshold_eur] [overage_threshold_pct]
Exit codes:
  0 = acceptable (no review required)
  1 = review required (exceeds threshold)
  2 = error (file not found, invalid JSON, missing fields)

Examples:
  python3 check-budget-overage.py data/china-feb15/budget.json 200 20
  python3 check-budget-overage.py data/trip/budget.json
"""

import sys
import json
from pathlib import Path


def check_budget_overage(budget_path: str, threshold_eur: float = 200.0, threshold_pct: float = 20.0) -> int:
    """
    Check if budget overage exceeds thresholds.

    Args:
        budget_path: Path to budget.json file
        threshold_eur: Absolute overage threshold in EUR
        threshold_pct: Percentage overage threshold

    Returns:
        0 if acceptable, 1 if review required, 2 if error
    """
    budget_file = Path(budget_path)

    if not budget_file.exists():
        print(f"Error: Budget file not found: {budget_path}", file=sys.stderr)
        return 2

    try:
        with budget_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {budget_path}: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error reading {budget_path}: {e}", file=sys.stderr)
        return 2

    # Extract overage data
    overage_eur = None
    overage_pct = None

    # Check for overage_eur in various possible locations
    if 'overage_eur' in data:
        overage_eur = data['overage_eur']
    elif 'summary' in data and 'overage_eur' in data['summary']:
        overage_eur = data['summary']['overage_eur']
    elif 'data' in data and 'overage' in data['data']:
        overage_eur = data['data']['overage']

    # Check for overage_percentage
    if 'overage_percentage' in data:
        overage_pct = data['overage_percentage']
    elif 'summary' in data and 'overage_percentage' in data['summary']:
        overage_pct = data['summary']['overage_percentage']
    elif 'data' in data and 'overage_percentage' in data['data']:
        overage_pct = data['data']['overage_percentage']

    if overage_eur is None or overage_pct is None:
        print(f"Error: Missing overage_eur or overage_percentage in {budget_path}", file=sys.stderr)
        print("Expected fields: overage_eur, overage_percentage (at root or in summary object)", file=sys.stderr)
        return 2

    # Convert to float for comparison
    try:
        overage_eur = float(overage_eur)
        overage_pct = float(overage_pct)
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid overage values: {e}", file=sys.stderr)
        return 2

    # Check thresholds
    eur_exceeded = abs(overage_eur) > threshold_eur
    pct_exceeded = abs(overage_pct) > threshold_pct

    if eur_exceeded or pct_exceeded:
        print(f"⚠️  BUDGET REVIEW REQUIRED")
        print(f"   Overage: €{overage_eur:.2f} ({overage_pct:.1f}%)")
        print(f"   Thresholds: €{threshold_eur} or {threshold_pct}%")
        if eur_exceeded:
            print(f"   ✗ Absolute overage exceeds €{threshold_eur}")
        if pct_exceeded:
            print(f"   ✗ Percentage overage exceeds {threshold_pct}%")
        print()
        print("   Day-by-day review is REQUIRED to adjust itinerary.")
        return 1
    else:
        print(f"✓ Budget acceptable")
        print(f"  Overage: €{overage_eur:.2f} ({overage_pct:.1f}%)")
        print(f"  Within thresholds: €{threshold_eur} and {threshold_pct}%")
        return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    budget_path = sys.argv[1]
    threshold_eur = float(sys.argv[2]) if len(sys.argv) > 2 else 200.0
    threshold_pct = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0

    return check_budget_overage(budget_path, threshold_eur, threshold_pct)


if __name__ == '__main__':
    sys.exit(main())
