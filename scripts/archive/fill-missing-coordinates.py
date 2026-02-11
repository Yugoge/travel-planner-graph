#!/usr/bin/env python3
"""
Fill missing coordinates for POIs in bucket-list trip data.

Strategy (in order of preference):
1. Gaode POI Detail API - using existing poi_id from search_results or gaode_id
2. Gaode POI Text Search API - using name_local/name_cn + city
3. Hardcoded lookup table - for well-known landmarks and HK/Macau POIs
4. City center fallback - approximate coordinates based on city

Gaode API returns GCJ-02 coordinates (China standard). We convert to WGS-84 for GPS.
"""

import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request

# --- GCJ-02 to WGS-84 conversion ---
# Gaode Maps uses GCJ-02; we need WGS-84 for standard GPS coordinates.

_A = 6378245.0  # Semi-major axis
_EE = 0.00669342162296594  # Eccentricity squared


def _transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def _out_of_china(lng, lat):
    """Check if coordinates are outside China (GCJ-02 only applies within China)."""
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def gcj02_to_wgs84(gcj_lng, gcj_lat):
    """Convert GCJ-02 coordinates to WGS-84."""
    if _out_of_china(gcj_lng, gcj_lat):
        # Outside China, no conversion needed (HK, Macau use WGS-84)
        return gcj_lng, gcj_lat

    d_lat = _transform_lat(gcj_lng - 105.0, gcj_lat - 35.0)
    d_lng = _transform_lng(gcj_lng - 105.0, gcj_lat - 35.0)
    rad_lat = gcj_lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1 - _EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((_A * (1 - _EE)) / (magic * sqrt_magic) * math.pi)
    d_lng = (d_lng * 180.0) / (_A / sqrt_magic * math.cos(rad_lat) * math.pi)
    return gcj_lng - d_lng, gcj_lat - d_lat


# --- Gaode API functions ---

def gaode_poi_detail(api_key, poi_id):
    """Get coordinates from Gaode POI Detail API using poi_id."""
    params = urllib.parse.urlencode({
        'key': api_key,
        'id': poi_id,
        'output': 'json'
    })
    url = f'https://restapi.amap.com/v3/place/detail?{params}'
    try:
        req = urllib.request.urlopen(url, timeout=10)
        data = json.loads(req.read())
        if data.get('status') == '1' and data.get('pois'):
            loc = data['pois'][0].get('location', '')
            if loc and ',' in loc:
                lng, lat = loc.split(',')
                return float(lng), float(lat)
    except Exception as e:
        print(f"    [WARN] POI detail API error for {poi_id}: {e}")
    return None, None


def gaode_poi_search(api_key, keywords, city):
    """Search for POI using Gaode text search API."""
    params = urllib.parse.urlencode({
        'key': api_key,
        'keywords': keywords,
        'city': city,
        'output': 'json',
        'offset': '1',
        'citylimit': 'true'
    })
    url = f'https://restapi.amap.com/v3/place/text?{params}'
    try:
        req = urllib.request.urlopen(url, timeout=10)
        data = json.loads(req.read())
        if data.get('status') == '1' and data.get('pois'):
            loc = data['pois'][0].get('location', '')
            if loc and ',' in loc:
                lng, lat = loc.split(',')
                return float(lng), float(lat)
    except Exception as e:
        print(f"    [WARN] POI search API error for '{keywords}' in '{city}': {e}")
    return None, None


# --- Well-known POI coordinates (WGS-84) ---
# For POIs outside mainland China or where API might not find them

