#!/usr/bin/env python3
"""
Validate Chinese name extraction logic for Issue #5

Tests both bilingual formats:
- Format 1 (attractions): 'English (Chinese)'
- Format 2 (entertainment): 'Chinese (English)'
"""

import re


def extract_chinese_name(name: str) -> str:
    """Extract Chinese name from bilingual format (same logic as fetch-images-batch.py)"""
    # Match content within parentheses and text before them
    match = re.search(r'^(.+?)\s*\((.+?)\)$', name)
    if not match:
        return ""

    before_paren = match.group(1).strip()
    inside_paren = match.group(2).strip()

    # Detect if text before parentheses contains Chinese characters
    has_chinese_before = bool(re.search(r'[\u4e00-\u9fff]', before_paren))

    if has_chinese_before:
        # Format 2: Chinese (English) - entertainment style
        return before_paren
    else:
        # Format 1: English (Chinese) - attractions style
        return inside_paren


def test_extraction():
    """Test cases covering both formats"""
    test_cases = [
        # Format 1: Attractions (English first)
        ("Raffles City Chongqing Observation Deck (来福士观景台)", "来福士观景台"),
        ("Huguang Guild Hall (湖广会馆)", "湖广会馆"),
        ("Hongyadong (洪崖洞民俗风貌区)", "洪崖洞民俗风貌区"),

        # Format 2: Entertainment (Chinese first)
        ("静·serene SPA 泰式按摩足疗 (Serene Thai SPA)", "静·serene SPA 泰式按摩足疗"),
        ("观远足道养生 (Guanyuan Zudao Wellness - Jiefangbei)", "观远足道养生"),
        ("KOH Thai SPA 暹罗之屿泰式按摩足疗 (Jiefangbei 2nd Branch)", "KOH Thai SPA 暹罗之屿泰式按摩足疗"),

        # Edge cases
        ("Plain Name", ""),  # No parentheses
        ("Some Place ()", ""),  # Empty parentheses
    ]

    print("Testing Chinese name extraction:")
    print("=" * 80)

    passed = 0
    failed = 0

    for input_name, expected in test_cases:
        result = extract_chinese_name(input_name)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status}")
        print(f"  Input:    {input_name}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    success = test_extraction()
    exit(0 if success else 1)
