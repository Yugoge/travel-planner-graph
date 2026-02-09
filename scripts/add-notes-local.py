#!/usr/bin/env python3
"""
Add notes_local (Chinese translation) fields to travel plan data files.
Places notes_local immediately after the existing notes field in each entry.
"""

import json
import sys
from collections import OrderedDict
from pathlib import Path


DATA_DIR = Path("/root/travel-planner/data/china-feb-15-mar-7-2026-20260202-195429")


def ordered_insert_after(d: dict, after_key: str, new_key: str, new_value) -> OrderedDict:
    """Insert new_key:new_value right after after_key in dict, preserving order."""
    result = OrderedDict()
    for k, v in d.items():
        result[k] = v
        if k == after_key:
            result[new_key] = new_value
    # If after_key wasn't found, append at end
    if new_key not in result:
        result[new_key] = new_value
    return result


def add_notes_local_to_dict(d: dict, notes_map: dict, path: str = "") -> dict:
    """
    Recursively walk a dict. When a 'notes' key is found, insert 'notes_local'
    right after it using the translation from notes_map, keyed by the notes value.
    """
    if not isinstance(d, dict):
        return d

    # Check if this dict has a 'notes' field and doesn't already have 'notes_local'
    if "notes" in d and "notes_local" not in d:
        notes_val = d["notes"]
        if notes_val in notes_map:
            d = dict(ordered_insert_after(d, "notes", "notes_local", notes_map[notes_val]))

    # Recurse into sub-dicts and lists
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = add_notes_local_to_dict(v, notes_map, f"{path}.{k}")
        elif isinstance(v, list):
            d[k] = [
                add_notes_local_to_dict(item, notes_map, f"{path}.{k}[{i}]")
                if isinstance(item, dict) else item
                for i, item in enumerate(v)
            ]

    return d


def process_file(filename: str, notes_map: dict):
    """Load JSON file, add notes_local translations, save back."""
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = add_notes_local_to_dict(data, notes_map)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Validate
    with open(filepath, "r", encoding="utf-8") as f:
        json.load(f)  # Will raise if invalid

    print(f"  [OK] {filename} - processed successfully")


