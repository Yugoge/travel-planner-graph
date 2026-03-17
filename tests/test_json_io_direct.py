#!/usr/bin/env python3
"""Test json_io library directly (not through save.py)."""

import sys
from pathlib import Path

# Import json_io
sys.path.insert(0, str(Path("/root/travel-planner/scripts")))
from lib.json_io import save_agent_json, load_agent_json, ValidationError

TEST_DIR = Path("/root/travel-planner/data/agent-test-20260212-191529")
TIMELINE_FILE = TEST_DIR / "timeline-direct.json"

print("=" * 60)
print("TESTING json_io LIBRARY DIRECTLY")
print("=" * 60)
print()

# Test 1: Save using save_agent_json
print("TEST 1: Save using save_agent_json()")
print("-" * 60)

timeline_data = {
    "days": [
        {
            "day": 1,
            "date": "2026-02-22",
            "timeline": {
                "Morning Museum": {
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "duration_minutes": 120
                },
                "Lunch": {
                    "start_time": "12:00",
                    "end_time": "13:00",
                    "duration_minutes": 60
                }
            },
            "travel_segments": [
                {
                    "name_base": "Walk to Museum",
                    "name_local": "步行前往博物馆",
                    "type_base": "walk",
                    "type_local": "步行",
                    "icon": "🚶",
                    "start_time": "08:30",
                    "end_time": "09:00",
                    "duration_minutes": 30
                }
            ]
        }
    ]
}

try:
    save_agent_json(
        file_path=TIMELINE_FILE,
        agent_name="timeline",
        data=timeline_data,
        validate=True,
        create_backup=True
    )
    print(f"✅ Saved successfully to {TIMELINE_FILE}")
except ValidationError as e:
    print(f"❌ Validation error: {e}")
    print(f"   HIGH issues: {len(e.high_issues)}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Load using load_agent_json
print()
print("TEST 2: Load using load_agent_json()")
print("-" * 60)

try:
    loaded_data = load_agent_json(TIMELINE_FILE, validate=False)
    print(f"✅ Loaded successfully")
    print(f"   Days: {len(loaded_data['days'])}")
    print(f"   Day 1 activities: {len(loaded_data['days'][0]['timeline'])}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 3: Try to save invalid data
print()
print("TEST 3: Attempt to save invalid data")
print("-" * 60)

invalid_data = {
    "days": [
        {
            "day": 1,
            "date": "2026-02-22",
            "timeline": {
                "Bad Activity": {
                    "start_time": "10:00"
                    # Missing end_time
                }
            }
        }
    ]
}

try:
    save_agent_json(
        file_path=TIMELINE_FILE,
        agent_name="timeline",
        data=invalid_data,
        validate=True
    )
    print("❌ Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"✅ Correctly caught validation error")
    print(f"   HIGH issues: {len(e.high_issues)}")
    for issue in e.high_issues[:3]:
        print(f"   - {issue.label}: {issue.field}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

# Test 4: Verify original file not corrupted
print()
print("TEST 4: Verify original file not corrupted after validation failure")
print("-" * 60)

try:
    reloaded_data = load_agent_json(TIMELINE_FILE)
    if "Morning Museum" in reloaded_data['days'][0]['timeline']:
        print("✅ Original valid data still intact")
    else:
        print("❌ Original data corrupted")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
print()
print("Summary:")
print("  - save_agent_json() works with validation")
print("  - load_agent_json() works correctly")
print("  - Invalid data correctly rejected")
print("  - Original files protected during validation")
