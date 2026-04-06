#!/usr/bin/env python3
"""
Check if budget overage exceeds thresholds requiring day-by-day review.
Usage: check-budget-overage.py <budget_json_path> [overage_threshold] [overage_threshold_pct]
Exit codes:
  0 = acceptable (no review required)
  1 = review required (exceeds threshold)
  2 = error (file not found, invalid JSON, missing fields)

Examples:
  python scripts/check-budget-overage.py data/china-feb15/budget.json 200 20
  python scripts/check-budget-overage.py data/trip/budget.json

Supported currencies: EUR, CNY
Accepted fields: overage_eur, overage_cny, overage (absolute); overage_percentage, overage_percent (relative)
Accepted paths: root, summary, data, data.trip_summary, data.days[0].budget_vs_user
"""

import sys
import json
from pathlib import Path

# Maps currency code to field names and symbol.
# Root cause: script was EUR-only; CNY plan field names added in budget agent ~commit cb6cc4d
CURRENCY_FIELDS = {
    'EUR': {
        'absolute': ['overage_eur', 'overage'],
        'percentage': ['overage_percentage', 'overage_percent'],
        'symbol': '€',
    },
    'CNY': {
        'absolute': ['overage_cny', 'overage'],
        'percentage': ['overage_percent', 'overage_percentage'],
        'symbol': '¥',
    },
}

ALL_ACCEPTED_FIELDS = (
    'overage_eur, overage_cny, overage (absolute); '
    'overage_percentage, overage_percent (relative)'
)
ALL_ACCEPTED_PATHS = 'root, summary, data, data.trip_summary, data.days[0].budget_vs_user'


def _first_day_budget_vs_user(days) -> dict:
    """Return data.days[0].budget_vs_user dict if present, else None."""
    if not (isinstance(days, list) and len(days) > 0):
        return None
    bvu = days[0].get('budget_vs_user')
    return bvu if isinstance(bvu, dict) else None


def _inner_nodes(inner: dict) -> list:
    """Return candidate nodes from the 'data' sub-dict."""
    nodes = [('data', inner)]
    trip_summary = inner.get('trip_summary')
    if isinstance(trip_summary, dict):
        nodes.append(('data.trip_summary', trip_summary))
    bvu = _first_day_budget_vs_user(inner.get('days'))
    if bvu is not None:
        nodes.append(('data.days[0].budget_vs_user', bvu))
    return nodes


def _get_candidate_nodes(data: dict) -> list:
    """Return list of (path_label, node_dict) for all candidate container paths."""
    if not isinstance(data, dict):
        return []
    nodes = [('root', data)]
    summary = data.get('summary')
    if isinstance(summary, dict):
        nodes.append(('summary', summary))
    inner = data.get('data')
    if isinstance(inner, dict):
        nodes.extend(_inner_nodes(inner))
    return nodes


def _detect_currency(nodes: list) -> str:
    """Detect currency by probing known field names in candidate nodes."""
    for _label, node in nodes:
        if 'overage_eur' in node:
            return 'EUR'
        if 'overage_cny' in node:
            return 'CNY'
    return 'EUR'


def _first_matching_field(node: dict, field_names: list) -> tuple:
    """Return (value, name) for the first field_name found in node, or (None, None)."""
    for name in field_names:
        if name in node:
            return node[name], name
    return None, None


def _resolve_field(nodes: list, field_names: list) -> tuple:
    """
    Search candidate nodes for any of the given field names.
    Returns (value, path_label) of the first match, or (None, None).
    """
    for label, node in nodes:
        value, name = _first_matching_field(node, field_names)
        if value is not None or name is not None:
            return value, f'{label}.{name}'
    return None, None


def _parse_json_file(budget_file: Path) -> object:
    """Read and JSON-parse a file. Caller handles exceptions."""
    return json.loads(budget_file.read_text(encoding='utf-8'))


def _load_budget_json(budget_path: str) -> tuple:
    """Load and parse a budget.json file. Returns (data, error_code)."""
    budget_file = Path(budget_path)
    if not budget_file.exists():
        print(f"Error: Budget file not found: {budget_path}", file=sys.stderr)
        return None, 2
    try:
        return _parse_json_file(budget_file), None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {budget_path}: {e}", file=sys.stderr)
        return None, 2
    except Exception as e:
        print(f"Error reading {budget_path}: {e}", file=sys.stderr)
        return None, 2


