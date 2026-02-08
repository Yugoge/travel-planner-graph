#!/usr/bin/env python3
"""Final validation for ISSUE-3: Compound category translation."""

import json
import re
import sys
from pathlib import Path

def main():
    print("ISSUE-3 Final Validation: Compound Category Translation")
    print("=" * 60)
    print()

    # 1. Verify formatCategoryLabel function exists in generator
    generator_file = Path('scripts/lib/html_generator.py')
    with open(generator_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'if (code.toString().includes(\'/\'))' in content:
        print("✓ formatCategoryLabel has slash-handling logic")
    else:
        print("✗ formatCategoryLabel missing slash-handling logic")
        return 1

    # 2. Check category mappings exist
    required_mappings = [
        'church', 'museum', 'historic building', 'historic_building',
        'mountain', 'observation deck', 'observation_deck',
        'tourist attraction', 'tourist_attraction', 'historic street'
    ]

    missing = []
    for mapping in required_mappings:
        pattern = f"'{mapping}'"
        if pattern not in content:
            missing.append(mapping)

    if missing:
        print(f"✗ Missing category mappings: {', '.join(missing)}")
        return 1
    else:
        print(f"✓ All {len(required_mappings)} required category mappings present")

    # 3. Verify HTML was generated
    html_file = Path('data/beijing-exchange-bucket-list-20260202-232405/travel-plan-test.html')
    if not html_file.exists():
        print("✗ HTML file not generated")
        return 1

    print(f"✓ HTML file generated: {html_file}")

    # 4. Extract and verify function in HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    if 'function formatCategoryLabel(code, type)' not in html_content:
        print("✗ formatCategoryLabel function not in HTML")
        return 1

    if 'if (code.toString().includes(\'/\'))' in html_content:
        print("✓ Slash-handling logic present in HTML")
    else:
        print("✗ Slash-handling logic missing in HTML")
        return 1

    # 5. Verify PLAN_DATA has compound categories
    match = re.search(r'const PLAN_DATA = ({.*?});', html_content, re.DOTALL)
    if not match:
        print("✗ Could not find PLAN_DATA in HTML")
        return 1

    plan_data = json.loads(match.group(1))
    compound_count = 0
    sample_compounds = []

    for day in plan_data.get('days', []):
        for attr in day.get('attractions', []):
            if '/' in attr.get('type', ''):
                compound_count += 1
                if len(sample_compounds) < 5:
                    sample_compounds.append(attr['type'])

    print(f"✓ Found {compound_count} compound categories in PLAN_DATA")
    print()
    print("Sample compound categories:")
    for cat in sample_compounds:
        print(f"  - {cat}")

    print()
    print("=" * 60)
    print("✓ ISSUE-3 validation PASSED")
    print()
    print("Summary:")
    print(f"  - formatCategoryLabel modified to handle slashes")
    print(f"  - {len(required_mappings)} required category mappings added")
    print(f"  - {compound_count} compound categories found in data")
    print(f"  - HTML successfully generated with updated function")
    print()
    print("Ready for QA verification:")
    print("  1. Open HTML file in browser")
    print("  2. Check that compound categories display in Chinese")
    print("  3. Verify no English compound categories remain")

    return 0

if __name__ == '__main__':
    sys.exit(main())