KNOWN_POIS = {
    # Hong Kong
    "tim ho wan": (114.1587, 22.2862),
    "添好运": (114.1587, 22.2862),
    "dim sum here": (114.1709, 22.3050),
    "点点心": (114.1709, 22.3050),
    "one dim sum": (114.1700, 22.3247),
    "一点心": (114.1700, 22.3247),
    "victoria peak": (114.1455, 22.2759),
    "the peak": (114.1455, 22.2759),
    "太平山顶": (114.1455, 22.2759),
    "tsim sha tsui": (114.1722, 22.2988),
    "尖沙咀": (114.1722, 22.2988),
    "temple street night market": (114.1700, 22.3060),
    "庙街夜市": (114.1700, 22.3060),
    "temple street": (114.1700, 22.3060),
    "lantau island": (113.9416, 22.2646),
    "大屿山": (113.9416, 22.2646),
    "tian tan buddha": (113.9050, 22.2540),
    "big buddha": (113.9050, 22.2540),
    "天坛大佛": (113.9050, 22.2540),
    "ngong ping 360": (113.9050, 22.2560),
    "昂坪360": (113.9050, 22.2560),
    "ngong ping": (113.9050, 22.2560),
    "昂坪": (113.9050, 22.2560),
    "a symphony of lights": (114.1722, 22.2930),
    "维多利亚港灯光秀": (114.1722, 22.2930),
    "harbour city": (114.1678, 22.2966),
    "海港城": (114.1678, 22.2966),
    "holiday inn golden mile": (114.1727, 22.2985),
    "hong kong station": (114.1587, 22.2862),

    # Macau
    "ruins of st. paul's": (113.5409, 22.1974),
    "大三巴牌坊": (113.5409, 22.1974),
    "the venetian macao": (113.5585, 22.1491),
    "威尼斯人": (113.5585, 22.1491),
    "senado square": (113.5384, 22.1937),
    "议事亭前地": (113.5384, 22.1937),
    "margaret's café e nata": (113.5393, 22.1917),
    "玛嘉烈蛋挞店": (113.5393, 22.1917),
    "the house of dancing water": (113.5621, 22.1482),
    "水舞间": (113.5621, 22.1482),

    # Shenzhen
    "oct loft creative culture park": (114.0131, 22.5414),
    "oct loft": (114.0131, 22.5414),
    "华侨城创意文化园": (114.0131, 22.5414),
    "dongmen pedestrian street": (114.1194, 22.5478),
    "东门步行街": (114.1194, 22.5478),
    "hyatt place shenzhen dongmen": (114.1220, 22.5500),

    # Harbin
    "harbin ice and snow world": (126.5362, 45.7850),
    "冰雪大世界": (126.5362, 45.7850),
    "哈尔滨冰雪大世界": (126.5362, 45.7850),
    "zhongyang street": (126.6175, 45.7723),
    "中央大街": (126.6175, 45.7723),
    "saint sophia cathedral": (126.6271, 45.7700),
    "圣索菲亚教堂": (126.6271, 45.7700),
    "sun island": (126.5900, 45.7940),
    "太阳岛": (126.5900, 45.7940),
    "ice bar": (126.6175, 45.7730),
    "pacer's bar": (126.6350, 45.7570),
    "harbin wei ye hotel": (126.6185, 45.7705),

    # Tianjin
    "tianjin eye": (117.1697, 39.1458),
    "天津之眼": (117.1697, 39.1458),
    "hai river": (117.2000, 39.1400),
    "海河": (117.2000, 39.1400),
    "ancient culture street": (117.1744, 39.1428),
    "古文化街": (117.1744, 39.1428),
    "kind hotel tianjin": (117.1970, 39.1375),

    # Xi'an
    "terracotta warriors": (109.2734, 34.3847),
    "兵马俑": (109.2734, 34.3847),
    "giant wild goose pagoda": (108.9596, 34.2186),
    "大雁塔": (108.9596, 34.2186),
    "bell and drum tower": (108.9536, 34.2601),
    "钟鼓楼": (108.9536, 34.2601),
    "muslim quarter": (108.9470, 34.2620),
    "回民街": (108.9470, 34.2620),
    "defu lane": (108.9550, 34.2550),
    "德福巷": (108.9550, 34.2550),
    "tang dynasty ever-bright city": (108.9500, 34.2550),
    "大唐不夜城": (108.9500, 34.2550),
    "tang dynasty show": (108.9540, 34.2600),
    "moxy xi'an downtown": (108.9580, 34.2660),

    # Suzhou
    "humble administrator's garden": (120.6326, 31.3255),
    "拙政园": (120.6326, 31.3255),
    "pingjiang road": (120.6350, 31.3180),
    "平江路": (120.6350, 31.3180),
    "shantang street": (120.6000, 31.3180),
    "山塘街": (120.6000, 31.3180),
    "scholars hotel pinjiangfu": (120.6355, 31.3190),
    "pingjiang road ancient street": (120.6350, 31.3180),
    "suzhou silk museum": (120.6280, 31.3150),
    "苏州丝绸博物馆": (120.6280, 31.3150),
    "kunqu opera": (120.6230, 31.3130),

    # Hangzhou
    "west lake": (120.1482, 30.2423),
    "西湖": (120.1482, 30.2423),
    "longjing village": (120.1230, 30.2200),
    "龙井村": (120.1230, 30.2200),
    "longjing tea village": (120.1230, 30.2200),
    "xixi national wetland park": (120.0720, 30.2730),
    "西溪湿地": (120.0720, 30.2730),
    "impression west lake": (120.1480, 30.2480),
    "印象西湖": (120.1480, 30.2480),
    "west lake night cruise": (120.1520, 30.2460),
    "hefang street": (120.1670, 30.2450),
    "河坊街": (120.1670, 30.2450),
    "hangzhou west lake hubin yintai atour": (120.1590, 30.2520),

    # Guilin / Yangshuo
    "li river cruise": (110.2800, 25.2700),
    "漓江": (110.2800, 25.2700),
    "west street": (110.4890, 24.7730),
    "西街": (110.4890, 24.7730),
    "impression liu sanjie": (110.4700, 24.7600),
    "印象刘三姐": (110.4700, 24.7600),
    "yulong river": (110.4200, 24.7400),
    "遇龙河": (110.4200, 24.7400),
    "ten-mile gallery": (110.4400, 24.7250),
    "十里画廊": (110.4400, 24.7250),
    "silver cave": (110.5100, 24.7450),
    "银子岩": (110.5100, 24.7450),
    "moon hill": (110.4650, 24.7200),
    "月亮山": (110.4650, 24.7200),
    "guilin specialty": (110.2960, 25.2730),
    "holiday inn express guilin": (110.2960, 25.2800),
    "the bamboo leaf yangshuo": (110.4880, 24.7740),

    # Zhangjiajie
    "zhangjiajie national forest park": (110.4346, 29.3207),
    "张家界国家森林公园": (110.4346, 29.3207),
    "yuanjiajie": (110.4350, 29.3480),
    "袁家界": (110.4350, 29.3480),
    "avatar mountain": (110.4350, 29.3480),
    "tianzi mountain": (110.4650, 29.3680),
    "天子山": (110.4650, 29.3680),
    "golden whip stream": (110.4370, 29.3150),
    "金鞭溪": (110.4370, 29.3150),
    "tianmen fox fairy": (110.4780, 29.0510),
    "天门狐仙": (110.4780, 29.0510),
    "charming xiangxi": (110.4780, 29.1200),
    "魅力湘西": (110.4780, 29.1200),
    "zhangjiajie specialty": (110.4790, 29.1260),
    "hilton garden inn zhangjiajie": (110.5390, 29.3530),

    # Guangzhou
    "canton tower": (113.3243, 23.1065),
    "广州塔": (113.3243, 23.1065),
    "shamian island": (113.2370, 23.1065),
    "沙面": (113.2370, 23.1065),
    "chen clan ancestral hall": (113.2454, 23.1259),
    "陈家祠": (113.2454, 23.1259),
    "pearl river night cruise": (113.2540, 23.1100),
    "珠江夜游": (113.2540, 23.1100),
    "beijing road pedestrian street": (113.2650, 23.1285),
    "北京路步行街": (113.2650, 23.1285),
    "shamian island shops": (113.2370, 23.1065),
    "arthur hotel canton tower": (113.3200, 23.1010),
}

