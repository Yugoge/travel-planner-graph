#!/usr/bin/env python3
"""Fix missing fields in attractions.json for both trips.

Adds:
- Trip 1: opening_hours for all 35 items, type_local for 5 Day 7 items
- Trip 2: currency_local, type_local, notes_local for all 48 items
"""

import json
import sys
from pathlib import Path


def fix_trip1(filepath: str) -> dict:
    """Add opening_hours and missing type_local to Trip 1 attractions."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Map of attraction name_base -> opening_hours
    # Determined by type of attraction
    opening_hours_map = {
        # Day 1 - Chongqing
        "Raffles City Chongqing Observation Deck": "09:00-22:00",
        "Huguang Guild Hall": "09:00-17:00",
        "Xiayao Li & Longmenhao Old Street": "All day",
        "Liziba Station": "06:30-22:30",
        "Hongyadong Folk Culture District": "All day",
        # Day 2 - Bazhong
        "Nankang Slope": "06:00-22:00",
        "Wangwang Mountain Sports Park": "06:00-22:00",
        # Day 3 - Chengdu
        "Chengdu Taikoo Li": "10:00-22:00",
        # Day 4 - Chengdu -> Shanghai
        "Chengdu Giant Panda Breeding Research Base": "07:30-18:00",
        "Jinli Ancient Street": "All day",
        "The Bund Night Walk": "All day",
        # Day 5 - Shanghai
        "plusone coffee (Anfu Road)": "10:00-20:00",
        "Gregorius SHADE": "10:00-18:00",
        "Wukang Road Walking Area": "All day",
        "Garden Books (Changle Road)": "10:00-22:00",
        "Pudong Art Museum": "10:00-21:00",
        "French Concession Side Streets": "All day",
        # Day 6 - Shanghai
        "Shanghai Disneyland": "08:30-20:30",
        # Day 7 - Shanghai
        "Suzhou Creek Riverside Walk": "All day",
        "The Bund Walk": "All day",
        "Nanjing Road Pedestrian Street": "All day",
        "Pudong Riverside Cycling & Ferry": "06:00-21:00",
        "TOP TOY Global Flagship Store (Optional)": "10:00-22:00",
        # Day 9 - Beijing
        "Tsinghua University Campus": "All day",
        "Peking University Campus": "All day",
        "Nearby Life Support Facilities": "All day",
        # Day 10 - Beijing
        "University Neighborhood Exploration": "All day",
        # Day 13 - Beijing
        "Forbidden City": "08:30-17:00",
        "Nanluoguxiang OR 798 Art District": "All day",
        # Day 14 - Beijing
        "Coffee Shops & Cute Shops": "10:00-22:00",
        "Shopping for Fashion Items": "10:00-22:00",
        # Day 15 - Beijing
        "Free Day - Flexible Planning": "All day",
        # Day 16 - Tianjin / Beijing
        "Tianjin Day Trip - Optional": "All day",
        "Alternative: Beijing Free Day": "All day",
        # Day 20 - Beijing
        "Final Day Activities - Shopping & Memorable Experiences": "All day",
    }

    # Day 7 type_local mappings for items missing type_local
    day7_type_local_map = {
        "Riverside Walk": "滨江步道",
        "Scenic Walk": "景观步道",
        "Commercial Street": "商业街",
        "Ferry & Cycling Tour": "轮渡&骑行游",
        "Designer Toy Store": "设计师玩具店",
    }

    count_hours = 0
    count_type = 0

    for day in data["data"]["days"]:
        for attr in day.get("attractions", []):
            name = attr.get("name_base", "")

            # Add opening_hours if missing
            if "opening_hours" not in attr and name in opening_hours_map:
                attr["opening_hours"] = opening_hours_map[name]
                count_hours += 1

            # Add type_local for Day 7 items missing it
            if "type_local" not in attr:
                type_base = attr.get("type", "")
                if type_base in day7_type_local_map:
                    attr["type_local"] = day7_type_local_map[type_base]
                    count_type += 1

    print(f"Trip 1: Added opening_hours to {count_hours} items")
    print(f"Trip 1: Added type_local to {count_type} items")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def fix_trip2(filepath: str) -> dict:
    """Add currency_local, type_local, and notes_local to Trip 2 attractions."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # type_base -> type_local translation map
    type_local_map = {
        "Historic Street / Pedestrian Area": "历史街区",
        "Church / Museum / Historic Building": "宗教景点",
        "Winter Theme Park / Ice Sculpture Park": "冰雪节",
        "Scenic Area / Park / Wetland": "风景公园",
        "Wildlife Park / Tiger Sanctuary": "野生动物园",
        "Historic District / Pedestrian Area": "意式建筑",
        "Ferris Wheel / Observation": "地标",
        "Historic Pedestrian Street / Shopping": "文化街",
        "Historic Architecture District / Walking Tour": "历史街区",
        "Museum / Archaeological Site / UNESCO World Heritage": "历史遗迹",
        "Imperial Palace / Hot Springs / Historic Site": "温泉",
        "Food Street / Historic Quarter": "宗教区",
        "Historic Towers / Cultural Landmark": "地标",
        "Historic City Wall / Fortification": "城墙",
        "Buddhist Pagoda / Temple / UNESCO World Heritage": "宝塔",
        "History Museum": "博物馆",
        "Pedestrian Street / Cultural Theme Park": "文化街",
        "Classical Chinese Garden / UNESCO World Heritage": "园林",
        "Art and History Museum": "博物馆",
        "Historic Canal Street / Shopping": "历史街区",
        "Historic Canal Street / Nightlife": "历史街区",
        "Lake / Scenic Area / UNESCO World Heritage": "湖景",
        "Buddhist Temple / Historic Site": "寺庙",
        "Tea Plantation Village / Cultural Experience": "茶村",
        "Wetland Park / Nature Reserve": "湿地公园",
        "River Cruise / Scenic Cruise": "游船",
        "Historic Pedestrian Street / Nightlife": "商业街",
        "Outdoor Performance / Cultural Show": "灯光秀",
        "River Rafting / Scenic Activity": "竹筏漂流",
        "Scenic Cycling Route": "景观大道",
        "Karst Cave": "溶洞",
        "Mountain / Hiking / Viewpoint": "山峰",
        "National Park / UNESCO World Heritage / Scenic Area": "国家公园",
        "Mountain Scenic Area / Viewpoints": "山景",
        "Mountain Scenic Area / Cable Car": "山景",
        "Stream Valley / Hiking Trail": "景观大道",
        "Observation Tower / Landmark": "观光塔",
        "Historic District / Colonial Architecture": "历史岛屿",
        "Ancestral Hall / Museum / Historic Architecture": "祠堂",
        "Arts District / Creative Park": "创意园区",
        "Mountain / Observation Deck / Tourist Attraction": "观景台",
        "Shopping District / Waterfront / Tourist Area": "海滨长廊",
        "Night Market / Street Market": "夜市",
        "Island / Nature / Tourist Area": "历史岛屿",
        "Buddhist Statue / Monument": "寺庙",
        "Cable Car / Scenic Transport": "缆车",
        "Historic Ruins / UNESCO World Heritage": "世界遗产",
        "Casino Resort / Shopping Mall / Entertainment": "度假村",
    }

    # notes_base -> notes_local translation map (per attraction name)
    notes_local_map = {
        "Zhongyang Street / Central Street": "免费步行。餐饮购物另付。冰雪节期间（12-2月）非常热闹。",
        "Saint Sophia Cathedral": "内部博物馆需购票。外观免费参观。非常上镜。",
        "Harbin Ice and Snow World": "冬季限定景点。注意保暖。门票较贵但值得。夜晚冰雕灯光最佳。旺季建议提前预订。",
        "Sun Island Scenic Area": "主景区需购票。部分小景点另收费。地铁2号线可达。",
        "Siberian Tiger Park / Northeast Tiger Forest Park": "门票含穿越虎区的摆渡车。喂食活动另收费。有教育和保护意义。",
        "Tianjin Italian Style Street / Italian Concession Area": "免费参观。餐饮和博物馆另付费。非常适合拍照。靠近天津站。",
        "Tianjin Eye Ferris Wheel": "票价为一圈（约30分钟）。热门景点可能排队。夜景最佳。",
        "Tianjin Ancient Culture Street": "街道免费进入。购物和美食另付。手工艺品可砍价。周末人多。",
        "Tianjin Five Great Avenues Cultural Tourism Area": "街道免费步行。部分洋楼开放为博物馆（另收费）。可租自行车或乘马车。适合建筑摄影。",
        "Museum of Qin Terracotta Warriors and Horses": "强烈建议提前网上预约。建议请导游或使用语音导览。距市区40公里（1-1.5小时车程）。部分区域禁止拍照。",
        "Huaqing Palace / Huaqing Hot Springs": "可与兵马俑一起游览（均在临潼区）。可选晚间《长恨歌》演出（另付费，季节性）。温泉已不可泡浴。",
        "Muslim Quarter / Hui Min Jie": "免费进入。美食预算每人50-100元。晚间和周末非常拥挤。注意防盗。建议多品尝小吃。",
        "Xi'an Bell Tower and Drum Tower Museum": "联票比单买便宜。夜景灯光壮观。鼓楼有定时表演。位于市中心靠近回民街。",
        "Xi'an Ancient City Wall": "城墙上可租自行车（另付约45元，100分钟）。多个城门可进入。南门（永宁门）设施最好。骑行全程3-4小时，步行5-6小时。",
        "Giant Wild Goose Pagoda / Big Wild Goose Pagoda": "门票含寺院和塔。可登塔俯瞰城市。北广场音乐喷泉免费且热门（通常晚间，查时间表）。",
        "Shaanxi History Museum": "免费但须提前网上预约（常提前数天约满）。特展可能收费。至少预留2-3小时。建议语音导览。",
        "Tang Dynasty Never-Night City / Datang Everbright City": "完全免费。夜晚灯光最佳。周末非常拥挤。演出时间不固定。餐厅和商店众多。建议1.5-2小时。",
        "Humble Administrator's Garden / Zhuozheng Yuan": "建议提前预约。中午人多。可与苏州博物馆一起游览。摄影爱好者需多留时间。",
        "Suzhou Museum": "免费但需提前网上预约。非常热门，提前3-5天预约。建筑本身就是看点。大部分区域可拍照。",
        "Pingjiang Road / Pingjiang Lu": "免费进入。餐饮购物乘船另付。可坐小船游河（另付费）。下午和傍晚人多。处处可拍照。",
        "Shantang Street / Shantang Jie": "主街免费步行。部分历史建筑收门票。适合晚餐——品尝苏式面食。夜景是亮点。",
        "West Lake / Xihu": "主湖区免费。游船另付（游岛55元）。部分景点（寺庙、园林）另收门票。可步行或租车环湖。春秋为旺季。",
        "Lingyin Temple / Temple of Soul's Retreat": "景区门票45元+寺庙门票30元=共75元。非常热门。可烧香。有素斋餐厅。位于西湖以西约30分钟车程。",
        "Longjing Village / Dragon Well Tea Village": "村庄免费进入。品茶和购买另付。正宗龙井茶较贵。小心旅游陷阱和假茶。建议去正规茶馆。",
        "Xixi National Wetland Park": "门票80元。电动船另付（60-100元）。公园很大建议坐船。比西湖人少。至少预留2-3小时。",
        "Li River Cruise": "提前订票。价格因船型而异。通常含午餐。航程4-5小时。建议上午出发。天气好时最佳。",
        "West Street / Xijie": "免费步行。餐饮购物另付。旅游气息浓但氛围好。适合漓江下船后晚餐。酒吧街夜间较吵。",
        "Impression Liu Sanjie / Impression Sanjie Liu": "票价238-680元视座位而定。旺季提前订票。雨天可能取消（露天演出）。冬天注意保暖。距阳朔镇10分钟。",
        "Yulong River Bamboo Rafting": "价格因漂流段而异（80-240元）。最热门：金龙桥到旧县。两人一筏。带防水袋。可能会湿。可与十里画廊骑行结合。",
        "Ten-Mile Gallery / Shili Hualang": "道路免费通行。沿途部分景点收费（月亮山15元等）。在阳朔镇租电动车或自行车（20-40元/天）。平坦好骑。带水和防晒。",
        "Silver Cave / Yinzi Yan": "门票65元。距阳朔约30公里（45分钟车程）。洞内步行道约2公里。台阶湿滑穿好鞋。洞内较潮湿。",
        "Moon Hill": "门票15元。爬800+级台阶需一定体力。带水。山顶风景值得。可从山脚免费远观。十里画廊骑行路线的一部分。",
        "Zhangjiajie National Forest Park": "多日票（228元有效4天）。公园很大一天较赶，2-3天最佳。缆车电梯另付（67-72元）。穿舒适登山鞋。天气多变。观景台和缆车处人多。",
        "Yuanjiajie Scenic Area / Avatar Mountain": "含在公园门票内。可乘百龙天梯（72元，世界最高户外电梯326米）或徒步。旺季电梯排队2小时+。步行环线2-3小时。必游区域。",
        "Tianzi Mountain / Emperor Mountain": "含在公园门票内。缆车67元单程（建议上山乘坐）。可徒步上下（较累）。多个观景点沿山脊步道。天气影响能见度。预留2-3小时。",
        "Golden Whip Stream": "含在公园门票内。全程较平坦。全程步行2.5-3小时。可中途转缆车上山。带水和零食。可能遇到猴子（勿喂食）。适合上午游览。",
        "Canton Tower / Guangzhou Tower": "票价因楼层而异：150元（低层观景台）至398元（顶层+项目）。网上购票有优惠。晚间票热门。地铁可达。预留1.5-2小时。带身份证取票。",
        "Shamian Island / Shameen Island": "免费参观。咖啡馆餐厅另付。非常适合拍照。适合悠闲散步。部分建筑为领事馆。热门婚纱摄影地。靠近黄沙地铁站。",
        "Chen Clan Ancestral Hall / Chen Clan Academy": "门票10元。可拍照。多个庭院和大厅保存完好。有语音导览。预留1-1.5小时。可购买传统工艺品纪念品。地铁陈家祠站。",
        "OCT Loft Creative Culture Park": "园区免费进入。个别场馆可能收费。周末有活动和市集。地铁可达。适合喝咖啡、逛展、拍照。",
        "Victoria Peak / The Peak": "山顶缆车往返+凌霄阁约115港币。缆车高峰排队1-2小时。替代方案：巴士15路或出租车上山。天气好很关键。傍晚人多。",
        "Tsim Sha Tsui": "海滨免费。幻彩咏香江每晚8点免费。海滨长廊适合拍港岛景色。博物馆另收费。购物从奢侈品到平价都有。",
        "Temple Street Night Market": "免费逛。购物可砍价。试试街头美食（海鲜、煲仔饭）。人多注意随身物品。靠近佐敦/油麻地地铁站。",
        "Lantau Island": "地铁东涌线或渡轮可达。缆车到昂坪（见下条）。可玩一整天。大澳渔村值得去（传统棚屋）。比港岛清幽。",
        "Tian Tan Buddha / Big Buddha": "外观免费。进入内部60港币（含餐券）。268级台阶。宝莲禅寺有素斋。乘昂坪360缆车或巴士可达。天气好很重要。",
        "Ngong Ping 360 Cable Car": "标准车厢往返约235港币。水晶车厢（玻璃地板）加价。高峰排队1-2小时。网上购票可免排队。大风大雨停运。替代：东涌23路巴士。",
        "Ruins of St. Paul's": "免费参观。白天和周末人非常多。有台阶通向牌坊。附近有澳门博物馆（15澳门元）。接近街上有很多旅游商店。可登大炮台看城景。",
        "The Venetian Macao": "免费进入参观。贡多拉船另付（128澳门元）。赌场需21岁以上。大运河购物中心350+商店。多家餐厅。渡轮码头有免费接驳巴士。公共区域可拍照。",
    }

    # Currency mapping by day/location
    # Days 1-11: mainland China = CNY
    # Day 12: OCT Loft (Shenzhen) = CNY, Victoria Peak/Tsim Sha Tsui/Temple Street = HKD
    # Day 13: Lantau/Tian Tan/Ngong Ping = HKD, Ruins of St. Paul's/Venetian Macao = MOP
    hkd_attractions = {
        "Victoria Peak / The Peak",
        "Tsim Sha Tsui",
        "Temple Street Night Market",
        "Lantau Island",
        "Tian Tan Buddha / Big Buddha",
        "Ngong Ping 360 Cable Car",
    }
    mop_attractions = {
        "Ruins of St. Paul's",
        "The Venetian Macao",
    }

    count_currency = 0
    count_type = 0
    count_notes = 0

    for day in data["data"]["days"]:
        for attr in day.get("attractions", []):
            name = attr.get("name_base", "")
            type_val = attr.get("type", "")

            # Fix currency: rename "currency" to "currency_local" if exists,
            # otherwise add currency_local
            if "currency" in attr:
                # Rename to currency_local
                attr["currency_local"] = attr.pop("currency")
                count_currency += 1
            elif "currency_local" not in attr:
                if name in hkd_attractions:
                    attr["currency_local"] = "HKD"
                elif name in mop_attractions:
                    attr["currency_local"] = "MOP"
                else:
                    attr["currency_local"] = "CNY"
                count_currency += 1

            # Add type_local
            if "type_local" not in attr:
                if type_val in type_local_map:
                    attr["type_local"] = type_local_map[type_val]
                    count_type += 1
                else:
                    print(f"  WARNING: No type_local mapping for type='{type_val}' "
                          f"(attraction: {name})")

            # Add notes_local
            if "notes_local" not in attr:
                if name in notes_local_map:
                    attr["notes_local"] = notes_local_map[name]
                    count_notes += 1
                else:
                    print(f"  WARNING: No notes_local mapping for '{name}'")

    print(f"Trip 2: Added/fixed currency_local on {count_currency} items")
    print(f"Trip 2: Added type_local to {count_type} items")
    print(f"Trip 2: Added notes_local to {count_notes} items")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def validate_json(filepath: str) -> bool:
    """Validate JSON file is parseable."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"VALID: {filepath}")
        return True
    except json.JSONDecodeError as e:
        print(f"INVALID: {filepath} - {e}")
        return False


def count_attractions(data: dict) -> int:
    """Count total attractions in data."""
    total = 0
    for day in data["data"]["days"]:
        total += len(day.get("attractions", []))
    return total


def audit_fields(data: dict, label: str, required_fields: list[str]):
    """Audit missing fields across all attractions."""
    print(f"\n--- Audit: {label} ---")
    total = count_attractions(data)
    print(f"Total attractions: {total}")

    for field in required_fields:
        missing = 0
        missing_names = []
        for day in data["data"]["days"]:
            for attr in day.get("attractions", []):
                if field not in attr:
                    missing += 1
                    missing_names.append(attr.get("name_base", "unknown"))
        if missing > 0:
            print(f"  MISSING '{field}': {missing}/{total}")
            for name in missing_names[:5]:
                print(f"    - {name}")
            if len(missing_names) > 5:
                print(f"    ... and {len(missing_names) - 5} more")
        else:
            print(f"  OK '{field}': {total}/{total}")


def main():
    trip1_path = "/root/travel-planner/data/china-feb-15-mar-7-2026-20260202-195429/attractions.json"
    trip2_path = "/root/travel-planner/data/beijing-exchange-bucket-list-20260202-232405/attractions.json"

    print("=" * 60)
    print("Fixing Trip 1 attractions...")
    print("=" * 60)
    trip1_data = fix_trip1(trip1_path)

    print("\n" + "=" * 60)
    print("Fixing Trip 2 attractions...")
    print("=" * 60)
    trip2_data = fix_trip2(trip2_path)

    print("\n" + "=" * 60)
    print("Validating JSON files...")
    print("=" * 60)
    v1 = validate_json(trip1_path)
    v2 = validate_json(trip2_path)

    # Audit required fields
    trip1_required = [
        "name_base", "name_local", "location_base", "location_local",
        "cost", "type", "opening_hours", "type_local"
    ]
    trip2_required = [
        "name_base", "name_local", "location_base", "location_local",
        "cost", "type", "currency_local", "type_local", "notes_local"
    ]

    audit_fields(trip1_data, "Trip 1", trip1_required)
    audit_fields(trip2_data, "Trip 2", trip2_required)

    if v1 and v2:
        print("\nAll files valid.")
        return 0
    else:
        print("\nSome files had validation errors!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