def main():
    print("Adding notes_local translations to travel plan data files...")
    print(f"Data directory: {DATA_DIR}\n")

    # =========================================================================
    # MEALS.JSON
    # =========================================================================
    print("Processing meals.json...")
    meals_notes = {
        # Day 1
        "Breakfast after observation deck visit. Multiple options available in mall food court. Convenient location.":
            "参观观景台后用早餐。商场美食广场内有多种选择，方便快捷。",
        "NO HOTPOT (saving for dinner). Authentic Jianghu dishes near Huguang Guild Hall. Popular local restaurant.":
            "不吃火锅（留着晚上吃）。湖广会馆附近的正宗江湖菜。当地人气餐厅。",
        "HILLSIDE HOTPOT WITH NIGHT VIEW (南山半山腰). Elevated location with panoramic Chongqing night view. Reservations recommended.":
            "南山半山腰火锅，可欣赏重庆夜景全景。建议提前预约。",
        # Day 2
        "Breakfast with family at home. Chinese New Year Eve preparations.":
            "在家和家人一起吃早餐。除夕准备中。",
        "Family lunch. Chinese New Year Eve gathering.":
            "家庭午餐。除夕团聚。",
        "Chinese New Year Eve celebration dinner with family. Traditional reunion feast.":
            "除夕年夜饭，家庭团聚传统盛宴。",
        # Day 3
        "MUST-VISIT: Most authentic Bazhong breakfast. Famous sauce meat buns (酱肉包子). User-specified restaurant.":
            "必去：最正宗的巴中早餐。招牌酱肉包子。指定餐厅。",
        "MUST-VISIT: Famous for Bazhong-style beef dishes. User-specified restaurant before train departure.":
            "必去：巴中特色牛肉。指定餐厅，火车出发前用餐。",
        "MATURE SICHUAN RESTAURANT near Jinli Ancient Street. Established restaurant with authentic Chengdu flavors. Open during Spring Festival (11:00-21:30). Reservations recommended. Famous for fish-flavored shredded pork (鱼香肉丝), kung pao chicken, and seasonal bamboo shoots. Walking distance from Jinli. Phone: 028-8505-3333. Verified via Google Maps (rating 4.4).":
            "锦里古街附近的老牌川菜馆。正宗成都味道。春节期间营业（11:00-21:30）。建议预约。招牌菜：鱼香肉丝、宫保鸡丁、时令竹笋。步行可达锦里。电话：028-8505-3333。评分4.4。",
        # Day 4
        "LOCAL CHENGDU BREAKFAST: Famous for authentic Sichuan-style chāoshǒu (抄手/wontons). Flagship store near user's family home. Opens at 07:00, perfect for early breakfast before panda base visit. Rating: 4.6/5.0. Cost: ¥21 per person. Operating hours: 07:00-20:30 daily. Verified via Gaode Maps.":
            "成都本地早餐：正宗四川抄手。旗舰店靠近家。07:00开门，适合早起去熊猫基地前用餐。评分4.6，人均¥21。营业时间：07:00-20:30。",
        "⚠️ CRITICAL TIMING: Restaurant opens at 11:00 AM (NOT before). User MUST arrive exactly at 11:00 opening time. Only 45-minute window before airport departure (high-risk schedule with zero margin for delays). Rating: 4.7/5.0. Cost: ¥75 per person. Operating hours: Regular 11:00-21:30, Spring Festival 11:00-23:00. Restaurant may need 5-10 minutes after opening for service readiness. Consider backup plan if delayed. Verified via Gaode Maps POI ID: B0KB17BRRJ.":
            "⚠️ 时间紧迫：餐厅11:00开门（不会提前）。必须准时11:00到达。只有45分钟窗口期就要赶飞机（零容错高风险行程）。评分4.7，人均¥75。营业时间：平时11:00-21:30，春节11:00-23:00。如延误需考虑备选方案。",
        "虹口区自助餐口味榜第1名, MB5+澳洲和牛不限量, 需提前预约 [links: {'gaode_id': 'B0K0VNBOLW'}; rating: 4.8; signature_dishes: Australian MB5+ wagyu (multiple cuts: oyster blade, flank, snowflake sirloin), seafood sashimi, unlimited refills]":
            "虹口区自助餐口味榜第1名。MB5+澳洲和牛不限量。需提前预约。评分4.8。招牌：澳洲MB5+和牛（多部位：牛肩胛、牛腹肉、雪花西冷）、海鲜刺身、无限续加。",
        # Day 5
        "INFJ-FRIENDLY: Cozy specialty coffee shop near hotel. Perfect for morning coffee and light breakfast before city exploration. Convenient location for start of People's Square/Bund day. Verified via Gaode Maps POI ID: B0L6K9D71B.":
            "温馨精品咖啡店，靠近酒店。适合早晨喝咖啡、简单早餐后开始城市探索。位置方便。",
        "MICHELIN-RECOMMENDED: Authentic Shanghai local cuisine (本帮菜). Rating: 4.8/5.0. Cost: ¥186 per person. Operating hours: Mon-Fri 11:00-14:00, 17:00-21:30; Sat-Sun 11:00-14:00, 16:30-21:30. Famous for classic Shanghai dishes. Business area: Fenglin Road (枫林路). Verified via Gaode Maps POI ID: B0FFF407ML. Also available: Jing'an Temple Branch (静安寺店) at Yuyuan Road 142 if preferred.":
            "米其林推荐：正宗上海本帮菜。评分4.8，人均¥186。营业时间：周一至五11:00-14:00、17:00-21:30；周末11:00-14:00、16:30-21:30。经典上海菜。另有静安寺店（愚园路142号）可选。",
        "USER-SPECIFIED RESTAURANT (Option 3/3): Premium Japanese yakiniku (charcoal grill). Rating: 4.5/5.0. Cost: ¥127 per person. Operating hours: 11:30-14:00, 17:00-23:00 (Spring Festival 2026-02-16 to 2026-02-21: 16:00-22:00). High-quality grilled meats. Reservations strongly recommended. Phone: 021 6446 9999. Verified via Gaode Maps POI ID: B0FFIVKQPF and Google Maps Place ID: ChIJEXBMOhlwsjURIlaJlMRNRIM.":
            "指定餐厅：高级日式烧肉（炭烤）。评分4.5，人均¥127。营业时间：11:30-14:00、17:00-23:00（春节期间16:00-22:00）。强烈建议预约。电话：021 6446 9999。",
        # Day 6
        "Early breakfast before Shanghai Disneyland full day. Quick and convenient.":
            "迪士尼全天游玩前的早餐。快速方便。",
        "Lunch inside Disneyland. Multiple themed restaurants available. Budget for park food prices.":
            "迪士尼园内午餐。有多个主题餐厅。注意园内物价较高。",
        "Dinner at Disneyland or nearby Disneytown. Many options after park closes.":
            "迪士尼园内或迪士尼小镇晚餐。闭园后有很多选择。",
        # Day 7
        "Cozy coffee shop matching girlfriend's interests. INFJ-friendly atmosphere. Good for photography.":
            "温馨咖啡店，适合女朋友的喜好。安静舒适的氛围，适合拍照。",
        "Lunch in artsy Tianzifang area. Many cute shops and cafes nearby. Instagram-worthy.":
            "田子坊艺术区午餐。周边有很多可爱的小店和咖啡馆。适合拍照打卡。",
        "MICHELIN GUIDE restaurant. High-end dining experience. Seafood specialties. Reservations required.":
            "米其林指南餐厅。高端用餐体验。海鲜特色。需要预约。",
        # Day 8
        "Early morning flight (9:05). Quick breakfast at airport before boarding.":
            "早班飞机（9:05）。登机前在机场快速用早餐。",
        "Lunch after arrival (11:25) and before university registration. Near Haidian area.":
            "到达后午餐（11:25到）。大学注册前用餐。海淀区附近。",
        "Quick dinner before evening dance drama performance. Light meal recommended.":
            "晚间舞剧演出前快速晚餐。建议吃清淡些。",
        # Day 9
        "Hotel breakfast before girlfriend's orientation. Check-out and move to rental apartment.":
            "女朋友报到前在酒店吃早餐。退房后搬去短租公寓。",
        "University canteen experience. Authentic student dining. Affordable and convenient during campus tour.":
            "大学食堂体验。正宗学生餐，实惠方便。参观校园时顺便吃。",
        "First dinner at new rental. Establish nearby dining options for girlfriend's comfort zone.":
            "搬到新住处后的第一顿晚餐。帮女朋友熟悉附近的吃饭选择。",
        # Day 10
        "Local breakfast spot. Baozi, jianbing, or doujiang options.":
            "本地早餐店。包子、煎饼或豆浆。",
        "Lunch in university neighborhood. Many student-friendly options. After dance studio registration.":
            "大学周边午餐。学生餐选择多。舞蹈工作室注册后用餐。",
        "Wudaokou has excellent Korean food. Popular with students. Evening after girlfriend finishes class.":
            "五道口韩餐很好。学生区人气旺。女朋友下课后晚餐。",
        # Day 11
        "Wednesday - girlfriend has class. Quick breakfast near apartment.":
            "周三——女朋友上课。公寓附近快速早餐。",
        "NO FAR TRIPS (girlfriend has class). Stay near apartment during day.":
            "不要跑远（女朋友有课）。白天待在公寓附近。",
        "Evening activities possible after girlfriend's class. Casual dinner together.":
            "女朋友下课后可以安排活动。休闲晚餐。",
        # Day 12
        "Thursday - girlfriend has class. Local breakfast.":
            "周四——女朋友上课。本地早餐。",
        "Evening activities possible. Copper pot hotpot (铜锅涮肉) is Beijing specialty.":
            "晚上可以安排活动。铜锅涮肉是北京特色。",
        # Day 13
        "Friday - full day available. Breakfast before Forbidden City visit.":
            "周五——全天可用。故宫参观前吃早餐。",
        "Famous Beijing zhajiangmian (fried sauce noodles). Near Nanluoguxiang area. Authentic local food.":
            "著名的北京炸酱面。靠近南锣鼓巷。正宗地道美食。",
        "Authentic Beijing copper pot lamb hotpot (铜锅涮肉). Traditional dining experience. Near 798 or Nanluoguxiang area.":
            "正宗北京铜锅涮羊肉。传统用餐体验。靠近798或南锣鼓巷。",
        # Day 14
        "Cozy coffee shop day. INFJ-friendly atmosphere. Good for girlfriend's photography interest.":
            "舒适的咖啡店日。安静氛围。适合女朋友的摄影爱好。",
        "Lunch in Sanlitun shopping area. Many cute shops nearby. Fashion shopping opportunities.":
            "三里屯购物区午餐。周边很多可爱小店。时尚购物好去处。",
        "Dinner in artistic 798 area. Many creative restaurants. Matches girlfriend's interests.":
            "798艺术区晚餐。很多创意餐厅。符合女朋友的喜好。",
        # Day 15
        "Saturday - free day. Flexible breakfast timing.":
            "周六——自由日。早餐时间灵活。",
        "Must-try Beijing roast duck (北京烤鸭). Recommend Quanjude or Da Dong. Make reservations.":
            "必吃北京烤鸭。推荐全聚德或大董。需要预约。",
        "Casual dinner near apartment. Free day schedule.":
            "公寓附近休闲晚餐。自由日行程。",
        # Day 16
        "If Tianjin day trip: early breakfast before train. Otherwise local breakfast.":
            "如果去天津一日游：坐火车前早点吃早餐。否则就在本地吃。",
        "IF TIANJIN TRIP: Try goubuli baozi (狗不理包子), erduoyan zhagao (耳朵眼炸糕). Otherwise lunch in Beijing.":
            "如果去天津：尝尝狗不理包子、耳朵眼炸糕。否则在北京吃午餐。",
        "Return from Tianjin or Beijing dinner. Relaxed evening meal.":
            "天津返回或北京晚餐。轻松的晚餐。",
        # Day 17
        "Tuesday - girlfriend has class. Local breakfast.":
            "周二——女朋友上课。本地早餐。",
        "Evening activities possible after class. Wudaokou has good Japanese restaurants.":
            "下课后可以安排活动。五道口有不错的日本餐厅。",
        # Day 18
        "Wednesday - girlfriend has class. Local breakfast.":
            "周三——女朋友上课。本地早餐。",
        "Evening activities possible. Spicy Sichuan food. Many options in university area.":
            "晚上可以安排活动。麻辣川菜。大学城选择多。",
        # Day 19
        "Thursday - girlfriend has class. Local breakfast.":
            "周四——女朋友上课。本地早餐。",
        "Evening activities possible. Change of pace with Western food. Pizza or pasta options.":
            "晚上可以安排活动。换换口味吃西餐。披萨或意面。",
        # Day 20
        "Final day together. Special brunch experience. Make it memorable.":
            "在一起的最后一天。特别的早午餐体验。留下美好回忆。",
        "Lunch during final shopping trip. Mall dining convenient.":
            "最后一次购物时的午餐。商场内用餐方便。",
        "FINAL DINNER TOGETHER. Memorable and romantic. Choose nice restaurant with good ambiance. Make reservations.":
            "最后的告别晚餐。浪漫难忘。选一家氛围好的餐厅。需要预约。",
        # Day 21
        "Departure day. Light breakfast. Time for final goodbyes.":
            "出发日。简单早餐。最后的告别时间。",
        "Depends on departure time. Airport meal or final lunch together before goodbye.":
            "取决于出发时间。机场用餐或最后一顿午餐告别。",
        "Departure day. Likely no dinner or in-flight meal.":
            "出发日。可能没有晚餐或飞机餐。",
    }
    process_file("meals.json", meals_notes)

    # =========================================================================
    # ATTRACTIONS.JSON
    # =========================================================================
    print("Processing attractions.json...")
    attractions_notes = {
        # Day 1
        "Morning visit after luggage check-in. Panoramic views of Yangtze and Jialing rivers confluence. Breakfast at Raffles City after visit.":
            "寄存行李后上午参观。可欣赏长江和嘉陵江交汇处的全景。参观后在来福士吃早餐。",
        "Traditional Qing dynasty guild hall with ornate architecture. Located near river area, easy access from Raffles City.":
            "传统清代会馆，建筑华丽。靠近江边区域，从来福士过来交通便利。",
        "Afternoon visit. Historic riverside neighborhood with cafes, bookstores, and 熹玥盒子. Free entry, great for photography and leisurely strolling. Adjacent areas within walking distance.":
            "下午参观。历史江边街区，有咖啡馆、书店和熹玥盒子。免费入场，适合拍照和悠闲漫步。相邻区域步行可达。",
        "Optional if time permits. Famous monorail station where train passes through building. Viewing platform available. Free attraction.":
            "时间允许的话可去。著名的轻轨穿楼站。有观景平台。免费景点。",
        "Optional evening visit before hotpot dinner. Best viewed at night when illuminated. Can be crowded. Free entry.":
            "火锅晚餐前可选择游览。夜晚亮灯时最佳观赏。可能人多。免费入场。",
        # Day 2
        "Option 1 for afternoon family activity. Local scenic area with Buddhist grottos and hillside park. Free entry. Good for leisurely walk with family. Not heavily touristed. Choose between this and Wangwang Mountain based on family preference.":
            "下午家庭活动选项一。本地景区，有佛教石窟和山坡公园。免费入场。适合和家人散步。游客不多。根据家人喜好在此和望王山之间选择。",
        "Option 2 for afternoon family activity. Mountain park with observation platform (望王山仙踪观景台) near family home at 半山逸城A区. Free entry. Good views of Bazhong city. Easy hiking trails. More convenient location close to residence. Choose between this and Nankang Slope.":
            "下午家庭活动选项二。山顶公园，有望王山仙踪观景台，靠近家（半山逸城A区）。免费入场。巴中城市景色好。登山步道简单。离家近更方便。可与南龛坡二选一。",
        # Day 3
        "Evening stroll after arriving in Chengdu. Modern lifestyle district with boutiques, cafes, and restaurants. Perfect for orientation walk and dinner area exploration. Morning left free for relaxed start after 除夕 late night celebrations.":
            "到达成都后的傍晚漫步。现代生活街区，有精品店、咖啡馆和餐厅。适合熟悉环境和探索晚餐选择。上午留给除夕熬夜后的休息。",
        # Day 4
        "Arrive 9:00am, leave by 10:00am as planned. Early morning is best time to see pandas active. Book tickets online in advance. Take Metro Line 3 to Xiongmao Avenue Station. Limited 1-hour visit due to afternoon flight.":
            "计划9:00到、10:00离开。清晨是看大熊猫活跃的最佳时间。提前网上购票。乘坐地铁3号线到熊猫大道站。因下午航班只能参观1小时。",
        "Quick visit before flight. Traditional Qing dynasty style street with snacks and crafts. Free entry. Close to city center, easy access before heading to airport.":
            "飞机前快速游览。传统清代风格街道，有小吃和手工艺品。免费入场。靠近市中心，去机场前方便到达。",
        "Night view of Pudong skyline, colonial architecture illuminated. Right after dinner at Lao Gan Bei (Bund No.5). Open 24 hours.":
            "浦东天际线夜景，殖民时期建筑灯光璀璨。老乾杯（外滩5号）晚餐后直接来。全天开放。",
        # Day 5
        "INFJ-friendly specialty coffee shop on famous Anfu Road. Cozy atmosphere, photogenic interior. Rating 4.4/5. Average spend ~55 RMB per person. Open 10:00-20:00 daily. Perfect for quiet coffee break and photography. Near Changshu Road Metro Station (Line 1/7).":
            "安福路上的精品咖啡店。氛围温馨，适合拍照。评分4.4，人均约55元。每天10:00-20:00营业。适合安静喝咖啡和拍照。靠近常熟路地铁站（1/7号线）。",
        "Highly rated (4.6/5) cafe and boutique clothing store. INFJ-friendly quiet space with aesthetic design. Average spend ~45 RMB. Open 10:00-18:00 daily. Combines coffee culture with fashion shopping. Perfect for girlfriend's personality - cozy, photogenic, not crowded.":
            "高评分（4.6）咖啡馆兼精品服装店。安静美学空间。人均约45元。每天10:00-18:00营业。咖啡与时尚购物结合。温馨舒适，不拥挤。",
        "Famous tree-lined historic street in French Concession. Perfect for photography with European-style architecture. INFJ-friendly: peaceful walking area with boutique shops, cafes, and art galleries. Free to explore. Connects to Anfu Road area. Iconic Wukang Building at north end is Instagram-worthy landmark. Recommended duration: 1h.":
            "法租界著名的林荫历史街道。欧式建筑，适合拍照。安静的步行区，有精品店、咖啡馆和画廊。免费游览。与安福路相连。北端的武康大楼是标志性打卡点。建议游览1小时。",
        "Cozy English bookstore with cafe in French Concession. Rating 4.3/5. Open 10:00-22:00 daily. Perfect for girlfriend who loves English bookstores. INFJ-friendly quiet space with wide English book selection. Can browse and have coffee/tea. Also houses Taofeng Western Book Company. Recommended duration: 1h15m.":
            "法租界温馨英文书店，带咖啡。评分4.3。每天10:00-22:00营业。英文书籍丰富。可以边逛边喝咖啡。建议游览1小时15分钟。",
        "Optional if time permits. Contemporary art museum with rotating exhibitions. Waterfront location near Lujiazui. Quiet, INFJ-friendly atmosphere. Book tickets online in advance. Consider based on energy levels after walking French Concession.":
            "时间允许可去。当代美术馆，轮换展览。靠近陆家嘴的江边位置。安静。提前网上购票。根据逛完法租界后的体力决定。",
        "[opening_hours: 24h; highlights: Tree-lined lanes, art deco architecture, hidden boutiques; tips: Wander along Yongfu Road, Fuxing West Road, Hunan Road] Recommended duration: 1.5h.":
            "全天开放。亮点：林荫小巷、装饰艺术建筑、隐藏精品店。推荐路线：永福路、复兴西路、湖南路。建议游览1.5小时。",
        # Day 6
        "Full day visit. Book tickets online in advance (official app or website). Arrive early for rope drop. FastPass+ system available via app. Take Metro Line 11 to Disney Resort Station. Ticket price is standard weekday rate (varies by season). Park hours typically 9am-9pm. Popular attractions: TRON, Pirates of Caribbean, Enchanted Storybook Castle.":
            "全天游玩。提前在官方APP或官网购票。早到抢先入园。可通过APP使用快速通行证。乘坐地铁11号线到迪士尼站。票价为平日标准价（随季节变动）。乐园通常9:00-21:00营业。热门项目：创极速光轮、加勒比海盗、奇幻童话城堡。",
        # Day 7
        "TOP TOY global flagship - similar to Popmart but larger selection. Perfect for girlfriend who loves cute collectibles (潮玩店). Rating 4.7/5. Three floors of designer toys, blind boxes, anime figures. Near Nanjing East Road pedestrian street. Free entry, pay only for purchases. More curated and spacious than regular Popmart stores.":
            "TOP TOY全球旗舰店——类似泡泡玛特但品类更丰富。适合喜欢潮玩的女朋友。评分4.7。三层楼的设计师玩具、盲盒、动漫手办。靠近南京东路步行街。免费入场。",
        "Official Popmart store in popular shopping mall. Rating 4.5/5. Full range of Popmart blind boxes and collectibles. Easy access near Qufu Road Metro Station. Can visit after TOP TOY for comparison. Free browsing.":
            "热门商场内的泡泡玛特官方店。评分4.5。全系列盲盒和收藏品。靠近曲阜路地铁站。可在TOP TOY之后对比选购。免费浏览。",
        "Historic arts district with indie toy shops, boutique galleries, cafes. Rating 4.6/5. Open 24 hours but shops typically 10:00-20:00. INFJ-friendly: less touristy than Xintiandi, more authentic atmosphere. Narrow alleyways with unique shops - perfect for discovering hidden gems and photography. Free to explore.":
            "历史艺术街区，有独立潮玩店、精品画廊、咖啡馆。评分4.6。全天开放但店铺通常10:00-20:00。比新天地更有地道氛围。窄巷里的特色小店，适合发现惊喜和拍照。免费游览。",
        "If not visited on Day 5. Cozy English bookstore with cafe in French Concession. Rating 4.3/5. Open 10:00-22:00 daily. Perfect for girlfriend's love of English bookstores. INFJ-friendly quiet space. Note: Eslite Bookstore is located in Suzhou (not Shanghai), so Garden Books is the best option for English books in Shanghai.":
            "如第5天未去可补。法租界温馨英文书店，带咖啡。评分4.3。每天10:00-22:00营业。注意：诚品书店在苏州（不在上海），Garden Books是上海最佳英文书店。",
        "Specialty coffee scene on Anfu Road area. Multiple boutique cafes within walking distance: COSTA (Anfu Road 166), RACBAR (Anfu Road 322), Manner Coffee (Anfu Road 168), 13DE MARZO CAFÉ. All INFJ-friendly with cozy, photogenic interiors. See meals agent for detailed cafe recommendations and reviews.":
            "安福路精品咖啡区。步行范围内多家精品咖啡馆：COSTA（安福路166号）、RACBAR（安福路322号）、Manner Coffee（安福路168号）、13DE MARZO CAFÉ。都是温馨舒适的拍照好去处。",
        # Day 9
        "Help girlfriend establish comfort zone. Campus tour to familiarize with area. Beautiful traditional Chinese architecture mixed with modern buildings. ID required for entry (passport). May need advance registration online. Large campus, focus on main areas near student services.":
            "帮女朋友熟悉环境。校园导览。传统中式与现代建筑交融。入校需证件（护照）。可能需提前网上预约。校园很大，重点看学生服务区附近。",
        "Alternative or additional campus visit. Historic Weiming Lake (未名湖) is iconic. Similar entry requirements as Tsinghua. Both universities close to each other. Explore nearby restaurants and facilities for girlfriend's daily life support.":
            "备选或补充的校园参观。未名湖是标志性景点。入校要求同清华。两校相邻。帮女朋友探索周边的餐厅和生活设施。",
        "After campus tours, explore Wudaokou area (五道口) - student district with restaurants, cafes, supermarkets, and international food. Help girlfriend identify daily necessities locations: grocery stores, pharmacies, banks, metro stations.":
            "校园参观后探索五道口学生区——有餐厅、咖啡馆、超市和国际美食。帮女朋友找到日常所需：便利店、药店、银行、地铁站。",
        # Day 10
        "Continue establishing girlfriend's comfort zone. After dance studio registration, explore more local amenities. Evening activities possible after class.":
            "继续帮女朋友熟悉环境。舞蹈工作室注册后探索更多周边设施。下课后可安排晚间活动。",
        # Day 13
        "Full day available. Book tickets online in advance (mandatory, through official website). Enter from Meridian Gate (午门), exit from Gate of Divine Prowess (神武门). Audio guide recommended. Allow 3-4 hours minimum. Avoid Tuesdays (closed). Popular palaces: Hall of Supreme Harmony, Imperial Garden, Palace of Gathered Elegance, Clock Museum.":
            "全天可用。需提前在官网购票（必须）。从午门进、神武门出。建议租语音导览。至少预留3-4小时。周二闭馆。热门宫殿：太和殿、御花园、储秀宫、钟表馆。",
        "Choose based on interest: (1) Nanluoguxiang - historic hutong alley with cafes, boutiques, traditional architecture. Touristy but charming. Closer to Forbidden City. (2) 798 Art District - contemporary art galleries in former factory complex. Less crowded, more INFJ-friendly. Modern art scene. Both free entry. 798 requires taxi/Didi from city center.":
            "根据兴趣选择：(1) 南锣鼓巷——历史胡同，有咖啡馆、精品店、传统建筑。游客多但有韵味。靠近故宫。(2) 798艺术区——旧工厂改造的当代艺术画廊。人少，更安静。都免费。798需从市中心打车。",
        # Day 14
        "Explore Beijing's specialty coffee scene and designer toy shops. Sanlitun area has many lifestyle boutiques. See meals and shopping agents for specific recommendations.":
            "探索北京精品咖啡和设计师潮玩店。三里屯有很多生活方式精品店。",
        "If desired. Major shopping districts: Sanlitun Taikoo Li (high-end, similar to Chengdu Taikoo Li), Xidan (mid-range Chinese brands), Wangfujing (department stores). See shopping agent for details.":
            "如果需要购物。主要购物区：三里屯太古里（高端，类似成都太古里）、西单（中端国产品牌）、王府井（百货商场）。",
        # Day 15
        "Options: (1) Temple of Heaven Park (天坛) - historic temple complex with beautiful architecture. (2) Summer Palace (颐和园) - imperial garden with Kunming Lake. (3) Jingshan Park (景山公园) - hill park behind Forbidden City with panoramic city views. (4) More hutong exploration. (5) Museums: National Museum, Capital Museum. Plan based on weather and mood.":
            "可选：(1) 天坛——历史古建筑群。(2) 颐和园——皇家园林，有昆明湖。(3) 景山公园——故宫后面的山顶公园，可看城市全景。(4) 胡同探索。(5) 博物馆：国家博物馆、首都博物馆。根据天气和心情决定。",
        # Day 16
        "If desired, day trip to Tianjin. High-speed train 30 minutes from Beijing South Station to Tianjin. Attractions: (1) Italian Style Street (意大利风情街) - European architecture. (2) Ancient Culture Street (古文化街) - traditional shops and temples. (3) Haihe River waterfront. (4) Five Great Avenues (五大道) - colonial-era mansions, good for photography. (5) Porcelain House (瓷房子) - unique museum. Train cost ~54 RMB one-way.":
            "可选天津一日游。北京南站高铁30分钟到天津。景点：(1) 意大利风情街——欧式建筑。(2) 古文化街——传统店铺和寺庙。(3) 海河滨水区。(4) 五大道——殖民时期洋楼，适合拍照。(5) 瓷房子——独特博物馆。高铁单程约54元。",
        "If not going to Tianjin, more Beijing exploration. Options same as Day 15. Or relaxed day at cafes and local neighborhoods.":
            "不去天津的话继续探索北京。选项同第15天。或者在咖啡馆和周边放松一天。",
        # Day 20
        "Last full day together. Options: (1) Revisit favorite spots from trip. (2) Final shopping for gifts/souvenirs. (3) Lama Temple (雍和宫) - beautiful Tibetan Buddhist temple. (4) National Centre for Performing Arts if special show available. (5) Romantic dinner at special restaurant (see meals agent). (6) Photography at scenic spots. Make it memorable.":
            "在一起的最后一整天。选项：(1) 重访旅途中喜欢的地方。(2) 最后买礼物/纪念品。(3) 雍和宫——藏传佛教寺庙。(4) 国家大剧院（如有演出）。(5) 特别餐厅浪漫晚餐。(6) 景点拍照留念。留下美好回忆。",
    }
    process_file("attractions.json", attractions_notes)

    # =========================================================================
    # ENTERTAINMENT.JSON
    # =========================================================================
    print("Processing entertainment.json...")
    entertainment_notes = {
        # Day 1
        "HIGHEST RATED ALTERNATIVE (165 likes, 7 comments on RedNote, 4.7 Gaode rating). Cheaper than competitor Gold Impression. 80min basic service. Can stay overnight as budget accommodation. Great food options: beef noodle, Chongqing xiaomian, chicken offal. Self-serve buffet 11:30-14:00 & 17:30-21:00 (+59 RMB). Clean environment, updated movies/TV shows. Holiday note: Book ahead or arrive early. Gaode verified cost: 182 RMB avg.":
            "最高评分替代选择（小红书165赞、7评论，高德评分4.7）。比竞品金印象便宜。80分钟基础服务。可过夜当经济住宿。餐食不错：牛肉面、重庆小面、鸡杂。自助餐11:30-14:00和17:30-21:00（加59元）。环境干净。节假日建议提前预订。人均182元。",
        # Day 2
        "TRADITIONAL AFTERNOON ACTIVITY - Making dumplings is done in the AFTERNOON (13:00-15:00), NOT evening, to prepare for 守岁 midnight eating. This is the authentic timing for 除夕 dumpling preparation in Chinese families. Visual, hands-on activity requiring minimal Chinese. Dumpling-making is universal across China/Japan/Korea (similar to gyoza/mandu) - perfect conversation bridge for girlfriend's Asian culture interest. Family members demonstrate folding techniques, girlfriend follows visually. Traditionally includes hiding coins/peanuts for good fortune - fun, low-pressure surprise element. User can translate simple instructions ('fold here', 'press edges'). Activity naturally includes passive elders who can demonstrate traditional techniques. Duration: ~90-120 minutes. These dumplings will be eaten at midnight (守岁), creating connection between afternoon activity and midnight tradition.":
            "传统下午活动——包饺子在下午（13:00-15:00）进行，不是晚上，为守岁零点吃做准备。这是除夕包饺子的正宗时间。动手活动，不太需要语言交流。包饺子在中日韩都有（类似饺子/煎饺/馒头），是女朋友了解亚洲文化的好桥梁。家人示范包法，女朋友看着学。传统上会包硬币/花生寓意好运。约90-120分钟。这些饺子将在守岁零点时吃。",
        "FLEXIBLE AFTERNOON-EVENING TRANSITION (15:00-18:00) - After dumpling-making, this is unstructured family time before 年夜饭 (reunion dinner). No scheduled activities - authentic Chinese family 除夕 afternoon rhythm. Options include: rest/nap (girlfriend may have jet lag from France, 14-hour time difference from Paris), help prepare New Year's Eve dinner in kitchen with family members (optional participation), put up Spring Festival couplets/福字 decorations if not already done (traditional last-minute activity), natural family time chatting/watching TV/relaxing, give girlfriend space to adapt and recharge (first meeting with family, introverted personality needs quiet time). LOW-PRESSURE PERIOD: No expectations, no performance required. Girlfriend chooses based on energy level and comfort. User available to translate if needed but also gives space. Some family members may nap (common after lunch and dumpling-making). Natural buffer before evening festivities begin. Duration: ~3 hours until dinner preparation intensifies around 17:30-18:00.":
            "灵活的下午到傍晚过渡（15:00-18:00）。包完饺子后的自由家庭时间，年夜饭前无固定安排。正宗中国家庭除夕下午节奏。可选：休息/小睡（女朋友可能有时差）、帮忙准备年夜饭（自愿参与）、贴春联/福字（传统活动）、聊天/看电视/放松。无压力时段。女朋友根据精力和舒适度自行选择。约3小时直到17:30-18:00开始备餐。",
        "NATURAL 除夕夜 FLOW - Reunion dinner (年夜饭) starts around 18:30-19:30. At 20:00, CCTV Spring Festival Gala (春晚) turns on as BACKGROUND while eating, chatting, drinking tea. This is NOT a scheduled 'activity' - it's what Chinese families naturally do on 除夕夜. 春晚 runs in background while conversations happen naturally. No forced 'photo viewing time' or 'story discussion segments' - these happen ORGANICALLY during dinner if they happen at all. Family might comment on performances, girlfriend watches visual acts (dance, acrobatics, martial arts), user whispers brief translations if needed. Low-pressure: focus is on BEING TOGETHER, not performing or entertaining. Conversations about France, family, traditions happen naturally WITHOUT scheduling them. English subtitles available via CGTN YouTube livestream (https://www.youtube.com/@ChinaGlobalTVNetwork) or iQIYI International - set up laptop/tablet for girlfriend if desired. Duration: 18:30-23:45 (natural flow, no rigid timeline).":
            "自然的除夕夜流程。年夜饭约18:30-19:30开始。20:00春晚作为背景播放，边吃边聊边喝茶。这不是刻意安排的'活动'——是中国家庭除夕夜的自然状态。春晚在背景播放，聊天自然发生。家人可能评论节目，女朋友看视觉表演（舞蹈、杂技、武术）。重点是一家人在一起。英文字幕可通过CGTN YouTube或爱奇艺国际版观看。18:30-23:45自然流动，无固定时间表。",
        "守岁 TRADITION - 'Guarding the Year' (一夜連雙歲 'one night connecting two years') - families stay awake to welcome the new year, symbolizes longevity for parents. At midnight (00:00 Feb 17), family eats the dumplings MADE IN AFTERNOON (13:00-15:00), NOT fresh ones. This connects afternoon preparation activity to midnight eating ritual. Small fireworks if permitted in Bazhong. LOW-PRESSURE RITUAL: Simple actions (eating together, watching fireworks), minimal speaking required. Girlfriend participates through presence and shared experience, not performance. User explains simple symbolism: 'Staying awake brings luck to parents' (15-second explanation). Introverted-friendly: focus is on the MOMENT and family togetherness, not individual attention. Natural conclusion to evening - signals rest time approaching. If girlfriend tired from Day 1 travel (arrived Chongqing 14:30, then train to Bazhong), she can rest earlier without judgment - Chinese families understand exhaustion.":
            "守岁传统——'一夜连双岁'，一家人守夜迎新年，象征给父母添寿。零点（2月17日00:00）吃下午包的饺子（不是现包的）。下午包饺子和零点吃连接在一起。如巴中允许可放小烟花。简单仪式：一起吃饺子、看烟花，不需要多说话。女朋友通过在场和共同体验参与。如果太累可以提前休息，家人都理解。",
        # Day 5
        "Trendy specialty coffee on Anfu Road in the heart of French Concession. Popular with locals and visitors. Part of Day 5 French Concession walking tour.":
            "安福路上的时尚精品咖啡。法租界核心区域。当地人和游客都爱来。第5天法租界漫步行程的一部分。",
        "Unique cafe-boutique hybrid on Anfu Road. Combines specialty coffee with curated designer clothing. Rating 4.6/5. Part of Day 5 French Concession walking tour.":
            "安福路上独特的咖啡馆+精品服装店。精品咖啡与设计师服饰结合。评分4.6。第5天法租界漫步行程的一部分。",
        "Iconic English-language bookstore and cafe in the French Concession. Great for browsing with coffee. Rating 4.3/5. Free entry, pay for purchases. Part of Day 5 French Concession walking tour.":
            "法租界标志性英文书店兼咖啡馆。适合边喝咖啡边逛书。评分4.3。免费入场。第5天法租界漫步行程的一部分。",
        # Day 7
        "Popmart alternative with collectible toys, plushies, blind boxes. Features Sanrio, Disney, Line Friends. Has café on 3rd floor. Budget is estimated for purchases.":
            "泡泡玛特替代——收藏玩具、毛绒、盲盒。有三丽鸥、迪士尼、Line Friends。3楼有咖啡馆。预算为估计购买费用。",
        "Widest selection of English-language books in Shanghai. Ground floor has ice-cream parlor/café for browsing. Budget for book purchases.":
            "上海最全的英文书籍。一楼有冰淇淋店/咖啡馆。预算为购书费用。",
        "Nine-floor establishment, biggest foreign bookstore. Ground floor has cheap Signet, Collins, Bantam Classics, Penguin Classics, recent releases.":
            "九层楼的上海最大外文书店。一楼有平价的Signet、Collins、Bantam经典、企鹅经典和新书。",
        "Described as perhaps Shanghai's best coffee shop overall. Beautifully made coffee. Hidden gem atmosphere.":
            "被誉为上海最好的咖啡店之一。咖啡制作精美。隐秘宝藏氛围。",
        # Day 8
        "CRITICAL: Must verify February 2026 schedule - not yet confirmed. Typical ticket prices: 180-980 RMB. Book via National Centre official website, WeChat 'guojiadadjuyuanzhihuiguanjia', or hotline 66550000. Book 1-2 months in advance. Performance duration ~90 minutes. Plan dinner before 18:00 to arrive on time.":
            "重要：需确认2026年2月演出时间——尚未确认。票价通常180-980元。通过国家大剧院官网、微信'国家大剧院智慧管家'或热线66550000购票。提前1-2个月预订。演出约90分钟。18:00前吃完晚餐以准时到场。",
        # Day 10
        "Official academy accepting international students since 1955. Nearly 100 professional dance classrooms. Visit international student office for registration. Website: https://international.bda.edu.cn. This is for registration/tour, not a dance class. Actual class registration and fees TBD.":
            "1955年起招收国际学生的官方舞蹈学院。近100间专业舞蹈教室。到国际学生办公室注册。网站：https://international.bda.edu.cn。本次为注册/参观，非上课。实际课程和费用待定。",
        "Popular with international students. Has rooftop open-air café. Near Wudaokou subway. Great for university neighborhood exploration.":
            "国际学生常去。有露天屋顶咖啡区。靠近五道口地铁站。适合探索大学周边。",
        # Day 11
        "11-year establishment. Underground space in 'Secret Garden' fairy tale style. Over 30 varieties of specialty hand-brewed coffee. Professional bar area. Cozy atmosphere perfect for evening after girlfriend's class.":
            "开了11年的老店。地下空间，'秘密花园'童话风格。30多种精品手冲咖啡。专业吧台。女朋友下课后来这里很舒服。",
        # Day 12
        "Beautiful spaces and quality coffee. Quiet, orderly atmosphere. Good for post-class relaxation.":
            "空间美，咖啡好。安静有序的氛围。适合下课后放松。",
        # Day 13
        "BOOKING REQUIRED: Options include Wave Soda (WAVESODA摄影工作室) at Jingyuan Art Centre (~2,388 RMB for 2 costumes, 2 sets, 12 photos) or Himo Studio (海马体照相馆, 600 locations nationwide). Book 2-3 weeks in advance. Session duration: 2-3 hours. Scheduled on Friday to avoid Tue/Wed/Thu class days.":
            "需预约：可选Wave Soda（WAVESODA摄影工作室，景源艺术中心，约2388元含2套服装、2个场景、12张照片）或海马体照相馆（全国600家）。提前2-3周预约。拍摄2-3小时。安排在周五避开周二至周四上课。",
        # Day 14
        "Over 1000 art toys, 9 categories including Blind Boxes, Garage Kits, Gundam Models, Lego. Popularizes designer toys. Budget for purchases.":
            "超过1000款潮玩，9大品类含盲盒、手办、高达模型、乐高。推广设计师玩具。预算为购买费用。",
        "Upscale international toy retailers. FAO is Asia's first flagship. Hamleys is one of largest single-building toy stores. Budget for cute toys and souvenirs.":
            "高端国际玩具零售商。FAO是亚洲首家旗舰店。Hamleys是最大的单体玩具店之一。预算为购买可爱玩具和纪念品。",
        "International chain with wide range of English books. Fiction, non-fiction, bestsellers, classics. Budget for book purchases.":
            "国际连锁书店，英文书籍丰富。小说、非虚构、畅销书、经典。预算为购书费用。",
        # Day 15
        "Iconic destination for international readers. Extensive collection of foreign-language books, particularly English.":
            "国际读者的标志性目的地。外文书籍收藏丰富，尤其是英文。",
        "Second floor has large range of English-language editions and small cafe. Good for browsing and relaxing.":
            "二楼有大量英文版书籍和小咖啡区。适合浏览和放松。",
        # Day 17
        "Evening exploration of niche coffee shops after girlfriend's class. Visit 2-3 shops discovered earlier in trip.":
            "女朋友下课后探索小众咖啡店。去之前发现的2-3家店。",
        # Day 20
        "Last chance for cute toy purchases and memorable souvenirs. Visit favorite spots from earlier days. Budget for final purchases.":
            "最后一次购买可爱玩具和纪念品的机会。重访之前喜欢的店。最后的购物预算。",
    }
    process_file("entertainment.json", entertainment_notes)

    # =========================================================================
    # ACCOMMODATION.JSON
    # =========================================================================
    print("Processing accommodation.json...")
    accommodation_notes = {
        # Day 1
        "Luxury 5-star hotel in Raffles City complex. Check luggage early morning (4:40am arrival). Visit observation deck before breakfast. Late check-in at 23:00 after spa visit. Rate estimated at €80-100/night. Recent reviews highlight excellent breakfast variety, stunning views, and professional service.":
            "来福士综合体内的豪华五星级酒店。凌晨4:40到达先寄存行李。早餐前参观观景台。23:00做完足疗后入住。房价估计€80-100/晚。好评：早餐丰富、景色绝佳、服务专业。",
        # Day 2
        "Chinese New Year celebration with family. No cost. Staying with family. Arrive 11:00 after train from Chongqing.":
            "和家人一起过年。免费住宿。从重庆坐火车11:00到达。",
        # Day 3
        "One night stay at family home in Chengdu. No cost. Convenient for early morning panda base visit. Arrive 15:45 after train from Bazhong.":
            "成都家中住一晚。免费。方便第二天一早去熊猫基地。巴中坐火车15:45到达。",
        # Day 4
        "New hotel (opened 2026). Boutique mid-range hotel with modern amenities. Excellent location 400m from Nanjing Road Pedestrian Street. Late check-in at 18:50 after flight from Chengdu. Rate estimated at €65-85/night. Booking required for exact rates.":
            "新开业酒店（2026年开业）。精品中端酒店，设施现代。距南京路步行街400米位置极佳。成都飞来后18:50入住。房价估计€65-85/晚。需预订确认具体价格。",
        # Day 5
        "Second night at same hotel. No check-in required":
            "同一酒店第二晚。无需办理入住。",
        # Day 6
        "Third night at same hotel. Convenient for Disneyland day trip":
            "同一酒店第三晚。方便去迪士尼一日游。",
        # Day 7
        "Fourth and final night in Shanghai. Check out Feb 22 morning for 9:05am flight to Beijing":
            "上海第四晚也是最后一晚。2月22日早上退房赶9:05飞北京的航班。",
        # Day 8
        "Budget hotel chain (Orange Hotels). One night only. Convenient for university area. Rate estimated at €35-45/night. Book through Trip.com or Ctrip":
            "连锁经济型酒店（桔子酒店）。仅住一晚。靠近大学区域方便。房价估计€35-45/晚。通过Trip.com或携程预订。",
        # Day 9
        "13 nights total (Feb 23 - Mar 7). Estimated 4,000-6,000 RMB/month (€500-750/month). Daily rate calculated at ~€35/night for mid-range apartment. Location TBD but should be near Tsinghua/Peking University for girlfriend's classes. Book through Ziroom app (English interface available) or Airbnb China [total_for_stay: 455]":
            "共13晚（2月23日至3月7日）。预计月租4000-6000元（€500-750/月）。日均约€35/晚的中端公寓。位置待定，需靠近清华/北大方便女朋友上课。通过自如APP（有英文界面）或Airbnb中国预订。",
        # Days 10-20 (all same)
        "Continuing stay in rental apartment":
            "继续住在短租公寓。",
        # Day 21
        "Final night in rental apartment. Check out for departure":
            "短租公寓最后一晚。退房出发。",
    }
    process_file("accommodation.json", accommodation_notes)

    # =========================================================================
    # TRANSPORTATION.JSON
    # =========================================================================
    print("Processing transportation.json...")
    transportation_notes = {
        # Day 2 main
        "✅ SCHEDULE VERIFIED BY USER. Depart Chongqing North 07:26, arrive Bazhong East 10:36. Total journey including hotel→station→home: ~5 hours. Wake up 05:30, depart hotel 06:00, arrive station 06:45, board at 07:15, depart 07:26, arrive 10:36, reach family home by 11:30. Chinese New Year Eve (除夕) - most important reunion day.":
            "✅ 用户已确认时刻表。重庆北07:26出发，巴中东10:36到达。全程含酒店→车站→家约5小时。05:30起床，06:00出发，06:45到站，07:15上车，07:26发车，10:36到达，11:30到家。除夕——最重要的团圆日。",
        # Day 2 verified_train notes
        "VERIFIED schedule. User confirmed: 重庆北 07:26 → 巴中东 10:36. Book on January 17, 2026 at 8:00am (30 days before departure).":
            "✅ 已确认时刻表。重庆北07:26 → 巴中东10:36。2026年1月17日早8:00开抢（发车前30天）。",
        # Day 2 local transport notes
        "Coordinate with family in advance. Bazhong East Station is ~15km from city center.":
            "提前和家人协调。巴中东站距市中心约15公里。",
        "Public bus from Bazhong East Station to city center":
            "巴中东站到市中心的公交车。",
        "Direct to 半山逸城A区":
            "直达半山逸城A区。",
        # Day 3 main
        "✅ VERIFIED BY USER. 巴中西站 12:42 → 成都东站 14:52 (2h 10min). ⚠️ IMPORTANT: Bazhong WEST Station (巴中西站), NOT Bazhong East (巴中东站). Timeline: 07:00 拜年 with family, 09:00 breakfast at 老五酱肉包子 (MUST-VISIT), 11:00 lunch at 老七牛肉 (MUST-VISIT), 12:00 taxi to 巴中西站, 12:42 train departs, 14:52 arrive 成都东, 15:30 check-in hotel, 17:00 dinner at Taolin Restaurant Taikoo Li (1/3 required Chengdu restaurants).":
            "✅ 用户已确认。巴中西站12:42 → 成都东站14:52（2小时10分钟）。⚠️ 注意：从巴中西站出发，不是巴中东站。行程：07:00拜年，09:00老五酱肉包子（必去），11:00老七牛肉（必去），12:00打车去巴中西站，12:42发车，14:52到成都东，15:30入住，17:00晚餐。",
        # Day 3 verified_train notes
        "VERIFIED schedule. User confirmed: 巴中西 12:42 → 成都东 14:52. ⚠️ NOTE: Departs from Bazhong WEST Station (巴中西站), NOT Bazhong East. Allow time for travel from family home to correct station.":
            "✅ 已确认时刻表。巴中西12:42 → 成都东14:52。⚠️ 注意：从巴中西站出发，不是巴中东站。预留从家到正确车站的时间。",
        # Day 4 main
        "Flight ALREADY BOOKED. CA4509 departs 14:35 from CTU T2, arrives PVG T2 at 17:20. Morning itinerary: Home (07:00) → Mingting Restaurant breakfast (07:24-08:00) → Giant Panda Base (08:51-10:00) → Taikoo Li shopping (11:01-12:00) → Shuangliu Airport T2 (13:11) → Flight (14:35). Evening itinerary: Pudong Airport T2 (17:20) → Hotel check-in (18:50) → Bund Night Walk (19:15-20:15) → Taxi to Aimuniu (20:15-20:30) → Dinner (20:30-22:30) → Taxi to hotel (22:30-22:50). Total morning routes: 207 minutes. Total evening routes: 40 minutes (5 min walk + 35 min taxi). CRITICAL: Must depart Taikoo Li by 12:00 to allow 95-minute buffer before check-in deadline. Use Metro Line 3 for airport route (fastest, most reliable during Spring Festival). Total Day 4 Shanghai transport cost: ¥70 (~$9.90). Morning: ¥15 (metro/bus). Evening: ¥55 (taxis).":
            "机票已订。CA4509 成都双流T2 14:35起飞，上海浦东T2 17:20到达。上午行程：07:00出发→07:24明婷小馆早餐→08:51熊猫基地→11:01太古里购物→13:11到机场T2→14:35起飞。晚间：17:20浦东到达→18:50酒店入住→19:15外滩夜景→20:30爱牧牛晚餐→22:50回酒店。关键：12:00前必须离开太古里赶飞机。地铁3号线去机场（最快最稳）。第4天上海交通费约¥70。",
        # Day 8 main
        "Flight ALREADY BOOKED. Departure 09:05 from PVG T1, arrival 11:25 at Beijing Daxing. Total journey ~4.5h including airport transfers. Must leave hotel by 06:30 to allow 2.5h buffer. Hotel to Pudong T1: ~1.5h by metro (Line 2). Beijing Daxing to Orange Hotel (中关村): ~2h by Daxing Airport Express + subway Line 4 + Line 10. Afternoon university registration, evening dance drama '只此青绿'. Tight schedule requires efficient airport transfers.":
            "机票已订。浦东T1 09:05起飞，北京大兴11:25到达。含机场接驳全程约4.5小时。06:30前必须离开酒店。酒店到浦东T1约1.5小时（地铁2号线）。大兴到桔子酒店（中关村）约2小时（大兴机场快线+4号线+10号线）。下午大学注册，晚上看舞剧《只此青绿》。行程紧凑需高效换乘。",
    }
    process_file("transportation.json", transportation_notes)

    print("\nAll files processed successfully!")
    print("Run 'python -m json.tool <file>' to verify JSON validity if needed.")


if __name__ == "__main__":
    main()
