"""Day-data merge helpers extracted from generate-html-interactive.py.

Each helper is <=30 lines per the project quality gate. The renderer
(InteractiveHTMLGenerator) calls these in order via _merge_day_data.

Bug-1 (meals alternatives), Bug-2 (gaode_id fast-path), Bug-3
(unscheduled-optionals) fixes are folded in here.

W7 refactor: extracted 2026-05-14 from spec-20260513-085358.
Invariant (codex round-2 Q1): json.dumps(sort_keys=True) over the
merged dict must match the pre-refactor output byte-for-byte for all
15 days of china-20260412-092624.
"""


def _empty_budget():
    """Return zeroed per-category budget dict."""
    return {"meals": 0, "attractions": 0, "entertainment": 0,
            "accommodation": 0, "shopping": 0, "cafe": 0,
            "transportation": 0, "total": 0}


def build_skeleton(gen, day_skeleton):
    """Build the initial merged-dict skeleton for one day."""
    day_num = day_skeleton.get("day", 1)
    location_base = day_skeleton.get("location", "Unknown")
    return {
        "day": day_num,
        "date": day_skeleton.get("date", ""),
        "location_base": location_base,
        "location_local": day_skeleton.get("location_local", ""),
        "cover": gen._get_cover_image(location_base, day_num),
        "user_plans": day_skeleton.get("user_plans", []),
        "meals": {}, "attractions": [], "entertainment": [],
        "accommodation": None, "transportation": None,
        "shopping": [], "cafe": [],
        "budget": _empty_budget(),
    }


def _common_fields(item, cost_display):
    """Fields shared by meal/cafe/attraction/entertainment/shop cards."""
    return {
        "name_base": item.get("name_base", ""),
        "name_local": item.get("name_local", ""),
        "location_base": item.get("location_base", ""),
        "location_local": item.get("location_local", ""),
        "coordinates": item.get("coordinates", {}),
        "cost": cost_display, "cost_local": item.get("cost", 0),
        "optional": item.get("optional", False),
        "notes_base": item.get("notes_base", ""),
        "notes_local": item.get("notes_local", ""),
        "links": item.get("links", {}),
    }


def _image_for(gen, category, item):
    """Resolve placeholder image for a card."""
    nb = item.get("name_base", "")
    nl = item.get("name_local", "")
    return gen._get_placeholder_image(
        category, poi_name=nl if nl else nb, gaode_id=item.get("gaode_id", ""),
        name_base=nb, name_local=nl,
        location_base=item.get("location_base", ""),
        location_local=item.get("location_local", ""),
        is_home=gen._is_home_location(item))


def _to_display_cost(gen, item):
    """Convert item cost to display currency."""
    return gen._to_display_currency(item.get("cost", 0),
                                    item.get("currency_local", "CNY"))


def _meal_card(gen, meal, meal_time):
    """Build one rendered meal card (primary or alternative)."""
    cost = _to_display_cost(gen, meal)
    card = _common_fields(meal, cost)
    card.update({
        "cuisine_base": meal.get("cuisine_base", ""),
        "cuisine_local": meal.get("cuisine_local", ""),
        "signature_dishes_base": meal.get("signature_dishes_base", ""),
        "signature_dishes_local": meal.get("signature_dishes_local", ""),
        "image": _image_for(gen, "meal", meal),
        "time": meal_time,
    })
    return card, cost


def _merge_meal_slot(gen, merged, meal_type, day_meals, day_timeline, alt_map):
    """Handle one meal type slot (breakfast/lunch/dinner)."""
    meal_slot = day_meals[meal_type]
    primary = meal_slot.get("primary", meal_slot)
    mt = gen._get_meal_time_from_timeline(meal_type, day_timeline)
    card, cost = _meal_card(gen, primary, mt)
    card["name_base"] = primary.get("name_base", meal_type)
    merged["meals"][meal_type] = card
    merged["budget"]["meals"] += cost
    alts = meal_slot.get("alternatives", []) if isinstance(meal_slot, dict) else []
    if alts:
        alt_map[meal_type] = [_meal_card(gen, a, None)[0] for a in alts]