# City center coordinates (WGS-84) as fallback
CITY_CENTERS = {
    "harbin": (126.65, 45.75),
    "tianjin": (117.20, 39.13),
    "xi'an": (108.94, 34.26),
    "suzhou": (120.62, 31.30),
    "hangzhou": (120.17, 30.25),
    "guilin": (110.29, 25.27),
    "yangshuo": (110.49, 24.77),
    "guilin / yangshuo": (110.29, 25.27),
    "zhangjiajie": (110.48, 29.12),
    "guangzhou": (113.26, 23.13),
    "shenzhen": (114.06, 22.55),
    "hong kong": (114.17, 22.28),
    "macau": (113.55, 22.20),
    "shenzhen / hong kong": (114.06, 22.55),
    "hong kong / macau": (114.17, 22.28),
    "beijing": (116.40, 39.91),
}


def lookup_known_poi(name, city):
    """Try to find coordinates in the known POI table."""
    # Normalize name for lookup
    name_lower = name.lower().strip()

    # Try exact match first
    if name_lower in KNOWN_POIS:
        return KNOWN_POIS[name_lower]

    # Try substring matching with key POI terms
    for key, coords in KNOWN_POIS.items():
        if key in name_lower or name_lower in key:
            return coords

    # Try matching city-specific keywords
    for key, coords in KNOWN_POIS.items():
        # Split name into words and check if any significant word matches
        name_words = set(name_lower.replace('/', ' ').replace('-', ' ').split())
        key_words = set(key.replace('/', ' ').replace('-', ' ').split())
        # If they share significant words (not just articles)
        common = name_words & key_words - {'the', 'a', 'an', 'of', 'in', 'at', 'to', 'and', '/', '-'}
        if len(common) >= 2:
            return coords

    return None, None


