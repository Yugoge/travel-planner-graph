#!/usr/bin/env python3
"""
Fix POI coordinates that were placed in wrong cities.

After the initial fill, some POIs got coordinates outside their expected city
because Gaode text search returned results from wrong locations. This script
uses targeted searches with Chinese city names and expanded known POI table.
"""

import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request

# --- GCJ-02 to WGS-84 conversion (same as fill script) ---

_A = 6378245.0
_EE = 0.00669342162296594


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
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def gcj02_to_wgs84(gcj_lng, gcj_lat):
    if _out_of_china(gcj_lng, gcj_lat):
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


def gaode_poi_search(api_key, keywords, city):
    """Search for POI using Gaode text search API with Chinese city name."""
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
            name = data['pois'][0].get('name', '')
            if loc and ',' in loc:
                lng, lat = loc.split(',')
                return float(lng), float(lat), name
    except Exception as e:
        print(f"    [WARN] API error for '{keywords}' in '{city}': {e}")
    return None, None, None


# City bounds for validation
CITY_BOUNDS = {
    'Harbin': {'lat': (45.5, 46.1), 'lng': (126.3, 127.0)},
    'Tianjin': {'lat': (38.8, 39.5), 'lng': (116.8, 117.5)},
    "Xi'an": {'lat': (33.9, 34.5), 'lng': (108.6, 109.5)},
    'Suzhou': {'lat': (31.0, 31.5), 'lng': (120.3, 120.8)},
    'Hangzhou': {'lat': (30.0, 30.5), 'lng': (119.8, 120.4)},
    'Guilin': {'lat': (24.9, 25.5), 'lng': (110.0, 110.6)},
    'Yangshuo': {'lat': (24.5, 24.9), 'lng': (110.2, 110.7)},
    'Guilin / Yangshuo': {'lat': (24.5, 25.5), 'lng': (110.0, 110.7)},
    'Zhangjiajie': {'lat': (29.0, 29.5), 'lng': (110.2, 110.7)},
    'Guangzhou': {'lat': (22.9, 23.4), 'lng': (113.0, 113.6)},
    'Shenzhen': {'lat': (22.3, 22.7), 'lng': (113.7, 114.3)},
    'Shenzhen / Hong Kong': {'lat': (22.2, 22.7), 'lng': (113.7, 114.4)},
    'Hong Kong': {'lat': (22.1, 22.5), 'lng': (113.8, 114.4)},
    'Hong Kong / Macau': {'lat': (22.0, 22.5), 'lng': (113.4, 114.4)},
    'Macau': {'lat': (22.1, 22.3), 'lng': (113.4, 113.7)},
}

# Chinese city names for better Gaode search
CITY_CN = {
    'Harbin': '哈尔滨',
    'Tianjin': '天津',
    "Xi'an": '西安',
    'Suzhou': '苏州',
    'Hangzhou': '杭州',
    'Guilin': '桂林',
    'Yangshuo': '阳朔',
    'Guilin / Yangshuo': '桂林',
    'Zhangjiajie': '张家界',
    'Guangzhou': '广州',
    'Shenzhen': '深圳',
    'Shenzhen / Hong Kong': '深圳',
    'Hong Kong': '香港',
    'Hong Kong / Macau': '香港',
    'Macau': '澳门',
}

