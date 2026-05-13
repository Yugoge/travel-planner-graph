#!/usr/bin/env python3
"""Day 13 dinner primary fix: travelers are on G26 17:00-21:32.
Sit-down 本帮菜 (HOMES) impossible. Change primary to G26 on-train meal order,
demote HOMES to alternative. Mirror Day 12 breakfast G5车上早餐 structure.
"""
import json
import subprocess
from pathlib import Path

BASE = Path('/root/travel-planner/data/china-20260412-092624')

with open(BASE / 'meals.json') as f:
    meals = json.load(f)

day13 = next(d for d in meals['data']['days'] if d['day'] == 13)

# Move current primary to alternatives[0]
current_primary = day13['dinner']['primary']
current_alts = day13['dinner'].get('alternatives', [])

# Add a note to demoted item
current_primary_demoted = dict(current_primary)
current_primary_demoted['optional'] = True
current_primary_demoted['notes_base'] = (
    "DEMOTED (G26 conflict): Travelers depart Shanghai Hongqiao 17:00 on G26 to Beijing. "
    "This venue opens 17:00 — no time to dine. Keep as theoretical option if departure changes. "
) + current_primary_demoted.get('notes_base', '')

new_primary = {
    "name_base": "G26 HSR On-Train Dinner (高铁G26车上晚餐)",
    "name_local": "高铁G26车厢晚餐",
    "location_base": "On board G26 Shanghai Hongqiao → Beijing South, 17:00-21:32",
    "location_local": "G26次列车车厢内 上海虹桥→北京南 17:00-21:32",
    "cost": 50,
    "currency_local": "CNY",
    "optional": False,
    "cuisine_base": "Train Dining Car / Pre-Order Meal Service",
    "cuisine_local": "高铁餐车 / 高铁点餐",
    "signature_dishes_base": "Boxed rice meals (he fan), dumplings, packaged snacks. Also available via 'G26 点餐' service (pre-order from station kiosks or 12306 app for hot meals delivered at intermediate stops).",
    "signature_dishes_local": "盒饭，饺子，包装零食。可使用「G26点餐」服务（12306 App 或车站柜台预订，途中停靠站送餐）。",
    "notes_base": (
        "Travelers board G26 at Shanghai Hongqiao 17:00 — dinner happens en-route to Beijing (arrival 21:32). "
        "Options: (a) Dining car (餐车) sells hot boxed meals 25-50 CNY, dumplings 15-20 CNY, snacks. "
        "(b) Pre-order via 12306 app under '订餐服务' — choose from station vendors at upcoming stops; hot meal delivered to seat at the station. "
        "(c) Bring takeout from Shanghai before boarding (e.g. 新雅粤菜馆 takeaway near 虹桥). "
        "Budget ~50 CNY/person."
    ),
    "notes_local": (
        "两人于 17:00 在上海虹桥站登 G26，晚餐需车上解决（21:32 抵北京南）。可选："
        "(a) 餐车热盒饭 25-50元 / 饺子 15-20元 / 零食; "
        "(b) 用 12306 App「订餐服务」预订沿途车站送餐，选择中式快餐或地方特色，热食座位送达; "
        "(c) 虹桥站附近购买外带带上车（如新雅粤菜馆）。预算约 50 元/人。"
    ),
    "search_results": [
        {
            "skill": "rednote",
            "type": "search_attempt",
            "url": "https://www.xiaohongshu.com/search_result?keyword=G26高铁点餐推荐",
            "display_text": "RedNote - G26高铁点餐推荐 (search attempted; rate-limited)"
        }
    ]
}

day13['dinner']['primary'] = new_primary
day13['dinner']['alternatives'] = [current_primary_demoted] + current_alts

# Save via save.py per-day
tmp_payload = {
    "agent": "meals",
    "status": "complete",
    "data": {
        "days": [day13]
    }
}

tmp_file = Path('/tmp/day13_meals_payload.json')
with open(tmp_file, 'w') as f:
    json.dump(tmp_payload, f, ensure_ascii=False, indent=2)

result = subprocess.run([
    'python3', '/root/travel-planner/scripts/save.py',
    '--agent', 'meals',
    '--trip', 'china-20260412-092624',
    '--day', '13',
    '--input', str(tmp_file),
], capture_output=True, text=True, cwd='/root/travel-planner')

print("save.py stdout:", result.stdout[:500])
print("save.py stderr:", result.stderr[:500] if result.stderr else "(none)")
print("save.py exit:", result.returncode)

# Verify
with open(BASE / 'meals.json') as f:
    md = json.load(f)
day13_re = next(d for d in md['data']['days'] if d['day'] == 13)
print(f"\nDay 13 dinner primary: {day13_re['dinner']['primary']['name_local']}")
print(f"Day 13 dinner alts count: {len(day13_re['dinner'].get('alternatives', []))}")
for i, a in enumerate(day13_re['dinner'].get('alternatives', [])):
    print(f"  alt[{i}]: {a.get('name_local','?')}")