def get_city_center(city):
    """Get city center coordinates as last-resort fallback."""
    city_lower = city.lower().strip()
    for key, coords in CITY_CENTERS.items():
        if key in city_lower or city_lower in key:
            return coords
    return None, None


def extract_poi_id(item):
    """Extract Gaode POI ID from item's gaode_id or search_results."""
    gaode_id = item.get('gaode_id')
    if gaode_id:
        return gaode_id

    for sr in item.get('search_results', []):
        if sr.get('skill') == 'gaode-maps' and sr.get('poi_id'):
            return sr['poi_id']

    return None


def extract_search_name(item):
    """Extract the best search name for the item."""
    # Prefer Chinese name for Gaode search
    for field in ['name_local', 'name_cn', 'name_chinese', 'name']:
        val = item.get(field, '')
        if val and any('\u4e00' <= c <= '\u9fff' for c in val):
            return val

    return item.get('name_base', '') or item.get('name', '')


def determine_city_for_search(day_location, item):
    """Determine the city name for Gaode API search."""
    loc = day_location or ''

    # Handle compound locations
    if '/' in loc:
        parts = [p.strip() for p in loc.split('/')]
        # Try to determine which city from the item's location
        item_loc = (item.get('location_base', '') + ' ' + item.get('location_local', '')).lower()
        for part in parts:
            if part.lower() in item_loc:
                return part
        return parts[0]

    return loc


def is_outside_mainland_china(city):
    """Check if the city is outside mainland China."""
    hk_macau = {'hong kong', 'macau', 'macao', 'lantau'}
    city_lower = city.lower()
    for term in hk_macau:
        if term in city_lower:
            return True
    return False


