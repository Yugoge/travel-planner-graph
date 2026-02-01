#!/usr/bin/env python3
"""
Extract booking items from timeline/budget warnings and generate actionable checklist.
Usage: generate-booking-checklist.py <timeline_json_path> <budget_json_path>
Exit codes:
  0 = success (checklist generated)
  2 = error (file not found, invalid JSON)

Examples:
  python3 generate-booking-checklist.py data/trip/timeline.json data/trip/budget.json
  python3 generate-booking-checklist.py /root/travel-planner/data/china-feb15/timeline.json /root/travel-planner/data/china-feb15/budget.json
"""

import sys
import json
from pathlib import Path
from typing import Dict, List


def extract_urgent_items(warnings: List) -> List[Dict[str, str]]:
    """Extract URGENT booking items (trains, sold-out tickets)."""
    urgent = []

    keywords_urgent = [
        'train', 'railway', 'ticket', 'sold out', 'book immediately',
        'advance booking required', 'limited availability', 'peak season',
        'reservation required', 'must book'
    ]

    for warning in warnings:
        # Handle both string and dict warnings
        if isinstance(warning, dict):
            warning_text = warning.get('description', '') + ' ' + warning.get('recommendation', '')
            warning_lower = warning_text.lower()
        else:
            warning_lower = str(warning).lower()
        if any(keyword in warning_lower for keyword in keywords_urgent):
            # Try to extract day number
            day_num = None
            if isinstance(warning, dict) and 'day' in warning:
                day_num = str(warning['day'])
            elif 'day ' in warning_lower:
                try:
                    day_num = warning_lower.split('day ')[1].split()[0].strip(':,')
                except:
                    pass

            # Get item text
            if isinstance(warning, dict):
                item_text = warning.get('description', str(warning))
            else:
                item_text = str(warning)

            urgent.append({
                'item': item_text,
                'day': day_num,
                'category': 'transportation' if 'train' in warning_lower or 'railway' in warning_lower else 'activity'
            })

    return urgent


def extract_advance_items(warnings: List) -> List[Dict[str, str]]:
    """Extract ADVANCE booking items (restaurants, popular attractions)."""
    advance = []

    keywords_advance = [
        'reservation recommended', 'popular', 'advance notice',
        'restaurant', 'busy', 'recommend booking', 'should reserve',
        'attraction', 'museum', 'show', 'performance'
    ]

    for warning in warnings:
        # Handle both string and dict warnings
        if isinstance(warning, dict):
            warning_text = warning.get('description', '') + ' ' + warning.get('recommendation', '')
            warning_lower = warning_text.lower()
        else:
            warning_lower = str(warning).lower()
        # Skip if already categorized as urgent
        if any(keyword in warning_lower for keyword in ['train', 'sold out', 'must book']):
            continue

        if any(keyword in warning_lower for keyword in keywords_advance):
            # Try to extract day number
            day_num = None
            if isinstance(warning, dict) and 'day' in warning:
                day_num = str(warning['day'])
            elif 'day ' in warning_lower:
                try:
                    day_num = warning_lower.split('day ')[1].split()[0].strip(':,')
                except:
                    pass

            # Get item text
            if isinstance(warning, dict):
                item_text = warning.get('description', str(warning))
            else:
                item_text = str(warning)

            advance.append({
                'item': item_text,
                'day': day_num,
                'category': 'restaurant' if 'restaurant' in warning_lower or 'dinner' in warning_lower else 'activity'
            })

    return advance


