#!/usr/bin/env python3
"""Fix accommodation agent data for both trips by adding missing fields."""

import json
import sys
from pathlib import Path

# === Translation maps ===
AMENITY_TRANSLATIONS = {
    "WiFi": "WiFi",
    "Air Conditioning": "空调",
    "Air conditioning": "空调",
    "Breakfast": "早餐",
    "Breakfast included": "含早餐",
    "Breakfast buffet": "自助早餐",
    "Breakfast available": "可选早餐",
    "Basic breakfast": "简易早餐",
    "Parking": "停车场",
    "Swimming Pool": "游泳池",
    "Swimming pool": "游泳池",
    "Gym": "健身房",
    "Gym and pool": "健身房和游泳池",
    "Free gym": "免费健身房",
    "Laundry": "洗衣服务",
    "Free laundry service": "免费洗衣服务",
    "Free laundry facilities": "免费洗衣设施",
    "Room Service": "客房服务",
    "Kitchen": "厨房",
    "Full kitchen": "完整厨房",
    "Washer": "洗衣机",
    "Washing machine": "洗衣机",
    "TV": "电视",
    "Refrigerator": "冰箱",
    "Elevator": "电梯",
    "24-hour Front Desk": "24小时前台",
    "24-hour front desk": "24小时前台",
    "Luggage Storage": "行李寄存",
    "Luggage storage": "行李寄存",
    "Free Parking": "免费停车",
    "Hot Water": "热水",
    "Heating": "暖气",
    "Central heating": "中央暖气",
    "Private Bathroom": "独立卫浴",
    "Non-smoking Rooms": "无烟房",
    "Pet Friendly": "允许宠物",
    "Balcony": "阳台",
    "Private residence": "私人住宅",
    "Family hospitality": "家庭接待",
    "Home-cooked meals": "家常菜",
    "Chinese New Year celebration": "春节庆祝",
    "Central location near Taikoo Li": "靠近太古里的中心位置",
    "Smart room controls": "智能房间控制",
    "Café and bar": "咖啡厅和酒吧",
    "Robot service": "机器人服务",
    "Near Nanjing Road Pedestrian Street (400m)": "距南京路步行街400米",
    "Near Nanjing Road Pedestrian Street": "靠近南京路步行街",
    "Walking distance to The Bund": "步行可达外滩",
    "Wake-up service": "叫醒服务",
    "Budget-friendly": "经济实惠",
    "Near universities": "靠近大学",
    "Living space": "客厅",
    "Bedroom(s)": "卧室",
    "River views": "江景",
    "In-building observation deck": "楼内观景台",
    "Spa services": "水疗服务",
    "Club lounge": "行政酒廊",
    "Restaurant": "餐厅",
    "Near Zhongyang Street": "靠近中央大街",
    "Central location": "中心位置",
    "Italian-style architecture views": "意大利风格建筑景观",
    "Pool table & lounge": "台球和休息室",
    "Karaoke booth": "KTV包间",
    "Walking distance to Bell Tower": "步行可达钟楼",
    "Traditional Chinese architecture": "中式传统建筑",
    "Near Humble Administrator's Garden": "靠近拙政园",
    "Canal-side location": "运河旁位置",
    "Modern rooms": "现代客房",
    "Near West Lake": "靠近西湖",
    "Work cubicles with views": "带景观的工作间",
    "Restaurant with Western food": "提供西餐的餐厅",
    "Free bike rental": "免费自行车租借",
    "Free shuttle to town": "免费接驳班车",
    "Garden views": "花园景观",
    "New property (2025)": "2025年新开业",
    "Fitness center": "健身中心",
    "Near metro station": "靠近地铁站",
    "Spacious rooms": "宽敞客房",
    "Living room area": "客厅区域",
    "Adjacent to shopping mall": "紧邻购物中心",
    "Laojie metro station nearby": "靠近老街地铁站",
    "Renovated rooms available": "可选翻新房间",
    "Rooftop bar": "天台酒吧",
    "Near MTR station": "靠近港铁站",
}

# Fallback: if exact match not found, try prefix matching or return original
def translate_amenity(amenity_en):
    if amenity_en in AMENITY_TRANSLATIONS:
        return AMENITY_TRANSLATIONS[amenity_en]
    # Try case-insensitive
    for k, v in AMENITY_TRANSLATIONS.items():
        if k.lower() == amenity_en.lower():
            return v
    # Check if it starts with a known key (for things like "Breakfast buffet (CNY 228/adult)")
    for k, v in AMENITY_TRANSLATIONS.items():
        if amenity_en.lower().startswith(k.lower()):
            return v
    # Return as-is (untranslatable unique items)
    return amenity_en


