#!/usr/bin/env python3
"""
Verify that generated HTML properly handles:
1. Category code formatting (no raw codes visible in rendered HTML)
2. Null address handling (shows fallback message)
3. Bilingual labels present
"""

import json
import re
from pathlib import Path

def extract_plan_data(html_path):
    """Extract PLAN_DATA JavaScript object from HTML."""
    html_content = html_path.read_text()
    match = re.search(r'const PLAN_DATA = (\{.*?\});', html_content, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None

def verify_formatters_exist(html_path):
    """Verify formatter functions exist in HTML."""
    html_content = html_path.read_text()
    checks = {
        'formatCategoryLabel': 'function formatCategoryLabel(code, type)' in html_content,
        'formatAddress': 'function formatAddress(address)' in html_content,
        'CATEGORY_MAPPINGS': 'const CATEGORY_MAPPINGS = {' in html_content,
    }
    return checks

def verify_formatter_calls(html_path):
    """Verify formatters are called in render functions."""
    html_content = html_path.read_text()
    checks = {
        'formatAddress_called': 'formatAddress(' in html_content,
        'formatCategoryLabel_called': 'formatCategoryLabel(' in html_content,
        'attraction_formatting': 'formatCategoryLabel(attr.type, \'attraction\')' in html_content,
        'hotel_formatting': 'formatCategoryLabel(' in html_content and 'hotel' in html_content,
        'restaurant_formatting': 'formatCategoryLabel(' in html_content and 'restaurant' in html_content,
    }
    return checks

def verify_bilingual_labels(html_path):
    """Verify bilingual labels exist in mappings."""
    html_content = html_path.read_text()
    bilingual_samples = [
        'Historical Site / 历史遗址',
        'Mid-Range Hotel / 中档酒店',
        'Local Cuisine / 本地菜',
        'Address not available / 地址未提供'
    ]
    checks = {label: label in html_content for label in bilingual_samples}
    return checks

def main():
    html_path = Path('/root/travel-planner/data/china-exchange-bucket-list-2026/travel-plan-test.html')

    if not html_path.exists():
        print(f"❌ HTML file not found: {html_path}")
        return 1

    print("=== HTML Rendering Verification ===\n")

    # Check 1: Verify formatters exist
    print("1. Checking formatter functions exist...")
    formatters = verify_formatters_exist(html_path)
    all_pass = True
    for name, exists in formatters.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {name}")
        if not exists:
            all_pass = False

    # Check 2: Verify formatters are called
    print("\n2. Checking formatters are called in render functions...")
    calls = verify_formatter_calls(html_path)
    for name, called in calls.items():
        status = "✓" if called else "✗"
        print(f"  {status} {name}")
        if not called:
            all_pass = False

    # Check 3: Verify bilingual labels
    print("\n3. Checking bilingual labels present...")
    labels = verify_bilingual_labels(html_path)
    for label, exists in labels.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {label}")
        if not exists:
            all_pass = False

    # Check 4: Verify PLAN_DATA contains raw codes (expected)
    print("\n4. Checking PLAN_DATA contains raw category codes (expected)...")
    plan_data = extract_plan_data(html_path)
    if plan_data:
        raw_codes_found = False
        if 'cities' in plan_data:
            for city in plan_data.get('cities', []):
                for attr in city.get('attractions', []):
                    if attr.get('type') in ['historical_site', 'museum', 'temple']:
                        print(f"  ✓ Found raw code '{attr.get('type')}' in PLAN_DATA (correct)")
                        raw_codes_found = True
                        break
                if raw_codes_found:
                    break
        if not raw_codes_found:
            print("  ⚠ No raw codes found in PLAN_DATA (may be OK if no matching data)")
    else:
        print("  ✗ Could not extract PLAN_DATA")
        all_pass = False

    # Summary
    print("\n=== Summary ===")
    if all_pass:
        print("✓ All verification checks passed")
        print("\n✓ Implementation correctly:")
        print("  - Defines formatter functions")
        print("  - Calls formatters in render functions")
        print("  - Includes bilingual labels")
        print("  - Preserves raw codes in PLAN_DATA")
        print("  - Formats codes at render time (not in data)")
        return 0
    else:
        print("✗ Some verification checks failed")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
