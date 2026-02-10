#!/usr/bin/env python3
"""
Interactive React Travel Plan Generator
Converts skeleton.json + agent outputs → standalone React HTML application
Generates single-file HTML with embedded React components
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime


class InteractiveHTMLGenerator:
    """Generate interactive React travel plan from skeleton and agent data"""

    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data" / plan_id

        # Load all data
        self.skeleton = self._load_json("plan-skeleton.json")
        self.attractions = self._load_json("attractions.json")
        self.meals = self._load_json("meals.json")
        self.accommodation = self._load_json("accommodation.json")
        self.entertainment = self._load_json("entertainment.json")
        self.shopping = self._load_json("shopping.json")
        self.transportation = self._load_json("transportation.json")
        self.timeline = self._load_json("timeline.json")
        self.budget = self._load_json("budget.json")

        # Load requirements-skeleton for ui_labels (toggle display text per trip)
        self.requirements = self._load_json("requirements-skeleton.json")

        # Load image fetcher for real photos
        self.images_cache = self._load_json("images.json")

        # Load currency config for display
        self._eur_to_cny_rate = self._load_eur_to_cny_rate()
        self._display_currency, self._display_symbol = self._load_display_currency()

    def _load_eur_to_cny_rate(self) -> float:
        """Fetch real-time EUR→CNY rate via fetch-exchange-rate.sh, fallback to config."""
        fetch_script = self.base_dir / "scripts" / "utils" / "fetch-exchange-rate.sh"
        if fetch_script.exists():
            try:
                result = subprocess.run(
                    [str(fetch_script), "EUR", "CNY"],
                    capture_output=True, text=True, check=True, timeout=10
                )
                rate = float(result.stdout.strip())
                print(f"Exchange rate (real-time): 1 EUR = {rate} CNY", file=sys.stderr)
                return rate
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
                print(f"Warning: Real-time exchange rate fetch failed: {e}, using config fallback", file=sys.stderr)

        # Fallback to config
        config_path = self.base_dir / "config" / "currency-config.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            cny_to_eur = config.get("fallback_exchange_rate", 0.128)
            rate = 1.0 / cny_to_eur if cny_to_eur > 0 else 7.8
            print(f"Exchange rate (config fallback): 1 EUR = {rate} CNY", file=sys.stderr)
            return rate
        except (FileNotFoundError, json.JSONDecodeError):
            return 7.8

    def _load_display_currency(self) -> tuple:
        """Load display currency from config/currency-config.json."""
        config_path = self.base_dir / "config" / "currency-config.json"
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            currency = config.get("default_display_currency", "EUR")
            symbol_map = config.get("currency_symbol_map", {})
            symbol = symbol_map.get(currency, "€")
            print(f"Display currency: {currency} ({symbol})", file=sys.stderr)
            return currency, symbol
        except (FileNotFoundError, json.JSONDecodeError):
            return "EUR", "€"

    def _to_display_currency(self, amount: float, source_currency: str = "CNY") -> float:
        """Convert any amount to display currency (EUR) using proper exchange rates."""
        if amount == 0:
            return 0
        if source_currency == self._display_currency:
            return amount
        # Convert source to EUR
        if self._display_currency == "EUR":
            if source_currency == "CNY":
                return amount / self._eur_to_cny_rate if self._eur_to_cny_rate > 0 else 0
            elif source_currency == "USD":
                # USD to EUR (approximate: 1 USD ~ 0.92 EUR)
                return amount * 0.92
            else:
                # Unknown currency, treat as CNY
                return amount / self._eur_to_cny_rate if self._eur_to_cny_rate > 0 else 0
        return amount

    # Common Chinese city names for bilingual display
    CITY_NAMES_LOCAL = {
        "chongqing": "重庆", "bazhong": "巴中", "chengdu": "成都",
        "shanghai": "上海", "beijing": "北京", "harbin": "哈尔滨",
        "guangzhou": "广州", "shenzhen": "深圳", "hangzhou": "杭州",
        "suzhou": "苏州", "nanjing": "南京", "xian": "西安",
        "guilin": "桂林", "kunming": "昆明", "lijiang": "丽江",
        "hong kong": "香港", "macau": "澳门", "taipei": "台北",
        "lhasa": "拉萨", "qingdao": "青岛", "dalian": "大连",
        "sanya": "三亚", "xiamen": "厦门", "wuhan": "武汉",
        "changsha": "长沙", "zhangjiajie": "张家界", "chengde": "承德",
        "tianjin": "天津",
    }

    def _extract_local_city(self, location_field: str, city_name: str) -> str:
        """Extract Chinese city name from location field or city name lookup."""
        # Try to find Chinese characters in the location field
        import re
        if location_field:
            chinese = re.findall(r'[\u4e00-\u9fff]+', location_field)
            if chinese:
                return chinese[0]  # First Chinese word group (usually city name)
        # Fallback to lookup table
        return self.CITY_NAMES_LOCAL.get(city_name.lower(), "")

    def _split_bilingual(self, text: str) -> tuple:
        """Split 'English (Chinese)' format into (base, local) tuple.

        Fix #9: Parse inline bilingual strings like 'Chongqing North Station (重庆北站)'
        and separate into base (English) and local (Chinese) parts.
        Returns (base, local). If no Chinese parenthetical found, returns (text, text).
        """
        import re
        if not text:
            return ("", "")
        m = re.match(r'^(.+?)\s*\(([^\)]+)\)\s*$', text)
        if m:
            eng, chn = m.group(1).strip(), m.group(2).strip()
            if re.search(r'[\u4e00-\u9fff]', chn):
                return (eng, chn)
        return (text, text)

    def _extract_transport_cost_cny(self, loc_change: dict) -> float:
        """Extract the most accurate CNY cost from transportation data.

        Priority: route_details.verified_train.cost_cny > cost_cny > cost (with currency check)
        """
        # Check route_details for verified cost_cny
        route_details = loc_change.get("route_details", {})
        verified = route_details.get("verified_train") or route_details.get("verified_flight") or {}
        if verified.get("cost_cny"):
            return float(verified["cost_cny"])

        # Check top-level cost_cny
        if loc_change.get("cost_cny"):
            return float(loc_change["cost_cny"])

        # Fallback: use cost field with currency awareness
        cost = loc_change.get("cost", 0)
        currency = loc_change.get("currency", "CNY")
        if currency == "CNY":
            return float(cost)
        elif currency == "USD":
            return float(cost) * 7.3  # approximate USD→CNY
        elif currency == "EUR":
            return float(cost) * 8.2  # approximate EUR→CNY
        return float(cost)

    def _is_home_location(self, item: dict) -> bool:
        """Check if item represents a home/family location.

        Fix #7: Identify home/family locations so image fallback logic
        can use neighborhood-based search instead of irrelevant stock photos.
        """
        name = (
            (item.get("name_base") or "") +
            (item.get("name_local") or "") +
            (item.get("name") or "")
        ).lower()
        item_type = (item.get("type") or "").lower()
        home_name_keywords = ["family home", "家", "home", "family"]
        home_type_keywords = ["family", "home stay", "homestay"]
        return (
            any(kw in name for kw in home_name_keywords) or
            any(kw in item_type for kw in home_type_keywords)
        )

    def _format_trip_type(self, trip_type: str) -> str:
        """Convert trip_type code to natural language (Fix #1, #3)
        Root cause: commit 52d3528 - no formatting for trip types
        """
        type_map = {
            "bucket_list": "Bucket List",
            "weekend_extended": "Extended Weekend",
            "weekend_short": "Short Weekend",
            "itinerary": "Itinerary",
            "day_trip": "Day Trip",
            "week_long": "Week-long Trip"
        }
        return type_map.get(trip_type, trip_type.replace("_", " ").title())

    def _format_preferences(self, preferences: dict) -> str:
        """Format preferences without code prefixes (Fix #2)
        Root cause: commit 52d3528 - dict keys shown as prefixes
        """
        if not isinstance(preferences, dict):
            return str(preferences)

        # Remove keys like 'trip_style:', just show values
        formatted = []
        for key, value in preferences.items():
            if key == "trip_style":
                # Skip trip_style entirely as it's redundant with trip_type
                continue
            formatted.append(str(value))

        return ", ".join(formatted) if formatted else ""

    def _load_json(self, filename: str) -> dict:
        """Load JSON file from data directory"""
        path = self.data_dir / filename
        if not path.exists():
            print(f"Warning: {filename} not found, using empty dict")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Agent files have structure: { agent, status, data: {...} }
            # Extract actual data from 'data' field if it exists
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
                return data['data']

            return data

    def _format_type(self, type_code: str) -> str:
        """Convert type code to natural language (Fix #6)
        Root cause: commit 123f8df - no formatter for type codes
        Examples: historical_site → Historical Site, cultural_performance → Cultural Performance
        """
        if not type_code:
            return ""

        # Common type mappings
        type_map = {
            "historical_site": "Historical Site",
            "cultural_district": "Cultural District",
            "religious_site": "Religious Site",
            "museum": "Museum",
            "park": "Park",
            "cultural_performance": "Cultural Performance",
            "nightlife": "Nightlife",
            "spa_wellness": "Spa & Wellness",
            "shopping": "Shopping",
            "hotel": "Hotel",
            "hostel": "Hostel",
            "guesthouse": "Guesthouse"
        }

        # Return mapped value or format by replacing underscores and title-casing
        return type_map.get(type_code, type_code.replace("_", " ").title())

    def _get_cover_image(self, location: str, index: int = 0) -> str:
        """Get cover image URL for location from images cache or fallback to Unsplash
        Fix #1: City cover images should use cache, not always fallback to Unsplash
        Root cause: commit 123f8df - cache lookup logic was incomplete
        """
        # Try to get from images cache first
        if self.images_cache and "city_covers" in self.images_cache:
            city_covers = self.images_cache["city_covers"]
            # Try exact match first
            if location in city_covers:
                url = city_covers[location]
                if url and url.startswith("http"):
                    return url

            # Try case-insensitive match
            key = location.lower()
            for city, url in city_covers.items():
                if city.lower() == key:
                    if url and url.startswith("http"):
                        return url

            # Try partial match (for variations like "Xi'an" vs "Xian")
            for city, url in city_covers.items():
                if city.lower() in key or key in city.lower():
                    if url and url.startswith("http"):
                        return url

        # NO FALLBACK - return empty string if not in cache
        return ""

    def _get_placeholder_image(self, category: str, poi_name: str = "", gaode_id: str = "",
                              name_base: str = "", name_local: str = "",
                              location_base: str = "", location_local: str = "",
                              is_home: bool = False) -> str:
        """Get image from cache ONLY - NO fallbacks allowed.

        Fix #7: For home/family locations, skip name-based lookups (which return
        irrelevant results) and try location/address-based cache lookups instead.
        """
        # ONLY return images from cache, never fallback
        if self.images_cache and "pois" in self.images_cache:
            pois = self.images_cache["pois"]

            # Fix #7: For home locations, try name/location/substring lookup
            if is_home:
                # Try exact name-based cache keys
                for name in [poi_name, name_base, name_local]:
                    if not name:
                        continue
                    for prefix in ["gaode_", "google_"]:
                        cache_key = f"{prefix}{name}"
                        if cache_key in pois:
                            return pois[cache_key]
                # Try location-based cache keys
                for loc in [location_local, location_base]:
                    if not loc or len(loc) < 3:
                        continue
                    for prefix in ["gaode_", "google_"]:
                        cache_key = f"{prefix}{loc}"
                        if cache_key in pois:
                            return pois[cache_key]
                # Fallback: substring match — find any cache key containing
                # one of our names, or vice versa
                search_terms = [n for n in [poi_name, name_base, name_local] if n and len(n) > 2]
                for cache_key, url in pois.items():
                    for term in search_terms:
                        if term in cache_key or cache_key.split("_", 1)[-1] in term:
                            return url
                # For home locations, return empty rather than a misleading image
                return ""

            # Try gaode_id cache key
            if gaode_id:
                cache_key = f"gaode_{gaode_id}"
                if cache_key in pois:
                    return pois[cache_key]

            # Try exact match with all name variants
            for name in [poi_name, name_base, name_local]:
                if not name:
                    continue
                for prefix in ["gaode_", "google_"]:
                    cache_key = f"{prefix}{name}"
                    if cache_key in pois:
                        return pois[cache_key]

            # Try substring match: cache key contains name_base or name_local
            # Handles keys like "gaode_Raffles City Observation Deck (来福士观景台)"
            # matching name_base="Raffles City Observation Deck" or name_local="来福士观景台"
            for name in [name_base, name_local, poi_name]:
                if not name or len(name) < 3:
                    continue
                for cache_key, url in pois.items():
                    if name in cache_key:
                        return url

        # NO FALLBACK - return empty string if not in cache
        return ""

    def _normalize_time(self, time_val, default_duration_hours: float = 1.0) -> dict:
        """Normalize time values to {start, end} dict format.

        Handles:
        - dict with start/end: returns as-is
        - string "HH:MM-HH:MM": splits into start/end
        - string "HH:MM": uses default_duration_hours to calculate end
        - None/invalid: returns None
        """
        if isinstance(time_val, dict) and time_val.get("start") and time_val.get("end"):
            return time_val
        if isinstance(time_val, str):
            if "-" in time_val and ":" in time_val:
                # Format: "07:00-08:00"
                parts = time_val.split("-")
                if len(parts) == 2:
                    return {"start": parts[0].strip(), "end": parts[1].strip()}
            elif ":" in time_val:
                # Format: "22:00" - single time, add default duration
                try:
                    h, m = map(int, time_val.split(":"))
                    end_h = h + int(default_duration_hours)
                    end_m = m + int((default_duration_hours % 1) * 60)
                    if end_m >= 60:
                        end_h += 1
                        end_m -= 60
                    if end_h >= 24:
                        end_h = 23
                        end_m = 59
                    return {"start": time_val, "end": f"{end_h:02d}:{end_m:02d}"}
                except (ValueError, TypeError):
                    pass
        return None

    def _find_timeline_item(self, item_name: str, day_timeline: dict,
                            time_hint: str = None) -> dict:
        """Find timeline entry for given item name with precise matching.

        Root cause fix: Previous fuzzy matching matched "Travel to X"/"Walk to X"
        transit entries instead of actual POI entries. Now excludes transit entries
        and uses multi-tier matching: exact > base-name exact > substring (POI only).

        When multiple entries match the same name (e.g. "Family Home" appears as
        both lunch and dinner), uses time_hint to pick the closest match.
        Args:
            time_hint: Expected time slot like "breakfast"/"lunch"/"dinner" or "HH:MM"
        """
        if not day_timeline or not item_name:
            return None

        # Transit prefixes to exclude from matching (these are travel segments, not POIs)
        # Note: "hotel check" intentionally omitted so accommodation can match
        # "Hotel check-in" entries in timeline. Sync-agent-data.py keeps "hotel check"
        # in its own list because _sync_accommodation uses direct name lookup instead.
        transit_prefixes = (
            "travel to", "walk to", "drive to", "taxi to", "bus to",
            "train to", "metro to", "subway to", "transfer to",
            "travel from", "walk from", "drive from",
            "travel back", "return to", "board train",
            "check luggage", "wake up", "arrive ",
            "return home", "free time", "settle in",
        )

        # Time hint ranges for meal slots
        hint_ranges = {
            "breakfast": (5, 10),   # 05:00-10:00
            "lunch": (10, 15),      # 10:00-15:00
            "dinner": (17, 23),     # 17:00-23:00
        }

        def _is_transit(key: str) -> bool:
            return key.lower().startswith(transit_prefixes)

        def _time_in_range(tl_val: dict, hint: str) -> bool:
            """Check if timeline entry falls within the hint time range."""
            if not hint or not tl_val:
                return True
            start = tl_val.get("start_time", "")
            if not start:
                return True
            try:
                h = int(start.split(":")[0])
            except (ValueError, IndexError):
                return True
            if hint in hint_ranges:
                lo, hi = hint_ranges[hint]
                return lo <= h < hi
            # Direct HH:MM hint - match within 2 hours
            try:
                hint_h = int(hint.split(":")[0])
                return abs(h - hint_h) <= 2
            except (ValueError, IndexError):
                return True

        def _collect_matches(candidates):
            """From a list of (key, val) candidates, pick the best one using time_hint."""
            if not candidates:
                return None
            if len(candidates) == 1 or not time_hint:
                return candidates[0][1]
            # Multiple candidates: prefer the one matching the time hint
            for key, val in candidates:
                if _time_in_range(val, time_hint):
                    return val
            return candidates[0][1]

        # Tier 1: Exact match (highest priority)
        exact = [(k, v) for k, v in day_timeline.items() if k == item_name]
        if exact:
            return _collect_matches(exact)

        # Tier 2: Base-name exact match (strip parenthetical Chinese/English suffixes)
        item_base = item_name.split("(")[0].strip().split("（")[0].strip()
        tier2 = []
        for timeline_key, timeline_val in day_timeline.items():
            if _is_transit(timeline_key):
                continue
            timeline_base = timeline_key.split("(")[0].strip().split("（")[0].strip()
            if item_base.lower() == timeline_base.lower():
                tier2.append((timeline_key, timeline_val))
        if tier2:
            return _collect_matches(tier2)

        # Tier 3: Substring match - POI entries only (exclude transit)
        tier3 = []
        for timeline_key, timeline_val in day_timeline.items():
            if _is_transit(timeline_key):
                continue
            if item_base.lower() in timeline_key.lower() or timeline_key.split("(")[0].strip().lower() in item_base.lower():
                tier3.append((timeline_key, timeline_val))
        if tier3:
            return _collect_matches(tier3)

        return None

    def _merge_day_data(self, day_skeleton: dict) -> dict:
        """Merge skeleton day with agent data

        Fix #6: Use actual times from timeline.json instead of virtual defaults
        Root cause: timeline.json loaded but never consumed in merge logic
        """
        day_num = day_skeleton.get("day", 1)
        date = day_skeleton.get("date", "")
        location = day_skeleton.get("location", "Unknown")

        # Fix #6: Get timeline for this day (root cause: timeline data ignored)
        # Note: _load_json already extracts 'data' field, so timeline has 'days' directly
        day_timeline = {}
        if self.timeline and "days" in self.timeline:
            timeline_day = next(
                (d for d in self.timeline["days"] if d.get("day") == day_num),
                None
            )
            if timeline_day and "timeline" in timeline_day:
                day_timeline = timeline_day["timeline"]

        merged = {
            "day": day_num,
            "date": date,
            "location": location,
            "cover": self._get_cover_image(location, day_num),
            "user_plans": day_skeleton.get("user_plans", []),
            "meals": {},
            "attractions": [],
            "entertainment": [],
            "accommodation": None,
            "transportation": None,
            "shopping": [],
            "budget": {
                "meals": 0,
                "attractions": 0,
                "entertainment": 0,
                "accommodation": 0,
                "shopping": 0,
                "transportation": 0,
                "total": 0
            }
        }

        # Fix #6: Merge meals with actual timeline times instead of virtual defaults
        # Root cause: hardcoded meal_default_times used instead of reading timeline.json
        meal_default_times = {
            "breakfast": {"start": "08:00", "end": "09:00"},
            "lunch": {"start": "12:00", "end": "13:30"},
            "dinner": {"start": "18:30", "end": "20:00"}
        }
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if self.meals and "days" in self.meals:
                day_meals = next((d for d in self.meals["days"] if d.get("day") == day_num), {})
                if meal_type in day_meals:
                    meal = day_meals[meal_type]
                    # Convert cost to display currency (EUR)
                    cost = meal.get("cost", 0)
                    meal_currency = meal.get("currency", "CNY")
                    if cost == 0 and "price_range_eur_low" in meal:
                        cost = meal.get("price_range_eur_low", 0)
                        meal_currency = "EUR"
                    cost = self._to_display_currency(cost, meal_currency)

                    # Fix #6: Lookup actual time from timeline.json instead of using virtual defaults
                    meal_name = meal.get("name_base", meal.get("name", ""))
                    timeline_item = self._find_timeline_item(meal_name, day_timeline, time_hint=meal_type)
                    if timeline_item and "start_time" in timeline_item and "end_time" in timeline_item:
                        meal_time = {
                            "start": timeline_item["start_time"],
                            "end": timeline_item["end_time"]
                        }
                    else:
                        # Fallback to default times if timeline missing
                        raw_time = meal.get("time", meal_default_times[meal_type])
                        meal_time = self._normalize_time(raw_time) or meal_default_times[meal_type]

                    # Root cause fix (commit 8f2bddd): Support standardized name_base/name_local fields
                    # Backward compatible with old name/name_en format
                    name_base = meal.get("name_base", meal_name)
                    name_local = meal.get("name_local", meal.get("name_en", ""))

                    merged["meals"][meal_type] = {
                        "name": name_local if name_local else name_base,  # Display local by default
                        "name_base": name_base,
                        "name_local": name_local,
                        "name_en": meal.get("name_en", ""),  # Keep for backward compatibility
                        "location": meal.get("location_local", meal.get("location", "")),
                        "location_base": meal.get("location_base", meal.get("location", "")),
                        "location_local": meal.get("location_local", meal.get("location", "")),
                        "coordinates": meal.get("coordinates", {}),
                        "cost": cost,
                        "cuisine": meal.get("cuisine", ""),
                        "cuisine_local": meal.get("cuisine_local", ""),
                        "signature_dishes": meal.get("signature_dishes", ""),
                        "signature_dishes_local": meal.get("signature_dishes_local", ""),
                        "notes": meal.get("notes", ""),
                        "notes_local": meal.get("notes_local", ""),
                        "image": self._get_placeholder_image(
                            "meal",
                            poi_name=name_local if name_local else meal_name,
                            gaode_id=meal.get("gaode_id", ""),
                            name_base=name_base,
                            name_local=name_local,
                            location_base=meal.get("location_base", meal.get("location", "")),
                            location_local=meal.get("location_local", meal.get("location", "")),
                            is_home=self._is_home_location(meal)
                        ),
                        "time": meal_time,
                        "links": meal.get("links", {})
                    }
                    merged["budget"]["meals"] += cost

        # Merge attractions with sequential time allocation
        if self.attractions and "days" in self.attractions:
            day_attrs = next((d for d in self.attractions["days"] if d.get("day") == day_num), {})
            if "attractions" in day_attrs:
                current_time_hour = 10  # Start attractions at 10:00
                current_time_minute = 0
                for attr in day_attrs["attractions"]:
                    # Fix #6: Lookup actual time from timeline.json first
                    attr_name = attr.get("name_base", attr.get("name", ""))
                    timeline_item = self._find_timeline_item(attr_name, day_timeline)

                    if timeline_item and "start_time" in timeline_item and "end_time" in timeline_item:
                        # Use actual timeline times
                        attr_time = {
                            "start": timeline_item["start_time"],
                            "end": timeline_item["end_time"]
                        }
                    elif not attr.get("time"):
                        # Fallback: Calculate virtual time based on recommended duration
                        duration_str = attr.get("recommended_duration", "2h")
                        duration_hours = 2.0  # default
                        if "h" in duration_str:
                            try:
                                duration_hours = float(duration_str.replace("h", "").strip())
                            except:
                                duration_hours = 2.0
                        elif "min" in duration_str:
                            try:
                                duration_hours = float(duration_str.replace("min", "").strip()) / 60
                            except:
                                duration_hours = 2.0

                        start_time = f"{current_time_hour:02d}:{current_time_minute:02d}"
                        end_hour = current_time_hour + int(duration_hours)
                        end_minute = current_time_minute + int((duration_hours % 1) * 60)
                        if end_minute >= 60:
                            end_hour += 1
                            end_minute -= 60
                        end_time = f"{end_hour:02d}:{end_minute:02d}"

                        attr_time = {"start": start_time, "end": end_time}

                        # Update current time for next attraction (add 30min buffer)
                        current_time_hour = end_hour
                        current_time_minute = end_minute + 30
                        if current_time_minute >= 60:
                            current_time_hour += 1
                            current_time_minute -= 60
                    else:
                        attr_time = self._normalize_time(attr.get("time"), default_duration_hours=1.5) or attr.get("time")

                    # Convert cost to display currency (EUR)
                    cost = attr.get("cost", 0)
                    attr_currency = attr.get("currency", "CNY")
                    if cost == 0 and "ticket_price_eur" in attr:
                        cost = attr.get("ticket_price_eur", 0)
                        attr_currency = "EUR"
                    cost = self._to_display_currency(cost, attr_currency)

                    # Root cause fix (commit 8f2bddd): Support standardized name_base/name_local fields
                    # Backward compatible with old name/name_en format
                    attr_name_base = attr.get("name_base", attr_name)
                    attr_name_local = attr.get("name_local", attr.get("name_en", ""))

                    # Fix issue #11: Detect optional items from timeline name or attraction notes
                    is_optional = False
                    if day_timeline:
                        for tl_name in day_timeline:
                            if attr_name.lower() in tl_name.lower() and "optional" in tl_name.lower():
                                is_optional = True
                                break
                    if "optional" in str(attr.get("notes", "")).lower():
                        is_optional = True

                    merged["attractions"].append({
                        "name": attr_name_local if attr_name_local else attr_name_base,  # Display local by default
                        "name_base": attr_name_base,
                        "name_local": attr_name_local,
                        "name_en": attr.get("name_en", ""),  # Keep for backward compatibility
                        "location": attr.get("location_local", attr.get("location", "")),
                        "location_base": attr.get("location_base", attr.get("location", "")),
                        "location_local": attr.get("location_local", attr.get("location", "")),
                        "coordinates": attr.get("coordinates", {}),
                        "type": self._format_type(attr.get("type", "")),
                        "type_local": attr.get("type_local", ""),
                        "cost": cost,
                        "opening_hours": attr.get("opening_hours", ""),
                        "recommended_duration": attr.get("recommended_duration", ""),
                        "optional": is_optional,
                        "image": self._get_placeholder_image(
                            "attraction",
                            poi_name=attr_name_local if attr_name_local else attr_name,
                            gaode_id=attr.get("gaode_id", ""),
                            name_base=attr_name_base,
                            name_local=attr_name_local,
                            location_base=attr.get("location_base", attr.get("location", "")),
                            location_local=attr.get("location_local", attr.get("location", "")),
                            is_home=self._is_home_location(attr)
                        ),
                        "highlights": attr.get("highlights", []),
                        "notes": attr.get("notes", ""),
                        "notes_local": attr.get("notes_local", ""),
                        "why_worth_visiting": attr.get("why_worth_visiting", ""),
                        "why_worth_visiting_local": attr.get("why_worth_visiting_local", ""),
                        "best_time_to_visit": attr.get("best_time_to_visit", ""),
                        "best_time_to_visit_local": attr.get("best_time_to_visit_local", ""),
                        "time": attr_time,
                        "links": attr.get("links", {})
                    })
                    merged["budget"]["attractions"] += cost

        # Merge entertainment with sequential evening time allocation
        if self.entertainment and "days" in self.entertainment:
            day_ent = next((d for d in self.entertainment["days"] if d.get("day") == day_num), {})
            if "entertainment" in day_ent:
                current_time_hour = 19  # Start entertainment at 19:00 (after dinner)
                current_time_minute = 0
                for ent in day_ent["entertainment"]:
                    # Fix #6: Lookup actual time from timeline.json first
                    ent_name = ent.get("name_base", ent.get("name", ""))
                    timeline_item = self._find_timeline_item(ent_name, day_timeline)

                    if timeline_item and "start_time" in timeline_item and "end_time" in timeline_item:
                        # Use actual timeline times
                        ent_time = {
                            "start": timeline_item["start_time"],
                            "end": timeline_item["end_time"]
                        }
                    else:
                        # Try to normalize existing time value
                        normalized = self._normalize_time(ent.get("time"), default_duration_hours=1.0)
                        if normalized:
                            ent_time = normalized
                        else:
                            # Fallback: Calculate virtual time based on duration
                            duration_str = ent.get("duration", "2h")
                            duration_hours = 2.0
                            if "h" in duration_str:
                                try:
                                    duration_hours = float(duration_str.replace("h", "").strip())
                                except:
                                    duration_hours = 2.0
                            elif "min" in duration_str:
                                try:
                                    duration_hours = float(duration_str.replace("min", "").strip()) / 60
                                except:
                                    duration_hours = 2.0

                            start_time = f"{current_time_hour:02d}:{current_time_minute:02d}"
                            end_hour = current_time_hour + int(duration_hours)
                            end_minute = current_time_minute + int((duration_hours % 1) * 60)
                            if end_minute >= 60:
                                end_hour += 1
                                end_minute -= 60
                            end_time = f"{end_hour:02d}:{end_minute:02d}"

                            ent_time = {"start": start_time, "end": end_time}

                            # Update current time for next entertainment
                            current_time_hour = end_hour
                            current_time_minute = end_minute

                    # Convert cost to display currency (EUR)
                    cost = ent.get("cost", 0)
                    ent_currency = ent.get("currency", "CNY")
                    if cost == 0 and "cost_eur" in ent:
                        cost = ent.get("cost_eur", 0)
                        ent_currency = "EUR"
                    cost = self._to_display_currency(cost, ent_currency)

                    # Root cause fix (commit 8f2bddd): Support standardized name_base/name_local fields
                    # Backward compatible with old name/name_en format
                    ent_name_base = ent.get("name_base", ent_name)
                    ent_name_local = ent.get("name_local", ent.get("name_en", ""))

                    merged["entertainment"].append({
                        "name": ent_name_local if ent_name_local else ent_name_base,  # Display local by default
                        "name_base": ent_name_base,
                        "name_local": ent_name_local,
                        "name_en": ent.get("name_en", ""),  # Keep for backward compatibility
                        "location": ent.get("location_local", ent.get("location", "")),
                        "location_base": ent.get("location_base", ent.get("location", "")),
                        "location_local": ent.get("location_local", ent.get("location", "")),
                        "coordinates": ent.get("coordinates", {}),
                        "type": self._format_type(ent.get("type", "")),
                        "type_local": ent.get("type_local", ""),
                        "cost": cost,
                        "duration": ent.get("duration", ""),
                        "note": ent.get("note", ""),
                        "note_local": ent.get("note_local", ""),
                        "notes": ent.get("notes", ""),
                        "notes_local": ent.get("notes_local", ""),
                        "image": self._get_placeholder_image(
                            "entertainment",
                            poi_name=ent_name_local if ent_name_local else ent_name,
                            gaode_id=ent.get("gaode_id", ""),
                            name_base=ent_name_base,
                            name_local=ent_name_local,
                            location_base=ent.get("location_base", ent.get("location", "")),
                            location_local=ent.get("location_local", ent.get("location", "")),
                            is_home=self._is_home_location(ent)
                        ),
                        "time": ent_time,
                        "links": ent.get("links", {})
                    })
                    merged["budget"]["entertainment"] += cost

        # Merge shopping items into day data and budget
        if self.shopping and "days" in self.shopping:
            day_shop = next((d for d in self.shopping["days"] if d.get("day") == day_num), {})
            for shop_item in day_shop.get("shopping", []):
                cost = shop_item.get("cost", 0)
                shop_currency = shop_item.get("currency", "CNY")
                cost = self._to_display_currency(cost, shop_currency)

                shop_name_base = shop_item.get("name_base", shop_item.get("name", ""))
                shop_name_local = shop_item.get("name_local", "")

                merged["shopping"].append({
                    "name": shop_name_local if shop_name_local else shop_name_base,
                    "name_base": shop_name_base,
                    "name_local": shop_name_local,
                    "location": shop_item.get("location_local", shop_item.get("location_base", "")),
                    "location_base": shop_item.get("location_base", ""),
                    "location_local": shop_item.get("location_local", ""),
                    "coordinates": shop_item.get("coordinates", {}),
                    "type": shop_item.get("type", "Shopping"),
                    "cost": cost,
                    "notes": shop_item.get("notes", ""),
                    "image": self._get_placeholder_image(
                        "attraction",
                        poi_name=shop_name_local if shop_name_local else shop_name_base,
                        name_base=shop_name_base,
                        name_local=shop_name_local
                    ),
                    "time": self._normalize_time(shop_item.get("time", {})) or {"start": "15:00", "end": "16:00"},
                    "links": {}
                })
                merged["budget"]["shopping"] += cost

        # Merge accommodation
        if self.accommodation and "days" in self.accommodation:
            day_acc = next((d for d in self.accommodation["days"] if d.get("day") == day_num), {})
            if "accommodation" in day_acc:
                acc = day_acc["accommodation"]
                # Convert cost to display currency (EUR)
                cost = acc.get("cost", 0)
                acc_currency = acc.get("currency", "CNY")
                if cost == 0 and "price_per_night_eur" in acc:
                    cost = acc.get("price_per_night_eur", 0)
                    acc_currency = "EUR"
                cost = self._to_display_currency(cost, acc_currency)

                # Root cause fix: Support standardized name_base/name_local fields
                acc_name_base = acc.get("name_base", acc.get("name", ""))
                acc_name_local = acc.get("name_local", acc.get("name_cn", ""))

                # Fix issue #10 (root cause): Lookup check-in time from timeline.
                # "hotel check" removed from transit_prefixes so _find_timeline_item()
                # can now match "Hotel check-in" entries directly (no workaround needed).
                acc_time = {"start": "15:00", "end": "16:00"}  # default
                if day_timeline:
                    acc_name_for_lookup = acc.get("name_base", acc.get("name", ""))
                    timeline_item_acc = self._find_timeline_item(acc_name_for_lookup, day_timeline)
                    if not timeline_item_acc:
                        # Fallback: search for "Hotel check-in" as a timeline key name
                        timeline_item_acc = self._find_timeline_item("Hotel check-in", day_timeline)
                    if timeline_item_acc and "start_time" in timeline_item_acc and "end_time" in timeline_item_acc:
                        acc_time = {"start": timeline_item_acc["start_time"], "end": timeline_item_acc["end_time"]}
                else:
                    raw_acc_time = acc.get("time")
                    if raw_acc_time:
                        normalized_acc_time = self._normalize_time(raw_acc_time)
                        if normalized_acc_time:
                            acc_time = normalized_acc_time

                # Parse rating: handle both numeric "rating" and string "star_rating" (e.g. "4-star")
                rating = acc.get("rating")
                if rating is None:
                    star_rating_str = acc.get("star_rating", "")
                    if star_rating_str:
                        import re
                        m = re.search(r'(\d+)', str(star_rating_str))
                        rating = float(m.group(1)) if m else None

                # Parse stars: prefer explicit stars, fallback to rating
                stars = acc.get("stars", 0)
                if not stars and rating is not None:
                    stars = int(rating)

                merged["accommodation"] = {
                    "name": acc_name_local if acc_name_local else acc_name_base,
                    "name_base": acc_name_base,
                    "name_local": acc_name_local,
                    "name_cn": acc.get("name_cn", ""),  # backward compat
                    "type": self._format_type(acc.get("type", "hotel")),
                    "type_local": acc.get("type_local", ""),
                    "location": acc.get("location_local", acc.get("location", "")),
                    "location_base": acc.get("location_base", acc.get("location", "")),
                    "location_local": acc.get("location_local", acc.get("location", "")),
                    "coordinates": acc.get("coordinates", {}),
                    "cost": cost,
                    "rating": rating,
                    "stars": stars if stars else 0,
                    "amenities": acc.get("amenities", []),
                    "check_in": acc.get("check_in", ""),
                    "check_out": acc.get("check_out", ""),
                    "notes": acc.get("notes", ""),
                    "notes_local": acc.get("notes_local", ""),
                    "time": acc_time,
                    "links": acc.get("links", {}),
                    "image": self._get_placeholder_image(
                        "accommodation",
                        poi_name=acc_name_local if acc_name_local else acc_name_base,
                        gaode_id=acc.get("gaode_id", ""),
                        name_base=acc_name_base,
                        name_local=acc_name_local,
                        location_base=acc.get("location_base", acc.get("location", "")),
                        location_local=acc.get("location_local", acc.get("location", "")),
                        is_home=self._is_home_location(acc)
                    )
                }
                merged["budget"]["accommodation"] = cost

        # Merge transportation (Fix Issue #8: transportation missing from HTML)
        # Root cause: transportation.json loaded but never processed in _merge_day_data
        # Fix Issue #9: Handle both location_change (itinerary) and from_beijing (bucket-list) formats
        if self.transportation and "days" in self.transportation:
            day_trans = next((d for d in self.transportation["days"] if d.get("day") == day_num), {})

            # Support both formats: location_change (itinerary) and from_beijing (bucket-list)
            loc_change = day_trans.get("location_change")
            from_beijing = day_trans.get("from_beijing")

            if loc_change:
                # Itinerary format: location_change with route_details
                route_details = loc_change.get("route_details", {})

                # Determine transport type and icon
                transport_type = loc_change.get("transportation", "")
                if "train" in transport_type.lower():
                    icon = "🚄"
                    type_display = "High-speed Train"
                elif "flight" in transport_type.lower():
                    icon = "✈️"
                    type_display = "Flight"
                else:
                    icon = "🚌"
                    type_display = transport_type

                # Extract route info based on transport type
                if "flight_number" in route_details:
                    # Flight
                    departure_point = route_details.get("departure_airport", "")
                    arrival_point = route_details.get("arrival_airport", "")
                    route_number = route_details.get("flight_number", "")
                    airline = route_details.get("airline", "")
                else:
                    # Train
                    departure_point = route_details.get("departure_station", "")
                    arrival_point = route_details.get("arrival_station", "")
                    verified = route_details.get("verified_train", {})
                    raw_train_num = verified.get("train_number", "")
                    # Filter out metadata strings - only keep actual train numbers (e.g., D2205, G8051)
                    route_number = raw_train_num if raw_train_num and not raw_train_num.upper().startswith("VERIFIED") else ""
                    airline = ""

                # Booking status
                booking_status = loc_change.get("booking_status", "")
                if not booking_status:
                    if loc_change.get("booking_required", False):
                        urgency = loc_change.get("booking_urgency", "")
                        if "CRITICAL" in urgency or "URGENT" in urgency:
                            booking_status = "URGENT"
                        else:
                            booking_status = "REQUIRED"
                    else:
                        booking_status = "VERIFIED"

                # Extract bilingual city names from location fields
                from_local = self._extract_local_city(loc_change.get("from_location", ""), loc_change.get("from", ""))
                to_local = self._extract_local_city(loc_change.get("to_location", ""), loc_change.get("to", ""))

                # Fix #9: Split bilingual departure/arrival points
                dep_base, dep_local = self._split_bilingual(departure_point)
                arr_base, arr_local = self._split_bilingual(arrival_point)

                merged["transportation"] = {
                    "from": loc_change.get("from", ""),
                    "to": loc_change.get("to", ""),
                    "from_local": from_local,
                    "to_local": to_local,
                    "departure_point": dep_base,
                    "departure_point_local": dep_local,
                    "arrival_point": arr_base,
                    "arrival_point_local": arr_local,
                    "departure_time": loc_change.get("departure_time", ""),
                    "arrival_time": loc_change.get("arrival_time", ""),
                    "transport_type": type_display,
                    "icon": icon,
                    "route_number": route_number,
                    "airline": airline,
                    "cost": self._to_display_currency(
                        self._extract_transport_cost_cny(loc_change),
                        "CNY"
                    ),
                    "cost_type": loc_change.get("cost_type", ""),
                    "booking_status": booking_status,
                    "booking_urgency": loc_change.get("booking_urgency", ""),
                    "notes": loc_change.get("notes", ""),
                    "notes_local": loc_change.get("notes_local", ""),
                    "time": {
                        "start": loc_change.get("departure_time", "07:00"),
                        "end": loc_change.get("arrival_time", "10:00")
                    }
                }

            elif from_beijing:
                # Bucket-list format: from_beijing with options array
                # Use recommended option
                recommended_method = from_beijing.get("recommended", "high_speed_train")
                options = from_beijing.get("options", [])

                # Find recommended option
                option = next((o for o in options if o.get("method") == recommended_method),
                             options[0] if options else {})

                if option:
                    method = option.get("method", "")

                    # Determine transport type and icon
                    if "flight" in method:
                        icon = "✈️"
                        type_display = "Flight"
                    elif "train" in method:
                        icon = "🚄"
                        type_display = option.get("train_type", "High-speed Train")
                    else:
                        icon = "🚌"
                        type_display = method.replace("_", " ").title()

                    # Extract station/airport info
                    stations = option.get("stations", {})
                    airports = option.get("airports", {})
                    departure_point = stations.get("departure", "") or airports.get("departure", "")
                    arrival_point = stations.get("arrival", "") or airports.get("arrival", "")

                    # Build descriptive notes
                    notes_parts = []
                    if "duration_hours" in option:
                        hours = option["duration_hours"]
                        notes_parts.append(f"Duration: {hours}h")
                    elif "duration_minutes" in option:
                        mins = option["duration_minutes"]
                        notes_parts.append(f"Duration: {mins} minutes")

                    if "frequency" in option:
                        notes_parts.append(f"Frequency: {option['frequency']}")

                    if "notes" in option:
                        notes_parts.append(option["notes"])

                    # Extract cost and convert to display currency
                    cost_cny = option.get("cost_cny", 0)
                    cost_eur = option.get("cost_eur", 0)

                    # Route info (train number, flight code, etc.)
                    route_number = ""
                    if "fastest_trains" in option and option["fastest_trains"]:
                        route_number = option["fastest_trains"][0]

                    # Fix #9: Split bilingual departure/arrival points for bucket-list
                    bl_dep_base, bl_dep_local = self._split_bilingual(departure_point)
                    bl_arr_base, bl_arr_local = self._split_bilingual(arrival_point)

                    merged["transportation"] = {
                        "from": "Beijing",
                        "to": location,
                        "from_local": self.CITY_NAMES_LOCAL.get("beijing", "北京"),
                        "to_local": self._extract_local_city("", location),
                        "departure_point": bl_dep_base,
                        "departure_point_local": bl_dep_local,
                        "arrival_point": bl_arr_base,
                        "arrival_point_local": bl_arr_local,
                        "departure_time": option.get("departure_times", "").split(" - ")[0] if option.get("departure_times") else "09:00",
                        "arrival_time": "",  # Not specified in bucket-list format
                        "transport_type": type_display,
                        "icon": icon,
                        "route_number": route_number,
                        "airline": "",
                        "cost": self._to_display_currency(cost_eur if cost_eur else cost_cny, "EUR" if cost_eur else "CNY"),
                        "booking_status": "RECOMMENDED",
                        "booking_urgency": "",
                        "notes": " | ".join(notes_parts),
                        "time": {
                            "start": option.get("departure_times", "").split(" - ")[0] if option.get("departure_times") else "09:00",
                            "end": "12:00"  # Placeholder
                        }
                    }

        # Read structured travel_segments from timeline data (produced by enrichment agent)
        # travel_segments is at the day level (same level as "timeline"), not inside it
        # Each segment has: name_base, name_local, mode, start_time, end_time, duration_minutes
        timeline_day_obj = None
        if self.timeline and "days" in self.timeline:
            timeline_day_obj = next(
                (d for d in self.timeline["days"] if d.get("day") == day_num),
                None
            )
        if timeline_day_obj:
            raw_segments = timeline_day_obj.get("travel_segments", [])
            for seg in raw_segments:
                if not seg.get("start_time") or not seg.get("end_time"):
                    continue
                duration_min = seg.get("duration_minutes", 0)
                merged.setdefault("travel_segments", []).append({
                    "name": seg.get("name_base", ""),
                    "name_base": seg.get("name_base", ""),
                    "name_local": seg.get("name_local", ""),
                    "mode": seg.get("mode", "walk"),
                    "time": {"start": seg["start_time"], "end": seg["end_time"]},
                    "duration": f"{duration_min}min" if duration_min else "",
                    "type": "travel"
                })

        # Add transportation cost to budget (from merged transportation data)
        if merged.get("transportation") and merged["transportation"].get("cost", 0) > 0:
            merged["budget"]["transportation"] = merged["transportation"]["cost"]

        # Calculate total budget (includes all categories)
        merged["budget"]["total"] = sum([
            merged["budget"]["meals"],
            merged["budget"]["attractions"],
            merged["budget"]["entertainment"],
            merged["budget"]["accommodation"],
            merged["budget"]["shopping"],
            merged["budget"]["transportation"]
        ])

        return merged

    def _group_days_by_location(self, days: list) -> list:
        """Group days by location to create trips"""
        if not days:
            return []

        trips = []
        current_trip = None

        for day in days:
            location = day.get("location", "Unknown")

            if current_trip is None or current_trip["name"] != location:
                # Start new trip
                current_trip = {
                    "name": location,
                    "days_label": "1 day",
                    "cover": day.get("cover", ""),
                    "days": [day]
                }
                trips.append(current_trip)
            else:
                # Continue current trip
                current_trip["days"].append(day)
                current_trip["days_label"] = f"{len(current_trip['days'])} days"

        return trips

    def generate_plan_data(self) -> dict:
        """Generate complete PLAN_DATA structure

        Supports both formats:
        - itinerary: trip_summary + days (multi-day trips)
        - bucket_list: city_guides (10 destination options)
        """

        # Check format type
        is_bucket_list = self.skeleton.get("bucket_list_type") == "city_guides"

        if is_bucket_list:
            # Bucket list format: city_guides
            return self._generate_bucket_list_data()
        else:
            # Itinerary format: trip_summary + days
            return self._generate_itinerary_data()

    def _generate_bucket_list_data(self) -> dict:
        """Generate PLAN_DATA for bucket list (city_guides format)"""

        # Get toggle display labels from requirements-skeleton ui_labels
        ui_labels = self.requirements.get("trip_summary", {}).get("ui_labels", {})

        trip_summary = {
            "trip_type": "bucket_list",
            "description": "Destination Options",
            "base_location": "",
            "period": "",
            "travelers": "1 adult",
            "budget_per_trip": f"{self._display_symbol}200-500",
            "preferences": "",
            "base_display": ui_labels.get("base_display", "EN"),
            "local_display": ui_labels.get("local_display", "Local")
        }

        # Convert each city into a trip
        trips = []
        cities = self.skeleton.get("cities", [])

        for city_data in cities:
            city_name = city_data.get("city", "Unknown")

            # Create a single "day" for this city with all POIs
            day = {
                "day": 1,
                "date": city_data.get("recommended_duration", "1-2 days"),
                "location": city_name,
                "cover": self._get_cover_image(city_name, len(trips)),
                "user_plans": city_data.get("user_requirements", []),
                "meals": {},
                "attractions": [],
                "entertainment": [],
                "accommodation": None,
                "shopping": [],
                "budget": {
                    "meals": 0,
                    "attractions": 0,
                    "entertainment": 0,
                    "accommodation": 0,
                    "shopping": 0,
                    "transportation": 0,
                    "total": 0
                }
            }

            # Get POI data from agent files
            # Find attractions for this city
            if self.attractions and "cities" in self.attractions:
                city_attractions = next((c for c in self.attractions["cities"] if c.get("city") == city_name), {})
                for attr in city_attractions.get("attractions", []):
                    a_name_base = attr.get("name_base", attr.get("name", ""))
                    a_name_local = attr.get("name_local", attr.get("name_chinese", ""))
                    day["attractions"].append({
                        "name": a_name_local if a_name_local else a_name_base,
                        "name_base": a_name_base,
                        "name_local": a_name_local,
                        "location": city_name,
                        "type": self._format_type(attr.get("type", "")),
                        "type_local": attr.get("type_local", ""),
                        "cost": self._to_display_currency(attr.get("ticket_price_eur", 0), "EUR"),
                        "opening_hours": attr.get("opening_hours", ""),
                        "recommended_duration": f"{attr.get('recommended_duration_hours', 2)}h",
                        "image": self._get_placeholder_image("attraction", poi_name=a_name_local if a_name_local else a_name_base, name_base=a_name_base, name_local=a_name_local),
                        "highlights": attr.get("tips", [])[:3],
                        "notes": attr.get("notes", ""),
                        "notes_local": attr.get("notes_local", ""),
                        "time": {"start": "10:00", "end": "12:00"},
                        "links": {}
                    })
                    day["budget"]["attractions"] += self._to_display_currency(attr.get("ticket_price_eur", 0), "EUR")

            # Find meals for this city
            if self.meals and "cities" in self.meals:
                city_meals = next((c for c in self.meals["cities"] if c.get("city") == city_name), {})
                for i, meal in enumerate(city_meals.get("meals", [])[:3]):
                    meal_type = ["breakfast", "lunch", "dinner"][i]
                    m_name_base = meal.get("name_base", meal.get("name", ""))
                    m_name_local = meal.get("name_local", meal.get("name_chinese", ""))
                    day["meals"][meal_type] = {
                        "name": m_name_local if m_name_local else m_name_base,
                        "name_base": m_name_base,
                        "name_local": m_name_local,
                        "cost": self._to_display_currency(meal.get("price_range_eur_low", 10), "EUR"),
                        "cuisine": meal.get("cuisine_type", ""),
                        "cuisine_local": meal.get("cuisine_local", ""),
                        "signature_dishes": meal.get("signature_dish", ""),
                        "signature_dishes_local": meal.get("signature_dishes_local", ""),
                        "notes": meal.get("notes", ""),
                        "notes_local": meal.get("notes_local", ""),
                        "image": self._get_placeholder_image("meal", poi_name=m_name_local if m_name_local else m_name_base, name_base=m_name_base, name_local=m_name_local),
                        "time": {"start": "08:00", "end": "09:00"} if meal_type == "breakfast" else
                                {"start": "12:00", "end": "13:30"} if meal_type == "lunch" else
                                {"start": "18:30", "end": "20:00"},
                        "links": {}
                    }
                    day["budget"]["meals"] += self._to_display_currency(meal.get("price_range_eur_low", 10), "EUR")

            # Calculate total
            day["budget"]["total"] = sum([
                day["budget"]["meals"],
                day["budget"]["attractions"],
                day["budget"]["entertainment"],
                day["budget"]["accommodation"],
                day["budget"]["shopping"],
                day["budget"]["transportation"]
            ])

            # Create trip with this single day
            trip = {
                "name": city_name,
                "days_label": city_data.get("recommended_duration", "1-2 days"),
                "cover": day["cover"],
                "days": [day]
            }
            trips.append(trip)

        return {
            "trip_summary": trip_summary,
            "trips": trips
        }

    def _generate_itinerary_data(self) -> dict:
        """Generate PLAN_DATA for itinerary (trip_summary + days format)"""

        # Build trip summary from skeleton's trip_summary section
        skel_summary = self.skeleton.get("trip_summary", {})
        prefs = skel_summary.get("preferences", {})
        if isinstance(prefs, dict):
            # Fix #2: Use formatter to remove code prefixes
            prefs_str = self._format_preferences(prefs)
        else:
            prefs_str = str(prefs)

        # Fix #2: Calculate period from duration_days
        # Root cause: Missing from original implementation
        duration_days = skel_summary.get("duration_days", 0)
        period = f"{duration_days} day{'s' if duration_days != 1 else ''}"

        # Get toggle display labels from requirements-skeleton ui_labels
        ui_labels = self.requirements.get("trip_summary", {}).get("ui_labels", {})

        trip_summary = {
            # Fix #1, #3: Format trip_type for natural language display
            "trip_type": self._format_trip_type(skel_summary.get("trip_type", "itinerary")),
            "description": skel_summary.get("description", "Travel Plan"),
            "base_location": skel_summary.get("base_location", ""),
            "period": period,
            "travelers": skel_summary.get("travelers", "1 adult"),
            "budget_per_trip": skel_summary.get("budget_per_trip", f"{self._display_symbol}500"),
            "preferences": prefs_str,
            "base_display": ui_labels.get("base_display", "EN"),
            "local_display": ui_labels.get("local_display", "Local")
        }

        # Merge all days
        merged_days = []
        if "days" in self.skeleton:
            for day_skel in self.skeleton["days"]:
                merged_day = self._merge_day_data(day_skel)
                merged_days.append(merged_day)

        # Group days into trips
        trips = self._group_days_by_location(merged_days)

        return {
            "trip_summary": trip_summary,
            "trips": trips
        }

    def generate_html(self) -> str:
        """Generate complete HTML with embedded React app"""

        plan_data = self.generate_plan_data()
        plan_data_json = json.dumps(plan_data, ensure_ascii=False, indent=2)

        # Read React component template
        react_template = self._read_react_template()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{plan_data['trip_summary']['description']}</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      overflow-x: hidden;
    }}
  </style>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel">
    // Embedded PLAN_DATA
    const PLAN_DATA = {plan_data_json};
    const CURRENCY_SYMBOL = "{self._display_symbol}";

    {react_template}

    // Render app
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<NotionTravelApp />);
  </script>
</body>
</html>"""

        return html

    def _read_react_template(self) -> str:
        """Read React component template"""
        # Return the React component code directly
        return """
// ============================================================
// HOOKS
// ============================================================
const { useState, useEffect, useCallback } = React;

const useBreakpoint = () => {
  const [bp, setBp] = useState(() => {
    const w = window.innerWidth;
    return w < 640 ? 'sm' : w < 960 ? 'md' : 'lg';
  });
  useEffect(() => {
    const h = () => { const w = window.innerWidth; setBp(w < 640 ? 'sm' : w < 960 ? 'md' : 'lg'); };
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);
  return bp;
};

// Mobile detection helper (reused by RedNoteLink, MapLink, etc.)
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

// ============================================================
// ATOMS
// ============================================================
const LinkChip = ({ href, type, compact }) => {
  if (!href) return null;
  const cfg = {
    google_maps: { icon: '🌍', label: 'Google Maps', bg: '#edf2fc', color: '#2b63b5' },
    gaode: { icon: '🗺️', label: '高德', bg: '#e9f5ec', color: '#1a7a32' },
    xiaohongshu: { icon: '📕', label: '小红书', bg: '#fce8e6', color: '#c5221f' },
    booking: { icon: '🏨', label: 'Booking', bg: '#e8eaf6', color: '#1a237e' },
    dianping: { icon: '⭐', label: '点评', bg: '#fff3e0', color: '#e65100' }
  }[type] || { icon: '🔗', label: 'Link', bg: '#f5f5f5', color: '#666' };
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" style={{
      display: 'inline-flex', alignItems: 'center', gap: '3px',
      padding: compact ? '2px 5px' : '2px 8px',
      background: cfg.bg, color: cfg.color,
      borderRadius: '3px', fontSize: compact ? '10px' : '11px',
      fontWeight: '500', textDecoration: 'none', transition: 'opacity .12s'
    }}
      onMouseEnter={e => e.currentTarget.style.opacity = '0.7'}
      onMouseLeave={e => e.currentTarget.style.opacity = '1'}
    >{cfg.icon}{compact ? '' : ` ${cfg.label}`}</a>
  );
};

const LinksRow = ({ links, compact }) => {
  if (!links || !Object.keys(links).length) return null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
      {Object.entries(links).map(([t, u]) => <LinkChip key={t} href={u} type={t} compact={compact} />)}
    </div>
  );
};

const PropertyRow = ({ label, children }) => (
  <div style={{ display: 'flex', alignItems: 'baseline', padding: '5px 0', fontSize: '14px', lineHeight: '1.6' }}>
    <span style={{ width: '130px', flexShrink: 0, color: '#9b9a97', fontSize: '13px' }}>{label}</span>
    <span style={{ color: '#37352f' }}>{children}</span>
  </div>
);

const Section = ({ title, icon, children }) => (
  <div style={{ marginBottom: '32px' }}>
    <div style={{
      display: 'flex', alignItems: 'center', gap: '8px',
      fontSize: '15px', fontWeight: '600', color: '#37352f',
      paddingBottom: '6px', marginBottom: '14px',
      borderBottom: '1px solid #edece9'
    }}>
      <span style={{ fontSize: '16px' }}>{icon}</span> {title}
    </div>
    {children}
  </div>
);

const Donut = ({ budget, size = 80, onBudgetClick, day }) => {
  const items = [
    { v: budget.meals || 0, c: '#f0b429', k: 'meals' },
    { v: budget.attractions || 0, c: '#4a90d9', k: 'attractions' },
    { v: budget.entertainment || 0, c: '#9b6dd7', k: 'entertainment' },
    { v: budget.accommodation || 0, c: '#45b26b', k: 'accommodation' },
    { v: budget.shopping || 0, c: '#e07c5a', k: 'shopping' },
    { v: budget.transportation || 0, c: '#0ea5e9', k: 'transportation' }
  ].filter(i => i.v > 0);
  const t = items.reduce((s, i) => s + i.v, 0);
  if (t === 0) return (
    <svg width={size} height={size} viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="15.915" fill="none" stroke="#e5e4e1" strokeWidth="2.5" />
      <text x="18" y="18" textAnchor="middle" dy=".35em" fontSize="6" fill="#9b9a97">{CURRENCY_SYMBOL}0</text>
    </svg>
  );
  let cum = 0;
  const p = (r, a) => ({ x: 50 + r * Math.cos((a - 90) * Math.PI / 180), y: 50 + r * Math.sin((a - 90) * Math.PI / 180) });
  const arc = (sa, ea) => { const s = p(44, ea), e = p(44, sa); return `M${s.x},${s.y}A44,44,0,${ea - sa > 180 ? 1 : 0},0,${e.x},${e.y}L50,50Z`; };
  return (
    <svg viewBox="0 0 100 100" style={{ width: size, height: size }}>
      {items.length === 1 ? (
        <circle cx="50" cy="50" r="44" fill={items[0].c} style={{ cursor: onBudgetClick ? 'pointer' : 'default' }} onClick={() => onBudgetClick && onBudgetClick(items[0].k, day)} />
      ) : (
        items.map((it, i) => { const a = (it.v / t) * 360; const d = arc(cum, cum + a); cum += a; return <path key={i} d={d} fill={it.c} style={{ cursor: onBudgetClick ? 'pointer' : 'default' }} onClick={() => onBudgetClick && onBudgetClick(it.k, day)} />; })
      )}
      <circle cx="50" cy="50" r="24" fill="white" />
    </svg>
  );
};

const PropLine = ({ label, value }) => (
  <div style={{ fontSize: '12px', lineHeight: 1.7 }}>
    <span style={{ color: '#9b9a97' }}>{label}</span>{' '}
    <span style={{ color: '#37352f' }}>{value}</span>
  </div>
);

// ============================================================
// SIDEBAR
// ============================================================
const Sidebar = ({ trips, selTrip, selDay, onSelect, isOpen, onClose, bp }) => {
  const [exp, setExp] = useState({ [trips[0]?.name]: true });
  const mobile = bp === 'sm';
  const W = bp === 'lg' ? 240 : 220;

  return (
    <>
      {mobile && isOpen && <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 199 }} />}
      <div style={{
        width: W, flexShrink: 0, background: '#fbfbfa', borderRight: '1px solid #f0efed',
        padding: '14px 8px', overflowY: 'auto', height: mobile ? '100%' : '100vh',
        position: mobile ? 'fixed' : 'sticky', top: 0, left: 0, bottom: mobile ? 0 : 'auto', zIndex: 200,
        transform: mobile && !isOpen ? `translateX(-${W + 10}px)` : 'none',
        transition: 'transform .25s ease',
        boxShadow: mobile && isOpen ? '2px 0 8px rgba(0,0,0,0.06)' : 'none'
      }}>
        <div style={{ padding: '4px 10px 12px', fontSize: '12px', fontWeight: '600', color: '#37352f', display: 'flex', alignItems: 'center', gap: '6px', lineHeight: '1.45' }}>
          <span>📋</span>
          <span style={{ flex: 1 }}>{PLAN_DATA.trip_summary.description}</span>
          {mobile && <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b4b4b4', fontSize: '14px' }}>✕</button>}
        </div>

        {trips.map((trip, ti) => {
          const open = exp[trip.name] !== false;
          const has = trip.days.length > 0;
          return (
            <div key={trip.name}>
              <div
                onClick={() => { setExp(p => ({ ...p, [trip.name]: !p[trip.name] })); if (has) onSelect(ti, 0); if (mobile) onClose(); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: '4px',
                  padding: '5px 10px', borderRadius: '5px', cursor: 'pointer',
                  fontSize: '13px', color: '#37352f',
                  background: selTrip === ti ? 'rgba(55,53,47,0.06)' : 'transparent',
                  borderLeft: selTrip === ti ? '2px solid #37352f' : '2px solid transparent',
                  transition: 'all .1s'
                }}
                onMouseEnter={e => { if (selTrip !== ti) e.currentTarget.style.background = 'rgba(55,53,47,0.03)'; }}
                onMouseLeave={e => { if (selTrip !== ti) e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ fontSize: '9px', color: '#b4b4b4', transform: open ? 'rotate(90deg)' : '', transition: 'transform .15s', display: 'inline-block', marginRight: '2px' }}>▶</span>
                <span style={{ fontWeight: '500', flex: 1 }}>{trip.name}</span>
                <span style={{ fontSize: '11px', color: '#b4b4b4' }}>({trip.days_label})</span>
              </div>
              {open && has && (
                <div style={{ marginLeft: '16px' }}>
                  {trip.days.map((d, di) => {
                    const active = selTrip === ti && selDay === di;
                    return (
                      <div key={di}
                        onClick={() => { onSelect(ti, di); if (mobile) onClose(); }}
                        style={{
                          padding: '4px 10px', borderRadius: '5px', cursor: 'pointer',
                          fontSize: '13px', color: '#37352f',
                          background: active ? 'rgba(55,53,47,0.06)' : 'transparent',
                          fontWeight: active ? '500' : '400',
                          borderLeft: active ? '2px solid #37352f' : '2px solid transparent',
                          transition: 'all .1s'
                        }}
                        onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'rgba(55,53,47,0.03)'; }}
                        onMouseLeave={e => { if (!active) e.currentTarget.style.background = active ? 'rgba(55,53,47,0.06)' : 'transparent'; }}
                      >📄 Day {d.day}</div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
};

// ============================================================
// ITEM DETAIL SIDEBAR
// ============================================================
const ItemDetailSidebar = ({ item, type, onClose, bp, lang, mapProvider }) => {
  if (!item) return null;
  const sm = bp === 'sm';
  const W = sm ? '85%' : '400px';

  return (
    <>
      <div onClick={onClose} style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 299
      }} />
      <div style={{
        position: 'fixed', right: 0, top: 0, bottom: 0,
        width: W, background: '#fff',
        boxShadow: '-2px 0 8px rgba(0,0,0,0.08)',
        overflowY: 'auto', zIndex: 300,
        animation: 'slideIn 0.25s ease',
        padding: '24px'
      }}>
        <style>{`@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ fontSize: '20px' }}>
            {{ meal: '🍽️', attraction: '📍', entertainment: '🎭', accommodation: '🏨', transportation: item.icon || '🚄' }[type] || '📄'}
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: '20px', color: '#b4b4b4', padding: '4px 8px'
          }}>✕</button>
        </div>

        {item.image && (
          <div style={{
            width: '100%', height: '200px', borderRadius: '8px',
            overflow: 'hidden', marginBottom: '20px', background: '#f5f3ef'
          }}>
            <img src={item.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              onError={e => e.target.style.display = 'none'} />
          </div>
        )}

        <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#37352f', margin: '0 0 4px' }}>
          {getDisplayName(item, lang)}
          <RedNoteLink name={item.name_local || item.name_base} />
        </h2>

        <div style={{ borderTop: '1px solid #f0efed', paddingTop: '16px' }}>
          {item.time && (
            <PropertyRow label="Time">
              {item.time.start} – {item.time.end}
            </PropertyRow>
          )}
          {/* Category-specific field ordering */}
          {type === 'accommodation' ? (<>
            {(item.cost !== undefined && (item.cost > 0 || item.cost_type === 'prepaid')) && <PropertyRow label="Cost">{fmtCost(item.cost, item.cost_type)}</PropertyRow>}
            {getDisplayField(item, 'type', lang) && <PropertyRow label="Type">{getDisplayField(item, 'type', lang)}</PropertyRow>}
            {item.stars > 0 && <PropertyRow label="Stars"><span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(item.stars)}</span></PropertyRow>}
            {item.rating !== undefined && item.rating !== null && <PropertyRow label="Rating">{item.rating}/5</PropertyRow>}
            {item.check_in && <PropertyRow label="Check-in">{item.check_in}</PropertyRow>}
            {item.check_out && <PropertyRow label="Check-out">{item.check_out}</PropertyRow>}
            {(item.location || item.location_base || item.location_local) && <PropertyRow label="Location"><MapLink item={item} lang={lang} mapProvider={mapProvider} /></PropertyRow>}
          </>) : (<>
            {(item.cost !== undefined && (item.cost > 0 || item.cost_type === 'prepaid')) && <PropertyRow label="Cost">{fmtCost(item.cost, item.cost_type)}</PropertyRow>}
            {getDisplayField(item, 'cuisine', lang) && <PropertyRow label="Cuisine">{getDisplayField(item, 'cuisine', lang)}</PropertyRow>}
            {getDisplayField(item, 'signature_dishes', lang) && <PropertyRow label="Signature Dishes">{getDisplayField(item, 'signature_dishes', lang)}</PropertyRow>}
            {getDisplayField(item, 'type', lang) && <PropertyRow label="Type">{getDisplayField(item, 'type', lang)}</PropertyRow>}
            {(item.location || item.location_base || item.location_local) && <PropertyRow label="Location"><MapLink item={item} lang={lang} mapProvider={mapProvider} /></PropertyRow>}
            {item.opening_hours && <PropertyRow label="Opening Hours">{item.opening_hours}</PropertyRow>}
            {item.recommended_duration && <PropertyRow label="Duration">{item.recommended_duration}</PropertyRow>}
            {item.duration && <PropertyRow label="Duration">{item.duration}</PropertyRow>}
            {item.rating !== undefined && item.rating !== null && <PropertyRow label="Rating">{item.rating}/5</PropertyRow>}
            {item.stars > 0 && <PropertyRow label="Stars"><span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(item.stars)}</span></PropertyRow>}
            {item.check_in && <PropertyRow label="Check-in">{item.check_in}</PropertyRow>}
            {item.check_out && <PropertyRow label="Check-out">{item.check_out}</PropertyRow>}
          </>)}
          {item.amenities && item.amenities.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>Amenities</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {item.amenities.map((a, i) => (
                  <span key={i} style={{ fontSize: '12px', padding: '3px 8px', background: '#f5f5f3', borderRadius: '4px', color: '#6b6b6b' }}>{a}</span>
                ))}
              </div>
            </div>
          )}
          {item.departure_time && item.arrival_time && <PropertyRow label={"Time"}>{item.departure_time} – {item.arrival_time}</PropertyRow>}
          {item.transport_type && <PropertyRow label={"Type"}>{item.transport_type}</PropertyRow>}
          {item.departure_point && <PropertyRow label={"Route"}>{lang === 'local' && item.departure_point_local ? item.departure_point_local : item.departure_point} → {lang === 'local' && item.arrival_point_local ? item.arrival_point_local : item.arrival_point}</PropertyRow>}
          {item.transport_type && item.cost != null && <PropertyRow label={lang === 'local' ? '费用' : 'Cost'}>{fmtCost(item.cost)}</PropertyRow>}
          {!item.transport_type && item.highlights && item.highlights.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>
                Highlights
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '14px', lineHeight: 1.8, color: '#37352f' }}>
                {item.highlights.map((h, i) => <li key={i}>{h}</li>)}
              </ul>
            </div>
          )}
          {!item.transport_type && (lang === 'local' && item.note_local ? item.note_local : item.note) && (
            <div style={{
              marginTop: '16px', padding: '12px 16px',
              background: '#fffdf5', borderRadius: '6px',
              border: '1px solid #f5ecd7', fontSize: '13px', color: '#9a6700'
            }}>
              💡 {lang === 'local' && item.note_local ? item.note_local : item.note}
            </div>
          )}
          {!item.transport_type && (lang === 'local' && item.notes_local ? item.notes_local : item.notes) && (
            <div style={{
              marginTop: '16px', padding: '12px 16px',
              background: '#f5f9fc', borderRadius: '6px',
              border: '1px solid #d9e8f5', fontSize: '13px', color: '#37352f', lineHeight: 1.6
            }}>
              {lang === 'local' && item.notes_local ? item.notes_local : item.notes}
            </div>
          )}
          {!item.transport_type && item.links && Object.keys(item.links).length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>
                Links
              </div>
              <LinksRow links={item.links} />
            </div>
          )}
        </div>
      </div>
    </>
  );
};

// ============================================================
// BUDGET DETAIL SIDEBAR
// ============================================================
const BudgetDetailSidebar = ({ category, items, total, onClose, bp, lang }) => {
  if (!category) return null;
  const sm = bp === 'sm';
  const W = sm ? '85%' : '400px';

  const categoryConfig = {
    meals: { icon: '🍽️', label: lang === 'local' ? '餐饮' : 'Meals', color: '#f0b429' },
    attractions: { icon: '📍', label: lang === 'local' ? '景点' : 'Attractions', color: '#4a90d9' },
    entertainment: { icon: '🎭', label: lang === 'local' ? '娱乐' : 'Entertainment', color: '#9b6dd7' },
    accommodation: { icon: '🏨', label: lang === 'local' ? '住宿' : 'Accommodation', color: '#45b26b' },
    shopping: { icon: '🛍️', label: lang === 'local' ? '购物' : 'Shopping', color: '#e07c5a' },
    transportation: { icon: '🚄', label: lang === 'local' ? '交通' : 'Transport', color: '#0ea5e9' }
  };
  const cfg = categoryConfig[category] || { icon: '💰', label: 'Budget', color: '#37352f' };

  return (
    <>
      <div onClick={onClose} style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.2)', zIndex: 299
      }} />
      <div style={{
        position: 'fixed', right: 0, top: 0, bottom: 0,
        width: W, background: '#fff',
        boxShadow: '-2px 0 8px rgba(0,0,0,0.08)',
        overflowY: 'auto', zIndex: 300,
        animation: 'slideIn 0.25s ease',
        padding: '24px'
      }}>
        <style>{`@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ fontSize: '24px' }}>{cfg.icon}</div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#37352f', margin: 0 }}>
              {cfg.label}
            </h2>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: '20px', color: '#b4b4b4', padding: '4px 8px'
          }}>✕</button>
        </div>

        {items && items.length > 0 ? (
          <div>
            {items.map((item, i) => (
              <div key={i} style={{
                padding: '14px 16px',
                background: '#fbfbfa',
                borderRadius: '6px',
                border: '1px solid #f0efed',
                marginBottom: '10px'
              }}>
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '4px' }}>
                  {lang === 'local' && item.name_local ? item.name_local : (item.name_base || item.name)}
                </div>
                {lang !== 'local' && item.name_local && (
                  <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{item.name_local}</div>
                )}
                {lang === 'local' && item.name_base && item.name_base !== item.name_local && (
                  <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{item.name_base}</div>
                )}
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: '14px', marginTop: '8px'
                }}>
                  <span style={{ color: '#9b9a97' }}>{lang === 'local' ? '费用' : 'Cost'}</span>
                  <span style={{ fontWeight: '600', color: cfg.color }}>
                    {fmtCost(item.cost)}
                  </span>
                </div>
              </div>
            ))}

            <div style={{
              marginTop: '20px', paddingTop: '16px',
              borderTop: '2px solid #edece9'
            }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                fontSize: '16px', fontWeight: '700', color: '#37352f'
              }}>
                <span>{lang === 'local' ? '合计' : 'Total'}</span>
                <span style={{ color: cfg.color }}>{CURRENCY_SYMBOL}{total.toFixed(0)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9b9a97' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>{cfg.icon}</div>
            <div style={{ fontSize: '14px' }}>No items in this category</div>
          </div>
        )}
      </div>
    </>
  );
};

// ============================================================
// KANBAN VIEW
// ============================================================
// Root cause fix (commit 8f2bddd): Helper to get display name based on language preference
const getDisplayName = (item, lang) => {
  if (!item) return '';
  if (lang === 'base') {
    return item.name_base || item.name || '';
  }
  return item.name_local || item.name || '';
};

// All costs are in display currency (from config). Use CURRENCY_SYMBOL.
const fmtCost = (c, costType) => {
  if (costType === 'prepaid') return 'Prepaid';
  const n = Number(c);
  if (!n || n === 0) return 'Free';
  return Number.isInteger(n) ? `${CURRENCY_SYMBOL}${n}` : `${CURRENCY_SYMBOL}${n.toFixed(1)}`;
};

// Fix issues #4,7,12: Language-aware location display
const getDisplayLocation = (item, lang) => {
  if (!item) return '';
  if (lang === 'base') return item.location_base || item.location || '';
  return item.location_local || item.location || '';
};

// Bilingual field helper: returns local variant when lang='local' and data exists
const getDisplayField = (item, field, lang) => {
  if (!item) return '';
  if (lang === 'local' && item[field + '_local']) return item[field + '_local'];
  return item[field + '_base'] || item[field] || '';
};

// Google Maps logo (from Simple Icons)
const GoogleMapsLogo = ({ size = 14 }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} style={{ display: 'block', flexShrink: 0 }}>
    <path fill="#4285F4" d="M19.527 4.799c1.212 2.608.937 5.678-.405 8.173-1.101 2.047-2.744 3.74-4.098 5.614-.619.858-1.244 1.75-1.669 2.727-.141.325-.263.658-.383.992-.121.333-.224.673-.34 1.008-.109.314-.236.684-.627.687h-.007c-.466-.001-.579-.53-.695-.887-.284-.874-.581-1.713-1.019-2.525-.51-.944-1.145-1.817-1.79-2.671L19.527 4.799zM8.545 7.705l-3.959 4.707c.724 1.54 1.821 2.863 2.871 4.18.247.31.494.622.737.936l4.984-5.925-.029.01c-1.741.601-3.691-.291-4.392-1.987a3.377 3.377 0 0 1-.209-.716c-.063-.437-.077-.761-.004-1.198l.001-.007zM5.492 3.149l-.003.004c-1.947 2.466-2.281 5.88-1.117 8.77l4.785-5.689-.058-.05-3.607-3.035zM14.661.436l-3.838 4.563a.295.295 0 0 1 .027-.01c1.6-.551 3.403.15 4.22 1.626.176.319.323.683.377 1.045.068.446.085.773.012 1.22l-.003.016 3.836-4.561A8.382 8.382 0 0 0 14.67.439l-.009-.003zM9.466 5.868L14.162.285l-.047-.012A8.31 8.31 0 0 0 11.986 0a8.439 8.439 0 0 0-6.169 2.766l-.016.018 3.665 3.084z"/>
  </svg>
);

// Gaode Maps (高德地图/AMap) logo - blue location pin with "A" based on brand color #0085fe
const GaodeLogo = ({ size = 14 }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} style={{ display: 'block', flexShrink: 0 }}>
    <path fill="#0085fe" d="M12 0C7.31 0 3.5 3.81 3.5 8.5C3.5 14.88 12 24 12 24s8.5-9.12 8.5-15.5C20.5 3.81 16.69 0 12 0z"/>
    <text x="12" y="12" textAnchor="middle" fill="white" fontSize="10" fontWeight="bold" fontFamily="Arial,sans-serif" dy=".35em">A</text>
  </svg>
);

// Gaode Maps native app deeplink handler for mobile
// Tries native scheme directly, falls back to H5 after 1.5s timeout
const openGaodeNative = (gaodeScheme, gaodeH5) => {
  const start = Date.now();
  const onVisChange = () => {
    // If page became hidden within 3s of click, app probably opened
    if (document.hidden) {
      document.removeEventListener('visibilitychange', onVisChange);
      clearTimeout(fallbackTimer);
    }
  };
  document.addEventListener('visibilitychange', onVisChange);
  // Try native scheme directly
  window.location.href = gaodeScheme;
  // Fallback to H5 if app didn't open
  const fallbackTimer = setTimeout(() => {
    document.removeEventListener('visibilitychange', onVisChange);
    if (!document.hidden && Date.now() - start < 3000) {
      window.location.href = gaodeH5;
    }
  }, 1500);
};

// Map link component with provider toggle support (Google Maps / Gaode Maps)
const MapLink = ({ item, lang, mapProvider = 'gaode' }) => {
  const loc = getDisplayLocation(item, lang);
  if (!loc) return null;
  const coords = item.coordinates;
  let googleHref, gaodeH5, gaodeScheme;
  if (coords && (coords.latitude || coords.lat)) {
    const lat = coords.latitude || coords.lat;
    const lng = coords.longitude || coords.lng;
    googleHref = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc)}&center=${lat},${lng}`;
    gaodeH5 = `https://uri.amap.com/marker?position=${lng},${lat}&name=${encodeURIComponent(loc)}&coordinate=gaode&callnative=0`;
    const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    gaodeScheme = isIOS
      ? `iosamap://viewMap?sourceApplication=travel&poiname=${encodeURIComponent(loc)}&lat=${lat}&lon=${lng}&dev=0`
      : `androidamap://viewMap?sourceApplication=travel&poiname=${encodeURIComponent(loc)}&lat=${lat}&lon=${lng}&dev=0`;
  } else {
    googleHref = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc)}`;
    gaodeH5 = `https://uri.amap.com/search?keyword=${encodeURIComponent(loc)}&callnative=0`;
    const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    gaodeScheme = isIOS
      ? `iosamap://poi?sourceApplication=travel&keywords=${encodeURIComponent(loc)}`
      : `androidamap://poi?sourceApplication=travel&keywords=${encodeURIComponent(loc)}`;
  }
  const isGaode = mapProvider === 'gaode';
  const Logo = isGaode ? GaodeLogo : GoogleMapsLogo;
  const title = isGaode ? 'Open in 高德地图' : 'Open in Google Maps';
  const color = isGaode ? '#0085fe' : '#4285F4';
  const handleClick = (e) => {
    e.stopPropagation();
    if (isGaode && isMobile) {
      e.preventDefault();
      openGaodeNative(gaodeScheme, gaodeH5);
    }
  };
  const href = isGaode ? gaodeH5 : googleHref;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
      <a href={href} target="_blank" rel="noopener noreferrer"
        style={{ color: color, textDecoration: 'none', borderBottom: `1px dashed ${color}` }}
        title={title}
        onClick={handleClick}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
          <Logo size={14} />
          {loc}
        </span>
      </a>
    </span>
  );
};

// Fix issue #8: RedNote (小红书) search link component with official logo
// Official SVG source: https://static.cdnlogo.com/logos/r/77/rednote-xiaohongshu.svg
const XhsLogo = ({ size = 14 }) => (
  <svg viewBox="0 0 377.97 376.53" width={size} height={size} style={{ display: 'block', flexShrink: 0 }}>
    <path fill="#ff2842" d="M43.86,1.11C21.81,5.7,3.59,22.91,1.34,46.07c-2.33,23.92,0,49.25,0,73.3v149.53c0,27.5-6.94,64.79,10.75,87.96,19.11,25.02,53.98,19.06,81.6,19.06h214.03c8.48,0,18.08,1.24,26.39-.49,22.05-4.59,40.26-21.8,42.51-44.96,2.33-23.92,0-49.25,0-73.3V107.64c0-27.5,6.94-64.79-10.75-87.96C346.76-5.34,311.89.62,284.27.62H70.24c-8.48,0-18.08-1.24-26.39.49M177.26,134.02l-10.26,27.85h17.59l-14.66,35.18,13.19,1.47c-1.45,3.93-3.4,11.34-6.35,14.42-2.17,2.26-5.48,1.71-8.31,1.71-6.39,0-19.3,2.65-22.72-4.4-1.57-3.23.68-7.31,1.95-10.26,2.66-6.17,6.19-12.48,7.57-19.06-3.19,0-7.22.63-10.26-.49-11.4-4.19,1.28-22.52,3.91-28.83,1.85-4.43,4.04-14.05,8.06-16.86,5.65-3.94,14.24-1.21,20.28-.73M61.45,226.38c4.03,0,10.02,1.2,12.46-2.93,2.59-4.39.73-14.06.73-19.06v-48.38c0-4.53-2.29-18.38,1.71-21.26,3.29-2.37,17.1-1.87,18.57,2.2,2.4,6.66.24,17.83.24,24.92v46.91c0,8.04,1.39,17.39-1.95,24.92-3.19,7.18-18.04,13.59-25.41,8.06-3.24-2.43-5.55-11.6-6.35-15.39M284.27,134.02v7.33c5.47,0,12.33-1.12,17.59.49,17.56,5.36,16.13,22.61,16.13,37.63,2.93,0,5.93-.23,8.8.49,16.85,4.21,14.66,21.06,14.66,34.69,0,7.27,1.36,15.86-3.42,21.99-5.27,6.75-13.9,5.86-21.5,5.86-2.36,0-6.25.75-8.31-.73-3.85-2.77-5.54-11-6.35-15.39,4.82,0,13.51,1.65,17.35-1.95,4.52-4.25,2.67-20.86-2.69-23.7-2.84-1.5-7.16-.73-10.26-.73h-21.99v42.51h-20.52v-42.51h-20.52v-20.52h20.52v-17.59h-13.19v-20.52h13.19v-7.33h20.52M237.36,141.35v20.52h-11.73v61.57h19.06v19.06h-67.43l7.82-18.32,18.57-.73v-61.57h-11.73v-20.52h45.44M320.92,161.88c0-4.17-.76-9.17.49-13.19,4.9-15.82,28.76-3.07,16.86,10.02-1.35,1.49-3.73,2.22-5.62,2.69-3.75.94-7.89.49-11.73.49M61.45,161.88l-6.11,54.24-10.02,17.59-8.8-23.46,4.4-48.38h20.52M128.88,161.88l4.4,48.38-8.8,21.99h-2.93c-7.87-12.46-8.87-25.31-10.26-39.58-.99-10.14-2.93-20.58-2.93-30.78h20.52M284.27,161.88v17.59h13.19v-17.59h-13.19M174.32,223.45l-7.33,19.06h-32.25l7.82-19.79,11.24.24,20.52.49Z"/>
  </svg>
);
const RedNoteLink = ({ name }) => {
  if (!name) return null;
  const webUrl = `https://www.xiaohongshu.com/search_result/?keyword=${encodeURIComponent(name)}&source=web_explore_feed`;
  const deepUrl = `xhsdiscover://search/result?keyword=${encodeURIComponent(name)}`;
  const href = isMobile ? deepUrl : webUrl;
  return (
    <a href={href} target={isMobile ? '_self' : '_blank'} rel="noopener noreferrer"
      style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', marginLeft: '6px', padding: '2px 6px', background: '#fff0f0', borderRadius: '4px', textDecoration: 'none', fontSize: '11px', color: '#ff2442', border: '1px solid #ffe0e0', transition: 'all .12s', verticalAlign: 'middle' }}
      title="Search on 小红书"
      onClick={e => e.stopPropagation()}
      onMouseEnter={e => { e.currentTarget.style.background = '#ffe0e0'; }}
      onMouseLeave={e => { e.currentTarget.style.background = '#fff0f0'; }}>
      <XhsLogo size={14} />
      <span style={{ fontWeight: '600' }}>小红书</span>
    </a>
  );
};

const ExpandableNotes = ({ text, textLocal, lang, maxLines = 2 }) => {
  const [expanded, setExpanded] = useState(false);
  const displayText = lang === 'local' && textLocal ? textLocal : text;
  if (!displayText) return null;
  return (
    <div style={{ marginTop: '6px', fontSize: '12px', color: '#6b6b6b', background: '#fafaf8', padding: '8px 10px', borderRadius: '6px', border: '1px solid #f0efed' }}>
      <div style={{
        overflow: expanded ? 'visible' : 'hidden',
        display: expanded ? 'block' : '-webkit-box',
        WebkitLineClamp: expanded ? 'unset' : maxLines,
        WebkitBoxOrient: 'vertical',
        lineHeight: 1.6,
        whiteSpace: 'pre-wrap'
      }}>
        {displayText}
      </div>
      <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        style={{ background: 'none', border: 'none', color: '#4a90d9', fontSize: '11px', cursor: 'pointer', padding: '4px 0 0', fontWeight: '500' }}>
        {expanded ? 'Show less' : 'Show more'}
      </button>
    </div>
  );
};

const KanbanView = ({ day, tripSummary, showSummary, bp, lang, mapProvider, onItemClick, onBudgetClick }) => {
  const sm = bp === 'sm';
  const px = sm ? '16px' : bp === 'md' ? '32px' : '48px';

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={{
        width: '100%',
        height: sm ? '120px' : '200px',
        background: day.cover ? `linear-gradient(to bottom, rgba(0,0,0,0) 50%, rgba(0,0,0,0.03) 100%), url(${day.cover})` : '#f5f5f5',
        backgroundSize: 'cover', backgroundPosition: 'center'
      }} />

      <div style={{ padding: `0 ${px}` }}>
        <div style={{ marginTop: sm ? '-24px' : '-36px', marginBottom: '24px' }}>
          <div style={{ fontSize: sm ? '40px' : '56px', lineHeight: 1, marginBottom: '8px' }}>🗺️</div>

          {showSummary ? (
            <>
              <h1 style={{ fontSize: sm ? '24px' : '36px', fontWeight: '700', color: '#37352f', margin: '0 0 20px', lineHeight: 1.25 }}>
                {tripSummary.description}
              </h1>
              <div style={{
                padding: sm ? '12px' : '16px 20px',
                background: '#fbfbfa', borderRadius: '8px',
                border: '1px solid #f0efed', marginBottom: '32px'
              }}>
                <PropertyRow label="Trip Type">{tripSummary.trip_type}</PropertyRow>
                {tripSummary.base_location && <PropertyRow label="Base Location">{tripSummary.base_location}</PropertyRow>}
                <PropertyRow label="Period">{tripSummary.period}</PropertyRow>
                <PropertyRow label="Travelers">{tripSummary.travelers}</PropertyRow>
                <PropertyRow label="Budget / Trip">{tripSummary.budget_per_trip}</PropertyRow>
                {/* Preferences hidden per user request */}
              </div>
            </>
          ) : (
            <h1 style={{ fontSize: sm ? '24px' : '36px', fontWeight: '700', color: '#37352f', margin: '0 0 24px', lineHeight: 1.25 }}>
              Day {day.day} – {day.location}
            </h1>
          )}

          {showSummary && (
            <h2 style={{ fontSize: sm ? '20px' : '26px', fontWeight: '700', color: '#37352f', margin: '0 0 28px' }}>
              Day {day.day} – {day.location}
            </h2>
          )}
        </div>

        {/* User Plans */}
        {day.user_plans && day.user_plans.length > 0 && (
          <Section title="User Plans" icon="📝">
            <div style={{
              padding: '14px 18px', background: '#fafafa', borderRadius: '6px',
              border: '1px solid #f0efed'
            }}>
              <ul style={{ margin: 0, padding: '0 0 0 18px', fontSize: '14px', lineHeight: 2, color: '#37352f' }}>
                {day.user_plans.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          </Section>
        )}

        {/* Meals */}
        <Section title="Meals" icon="🍽️">
          <div style={{ display: 'grid', gridTemplateColumns: sm ? '1fr' : 'repeat(3, 1fr)', gap: '14px' }}>
            {['breakfast', 'lunch', 'dinner'].map(type => {
              const meal = day.meals[type];
              if (!meal) return null;
              const lb = { breakfast: '🌅 Breakfast', lunch: '☀️ Lunch', dinner: '🌙 Dinner' }[type];
              return (
                <div key={type} style={{
                  background: '#fff', borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                  overflow: 'hidden', transition: 'box-shadow .15s', cursor: 'pointer'
                }}
                  onClick={() => onItemClick && onItemClick(meal, 'meal')}
                  onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04)'}
                  onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'}
                >
                  <div style={{ width: '100%', height: sm ? '100px' : '130px', overflow: 'hidden', background: '#f5f3ef' }}>
                    <img src={meal.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={e => { e.target.style.display = 'none'; }} />
                  </div>
                  <div style={{ padding: '12px 14px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '6px' }}>
                      {lb}: {getDisplayName(meal, lang)}
                      <RedNoteLink name={meal.name_local || meal.name_base} />
                    </div>
                    {meal.name_en && <div style={{ fontSize: '12px', color: '#9b9a97', marginBottom: '6px' }}>{meal.name_en}</div>}
                    <div style={{ fontSize: '12px', color: '#6b6b6b', lineHeight: 1.7 }}>
                      {meal.time && <div><span style={{ color: '#9b9a97' }}>Time</span> {meal.time.start} – {meal.time.end}</div>}
                      {meal.cost > 0 && <div><span style={{ color: '#9b9a97' }}>Cost</span> {fmtCost(meal.cost)}</div>}
                      {getDisplayField(meal, 'cuisine', lang) && <div><span style={{ color: '#9b9a97' }}>Cuisine</span> {getDisplayField(meal, 'cuisine', lang)}</div>}
                      {(meal.location || meal.location_base || meal.location_local) && <div><span style={{ color: '#9b9a97' }}>Location</span> <MapLink item={meal} lang={lang} mapProvider={mapProvider} /></div>}
                      {getDisplayField(meal, 'signature_dishes', lang) && !sm && <div><span style={{ color: '#9b9a97' }}>Signature</span> {getDisplayField(meal, 'signature_dishes', lang)}</div>}
                    </div>
                    <ExpandableNotes text={meal.notes} textLocal={meal.notes_local} lang={lang} />
                    <LinksRow links={meal.links} compact={sm} />
                  </div>
                </div>
              );
            })}
          </div>
        </Section>

        {/* Attractions + Right column */}
        <div style={{ display: 'grid', gridTemplateColumns: sm ? '1fr' : '1fr 1fr', gap: '24px' }}>
          {/* Attractions */}
          <Section title="Attractions" icon="📍">
            {day.attractions.map((attr, i) => (
              <div key={i} style={{
                background: '#fff', borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                overflow: 'hidden', marginBottom: '14px', transition: 'box-shadow .15s', cursor: 'pointer'
              }}
                onClick={() => onItemClick && onItemClick(attr, 'attraction')}
                onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'}
              >
                {sm ? (
                  <>
                    <div style={{ height: '110px', overflow: 'hidden', background: '#eef4f9' }}>
                      <img src={attr.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                    <div style={{ padding: '12px 14px' }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '4px' }}>
                        {getDisplayName(attr, lang)}
                        <RedNoteLink name={attr.name_local || attr.name_base} />
                        {attr.optional && <span style={{ fontSize: '11px', padding: '2px 6px', background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', color: '#9b9a97', marginLeft: '6px', fontWeight: '600', verticalAlign: 'middle' }}>Optional</span>}
                      </div>
                      {attr.time && <PropLine label="Time" value={`${attr.time.start} – ${attr.time.end}`} />}
                      {attr.cost > 0 && <PropLine label="Cost" value={<>{fmtCost(attr.cost)}</>} />}
                      <PropLine label="Type" value={getDisplayField(attr, 'type', lang)} />
                      {(attr.location || attr.location_base || attr.location_local) && <PropLine label="Location" value={<MapLink item={attr} lang={lang} mapProvider={mapProvider} />} />}
                      <ExpandableNotes text={attr.notes || attr.why_worth_visiting} textLocal={attr.notes_local || attr.why_worth_visiting_local} lang={lang} />
                      <LinksRow links={attr.links} compact />
                    </div>
                  </>
                ) : (
                  <div style={{ display: 'flex' }}>
                    <div style={{ width: '140px', flexShrink: 0, overflow: 'hidden', background: '#eef4f9' }}>
                      <img src={attr.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', minHeight: '160px' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                    <div style={{ padding: '14px 16px', flex: 1, lineHeight: 1.7 }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '2px' }}>
                        {getDisplayName(attr, lang)}
                        <RedNoteLink name={attr.name_local || attr.name_base} />
                        {attr.optional && <span style={{ fontSize: '11px', padding: '2px 6px', background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', color: '#9b9a97', marginLeft: '6px', fontWeight: '600', verticalAlign: 'middle' }}>Optional</span>}
                      </div>
                      {attr.time && <PropLine label="Time" value={`${attr.time.start} – ${attr.time.end}`} />}
                      {attr.cost > 0 && <PropLine label="Cost" value={<>{fmtCost(attr.cost)}</>} />}
                      <PropLine label="Type" value={getDisplayField(attr, 'type', lang)} />
                      {(attr.location || attr.location_base || attr.location_local) && <PropLine label="Location" value={<MapLink item={attr} lang={lang} mapProvider={mapProvider} />} />}
                      {attr.highlights && attr.highlights.length > 0 && (
                        <div style={{ marginTop: '6px' }}>
                          <span style={{ fontSize: '12px', color: '#9b9a97' }}>Highlights</span>
                          <ul style={{ margin: '2px 0 0', paddingLeft: '16px', fontSize: '12px', color: '#37352f', lineHeight: 1.7 }}>
                            {attr.highlights.map((h, j) => <li key={j}>{h}</li>)}
                          </ul>
                        </div>
                      )}
                      <ExpandableNotes text={attr.notes || attr.why_worth_visiting} textLocal={attr.notes_local || attr.why_worth_visiting_local} lang={lang} />
                      <LinksRow links={attr.links} />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </Section>

          {/* Right column */}
          <div>
            {day.entertainment?.length > 0 && (
              <Section title="Entertainment" icon="🎭">
                {day.entertainment.map((ent, i) => (
                  <div key={i} style={{
                    background: '#fff', borderRadius: '8px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                    overflow: 'hidden', marginBottom: '10px', cursor: 'pointer'
                  }}
                    onClick={() => onItemClick && onItemClick(ent, 'entertainment')}
                  >
                    {ent.image && (
                      <div style={{ width: '100%', height: sm ? '100px' : '120px', overflow: 'hidden', background: '#f5f3ef' }}>
                        <img src={ent.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={e => { e.target.style.display = 'none'; }} />
                      </div>
                    )}
                    <div style={{ padding: '14px 16px' }}>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>
                        {getDisplayName(ent, lang)}
                        <RedNoteLink name={ent.name_local || ent.name_base} />
                      </div>
                      {ent.time && <PropLine label="Time" value={`${ent.time.start} – ${ent.time.end}`} />}
                      {ent.cost > 0 && <PropLine label="Cost" value={fmtCost(ent.cost)} />}
                      <PropLine label="Type" value={getDisplayField(ent, 'type', lang)} />
                      {(ent.location || ent.location_base || ent.location_local) && <PropLine label="Location" value={<MapLink item={ent} lang={lang} mapProvider={mapProvider} />} />}
                      {ent.duration && <PropLine label="Duration" value={ent.duration} />}
                      {(lang === 'local' && ent.note_local ? ent.note_local : ent.note) && (
                        <div style={{ marginTop: '8px', padding: '8px 12px', background: '#fffdf5', borderRadius: '5px', border: '1px solid #f5ecd7', fontSize: '12px', color: '#9a6700' }}>
                          💡 {lang === 'local' && ent.note_local ? ent.note_local : ent.note}
                        </div>
                      )}
                      <ExpandableNotes text={ent.notes} textLocal={ent.notes_local} lang={lang} />
                      <LinksRow links={ent.links} compact={sm} />
                    </div>
                  </div>
                ))}
              </Section>
            )}

            {day.accommodation && (
              <Section title="Accommodation" icon="🏨">
                <div style={{
                  background: '#fff', borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                  overflow: 'hidden', cursor: 'pointer'
                }}
                  onClick={() => onItemClick && onItemClick(day.accommodation, 'accommodation')}
                >
                  {day.accommodation.image && (
                    <div style={{ width: '100%', height: sm ? '120px' : '160px', overflow: 'hidden', background: '#f5f3ef' }}>
                      <img src={day.accommodation.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        onError={e => { e.target.style.display = 'none'; }} />
                    </div>
                  )}
                  <div style={{ padding: '14px 16px' }}>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '4px' }}>
                      {getDisplayName(day.accommodation, lang)}
                      <RedNoteLink name={day.accommodation.name_local || day.accommodation.name_base} />
                    </div>
                    {day.accommodation.cost > 0 && <PropLine label="Cost" value={fmtCost(day.accommodation.cost)} />}
                    <PropLine label="Type" value={getDisplayField(day.accommodation, 'type', lang)} />
                    {day.accommodation.stars > 0 && <PropLine label="Stars" value={<span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(day.accommodation.stars)}</span>} />}
                    {day.accommodation.check_in && <PropLine label="Check-in" value={day.accommodation.check_in} />}
                    {day.accommodation.check_out && <PropLine label="Check-out" value={day.accommodation.check_out} />}
                    <PropLine label="Location" value={<MapLink item={day.accommodation} lang={lang} mapProvider={mapProvider} />} />
                    <ExpandableNotes text={day.accommodation.notes} textLocal={day.accommodation.notes_local} lang={lang} />
                    <LinksRow links={day.accommodation.links} compact={sm} />
                  </div>
                </div>
              </Section>
            )}

            {day.transportation && (
              <Section title="Transportation" icon={day.transportation.icon}>
                <div style={{
                  background: '#fff', borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                  overflow: 'hidden', cursor: 'pointer'
                }}
                  onClick={() => onItemClick && onItemClick(day.transportation, 'transportation')}
                >
                  <div style={{ padding: '14px 16px' }}>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {day.transportation.icon}
                      {' '}
                      {lang === 'local' && day.transportation.from_local ? day.transportation.from_local : day.transportation.from}
                      {' → '}
                      {lang === 'local' && day.transportation.to_local ? day.transportation.to_local : day.transportation.to}
                    </div>
                    <PropLine label={"Time"} value={`${day.transportation.departure_time} – ${day.transportation.arrival_time}`} />
                    <PropLine label={"Type"} value={day.transportation.transport_type} />
                    {(day.transportation.cost > 0 || day.transportation.cost_type === 'prepaid') && (
                      <PropLine label={"Cost"} value={fmtCost(day.transportation.cost, day.transportation.cost_type)} />
                    )}
                    <PropLine label={"Route"} value={`${lang === 'local' && day.transportation.departure_point_local ? day.transportation.departure_point_local : day.transportation.departure_point} → ${lang === 'local' && day.transportation.arrival_point_local ? day.transportation.arrival_point_local : day.transportation.arrival_point}`} />
                  </div>
                </div>
              </Section>
            )}

            <Section title={lang === 'local' ? '预算' : 'Budget'} icon="💰">
              <div style={{
                background: '#fff', borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                padding: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: sm ? 'center' : 'center', gap: '20px', flexDirection: sm ? 'column' : 'row' }}>
                  <Donut budget={day.budget} size={sm ? 72 : 88} onBudgetClick={onBudgetClick} day={day} />
                  <div style={{ fontSize: '13px', color: '#6b6b6b', lineHeight: 2, flex: 1, width: '100%' }}>
                    {[
                      { k: 'meals', l: lang === 'local' ? '餐饮' : 'Meals', c: '#f0b429' },
                      { k: 'attractions', l: lang === 'local' ? '景点' : 'Attractions', c: '#4a90d9' },
                      { k: 'entertainment', l: lang === 'local' ? '娱乐' : 'Entertainment', c: '#9b6dd7' },
                      { k: 'accommodation', l: lang === 'local' ? '住宿' : 'Accommodation', c: '#45b26b' },
                      { k: 'shopping', l: lang === 'local' ? '购物' : 'Shopping', c: '#e07c5a' },
                      { k: 'transportation', l: lang === 'local' ? '交通' : 'Transport', c: '#0ea5e9' }
                    ].filter(r => day.budget[r.k] > 0).map(r => (
                      <div key={r.k} style={{
                        display: 'flex', alignItems: 'center', gap: '8px',
                        cursor: 'pointer', padding: '4px 6px', margin: '0 -6px',
                        borderRadius: '4px', transition: 'background .12s'
                      }}
                        onClick={() => onBudgetClick && onBudgetClick(r.k, day)}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(55,53,47,0.04)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <span style={{ width: '10px', height: '10px', borderRadius: '3px', background: r.c, flexShrink: 0 }} />
                        <span style={{ flex: 1 }}>{r.l}</span>
                        <span style={{ fontWeight: '600', color: '#37352f' }}>{fmtCost(day.budget[r.k])}</span>
                      </div>
                    ))}
                    <div style={{ borderTop: '1px solid #edece9', marginTop: '8px', paddingTop: '8px', fontWeight: '700', color: '#37352f', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{lang === 'local' ? '合计' : 'Total'}</span><span>{CURRENCY_SYMBOL}{day.budget.total.toFixed(0)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </Section>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// TIMELINE VIEW
// ============================================================
const TRAVEL_MODE_EMOJI = {
  walk: '🚶', taxi: '🚕', bus: '🚌', metro: '🚇',
  train: '🚄', flight: '✈️', car: '🚗', bike: '🚲', transit: '🔄'
};
const getTravelEmoji = (entry) => TRAVEL_MODE_EMOJI[entry?.mode] || '🚶';

const TimelineView = ({ day, bp, lang, mapProvider, onItemClick }) => {
  // Fix #6: Add z-index state for click handling of overlapping items
  const [topItemIndex, setTopItemIndex] = useState(null);
  const sm = bp === 'sm';
  const px = sm ? '16px' : bp === 'md' ? '32px' : '48px';
  const timeW = sm ? '48px' : '62px';

  const entries = [];
  const add = (item, type, label) => {
    // Only add if item has valid time with start and end
    if (item?.time?.start && item?.time?.end) {
      entries.push({ ...item, _type: type, _label: label });
    }
  };
  // Add transportation if exists (Fix Issue #8, #9: bilingual label respects lang toggle)
  if (day.transportation) {
    const tFrom = lang === 'local' && day.transportation.from_local ? day.transportation.from_local : day.transportation.from;
    const tTo = lang === 'local' && day.transportation.to_local ? day.transportation.to_local : day.transportation.to;
    add(day.transportation, 'transportation', `${tFrom} → ${tTo}`);
  }
  add(day.meals.breakfast, 'meal', 'Breakfast');
  add(day.meals.lunch, 'meal', 'Lunch');
  add(day.meals.dinner, 'meal', 'Dinner');
  day.attractions?.forEach(a => add(a, 'attraction', 'Attraction'));
  day.entertainment?.forEach(e => add(e, 'entertainment', 'Entertainment'));
  if (day.accommodation) add(day.accommodation, 'accommodation', 'Check-in');
  // Fix issue #6: Add travel segments from timeline
  day.travel_segments?.forEach(t => {
    const label = lang === 'local' && t.name_local ? t.name_local : (t.name_base || t.name || '');
    add(t, 'travel', label);
  });

  // Sort by start time
  entries.sort((a, b) => a.time.start.localeCompare(b.time.start));

  const firstH = entries.length ? parseInt(entries[0].time.start) : 8;
  const lastH = entries.length ? Math.min(parseInt(entries[entries.length - 1].time.start) + 2, 24) : 20;
  const hours = []; for (let h = firstH; h <= lastH; h++) hours.push(h);

  const hH = sm ? 68 : 80;
  const typeStyle = {
    transportation: { bg: '#f0f9ff', border: '#7dd3fc', dot: '#0ea5e9' },
    meal: { bg: '#fffdf5', border: '#ebd984', dot: '#f0b429' },
    attraction: { bg: '#f6fafd', border: '#a8cceb', dot: '#4a90d9' },
    entertainment: { bg: '#faf6fd', border: '#c9aee6', dot: '#9b6dd7' },
    accommodation: { bg: '#f5fbf6', border: '#a2d9b1', dot: '#45b26b' },
    shopping: { bg: '#fff7f5', border: '#f0b29a', dot: '#e07c5a' },
    travel: { bg: '#f8f8f8', border: '#d0d0d0', dot: '#999' }
  };

  const top = (t) => { const [h, m] = t.split(':').map(Number); return (h - firstH) * hH + (m / 60) * hH; };
  const rawHgt = (s, e) => top(e) - top(s);
  const hgt = (s, e) => Math.max(rawHgt(s, e), sm ? 56 : 64);

  // Debug: log entries count
  if (entries.length === 0) {
    console.warn('Timeline has no entries for day:', day.day, day.location);
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{
        width: '100%', height: sm ? '100px' : '160px',
        background: day.cover ? `url(${day.cover})` : '#f5f5f5',
        backgroundSize: 'cover', backgroundPosition: 'center'
      }} />

      <div style={{ padding: `0 ${px}` }}>
        <div style={{ marginTop: sm ? '-20px' : '-30px', marginBottom: '24px' }}>
          <div style={{ fontSize: sm ? '36px' : '48px', lineHeight: 1, marginBottom: '6px' }}>📍</div>
          <h2 style={{ fontSize: sm ? '22px' : '28px', fontWeight: '700', color: '#37352f', margin: 0 }}>
            Day {day.day} – {day.location}
          </h2>
        </div>

        {entries.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9b9a97' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏰</div>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>No timeline data available</div>
            <div style={{ fontSize: '13px' }}>This day has no scheduled activities with time information</div>
          </div>
        ) : (
          <div style={{ display: 'flex', position: 'relative' }}>
          <div style={{ width: timeW, flexShrink: 0 }}>
            {hours.map(h => (
              <div key={h} style={{ height: hH, fontSize: '12px', color: '#c4c4c0', fontFamily: 'ui-monospace, monospace', paddingTop: '2px' }}>
                {String(h).padStart(2, '0')}:00
              </div>
            ))}
          </div>

          <div style={{ flex: 1, position: 'relative', borderLeft: '1px dashed #e5e4e1', minWidth: 0 }}>
            {hours.map(h => <div key={h} style={{ height: hH, borderBottom: '1px solid #f5f5f3' }} />)}

            {entries.map((entry, i) => {
              const st = typeStyle[entry._type] || typeStyle.attraction;
              const t = top(entry.time.start);
              const entryH = hgt(entry.time.start, entry.time.end);
              const tooNarrow = entryH < (sm ? 32 : 40);
              const showText = !tooNarrow && entryH > (sm ? 40 : 48);
              const showSubtext = !tooNarrow && entryH > (sm ? 56 : 68);
              // Fix #6: Use dynamic z-index based on click state
              const isTop = topItemIndex === i;
              const zIdx = isTop ? 10 : 2;
              return (
                <div key={i} style={{
                  position: 'absolute', top: t, left: '10px', right: '10px',
                  height: entryH - 4,
                  background: st.bg, borderLeft: `3px ${entry.optional ? 'dashed' : 'solid'} ${st.border}`,
                  borderRadius: '6px', padding: tooNarrow ? '0 6px' : (sm ? '8px 10px' : '10px 14px'),
                  display: 'flex', gap: tooNarrow ? '0' : '10px', alignItems: tooNarrow ? 'center' : 'flex-start',
                  boxShadow: isTop ? '0 4px 12px rgba(0,0,0,0.12)' : '0 1px 3px rgba(0,0,0,0.04)',
                  zIndex: zIdx, overflow: 'hidden', transition: 'all .15s', cursor: 'pointer'
                }}
                  onClick={() => { setTopItemIndex(i); onItemClick && onItemClick(entry, entry._type); }}
                  onMouseEnter={e => { if (!isTop) e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)'; }}
                  onMouseLeave={e => { if (!isTop) e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04)'; }}
                >
                  <div style={{
                    position: 'absolute', left: '-8px', top: '50%', transform: 'translateY(-50%)',
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: st.dot, border: '2px solid #fff'
                  }} />

                  {entry.image && !sm && showText && (
                    <div style={{ width: '50px', height: '50px', borderRadius: '6px', overflow: 'hidden', flexShrink: 0 }}>
                      <img src={entry.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '11px', color: '#b4b4b4' }}>{entry.time.start} – {entry.time.end}</div>
                    {showText && (
                    <div style={{
                      fontSize: sm ? '12px' : '14px', fontWeight: '600', color: '#37352f',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
                    }}>
                      {entry._type === 'transportation' || entry._type === 'travel' ? (
                        <span>{entry._type === 'transportation' ? entry.icon : getTravelEmoji(entry)} {entry._label}{entry.duration ? ` (${entry.duration})` : ''}</span>
                      ) : (
                        <span>{entry._label}: {getDisplayName(entry, lang)}</span>
                      )}
                      {entry.optional && (
                        <span style={{ fontSize: '11px', padding: '2px 6px', background: '#f5f5f3', border: '1px solid #e0e0e0', borderRadius: '4px', color: '#9b9a97', marginLeft: '6px', fontWeight: '600', verticalAlign: 'middle' }}>Optional</span>
                      )}
                    </div>
                    )}
                    {showSubtext && (entry._type === 'transportation' ? (
                      <div style={{ fontSize: '11px', color: '#9b9a97', marginTop: '2px', lineHeight: 1.5 }}>
                        <div>{lang === 'local' && entry.departure_point_local ? entry.departure_point_local : entry.departure_point} → {lang === 'local' && entry.arrival_point_local ? entry.arrival_point_local : entry.arrival_point}</div>
                        {entry.route_number && entry.route_number !== 'VERIFIED' && (
                          <div>{entry.transport_type} {entry.route_number}</div>
                        )}
                        {entry.booking_status && (
                          <span style={{
                            display: 'inline-block',
                            marginTop: '2px',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            fontSize: '10px',
                            fontWeight: '600',
                            background: entry.booking_status.includes('URGENT') ? '#fff4e6' :
                                       entry.booking_status.includes('VERIFIED') ? '#e9f5ec' : '#edf2fc',
                            color: entry.booking_status.includes('URGENT') ? '#d97706' :
                                  entry.booking_status.includes('VERIFIED') ? '#1a7a32' : '#2b63b5'
                          }}>
                            {entry.booking_status}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#9b9a97', flexWrap: 'wrap', marginTop: '2px' }}>
                        {entry.recommended_duration && <span>⏱ {entry.recommended_duration}</span>}
                        {entry.cost !== undefined && Number(entry.cost) > 0 && (
                          <span style={{
                            padding: '1px 6px', borderRadius: '3px', fontWeight: '600',
                            background: '#f5f5f3',
                            color: '#37352f'
                          }}>
                            {fmtCost(entry.cost)}
                          </span>
                        )}
                        {entry.stars && <span style={{ color: '#e9b200' }}>{'★'.repeat(entry.stars)}</span>}
                      </div>
                    ))}
                    {showSubtext && entry._type !== 'transportation' && <LinksRow links={entry.links} compact={sm} />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

// ============================================================
// APP
// ============================================================
function NotionTravelApp() {
  const [selTrip, setSelTrip] = useState(0);
  const [selDay, setSelDay] = useState(0);
  const [view, setView] = useState('kanban');
  const [sbOpen, setSbOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedBudgetCat, setSelectedBudgetCat] = useState(null);
  // Root cause fix (commit 8f2bddd): Add language toggle for bilingual POI display
  const [lang, setLang] = useState('local');  // 'local' or 'base'
  const [mapProvider, setMapProvider] = useState('gaode');  // 'gaode' or 'google'
  const bp = useBreakpoint();
  const sm = bp === 'sm';

  const trip = PLAN_DATA.trips[selTrip];
  const day = trip?.days?.[selDay];

  const handleItemClick = (item, type) => {
    setSelectedBudgetCat(null);
    setSelectedItem({ item, type });
  };

  const handleBudgetClick = (category, dayData) => {
    setSelectedItem(null);

    let items = [];
    let total = 0;

    if (category === 'meals') {
      ['breakfast', 'lunch', 'dinner'].forEach(mealType => {
        if (dayData.meals[mealType]) {
          items.push(dayData.meals[mealType]);
          total += dayData.meals[mealType].cost || 0;
        }
      });
    } else if (category === 'attractions') {
      items = dayData.attractions || [];
      total = dayData.budget.attractions || 0;
    } else if (category === 'entertainment') {
      items = dayData.entertainment || [];
      total = dayData.budget.entertainment || 0;
    } else if (category === 'accommodation') {
      items = dayData.accommodation ? [dayData.accommodation] : [];
      total = dayData.budget.accommodation || 0;
    } else if (category === 'shopping') {
      items = dayData.shopping || [];
      total = dayData.budget.shopping || 0;
    } else if (category === 'transportation') {
      items = dayData.transportation ? [dayData.transportation] : [];
      total = dayData.budget.transportation || 0;
    }

    setSelectedBudgetCat({ category, items, total });
  };

  return (
    <div style={{
      display: 'flex',
      fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, 'Noto Sans SC', sans-serif",
      background: '#ffffff', minHeight: '100vh', color: '#37352f'
    }}>
      <Sidebar
        trips={PLAN_DATA.trips} selTrip={selTrip} selDay={selDay}
        onSelect={(ti, di) => { setSelTrip(ti); setSelDay(di); }}
        isOpen={sbOpen} onClose={() => setSbOpen(false)} bp={bp}
      />

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          borderBottom: '1px solid #f0efed',
          padding: `0 ${sm ? '12px' : '20px'}`,
          display: 'flex', alignItems: 'center', flexWrap: 'wrap',
          position: 'sticky', top: 0, background: 'rgba(255,255,255,0.97)',
          backdropFilter: 'blur(8px)', zIndex: 50, gap: '2px'
        }}>
          {sm && (
            <button onClick={() => setSbOpen(true)} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '17px', padding: '10px 6px 10px 2px', color: '#37352f'
            }}>☰</button>
          )}
          {['kanban', 'timeline'].map(m => (
            <button key={m} onClick={() => setView(m)} style={{
              padding: sm ? '10px 8px' : '11px 16px', background: 'none', border: 'none',
              borderBottom: view === m ? '2px solid #37352f' : '2px solid transparent',
              fontSize: '14px', fontWeight: view === m ? '600' : '400',
              color: view === m ? '#37352f' : '#b4b4b4',
              cursor: 'pointer', transition: 'all .12s', whiteSpace: 'nowrap'
            }}>
              {m === 'kanban' ? 'Kanban View' : 'Timeline View'}
            </button>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: sm ? '6px' : '12px', ...(sm ? { width: '100%', justifyContent: 'flex-end', paddingBottom: '6px' } : {}) }}>
            {/* Map provider toggle */}
            <div style={{ display: 'flex', gap: '2px', background: '#f5f5f3', borderRadius: '6px', padding: '2px', border: '1px solid #e0e0e0' }}>
              <button onClick={() => setMapProvider('gaode')} style={{
                padding: sm ? '5px 6px' : '6px 10px',
                background: mapProvider === 'gaode' ? '#e6f3ff' : 'transparent',
                border: mapProvider === 'gaode' ? '1px solid #0085fe' : '1px solid transparent',
                borderRadius: '4px',
                fontSize: '12px', fontWeight: mapProvider === 'gaode' ? '600' : '400',
                color: mapProvider === 'gaode' ? '#0085fe' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s',
                display: 'flex', alignItems: 'center', gap: '3px'
              }}>
                <GaodeLogo size={12} />
                {sm ? '高德' : '高德地图'}
              </button>
              <button onClick={() => setMapProvider('google')} style={{
                padding: sm ? '5px 6px' : '6px 10px',
                background: mapProvider === 'google' ? '#e8f0fe' : 'transparent',
                border: mapProvider === 'google' ? '1px solid #4285F4' : '1px solid transparent',
                borderRadius: '4px',
                fontSize: '12px', fontWeight: mapProvider === 'google' ? '600' : '400',
                color: mapProvider === 'google' ? '#4285F4' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s',
                display: 'flex', alignItems: 'center', gap: '3px'
              }}>
                <GoogleMapsLogo size={12} />
                Google
              </button>
            </div>
            {/* Language toggle */}
            <div style={{ display: 'flex', gap: '4px' }}>
              <button onClick={() => setLang('local')} style={{
                padding: sm ? '8px 10px' : '9px 14px',
                background: lang === 'local' ? '#e9f5ec' : '#f5f5f3',
                border: `1px solid ${lang === 'local' ? '#45b26b' : '#e0e0e0'}`,
                borderRadius: '6px',
                fontSize: '13px', fontWeight: lang === 'local' ? '600' : '400',
                color: lang === 'local' ? '#45b26b' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s'
              }}>
                {PLAN_DATA.trip_summary.local_display || 'Local'}
              </button>
              <button onClick={() => setLang('base')} style={{
                padding: sm ? '8px 10px' : '9px 14px',
                background: lang === 'base' ? '#e9f5ec' : '#f5f5f3',
                border: `1px solid ${lang === 'base' ? '#45b26b' : '#e0e0e0'}`,
                borderRadius: '6px',
                fontSize: '13px', fontWeight: lang === 'base' ? '600' : '400',
                color: lang === 'base' ? '#45b26b' : '#6b6b6b',
                cursor: 'pointer', transition: 'all .12s'
              }}>
                {PLAN_DATA.trip_summary.base_display || 'EN'}
              </button>
            </div>
          </div>
        </div>

        {day ? (
          view === 'kanban'
            ? <KanbanView
                day={day}
                tripSummary={PLAN_DATA.trip_summary}
                showSummary={selDay === 0 && selTrip === 0}
                bp={bp}
                lang={lang}
                mapProvider={mapProvider}
                onItemClick={handleItemClick}
                onBudgetClick={handleBudgetClick}
              />
            : <TimelineView
                day={day}
                bp={bp}
                lang={lang}
                mapProvider={mapProvider}
                onItemClick={handleItemClick}
              />
        ) : (
          <div style={{ padding: `60px ${sm ? '16px' : '48px'}`, color: '#c4c4c0' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>🗺️</div>
            <div style={{ fontWeight: '500', fontSize: '16px', color: '#9b9a97' }}>{trip?.name}</div>
            <div style={{ marginTop: '4px' }}>Itinerary coming soon...</div>
          </div>
        )}

        {selectedItem && (
          <ItemDetailSidebar
            item={selectedItem.item}
            type={selectedItem.type}
            onClose={() => setSelectedItem(null)}
            bp={bp}
            lang={lang}
            mapProvider={mapProvider}
          />
        )}

        {selectedBudgetCat && (
          <BudgetDetailSidebar
            category={selectedBudgetCat.category}
            items={selectedBudgetCat.items}
            total={selectedBudgetCat.total}
            onClose={() => setSelectedBudgetCat(null)}
            bp={bp}
            lang={lang}
          />
        )}
      </div>
    </div>
  );
}
"""

    def generate(self) -> str:
        """Main generation method"""
        print(f"Generating Notion-style React HTML for plan: {self.plan_id}")
        print(f"Data directory: {self.data_dir}")

        # Generate HTML
        html = self.generate_html()

        # Write output
        output_dir = self.base_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"travel-plan-{self.plan_id}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ Generated: {output_file}")
        print(f"   File size: {len(html) / 1024:.1f} KB")

        return str(output_file)


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-notion-react.py <plan-id>")
        print("Example: python generate-notion-react.py beijing-exchange-bucket-list-20260202-232405")
        sys.exit(1)

    plan_id = sys.argv[1]

    try:
        generator = InteractiveHTMLGenerator(plan_id)
        output_file = generator.generate()

        print("\n" + "="*60)
        print("✅ Notion React HTML generation complete!")
        print(f"📄 Output: {output_file}")
        print(f"🌐 Open in browser: file://{output_file}")
        print("="*60)

    except Exception as e:
        print(f"❌ Error generating Notion React HTML: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
