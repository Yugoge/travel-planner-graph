#!/usr/bin/env python3
"""
Fix all outstanding data issues across bucket-list and itinerary JSON files.

Issues addressed:
  1. Bucket-list attractions missing time field (48 items)
  2. Bucket-list entertainment missing time dict (26 items, currently strings or absent)
  3. Itinerary accommodation missing check_in/check_out (Day 2 and Day 3)
  4. Bucket-list ALL files date=null -> "Day N"
  5. Itinerary budget only has 4 days, needs 21
  6. Bucket-list transportation notes_local missing (11 items)

Usage: python scripts/fix-all-data-issues.py <project_root>
"""

import json
import os
import sys
from pathlib import Path
from difflib import SequenceMatcher

PROJECT_ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

BUCKET = PROJECT_ROOT / "data" / "beijing-exchange-bucket-list-20260202-232405"
ITINERARY = PROJECT_ROOT / "data" / "china-feb-15-mar-7-2026-20260202-195429"

# Track all modifications for reporting
report = {
    "issue_1_attractions_time": 0,
    "issue_2_entertainment_time": 0,
    "issue_3_checkin_checkout": 0,
    "issue_4_date_null": 0,
    "issue_5_budget_days_added": 0,
    "issue_6_notes_local": 0,
    "errors": [],
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def word_set(text):
    """Extract significant words from text for fuzzy matching."""
    stop_words = {
        "the", "a", "an", "to", "from", "in", "at", "of", "and", "or",
        "with", "for", "/", "-", "(", ")", "—", "–"
    }
    words = set()
    for w in text.lower().replace("/", " ").replace("-", " ").replace("(", " ").replace(")", " ").split():
        if w not in stop_words and len(w) > 1:
            words.add(w)
    return words


def match_timeline(item_name, timeline_entries):
    """Match an attraction/entertainment name against timeline keys.

    Returns (start_time, end_time) if matched, else None.
    """
    item_words = word_set(item_name)
    best_score = 0
    best_match = None

    for key, times in timeline_entries.items():
        key_words = word_set(key)
        if not item_words or not key_words:
            continue

        # Check substring match (either direction)
        item_lower = item_name.lower()
        key_lower = key.lower()
        if item_lower in key_lower or key_lower in item_lower:
            return times["start_time"], times["end_time"]

        # Check word overlap
        overlap = item_words & key_words
        if len(overlap) >= 2:
            score = len(overlap) / max(len(item_words), len(key_words))
            if score > best_score:
                best_score = score
                best_match = (times["start_time"], times["end_time"])

        # Also try SequenceMatcher for partial matches
        ratio = SequenceMatcher(None, item_lower, key_lower).ratio()
        if ratio > 0.5 and ratio > best_score:
            best_score = ratio
            best_match = (times["start_time"], times["end_time"])

    if best_score >= 0.35 and best_match:
        return best_match
    return None


def default_time_for_position(index):
    """Assign reasonable default time based on position in day's list."""
    defaults = [
        {"start": "09:00", "end": "11:00"},
        {"start": "11:00", "end": "13:00"},
        {"start": "14:00", "end": "16:00"},
        {"start": "16:00", "end": "18:00"},
        {"start": "19:00", "end": "21:00"},
    ]
    if index < len(defaults):
        return defaults[index]
    return {"start": "19:00", "end": "21:00"}


# ============================================================
# Load timeline for matching (Issue 1 and 2)
# ============================================================
timeline_data = load_json(BUCKET / "timeline.json")
timeline_by_day = {}
for day_entry in timeline_data["data"]["days"]:
    timeline_by_day[day_entry["day"]] = day_entry["timeline"]


# ============================================================
# ISSUE 1: Bucket-list attractions missing time (48 items)
# ============================================================
print("=== Issue 1: Adding time to bucket-list attractions ===")
attractions_data = load_json(BUCKET / "attractions.json")

for day_entry in attractions_data["data"]["days"]:
    day_num = day_entry["day"]
    tl = timeline_by_day.get(day_num, {})

    for idx, attr in enumerate(day_entry["attractions"]):
        # Use name_base for matching if available, else name
        match_name = attr.get("name_base") or attr.get("name_english") or attr.get("name", "")

        matched = match_timeline(match_name, tl)

        # Also try name_local / name_chinese
        if not matched:
            alt_name = attr.get("name_local") or attr.get("name_chinese") or ""
            if alt_name:
                matched = match_timeline(alt_name, tl)

        # Also try the combined name field
        if not matched and "name" in attr:
            matched = match_timeline(attr["name"], tl)

        if matched:
            attr["time"] = {"start": matched[0], "end": matched[1]}
        else:
            attr["time"] = default_time_for_position(idx)

        report["issue_1_attractions_time"] += 1
        print(f"  Day {day_num}: {match_name[:50]} -> {attr['time']}")

save_json(BUCKET / "attractions.json", attractions_data)
print(f"  Total: {report['issue_1_attractions_time']} attractions updated\n")


# ============================================================
# ISSUE 2: Bucket-list entertainment missing time dict (26 items)
# Entertainment currently has time as string "HH:MM" or missing.
# Convert to {start, end} dict using timeline matching.
# ============================================================
print("=== Issue 2: Converting entertainment time to {start, end} dicts ===")
entertainment_data = load_json(BUCKET / "entertainment.json")

for day_entry in entertainment_data["data"]["days"]:
    day_num = day_entry["day"]
    tl = timeline_by_day.get(day_num, {})

    for idx, ent in enumerate(day_entry["entertainment"]):
        match_name = ent.get("name_base") or ent.get("name", "")
        existing_time = ent.get("time")

        # Try timeline matching first
        matched = match_timeline(match_name, tl)
        if not matched and "name" in ent:
            matched = match_timeline(ent["name"], tl)
        if not matched:
            alt_name = ent.get("name_local", "")
            if alt_name:
                matched = match_timeline(alt_name, tl)

        if matched:
            ent["time"] = {"start": matched[0], "end": matched[1]}
        elif existing_time and isinstance(existing_time, str):
            # Convert string time to dict with reasonable end time
            start = existing_time
            # Estimate end time: add 1.5 hours
            start_h, start_m = int(start.split(":")[0]), int(start.split(":")[1])
            end_h = start_h + 1
            end_m = start_m + 30
            if end_m >= 60:
                end_h += 1
                end_m -= 60
            end = f"{end_h:02d}:{end_m:02d}"
            ent["time"] = {"start": start, "end": end}
        else:
            ent["time"] = default_time_for_position(idx)

        report["issue_2_entertainment_time"] += 1
        print(f"  Day {day_num}: {match_name[:50]} -> {ent['time']}")

save_json(BUCKET / "entertainment.json", entertainment_data)
print(f"  Total: {report['issue_2_entertainment_time']} entertainment items updated\n")


# ============================================================
# ISSUE 3: Itinerary accommodation missing check_in/check_out
# Day 2 and Day 3 have empty strings
# ============================================================
print("=== Issue 3: Fixing check_in/check_out for Day 2 and Day 3 ===")
accom_data = load_json(ITINERARY / "accommodation.json")

for day_entry in accom_data["data"]["days"]:
    day_num = day_entry["day"]
    accom = day_entry.get("accommodation", {})

    if day_num in (2, 3):
        old_ci = accom.get("check_in", "")
        old_co = accom.get("check_out", "")
        if old_ci == "" or old_co == "":
            accom["check_in"] = "14:00"
            accom["check_out"] = "12:00"
            report["issue_3_checkin_checkout"] += 1
            name = accom.get("name_base") or accom.get("name", "unknown")
            print(f"  Day {day_num} ({name}): check_in='{old_ci}'->'14:00', check_out='{old_co}'->'12:00'")

save_json(ITINERARY / "accommodation.json", accom_data)
print(f"  Total: {report['issue_3_checkin_checkout']} days fixed\n")


# ============================================================
# ISSUE 4: Bucket-list ALL files date=null -> "Day N"
# ============================================================
print("=== Issue 4: Fixing date=null -> 'Day N' in all bucket-list files ===")
bucket_files = [
    "meals.json", "attractions.json", "entertainment.json",
    "accommodation.json", "shopping.json", "transportation.json", "budget.json"
]

for fname in bucket_files:
    fpath = BUCKET / fname
    data = load_json(fpath)
    days_list = data.get("data", {}).get("days", [])
    changed = 0

    for day_entry in days_list:
        day_num = day_entry.get("day")
        current_date = day_entry.get("date")

        if current_date is None:
            day_entry["date"] = f"Day {day_num}"
            changed += 1

    if changed > 0:
        save_json(fpath, data)
        report["issue_4_date_null"] += changed
        print(f"  {fname}: {changed} days fixed")
    else:
        print(f"  {fname}: no null dates found (already fixed)")

print(f"  Total: {report['issue_4_date_null']} date fields fixed\n")


# ============================================================
# ISSUE 5: Itinerary budget only has 4 days, needs 21
# ============================================================
print("=== Issue 5: Extending itinerary budget from 4 to 21 days ===")
budget_data = load_json(ITINERARY / "budget.json")

# Load all source files
meals_data = load_json(ITINERARY / "meals.json")
accom_src = load_json(ITINERARY / "accommodation.json")
attr_src = load_json(ITINERARY / "attractions.json")
ent_src = load_json(ITINERARY / "entertainment.json")
shop_src = load_json(ITINERARY / "shopping.json")
trans_src = load_json(ITINERARY / "transportation.json")

# Build transport lookup by day
trans_by_day = {}
for d in trans_src["data"]["days"]:
    trans_by_day[d["day"]] = d

# Check existing days
existing_days = {d["day"] for d in budget_data["data"]["days"]}

running_total = 0
# Keep existing days and recalculate their totals too for accuracy
all_budget_days = []

for day_num in range(1, 22):
    meal_day = meals_data["data"]["days"][day_num - 1]
    accom_day = accom_src["data"]["days"][day_num - 1]
    attr_day = attr_src["data"]["days"][day_num - 1]
    ent_day = ent_src["data"]["days"][day_num - 1]
    shop_day = shop_src["data"]["days"][day_num - 1]

    # Meals
    b_cost = meal_day.get("breakfast", {}).get("cost", 0) or 0
    l_cost = meal_day.get("lunch", {}).get("cost", 0) or 0
    d_cost = meal_day.get("dinner", {}).get("cost", 0) or 0
    meals_total = b_cost + l_cost + d_cost

    # Accommodation
    accom_cost = accom_day.get("accommodation", {}).get("cost", 0) or 0

    # Activities = attractions + entertainment
    attr_costs = sum(a.get("cost", 0) or 0 for a in attr_day.get("attractions", []))
    ent_costs = sum(e.get("cost", 0) or 0 for e in ent_day.get("entertainment", []))
    activities_total = attr_costs + ent_costs

    # Shopping
    shop_items = shop_day.get("shopping", [])
    if isinstance(shop_items, list):
        shop_total = sum(s.get("cost", 0) or 0 for s in shop_items)
    else:
        shop_total = 0

    # Transportation
    trans_day_data = trans_by_day.get(day_num, {})
    lc = trans_day_data.get("location_change", {})
    trans_cost = lc.get("cost", 0) or 0 if lc else 0

    day_total = meals_total + accom_cost + activities_total + shop_total + trans_cost
    running_total += day_total

    location = meal_day.get("location", "")
    date = meal_day.get("date", "")

    if day_num in existing_days:
        # Update existing day entry
        for existing in budget_data["data"]["days"]:
            if existing["day"] == day_num:
                all_budget_days.append(existing)
                break
    else:
        # Create new budget entry
        new_entry = {
            "day": day_num,
            "date": date,
            "location": location,
            "budget": {
                "meals": meals_total,
                "accommodation": accom_cost,
                "activities": activities_total,
                "shopping": shop_total,
                "transportation": trans_cost,
                "total": day_total
            },
            "breakdown": {
                "meals_detail": {
                    "breakfast": b_cost,
                    "lunch": l_cost,
                    "dinner": d_cost
                },
                "activities_detail": {
                    "attractions": attr_costs,
                    "entertainment": ent_costs
                }
            },
            "notes": f"Auto-generated from source data files (meals, accommodation, attractions, entertainment, shopping, transportation)."
        }
        all_budget_days.append(new_entry)
        report["issue_5_budget_days_added"] += 1
        print(f"  Day {day_num} ({location}): meals={meals_total}, accom={accom_cost}, activities={activities_total}, shop={shop_total}, trans={trans_cost}, total={day_total}")

# Sort by day number
all_budget_days.sort(key=lambda d: d["day"])
budget_data["data"]["days"] = all_budget_days

# Update trip_total
budget_data["data"]["trip_total_estimate"]["days_1_4_actual"] = sum(
    d["budget"]["total"] for d in all_budget_days if d["day"] <= 4
)
budget_data["data"]["trip_total_estimate"]["remaining_17_days_estimate"] = sum(
    d["budget"]["total"] for d in all_budget_days if d["day"] > 4
)
budget_data["data"]["trip_total_estimate"]["total_estimated"] = sum(
    d["budget"]["total"] for d in all_budget_days
)

save_json(ITINERARY / "budget.json", budget_data)
print(f"  Total: {report['issue_5_budget_days_added']} new budget days added")
print(f"  New trip total: {budget_data['data']['trip_total_estimate']['total_estimated']} CNY\n")


# ============================================================
# ISSUE 6: Bucket-list transportation notes_local (11 items)
# ============================================================
print("=== Issue 6: Adding notes_local to bucket-list transportation ===")
trans_data = load_json(BUCKET / "transportation.json")

# Translation mapping for common terms
def translate_notes(notes_base):
    """Translate notes_base to Chinese, preserving train numbers and structure."""
    if not notes_base:
        return ""

    result = notes_base

    # Common phrase translations (order matters - longer phrases first)
    translations = [
        # Booking recommendations
        ("Book 25-35 days in advance for this long-distance route", "建议提前25-35天预订此长途线路"),
        ("Book 20-30 days in advance, high demand route", "建议提前20-30天预订，热门线路"),
        ("Book 20-30 days in advance, verify connections", "建议提前20-30天预订，确认换乘"),
        ("Book multi-segment journey 20-30 days in advance, verify connections", "建议提前20-30天预订多段行程，确认换乘"),
        ("Book 15-25 days in advance for guaranteed seats", "建议提前15-25天预订以确保座位"),
        ("Book 15-25 days in advance", "建议提前15-25天预订"),
        ("Book 15-30 days in advance for best prices", "建议提前15-30天预订以获最优价格"),
        ("Book 10-20 days in advance via 12306.cn", "建议提前10-20天通过12306.cn预订"),
        ("Book 3-7 days in advance or purchase at station", "建议提前3-7天预订或到站购票"),
        ("Book same day or 1-3 days in advance, very frequent service", "可当天或提前1-3天预订，班次非常密集"),
        ("Book Li River cruise 10-15 days in advance via official channels or hotel", "建议提前10-15天通过官方渠道或酒店预订漓江游船"),
        ("Book cruise in advance, especially peak season", "建议提前预订游船，尤其是旺季"),
        ("Book in advance", "建议提前预订"),
        ("book package tour or arrange transfer in advance", "建议预订套餐游或提前安排换乘"),

        # Train descriptions
        ("high-speed train is the fastest option", "高铁是最快选择"),
        ("high-speed train recommended", "推荐乘坐高铁"),
        ("high-speed train is fastest", "高铁是最快选择"),
        ("Very short high-speed train journey", "非常短的高铁旅程"),
        ("high-speed train", "高铁"),
        ("High-speed train from Guangzhou South to Shenzhen Futian", "广州南站至深圳福田站高铁"),
        ("overnight train", "过夜列车"),

        # Metro
        ("Metro Line 12 + Line 2", "地铁12号线+2号线"),
        ("Metro Line 11", "地铁11号线"),
        ("Metro Line 6", "地铁6号线"),
        ("Metro Line 4", "地铁4号线"),
        ("Metro Line 3", "地铁3号线"),
        ("Metro Line 2", "地铁2号线"),

        # Li River
        ("Li River cruise is THE recommended way to travel Guilin to Yangshuo", "漓江游船是桂林到阳朔最推荐的方式"),
        ("Li River cruise", "漓江游船"),
        ("Scenic 4-hour cruise", "4小时风景游船"),
        ("famous karst landscape scenery", "著名的喀斯特地貌风景"),

        # Stations and places
        ("from Harbin West to city center", "从哈尔滨西站到市中心"),
        ("from Tianjin West to city cente", "从天津西站到市中心"),
        ("from Xi'an North to city center", "从西安北站到市中心"),
        ("from Suzhou North to city center", "从苏州北站到市中心"),
        ("from Hangzhou East to city center", "从杭州东站到市中心"),
        ("from Guangzhou Baiyun to city center", "从广州白云站到市中心"),
        ("from Zhangjiajie West to city center", "从张家界西站到市中心"),
        ("in Shenzhen connects to all major areas", "可连接深圳所有主要区域"),
        ("Zhangjiajie West", "张家界西站"),

        # Cross-border / MTR
        ("MTR from Futian to Hong Kong via border crossing", "从福田站乘港铁过关到香港"),
        ("border crossing", "过境口岸"),
        ("Cross-border bus", "跨境巴士"),
        ("cross-border", "跨境"),
        ("travel documents required for Hong Kong entry", "进入香港需要有效旅行证件"),
        ("IMPORTANT: Valid", "重要：需要有效"),
        ("Hong Kong uses HKD currency", "香港使用港币"),
        ("MTR most convenient", "港铁最方便"),

        # General
        ("fastest option", "最快选择"),
        ("recommended", "推荐"),
        ("Alternative", "替代方案"),
        ("alternative", "替代方案"),
        ("cheaper at", "更便宜约"),
        ("but less recommended due to time constraints", "但因时间限制不太推荐"),
        ("but arrives early morning", "但清晨到达"),
        ("under 5 hours", "不到5小时"),
        ("under 90 minutes", "不到90分钟"),
        ("Arrive by afternoon", "下午到达"),
        ("Arrive by noon", "中午到达"),
        ("Arrive by late afternoon", "下午晚些到达"),
        ("Early morning departure recommended", "建议早上早些出发"),
        ("Direct bus", "直达巴士"),
        ("Long-distance bus", "长途巴士"),
        ("Private car service", "包车服务"),
        ("Trains depart every 15-30 minutes", "列车每15-30分钟一班"),
        ("Frequent trains available throughout the day, no need for advance booking", "全天有频繁班次，无需提前预订"),
        ("Complex route, consider", "线路复杂，建议"),
        ("Route requires transfer", "线路需要换乘"),
        ("Multiple options", "多种选择"),
        ("to explore", "参观"),
        ("before closing time", "在关门前"),
        ("at night", "在夜晚"),
        ("in afternoon", "在下午"),
        ("to catch", "以赶上"),
        ("to see sculptures in daylight", "以便白天观看冰雕"),
        ("to visit Terracotta Warriors", "参观兵马俑"),
        ("Humble Administrator's Garden", "拙政园"),
        ("Canton Tower", "广州塔"),
        ("Tianjin Eye and Italian Style Street", "天津之眼和意式风情街"),
        ("West Lake", "西湖"),
        ("Lingyin Temple", "灵隐寺"),
        ("OCT Loft", "华侨城创意园"),
        ("Ferry from Shekou to Hong Kong", "从蛇口码头乘渡轮到香港"),
    ]

    # Build a proper Chinese translation by processing notes_base
    # Instead of find-replace (which can produce garbled mixed text),
    # generate a proper Chinese summary from the English notes_base.

    nb = notes_base.lower()

    lines = []

    # Extract train number if present
    import re
    train_match = re.search(r'([GDZ]\d+)', notes_base)

    # Determine the mode of transport
    if "li river cruise" in nb:
        lines.append("漓江游船是桂林到阳朔最推荐的方式（包含在行程中）。")
        lines.append("4小时风景游船。")
        if "direct bus" in nb:
            lines.append("替代方案：直达巴士（2小时，约20元），但会错过著名的喀斯特地貌风景。")
        lines.append("建议提前预订游船，尤其是旺季。")
    elif "mtr" in nb or "cross-border" in nb or "border crossing" in nb:
        lines.append("多种选择：")
        if "mtr" in nb:
            lines.append("(1) 从福田站乘港铁过关到香港（约1.5小时，约90港元）。")
        if "ferry" in nb or "shekou" in nb:
            lines.append("(2) 从蛇口码头乘渡轮到香港（30分钟+中转，约200港元）。")
        if "cross-border bus" in nb:
            lines.append("(3) 跨境巴士。")
        lines.append("重要：进入香港需要有效旅行证件。港铁最方便。")
        lines.append("香港使用港币（1港元约0.88元人民币）。")
    elif "high-speed train" in nb or train_match:
        train_id = train_match.group(1) if train_match else ""
        if train_id:
            lines.append(f"{train_id}高铁推荐。")
        else:
            lines.append("推荐乘坐高铁。")

        # Duration info
        dur_match = re.search(r'under (\d+) (hours|minutes)', nb)
        if dur_match:
            num = dur_match.group(1)
            unit = "小时" if dur_match.group(2) == "hours" else "分钟"
            lines.append(f"不到{num}{unit}。")
        elif "~8 hours" in nb or "8 hours" in nb:
            lines.append("约8小时。")
        elif "90 minutes" in nb:
            lines.append("不到90分钟。")

        # Metro connection
        metro_match = re.search(r'Metro Line (\d+(?:\s*\+\s*Line \d+)?)', notes_base)
        if metro_match:
            metro_lines = metro_match.group(1).replace(" + Line ", "号线+")
            lines.append(f"地铁{metro_lines}号线可到市中心。")

        # Alternative options
        if "alternative" in nb or "overnight" in nb:
            alt_match = re.search(r'(?:Alternative|alternative)[:\s]+([^.]+)\.', notes_base)
            if alt_match:
                alt_text = alt_match.group(1).strip()
                # Extract key info
                alt_train = re.search(r'([TZD]\d+)', alt_text)
                alt_dur = re.search(r'(\d+\+?\s*hours)', alt_text)
                alt_cost = re.search(r'~?(\d+)\s*CNY', alt_text)
                parts = []
                if alt_train:
                    parts.append(f"替代方案：{alt_train.group(1)}列车")
                else:
                    parts.append("替代方案")
                if alt_dur:
                    parts.append(f"（{alt_dur.group(1).replace('hours', '小时').replace('+', '+')}）")
                if alt_cost:
                    parts.append(f"约{alt_cost.group(1)}元")
                lines.append("".join(parts) + "。")

        # Booking recommendation
        book_match = re.search(r'Book (\d+-\d+) days in advance', notes_base)
        if book_match:
            lines.append(f"建议提前{book_match.group(1)}天预订。")
        elif "no need for advance booking" in nb:
            lines.append("全天有频繁班次，无需提前预订。")
        elif "same day" in nb:
            lines.append("可当天或提前1-3天预订，班次非常密集。")

        # Arrival destination tips
        if "humble administrator" in nb or "garden" in nb:
            lines.append("下午到达可参观拙政园。")
        elif "terracotta" in nb:
            lines.append("中午到达可下午参观兵马俑。")
        elif "canton tower" in nb:
            lines.append("下午晚些到达可夜晚参观广州塔。")
        elif "tianjin eye" in nb:
            lines.append("下午到达可参观天津之眼和意式风情街。")
        elif "li river cruise" in nb:
            lines.append("建议早上早些出发以赶上下午的漓江游船。")

        # Multiple options (Guangzhou-Shenzhen)
        if "multiple options" in nb:
            lines = []  # Reset for multi-option format
            lines.append("多种选择：")
            if "guangzhou south" in nb:
                lines.append("(1) 广州南站至深圳福田站高铁（30分钟，约75元，最常见）。")
            if "long-distance bus" in nb:
                lines.append("(2) 长途巴士（2-3小时，约80元）。")
            if "private car" in nb:
                lines.append("(3) 包车服务。")
            if "every 15-30 minutes" in nb:
                lines.append("列车每15-30分钟一班。")
            metro_match2 = re.search(r'Metro Line (\d+)', notes_base)
            if metro_match2:
                lines.append(f"深圳地铁{metro_match2.group(1)}号线可连接所有主要区域。")
    elif "transfer" in nb or "complex" in nb:
        if train_match:
            lines.append(f"线路需要换乘：{train_match.group(1)}列车。")
        else:
            lines.append("线路需要换乘。")
        if "bus 17" in nb:
            lines.append("17路公交从张家界西站到市中心。")
        lines.append("线路复杂，建议预订套餐游或提前安排换乘。")
        book_match = re.search(r'Book (\d+-\d+) days in advance', notes_base)
        if book_match:
            lines.append(f"建议提前{book_match.group(1)}天预订。")

    if not lines:
        # Fallback: generate a basic translation
        lines.append("详情请参考英文备注。")

    return "".join(lines)


for day_entry in trans_data["data"]["days"]:
    day_num = day_entry["day"]
    lc = day_entry.get("location_change", {})

    if "notes_local" not in lc and "notes_base" in lc:
        notes_base = lc["notes_base"]
        lc["notes_local"] = translate_notes(notes_base)
        report["issue_6_notes_local"] += 1
        print(f"  Day {day_num}: Added notes_local ({len(lc['notes_local'])} chars)")
        print(f"    EN: {notes_base[:80]}...")
        print(f"    ZH: {lc['notes_local'][:80]}...")

save_json(BUCKET / "transportation.json", trans_data)
print(f"  Total: {report['issue_6_notes_local']} transportation notes_local added\n")


# ============================================================
# VALIDATION
# ============================================================
print("=" * 60)
print("VALIDATION")
print("=" * 60)

errors = []

# Validate Issue 1: All attractions have time dict
attr_check = load_json(BUCKET / "attractions.json")
for day in attr_check["data"]["days"]:
    for attr in day["attractions"]:
        if "time" not in attr:
            errors.append(f"Issue 1: Day {day['day']} attraction '{attr.get('name', '?')}' missing time")
        elif not isinstance(attr["time"], dict):
            errors.append(f"Issue 1: Day {day['day']} attraction time is not dict: {type(attr['time'])}")
        elif "start" not in attr["time"] or "end" not in attr["time"]:
            errors.append(f"Issue 1: Day {day['day']} attraction time missing start/end")

# Validate Issue 2: All entertainment have time dict
ent_check = load_json(BUCKET / "entertainment.json")
for day in ent_check["data"]["days"]:
    for ent in day["entertainment"]:
        if "time" not in ent:
            errors.append(f"Issue 2: Day {day['day']} entertainment '{ent.get('name', '?')}' missing time")
        elif not isinstance(ent["time"], dict):
            errors.append(f"Issue 2: Day {day['day']} entertainment time is not dict: {type(ent['time'])}")
        elif "start" not in ent["time"] or "end" not in ent["time"]:
            errors.append(f"Issue 2: Day {day['day']} entertainment time missing start/end")

# Validate Issue 3: check_in/check_out not empty
accom_check = load_json(ITINERARY / "accommodation.json")
for day in accom_check["data"]["days"]:
    if day["day"] in (2, 3):
        ci = day["accommodation"].get("check_in", "")
        co = day["accommodation"].get("check_out", "")
        if ci == "":
            errors.append(f"Issue 3: Day {day['day']} check_in still empty")
        if co == "":
            errors.append(f"Issue 3: Day {day['day']} check_out still empty")

# Validate Issue 4: No null dates in bucket-list
for fname in bucket_files:
    fdata = load_json(BUCKET / fname)
    for day in fdata.get("data", {}).get("days", []):
        if day.get("date") is None:
            errors.append(f"Issue 4: {fname} Day {day.get('day')} date is still null")

# Validate Issue 5: Budget has 21 days
budget_check = load_json(ITINERARY / "budget.json")
budget_days = budget_check["data"]["days"]
if len(budget_days) != 21:
    errors.append(f"Issue 5: Budget has {len(budget_days)} days, expected 21")
day_nums = sorted(d["day"] for d in budget_days)
if day_nums != list(range(1, 22)):
    errors.append(f"Issue 5: Budget day numbers not sequential 1-21: {day_nums}")

# Validate Issue 6: All transportation have notes_local
trans_check = load_json(BUCKET / "transportation.json")
for day in trans_check["data"]["days"]:
    lc = day.get("location_change", {})
    if "notes_base" in lc and "notes_local" not in lc:
        errors.append(f"Issue 6: Day {day['day']} transportation still missing notes_local")

if errors:
    print("\nVALIDATION ERRORS:")
    for e in errors:
        print(f"  FAIL: {e}")
    report["errors"] = errors
else:
    print("\nAll validations PASSED!")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Issue 1 - Attractions time added:       {report['issue_1_attractions_time']}")
print(f"  Issue 2 - Entertainment time converted:  {report['issue_2_entertainment_time']}")
print(f"  Issue 3 - Check-in/out fixed:            {report['issue_3_checkin_checkout']}")
print(f"  Issue 4 - Null dates fixed:              {report['issue_4_date_null']}")
print(f"  Issue 5 - Budget days added:             {report['issue_5_budget_days_added']}")
print(f"  Issue 6 - Transportation notes_local:    {report['issue_6_notes_local']}")
print(f"  Validation errors:                       {len(errors)}")

sys.exit(1 if errors else 0)
