"""Plan-data and HTML builders extracted from generate-html-interactive.py.

W7 refactor (spec-20260513-085358): module-level functions take the
InteractiveHTMLGenerator instance as `gen` and access its attributes/methods.
Each helper is <=30 lines per the project quality gate.
"""

import json
import re


def _split_blocks(text):
    """Split notes text into category blocks separated by blank lines."""
    return re.split(r"\n\n", text) if text else []


def _extract_category(block):
    """Return (category_name, rest_after_brackets) or (None, None) on no match."""
    m = re.match(r"\[([^\]]+)\]|【([^】]+)】", block)
    if not m:
        return None, None
    category = (m.group(1) or m.group(2)).strip()
    rest = block[m.end():].strip()
    return category, rest


def _is_dining_cat(category):
    """True for dining/restaurant categories not to be parsed as brands."""
    return any(k in category.upper() for k in ("DINING", "RESTAURANT", "餐饮"))


def _local_block_for(local_blocks, block_idx, fallback_cat):
    """Return (category_local, local_block_rest_text) for a given block index."""
    if block_idx >= len(local_blocks):
        return fallback_cat, ""
    lb = local_blocks[block_idx].strip()
    cat_local, rest_local = _extract_category(lb)
    if cat_local is None:
        return fallback_cat, ""
    return cat_local, rest_local


def _strip_floor_and_hash(name_part):
    """Return (brand_name_clean, floor_string) after stripping floor + hash."""
    fm = re.search(r"([B]?\d+F(?:/[B]?\d+F)*)", name_part, re.IGNORECASE)
    floor = fm.group(1) if fm else ""
    bn = re.sub(r"\s*[B]?\d+F(?:/[B]?\d+F)*\s*", " ", name_part, flags=re.IGNORECASE).strip()
    bn = re.sub(r"\s*#\w+\s*$", "", bn).strip()
    return bn, floor


def _parse_brand_entry(entry):
    """Parse one brand entry; return (brand_name, floor, description) or None."""
    parts = re.split(r"\s*(?:--|—)\s*", entry, maxsplit=1)
    name_part = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else ""
    brand_name, floor = _strip_floor_and_hash(name_part)
    if not brand_name:
        return None
    return brand_name, floor, description


def _parse_local_entry(local_entries, brand_idx, default_name):
    """Return (name_local, description_local) for a brand index."""
    if brand_idx >= len(local_entries):
        return default_name, ""
    lp = re.split(r"\s*(?:--|—)\s*", local_entries[brand_idx], maxsplit=1)
    lname_part = lp[0].strip()
    desc_local = lp[1].strip() if len(lp) > 1 else ""
    name_local_clean, _ = _strip_floor_and_hash(lname_part)
    return (name_local_clean or default_name), desc_local


def _brand_dict(bn, nl, category, category_local, floor, desc, dl):
    """Pack one brand record dict."""
    return {"name": bn, "name_local": nl,
            "category": category, "category_local": category_local,
            "floor": floor, "description": desc, "description_local": dl}


def _build_brand_block(block, local_block, fallback_cat):
    """Parse one block's brand entries; return list of brand dicts."""
    category, rest = _extract_category(block)
    if category is None or _is_dining_cat(category):
        return []
    category_local, local_rest = local_block
    brand_entries = [b.strip() for b in rest.split("|") if b.strip()]
    local_entries = [b.strip() for b in local_rest.split("|") if b.strip()] if local_rest else []
    out = []
    for bi, entry in enumerate(brand_entries):
        parsed = _parse_brand_entry(entry)
        if not parsed:
            continue
        bn, floor, desc = parsed
        nl, dl = _parse_local_entry(local_entries, bi, bn)
        out.append(_brand_dict(bn, nl, category, category_local, floor, desc, dl))
    return out


def parse_shopping_brands(notes_base, notes_local=""):
    """Public entry: notes_base + notes_local -> list of brand dicts."""
    if not notes_base:
        return []
    blocks = _split_blocks(notes_base)
    local_blocks = _split_blocks(notes_local)
    out = []
    for bi, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        category_local_pair = _local_block_for(local_blocks, bi, block)
        out.extend(_build_brand_block(block, category_local_pair, category_local_pair[0]))
    return out


