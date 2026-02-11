#!/usr/bin/env python3
"""
Quick test for Chinese name extraction from parentheses.
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

    has_chinese_before = bool(re.search(r'[\u4e00-\u9fff]', before_paren))

    if has_chinese_before:
        return before_paren
    else:
        return inside_paren


# Test cases from actual data
test_cases = [
    ("Raffles City Chongqing Observation Deck (来福士观景台)", "来福士观景台"),
    ("Huguang Guild Hall (湖广会馆)", "湖广会馆"),
    ("Xiayao Li (下浩里) & Longmenhao Old Street (龙门浩老街)", "下浩里"),  # First match
    ("Liziba Station (李子坝单轨穿楼) - Optional", "李子坝单轨穿楼"),
    ("Hongyadong (洪崖洞民俗风貌区) - Optional", "洪崖洞民俗风貌区"),
    ("Chengdu Taikoo Li (成都太古里)", "成都太古里"),
    ("Some Place Without Chinese", ""),  # No parentheses
    ("", ""),  # Empty string
]

print("Testing Chinese name extraction:")
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
        print(f"{status} '{original[:40]}...' -> '{result}'")

print("=" * 70)
if all_passed:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed!")
    exit(1)