def fill_coordinates(data_dir, api_key):
    """Main function to fill missing coordinates in all agent files."""
    files = ['meals.json', 'attractions.json', 'entertainment.json',
             'accommodation.json', 'shopping.json']

    total_filled = 0
    total_missing = 0
    api_calls = 0
    results_by_method = {'poi_detail': 0, 'poi_search': 0, 'known_lookup': 0, 'city_fallback': 0}

    for filename in files:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"[SKIP] {filename} not found")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        agent = data.get('agent', filename.replace('.json', ''))
        days = data.get('data', {}).get('days', [])
        file_filled = 0

        print(f"\n{'=' * 60}")
        print(f"Processing: {filename} (agent: {agent})")
        print(f"{'=' * 60}")

        for day in days:
            day_num = day.get('day', '?')
            day_location = day.get('location', '')

            # Collect items to process based on agent type
            items_to_process = []

            if agent == 'meals':
                for meal_type in ['breakfast', 'lunch', 'dinner']:
                    item = day.get(meal_type)
                    if item and 'coordinates' not in item:
                        items_to_process.append((meal_type, item))
            elif agent == 'accommodation':
                item = day.get('accommodation')
                if item and 'coordinates' not in item:
                    items_to_process.append(('accommodation', item))
            elif agent in ['attractions', 'entertainment', 'shopping']:
                for item in day.get(agent, []):
                    if 'coordinates' not in item:
                        name = item.get('name_base', '') or item.get('name', '')
                        items_to_process.append((name[:30], item))

            for label, item in items_to_process:
                total_missing += 1
                name = item.get('name_base', '') or item.get('name', '')
                search_name = extract_search_name(item)
                city = determine_city_for_search(day_location, item)

                lng, lat = None, None
                method = None

                # Strategy 1: Use Gaode POI Detail API with existing poi_id
                poi_id = extract_poi_id(item)
                if poi_id and not is_outside_mainland_china(city):
                    lng, lat = gaode_poi_detail(api_key, poi_id)
                    api_calls += 1
                    if lng and lat:
                        # Convert GCJ-02 to WGS-84
                        lng, lat = gcj02_to_wgs84(lng, lat)
                        method = 'poi_detail'
                    time.sleep(0.1)  # Rate limiting

                # Strategy 2: Use Gaode POI Text Search
                if not method and not is_outside_mainland_china(city):
                    lng, lat = gaode_poi_search(api_key, search_name, city)
                    api_calls += 1
                    if lng and lat:
                        lng, lat = gcj02_to_wgs84(lng, lat)
                        method = 'poi_search'
                    time.sleep(0.1)

                # Strategy 3: Known POI lookup (for HK/Macau and other well-known places)
                if not method:
                    result = lookup_known_poi(name, city)
                    if result and result[0] is not None:
                        lng, lat = result
                        method = 'known_lookup'

                # Also try Chinese name in known lookup
                if not method and search_name:
                    result = lookup_known_poi(search_name, city)
                    if result and result[0] is not None:
                        lng, lat = result
                        method = 'known_lookup'

                # Strategy 4: City center fallback
                if not method:
                    center = get_city_center(city)
                    if center and center[0] is not None:
                        lng, lat = center
                        method = 'city_fallback'

                if lng and lat:
                    item['coordinates'] = {
                        'lat': round(lat, 6),
                        'lng': round(lng, 6)
                    }
                    file_filled += 1
                    total_filled += 1
                    results_by_method[method] += 1
                    status = "OK" if method != 'city_fallback' else "APPROX"
                    print(f"  [{status}] Day {day_num} {label}: {name[:50]} -> ({lat:.4f}, {lng:.4f}) [{method}]")
                else:
                    print(f"  [FAIL] Day {day_num} {label}: {name[:50]} -> NO COORDINATES FOUND")

        # Save updated file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')

        print(f"  -> {file_filled} coordinates filled in {filename}")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total POIs missing coordinates: {total_missing}")
    print(f"Total coordinates filled: {total_filled}")
    print(f"Total API calls: {api_calls}")
    print(f"Methods used:")
    for method, count in results_by_method.items():
        print(f"  {method}: {count}")
    if total_missing > total_filled:
        print(f"WARNING: {total_missing - total_filled} POIs still missing coordinates!")

    return total_filled, total_missing


if __name__ == '__main__':
    # Parameters
    data_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/beijing-exchange-bucket-list-20260202-232405'
    api_key = sys.argv[2] if len(sys.argv) > 2 else os.environ.get(
        'GAODE_API_KEY',
        os.environ.get('AMAP_API_KEY', '99e97af6fd426ce3cfc45d22d26e78e3')
    )

    if not os.path.isdir(data_dir):
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Data directory: {data_dir}")
    print(f"API key: {api_key[:8]}...{api_key[-4:]}")

    filled, total = fill_coordinates(data_dir, api_key)

    if filled == total:
        print(f"\nAll {total} POIs now have coordinates.")
        sys.exit(0)
    else:
        print(f"\n{filled}/{total} POIs filled. {total - filled} still missing.")
        sys.exit(2 if filled > 0 else 1)
