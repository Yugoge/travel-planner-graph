#!/usr/bin/env python3
"""
Test enhanced Chinese name extraction that handles both formats.
Root cause fix validation for Issue #3.
"""

import re


def extract_chinese_name(name: str) -> str:
    """Extract Chinese name from bilingual format (current implementation)"""
    # Find FIRST parenthesized content (handles multiple parentheses and trailing text)
    match = re.search(r'^(.+?)\s*\(([^)]+)\)', name)
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


# Test both formats
test_cases = [
    # Format 1: English (Chinese) - attractions
    ("Raffles City Chongqing Observation Deck (来福士观景台)", "来福士观景台"),
    ("Huguang Guild Hall (湖广会馆)", "湖广会馆"),
    ("Chengdu Taikoo Li (成都太古里)", "成都太古里"),

    # Format 2: Chinese (English) - entertainment
    ("静·serene SPA 泰式按摩足疗 (Serene Thai SPA)", "静·serene SPA 泰式按摩足疗"),
    ("重庆大剧院 (Chongqing Grand Theatre)", "重庆大剧院"),

    # Edge cases
    ("Some Place Without Chinese", ""),
    ("", ""),
]

print("Testing enhanced Chinese name extraction (both formats):")
print("=" * 70)

all_passed = True
for original, expected in test_cases:
    result = extract_chinese_name(original)
    status = "✓" if result == expected else "✗"

    if result != expected:
        all_passed = False
        print(f"{status} FAIL")
        print(f"  Input:    '{original}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
    else:
        short_name = original[:50] + "..." if len(original) > 50 else original
        print(f"{status} '{short_name}' -> '{result}'")

print("=" * 70)
if all_passed:
    print("✅ All tests passed! Handles both formats correctly:")
    print("   Format 1 (attractions): English (Chinese)")
    print("   Format 2 (entertainment): Chinese (English)")
else:
    print("❌ Some tests failed!")
    exit(1)
