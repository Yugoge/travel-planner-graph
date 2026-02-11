#!/usr/bin/env python3
"""Fix missing localization fields in travel planner JSON data files.

Issue 1: Add notes_local (Chinese translations) to 11 transportation items
         that have notes_base but no notes_local.
Issue 2: Add check_in/check_out times to 2 accommodation items (residential
         apartments) that have empty values.

Usage:
    python fix-missing-localization.py <transportation_json> <accommodation_json>
"""

import json
import sys
from pathlib import Path


def translate_transportation_notes(notes_base: str) -> str:
    """Translate transportation notes_base from English to Chinese.

    Uses domain-specific translation for travel/transit terminology.
    Keeps train numbers, prices, and proper nouns as-is.
    """
    # Map each day's notes_base to its Chinese translation
    # Each translation is crafted from the full notes_base content
    translations = {
        "G105 high-speed train is the fastest option. Book 2-3 weeks in advance for best prices. Alternative: T47 overnight train (13 hours, cheaper at ~250 CNY but arrives early morning). Metro Line 3 from Harbin West to city center (~20 min).":
            "G105高铁是最快选择。建议提前2-3周预订以获最优价格。备选：T47夜间列车（13小时，约250元较便宜但凌晨到达）。地铁3号线从哈尔滨西站到市中心（约20分钟）。",

        "G2644 high-speed train recommended. Metro Line 6 from Tianjin West to city center (Tianjin Binjiang). Alternative slower train Z238 available (12+ hours, ~280 CNY). Arrive by afternoon to explore Tianjin Eye and Italian Style Street.":
            "推荐G2644高铁。地铁6号线从天津西站到市中心（天津滨江道）。备选较慢列车Z238（12小时以上，约280元）。下午到达可游览天津之眼和意式风情街。",

        "G1293 high-speed train is fastest (under 5 hours). Metro Line 4 from Xi'an North to city center. Overnight train T58 available (14+ hours, ~320 CNY) but less recommended due to time constraints. Arrive by noon to visit Terracotta Warriors in afternoon.":
            "G1293高铁是最快选择（不到5小时）。地铁4号线从西安北站到市中心。夜间列车T58可选（14小时以上，约320元）但因时间紧张不太推荐。中午到达，下午可参观兵马俑。",

        "G4876 high-speed train recommended. Metro Line 2 from Suzhou North to city center (take to Guangji South Rd). Overnight train Z306 available (15+ hours, ~400 CNY). Arrive by afternoon to explore Humble Administrator's Garden before closing time.":
            "推荐G4876高铁。地铁2号线从苏州北站到市中心（乘至广济南路站）。夜间列车Z306可选（15小时以上，约400元）。下午到达可在闭园前游览拙政园。",

        "Very short high-speed train journey (under 90 minutes). Metro Line 4 from Hangzhou East to city center. Frequent trains available throughout the day, no need for advance booking. Can depart mid-morning and still have full day in Hangzhou.":
            "高铁车程很短（不到90分钟）。地铁4号线从杭州东站到市中心。全天班次频繁，无需提前预订。上午出发仍可在杭州游玩一整天。",

        "G263 high-speed train is fastest option (~8 hours). Alternative: overnight train D195 from Hangzhou South via Shanghai South (16+ hours, ~480 CNY). Early morning departure recommended to catch Li River cruise in afternoon. Bus K2 or taxi from Guilin North to cruise departure point.":
            "G263高铁是最快选择（约8小时）。备选：D195夜间列车从杭州南经上海南（16小时以上，约480元）。推荐早班出发以便下午赶上漓江游船。从桂林北站乘K2路公交或出租车到游船码头。",

        "Li River cruise is THE recommended way to travel Guilin to Yangshuo (included in itinerary plans). Scenic 4-hour cruise. Alternative: Direct bus (2 hours, 80 KM, ~20 CNY) but misses the famous karst landscape scenery. Book cruise in advance, especially peak season.":
            "漓江游船是从桂林到阳朔最推荐的出行方式（已列入行程计划）。4小时观光游船。备选：直达大巴（2小时，80公里，约20元）但会错过著名喀斯特山水风光。建议提前预订游船，旺季尤其重要。",

        "Route requires transfer: Yangshuo → Guilin → Nanning → Zhangjiajie West. Alternative direct bus from Yangshuo to Guilin (1.5 hours), then D3968 train from Guilin. Bus 17 from Zhangjiajie West to city center. Complex route, consider booking package tour or arrange transfer in advance.":
            "该路线需要换乘：阳朔 → 桂林 → 南宁 → 张家界西。备选：阳朔直达大巴到桂林（1.5小时），再从桂林乘D3968列车。17路公交从张家界西站到市中心。路线复杂，建议预订旅行套餐或提前安排换乘。",

        "G6115 high-speed train recommended. Metro Line 12 + Line 2 from Guangzhou Baiyun to city center. Overnight train Z235 available (16+ hours, ~350 CNY). Arrive by late afternoon to explore Canton Tower at night.":
            "推荐G6115高铁。地铁12号线换乘2号线从广州白云站到市中心。夜间列车Z235可选（16小时以上，约350元）。傍晚到达，晚上可游览广州塔。",

        "Multiple options: (1) High-speed train from Guangzhou South to Shenzhen Futian (30 min, ~75 CNY, most common), (2) Long-distance bus (2-3 hours, ~80 CNY), (3) Private car service. Trains depart every 15-30 minutes. Metro Line 11 in Shenzhen connects to all major areas.":
            "多种选择：(1) 广州南站到深圳福田高铁（30分钟，约75元，最常见），(2) 长途大巴（2-3小时，约80元），(3) 包车服务。高铁每15-30分钟一班。深圳地铁11号线连接各主要区域。",

        "Multiple options: (1) MTR from Futian to Hong Kong via border crossing (1.5 hours, ~90 HKD), (2) Ferry from Shekou to Hong Kong Airport/Central (30 min + transit, ~200 HKD), (3) Cross-border bus. IMPORTANT: Valid travel documents required for Hong Kong entry. MTR most convenient. Hong Kong uses HKD currency (1 HKD ≈ 0.88 CNY).":
            "多种选择：(1) 从福田乘港铁经过境口岸到香港（1.5小时，约90港币），(2) 蛇口渡轮到香港机场/中环（30分钟+中转，约200港币），(3) 跨境巴士。重要提示：入境香港需持有效旅行证件。港铁最方便。香港使用港币（1港币 ≈ 0.88元人民币）。",
    }

    if notes_base in translations:
        return translations[notes_base]

    # Fallback: return empty string if no match found (should not happen)
    print(f"  WARNING: No translation found for notes_base: {notes_base[:60]}...")
    return ""