def _empty_bucket_budget():
    """Empty per-category budget for one bucket-list day."""
    return {"meals": 0, "attractions": 0, "entertainment": 0,
            "accommodation": 0, "shopping": 0, "cafe": 0,
            "transportation": 0, "total": 0}


def _bucketlist_ui_labels(gen):
    """Build merged ui_labels dict for bucket-list mode."""
    req_labels = gen.requirements.get("trip_summary", {}).get("ui_labels", {})
    base_labels = {**gen.DEFAULT_UI_LABELS_BASE, **req_labels.get("base", {})}
    return {
        "base_display": req_labels.get("base_display", "EN"),
        "local_display": req_labels.get("local_display", "Local"),
        "base": base_labels, "local": req_labels.get("local", {}),
    }


def _bucketlist_trip_summary(gen, ui_labels):
    """Build trip_summary dict for bucket-list mode."""
    rs = gen.requirements.get("trip_summary", {})
    return {
        "trip_type": "bucket_list",
        "trip_type_local": rs.get("trip_type_local", ""),
        "description": rs.get("description", "Destination Options"),
        "description_local": "",
        "base_location": rs.get("base_location", ""),
        "period": rs.get("period", ""), "period_local": "",
        "travelers": rs.get("travelers", "1 adult"), "travelers_local": "",
        "budget_per_trip": rs.get("budget_per_trip", f"{gen._display_symbol}200-500"),
        "preferences": "",
        "base_display": ui_labels.get("base_display", "EN"),
        "local_display": ui_labels.get("local_display", "Local"),
        "ui_labels": ui_labels,
    }


def _bucketlist_init_day(gen, city_data, trip_idx):
    """Build the empty day dict for a bucket-list city."""
    city_name = city_data.get("city", "Unknown")
    return {
        "day": 1, "date": city_data.get("recommended_duration", "1-2 days"),
        "location": city_name,
        "cover": gen._get_cover_image(city_name, trip_idx),
        "user_plans": city_data.get("user_requirements", []),
        "meals": {}, "attractions": [], "entertainment": [],
        "accommodation": None, "shopping": [], "cafe": [],
        "budget": _empty_bucket_budget(),
    }


def _bucketlist_attr_card(gen, attr, city_name):
    """Build one bucket-list attraction card."""
    a_name_base = attr.get("name_base", attr.get("name", ""))
    a_name_local = attr.get("name_local", attr.get("name_chinese", ""))
    cost = gen._to_display_currency(attr.get("ticket_price_eur", 0), "EUR")
    img = gen._get_placeholder_image(
        "attraction",
        poi_name=a_name_local if a_name_local else a_name_base,
        name_base=a_name_base, name_local=a_name_local)
    return {
        "name_base": a_name_base, "name_local": a_name_local,
        "location_base": city_name, "location_local": "",
        "type_base": gen._format_type(attr.get("type", "")),
        "type_local": attr.get("type_local", ""),
        "cost": cost, "cost_local": attr.get("ticket_price_eur", 0),
        "opening_hours": attr.get("opening_hours", ""),
        "recommended_duration": f"{attr.get('recommended_duration_hours', 2)}h",
        "image": img,
        "notes_base": attr.get("notes", ""), "notes_local": attr.get("notes_local", ""),
        "time": {"start": "10:00", "end": "12:00"}, "links": {},
    }


def _bucketlist_fill_attractions(gen, day, city_name):
    """Append attractions for one city to day attractions list."""
    if not (gen.attractions and "cities" in gen.attractions):
        return
    ca = next((c for c in gen.attractions["cities"] if c.get("city") == city_name), {})
    for attr in ca.get("attractions", []) or []:
        day["attractions"].append(_bucketlist_attr_card(gen, attr, city_name))
        day["budget"]["attractions"] += day["attractions"][-1]["cost"]