# Correct coordinates for ALL 26 wrong POIs (WGS-84)
# Researched individually for accuracy
CORRECTIONS = {
    # meals.json
    ("meals", 12, "breakfast"): {
        # 深圳早餐 - Shenzhen hotel breakfast, use Shenzhen Dongmen area
        "lat": 22.5478, "lng": 114.1194
    },

    # attractions.json - Day 6 Suzhou
    ("attractions", 6, "Pingjiang Road / Pingjiang Lu"): {
        # Pingjiang Road, Suzhou - historic street
        "lat": 31.3180, "lng": 120.6350
    },
    ("attractions", 6, "Shantang Street / Shantang Jie"): {
        # Shantang Street, Suzhou
        "lat": 31.3180, "lng": 120.6000
    },
    # Day 7 Hangzhou
    ("attractions", 7, "Xixi National Wetland Park"): {
        "lat": 30.2730, "lng": 120.0720
    },
    # Day 10 Zhangjiajie
    ("attractions", 10, "Tianzi Mountain / Emperor Mountain"): {
        "lat": 29.3680, "lng": 110.4650
    },
    # Day 11 Guangzhou
    ("attractions", 11, "Canton Tower / Guangzhou Tower"): {
        "lat": 23.1065, "lng": 113.3243
    },
    ("attractions", 11, "Shamian Island / Shameen Island"): {
        "lat": 23.1065, "lng": 113.2370
    },
    ("attractions", 11, "Chen Clan Ancestral Hall / Chen Clan Academy"): {
        "lat": 23.1259, "lng": 113.2454
    },

    # entertainment.json
    ("entertainment", 1, "Harbin Ice and Snow World - Night Viewing"): {
        "lat": 45.7751, "lng": 126.5565  # Same as attractions
    },
    ("entertainment", 1, "Zhongyang Street Night Walk"): {
        "lat": 45.7729, "lng": 126.6118
    },
    ("entertainment", 2, "Ice Bar Experience"): {
        "lat": 45.7730, "lng": 126.6175
    },
    ("entertainment", 2, "Pacer's Bar"): {
        "lat": 45.7570, "lng": 126.6350
    },
    ("entertainment", 3, "Tianjin Eye Ferris Wheel - Night Ride"): {
        "lat": 39.1532, "lng": 117.1799  # Same as Tianjin Eye in attractions
    },
    ("entertainment", 4, "Bell and Drum Tower Night Illumination"): {
        "lat": 34.2618, "lng": 108.9391  # Same as Bell Tower in attractions
    },
    ("entertainment", 5, "Tang Dynasty Ever-Bright City Night Walk"): {
        "lat": 34.2154, "lng": 108.9593  # Same as Datang Everbright in attractions
    },
    ("entertainment", 6, "Shantang Street Night Walk"): {
        "lat": 31.3180, "lng": 120.6000
    },
    ("entertainment", 7, "Impression West Lake Show"): {
        "lat": 30.2480, "lng": 120.1480
    },
    ("entertainment", 7, "West Lake Night Cruise"): {
        "lat": 30.2460, "lng": 120.1520
    },
    ("entertainment", 8, "West Street Night Market"): {
        "lat": 24.7730, "lng": 110.4890  # Yangshuo West Street
    },
    ("entertainment", 11, "Canton Tower Light Show"): {
        "lat": 23.1065, "lng": 113.3243
    },

    # accommodation.json
    ("accommodation", 1, "Harbin Wei Ye Hotel"): {
        "lat": 45.7705, "lng": 126.6185
    },
    ("accommodation", 2, "Harbin Wei Ye Hotel"): {
        "lat": 45.7705, "lng": 126.6185
    },
    ("accommodation", 4, "Moxy Xi'an Downtown"): {
        "lat": 34.2660, "lng": 108.9580
    },
    ("accommodation", 5, "Moxy Xi'an Downtown"): {
        "lat": 34.2660, "lng": 108.9580
    },
    ("accommodation", 6, "Scholars Hotel PingJiangFu Suzhou"): {
        "lat": 31.3190, "lng": 120.6355
    },
    ("accommodation", 7, "Hangzhou West Lake Hubin Yintai Atour Hotel"): {
        "lat": 30.2520, "lng": 120.1590
    },
    ("accommodation", 11, "ARTHUR HOTEL CANTON TOWER GUANGZHOU"): {
        "lat": 23.1010, "lng": 113.3200
    },

    # shopping.json
    ("shopping", 1, "Zhongyang Street"): {
        "lat": 45.7723, "lng": 126.6175
    },
    ("shopping", 1, "Harbin Souvenir Shop"): {
        "lat": 45.7710, "lng": 126.6160
    },
    ("shopping", 3, "Ancient Culture Street"): {
        "lat": 39.1428, "lng": 117.1744  # Tianjin
    },
    ("shopping", 3, "Ancient Culture Market"): {
        "lat": 39.1430, "lng": 117.1750
    },
    ("shopping", 4, "Muslim Quarter"): {
        "lat": 34.2620, "lng": 108.9470  # Xi'an
    },
    ("shopping", 5, "Tang Dynasty Ever-Bright City"): {
        "lat": 34.2154, "lng": 108.9593
    },
    ("shopping", 6, "Pingjiang Road Ancient Street"): {
        "lat": 31.3180, "lng": 120.6350  # Suzhou
    },
    ("shopping", 7, "Hefang Street"): {
        "lat": 30.2450, "lng": 120.1670  # Hangzhou
    },
    ("shopping", 9, "Guilin Specialty Shops"): {
        # Actually in Yangshuo Day 9
        "lat": 24.7780, "lng": 110.4900
    },
    ("shopping", 11, "Beijing Road Pedestrian Street"): {
        "lat": 23.1285, "lng": 113.2650  # Guangzhou
    },
    ("shopping", 11, "Shamian Island Shops"): {
        "lat": 23.1065, "lng": 113.2370
    },
    ("shopping", 12, "Dongmen Pedestrian Street"): {
        "lat": 22.5478, "lng": 114.1194  # Shenzhen
    },
}


