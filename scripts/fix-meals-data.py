#!/usr/bin/env python3
"""
Fix meals agent data for both trips.
- Trip 1 (china itinerary): Add signature_dishes_base and signature_dishes_local
- Trip 2 (bucket list): Add currency_local, time, cuisine_local, signature_dishes_base/local, notes_local
"""

import json
import sys
from pathlib import Path


def fix_trip1(filepath: str) -> None:
    """Add signature_dishes_base and signature_dishes_local to all 63 meals in Trip 1."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Mapping: (day, meal_type) -> (signature_dishes_base, signature_dishes_local)
    # Based on restaurant name, cuisine, and context
    sig_dishes = {
        # Day 1 - Chongqing
        (1, "breakfast"): (
            "Chongqing xiaomian, steamed buns, soy milk",
            "重庆小面, 馒头, 豆浆"
        ),
        (1, "lunch"): (
            "Spicy boiled fish, Chongqing laziji, stir-fried tripe",
            "水煮鱼, 重庆辣子鸡, 爆炒毛肚"
        ),
        (1, "dinner"): (
            "Spicy beef hotpot, fresh duck intestines, sliced lotus root",
            "麻辣牛油火锅, 鲜鸭肠, 藕片"
        ),
        # Day 2 - Bazhong (home meals)
        (2, "breakfast"): (
            "Homemade dumplings, congee, pickled vegetables",
            "家常水饺, 稀饭, 泡菜"
        ),
        (2, "lunch"): (
            "Braised pork belly, stir-fried vegetables, steamed rice",
            "红烧肉, 炒时蔬, 蒸米饭"
        ),
        (2, "dinner"): (
            "Sichuan reunion feast, braised whole fish, mapo tofu, stir-fried pork with chili",
            "四川年夜饭, 红烧全鱼, 麻婆豆腐, 回锅肉"
        ),
        # Day 3 - Bazhong -> Chengdu
        (3, "breakfast"): (
            "Sauce meat buns, mung bean porridge, pickled radish",
            "酱肉包子, 绿豆粥, 泡萝卜"
        ),
        (3, "lunch"): (
            "Braised beef noodles, cold beef slices, beef offal soup",
            "红烧牛肉面, 凉拌牛肉, 牛杂汤"
        ),
        (3, "dinner"): (
            "Fish-flavored shredded pork, kung pao chicken, seasonal bamboo shoots",
            "鱼香肉丝, 宫保鸡丁, 时令竹笋"
        ),
        # Day 4 - Chengdu -> Shanghai
        (4, "breakfast"): (
            "Sichuan spicy wontons, red oil chaoshou, clear soup chaoshou",
            "四川红油抄手, 龙抄手, 清汤抄手"
        ),
        (4, "lunch"): (
            "Twice-cooked pork, mapo tofu, dan dan noodles",
            "回锅肉, 麻婆豆腐, 担担面"
        ),
        (4, "dinner"): (
            "Australian MB5+ wagyu, snowflake sirloin, seafood sashimi platter",
            "澳洲MB5+和牛, 雪花西冷, 海鲜刺身拼盘"
        ),
        # Day 5 - Shanghai
        (5, "breakfast"): (
            "Specialty pour-over coffee, avocado toast, croissant",
            "手冲精品咖啡, 牛油果吐司, 可颂"
        ),
        (5, "lunch"): (
            "Braised pork belly Shanghai-style, smoked fish, crystal shrimp",
            "上海红烧肉, 熏鱼, 水晶虾仁"
        ),
        (5, "dinner"): (
            "Premium wagyu yakiniku, harami skirt steak, karubi short rib",
            "特选和牛烧肉, 横膈膜肉, 牛小排"
        ),
        # Day 6 - Shanghai (Disneyland)
        (6, "breakfast"): (
            "Congee, steamed buns, tea eggs",
            "粥, 馒头, 茶叶蛋"
        ),
        (6, "lunch"): (
            "Themed park burgers, chicken tenders, seasonal specials",
            "主题园区汉堡, 炸鸡块, 季节限定套餐"
        ),
        (6, "dinner"): (
            "Pizza, pasta, themed desserts",
            "披萨, 意面, 主题甜点"
        ),
        # Day 7 - Shanghai
        (7, "breakfast"): (
            "Oat latte, breakfast sandwich, fresh pastry",
            "燕麦拿铁, 早餐三明治, 现烤糕点"
        ),
        (7, "lunch"): (
            "Shanghai braised pork, lion's head meatball, steamed crab",
            "上海红烧肉, 红烧狮子头, 清蒸大闸蟹"
        ),
        (7, "dinner"): (
            "Jiaodong sea cucumber, nine-turn large intestine, dezhou braised chicken",
            "胶东海参, 九转大肠, 德州扒鸡"
        ),
        # Day 8 - Shanghai -> Beijing
        (8, "breakfast"): (
            "Congee, steamed buns, tea eggs",
            "粥, 馒头, 茶叶蛋"
        ),
        (8, "lunch"): (
            "Braised noodles, fried rice, stir-fried vegetables",
            "炸酱面, 蛋炒饭, 炒青菜"
        ),
        (8, "dinner"): (
            "Quick noodles, dumplings, cold dishes",
            "拉面, 水饺, 凉菜拼盘"
        ),
        # Day 9 - Beijing
        (9, "breakfast"): (
            "Congee, steamed buns, tea eggs",
            "粥, 馒头, 茶叶蛋"
        ),
        (9, "lunch"): (
            "Canteen braised pork, mapo tofu, stir-fried greens",
            "食堂红烧肉, 麻婆豆腐, 炒青菜"
        ),
        (9, "dinner"): (
            "Stir-fried dishes, braised eggplant, tomato egg soup",
            "家常炒菜, 红烧茄子, 番茄蛋汤"
        ),
        # Day 10 - Beijing
        (10, "breakfast"): (
            "Jianbing, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (10, "lunch"): (
            "Braised noodles, fried rice, stir-fried dishes",
            "炸酱面, 蛋炒饭, 小炒菜"
        ),
        (10, "dinner"): (
            "Korean BBQ, bibimbap, kimchi jjigae",
            "韩式烤肉, 石锅拌饭, 泡菜汤"
        ),
        # Day 11 - Beijing
        (11, "breakfast"): (
            "Jianbing, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (11, "lunch"): (
            "Braised noodles, dumplings, stir-fried greens",
            "炸酱面, 饺子, 炒青菜"
        ),
        (11, "dinner"): (
            "Stir-fried dishes, braised chicken, rice",
            "家常炒菜, 黄焖鸡, 米饭"
        ),
        # Day 12 - Beijing
        (12, "breakfast"): (
            "Jianbing, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (12, "lunch"): (
            "Braised noodles, dumplings, stir-fried greens",
            "炸酱面, 饺子, 炒青菜"
        ),
        (12, "dinner"): (
            "Copper pot lamb, sesame sauce dip, frozen tofu",
            "铜锅涮羊肉, 麻酱蘸料, 冻豆腐"
        ),
        # Day 13 - Beijing
        (13, "breakfast"): (
            "Baozi, millet porridge, pickled vegetables",
            "包子, 小米粥, 咸菜"
        ),
        (13, "lunch"): (
            "Beijing zhajiang noodles, pickled garlic, cucumber strips",
            "老北京炸酱面, 腊八蒜, 黄瓜丝"
        ),
        (13, "dinner"): (
            "Copper pot lamb slices, sesame dip, Chinese cabbage",
            "手切鲜羊肉, 麻酱小料, 白菜豆腐"
        ),
        # Day 14 - Beijing
        (14, "breakfast"): (
            "Flat white, croissant, fresh fruit bowl",
            "澳白咖啡, 可颂, 鲜果碗"
        ),
        (14, "lunch"): (
            "Fusion tacos, craft burgers, artisanal salads",
            "创意塔可, 手工汉堡, 精品沙拉"
        ),
        (14, "dinner"): (
            "Creative fusion dishes, artisan pizza, craft cocktails",
            "创意融合菜, 手工披萨, 精酿鸡尾酒"
        ),
        # Day 15 - Beijing
        (15, "breakfast"): (
            "Jianbing, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (15, "lunch"): (
            "Whole roast duck, duck pancakes, duck soup",
            "整只烤鸭, 鸭饼卷, 鸭架汤"
        ),
        (15, "dinner"): (
            "Stir-fried dishes, braised eggplant, tomato egg",
            "家常炒菜, 红烧茄子, 番茄炒蛋"
        ),
        # Day 16 - Beijing/Tianjin
        (16, "breakfast"): (
            "Jianbing guozi, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (16, "lunch"): (
            "Goubuli steamed buns, erduoyan fried cake, guifaxiang mahua",
            "狗不理包子, 耳朵眼炸糕, 桂发祥麻花"
        ),
        (16, "dinner"): (
            "Stir-fried dishes, braised noodles, cold appetizers",
            "家常炒菜, 炸酱面, 凉菜"
        ),
        # Day 17 - Beijing
        (17, "breakfast"): (
            "Jianbing, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (17, "lunch"): (
            "Braised noodles, dumplings, stir-fried greens",
            "炸酱面, 饺子, 炒青菜"
        ),
        (17, "dinner"): (
            "Tonkotsu ramen, gyoza, grilled skewers",
            "豚骨拉面, 煎饺, 烤串"
        ),
        # Day 18 - Beijing
        (18, "breakfast"): (
            "Jianbing, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (18, "lunch"): (
            "Braised noodles, dumplings, stir-fried greens",
            "炸酱面, 饺子, 炒青菜"
        ),
        (18, "dinner"): (
            "Mapo tofu, boiled fish in chili oil, dan dan noodles",
            "麻婆豆腐, 水煮鱼, 担担面"
        ),
        # Day 19 - Beijing
        (19, "breakfast"): (
            "Jianbing, soy milk, fried dough sticks",
            "煎饼果子, 豆浆, 油条"
        ),
        (19, "lunch"): (
            "Braised noodles, dumplings, stir-fried greens",
            "炸酱面, 饺子, 炒青菜"
        ),
        (19, "dinner"): (
            "Margherita pizza, carbonara pasta, tiramisu",
            "玛格丽特披萨, 卡邦尼意面, 提拉米苏"
        ),
        # Day 20 - Beijing
        (20, "breakfast"): (
            "Eggs Benedict, pancakes, fresh juice",
            "班尼迪克蛋, 松饼, 鲜榨果汁"
        ),
        (20, "lunch"): (
            "Shopping mall set lunch, pasta, salad",
            "商场套餐, 意面, 沙拉"
        ),
        (20, "dinner"): (
            "Peking duck, imperial court dishes, abalone",
            "北京烤鸭, 宫廷菜, 鲍鱼"
        ),
        # Day 21 - Beijing (departure)
        (21, "breakfast"): (
            "Baozi, millet porridge, pickled vegetables",
            "包子, 小米粥, 咸菜"
        ),
        (21, "lunch"): (
            "Congee, steamed buns, tea eggs",
            "粥, 馒头, 茶叶蛋"
        ),
        (21, "dinner"): (
            "N/A - Departure",
            "不适用 - 出发日"
        ),
    }

    meal_types = ["breakfast", "lunch", "dinner"]
    updated_count = 0

    for day_obj in data["data"]["days"]:
        day_num = day_obj["day"]
        for meal_type in meal_types:
            if meal_type in day_obj:
                meal = day_obj[meal_type]
                key = (day_num, meal_type)
                if key in sig_dishes:
                    base, local = sig_dishes[key]
                    if "signature_dishes_base" not in meal:
                        meal["signature_dishes_base"] = base
                        updated_count += 1
                    if "signature_dishes_local" not in meal:
                        meal["signature_dishes_local"] = local
                else:
                    print(f"  WARNING: No signature dishes defined for Day {day_num} {meal_type}", file=sys.stderr)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Trip 1: Updated {updated_count} meals with signature_dishes_base/local")


def fix_trip2(filepath: str) -> None:
    """Fix Trip 2: Add currency_local, time, cuisine_local, signature_dishes, notes_local."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Default time templates
    default_times = {
        "breakfast": {"start": "08:00", "end": "09:00"},
        "lunch": {"start": "12:00", "end": "13:30"},
        "dinner": {"start": "18:30", "end": "20:00"},
    }

    # Cuisine type -> Chinese translation mapping
    cuisine_map = {
        "traditional harbin breakfast & pastries": "东北传统早餐&糕点",
        "russian cuisine": "俄餐",
        "dongbei (northeast chinese) cuisine": "东北菜",
        "bakery & cafe": "烘焙&咖啡",
        "dongbei cuisine": "东北菜",
        "dumplings & northeast cuisine": "饺子&东北菜",
        "traditional tianjin breakfast": "天津传统早餐",
        "tianjin cuisine": "津菜",
        "tianjin traditional cuisine": "津菜",
        "traditional xi'an breakfast": "西安传统早餐",
        "shaanxi cuisine": "陕西菜",
        "muslim quarter specialties": "回民街特色",
        "traditional dumplings": "传统饺子",
        "shaanxi traditional": "陕西传统菜",
        "suzhou noodles": "苏式面",
        "suzhou cuisine": "苏帮菜",
        "suzhou traditional cuisine": "苏帮菜",
        "hangzhou traditional breakfast": "杭州传统早餐",
        "hangzhou traditional cuisine": "杭帮菜",
        "hangzhou home-style cuisine": "杭帮家常菜",
        "guilin rice noodles": "桂林米粉",
        "guangxi cuisine": "桂菜",
        "yangshuo specialties": "阳朔特色菜",
        "simple breakfast": "简餐早点",
        "hunan home cooking": "湘菜家常",
        "tujia minority cuisine": "土家族菜",
        "cantonese dim sum": "粤式点心",
        "cantonese tea house": "粤式茶楼",
        "cantonese fusion": "粤式融合菜",
        "cantonese breakfast": "粤式早餐",
        "michelin-starred dim sum": "米其林点心",
        "hong kong dim sum": "港式点心",
        "chinese vegetarian/regular": "中式素食/中餐",
        "portuguese pastries": "葡式糕点",
        "cantonese roast meats": "粤式烧腊",
    }

    # Currency by location context
    # Day 12 dinner + Day 13 breakfast/lunch are Hong Kong (HKD)
    # Day 13 dinner is Macau (MOP)
    # Everything else is CNY
    def get_currency(day_num, meal_type, location):
        loc_lower = location.lower() if location else ""
        if "hong kong" in loc_lower or "macau" in loc_lower:
            if "macau" in loc_lower:
                return "MOP"
            return "HKD"
        if day_num == 12 and meal_type in ("lunch", "dinner"):
            return "HKD"
        if day_num == 13:
            if meal_type == "dinner":
                return "MOP"
            return "HKD"
        return "CNY"

    # Custom times for specific meals
    custom_times = {
        (1, "breakfast"): {"start": "08:00", "end": "09:00"},
        (1, "lunch"): {"start": "12:00", "end": "13:30"},
        (1, "dinner"): {"start": "18:30", "end": "20:00"},
        (2, "breakfast"): {"start": "08:30", "end": "09:30"},
        (2, "lunch"): {"start": "12:00", "end": "13:30"},
        (2, "dinner"): {"start": "18:00", "end": "19:30"},
        (3, "breakfast"): {"start": "07:30", "end": "08:30"},
        (3, "lunch"): {"start": "12:00", "end": "13:30"},
        (3, "dinner"): {"start": "18:30", "end": "20:00"},
        (4, "breakfast"): {"start": "08:00", "end": "09:00"},
        (4, "lunch"): {"start": "12:00", "end": "13:30"},
        (4, "dinner"): {"start": "18:30", "end": "20:00"},
        (5, "breakfast"): {"start": "08:00", "end": "09:00"},
        (5, "lunch"): {"start": "12:00", "end": "13:30"},
        (5, "dinner"): {"start": "18:30", "end": "20:00"},
        (6, "breakfast"): {"start": "07:30", "end": "08:30"},
        (6, "lunch"): {"start": "12:00", "end": "13:30"},
        (6, "dinner"): {"start": "18:00", "end": "19:30"},
        (7, "breakfast"): {"start": "08:00", "end": "09:00"},
        (7, "lunch"): {"start": "12:00", "end": "14:00"},
        (7, "dinner"): {"start": "18:00", "end": "19:30"},
        (8, "breakfast"): {"start": "07:00", "end": "08:00"},
        (8, "lunch"): {"start": "12:00", "end": "13:30"},
        (8, "dinner"): {"start": "18:30", "end": "20:00"},
        (9, "breakfast"): {"start": "07:30", "end": "08:30"},
        (9, "lunch"): {"start": "12:00", "end": "13:30"},
        (9, "dinner"): {"start": "18:30", "end": "20:00"},
        (10, "breakfast"): {"start": "07:00", "end": "08:00"},
        (10, "lunch"): {"start": "12:00", "end": "13:30"},
        (10, "dinner"): {"start": "18:00", "end": "19:30"},
        (11, "breakfast"): {"start": "08:00", "end": "09:30"},
        (11, "lunch"): {"start": "12:00", "end": "13:30"},
        (11, "dinner"): {"start": "18:30", "end": "20:00"},
        (12, "breakfast"): {"start": "07:30", "end": "08:30"},
        (12, "lunch"): {"start": "12:00", "end": "13:30"},
        (12, "dinner"): {"start": "19:00", "end": "20:30"},
        (13, "breakfast"): {"start": "08:00", "end": "09:30"},
        (13, "lunch"): {"start": "12:30", "end": "14:00"},
        (13, "dinner"): {"start": "16:00", "end": "17:00"},
    }

    # Signature dishes mapping for Trip 2
    sig_dishes_trip2 = {
        # Day 1 - Harbin
        (1, "breakfast"): (
            "Guobaorou, frozen pear, traditional pastries",
            "锅包肉, 冻梨, 传统糕点"
        ),
        (1, "lunch"): (
            "Borscht, beef stroganoff, Russian-style red sausage",
            "红菜汤, 奶油牛肉, 俄式红肠"
        ),
        (1, "dinner"): (
            "Guobaorou, stewed pork with vermicelli, Di San Xian",
            "锅包肉, 猪肉炖粉条, 地三鲜"
        ),
        # Day 2 - Harbin
        (2, "breakfast"): (
            "Fresh pastries, coffee, Russian-style bread",
            "现烤糕点, 咖啡, 俄式面包"
        ),
        (2, "lunch"): (
            "Guobaorou, braised pork ribs, pickled cabbage stew",
            "锅包肉, 排骨炖豆角, 酸菜炖粉条"
        ),
        (2, "dinner"): (
            "Handmade pork dumplings, lamb dumplings, cold cucumber salad",
            "猪肉手工水饺, 羊肉饺子, 拍黄瓜"
        ),
        # Day 3 - Tianjin
        (3, "breakfast"): (
            "Jianbing guozi, douhua, fried dough sticks",
            "煎饼果子, 豆花, 油条"
        ),
        (3, "lunch"): (
            "Tianjin four-treasure stew, fried shrimp, eight-treasure rice",
            "四大扒, 炸虾仁, 八珍饭"
        ),
        (3, "dinner"): (
            "Stuffed steamed buns, eight-treasure rice, traditional Tianjin dishes",
            "狗不理包子, 八珍饭, 天津传统菜"
        ),
        # Day 4 - Xi'an
        (4, "breakfast"): (
            "Spicy meatball hu la tang, fried dough sticks, sesame flatbread",
            "肉丸胡辣汤, 油条, 芝麻烧饼"
        ),
        (4, "lunch"): (
            "Biangbiang noodles, roujiamo, liangpi cold noodles",
            "BiangBiang面, 肉夹馍, 凉皮"
        ),
        (4, "dinner"): (
            "Guantang bao soup dumplings, yangrou paomo, roasted lamb skewers",
            "灌汤包, 羊肉泡馍, 烤羊肉串"
        ),
        # Day 5 - Xi'an
        (5, "breakfast"): (
            "Dumpling feast banquet, traditional Northern dumplings, hot soy milk",
            "饺子宴, 传统北方饺子, 热豆浆"
        ),
        (5, "lunch"): (
            "Gourd chicken, Shaanxi braised pork, hand-pulled noodles",
            "葫芦鸡, 陕西红烧肉, 手工扯面"
        ),
        (5, "dinner"): (
            "Lamb paomo with hand-torn bread, beef paomo, garlic cucumbers",
            "羊肉泡馍, 牛肉泡馍, 蒜泥黄瓜"
        ),
        # Day 6 - Suzhou
        (6, "breakfast"): (
            "Three-shrimp noodles, red oil wontons, scallion oil noodles",
            "三虾面, 红油馄饨, 葱油拌面"
        ),
        (6, "lunch"): (
            "Squirrel-shaped mandarin fish, sweet and sour spare ribs, Biluochun shrimp",
            "松鼠鳜鱼, 糖醋排骨, 碧螺虾仁"
        ),
        (6, "dinner"): (
            "Squirrel mandarin fish, Suzhou braised pork, seasonal river delicacies",
            "松鼠鳜鱼, 苏式红烧肉, 时令河鲜"
        ),
        # Day 7 - Hangzhou
        (7, "breakfast"): (
            "Xiaolongbao, shaomai, cat ear noodles",
            "小笼包, 烧麦, 猫耳朵"
        ),
        (7, "lunch"): (
            "West Lake vinegar fish, Dongpo pork, Beggar's chicken",
            "西湖醋鱼, 东坡肉, 叫化鸡"
        ),
        (7, "dinner"): (
            "Grandma's braised pork, tea-smoked chicken, stir-fried river shrimp",
            "外婆红烧肉, 茶香鸡, 清炒河虾"
        ),
        # Day 8 - Guilin/Yangshuo
        (8, "breakfast"): (
            "Guilin rice noodles with braised beef, pickled bean toppings, fried peanuts",
            "桂林卤牛肉米粉, 酸豆角, 炸花生"
        ),
        (8, "lunch"): (
            "Li River steamed fish, bamboo rice, stir-fried water spinach",
            "漓江清蒸鱼, 竹筒饭, 炒空心菜"
        ),
        (8, "dinner"): (
            "Beer fish, bamboo rice, stir-fried river snails",
            "啤酒鱼, 竹筒饭, 炒田螺"
        ),
        # Day 9 - Yangshuo
        (9, "breakfast"): (
            "Guilin rice noodles with marinated meat, pickled greens",
            "桂林卤肉米粉, 酸菜"
        ),
        (9, "lunch"): (
            "Crispy roast goose, char siu BBQ pork, honey-glazed roast duck",
            "脆皮烧鹅, 叉烧, 蜜汁烤鸭"
        ),
        (9, "dinner"): (
            "Beer fish, stir-fried river snails with chili, Guilin rice noodles",
            "啤酒鱼, 爆炒田螺, 桂林米粉"
        ),
        # Day 10 - Zhangjiajie
        (10, "breakfast"): (
            "Rice porridge, steamed buns, pickled vegetables",
            "米粥, 馒头, 咸菜"
        ),
        (10, "lunch"): (
            "Tujia smoked pork, wild mountain vegetables, farmhouse chicken",
            "土家腊肉, 野山菜, 农家土鸡"
        ),
        (10, "dinner"): (
            "Wild mountain vegetables, cured meats, spicy Tujia chicken",
            "野生山菜, 腊味拼盘, 土家辣子鸡"
        ),
        # Day 11 - Guangzhou
        (11, "breakfast"): (
            "Shrimp dumplings, char siu bao, cheung fun rice rolls",
            "虾饺, 叉烧包, 肠粉"
        ),
        (11, "lunch"): (
            "Assorted dim sum, roast goose, congee with century egg",
            "精选点心拼盘, 烧鹅, 皮蛋瘦肉粥"
        ),
        (11, "dinner"): (
            "Cantonese soup of the day, white-cut chicken, steamed fish",
            "老火靓汤, 白切鸡, 清蒸鱼"
        ),
        # Day 12 - Shenzhen/Hong Kong
        (12, "breakfast"): (
            "Dim sum, congee, cheung fun rice rolls",
            "点心, 粥, 肠粉"
        ),
        (12, "lunch"): (
            "Baked BBQ pork buns, steamed shrimp dumplings, egg tarts",
            "酥皮焗叉烧包, 鲜虾蒸饺, 蛋挞"
        ),
        (12, "dinner"): (
            "Creative truffle dumplings, crystal shrimp rolls, custard buns",
            "松露蒸饺, 水晶虾卷, 流沙包"
        ),
        # Day 13 - Hong Kong/Macau
        (13, "breakfast"): (
            "Steamed shrimp dumplings, BBQ pork buns, turnip cake",
            "鲜虾蒸饺, 叉烧包, 萝卜糕"
        ),
        (13, "lunch"): (
            "Vegetarian set meal, noodle soup, tofu dishes",
            "素斋套餐, 汤面, 豆腐菜品"
        ),
        (13, "dinner"): (
            "Portuguese egg tarts, serradura pudding, custard pastries",
            "葡式蛋挞, 木糠布甸, 奶油酥饼"
        ),
    }

    # Notes translations for Trip 2
    notes_translations = {
        (1, "breakfast"): "百年老字号哈尔滨糕点店，始建于1911年。中央大街上的绝佳早餐地点。",
        (1, "lunch"): "正宗俄式西餐，体现哈尔滨与俄罗斯的历史渊源。靠近圣索菲亚教堂。",
        (1, "dinner"): "高评分正宗东北菜餐厅。位于哈尔滨融创茂内，靠近冰雪大世界。",
        (2, "breakfast"): "中央大街附近的时尚烘焙店，早餐选择丰富。",
        (2, "lunch"): "哈尔滨知名连锁东北菜，正宗东北风味。全市多家分店。",
        (2, "dinner"): "专营传统东北水饺。品尝正宗东北家常味道的好去处。",
        (3, "breakfast"): "正宗天津早餐名店。一定要尝尝传统煎饼果子。",
        (3, "lunch"): "位于津湾广场，可欣赏海河风光。老牌餐厅，经典天津菜。",
        (3, "dinner"): "160年老字号，联合国教科文组织非遗品牌。一定要尝招牌包子。",
        (4, "breakfast"): "正宗本地早餐店。胡辣汤是西安必尝早餐。",
        (4, "lunch"): "传统陕菜的现代演绎。西安美食文化的绝佳入门。",
        (4, "dinner"): "回民街标志性餐厅。正宗清真西安美食。一定要尝招牌灌汤包。",
        (5, "breakfast"): "非遗品牌，始创于1936年。以饺子宴闻名。",
        (5, "lunch"): "高端传统陕菜餐厅，现代摆盘。体验精致陕菜的好去处。",
        (5, "dinner"): "专营西安最著名的泡馍。正宗做法，分量十足。",
        (6, "breakfast"): "苏式面馆。三虾面是当地名吃。平江路上的绝佳早餐地点。",
        (6, "lunch"): "高端苏帮菜餐厅。体验精致苏式菜肴的好去处。",
        (6, "dinner"): "创建于1757年，苏州最著名的餐厅之一。必尝招牌松鼠鳜鱼。建议预约。",
        (7, "breakfast"): "杭州百年老字号，始创于1913年。传统杭州早点和点心。靠近西湖。",
        (7, "lunch"): "170年历史的标志性餐厅，坐拥西湖美景。必尝杭州经典菜。建议提前预订湖景座位。",
        (7, "dinner"): "人气连锁餐厅，优质杭帮家常菜，价格实惠。湖边位置，风景优美。",
        (8, "breakfast"): "正宗桂林米粉，当地必尝特色。每日现做鲜粉。漓江游船前的快速早餐。",
        (8, "lunch"): "漓江游船途中或到达阳朔后午餐。抵达后河边有很多选择。",
        (8, "dinner"): "阳朔最著名的菜——啤酒鱼。西街上的获奖餐厅。漓江游后的完美晚餐。",
        (9, "breakfast"): "阳朔当地人气米粉店。实惠正宗。",
        (9, "lunch"): "以粤式烧腊闻名。遇龙河竹筏漂流后的午餐好选择。",
        (9, "dinner"): "另一家获奖啤酒鱼餐厅。想换个口味尝当地特色的好选择。",
        (10, "breakfast"): "景区内酒店或简餐。选择有限但方便早起出发。建议带零食。",
        (10, "lunch"): "景区附近的家庭餐馆。正宗土家族特色菜。简单但丰盛。",
        (10, "dinner"): "专营土家族菜肴和山中野菜。正宗当地风味。",
        (11, "breakfast"): "广州高端点心连锁。经典早茶体验。必尝粤式饮茶。",
        (11, "lunch"): "越秀公园附近的传统茶楼。午后点心或参观广州塔后午餐的好去处。",
        (11, "dinner"): "以高品质靓汤和创意融合菜闻名的现代粤菜餐厅。",
        (12, "breakfast"): "过关前在深圳快速早餐。留着胃口吃香港美食。",
        (12, "lunch"): "世界最便宜的米其林星级餐厅。物美价廉的优质点心。排队可能较长。",
        (12, "dinner"): "庙街夜市附近的人气本地点心店。晚餐后可逛夜市。",
        (13, "breakfast"): "获奖点心餐厅。前往大屿山前的美味早餐。高品质实惠价格。",
        (13, "lunch"): "昂坪大佛附近午餐。选择有限，可考虑宝莲禅寺附近素食。",
        (13, "dinner"): "澳门最著名的蛋挞店。必尝正宗葡式蛋挞。附近还有葡国餐厅可用晚餐。",
    }

    meal_types = ["breakfast", "lunch", "dinner"]
    updated_fields = 0

    for day_obj in data["data"]["days"]:
        day_num = day_obj["day"]
        location = day_obj.get("location", "")

        for meal_type in meal_types:
            if meal_type not in day_obj:
                continue
            meal = day_obj[meal_type]

            # 1. Fix currency_local (rename 'currency' if exists, or add new)
            if "currency_local" not in meal:
                if "currency" in meal:
                    # Rename currency -> currency_local
                    meal["currency_local"] = meal.pop("currency")
                else:
                    meal_location = meal.get("location_base", meal.get("location", ""))
                    meal["currency_local"] = get_currency(day_num, meal_type, f"{location} {meal_location}")
                updated_fields += 1

            # 2. Fix time
            if "time" not in meal:
                key = (day_num, meal_type)
                if key in custom_times:
                    meal["time"] = custom_times[key]
                else:
                    meal["time"] = default_times[meal_type]
                updated_fields += 1

            # 3. Fix cuisine_local
            if "cuisine_local" not in meal:
                cuisine_raw = meal.get("cuisine_base", meal.get("cuisine", ""))
                cuisine_lower = cuisine_raw.lower().strip()
                if cuisine_lower in cuisine_map:
                    meal["cuisine_local"] = cuisine_map[cuisine_lower]
                else:
                    # Fallback: try partial matching
                    matched = False
                    for eng, chn in cuisine_map.items():
                        if eng in cuisine_lower or cuisine_lower in eng:
                            meal["cuisine_local"] = chn
                            matched = True
                            break
                    if not matched:
                        meal["cuisine_local"] = cuisine_raw  # Keep original if no match
                        print(f"  WARNING: No cuisine translation for '{cuisine_raw}' (Day {day_num} {meal_type})", file=sys.stderr)
                updated_fields += 1

            # 4. Fix signature_dishes_base and signature_dishes_local
            key = (day_num, meal_type)
            if "signature_dishes_base" not in meal:
                if key in sig_dishes_trip2:
                    meal["signature_dishes_base"] = sig_dishes_trip2[key][0]
                elif "signature_dishes" in meal:
                    # Use existing signature_dishes as base
                    meal["signature_dishes_base"] = meal["signature_dishes"]
                updated_fields += 1

            if "signature_dishes_local" not in meal:
                if key in sig_dishes_trip2:
                    meal["signature_dishes_local"] = sig_dishes_trip2[key][1]
                updated_fields += 1

            # 5. Fix notes_local
            if "notes_local" not in meal:
                if key in notes_translations:
                    meal["notes_local"] = notes_translations[key]
                updated_fields += 1

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Trip 2: Updated {updated_fields} field additions/fixes")