TYPE_TRANSLATIONS = {
    "hotel": "酒店",
    "Hotel": "酒店",
    "boutique_hotel": "精品酒店",
    "Boutique Hotel": "精品酒店",
    "budget_hotel": "经济酒店",
    "resort": "度假村",
    "Resort Hotel": "度假酒店",
    "guesthouse": "民宿",
    "hostel": "青年旅舍",
    "Family Home Stay": "家庭住宿",
    "Vacation Rental / Short-term Apartment": "度假短租公寓",
}


def translate_type(type_en):
    if type_en in TYPE_TRANSLATIONS:
        return TYPE_TRANSLATIONS[type_en]
    for k, v in TYPE_TRANSLATIONS.items():
        if k.lower() == type_en.lower():
            return v
    return type_en


# === Trip 1: Star ratings based on name/type ===
def get_trip1_stars(name_base, type_base):
    name = name_base.lower() if name_base else ""
    t = type_base.lower() if type_base else ""

    # Family homes / residential
    if "family" in t or "residential" in name or "banshan" in name or "xijin" in name:
        return None
    # Serviced apartments / short-term rental
    if "rental" in t or "apartment" in t or "short-term" in name.lower():
        return None
    # Luxury
    if "intercontinental" in name or "jw marriott" in name or "disneyland hotel" in name:
        return 5
    # Upper mid-range
    if "hilton garden" in name or "hyatt place" in name:
        return 4
    # Mid-range
    if "atour" in name or "moxy" in name or "holiday inn express" in name or "sk lusso" in name:
        return 3
    # Budget/Express
    if "orange" in name or "home inn" in name or "7days" in name or "7 days" in name:
        return 2
    # Hostels
    if "hostel" in t:
        return 1
    # Default mid-range for generic hotels
    return 3


# === Trip 2: Star ratings (explicit from task) ===
TRIP2_STARS = {
    "Harbin Wei Ye Hotel": 3,
    "Kind Hotel Tianjin": 3,
    "Moxy Xi'an Downtown": 3,
    "Scholars Hotel PingJiangFu Suzhou": 4,
    "Hangzhou West Lake Hubin Yintai Atour Hotel": 4,
    "Holiday Inn Express Guilin City Center": 3,
    "The Bamboo Leaf Yangshuo": 3,
    "Hilton Garden Inn Zhangjiajie Wulingyuan": 4,
    "ARTHUR HOTEL CANTON TOWER GUANGZHOU": 3,
    "Hyatt Place Shenzhen Dongmen": 4,
    "Holiday Inn Golden Mile Hong Kong": 4,
}

TRIP2_NAME_LOCAL = {
    "Harbin Wei Ye Hotel": "哈尔滨威业酒店",
    "Kind Hotel Tianjin": "天津凯德酒店",
    "Moxy Xi'an Downtown": "西安市中心万豪Moxy酒店",
    "Scholars Hotel PingJiangFu Suzhou": "苏州平江府书香世家酒店",
    "Hangzhou West Lake Hubin Yintai Atour Hotel": "杭州西湖湖滨银泰亚朵酒店",
    "Holiday Inn Express Guilin City Center": "桂林市中心智选假日酒店",
    "The Bamboo Leaf Yangshuo": "阳朔竹叶居",
    "Hilton Garden Inn Zhangjiajie Wulingyuan": "张家界武陵源希尔顿花园酒店",
    "ARTHUR HOTEL CANTON TOWER GUANGZHOU": "广州广州塔亚瑟酒店",
    "Hyatt Place Shenzhen Dongmen": "深圳东门凯悦嘉轩酒店",
    "Holiday Inn Golden Mile Hong Kong": "香港金域假日酒店",
}