def merge_meals(gen, merged, day_num, day_timeline):
    """Merge meals.json into merged-dict; Bug-1 alternatives folded in."""
    if not (gen.meals and "days" in gen.meals):
        return
    day_meals = next((d for d in gen.meals["days"] if d.get("day") == day_num), {})
    alt_map = {}
    for meal_type in ("breakfast", "lunch", "dinner"):
        if meal_type in day_meals:
            _merge_meal_slot(gen, merged, meal_type, day_meals, day_timeline, alt_map)
    if alt_map:
        merged["meal_alternatives"] = alt_map


def _cafe_card(gen, item, day_timeline):
    """Build one rendered cafe card from a cafe.json entry."""
    cost = _to_display_cost(gen, item)
    card = _common_fields(item, cost)
    t = gen._get_timeline_time(item.get("name_base", ""), item.get("name_local", ""),
                               day_timeline, item.get("gaode_id", ""))
    card.update({
        "type_base": gen._format_type(item.get("type_base", "")),
        "type_local": item.get("type_local", ""),
        "cuisine_base": item.get("cuisine_base", ""),
        "cuisine_local": item.get("cuisine_local", ""),
        "signature_dishes_base": item.get("signature_dishes_base", ""),
        "signature_dishes_local": item.get("signature_dishes_local", ""),
        "image": _image_for(gen, "cafe", item),
        "time": t,
    })
    return card


def merge_cafe(gen, merged, day_num, day_timeline):
    """Merge cafe.json into merged-dict."""
    if not (gen.cafe and "days" in gen.cafe):
        return
    day_cafe = next((d for d in gen.cafe["days"] if d.get("day") == day_num), {})
    for item in day_cafe.get("cafe", []) or []:
        card = _cafe_card(gen, item, day_timeline)
        merged["cafe"].append(card)
        merged["budget"]["cafe"] += card["cost"]


def _attr_card(gen, attr, day_timeline):
    """Build one rendered attraction card from attractions.json entry."""
    cost = _to_display_cost(gen, attr)
    card = _common_fields(attr, cost)
    t = gen._get_timeline_time(attr.get("name_base", ""), attr.get("name_local", ""),
                               day_timeline, attr.get("gaode_id", ""))
    card.update({
        "type_base": gen._format_type(attr.get("type_base", "")),
        "type_local": attr.get("type_local", ""),
        "opening_hours": attr.get("opening_hours", ""),
        "image": _image_for(gen, "attraction", attr),
        "time": t,
    })
    return card


def merge_attractions(gen, merged, day_num, day_timeline):
    """Merge attractions.json into merged-dict (no alternatives[] read)."""
    if not (gen.attractions and "days" in gen.attractions):
        return
    day_attrs = next((d for d in gen.attractions["days"] if d.get("day") == day_num), {})
    for attr in day_attrs.get("attractions", []) or []:
        card = _attr_card(gen, attr, day_timeline)
        merged["attractions"].append(card)
        merged["budget"]["attractions"] += card["cost"]


def _ent_card(gen, ent, day_timeline):
    """Build one rendered entertainment card."""
    cost = _to_display_cost(gen, ent)
    card = _common_fields(ent, cost)
    t = gen._get_timeline_time(ent.get("name_base", ""), ent.get("name_local", ""),
                               day_timeline, ent.get("gaode_id", ""))
    card.update({
        "type_base": gen._format_type(ent.get("type_base", "")),
        "type_local": ent.get("type_local", ""),
        "note_base": ent.get("note_base", ""),
        "note_local": ent.get("note_local", ""),
        "image": _image_for(gen, "entertainment", ent),
        "time": t,
    })
    return card


def merge_entertainment(gen, merged, day_num, day_timeline):
    """Merge entertainment.json into merged-dict."""
    if not (gen.entertainment and "days" in gen.entertainment):
        return
    day_ent = next((d for d in gen.entertainment["days"] if d.get("day") == day_num), {})
    for ent in day_ent.get("entertainment", []) or []:
        card = _ent_card(gen, ent, day_timeline)
        merged["entertainment"].append(card)
        merged["budget"]["entertainment"] += card["cost"]


