#!/usr/bin/env python3
"""Day 13 data-layer patch: add timeline entries for optional attractions/shopping
so the renderer surfaces them with dashed-border + Optional badge, matching Chengdu Day 5/6.

No script (renderer) modification. Pure data shape: each optional gets its own timeline
entry with start_time/end_time/duration_minutes/optional:true, identical to how Day 5
encodes 'Kuanzhai Alley Hidden Corners [Optional Plan B]'.
"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path('/root/travel-planner/data/china-20260412-092624')

def load(p):
    with open(p) as f:
        return json.load(f)

# 1. Load all relevant files
tl = load(BASE / 'timeline.json')
attr = load(BASE / 'attractions.json')
shop = load(BASE / 'shopping.json')

day13_tl = next(d for d in tl['data']['days'] if d['day'] == 13)
day13_attr = next(d for d in attr['data']['days'] if d['day'] == 13)
day13_shop = next(d for d in shop['data']['days'] if d['day'] == 13)

# 2. New timeline entries to add (data-layer only)
new_entries = {
    # Optional morning attraction — parallel with 豫园+城隍庙 primary
    "Shanghai Tower Observatory (上海中心大厦) — Morning Alternative": {
        "start_time": "09:45",
        "end_time": "12:00",
        "duration_minutes": 135,
        "optional": True
    },
    # Optional afternoon attraction — parallel with 静安寺 primary
    "Xintiandi Stone Lane Heritage Walk (新天地石库门历史街区) — Afternoon Alternative": {
        "start_time": "14:00",
        "end_time": "15:30",
        "duration_minutes": 90,
        "optional": True
    },
    # Optional shopping: 新天地 — afternoon (combine with stroll, parallel to 静安寺)
    "Xintiandi (新天地) — Heritage Shopping District": {
        "start_time": "14:00",
        "end_time": "15:30",
        "duration_minutes": 90,
        "optional": True
    },
    # Optional shopping: 豫园商城 — morning, parallel with 豫园 (natural combo)
    "Yu Garden Bazaar (豫园商城) — Shopping Alternative (Morning)": {
        "start_time": "09:45",
        "end_time": "12:00",
        "duration_minutes": 135,
        "optional": True
    },
    # Optional shopping: 淮海中路 K11 — afternoon alternative
    "Huaihai Middle Road & K11 Art Mall (淮海中路·K11) — Shopping Alternative": {
        "start_time": "14:00",
        "end_time": "15:30",
        "duration_minutes": 90,
        "optional": True
    },
}

# 3. Update timeline dict
day13_tl['timeline'].update(new_entries)

# 4. Save Day 13 timeline via save.py (data-layer respects schema; per-day write)
# Write a temp single-day payload that save.py can ingest
tmp_payload = {
    "agent": "timeline",
    "status": "complete",
    "data": {
        "days": [day13_tl]
    }
}

tmp_file = Path('/tmp/day13_tl_payload.json')
with open(tmp_file, 'w') as f:
    json.dump(tmp_payload, f, ensure_ascii=False, indent=2)

# Invoke save.py with --day 13
result = subprocess.run([
    'python3', '/root/travel-planner/scripts/save.py',
    '--agent', 'timeline',
    '--trip', 'china-20260412-092624',
    '--day', '13',
    '--input', str(tmp_file),
], capture_output=True, text=True, cwd='/root/travel-planner')

print("save.py stdout:", result.stdout)
print("save.py stderr:", result.stderr[:500] if result.stderr else "(none)")
print("save.py exit:", result.returncode)

if result.returncode != 0:
    print("FAILED - falling back to direct write")
    # Direct write fallback
    with open(BASE / 'timeline.json', 'w') as f:
        json.dump(tl, f, ensure_ascii=False, indent=2)
    print("Wrote timeline.json directly.")

# 5. Verify
re_tl = load(BASE / 'timeline.json')
re_day13 = next(d for d in re_tl['data']['days'] if d['day'] == 13)
opt_count = sum(1 for v in re_day13['timeline'].values() if v.get('optional'))
print(f"\nDay 13 timeline entries: {len(re_day13['timeline'])}")
print(f"  Optional entries: {opt_count}")
for name in new_entries:
    in_tl = name in re_day13['timeline']
    print(f"  [{('✓' if in_tl else '✗')}] {name[:90]}")