def fix_transportation_notes_local(file_path: str) -> int:
    """Add notes_local to transportation items missing it.

    Returns number of items fixed.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixed_count = 0

    for day_entry in data.get("data", {}).get("days", []):
        loc_change = day_entry.get("location_change")
        if not loc_change:
            continue

        notes_base = loc_change.get("notes_base", "")
        notes_local = loc_change.get("notes_local", "")

        if notes_base and not notes_local:
            translation = translate_transportation_notes(notes_base)
            if translation:
                loc_change["notes_local"] = translation
                fixed_count += 1
                day_num = day_entry.get("day", "?")
                from_city = loc_change.get("from_base", "?")
                to_city = loc_change.get("to_base", "?")
                print(f"  Fixed Day {day_num}: {from_city} -> {to_city}")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return fixed_count


def fix_accommodation_check_times(file_path: str) -> int:
    """Add check_in/check_out to accommodation items with empty values.

    Targets residential/family apartments that should have standard times.
    Returns number of items fixed.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixed_count = 0

    # Target names for the two specific items
    target_names = {
        "Banshan Yicheng Residential Complex",
        "Xijin International Residential Complex",
    }

    for day_entry in data.get("data", {}).get("days", []):
        accommodation = day_entry.get("accommodation")
        if not accommodation:
            continue

        name = accommodation.get("name_base", "")
        if name not in target_names:
            continue

        check_in = accommodation.get("check_in", "")
        check_out = accommodation.get("check_out", "")

        if not check_in or not check_out:
            accommodation["check_in"] = "14:00"
            accommodation["check_out"] = "12:00"
            fixed_count += 1
            day_num = day_entry.get("day", "?")
            print(f"  Fixed Day {day_num}: {name} -> check_in=14:00, check_out=12:00")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return fixed_count


def validate_transportation(file_path: str) -> list:
    """Validate all transportation items have notes_local when notes_base exists."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors = []
    for day_entry in data.get("data", {}).get("days", []):
        loc_change = day_entry.get("location_change")
        if not loc_change:
            continue

        day_num = day_entry.get("day", "?")
        notes_base = loc_change.get("notes_base", "")
        notes_local = loc_change.get("notes_local", "")

        if notes_base and not notes_local:
            errors.append(f"Day {day_num}: has notes_base but missing notes_local")

    return errors


def validate_accommodation(file_path: str) -> list:
    """Validate targeted accommodation items have check_in/check_out."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors = []
    target_names = {
        "Banshan Yicheng Residential Complex",
        "Xijin International Residential Complex",
    }

    for day_entry in data.get("data", {}).get("days", []):
        accommodation = day_entry.get("accommodation")
        if not accommodation:
            continue

        name = accommodation.get("name_base", "")
        if name not in target_names:
            continue

        day_num = day_entry.get("day", "?")
        check_in = accommodation.get("check_in", "")
        check_out = accommodation.get("check_out", "")

        if not check_in:
            errors.append(f"Day {day_num}: {name} missing check_in")
        if not check_out:
            errors.append(f"Day {day_num}: {name} missing check_out")

    return errors


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <transportation_json> <accommodation_json>")
        sys.exit(1)

    transport_path = sys.argv[1]
    accommodation_path = sys.argv[2]

    # Validate input files exist
    for path in [transport_path, accommodation_path]:
        if not Path(path).exists():
            print(f"Error: File not found: {path}")
            sys.exit(1)

    # Step 1: Fix transportation notes_local
    print("=" * 60)
    print("Issue 1: Adding notes_local to transportation items")
    print("=" * 60)
    transport_fixed = fix_transportation_notes_local(transport_path)
    print(f"\nFixed {transport_fixed} transportation items.\n")

    # Step 2: Fix accommodation check_in/check_out
    print("=" * 60)
    print("Issue 2: Adding check_in/check_out to accommodation items")
    print("=" * 60)
    accommodation_fixed = fix_accommodation_check_times(accommodation_path)
    print(f"\nFixed {accommodation_fixed} accommodation items.\n")

    # Step 3: Validate
    print("=" * 60)
    print("Validation")
    print("=" * 60)

    transport_errors = validate_transportation(transport_path)
    accommodation_errors = validate_accommodation(accommodation_path)

    all_errors = transport_errors + accommodation_errors

    if all_errors:
        print("VALIDATION FAILED:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("  Transportation: All 11 items have notes_local -- PASS")
        print("  Accommodation: Both items have check_in/check_out -- PASS")
        print("\nAll validations passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