def _shop_brand_one(brand, b_name):
    """Format a single brand bullet line (base + local)."""
    b_name_local = brand.get("name_local", b_name)
    b_cat = brand.get("category", "")
    b_desc = brand.get("description", "")
    b_desc_local = brand.get("description_local", b_desc)
    lb = f"• {b_name}"
    ll = f"• {b_name_local}"
    if b_cat:
        lb += f" ({b_cat})"
        ll += f" ({b_cat})"
    if b_desc:
        lb += f" — {b_desc}"
    if b_desc_local:
        ll += f" — {b_desc_local}"
    return lb, ll


def _shop_brand_lines(brands):
    """Build base/local brand bullet text from shopping.brands[]."""
    base_lines, local_lines = [], []
    for brand in brands:
        b_name = brand.get("name", "")
        if not b_name:
            continue
        lb, ll = _shop_brand_one(brand, b_name)
        base_lines.append(lb)
        local_lines.append(ll)
    return "\n".join(base_lines), "\n".join(local_lines)


def _shop_notes_with_brands(notes_base, notes_local, brands):
    """Append parsed brand bullets to base/local notes if any."""
    if not brands:
        return notes_base, notes_local
    bt_base, bt_local = _shop_brand_lines(brands)
    notes_base = (notes_base.rstrip() + "\n\n**Shops:**\n" + bt_base
                  if notes_base else "**Shops:**\n" + bt_base)
    notes_local = (notes_local.rstrip() + "\n\n**推荐店铺：**\n" + bt_local
                   if notes_local else "**推荐店铺：**\n" + bt_local)
    return notes_base, notes_local


def _shop_card(gen, item, day_timeline):
    """Build one rendered shopping card."""
    cost = _to_display_cost(gen, item)
    notes_base = item.get("notes_base", "")
    notes_local = item.get("notes_local", "")
    brands = item.get("brands", []) or gen._parse_shopping_brands(notes_base, notes_local)
    notes_base, notes_local = _shop_notes_with_brands(notes_base, notes_local, brands)
    card = _common_fields(item, cost)
    card["notes_base"] = notes_base
    card["notes_local"] = notes_local
    nb, nl = item.get("name_base", ""), item.get("name_local", "")
    mall_image = gen._get_placeholder_image(
        "attraction", poi_name=nl if nl else nb, name_base=nb, name_local=nl)
    mall_time = gen._get_timeline_time(nb, nl, day_timeline, item.get("gaode_id", ""))
    card.update({"type_base": item.get("type_base", ""),
                 "type_local": item.get("type_local", ""),
                 "image": mall_image, "time": mall_time, "links": {}})
    return card


def merge_shopping(gen, merged, day_num, day_timeline):
    """Merge shopping.json into merged-dict."""
    if not (gen.shopping and "days" in gen.shopping):
        return
    day_shop = next((d for d in gen.shopping["days"] if d.get("day") == day_num), {})
    for item in day_shop.get("shopping", []) or []:
        card = _shop_card(gen, item, day_timeline)
        merged["shopping"].append(card)
        merged["budget"]["shopping"] += card["cost"]


def _acc_card_extra(gen, acc, acc_time):
    """Fields specific to accommodation cards."""
    return {
        "type_base": gen._format_type(acc.get("type_base", "")),
        "type_local": acc.get("type_local", ""),
        "stars": acc.get("stars", 0) or 0,
        "amenities_base": acc.get("amenities_base", []),
        "amenities_local": acc.get("amenities_local", []),
        "check_in": acc.get("check_in", ""),
        "check_out": acc.get("check_out", ""),
        "time": acc_time,
        "image": _image_for(gen, "accommodation", acc),
    }