TRIP2_NOTES_LOCAL = {
    "Harbin Wei Ye Hotel_1": "位于哈尔滨市中心，靠近东正教堂遗址和中央大街。步行5分钟即达冰雪大世界区域。安全社区，可方便前往俄式建筑区。旅客评分4.5/5。",
    "Harbin Wei Ye Hotel_2": "同一酒店第二晚。步行可达太阳岛公园和东北虎林园。探索东北菜餐厅的便利基地。",
    "Kind Hotel Tianjin": "位于意式风情街上的绝佳位置。步行可达天津之眼（3公里）、古文化街和五大道。评分5/5。安静、维护良好。",
    "Moxy Xi'an Downtown_1": "位于钟楼和回民街附近的现代精品酒店。步行5分钟可达钟楼地铁站。评分4.8/5，服务获赞。免费洗衣房配有洗衣机和烘干机。适合独行旅客。靠近夜市。",
    "Moxy Xi'an Downtown_2": "西安第二晚住同一酒店。方便游览城墙骑行、大雁塔和陕西历史博物馆。靠近大唐不夜城。",
    "Scholars Hotel PingJiangFu Suzhou": "靠近平江路古街和运河的中式传统风格酒店。步行3分钟到拙政园。旁边是购物区，运河景色如画。参观苏州博物馆的绝佳位置。评分4.4/5。",
    "Hangzhou West Lake Hubin Yintai Atour Hotel": "靠近西湖景区的热门地段。步行20分钟到湖滨银泰和西湖湖滨。早餐服务出色。游览灵隐寺和龙井茶村的良好基地。评分4.7/5。设施现代。",
    "Holiday Inn Express Guilin City Center": "位于主要美食和购物区旁的绝佳中心位置。正对人民广场。步行5分钟到漓江出发点。早餐楼层设有免费自助洗衣房。房间宽敞。评分4.4/5。适合早起出发漓江游船。",
    "The Bamboo Leaf Yangshuo": "距漓江游船下船点步行8分钟的宁静度假酒店。步行20分钟或骑行可达阳朔镇和西街。游泳池和优秀餐厅。英语服务员非常热心。免费自行车可骑行十里画廊。评分4.7/5。遇龙河漂流的理想基地。",
    "Hilton Garden Inn Zhangjiajie Wulingyuan": "2025年新开业酒店，位于武陵源区靠近国家森林公园入口。服务出色，工作人员可帮忙安排门票和交通。早餐优秀。房间超大宽敞。免费洗衣机。游览阿凡达哈利路亚山和天子山缆车的理想位置。评分4.7/5。",
    "ARTHUR HOTEL CANTON TOWER GUANGZHOU": "距广州塔一站地铁的绝佳位置。非常靠近客村地铁站（B出口）。步行可达广州塔和珠江。设施现代，前台服务热情。评分4.5/5。适合前往沙面岛和陈家祠后乘高铁去深圳。",
    "Hyatt Place Shenzhen Dongmen": "超大房间配大床和客厅区域。距老街地铁站（H出口）不到100米。位于东门步行街1234Space购物中心内。罗湖口岸过关去香港仅两站地铁。含每日早餐。评分4.3/5。",
    "Holiday Inn Golden Mile Hong Kong": "位于尖沙咀港铁站（N5出口）的黄金地段。步行可达山顶缆车、天星小轮和庙街夜市。尖沙咀购物区中心。方便一日游前往大屿山（天坛大佛）和乘船去澳门。评分4.1/5。如有翻新房间建议预订。",
}

# Check-in/out for Trip 2 (luxury = 15:00/12:00, budget = 14:00/11:00, standard = 14:00/12:00)
TRIP2_CHECKIN = {
    "Harbin Wei Ye Hotel": ("14:00", "12:00"),
    "Kind Hotel Tianjin": ("14:00", "12:00"),
    "Moxy Xi'an Downtown": ("15:00", "12:00"),
    "Scholars Hotel PingJiangFu Suzhou": ("14:00", "12:00"),
    "Hangzhou West Lake Hubin Yintai Atour Hotel": ("14:00", "12:00"),
    "Holiday Inn Express Guilin City Center": ("14:00", "12:00"),
    "The Bamboo Leaf Yangshuo": ("14:00", "12:00"),
    "Hilton Garden Inn Zhangjiajie Wulingyuan": ("14:00", "12:00"),
    "ARTHUR HOTEL CANTON TOWER GUANGZHOU": ("14:00", "12:00"),
    "Hyatt Place Shenzhen Dongmen": ("15:00", "12:00"),
    "Holiday Inn Golden Mile Hong Kong": ("14:00", "12:00"),
}