def _print_review_required(symbol, overage_abs, overage_pct, abs_path, pct_path, threshold_amount, threshold_pct, abs_exceeded, pct_exceeded):
    """Print review-required diagnostics."""
    print("BUDGET REVIEW REQUIRED")
    print(f"  Overage: {symbol}{overage_abs:.2f} ({overage_pct:.1f}%)  [from {abs_path}, {pct_path}]")
    print(f"  Thresholds: {symbol}{threshold_amount} or {threshold_pct}%")
    if abs_exceeded:
        print(f"  Absolute overage exceeds {symbol}{threshold_amount}")
    if pct_exceeded:
        print(f"  Percentage overage exceeds {threshold_pct}%")
    print()
    print("  Day-by-day review is REQUIRED to adjust itinerary.")


def _print_acceptable(symbol, overage_abs, overage_pct, abs_path, pct_path, threshold_amount, threshold_pct):
    """Print budget-acceptable diagnostics."""
    print("Budget acceptable")
    print(f"  Overage: {symbol}{overage_abs:.2f} ({overage_pct:.1f}%)  [from {abs_path}, {pct_path}]")
    print(f"  Within thresholds: {symbol}{threshold_amount} and {threshold_pct}%")


def _resolve_overage_values(nodes, fields, budget_path):
    """
    Resolve absolute and percentage overage from candidate nodes.
    Returns (overage_abs, abs_path, overage_pct, pct_path) or None on error.
    """
    overage_abs, abs_path = _resolve_field(nodes, fields['absolute'])
    overage_pct_val, pct_path = _resolve_field(nodes, fields['percentage'])
    if overage_abs is None or overage_pct_val is None:
        print(f"Error: Missing overage fields in {budget_path}", file=sys.stderr)
        print(f"  Accepted fields: {ALL_ACCEPTED_FIELDS}", file=sys.stderr)
        print(f"  Searched paths: {ALL_ACCEPTED_PATHS}", file=sys.stderr)
        return None
    try:
        return float(overage_abs), abs_path, float(overage_pct_val), pct_path
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid overage values: {e}", file=sys.stderr)
        return None


def _evaluate_thresholds(overage_abs, overage_pct, threshold_amount, threshold_pct, symbol, abs_path, pct_path):
    """Compare overage against thresholds and print result. Returns exit code 0 or 1."""
    abs_exceeded = abs(overage_abs) > threshold_amount
    pct_exceeded = abs(overage_pct) > threshold_pct
    if abs_exceeded or pct_exceeded:
        _print_review_required(symbol, overage_abs, overage_pct, abs_path, pct_path, threshold_amount, threshold_pct, abs_exceeded, pct_exceeded)
        return 1
    _print_acceptable(symbol, overage_abs, overage_pct, abs_path, pct_path, threshold_amount, threshold_pct)
    return 0


def check_budget_overage(budget_path: str, threshold_amount: float = 200.0, threshold_pct: float = 20.0) -> int:
    # Defaults: 200 currency units absolute / 20% relative — chosen as reasonable
    # thresholds where overage becomes significant enough to warrant day-by-day review.
    # Override via CLI args: check-budget-overage.py <path> <amount> <pct>
    """
    Check if budget overage exceeds thresholds.

    Args:
        budget_path: Path to budget.json file
        threshold_amount: Absolute overage threshold in native currency
        threshold_pct: Percentage overage threshold

    Returns:
        0 if acceptable, 1 if review required, 2 if error
    """
    data, err = _load_budget_json(budget_path)
    if err is not None:
        return err
    nodes = _get_candidate_nodes(data)
    currency = _detect_currency(nodes)
    fields = CURRENCY_FIELDS[currency]
    resolved = _resolve_overage_values(nodes, fields, budget_path)
    if resolved is None:
        return 2
    overage_abs, abs_path, overage_pct_val, pct_path = resolved
    return _evaluate_thresholds(overage_abs, overage_pct_val, threshold_amount, threshold_pct, fields['symbol'], abs_path, pct_path)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    budget_path = sys.argv[1]
    threshold_amount = float(sys.argv[2]) if len(sys.argv) > 2 else 200.0
    threshold_pct = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
    return check_budget_overage(budget_path, threshold_amount, threshold_pct)


if __name__ == '__main__':
    sys.exit(main())