def _meal_time_for_type(meal_type):
    """Default time slot for bucket-list meal-type."""
    if meal_type == "breakfast":
        return {"start": "08:00", "end": "09:00"}
    if meal_type == "lunch":
        return {"start": "12:00", "end": "13:30"}
    return {"start": "18:30", "end": "20:00"}


def _bucketlist_meal_card(gen, meal, meal_type, city_name):
    """Build one bucket-list meal card."""
    nb = meal.get("name_base", meal.get("name", ""))
    nl = meal.get("name_local", meal.get("name_chinese", ""))
    cost = gen._to_display_currency(meal.get("price_range_eur_low", 10), "EUR")
    img = gen._get_placeholder_image(
        "meal", poi_name=nl if nl else nb, name_base=nb, name_local=nl)
    return {
        "name_base": nb, "name_local": nl,
        "location_base": city_name, "location_local": "",
        "cost": cost, "cost_local": meal.get("price_range_eur_low", 10),
        "cuisine_base": meal.get("cuisine_type", ""),
        "cuisine_local": meal.get("cuisine_local", ""),
        "signature_dishes_base": meal.get("signature_dish", ""),
        "signature_dishes_local": meal.get("signature_dishes_local", ""),
        "notes_base": meal.get("notes", ""), "notes_local": meal.get("notes_local", ""),
        "image": img, "time": _meal_time_for_type(meal_type), "links": {},
    }


def _bucketlist_fill_meals(gen, day, city_name):
    """Fill day.meals for first 3 meals of one city."""
    if not (gen.meals and "cities" in gen.meals):
        return
    cm = next((c for c in gen.meals["cities"] if c.get("city") == city_name), {})
    for i, meal in enumerate((cm.get("meals", []) or [])[:3]):
        mt = ["breakfast", "lunch", "dinner"][i]
        day["meals"][mt] = _bucketlist_meal_card(gen, meal, mt, city_name)
        day["budget"]["meals"] += day["meals"][mt]["cost"]


def _bucketlist_day_total(day):
    """Set day.budget.total as sum of categories."""
    b = day["budget"]
    b["total"] = sum([b["meals"], b["attractions"], b["entertainment"],
                      b["accommodation"], b["shopping"], b["cafe"],
                      b["transportation"]])


def _bucketlist_one_trip(gen, city_data, trip_idx):
    """Build one city-as-trip object."""
    day = _bucketlist_init_day(gen, city_data, trip_idx)
    city_name = city_data.get("city", "Unknown")
    _bucketlist_fill_attractions(gen, day, city_name)
    _bucketlist_fill_meals(gen, day, city_name)
    _bucketlist_day_total(day)
    return {
        "name": city_name,
        "days_label": city_data.get("recommended_duration", "1-2 days"),
        "cover": day["cover"], "days": [day],
    }


def generate_bucket_list_data(gen):
    """Build PLAN_DATA for bucket list (city_guides format)."""
    ui_labels = _bucketlist_ui_labels(gen)
    trip_summary = _bucketlist_trip_summary(gen, ui_labels)
    trips = [_bucketlist_one_trip(gen, c, i)
             for i, c in enumerate(gen.skeleton.get("cities", []) or [])]
    return {"trip_summary": trip_summary, "trips": trips}


def _itinerary_ui_labels(gen):
    """Build merged ui_labels dict for itinerary mode."""
    req_labels = gen.requirements.get("trip_summary", {}).get("ui_labels", {})
    base_labels = {**gen.DEFAULT_UI_LABELS_BASE, **req_labels.get("base", {})}
    return {
        "base_display": req_labels.get("base_display", "EN"),
        "local_display": req_labels.get("local_display", "Local"),
        "base": base_labels, "local": req_labels.get("local", {}),
    }


def _itinerary_preferences(gen):
    """Resolve prefs string from skeleton."""
    prefs = gen.skeleton.get("trip_summary", {}).get("preferences", {})
    if isinstance(prefs, dict):
        return gen._format_preferences(prefs)
    return str(prefs)