def _acc_card(gen, acc, day_timeline):
    """Build the accommodation card from accommodation.json entry."""
    cost = _to_display_cost(gen, acc)
    card = _common_fields(acc, cost)
    nb, nl = acc.get("name_base", ""), acc.get("name_local", "")
    acc_time = gen._get_timeline_time(nb, nl, day_timeline, acc.get("gaode_id", ""))
    if not acc_time and acc.get("check_in"):
        acc_time = gen._normalize_time(acc.get("check_in"), default_duration_hours=0.5)
    card.update(_acc_card_extra(gen, acc, acc_time))
    return card


def merge_accommodation(gen, merged, day_num, day_timeline):
    """Merge accommodation.json into merged-dict."""
    if not (gen.accommodation and "days" in gen.accommodation):
        return
    day_acc = next((d for d in gen.accommodation["days"] if d.get("day") == day_num), {})
    if "accommodation" not in day_acc:
        return
    card = _acc_card(gen, day_acc["accommodation"], day_timeline)
    merged["accommodation"] = card
    merged["budget"]["accommodation"] = card["cost"]


def _trans_icon_type(loc_change, ui_local):
    """Pick icon + display strings for an itinerary transportation entry."""
    tt = loc_change.get("type_base", "")
    if "train" in tt.lower():
        return ("\U0001f684", tt or "High-speed Train",
                loc_change.get("type_local", "") or ui_local.get("high_speed_train", ""))
    if "flight" in tt.lower():
        return ("✈️", tt or "Flight",
                loc_change.get("type_local", "") or ui_local.get("flight", ""))
    return "\U0001f68c", tt, loc_change.get("type_local", "")


def _trans_booking_compute(loc_change):
    """Compute the booking_status string itself (no localization)."""
    bs = loc_change.get("status_base", "")
    if bs:
        return bs
    if loc_change.get("booking_required", False):
        urg = loc_change.get("booking_urgency", "")
        return "URGENT" if ("CRITICAL" in urg or "URGENT" in urg) else "REQUIRED"
    return "VERIFIED"


def _trans_booking(loc_change, ui_local):
    """Pick booking status base/local."""
    bs = _trans_booking_compute(loc_change)
    return bs, loc_change.get("status_local", "") or ui_local.get(bs.lower(), "")


def _trans_route_names(gen, lc):
    """Build from/to/dep/arr base+local fields for a loc_change."""
    fl = lc.get("from_local", "") or gen._extract_local_city(
        lc.get("from_location", ""), lc.get("from", ""))
    tl = lc.get("to_local", "") or gen._extract_local_city(
        lc.get("to_location", ""), lc.get("to", ""))
    dep_b, dep_l = gen._split_bilingual(lc.get("departure_point_base", ""))
    arr_b, arr_l = gen._split_bilingual(lc.get("arrival_point_base", ""))
    return {
        "from_local": fl, "to_local": tl,
        "departure_point_base": dep_b,
        "departure_point_local": lc.get("departure_point_local", "") or dep_l,
        "arrival_point_base": arr_b,
        "arrival_point_local": lc.get("arrival_point_local", "") or arr_l,
    }


def _lc_time_dict(lc):
    """Build the time dict for a loc_change entry."""
    return {
        "start": lc.get("departure_time", "07:00"),
        "end": lc.get("arrival_time", "10:00"),
    }


def _lc_names(lc, rn):
    """Build name_base/name_local fallback strings for a loc_change."""
    nb = lc.get("name_base", "") or f"{lc.get('from_base', '')} → {lc.get('to_base', '')}"
    have_local = rn["from_local"] and rn["to_local"]
    nl = lc.get("name_local", "") or (
        f"{rn['from_local']} → {rn['to_local']}" if have_local else "")
    return nb, nl


