#!/usr/bin/env python3
"""Simple test to verify validation is working."""

import json
import sys
import subprocess
from pathlib import Path

TEST_DIR = Path("/root/travel-planner/data/agent-test-20260212-191529")
TRIP_SLUG = "agent-test-20260212-191529"
SAVE_SCRIPT = Path("/root/travel-planner/scripts/save.py")

print("Testing validation with invalid timeline data...")
print("=" * 60)

# Create invalid data (missing end_time)
invalid_data = {
    "agent": "timeline",
    "status": "complete",
    "data": {
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
}

temp_file = TEST_DIR / ".tmp_test_invalid.json"
with open(temp_file, 'w', encoding='utf-8') as f:
    json.dump(invalid_data, f, indent=2)

cmd = [
    "python3",
    str(SAVE_SCRIPT),
    "--trip", TRIP_SLUG,
    "--agent", "timeline",
    "--input", str(temp_file)
]

print("Running:", " ".join(cmd))
print()

result = subprocess.run(cmd, capture_output=True, text=True)

print(f"Exit code: {result.returncode}")
print()

if result.stdout:
    print("STDOUT:")
    print(result.stdout)
    print()

if result.stderr:
    print("STDERR:")
    print(result.stderr)
    print()

temp_file.unlink()

if result.returncode != 0:
    print("✅ Validation correctly rejected invalid data")
    sys.exit(0)
else:
    print("❌ Validation should have rejected invalid data")
    sys.exit(1)