def validate_json(filepath: str) -> bool:
    """Validate that the file is valid JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"  VALID JSON: {filepath}")
        return True
    except json.JSONDecodeError as e:
        print(f"  INVALID JSON: {filepath} - {e}", file=sys.stderr)
        return False


def count_meals_and_gaps(filepath: str, trip_name: str) -> None:
    """Count total meals and remaining gaps for verification."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    meal_types = ["breakfast", "lunch", "dinner"]
    total = 0
    missing_sig_base = 0
    missing_sig_local = 0
    missing_currency = 0
    missing_time = 0
    missing_cuisine_local = 0
    missing_notes_local = 0

    for day_obj in data["data"]["days"]:
        for mt in meal_types:
            if mt in day_obj:
                total += 1
                meal = day_obj[mt]
                if "signature_dishes_base" not in meal:
                    missing_sig_base += 1
                if "signature_dishes_local" not in meal:
                    missing_sig_local += 1
                if "currency_local" not in meal and "currency" not in meal:
                    missing_currency += 1
                if "time" not in meal:
                    missing_time += 1
                if "cuisine_local" not in meal:
                    missing_cuisine_local += 1
                if "notes_local" not in meal:
                    missing_notes_local += 1

    print(f"\n  {trip_name} Summary:")
    print(f"    Total meals: {total}")
    print(f"    Missing signature_dishes_base: {missing_sig_base}")
    print(f"    Missing signature_dishes_local: {missing_sig_local}")
    print(f"    Missing currency_local/currency: {missing_currency}")
    print(f"    Missing time: {missing_time}")
    print(f"    Missing cuisine_local: {missing_cuisine_local}")
    print(f"    Missing notes_local: {missing_notes_local}")


if __name__ == "__main__":
    trip1_path = "/root/travel-planner/data/china-feb-15-mar-7-2026-20260202-195429/meals.json"
    trip2_path = "/root/travel-planner/data/beijing-exchange-bucket-list-20260202-232405/meals.json"

    print("=" * 60)
    print("Fixing meals data for both trips")
    print("=" * 60)

    print("\n--- Trip 1 (China Itinerary) ---")
    fix_trip1(trip1_path)

    print("\n--- Trip 2 (Beijing Bucket List) ---")
    fix_trip2(trip2_path)

    print("\n--- Validation ---")
    v1 = validate_json(trip1_path)
    v2 = validate_json(trip2_path)

    print("\n--- Gap Analysis (Post-Fix) ---")
    count_meals_and_gaps(trip1_path, "Trip 1")
    count_meals_and_gaps(trip2_path, "Trip 2")

    if v1 and v2:
        print("\nAll files valid. Done.")
        sys.exit(0)
    else:
        print("\nERROR: JSON validation failed!", file=sys.stderr)
        sys.exit(1)
