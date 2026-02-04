#!/usr/bin/env python3
"""Verify compound category translations in generated HTML."""

import sys
import json
import re
from pathlib import Path

def main():
    html_file = Path('data/beijing-exchange-bucket-list-20260202-232405/travel-plan-test.html')

    if not html_file.exists():
        print(f"Error: {html_file} does not exist")
        return 1

    # Read HTML content
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract PLAN_DATA JSON from HTML
    match = re.search(r'const PLAN_DATA = ({.*?});', html_content, re.DOTALL)
    if not match:
        print("Error: Could not find PLAN_DATA in HTML")
        return 1

    plan_data = json.loads(match.group(1))

    # Check for compound categories in attractions
    compound_categories = []
    for day in plan_data.get('days', []):
        for attr in day.get('attractions', []):
            if '/' in attr.get('type', ''):
                compound_categories.append(attr['type'])

    print(f"Found {len(compound_categories)} compound category types")
    print()

    # Show examples
    test_cases = [
        "Church / Museum / Historic Building",
        "Mountain / Observation Deck / Tourist Attraction",
        "Buddhist Temple / Historic Site",
        "Winter Theme Park / Ice Sculpture Park"
    ]

    print("Test cases from actual data:")
    for test in test_cases:
        if test in compound_categories:
            print(f"✓ Found: {test}")
        else:
            # Find similar
            similar = [c for c in compound_categories if test.split('/')[0].strip() in c]
            if similar:
                print(f"  Similar: {similar[0]}")

    print()
    print("Sample compound categories found:")
    for cat in sorted(set(compound_categories))[:10]:
        print(f"  - {cat}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