def extract_regular_items(warnings: List) -> List[Dict[str, str]]:
    """Extract regular booking items (not urgent or advance)."""
    regular = []

    urgent_keywords = ['train', 'sold out', 'must book', 'immediately']
    advance_keywords = ['reservation', 'advance', 'popular', 'recommend booking']

    for warning in warnings:
        # Handle both string and dict warnings
        if isinstance(warning, dict):
            warning_text = warning.get('description', '') + ' ' + warning.get('recommendation', '')
            warning_lower = warning_text.lower()
        else:
            warning_lower = str(warning).lower()

        # Skip if already categorized
        if any(keyword in warning_lower for keyword in urgent_keywords + advance_keywords):
            continue

        # Check if it's a booking-related warning
        booking_keywords = ['booking', 'reserve', 'ticket', 'admission', 'entry']
        if any(keyword in warning_lower for keyword in booking_keywords):
            day_num = None
            if isinstance(warning, dict) and 'day' in warning:
                day_num = str(warning['day'])
            elif 'day ' in warning_lower:
                try:
                    day_num = warning_lower.split('day ')[1].split()[0].strip(':,')
                except:
                    pass

            # Get item text
            if isinstance(warning, dict):
                item_text = warning.get('description', str(warning))
            else:
                item_text = str(warning)

            regular.append({
                'item': item_text,
                'day': day_num,
                'category': 'general'
            })

    return regular


def generate_markdown_checklist(urgent: List[Dict], advance: List[Dict], regular: List[Dict]) -> str:
    """Generate markdown checklist from categorized items."""
    md = []

    if urgent:
        md.append("## 🚨 URGENT - Book Immediately")
        md.append("")
        md.append("These items require immediate booking to avoid sold-out situations:")
        md.append("")
        for item in urgent:
            day_prefix = f"**Day {item['day']}**: " if item['day'] else ""
            md.append(f"- [ ] {day_prefix}{item['item']}")
        md.append("")

    if advance:
        md.append("## 📅 ADVANCE - Book 1-2 Weeks Ahead")
        md.append("")
        md.append("These items should be booked in advance for better availability:")
        md.append("")
        for item in advance:
            day_prefix = f"**Day {item['day']}**: " if item['day'] else ""
            md.append(f"- [ ] {day_prefix}{item['item']}")
        md.append("")

    if regular:
        md.append("## 📝 REGULAR - Book Before Trip")
        md.append("")
        md.append("These items can be booked anytime before departure:")
        md.append("")
        for item in regular:
            day_prefix = f"**Day {item['day']}**: " if item['day'] else ""
            md.append(f"- [ ] {day_prefix}{item['item']}")
        md.append("")

    if not urgent and not advance and not regular:
        md.append("## ✅ No Booking Actions Required")
        md.append("")
        md.append("All activities and accommodations are confirmed or don't require advance booking.")
        md.append("")

    return "\n".join(md)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    timeline_path = Path(sys.argv[1])
    budget_path = Path(sys.argv[2])

    # Read timeline warnings
    timeline_warnings = []
    if timeline_path.exists():
        try:
            with timeline_path.open('r', encoding='utf-8') as f:
                timeline_data = json.load(f)
                timeline_warnings = timeline_data.get('warnings', [])
        except Exception as e:
            print(f"Warning: Could not read timeline warnings: {e}", file=sys.stderr)
    else:
        print(f"Warning: Timeline file not found: {timeline_path}", file=sys.stderr)

    # Read budget warnings
    budget_warnings = []
    if budget_path.exists():
        try:
            with budget_path.open('r', encoding='utf-8') as f:
                budget_data = json.load(f)
                budget_warnings = budget_data.get('warnings', [])
        except Exception as e:
            print(f"Warning: Could not read budget warnings: {e}", file=sys.stderr)
    else:
        print(f"Warning: Budget file not found: {budget_path}", file=sys.stderr)

    # Combine all warnings
    all_warnings = timeline_warnings + budget_warnings

    if not all_warnings:
        print("No warnings found in timeline or budget.")
        print()
        print(generate_markdown_checklist([], [], []))
        return 0

    # Categorize warnings
    urgent = extract_urgent_items(all_warnings)
    advance = extract_advance_items(all_warnings)
    regular = extract_regular_items(all_warnings)

    # Generate and print checklist
    checklist = generate_markdown_checklist(urgent, advance, regular)
    print(checklist)

    return 0


if __name__ == '__main__':
    sys.exit(main())