def _build_transport_from_loc_change(gen, lc):
    """Build merged['transportation'] from itinerary loc_change format."""
    req = gen.requirements.get("trip_summary", {}).get("ui_labels", {})
    ui_local = req.get("local", {})
    icon, td, tdl = _trans_icon_type(lc, ui_local)
    bs, bl = _trans_booking(lc, ui_local)
    rn = _trans_route_names(gen, lc)
    cost_amt, cost_cur = gen._extract_transport_cost(lc)
    nb, nl = _lc_names(lc, rn)
    out = {
        "name_base": nb, "name_local": nl,
        "from_base": lc.get("from_base", ""), "to_base": lc.get("to_base", ""),
        "type_base": td, "type_local": tdl, "icon": icon,
        "route_number": lc.get("route_number", ""),
        "company_base": lc.get("company_base", ""),
        "company_local": lc.get("company_local", ""),
        "cost": gen._to_display_currency(cost_amt, cost_cur), "cost_local": cost_amt,
        "cost_type_base": lc.get("cost_type_base", ""),
        "cost_type_local": lc.get("cost_type_local", ""),
        "status_base": bs, "status_local": bl,
        "notes_base": lc.get("notes_base", ""), "notes_local": lc.get("notes_local", ""),
        "booking_required": lc.get("booking_required", False),
        "time": _lc_time_dict(lc),
    }
    out.update(rn)
    return out


def _bl_pick_option(from_beijing):
    """Pick the recommended option from a bucket-list from_beijing block."""
    rec = from_beijing.get("recommended", "high_speed_train")
    options = from_beijing.get("options", [])
    return next((o for o in options if o.get("method") == rec),
                options[0] if options else {})


def _bl_icon_type(option, ui_local):
    """Pick icon + display strings for a bucket-list option."""
    method = option.get("method", "")
    if "flight" in method:
        return "✈️", "Flight", ui_local.get("flight", "")
    if "train" in method:
        return ("\U0001f684", option.get("train_type", "High-speed Train"),
                ui_local.get("high_speed_train", ""))
    return "\U0001f68c", method.replace("_", " ").title(), ""


def _bl_notes(option):
    """Build descriptive notes list from a bucket-list option."""
    parts = []
    if "duration_hours" in option:
        parts.append(f"Duration: {option['duration_hours']}h")
    elif "duration_minutes" in option:
        parts.append(f"Duration: {option['duration_minutes']} minutes")
    if "frequency" in option:
        parts.append(f"Frequency: {option['frequency']}")
    if "notes" in option:
        parts.append(option["notes"])
    return parts


def _bl_endpoints(gen, option):
    """Build dep/arr base+local pair from a bucket-list option."""
    stations = option.get("stations", {})
    airports = option.get("airports", {})
    dep = stations.get("departure", "") or airports.get("departure", "")
    arr = stations.get("arrival", "") or airports.get("arrival", "")
    db, dl = gen._split_bilingual(dep)
    ab, al = gen._split_bilingual(arr)
    return db, dl, ab, al


def _bl_route_dict(gen, location_base):
    """Build base/local origin+destination dict for bucket-list."""
    bj_local = gen._extract_local_city("", "Beijing")
    loc_local = gen._extract_local_city("", location_base)
    return {
        "name_base": f"Beijing → {location_base}",
        "name_local": f"{bj_local} → {loc_local}" if bj_local else "",
        "from_base": "Beijing", "to_base": location_base,
        "from_local": bj_local, "to_local": loc_local,
    }


def _bl_cost_dict(gen, option):
    """Build cost-related fields for a bucket-list option."""
    cost_cny = option.get("cost_cny", 0)
    cost_eur = option.get("cost_eur", 0)
    cost_local = cost_cny if cost_cny else cost_eur
    return {
        "cost": gen._to_display_currency(cost_eur if cost_eur else cost_cny,
                                         "EUR" if cost_eur else "CNY"),
        "cost_local": cost_local,
        "cost_type_base": "", "cost_type_local": "",
    }


def _bl_time_dict(option):
    """Build the time dict for a bucket-list option."""
    dep = option.get("departure_times", "")
    start = dep.split(" - ")[0] if dep else "09:00"
    return {"start": start, "end": "12:00"}


