#!/usr/bin/env python3
"""
Interactive React Travel Plan Generator
Converts skeleton.json + agent outputs → standalone React HTML application
Generates single-file HTML with embedded React components
"""

import json
import re
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "lib"))
import render_day_data as _rd  # noqa: E402
import render_html_builders as _bld  # noqa: E402


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
        self.cafe = self._load_json("cafe.json")
        self.transportation = self._load_json("transportation.json")
        self.timeline = self._load_json("timeline.json")
        self.budget = self._load_json("budget.json")

        # Load requirements-skeleton for ui_labels (toggle display text per trip)
        self.requirements = self._load_json("requirements-skeleton.json")

        # Load image fetcher for real photos
        self.images_cache = self._load_json("images.json")

        # Load currency config for display
        self._exchange_rates = self._load_exchange_rates()
        self._default_currency, self._display_symbol = self._load_display_currency()
        self._type_display_map = self._load_validation_config()

    def _load_exchange_rates(self) -> dict:
        """Load exchange rates from config, with real-time override for trip currency."""
        config_path = self.base_dir / "config" / "currency-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        rates = dict(config.get("exchange_rates", {}))
        # Try real-time rate for the trip's currency_local
        trip_currency = self.requirements.get("trip_summary", {}).get("currency_local", "CNY")
        fetch_script = self.base_dir / "scripts" / "utils" / "fetch-exchange-rate.sh"
        if fetch_script.exists():
            try:
                result = subprocess.run(
                    [str(fetch_script), config.get("default_currency", "EUR"), trip_currency],
                    capture_output=True, text=True, check=True, timeout=10
                )
                rate = float(result.stdout.strip())
                print(f"Exchange rate (real-time): 1 {config.get('default_currency', 'EUR')} = {rate} {trip_currency}", file=sys.stderr)
                rates[trip_currency] = rate
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
                print(f"Warning: Real-time exchange rate fetch failed: {e}, using config fallback", file=sys.stderr)
        if not rates:
            raise RuntimeError("Exchange rate unavailable - cannot generate accurate budget display")
        print(f"Exchange rates loaded: {rates}", file=sys.stderr)
        return rates

    def _load_display_currency(self) -> tuple:
        """Load display currency from config/currency-config.json. Raises if config missing."""
        config_path = self.base_dir / "config" / "currency-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        currency = config["default_currency"]
        symbol = config["currency_symbol_map"][currency]
        print(f"Display currency: {currency} ({symbol})", file=sys.stderr)
        return currency, symbol



    def _load_validation_config(self) -> dict:
        """Load display maps from config. Raises if config missing."""
        type_path = self.base_dir / "config" / "type-display-map.json"

        with open(type_path, 'r') as f:
            type_cfg = json.load(f)
        return {**type_cfg.get("trip_types", {}), **type_cfg.get("poi_types", {})}

    def _to_display_currency(self, amount: float, currency_local: str = "CNY") -> float:
        """Convert amount from local currency to display currency (EUR) via division."""
        if amount == 0:
            return 0
        if currency_local == self._default_currency:
            return amount
        rate = self._exchange_rates.get(currency_local)
        if rate and rate > 0:
            return amount / rate
        return amount

    # Default UI labels (English only — local translations come from data)
    # These serve as fallback keys when requirements-skeleton doesn't provide a label.
    DEFAULT_UI_LABELS_BASE = {
        "time": "Time", "cost": "Cost", "type": "Type", "stars": "Stars",
        "checkin": "Check-in", "checkout": "Check-out",
        "location": "Location", "cuisine": "Cuisine", "signature": "Signature Dishes",
        "opening_hours": "Opening Hours", "duration": "Duration", "route": "Route",
        "route_number": "Route Number", "company": "Company", "status": "Status",
        "amenities": "Amenities", "links": "Links",
        "user_plans": "User Plans", "meals": "Meals", "attractions": "Attractions",
        "entertainment": "Entertainment", "accommodation": "Accommodation",
        "transportation": "Transportation", "shopping": "Shopping", "cafe": "Cafe", "budget": "Budget", "alternatives": "Also try",
        "transport": "Transport",
        "trip_type": "Trip Type", "base_location": "Base Location",
        "period": "Period", "travelers": "Travelers", "budget_trip": "Budget / Trip",
        "breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner",
        "cat_breakfast": "Breakfast", "cat_brunch": "Brunch", "cat_lunch": "Lunch", "cat_dinner": "Dinner",
        "cat_attraction": "Attraction", "cat_entertainment": "Entertainment",
        "cat_shopping": "Shopping", "cat_cafe": "Cafe", "cat_checkin": "Check-in",
        "kanban_view": "Kanban View", "timeline_view": "Timeline View",
        "prepaid": "Prepaid", "free": "Free", "optional": "Optional",
        "show_less": "Show less", "show_more": "Show more",
        "no_items": "No items in this category",
        "no_timeline": "No timeline data available",
        "no_timeline_sub": "This day has no scheduled activities with time information",
        "coming_soon": "Itinerary coming soon...",
        "day_prefix": "Day", "day_format": "Day {n}",
        "days_count": "{n} days", "days_count_1": "1 day", "total": "Total",
        "google_maps": "Google Maps", "booking_link": "Booking", "link": "Link",
        "open_google": "Open in Google Maps", "search_rednote": "Search on Xiaohongshu",
        "urgent": "URGENT", "required": "REQUIRED", "verified": "VERIFIED",
        "recommended": "RECOMMENDED",
        "high_speed_train": "High-speed Train", "flight": "Flight",
        "booking_required": "Booking Required",
    }

    def _extract_local_city(self, location_field: str, city_name: str) -> str:
        """Extract Chinese city name from location field data only.

        No hardcoded lookup table — if the data doesn't contain Chinese,
        return empty string so JSX falls back to base display.
        """
        import re
        if location_field:
            chinese = re.findall(r'[\u4e00-\u9fff]+', location_field)
            if chinese:
                return chinese[0]  # First Chinese word group (usually city name)
        return ""

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

    def _extract_transport_cost(self, loc_change: dict) -> tuple:
        """Extract cost and currency from transportation data.

        Returns (cost, currency_local) tuple.
        Priority: cost_cny (legacy) > cost + currency_local
        """
        # Legacy: cost_cny field
        route_details = loc_change.get("route_details", {})
        verified = route_details.get("verified_train") or route_details.get("verified_flight") or {}
        if verified.get("cost_cny"):
            return float(verified["cost_cny"]), "CNY"
        if loc_change.get("cost_cny"):
            return float(loc_change["cost_cny"]), "CNY"
        # Standard: cost + currency_local
        cost = float(loc_change.get("cost", 0))
        currency = loc_change.get("currency_local", "CNY")
        return cost, currency

    def _is_home_location(self, item: dict) -> bool:
        """Check if item is a home/family location via schema field is_home."""
        return item.get("is_home") is True

    def _format_trip_type(self, trip_type: str) -> str:
        """Convert trip_type code to natural language (Fix #1, #3)
        Root cause: commit 52d3528 - no formatting for trip types
        """
        return self._type_display_map.get(trip_type, trip_type.replace("_", " ").title())

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

        return self._type_display_map.get(type_code, type_code.replace("_", " ").title())

    def _get_cover_image(self, location: str, index: int = 0) -> str:
        """Get cover image URL from cache. Fix #1 (commit 123f8df). Fix dev-20260406-010004."""
        # Strip parenthetical suffix "City (District)" -> "City" before any lookup
        location = location.split("(")[0].strip()
        if not location:
            return ""
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

    def _parse_shopping_brands(self, notes_base: str, notes_local: str = "") -> list:
        """Delegate to render_html_builders.parse_shopping_brands."""
        return _bld.parse_shopping_brands(notes_base, notes_local)

    def _match_gaode_id_in_timeline(self, gaode_id, day_timeline):
        """Bug-2 Tier-0: exact gaode_id match in timeline entries."""
        if not gaode_id or not day_timeline:
            return None
        for tl_val in day_timeline.values():
            if not isinstance(tl_val, dict):
                continue
            if tl_val.get("gaode_id") == gaode_id and tl_val.get("start_time"):
                return {"start": tl_val["start_time"], "end": tl_val.get("end_time", "")}
        return None

    def _get_timeline_time(self, name_base: str, name_local: str, day_timeline: dict,
                           gaode_id: str = "") -> dict:
        """Bug-2: Tier-0 gaode_id fast-path; falls back to name tiers."""
        if not day_timeline:
            return None
        t0 = self._match_gaode_id_in_timeline(gaode_id, day_timeline)
        if t0: return t0
        for item_name in [name_base, name_local]:
            if not item_name:
                continue
            if item_name in day_timeline:
                entry = day_timeline[item_name]
                if isinstance(entry, dict) and entry.get("start_time"):
                    return {"start": entry["start_time"], "end": entry.get("end_time", "")}
        for item_name in [name_base, name_local]:
            if not item_name:
                continue
            item_base = item_name.split("(")[0].strip().split("（")[0].strip()
            for tl_key, tl_val in day_timeline.items():
                if not isinstance(tl_val, dict) or tl_val.get("transit"):
                    continue
                tl_base = tl_key.split("(")[0].strip().split("（")[0].strip()
                if item_base.lower() == tl_base.lower():
                    if tl_val.get("start_time"):
                        return {"start": tl_val["start_time"], "end": tl_val.get("end_time", "")}
        for item_name in [name_base, name_local]:
            if not item_name:
                continue
            item_base = item_name.split("(")[0].strip().lower()
            for tl_key, tl_val in day_timeline.items():
                if not isinstance(tl_val, dict) or tl_val.get("transit"):
                    continue
                tl_base = tl_key.split("(")[0].strip().lower()
                if item_base in tl_key.lower() or tl_base in item_name.lower():
                    if tl_val.get("start_time"):
                        return {"start": tl_val["start_time"], "end": tl_val.get("end_time", "")}
        return None

    def _get_meal_time_from_timeline(self, meal_type: str, day_timeline: dict) -> dict:
        """Look up meal time from timeline using meal_ref field.
        Returns {"start": "HH:MM", "end": "HH:MM"} or None.
        """
        if not day_timeline:
            return None
        for tl_val in day_timeline.values():
            if isinstance(tl_val, dict) and tl_val.get("meal_ref") == meal_type:
                if tl_val.get("start_time"):
                    return {"start": tl_val["start_time"], "end": tl_val.get("end_time", "")}
        return None

    def _get_day_timeline(self, day_num: int) -> dict:
        """Get the timeline dict for a specific day number."""
        if not self.timeline or "days" not in self.timeline:
            return {}
        for day in self.timeline["days"]:
            if day.get("day") == day_num:
                return day.get("timeline", {})
        return {}

    def _intra_icon(self, route):
        rt = (route.get("type_base") or "").lower()
        rtl = route.get("type_local") or ""
        if "flight" in rt: return "✈️"
        if "train" in rt or "hsr" in rt or "高铁" in rtl: return "🚄"
        if "chartered" in rt or "专车" in rtl: return "🚗"
        if "taxi" in rt: return "🚕"
        if "metro" in rt or "subway" in rt or "地铁" in rtl: return "🚇"
        return route.get("icon", "🚌")

    def _intra_pax_label(self, pax):
        if not isinstance(pax, list) or not pax: return ""
        sj = any("JADE" in str(p).upper() for p in pax)
        sm = any(("MATHILDE" in str(p).upper() or "MATILDE" in str(p).upper()) for p in pax)
        if sj and not sm: return "仅 Jade"
        if sm and not sj: return "仅 Matilde"
        if sj and sm: return "两人同乘"
        return ""

    def _build_intra_card(self, r):
        n_b = r.get("name_base", ""); n_l = r.get("name_local", "")
        booking = r.get("booking_status", "")
        rcost = self._to_display_currency(r.get("cost", 0), r.get("currency_local", "CNY"))
        org = r.get("origin"); dst = r.get("destination")
        from_b = r.get("from_base", "") or (org.get("name", "") if isinstance(org, dict) else "")
        to_b = r.get("to_base", "") or (dst.get("name", "") if isinstance(dst, dict) else "")
        return {
            "name_base": n_b, "name_local": n_l,
            "from_base": from_b, "to_base": to_b,
            "from_local": r.get("from_local", ""), "to_local": r.get("to_local", ""),
            "departure_point_base": r.get("departure_point_base", "") or from_b,
            "departure_point_local": r.get("departure_point_local", "") or r.get("from_local", ""),
            "arrival_point_base": r.get("arrival_point_base", "") or to_b,
            "arrival_point_local": r.get("arrival_point_local", "") or r.get("to_local", ""),
            "type_base": r.get("type_base", ""), "type_local": r.get("type_local", ""),
            "icon": self._intra_icon(r),
            "route_number": r.get("route_number", "") or r.get("vehicle_id", ""),
            "vehicle_id": r.get("vehicle_id", ""),
            "company_base": r.get("airline_base", "") or r.get("company_base", ""),
            "company_local": r.get("airline_local", "") or r.get("company_local", ""),
            "cost": rcost, "cost_local": r.get("cost", 0),
            "status_base": booking,
            "status_local": r.get("status_local", "") or ("已订" if booking == "BOOKED" else ""),
            "passengers": r.get("passengers", []),
            "pax_label": self._intra_pax_label(r.get("passengers", [])),
            "notes_base": r.get("notes_base", ""), "notes_local": r.get("notes_local", ""),
            "time": {"start": r.get("start_time", "") or r.get("departure_time", "") or r.get("pickup_time", ""),
                     "end": r.get("end_time", "") or r.get("arrival_time", "")}
        }

    def _inject_intra_routes(self, merged, day_num):
        """Read schema-defined intra_city_routes from transportation.json and
        attach as cards on merged.intra_routes. Reads ONLY schema-declared
        fields (intra_city_routes is documented in transportation.schema.json)."""
        if not (self.transportation and "days" in self.transportation):
            return
        dt = next((d for d in self.transportation["days"] if d.get("day") == day_num), {})
        intra_raw = dt.get("intra_city_routes")
        if isinstance(intra_raw, dict):
            intra = list(intra_raw.values())
        elif isinstance(intra_raw, list):
            intra = intra_raw
        else:
            return
        cards = [self._build_intra_card(r) for r in intra if isinstance(r, dict)]
        if cards:
            merged["intra_routes"] = cards

    def _merge_day_data(self, day_skeleton: dict) -> dict:
        """Thin orchestrator: delegates to scripts/lib/render_day_data helpers.

        W7 refactor (spec-20260513-085358): _merge_day_data shrunk from 581
        lines to <=30 by extracting 9 helpers into render_day_data.py. Bug-1
        (meals alternatives), Bug-2 (gaode_id fast-path), Bug-3 (unscheduled
        optionals) fixes live in the helpers.
        """
        merged = _rd.build_skeleton(self, day_skeleton)
        day_num = merged["day"]
        day_timeline = self._get_day_timeline(day_num)
        _rd.merge_meals(self, merged, day_num, day_timeline)
        _rd.merge_cafe(self, merged, day_num, day_timeline)
        _rd.merge_attractions(self, merged, day_num, day_timeline)
        _rd.merge_entertainment(self, merged, day_num, day_timeline)
        _rd.merge_shopping(self, merged, day_num, day_timeline)
        _rd.merge_accommodation(self, merged, day_num, day_timeline)
        _rd.merge_transportation(self, merged, day_num)
        _rd.calculate_budget_total(merged)
        _rd.extract_unscheduled_optionals(merged)
        return merged


    def _group_days_by_location(self, days: list) -> list:
        """Group days by location to create trips"""
        if not days:
            return []

        trips = []
        current_trip = None

        for day in days:
            location_base = day.get("location_base", "Unknown")

            if current_trip is None or current_trip["name"] != location_base:
                # Start new trip
                current_trip = {
                    "name": location_base,
                    "name_local": day.get("location_local", ""),
                    "days_count": 1,
                    "cover": day.get("cover", ""),
                    "days": [day]
                }
                trips.append(current_trip)
            else:
                # Continue current trip
                current_trip["days"].append(day)
                current_trip["days_count"] = len(current_trip["days"])

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
        """Delegate to render_html_builders.generate_bucket_list_data."""
        return _bld.generate_bucket_list_data(self)

    def _generate_itinerary_data(self) -> dict:
        """Delegate to render_html_builders.generate_itinerary_data."""
        return _bld.generate_itinerary_data(self)

    def generate_html(self) -> str:
        """Delegate to render_html_builders.generate_html."""
        return _bld.generate_html(self)

    def _read_react_template(self) -> str:
        """Read React component template from scripts/lib/react_template.tpl."""
        tpl = Path(__file__).parent / "lib" / "react_template.tpl"
        return "\n" + tpl.read_text() + "\n"


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


        # Create canonical copy (without timestamp suffix) for stable URLs
        canonical_name = re.sub(r"-\d{8}-\d{6}$", "", self.plan_id)
        if canonical_name != self.plan_id:
            canonical_file = output_dir / f"travel-plan-{canonical_name}.html"
            with open(canonical_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"   Also: {canonical_file}")
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