def fix_trip1(file_path):
    """Fix Trip 1: Add amenities_local, stars; remove deprecated rating."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for day_entry in data["data"]["days"]:
        acc = day_entry["accommodation"]

        # Determine source amenities field
        amenities_source = acc.get("amenities_base") or acc.get("amenities") or []

        # Add amenities_local (translate each amenity)
        acc["amenities_local"] = [translate_amenity(a) for a in amenities_source]

        # Add stars based on name/type
        name_base = acc.get("name_base", "")
        type_base = acc.get("type", "") or acc.get("type_base", "")
        acc["stars"] = get_trip1_stars(name_base, type_base)

        # Remove deprecated "rating" field
        if "rating" in acc:
            del acc["rating"]

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Trip 1: Fixed {len(data['data']['days'])} days in {file_path}")
    return len(data["data"]["days"])


def fix_trip2(file_path):
    """Fix Trip 2: Add name_local, type_local, type_base, amenities_base,
    amenities_local, notes_local, stars, check_in, check_out; remove deprecated fields."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for day_entry in data["data"]["days"]:
        acc = day_entry["accommodation"]
        name_base = acc.get("name_base") or acc.get("name", "")
        day_num = day_entry.get("day", 0)

        # Ensure name_base exists (some may only have "name")
        if "name_base" not in acc and "name" in acc:
            acc["name_base"] = acc["name"]

        # Add name_local
        if name_base in TRIP2_NAME_LOCAL:
            acc["name_local"] = TRIP2_NAME_LOCAL[name_base]

        # Add type_base from existing "type" field
        if "type_base" not in acc and "type" in acc:
            acc["type_base"] = acc["type"]

        # Add type_local
        type_val = acc.get("type_base") or acc.get("type", "")
        acc["type_local"] = translate_type(type_val)

        # Ensure amenities_base exists (from "amenities")
        if "amenities_base" not in acc and "amenities" in acc:
            acc["amenities_base"] = acc["amenities"]

        # Add amenities_local
        amenities_source = acc.get("amenities_base") or acc.get("amenities") or []
        acc["amenities_local"] = [translate_amenity(a) for a in amenities_source]

        # Add notes_local (use lookup with day disambiguation for repeated hotels)
        notes_key = name_base
        if name_base == "Harbin Wei Ye Hotel":
            notes_key = f"Harbin Wei Ye Hotel_{day_num}"
        elif name_base == "Moxy Xi'an Downtown":
            notes_key = f"Moxy Xi'an Downtown_{day_num - 3}"  # day 4 -> _1, day 5 -> _2

        if notes_key in TRIP2_NOTES_LOCAL:
            acc["notes_local"] = TRIP2_NOTES_LOCAL[notes_key]
        elif name_base in TRIP2_NOTES_LOCAL:
            acc["notes_local"] = TRIP2_NOTES_LOCAL[name_base]

        # Ensure notes_base exists (from "notes")
        if "notes_base" not in acc and "notes" in acc:
            acc["notes_base"] = acc["notes"]

        # Add stars
        if name_base in TRIP2_STARS:
            acc["stars"] = TRIP2_STARS[name_base]

        # Add check_in / check_out
        if name_base in TRIP2_CHECKIN:
            acc["check_in"] = TRIP2_CHECKIN[name_base][0]
            acc["check_out"] = TRIP2_CHECKIN[name_base][1]

        # Remove deprecated fields
        if "rating" in acc:
            del acc["rating"]
        if "star_rating" in acc:
            del acc["star_rating"]

        # Ensure currency_local exists (required by schema)
        if "currency_local" not in acc:
            acc["currency_local"] = acc.get("currency", "CNY")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Trip 2: Fixed {len(data['data']['days'])} days in {file_path}")
    return len(data["data"]["days"])


def validate_json(file_path):
    """Validate that the file is valid JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"VALID JSON: {file_path}")

        # Check all days have required fields
        required = ["name_base", "location_base", "cost"]
        for day_entry in data["data"]["days"]:
            acc = day_entry["accommodation"]
            day = day_entry.get("day", "?")
            for field in required:
                if field not in acc:
                    print(f"  WARNING: Day {day} missing required field: {field}")

            # Check new fields exist
            if "amenities_local" not in acc:
                print(f"  WARNING: Day {day} missing amenities_local")
            if "stars" not in acc:
                print(f"  WARNING: Day {day} missing stars")

        return True
    except json.JSONDecodeError as e:
        print(f"INVALID JSON: {file_path} - {e}")
        return False


if __name__ == "__main__":
    trip1_path = "/root/travel-planner/data/china-feb-15-mar-7-2026-20260202-195429/accommodation.json"
    trip2_path = "/root/travel-planner/data/beijing-exchange-bucket-list-20260202-232405/accommodation.json"

    print("=" * 60)
    print("Fixing Trip 1 (China Feb 15 - Mar 7)")
    print("=" * 60)
    fix_trip1(trip1_path)

    print()
    print("=" * 60)
    print("Fixing Trip 2 (Beijing Exchange Bucket List)")
    print("=" * 60)
    fix_trip2(trip2_path)

    print()
    print("=" * 60)
    print("Validating both files...")
    print("=" * 60)
    v1 = validate_json(trip1_path)
    v2 = validate_json(trip2_path)

    if v1 and v2:
        print("\nAll files valid and updated successfully.")
        sys.exit(0)
    else:
        print("\nERROR: Validation failed!")
        sys.exit(1)