def _build_transport_from_bucket_list(gen, from_beijing, location_base):
    """Build merged['transportation'] from bucket-list from_beijing format."""
    option = _bl_pick_option(from_beijing)
    if not option:
        return None
    req = gen.requirements.get("trip_summary", {}).get("ui_labels", {})
    ui_local = req.get("local", {})
    icon, td, tdl = _bl_icon_type(option, ui_local)
    db, dl, ab, al = _bl_endpoints(gen, option)
    rn = option["fastest_trains"][0] if option.get("fastest_trains") else ""
    out = _bl_route_dict(gen, location_base)
    out.update(_bl_cost_dict(gen, option))
    out.update({
        "departure_point_base": db, "departure_point_local": dl,
        "arrival_point_base": ab, "arrival_point_local": al,
        "type_base": td, "type_local": tdl, "icon": icon,
        "route_number": rn, "company_base": "", "company_local": "",
        "status_base": "RECOMMENDED",
        "status_local": ui_local.get("recommended", ""),
        "notes_base": " | ".join(_bl_notes(option)), "notes_local": "",
        "time": _bl_time_dict(option),
    })
    return out


def _seg_card(seg):
    """Build one travel-segment card from a timeline.travel_segments entry."""
    dur = seg.get("duration_minutes", 0)
    return {
        "name_base": seg.get("name_base", ""),
        "name_local": seg.get("name_local", ""),
        "time": {"start": seg["start_time"], "end": seg["end_time"]},
        "duration": f"{dur}min" if dur else "",
        "type_base": seg.get("type_base", "travel"),
        "type_local": seg.get("type_local", ""),
        "icon": seg.get("icon", "\U0001f6b6"),
    }


def _merge_travel_segments(gen, merged, day_num):
    """Append raw travel_segments from timeline.json to merged."""
    if not (gen.timeline and "days" in gen.timeline):
        return
    tdo = next((d for d in gen.timeline["days"] if d.get("day") == day_num), None)
    if not tdo:
        return
    for seg in tdo.get("travel_segments", []) or []:
        if seg.get("start_time") and seg.get("end_time"):
            merged.setdefault("travel_segments", []).append(_seg_card(seg))


def _select_transport_block(gen, dt, location_base):
    """Pick the right transport-builder and return the built block (or None)."""
    loc_change = dt.get("location_change")
    if loc_change:
        return _build_transport_from_loc_change(gen, loc_change)
    from_beijing = dt.get("from_beijing")
    if from_beijing:
        return _build_transport_from_bucket_list(gen, from_beijing, location_base)
    return None


def merge_transportation(gen, merged, day_num):
    """Merge transportation.json + travel_segments into merged-dict."""
    if gen.transportation and "days" in gen.transportation:
        dt = next((d for d in gen.transportation["days"] if d.get("day") == day_num), {})
        block = _select_transport_block(gen, dt, merged["location_base"])
        if block:
            merged["transportation"] = block
    _merge_travel_segments(gen, merged, day_num)
    if merged.get("transportation") and merged["transportation"].get("cost", 0) > 0:
        merged["budget"]["transportation"] = merged["transportation"]["cost"]
    gen._inject_intra_routes(merged, day_num)


def calculate_budget_total(merged):
    """Final budget total = sum of all category subtotals."""
    b = merged["budget"]
    b["total"] = sum([b["meals"], b["attractions"], b["entertainment"],
                      b["accommodation"], b["shopping"], b["cafe"],
                      b["transportation"]])


def _is_optional_no_time(item):
    """True if an item is optional and lacks a timeline time slot."""
    return bool(item.get("optional")) and not item.get("time")


def _collect_unscheduled_for_cat(merged, cat):
    """Return list of optional-no-time items from one merged category."""
    out = []
    for item in merged.get(cat, []) or []:
        if _is_optional_no_time(item):
            rec = dict(item)
            rec["_category"] = cat
            out.append(rec)
    return out


def extract_unscheduled_optionals(merged):
    """Bug-3: build merged['unscheduled_optionals'] list (does not remove).

    Items remain in their per-category arrays so the existing per-category
    React sections still render them; the new list lets the template add
    a dedicated 'Unscheduled / Optional' section.
    """
    out = []
    for cat in ("attractions", "entertainment", "shopping", "cafe"):
        out.extend(_collect_unscheduled_for_cat(merged, cat))
    if out:
        merged["unscheduled_optionals"] = out