def _itinerary_trip_summary(gen, ui_labels):
    """Build trip_summary dict for itinerary mode."""
    ss = gen.skeleton.get("trip_summary", {})
    dd = ss.get("duration_days", 0)
    period = f"{dd} day{'s' if dd != 1 else ''}"
    desc_local = ss.get("description_local", "") or gen.skeleton.get("description_local", "")
    return {
        "trip_type": gen._format_trip_type(ss.get("trip_type", "itinerary")),
        "trip_type_local": ss.get("trip_type_local", ""),
        "description": ss.get("description", "Travel Plan"),
        "description_local": desc_local,
        "base_location": ss.get("base_location", ""),
        "period": period, "period_local": ss.get("period_local", ""),
        "travelers": ss.get("travelers", "1 adult"),
        "travelers_local": ss.get("travelers_local", ""),
        "budget_per_trip": ss.get("budget_per_trip", f"{gen._display_symbol}500"),
        "preferences": _itinerary_preferences(gen),
        "base_display": ui_labels.get("base_display", "EN"),
        "local_display": ui_labels.get("local_display", "Local"),
        "ui_labels": ui_labels,
    }


def generate_itinerary_data(gen):
    """Build PLAN_DATA for itinerary (trip_summary + days format)."""
    ui_labels = _itinerary_ui_labels(gen)
    trip_summary = _itinerary_trip_summary(gen, ui_labels)
    days_in = gen.skeleton.get("days", []) or []
    merged_days = [gen._merge_day_data(ds) for ds in days_in]
    trips = gen._group_days_by_location(merged_days)
    return {"trip_summary": trip_summary, "trips": trips}


HTML_HEAD = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    '  <meta charset="UTF-8">\n'
    '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    "  <title>__TITLE__</title>\n"
    '  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>\n'
    '  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>\n'
    '  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>\n'
    "  <style>\n"
    "    * { margin: 0; padding: 0; box-sizing: border-box; }\n"
    "    body { overflow-x: hidden; }\n"
    "    .category-scroll-container::-webkit-scrollbar { height: 6px; }\n"
    "    .category-scroll-container::-webkit-scrollbar-track { background: transparent; }\n"
    "    .category-scroll-container::-webkit-scrollbar-thumb "
    "{ background: rgba(0,0,0,0.15); border-radius: 3px; }\n"
    "    .category-scroll-container::-webkit-scrollbar-thumb:hover "
    "{ background: rgba(0,0,0,0.25); }\n"
    "  </style>\n</head>\n<body>\n  <div id=\"root\"></div>\n"
)


HTML_SCRIPT = (
    '  <script type="text/babel">\n'
    "    // Embedded PLAN_DATA\n"
    "    const PLAN_DATA = __PLAN_DATA__;\n"
    '    const CURRENCY_SYMBOL = "__SYMBOL__";\n'
    "    const TRIP_ID = __TRIP_ID__;\n\n"
    "    __REACT_TEMPLATE__\n\n"
    "    // Render app\n"
    "    const root = ReactDOM.createRoot(document.getElementById('root'));\n"
    "    root.render(<NotionTravelApp />);\n"
    "  </script>\n</body>\n</html>"
)


def generate_html(gen, trip_id=None):
    """Render the full HTML document for a plan (unified viewer/editor page).

    When trip_id is None (default), injects TRIP_ID = null — backward-compatible
    with one-arg callers such as generate-html-interactive.py.
    When trip_id is a string, injects the JSON-encoded trip id so the React tree
    can fetch candidates and activate the interactive editor layer.
    """
    plan_data = gen.generate_plan_data()
    plan_data_json = json.dumps(plan_data, ensure_ascii=False, indent=2)
    react_template = gen._read_react_template()
    title = plan_data["trip_summary"]["description"]
    head = HTML_HEAD.replace("__TITLE__", title)
    trip_id_js = "null" if trip_id is None else json.dumps(trip_id)
    script = (HTML_SCRIPT
              .replace("__TRIP_ID__", trip_id_js)
              .replace("__PLAN_DATA__", plan_data_json)
              .replace("__SYMBOL__", gen._display_symbol)
              .replace("__REACT_TEMPLATE__", react_template))
    return head + script
