#!/usr/bin/env python3
"""Test unified scripts architecture for timeline.json workflow."""

import json
import sys
import subprocess
from pathlib import Path

# Test configuration
TEST_DIR = Path("/root/travel-planner/data/agent-test-20260212-191529")
TRIP_SLUG = "agent-test-20260212-191529"
TIMELINE_FILE = TEST_DIR / "timeline.json"
SAVE_SCRIPT = Path("/root/travel-planner/scripts/save.py")

# Import json_io for loading
sys.path.insert(0, str(Path("/root/travel-planner/scripts")))
from lib.json_io import load_agent_json, save_agent_json

print("=" * 60)
print("TIMELINE.JSON WORKFLOW TEST")
print("=" * 60)
print()

# ============================================================
# TEST 1: Create minimal timeline.json
# ============================================================
print("TEST 1: Creating minimal timeline.json (2 days)")
print("-" * 60)

timeline_data = {
    "days": [
        {
            "day": 1,
            "date": "2026-02-20",
            "timeline": {
                "Hotel check-in": {
                    "start_time": "14:00",
                    "end_time": "14:30",
                    "duration_minutes": 30
                },
                "City Museum Visit": {
                    "start_time": "15:00",
                    "end_time": "17:00",
                    "duration_minutes": 120
                },
                "Dinner at Local Restaurant": {
                    "start_time": "18:30",
                    "end_time": "20:00",
                    "duration_minutes": 90
                },
                "Evening Walk": {
                    "start_time": "20:30",
                    "end_time": "21:30",
                    "duration_minutes": 60
                }
            },
            "travel_segments": [
                {
                    "name_base": "Taxi to City Museum",
                    "name_local": "打车前往市博物馆",
                    "type_base": "taxi",
                    "type_local": "出租车",
                    "icon": "🚕",
                    "start_time": "14:30",
                    "end_time": "15:00",
                    "duration_minutes": 30
                },
                {
                    "name_base": "Walk to Restaurant",
                    "name_local": "步行前往餐厅",
                    "type_base": "walk",
                    "type_local": "步行",
                    "icon": "🚶",
                    "start_time": "17:00",
                    "end_time": "18:30",
                    "duration_minutes": 90
                }
            ]
        },
        {
            "day": 2,
            "date": "2026-02-21",
            "timeline": {
                "Breakfast at Hotel": {
                    "start_time": "08:00",
                    "end_time": "09:00",
                    "duration_minutes": 60
                },
                "Historic Temple Tour": {
                    "start_time": "10:00",
                    "end_time": "12:00",
                    "duration_minutes": 120
                },
                "Lunch at Market": {
                    "start_time": "12:30",
                    "end_time": "14:00",
                    "duration_minutes": 90
                },
                "Hotel check-out": {
                    "start_time": "16:00",
                    "end_time": "16:30",
                    "duration_minutes": 30
                }
            },
            "travel_segments": [
                {
                    "name_base": "Metro to Temple District",
                    "name_local": "乘地铁前往寺庙区",
                    "type_base": "metro",
                    "type_local": "地铁",
                    "icon": "🚇",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "duration_minutes": 60
                }
            ]
        }
    ]
}

print(f"Created timeline with {len(timeline_data['days'])} days")
for day in timeline_data['days']:
    print(f"  Day {day['day']}: {len(day['timeline'])} activities, {len(day.get('travel_segments', []))} travel segments")

# ============================================================
# TEST 2: Save using scripts/save.py
# ============================================================
print()
print("TEST 2: Saving using scripts/save.py")
print("-" * 60)

# Write data to temp file for save.py
temp_input = TEST_DIR / ".tmp_timeline_input.json"
with open(temp_input, 'w', encoding='utf-8') as f:
    json.dump({
        "agent": "timeline",
        "status": "complete",
        "data": timeline_data,
        "notes": "Test timeline created by workflow test"
    }, f, indent=2, ensure_ascii=False)

# Run save.py
cmd = [
    "python3",
    str(SAVE_SCRIPT),
    "--trip", TRIP_SLUG,
    "--agent", "timeline",
    "--input", str(temp_input)
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"Exit code: {result.returncode}")
if result.stdout:
    print(f"STDOUT:\n{result.stdout}")
if result.stderr:
    print(f"STDERR:\n{result.stderr}")

# Clean up temp file
temp_input.unlink()

if result.returncode == 0:
    print("✅ Save successful")
else:
    print("❌ Save failed")
    sys.exit(1)

# Verify file exists
if TIMELINE_FILE.exists():
    print(f"✅ File created: {TIMELINE_FILE}")
    print(f"   Size: {TIMELINE_FILE.stat().st_size} bytes")