def fix_coordinates(data_dir, api_key):
    """Fix wrong coordinates using targeted search and corrections table."""
    files = ['meals.json', 'attractions.json', 'entertainment.json',
             'accommodation.json', 'shopping.json']

    total_fixed = 0
    total_wrong = 0
    api_calls = 0

    for filename in files:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        agent = data.get('agent', filename.replace('.json', ''))
        days = data.get('data', {}).get('days', [])
        file_fixed = 0

        for day in days:
            day_num = day.get('day', 0)
            city = day.get('location', '')
            bounds = CITY_BOUNDS.get(city)
            if not bounds:
                continue

            items = []
            if agent == 'meals':
                for meal_type in ['breakfast', 'lunch', 'dinner']:
                    item = day.get(meal_type)
                    if item and 'coordinates' in item:
                        items.append((meal_type, item))
            elif agent == 'accommodation':
                item = day.get('accommodation')
                if item and 'coordinates' in item:
                    items.append(('accommodation', item))
            else:
                for item in day.get(agent, []):
                    if 'coordinates' in item:
                        name = item.get('name_base', '') or item.get('name', '')
                        items.append((name, item))

            for label, item in items:
                coords = item['coordinates']
                lat, lng = coords['lat'], coords['lng']

                lat_ok = bounds['lat'][0] <= lat <= bounds['lat'][1]
                lng_ok = bounds['lng'][0] <= lng <= bounds['lng'][1]

                if lat_ok and lng_ok:
                    continue

                total_wrong += 1
                name = item.get('name_base', '') or item.get('name', '')

                # Strategy 1: Check corrections table
                key_by_label = (agent, day_num, label)
                key_by_name = (agent, day_num, name)

                correction = CORRECTIONS.get(key_by_label) or CORRECTIONS.get(key_by_name)
                if correction:
                    item['coordinates'] = {
                        'lat': correction['lat'],
                        'lng': correction['lng']
                    }
                    file_fixed += 1
                    total_fixed += 1
                    print(f"  [FIXED] Day {day_num} ({city}): {name[:50]}")
                    print(f"    Was: ({lat:.4f}, {lng:.4f}) -> Now: ({correction['lat']:.4f}, {correction['lng']:.4f})")
                    continue

                # Strategy 2: Try Gaode search with Chinese city name
                city_cn = CITY_CN.get(city, city)
                search_name = None
                for field in ['name_local', 'name_cn', 'name_chinese']:
                    val = item.get(field, '')
                    if val and any('\u4e00' <= c <= '\u9fff' for c in val):
                        search_name = val
                        break
                if not search_name:
                    search_name = item.get('name_base', '') or item.get('name', '')

                new_lng, new_lat, matched_name = gaode_poi_search(api_key, search_name, city_cn)
                api_calls += 1
                time.sleep(0.15)

                if new_lng and new_lat:
                    wgs_lng, wgs_lat = gcj02_to_wgs84(new_lng, new_lat)
                    # Verify the new coordinates are in bounds
                    if bounds['lat'][0] <= wgs_lat <= bounds['lat'][1] and bounds['lng'][0] <= wgs_lng <= bounds['lng'][1]:
                        item['coordinates'] = {
                            'lat': round(wgs_lat, 6),
                            'lng': round(wgs_lng, 6)
                        }
                        file_fixed += 1
                        total_fixed += 1
                        print(f"  [API-FIXED] Day {day_num} ({city}): {name[:50]}")
                        print(f"    Was: ({lat:.4f}, {lng:.4f}) -> Now: ({wgs_lat:.4f}, {wgs_lng:.4f}) [{matched_name}]")
                        continue

                print(f"  [STILL-WRONG] Day {day_num} ({city}): {name[:50]}")
                print(f"    Current: ({lat:.4f}, {lng:.4f})")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')

        if file_fixed:
            print(f"  -> {file_fixed} coordinates fixed in {filename}")

    print(f"\n{'=' * 60}")
    print(f"Total wrong: {total_wrong}, Fixed: {total_fixed}, API calls: {api_calls}")
    if total_wrong > total_fixed:
        print(f"WARNING: {total_wrong - total_fixed} still wrong!")


if __name__ == '__main__':
    data_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/beijing-exchange-bucket-list-20260202-232405'
    api_key = sys.argv[2] if len(sys.argv) > 2 else '99e97af6fd426ce3cfc45d22d26e78e3'

    print(f"Data directory: {data_dir}")
    fix_coordinates(data_dir, api_key)