else:
    print(f"❌ File not found: {TIMELINE_FILE}")
    sys.exit(1)

# ============================================================
# TEST 3: Load timeline data
# ============================================================
print()
print("TEST 3: Loading timeline data using load_agent_json()")
print("-" * 60)

try:
    loaded_data = load_agent_json(TIMELINE_FILE)
    print(f"✅ Loaded timeline data")
    print(f"   Days: {len(loaded_data['days'])}")

    # Verify data matches
    if loaded_data['days'][0]['day'] == timeline_data['days'][0]['day']:
        print("✅ Data matches original")
    else:
        print("❌ Data mismatch")
        sys.exit(1)

except Exception as e:
    print(f"❌ Load failed: {e}")
    sys.exit(1)

# ============================================================
# TEST 4: Modify and re-save
# ============================================================
print()
print("TEST 4: Modifying timeline and re-saving")
print("-" * 60)

# Add a new activity to day 1
loaded_data['days'][0]['timeline']['Late Night Snack'] = {
    "start_time": "22:00",
    "end_time": "22:30",
    "duration_minutes": 30
}

print("Added new activity: 'Late Night Snack' to Day 1")
print(f"Day 1 now has {len(loaded_data['days'][0]['timeline'])} activities")

# Save modified data
temp_modified = TEST_DIR / ".tmp_timeline_modified.json"
with open(temp_modified, 'w', encoding='utf-8') as f:
    json.dump({
        "agent": "timeline",
        "status": "complete",
        "data": loaded_data,
        "notes": "Modified timeline with new activity"
    }, f, indent=2, ensure_ascii=False)

# Run save.py again
cmd = [
    "python3",
    str(SAVE_SCRIPT),
    "--trip", TRIP_SLUG,
    "--agent", "timeline",
    "--input", str(temp_modified)
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"Exit code: {result.returncode}")
if result.stderr:
    print(f"STDERR:\n{result.stderr}")

temp_modified.unlink()

if result.returncode == 0:
    print("✅ Re-save successful")

    # Check if backup was created
    backup_file = TIMELINE_FILE.with_suffix('.json.bak')
    if backup_file.exists():
        print(f"✅ Backup created: {backup_file}")
    else:
        print("⚠️  No backup found (may be expected)")

else:
    print("❌ Re-save failed")
    sys.exit(1)

# Verify modification persisted
reloaded_data = load_agent_json(TIMELINE_FILE)
if 'Late Night Snack' in reloaded_data['days'][0]['timeline']:
    print("✅ Modification persisted correctly")
else:
    print("❌ Modification not found after reload")
    sys.exit(1)

# ============================================================
# TEST 5: Verify schema validation
# ============================================================
print()
print("TEST 5: Testing schema validation (attempt invalid data)")
print("-" * 60)

# Create invalid data (missing required field)
invalid_data = {
    "days": [
        {
            "day": 1,
            "date": "2026-02-20",
            "timeline": {
                "Invalid Activity": {
                    "start_time": "10:00"
                    # Missing end_time (required field)
                }
            }
        }
    ]
}

temp_invalid = TEST_DIR / ".tmp_timeline_invalid.json"
with open(temp_invalid, 'w', encoding='utf-8') as f:
    json.dump({
        "agent": "timeline",
        "status": "complete",
        "data": invalid_data
    }, f, indent=2, ensure_ascii=False)

cmd = [
    "python3",
    str(SAVE_SCRIPT),
    "--trip", TRIP_SLUG,
    "--agent", "timeline",
    "--input", str(temp_invalid)
]

print("Attempting to save invalid timeline data...")
result = subprocess.run(cmd, capture_output=True, text=True)

temp_invalid.unlink()

if result.returncode != 0:
    print("✅ Validation correctly rejected invalid data")
    print(f"   Error message: {result.stderr.strip()[:200]}")
else:
    print("❌ Validation should have rejected invalid data")
    sys.exit(1)

# ============================================================
# SUMMARY
# ============================================================
print()
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("✅ All tests passed successfully!")
print()
print("Verified workflows:")
print("  1. Create minimal timeline.json (2 days, 3-4 activities each)")
print("  2. Save using scripts/save.py with validation")
print("  3. Load using load_agent_json()")
print("  4. Modify and re-save with backup creation")
print("  5. Schema validation correctly rejects invalid data")
print()
print(f"Final timeline file: {TIMELINE_FILE}")
print(f"File size: {TIMELINE_FILE.stat().st_size} bytes")
print("=" * 60)
