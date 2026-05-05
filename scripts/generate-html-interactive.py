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
        """Parse structured notes_base to extract individual brand entries.
        
        Format: [CATEGORY] BrandName Floor -- description | BrandName2 Floor -- description
        Categories separated by double newlines.
        Returns list of brand dicts or empty list if parsing fails.
        """
        import re
        if not notes_base:
            return []
        
        brands = []
        # Split by double newline to get category blocks
        blocks = re.split(r'\n\n', notes_base)
        local_blocks = re.split(r'\n\n', notes_local) if notes_local else []
        
        for block_idx, block in enumerate(blocks):
            block = block.strip()
            if not block:
                continue
            
            # Extract category from [BRACKETS] or 【BRACKETS】
            cat_match = re.match(r'\[([^\]]+)\]|【([^】]+)】', block)
            if not cat_match:
                continue  # Skip non-categorized blocks (rating text, hours, etc.)
            
            category = (cat_match.group(1) or cat_match.group(2)).strip()
            # Skip dining/restaurant categories - not shopping brands
            if any(k in category.upper() for k in ['DINING', 'RESTAURANT', '餐饮']):
                continue
            
            rest = block[cat_match.end():].strip()
            
            # Get corresponding local block
            local_block = ""
            if block_idx < len(local_blocks):
                lb = local_blocks[block_idx].strip()
                lb_cat = re.match(r'\[([^\]]+)\]|【([^】]+)】', lb)
                if lb_cat:
                    local_block = lb[lb_cat.end():].strip()
                    category_local = (lb_cat.group(1) or lb_cat.group(2)).strip()
                else:
                    category_local = category
            else:
                category_local = category
                local_block = ""
            
            # Split by | to get individual brands
            brand_entries = [b.strip() for b in rest.split('|') if b.strip()]
            local_entries = [b.strip() for b in local_block.split('|') if b.strip()] if local_block else []
            
            for brand_idx, entry in enumerate(brand_entries):
                # Parse: BrandName (Chinese) Floor -- description
                # or: BrandName Floor -- description
                parts = re.split(r'\s*(?:--|—)\s*', entry, maxsplit=1)
                name_part = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                
                # Extract floor info (like 1F, 2F, B1, 1F/2F)
                floor_match = re.search(r'([B]?\d+F(?:/[B]?\d+F)*)', name_part, re.IGNORECASE)
                floor = floor_match.group(1) if floor_match else ""
                # Remove floor from name
                brand_name = re.sub(r'\s*[B]?\d+F(?:/[B]?\d+F)*\s*', ' ', name_part, flags=re.IGNORECASE).strip()
                # Remove trailing hash codes like #111, #147A
                brand_name = re.sub(r'\s*#\w+\s*$', '', brand_name).strip()
                
                if not brand_name:
                    continue
                
                # Get local description
                desc_local = ""
                name_local = brand_name
                if brand_idx < len(local_entries):
                    local_entry = local_entries[brand_idx]
                    local_parts = re.split(r'\s*(?:--|—)\s*', local_entry, maxsplit=1)
                    local_name_part = local_parts[0].strip()
                    desc_local = local_parts[1].strip() if len(local_parts) > 1 else ""
                    # Extract local name (remove floor)
                    local_name_clean = re.sub(r'\s*[B]?\d+F(?:/[B]?\d+F)*\s*', ' ', local_name_part, flags=re.IGNORECASE).strip()
                    local_name_clean = re.sub(r'\s*#\w+\s*$', '', local_name_clean).strip()
                    if local_name_clean:
                        name_local = local_name_clean
                
                brands.append({
                    "name": brand_name,
                    "name_local": name_local,
                    "category": category,
                    "category_local": category_local if 'category_local' in dir() else category,
                    "floor": floor,
                    "description": description,
                    "description_local": desc_local,
                })
        
        return brands

    def _get_timeline_time(self, name_base: str, name_local: str, day_timeline: dict) -> dict:
        """Look up time from timeline.json for a POI by name matching.
        Returns {"start": "HH:MM", "end": "HH:MM"} or None.
        """
        if not day_timeline:
            return None
        for item_name in [name_base, name_local]:
            if not item_name:
                continue
            # Tier 1: Exact match
            if item_name in day_timeline:
                entry = day_timeline[item_name]
                if isinstance(entry, dict) and entry.get("start_time"):
                    return {"start": entry["start_time"], "end": entry.get("end_time", "")}
        # Tier 2: Base-name match (strip parentheticals)
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
        # Tier 3: Substring match
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
        """Merge skeleton day with agent data.
        Time data sourced exclusively from timeline.json (single source of truth).
        """
        day_num = day_skeleton.get("day", 1)
        date = day_skeleton.get("date", "")
        location_base = day_skeleton.get("location", "Unknown")
        location_local = day_skeleton.get("location_local", "")

        # Build timeline lookup for this day
        day_timeline = self._get_day_timeline(day_num)

        merged = {
            "day": day_num,
            "date": date,
            "location_base": location_base,
            "location_local": location_local,
            "cover": self._get_cover_image(location_base, day_num),
            "user_plans": day_skeleton.get("user_plans", []),
            "meals": {},
            "attractions": [],
            "entertainment": [],
            "accommodation": None,
            "transportation": None,
            "shopping": [],
            "cafe": [],
            "budget": {
                "meals": 0,
                "attractions": 0,
                "entertainment": 0,
                "accommodation": 0,
                "shopping": 0,
                "cafe": 0,
                "transportation": 0,
                "total": 0
            }
        }

        for meal_type in ["breakfast", "lunch", "dinner"]:
            if self.meals and "days" in self.meals:
                day_meals = next((d for d in self.meals["days"] if d.get("day") == day_num), {})
                if meal_type in day_meals:
                    # Dual-read: new format has meal_slot.primary; old format is meal_item directly
                    meal_slot = day_meals[meal_type]
                    meal = meal_slot.get("primary", meal_slot)
                    # Convert cost to display currency
                    cost = meal.get("cost", 0)
                    meal_currency = meal.get("currency_local", "CNY")
                    cost = self._to_display_currency(cost, meal_currency)

                    meal_time = self._get_meal_time_from_timeline(meal_type, day_timeline)

                    name_base = meal.get("name_base", meal_type)
                    name_local = meal.get("name_local", "")

                    merged["meals"][meal_type] = {
                        "name_base": name_base,
                        "name_local": name_local,
                        "location_base": meal.get("location_base", ""),
                        "location_local": meal.get("location_local", ""),
                        "coordinates": meal.get("coordinates", {}),
                        "cost": cost,
                        "cost_local": meal.get("cost", 0),
                        "cuisine_base": meal.get("cuisine_base", ""),
                        "cuisine_local": meal.get("cuisine_local", ""),
                        "signature_dishes_base": meal.get("signature_dishes_base", ""),
                        "signature_dishes_local": meal.get("signature_dishes_local", ""),
                        "notes_base": meal.get("notes_base", ""),
                        "notes_local": meal.get("notes_local", ""),
                        "optional": meal.get("optional", False),
                        "image": self._get_placeholder_image(
                            "meal",
                            poi_name=name_local if name_local else name_base,
                            gaode_id=meal.get("gaode_id", ""),
                            name_base=name_base,
                            name_local=name_local,
                            location_base=meal.get("location_base", ""),
                            location_local=meal.get("location_local", ""),
                            is_home=self._is_home_location(meal)
                        ),
                        "time": meal_time,
                        "links": meal.get("links", {})
                    }
                    merged["budget"]["meals"] += cost


        # Merge cafe (array-based, like entertainment)
        if self.cafe and "days" in self.cafe:
            day_cafe = next((d for d in self.cafe["days"] if d.get("day") == day_num), {})
            if "cafe" in day_cafe:
                for cafe_item in day_cafe["cafe"]:
                    cafe_name_base = cafe_item.get("name_base", "")
                    cafe_name_local = cafe_item.get("name_local", "")
                    cafe_time = self._get_timeline_time(cafe_item.get("name_base",""), cafe_item.get("name_local",""), day_timeline)

                    cost = cafe_item.get("cost", 0)
                    cafe_currency = cafe_item.get("currency_local", "CNY")
                    cost = self._to_display_currency(cost, cafe_currency)

                    merged["cafe"].append({
                        "name_base": cafe_name_base,
                        "name_local": cafe_name_local,
                        "location_base": cafe_item.get("location_base", ""),
                        "location_local": cafe_item.get("location_local", ""),
                        "coordinates": cafe_item.get("coordinates", {}),
                        "type_base": self._format_type(cafe_item.get("type_base", "")),
                        "type_local": cafe_item.get("type_local", ""),
                        "cost": cost,
                        "cost_local": cafe_item.get("cost", 0),
                        "cuisine_base": cafe_item.get("cuisine_base", ""),
                        "cuisine_local": cafe_item.get("cuisine_local", ""),
                        "signature_dishes_base": cafe_item.get("signature_dishes_base", ""),
                        "signature_dishes_local": cafe_item.get("signature_dishes_local", ""),
                        "notes_base": cafe_item.get("notes_base", ""),
                        "notes_local": cafe_item.get("notes_local", ""),
                        "optional": cafe_item.get("optional", False),
                        "image": cafe_item.get("image_url", "") or self._get_placeholder_image(
                            "cafe",
                            poi_name=cafe_name_local if cafe_name_local else cafe_name_base,
                            gaode_id=cafe_item.get("gaode_id", ""),
                            name_base=cafe_name_base,
                            name_local=cafe_name_local,
                            location_base=cafe_item.get("location_base", ""),
                            location_local=cafe_item.get("location_local", ""),
                            is_home=self._is_home_location(cafe_item)
                        ),
                        "time": cafe_time,
                        "links": cafe_item.get("links", {})
                    })
                    merged["budget"]["cafe"] += cost

        # Merge attractions
        if self.attractions and "days" in self.attractions:
            day_attrs = next((d for d in self.attractions["days"] if d.get("day") == day_num), {})
            if "attractions" in day_attrs:
                for attr in day_attrs["attractions"]:
                    attr_name_base = attr.get("name_base", "")
                    attr_name_local = attr.get("name_local", "")
                    attr_time = self._get_timeline_time(attr.get("name_base",""), attr.get("name_local",""), day_timeline)

                    # Convert cost to display currency
                    cost = attr.get("cost", 0)
                    attr_currency = attr.get("currency_local", "CNY")
                    cost = self._to_display_currency(cost, attr_currency)

                    merged["attractions"].append({
                        "name_base": attr_name_base,
                        "name_local": attr_name_local,
                        "location_base": attr.get("location_base", ""),
                        "location_local": attr.get("location_local", ""),
                        "coordinates": attr.get("coordinates", {}),
                        "type_base": self._format_type(attr.get("type_base", "")),
                        "type_local": attr.get("type_local", ""),
                        "cost": cost,
                        "cost_local": attr.get("cost", 0),
                        "opening_hours": attr.get("opening_hours", ""),
                        "optional": attr.get("optional", False),
                        "image": self._get_placeholder_image(
                            "attraction",
                            poi_name=attr_name_local if attr_name_local else attr_name_base,
                            gaode_id=attr.get("gaode_id", ""),
                            name_base=attr_name_base,
                            name_local=attr_name_local,
                            location_base=attr.get("location_base", ""),
                            location_local=attr.get("location_local", ""),
                            is_home=self._is_home_location(attr)
                        ),
                        "notes_base": attr.get("notes_base", ""),
                        "notes_local": attr.get("notes_local", ""),
                        "time": attr_time,
                        "links": attr.get("links", {})
                    })
                    merged["budget"]["attractions"] += cost

        # Merge entertainment
        if self.entertainment and "days" in self.entertainment:
            day_ent = next((d for d in self.entertainment["days"] if d.get("day") == day_num), {})
            if "entertainment" in day_ent:
                for ent in day_ent["entertainment"]:
                    ent_name_base = ent.get("name_base", "")
                    ent_name_local = ent.get("name_local", "")
                    ent_time = self._get_timeline_time(ent.get("name_base",""), ent.get("name_local",""), day_timeline)

                    # Convert cost to display currency
                    cost = ent.get("cost", 0)
                    ent_currency = ent.get("currency_local", "CNY")
                    cost = self._to_display_currency(cost, ent_currency)

                    merged["entertainment"].append({
                        "name_base": ent_name_base,
                        "name_local": ent_name_local,
                        "location_base": ent.get("location_base", ""),
                        "location_local": ent.get("location_local", ""),
                        "coordinates": ent.get("coordinates", {}),
                        "type_base": self._format_type(ent.get("type_base", "")),
                        "type_local": ent.get("type_local", ""),
                        "cost": cost,
                        "cost_local": ent.get("cost", 0),
                        "note_base": ent.get("note_base", ""),
                        "note_local": ent.get("note_local", ""),
                        "notes_base": ent.get("notes_base", ""),
                        "notes_local": ent.get("notes_local", ""),
                        "optional": ent.get("optional", False),
                        "image": self._get_placeholder_image(
                            "entertainment",
                            poi_name=ent_name_local if ent_name_local else ent_name_base,
                            gaode_id=ent.get("gaode_id", ""),
                            name_base=ent_name_base,
                            name_local=ent_name_local,
                            location_base=ent.get("location_base", ""),
                            location_local=ent.get("location_local", ""),
                            is_home=self._is_home_location(ent)
                        ),
                        "time": ent_time,
                        "links": ent.get("links", {})
                    })
                    merged["budget"]["entertainment"] += cost

        # Merge shopping items into day data and budget
        # Parse notes_base to extract individual brand stores from malls
        if self.shopping and "days" in self.shopping:
            day_shop = next((d for d in self.shopping["days"] if d.get("day") == day_num), {})
            for shop_item in day_shop.get("shopping", []):
                cost = shop_item.get("cost", 0)
                shop_currency = shop_item.get("currency_local", "CNY")
                cost = self._to_display_currency(cost, shop_currency)

                shop_name_base = shop_item.get("name_base", "")
                shop_name_local = shop_item.get("name_local", "")
                notes_base = shop_item.get("notes_base", "")
                notes_local = shop_item.get("notes_local", "")

                # Get mall image (used as fallback for brand cards)
                mall_image = shop_item.get("image_url", "") or self._get_placeholder_image(
                    "attraction",
                    poi_name=shop_name_local if shop_name_local else shop_name_base,
                    name_base=shop_name_base,
                    name_local=shop_name_local
                )
                mall_time = self._get_timeline_time(shop_item.get("name_base",""), shop_item.get("name_local",""), day_timeline)

                # Single card per shopping item. If brands exist, append brand info to notes.
                # (Fix for cfc5766 brand-splitting that caused duplicate mall images on every brand card.)
                brands = shop_item.get("brands", []) or self._parse_shopping_brands(notes_base, notes_local)
                if brands:
                    # Build brand summary lines for notes
                    brand_lines_base = []
                    brand_lines_local = []
                    for brand in brands:
                        b_name = brand.get("name", "")
                        b_name_local = brand.get("name_local", b_name)
                        b_cat = brand.get("category", "")
                        b_desc = brand.get("description", "")
                        b_desc_local = brand.get("description_local", b_desc)
                        if b_name:
                            line_base = f"\u2022 {b_name}"
                            line_local = f"\u2022 {b_name_local}"
                            if b_cat:
                                line_base += f" ({b_cat})"
                                line_local += f" ({b_cat})"
                            if b_desc:
                                line_base += f" \u2014 {b_desc}"
                            if b_desc_local:
                                line_local += f" \u2014 {b_desc_local}"
                            brand_lines_base.append(line_base)
                            brand_lines_local.append(line_local)
                    brand_text_base = "\n".join(brand_lines_base)
                    brand_text_local = "\n".join(brand_lines_local)
                    # Append brand info to existing notes
                    if notes_base:
                        notes_base = notes_base.rstrip() + "\n\n**Shops:**\n" + brand_text_base
                    else:
                        notes_base = "**Shops:**\n" + brand_text_base
                    if notes_local:
                        notes_local = notes_local.rstrip() + "\n\n**\u63a8\u8350\u5e97\u94fa\uff1a**\n" + brand_text_local
                    else:
                        notes_local = "**\u63a8\u8350\u5e97\u94fa\uff1a**\n" + brand_text_local

                # Always create ONE card per shopping item
                merged["shopping"].append({
                    "name_base": shop_name_base,
                    "name_local": shop_name_local,
                    "location_base": shop_item.get("location_base", ""),
                    "location_local": shop_item.get("location_local", ""),
                    "coordinates": shop_item.get("coordinates", {}),
                    "type_base": shop_item.get("type_base", ""),
                    "type_local": shop_item.get("type_local", ""),
                    "cost": cost,
                    "cost_local": shop_item.get("cost", 0),
                    "notes_base": notes_base,
                    "notes_local": notes_local,
                    "optional": shop_item.get("optional", False),
                    "image": mall_image,
                    "time": mall_time,
                    "links": {}
                })
                merged["budget"]["shopping"] += cost

        # Merge accommodation
        if self.accommodation and "days" in self.accommodation:
            day_acc = next((d for d in self.accommodation["days"] if d.get("day") == day_num), {})
            if "accommodation" in day_acc:
                acc = day_acc["accommodation"]
                # Convert cost to display currency
                cost = acc.get("cost", 0)
                acc_currency = acc.get("currency_local", "CNY")
                cost = self._to_display_currency(cost, acc_currency)

                acc_name_base = acc.get("name_base", "")
                acc_name_local = acc.get("name_local", "")

                # Time comes from sync-injected item.time; fall back to check_in if absent
                acc_time = self._get_timeline_time(acc_name_base, acc_name_local, day_timeline)
                if not acc_time and acc.get("check_in"):
                    acc_time = self._normalize_time(acc.get("check_in"), default_duration_hours=0.5)

                # Parse stars from explicit field
                stars = acc.get("stars", 0)

                merged["accommodation"] = {
                    "name_base": acc_name_base,
                    "name_local": acc_name_local,
                    "type_base": self._format_type(acc.get("type_base", "")),
                    "type_local": acc.get("type_local", ""),
                    "location_base": acc.get("location_base", ""),
                    "location_local": acc.get("location_local", ""),
                    "coordinates": acc.get("coordinates", {}),
                    "cost": cost,
                    "cost_local": acc.get("cost", 0),
                    "stars": stars if stars else 0,
                    "amenities_base": acc.get("amenities_base", []),
                    "amenities_local": acc.get("amenities_local", []),
                    "check_in": acc.get("check_in", ""),
                    "check_out": acc.get("check_out", ""),
                    "notes_base": acc.get("notes_base", ""),
                    "notes_local": acc.get("notes_local", ""),
                    "optional": acc.get("optional", False),
                    "time": acc_time,
                    "links": acc.get("links", {}),
                    "image": acc.get("image_url", "") or self._get_placeholder_image(
                        "accommodation",
                        poi_name=acc_name_local if acc_name_local else acc_name_base,
                        name_base=acc_name_base,
                        name_local=acc_name_local,
                        location_base=acc.get("location_base", ""),
                        location_local=acc.get("location_local", ""),
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

                # Determine transport type and icon — local from ui_labels data
                req_labels = self.requirements.get("trip_summary", {}).get("ui_labels", {})
                ui_local = req_labels.get("local", {})
                transport_type = loc_change.get("type_base", "")
                if "train" in transport_type.lower():
                    icon = "🚄"
                    type_display = transport_type or "High-speed Train"
                    type_display_local = loc_change.get("type_local", "") or ui_local.get("high_speed_train", "")
                elif "flight" in transport_type.lower():
                    icon = "✈️"
                    type_display = transport_type or "Flight"
                    type_display_local = loc_change.get("type_local", "") or ui_local.get("flight", "")
                else:
                    icon = "🚌"
                    type_display = transport_type
                    type_display_local = loc_change.get("type_local", "")

                # Extract route info from direct fields
                departure_point = loc_change.get("departure_point_base", "")
                arrival_point = loc_change.get("arrival_point_base", "")
                route_number = loc_change.get("route_number", "")
                airline = loc_change.get("company_base", "")

                # Booking status — local strings come from ui_labels data
                booking_status = loc_change.get("status_base", "")
                if not booking_status:
                    if loc_change.get("booking_required", False):
                        urgency = loc_change.get("booking_urgency", "")
                        if "CRITICAL" in urgency or "URGENT" in urgency:
                            booking_status = "URGENT"
                        else:
                            booking_status = "REQUIRED"
                    else:
                        booking_status = "VERIFIED"
                # Resolve local from ui_labels (key = lowercase status), prefer direct field
                booking_status_local = loc_change.get("status_local", "") or ui_local.get(booking_status.lower(), "")

                # Extract bilingual city names — prefer new from_local/to_local, fallback to old extraction
                from_local = loc_change.get("from_local", "") or self._extract_local_city(loc_change.get("from_location", ""), loc_change.get("from", ""))
                to_local = loc_change.get("to_local", "") or self._extract_local_city(loc_change.get("to_location", ""), loc_change.get("to", ""))

                # Fix #9: Split bilingual departure/arrival points
                # Prefer new direct _local fields, fallback to split_bilingual for old data
                dep_base, dep_local = self._split_bilingual(departure_point)
                dep_local = loc_change.get("departure_point_local", "") or dep_local
                arr_base, arr_local = self._split_bilingual(arrival_point)
                arr_local = loc_change.get("arrival_point_local", "") or arr_local

                merged["transportation"] = {
                    "name_base": loc_change.get("name_base", "") or f"{loc_change.get('from_base', '')} \u2192 {loc_change.get('to_base', '')}",
                    "name_local": loc_change.get("name_local", "") or (f"{from_local} \u2192 {to_local}" if from_local and to_local else ""),
                    "from_base": loc_change.get("from_base", ""),
                    "to_base": loc_change.get("to_base", ""),
                    "from_local": from_local,
                    "to_local": to_local,
                    "departure_point_base": dep_base,
                    "departure_point_local": dep_local,
                    "arrival_point_base": arr_base,
                    "arrival_point_local": arr_local,
                    "type_base": type_display,
                    "type_local": type_display_local,
                    "icon": icon,
                    "route_number": route_number,
                    "company_base": airline,
                    "company_local": loc_change.get("company_local", ""),
                    "cost": self._to_display_currency(*self._extract_transport_cost(loc_change)),
                    "cost_local": self._extract_transport_cost(loc_change)[0],
                    "cost_type_base": loc_change.get("cost_type_base", ""),
                    "cost_type_local": loc_change.get("cost_type_local", ""),
                    "status_base": booking_status,
                    "status_local": booking_status_local,
                    "notes_base": loc_change.get("notes_base", ""),
                    "notes_local": loc_change.get("notes_local", ""),
                    "booking_required": loc_change.get("booking_required", False),
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

                    # Determine transport type and icon — local from ui_labels data
                    bl_req_labels = self.requirements.get("trip_summary", {}).get("ui_labels", {})
                    bl_ui_local = bl_req_labels.get("local", {})
                    if "flight" in method:
                        icon = "✈️"
                        type_display = "Flight"
                        type_display_local = bl_ui_local.get("flight", "")
                    elif "train" in method:
                        icon = "🚄"
                        type_display = option.get("train_type", "High-speed Train")
                        type_display_local = bl_ui_local.get("high_speed_train", "")
                    else:
                        icon = "🚌"
                        type_display = method.replace("_", " ").title()
                        type_display_local = ""

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
                        "name_base": f"Beijing \u2192 {location_base}",
                        "name_local": f"{self._extract_local_city('', 'Beijing')} \u2192 {self._extract_local_city('', location_base)}" if self._extract_local_city("", "Beijing") else "",
                        "from_base": "Beijing",
                        "to_base": location_base,
                        "from_local": self._extract_local_city("", "Beijing"),
                        "to_local": self._extract_local_city("", location_base),
                        "departure_point_base": bl_dep_base,
                        "departure_point_local": bl_dep_local,
                        "arrival_point_base": bl_arr_base,
                        "arrival_point_local": bl_arr_local,
                        "type_base": type_display,
                        "type_local": type_display_local,
                        "icon": icon,
                        "route_number": route_number,
                        "company_base": "",
                        "company_local": "",
                        "cost": self._to_display_currency(cost_eur if cost_eur else cost_cny, "EUR" if cost_eur else "CNY"),
                        "cost_local": cost_cny if cost_cny else cost_eur,
                        "cost_type_base": "",
                        "cost_type_local": "",
                        "status_base": "RECOMMENDED",
                        "status_local": bl_ui_local.get("recommended", ""),
                        "notes_base": " | ".join(notes_parts),
                        "notes_local": "",
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
                    "name_base": seg.get("name_base", ""),
                    "name_local": seg.get("name_local", ""),
                    "time": {"start": seg["start_time"], "end": seg["end_time"]},
                    "duration": f"{duration_min}min" if duration_min else "",
                    "type_base": seg.get("type_base", "travel"),
                    "type_local": seg.get("type_local", ""),
                    "icon": seg.get("icon", "\U0001f6b6")
                })

        # Add transportation cost to budget (from merged transportation data)
        if merged.get("transportation") and merged["transportation"].get("cost", 0) > 0:
            merged["budget"]["transportation"] = merged["transportation"]["cost"]

        self._inject_intra_routes(merged, day_num)

        # Calculate total budget (includes all categories)
        merged["budget"]["total"] = sum([
            merged["budget"]["meals"],
            merged["budget"]["attractions"],
            merged["budget"]["entertainment"],
            merged["budget"]["accommodation"],
            merged["budget"]["shopping"],
            merged["budget"]["cafe"],
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
        """Generate PLAN_DATA for bucket list (city_guides format)"""

        # Get ui_labels from requirements-skeleton and merge with defaults
        req_labels = self.requirements.get("trip_summary", {}).get("ui_labels", {})
        base_labels = {**self.DEFAULT_UI_LABELS_BASE, **req_labels.get("base", {})}
        local_labels = req_labels.get("local", {})  # No defaults for local — all from data
        ui_labels = {
            "base_display": req_labels.get("base_display", "EN"),
            "local_display": req_labels.get("local_display", "Local"),
            "base": base_labels,
            "local": local_labels,
        }

        req_summary = self.requirements.get("trip_summary", {})
        trip_summary = {
            "trip_type": "bucket_list",
            "trip_type_local": req_summary.get("trip_type_local", ""),
            "description": req_summary.get("description", "Destination Options"),
            "description_local": "",
            "base_location": req_summary.get("base_location", ""),
            "period": req_summary.get("period", ""),
            "period_local": "",
            "travelers": req_summary.get("travelers", "1 adult"),
            "travelers_local": "",
            "budget_per_trip": req_summary.get("budget_per_trip", f"{self._display_symbol}200-500"),
            "preferences": "",
            "base_display": ui_labels.get("base_display", "EN"),
            "local_display": ui_labels.get("local_display", "Local"),
            "ui_labels": ui_labels,
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
                "cafe": [],
                "budget": {
                    "meals": 0,
                    "attractions": 0,
                    "entertainment": 0,
                    "accommodation": 0,
                    "shopping": 0,
                    "cafe": 0,
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
                        "name_base": a_name_base,
                        "name_local": a_name_local,
                        "location_base": city_name,
                        "location_local": "",
                        "type_base": self._format_type(attr.get("type", "")),
                        "type_local": attr.get("type_local", ""),
                        "cost": self._to_display_currency(attr.get("ticket_price_eur", 0), "EUR"),
                        "cost_local": attr.get("ticket_price_eur", 0),
                        "opening_hours": attr.get("opening_hours", ""),
                        "recommended_duration": f"{attr.get('recommended_duration_hours', 2)}h",
                        "image": self._get_placeholder_image("attraction", poi_name=a_name_local if a_name_local else a_name_base, name_base=a_name_base, name_local=a_name_local),
                        "notes_base": attr.get("notes", ""),
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
                        "name_base": m_name_base,
                        "name_local": m_name_local,
                        "location_base": city_name,
                        "location_local": "",
                        "cost": self._to_display_currency(meal.get("price_range_eur_low", 10), "EUR"),
                        "cost_local": meal.get("price_range_eur_low", 10),
                        "cuisine_base": meal.get("cuisine_type", ""),
                        "cuisine_local": meal.get("cuisine_local", ""),
                        "signature_dishes_base": meal.get("signature_dish", ""),
                        "signature_dishes_local": meal.get("signature_dishes_local", ""),
                        "notes_base": meal.get("notes", ""),
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
                day["budget"]["cafe"],
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
        period_local = skel_summary.get("period_local", "")

        # Get ui_labels from requirements-skeleton and merge with defaults
        req_labels = self.requirements.get("trip_summary", {}).get("ui_labels", {})
        base_labels = {**self.DEFAULT_UI_LABELS_BASE, **req_labels.get("base", {})}
        local_labels = req_labels.get("local", {})  # No defaults for local — all from data
        ui_labels = {
            "base_display": req_labels.get("base_display", "EN"),
            "local_display": req_labels.get("local_display", "Local"),
            "base": base_labels,
            "local": local_labels,
        }

        # Bilingual trip type
        raw_trip_type = skel_summary.get("trip_type", "itinerary")

        # Travelers: local comes from data, not hardcoded
        travelers_raw = skel_summary.get("travelers", "1 adult")
        travelers_local = skel_summary.get("travelers_local", "")

        trip_summary = {
            # Fix #1, #3: Format trip_type for natural language display
            "trip_type": self._format_trip_type(raw_trip_type),
            "trip_type_local": skel_summary.get("trip_type_local", ""),
            "description": skel_summary.get("description", "Travel Plan"),
            "description_local": skel_summary.get("description_local", "") or self.skeleton.get("description_local", ""),
            "base_location": skel_summary.get("base_location", ""),
            "period": period,
            "period_local": period_local,
            "travelers": travelers_raw,
            "travelers_local": travelers_local,
            "budget_per_trip": skel_summary.get("budget_per_trip", f"{self._display_symbol}500"),
            "preferences": prefs_str,
            "base_display": ui_labels.get("base_display", "EN"),
            "local_display": ui_labels.get("local_display", "Local"),
            "ui_labels": ui_labels,
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
    .category-scroll-container::-webkit-scrollbar {{
      height: 6px;
    }}
    .category-scroll-container::-webkit-scrollbar-track {{
      background: transparent;
    }}
    .category-scroll-container::-webkit-scrollbar-thumb {{
      background: rgba(0,0,0,0.15);
      border-radius: 3px;
    }}
    .category-scroll-container::-webkit-scrollbar-thumb:hover {{
      background: rgba(0,0,0,0.25);
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
    { v: budget.cafe || 0, c: '#D4A574', k: 'cafe' },
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
const Sidebar = ({ trips, selTrip, selDay, onSelect, isOpen, onClose, bp, lang }) => {
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
                <span style={{ fontWeight: '500', flex: 1 }}>{(lang === 'local' && trip.name_local) ? trip.name_local : trip.name}</span>
                <span style={{ fontSize: '11px', color: '#b4b4b4' }}>({trip.days_count != null ? ((trip.days_count === 1 ? L('days_count_1', lang) : L('days_count', lang)).replace('{n}', trip.days_count)) : trip.days_label})</span>
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
                      >📄 {dayLabelSidebar(d, lang)}</div>
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
            {{ meal: '🍽️', attraction: '📍', entertainment: '🎭', shopping: '🛍️', accommodation: '🏨', transportation: item.icon || '🚄' }[type] || '📄'}
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
          {type === 'transportation' ? (<>
            {item.icon} {lang === 'local' && item.from_local ? item.from_local : item.from_base} → {lang === 'local' && item.to_local ? item.to_local : item.to_base}
          </>) : (<>
            {getDisplayName(item, lang)}
            <RedNoteLink name={item.name_local || item.name_base} />
          </>)}
        </h2>

        <div style={{ borderTop: '1px solid #f0efed', paddingTop: '16px' }}>
          {item.time && type !== 'transportation' && (
            <PropertyRow label={L('time', lang)}>
              {item.time.start} – {item.time.end}
            </PropertyRow>
          )}
          {/* Category-specific field ordering */}
          {type === 'accommodation' ? (<>
            {item.check_in && <PropertyRow label={L('checkin', lang)}>{item.check_in}</PropertyRow>}
            {item.check_out && <PropertyRow label={L('checkout', lang)}>{item.check_out}</PropertyRow>}
            {(item.cost !== undefined && (item.cost > 0 || item.cost_type_base === 'prepaid')) && <PropertyRow label={L('cost', lang)}>{fmtCost(item.cost, item.cost_type_base, lang)}</PropertyRow>}
            {getDisplayField(item, 'type', lang) && <PropertyRow label={L('type', lang)}>{getDisplayField(item, 'type', lang)}</PropertyRow>}
            {item.stars > 0 && <PropertyRow label={L('stars', lang)}><span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(item.stars)}</span></PropertyRow>}
            {(item.location_base || item.location_local) && <PropertyRow label={L('location', lang)}><MapLink item={item} lang={lang} mapProvider={mapProvider} /></PropertyRow>}
          </>) : type === 'transportation' ? (<>
            {item.time && <PropertyRow label={L('time', lang)}>{item.time.start} – {item.time.end}</PropertyRow>}
            {item.cost != null && (item.cost > 0 || item.cost_type_base === 'prepaid') && <PropertyRow label={L('cost', lang)}>{fmtCost(item.cost, item.cost_type_base, lang)}</PropertyRow>}
            <PropertyRow label={L('type', lang)}>{getDisplayField(item, 'type', lang)}</PropertyRow>
            {getDisplayField(item, 'company', lang) && <PropertyRow label={L('company', lang)}>{getDisplayField(item, 'company', lang)}</PropertyRow>}
            {item.route_number && <PropertyRow label={L('route_number', lang)}>{item.route_number}</PropertyRow>}
            {getDisplayField(item, 'status', lang) && (
              <PropertyRow label={L('status', lang)}>
                <span style={{
                  padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: '600',
                  background: item.status_base?.includes('URGENT') ? '#fff4e6' : item.status_base?.includes('VERIFIED') ? '#e9f5ec' : '#edf2fc',
                  color: item.status_base?.includes('URGENT') ? '#d97706' : item.status_base?.includes('VERIFIED') ? '#1a7a32' : '#2b63b5'
                }}>
                  {getDisplayField(item, 'status', lang)}
                </span>
              </PropertyRow>
            )}
            {item.departure_point_base && <PropertyRow label={L('route', lang)}>{lang === 'local' && item.departure_point_local ? item.departure_point_local : item.departure_point_base} → {lang === 'local' && item.arrival_point_local ? item.arrival_point_local : item.arrival_point_base}</PropertyRow>}
            {item.booking_required && (
              <div style={{ marginTop: '6px' }}>
                <span style={{ fontSize: '11px', padding: '2px 8px', background: '#fff3e0', border: '1px solid #ffcc80', borderRadius: '4px', color: '#e65100', fontWeight: '600' }}>
                  {L('booking_required', lang)}
                </span>
              </div>
            )}
          </>) : (<>
            {item.check_in && <PropertyRow label={L('checkin', lang)}>{item.check_in}</PropertyRow>}
            {item.check_out && <PropertyRow label={L('checkout', lang)}>{item.check_out}</PropertyRow>}
            {(item.cost !== undefined && (item.cost > 0 || item.cost_type_base === 'prepaid')) && <PropertyRow label={L('cost', lang)}>{fmtCost(item.cost, item.cost_type_base, lang)}</PropertyRow>}
            {getDisplayField(item, 'cuisine', lang) && <PropertyRow label={L('cuisine', lang)}>{getDisplayField(item, 'cuisine', lang)}</PropertyRow>}
            {getDisplayField(item, 'signature_dishes', lang) && <PropertyRow label={L('signature', lang)}>{getDisplayField(item, 'signature_dishes', lang)}</PropertyRow>}
            {getDisplayField(item, 'type', lang) && <PropertyRow label={L('type', lang)}>{getDisplayField(item, 'type', lang)}</PropertyRow>}
            {item.opening_hours && <PropertyRow label={L('opening_hours', lang)}>{item.opening_hours}</PropertyRow>}
            {(item.location_base || item.location_local) && <PropertyRow label={L('location', lang)}><MapLink item={item} lang={lang} mapProvider={mapProvider} /></PropertyRow>}
            {item.optional && <PropertyRow label={L('optional', lang)}><span style={{ padding: '2px 8px', background: '#f5f5f3', borderRadius: '4px', fontSize: '12px', color: '#9b9a97', fontWeight: '600' }}>{L('optional', lang)}</span></PropertyRow>}
            {item.stars > 0 && <PropertyRow label={L('stars', lang)}><span style={{ color: '#e9b200', letterSpacing: '1px' }}>{'★'.repeat(item.stars)}</span></PropertyRow>}
          </>)}
          {((lang === 'local' && item.amenities_local && item.amenities_local.length > 0) ? item.amenities_local : (item.amenities_base && item.amenities_base.length > 0 ? item.amenities_base : null)) && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>{L('amenities', lang)}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {(lang === 'local' && item.amenities_local && item.amenities_local.length > 0 ? item.amenities_local : item.amenities_base).map((a, i) => (
                  <span key={i} style={{ fontSize: '12px', padding: '3px 8px', background: '#f5f5f3', borderRadius: '4px', color: '#6b6b6b' }}>{a}</span>
                ))}
              </div>
            </div>
          )}
          {(lang === 'local' && item.note_local ? item.note_local : item.note_base) && (
            <div style={{
              marginTop: '16px', padding: '12px 16px',
              background: '#fffdf5', borderRadius: '6px',
              border: '1px solid #f5ecd7', fontSize: '13px', color: '#9a6700'
            }}>
              💡 {lang === 'local' && item.note_local ? item.note_local : item.note_base}
            </div>
          )}
          {(lang === 'local' && item.notes_local ? item.notes_local : item.notes_base) && (
            <div style={{
              marginTop: '16px', padding: '12px 16px',
              background: '#f5f9fc', borderRadius: '6px',
              border: '1px solid #d9e8f5', fontSize: '13px', color: '#37352f', lineHeight: 1.6
            }}>
              {lang === 'local' && item.notes_local ? item.notes_local : item.notes_base}
            </div>
          )}
          {item.links && Object.keys(item.links).length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '8px' }}>
                {L('links', lang)}
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
    meals: { icon: '🍽️', label: L('meals', lang), color: '#f0b429' },
    attractions: { icon: '📍', label: L('attractions', lang), color: '#4a90d9' },
    entertainment: { icon: '🎭', label: L('entertainment', lang), color: '#9b6dd7' },
    accommodation: { icon: '🏨', label: L('accommodation', lang), color: '#45b26b' },
    shopping: { icon: '🛍️', label: L('shopping', lang), color: '#e07c5a' },
    cafe: { icon: '\u2615', label: L('cafe', lang), color: '#D4A574' },
    transportation: { icon: '🚄', label: L('transport', lang), color: '#0ea5e9' }
  };
  const cfg = categoryConfig[category] || { icon: '💰', label: L('budget', lang), color: '#37352f' };

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
                  {lang === 'local' && item.name_local ? item.name_local : (item.name_base || '')}
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
                  <span style={{ color: '#9b9a97' }}>{L('cost', lang)}</span>
                  <span style={{ fontWeight: '600', color: cfg.color }}>
                    {fmtCost(item.cost, undefined, lang)}
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
                <span>{L('total', lang)}</span>
                <span style={{ color: cfg.color }}>{CURRENCY_SYMBOL}{total.toFixed(0)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9b9a97' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>{cfg.icon}</div>
            <div style={{ fontSize: '14px' }}>{L('no_items', lang)}</div>
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
    return item.name_base || '';
  }
  return item.name_local || item.name_base || '';
};

// All costs are in display currency (from config). Use CURRENCY_SYMBOL.
const fmtCost = (c, costType, lng) => {
  if (costType === 'prepaid') return L('prepaid', lng);
  const n = Number(c);
  if (!n || n === 0) return L('free', lng);
  return Number.isInteger(n) ? `${CURRENCY_SYMBOL}${n}` : `${CURRENCY_SYMBOL}${n.toFixed(1)}`;
};

// Fix issues #4,7,12: Language-aware location display
const getDisplayLocation = (item, lang) => {
  if (!item) return '';
  if (lang === 'base') return item.location_base || '';
  return item.location_local || item.location_base || '';
};

// Bilingual field helper: returns local variant when lang='local' and data exists
const getDisplayField = (item, field, lang) => {
  if (!item) return '';
  if (lang === 'local' && item[field + '_local']) return item[field + '_local'];
  return item[field + '_base'] || '';
};

// Data-driven bilingual labels — reads from PLAN_DATA.trip_summary.ui_labels
const L = (key, lng) => {
  const labels = PLAN_DATA.trip_summary.ui_labels || {};
  if (lng === 'local' && labels.local && labels.local[key]) {
    return labels.local[key];
  }
  if (labels.base && labels.base[key]) {
    return labels.base[key];
  }
  return key; // ultimate fallback: the key itself
};

// Format a YYYY-MM-DD date string into localized display
// Base lang: "Feb 15 (Sat)", Local lang: "2月15日 (六)"
const formatRealDate = (dateStr, lng) => {
  const m = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const d = new Date(parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]));
  if (isNaN(d.getTime())) return null;
  const labels = PLAN_DATA.trip_summary.ui_labels || {};
  if (lng === 'local' && labels.local && labels.local.day_format) {
    // Local lang format: "2月15日 (六)"
    const localMonths = ['1','2','3','4','5','6','7','8','9','10','11','12'];
    const localDays = labels.local.weekdays_short || ['日','一','二','三','四','五','六'];
    return `${localMonths[d.getMonth()]}月${d.getDate()}日 (${localDays[d.getDay()]})`;
  }
  // Base lang format: "Feb 15 (Sat)"
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  return `${months[d.getMonth()]} ${d.getDate()} (${days[d.getDay()]})`;
};

// Day label helper — handles format differences between languages
// For itinerary trips with real dates (YYYY-MM-DD): "Feb 15 (Sat) – Chongqing"
// For bucket-list / no real date: "Day 3 – Chongqing"
// Accepts day object or (dayNum, location, lng) for backward compat
const dayLabel = (dayNumOrObj, locationOrLng, lngOpt) => {
  // Support both: dayLabel(day, lang) and dayLabel(dayNum, location, lng)
  let dayNum, date, location, lng;
  if (typeof dayNumOrObj === 'object' && dayNumOrObj !== null) {
    // Called as dayLabel(dayObj, lang)
    const day = dayNumOrObj;
    dayNum = day.day;
    date = day.date || '';
    lng = locationOrLng;
    location = (lng === 'local' && day.location_local) ? day.location_local : day.location_base;
  } else {
    // Legacy: dayLabel(dayNum, location, lng)
    dayNum = dayNumOrObj;
    date = '';
    location = locationOrLng;
    lng = lngOpt;
  }
  // If day has a real date (YYYY-MM-DD), use formatted date instead of "Day N"
  const realDate = date ? formatRealDate(date, lng) : null;
  let prefix;
  if (realDate) {
    prefix = realDate;
  } else {
    const labels = PLAN_DATA.trip_summary.ui_labels || {};
    const fmt = (lng === 'local' && labels.local && labels.local.day_format)
      || (labels.base && labels.base.day_format) || 'Day {n}';
    prefix = fmt.replace('{n}', dayNum);
  }
  return prefix + (location ? ' – ' + location : '');
};

// Day label for sidebar nav (shows date only, no city name)
// Accepts day object or dayNum for backward compat
const dayLabelSidebar = (dayNumOrObj, lng) => {
  let dayNum, date;
  if (typeof dayNumOrObj === 'object' && dayNumOrObj !== null) {
    const day = dayNumOrObj;
    dayNum = day.day;
    date = day.date || '';
  } else {
    dayNum = dayNumOrObj;
    date = '';
  }
  // Use real date if available
  const realDate = date ? formatRealDate(date, lng) : null;
  return realDate ? realDate : `Day ${dayNum}`;
};

// Day label for sidebar nav (no location) - deprecated in favor of dayLabelSidebar
// Accepts day object or dayNum for backward compat
const dayLabelShort = (dayNumOrObj, lng) => {
  let dayNum, date;
  if (typeof dayNumOrObj === 'object' && dayNumOrObj !== null) {
    dayNum = dayNumOrObj.day;
    date = dayNumOrObj.date || '';
  } else {
    dayNum = dayNumOrObj;
    date = '';
  }
  const realDate = date ? formatRealDate(date, lng) : null;
  if (realDate) return realDate;
  const labels = PLAN_DATA.trip_summary.ui_labels || {};
  const fmt = (lng === 'local' && labels.local && labels.local.day_format)
    || (labels.base && labels.base.day_format) || 'Day {n}';
  return fmt.replace('{n}', dayNum);
};

// Meal type emoji (kept separate from label text — emoji is decoration, not translation)
const mealEmoji = { breakfast: '🌅', lunch: '☀️', dinner: '🌙' };

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
    googleHref = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
    gaodeH5 = `https://uri.amap.com/marker?position=${lng},${lat}&name=${encodeURIComponent(loc)}&callnative=0`;
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
        {expanded ? L('show_less', lang) : L('show_more', lang)}
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
                {lang === 'local' && tripSummary.description_local ? tripSummary.description_local : tripSummary.description}
              </h1>
              <div style={{
                padding: sm ? '12px' : '16px 20px',
                background: '#fbfbfa', borderRadius: '8px',
                border: '1px solid #f0efed', marginBottom: '32px'
              }}>
                <PropertyRow label={L('trip_type', lang)}>{lang === 'local' && tripSummary.trip_type_local ? tripSummary.trip_type_local : tripSummary.trip_type}</PropertyRow>
                {tripSummary.base_location && <PropertyRow label={L('base_location', lang)}>{tripSummary.base_location}</PropertyRow>}
                <PropertyRow label={L('period', lang)}>{lang === 'local' && tripSummary.period_local ? tripSummary.period_local : tripSummary.period}</PropertyRow>
                <PropertyRow label={L('travelers', lang)}>{lang === 'local' && tripSummary.travelers_local ? tripSummary.travelers_local : tripSummary.travelers}</PropertyRow>
                <PropertyRow label={L('budget_trip', lang)}>{tripSummary.budget_per_trip}</PropertyRow>
                {/* Preferences hidden per user request */}
              </div>
            </>
          ) : (
            <>
            <h1 style={{ fontSize: sm ? '24px' : '36px', fontWeight: '700', color: '#37352f', margin: '0 0 4px', lineHeight: 1.25 }}>
              {dayLabel(day, lang)}
            </h1>
            </>
          )}

          {showSummary && (
            <h2 style={{ fontSize: sm ? '20px' : '26px', fontWeight: '700', color: '#37352f', margin: '0 0 28px' }}>
              {dayLabel(day, lang)}
            </h2>
          )}
        </div>

        {/* User Plans */}
        {day.user_plans && day.user_plans.length > 0 && (
          <Section title={L('user_plans', lang)} icon="📝">
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

        {/* ========== HORIZONTAL SCROLL CARD ROWS ========== */}
        {(() => {
          const cardW = sm ? 240 : 280;
          const cardH = sm ? 300 : 320;
          const imgH = sm ? 120 : 140;
          const categoryColors = { meals: '#e67e22', attractions: '#3498db', entertainment: '#9b59b6', shopping: '#e74c3c', cafe: '#D4A574', accommodation: '#27ae60', transportation: '#0ea5e9' };

          const scrollContainerStyle = {
            display: 'flex', flexWrap: 'nowrap', gap: '12px',
            overflowX: 'auto', overflowY: 'hidden',
            scrollBehavior: 'smooth', WebkitOverflowScrolling: 'touch',
            scrollSnapType: 'x proximity',
            paddingBottom: '8px',
            scrollbarWidth: 'thin', scrollbarColor: 'rgba(0,0,0,0.15) transparent'
          };

          const cardStyle = (catColor, isPrimary, isOptional) => ({
            width: cardW + 'px', minWidth: cardW + 'px', height: cardH + 'px',
            flexShrink: 0, scrollSnapAlign: 'start',
            background: '#fff', borderRadius: '8px',
            border: isOptional ? '1.5px dashed ' + catColor + '80' : 'none',
            boxShadow: isOptional ? '0 1px 3px rgba(0,0,0,0.04)' : (isPrimary ? '0 1px 3px rgba(0,0,0,0.06), 0 0 0 1.5px ' + catColor + '33' : '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'),
            overflow: 'hidden', transition: 'box-shadow .15s, transform .15s', cursor: 'pointer',
            display: 'flex', flexDirection: 'column'
          });

          const hoverOn = (e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1), 0 0 0 1px rgba(74,144,217,0.2)'; e.currentTarget.style.transform = 'translateY(-2px)'; };
          const hoverOff = (e, catColor, isPrimary, isOptional) => { e.currentTarget.style.boxShadow = isOptional ? '0 1px 3px rgba(0,0,0,0.04)' : (isPrimary ? '0 1px 3px rgba(0,0,0,0.06), 0 0 0 1.5px ' + catColor + '33' : '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)'); e.currentTarget.style.transform = 'translateY(0)'; };

          const categoryRowStyle = { position: 'relative' };
          const fadeStyle = {
            content: "''", position: 'absolute', right: 0, bottom: '8px',
            width: '40px', height: (cardH) + 'px',
            background: 'linear-gradient(to right, transparent, rgba(255,255,255,0.9))',
            pointerEvents: 'none', zIndex: 1
          };

          return (
            <>
              {/* Meals */}
              <Section title={L('meals', lang)} icon="🍽️">
                <div style={categoryRowStyle}>
                  <div style={scrollContainerStyle} className="category-scroll-container">
                    {['breakfast', 'lunch', 'dinner'].flatMap(type => {
                      const meal = day.meals[type];
                      if (!meal) return [];
                      const emoji = mealEmoji[type] || '';
                      const label = L(type, lang);
                      return [{...meal, _type: type, _emoji: emoji, _label: label, _isPrimary: true, _oi: 0}];
                    }).map((opt, gi) => {
                      const catColor = categoryColors.meals;
                      return (
                        <div key={gi} style={cardStyle(catColor, opt._isPrimary)}
                          onClick={() => onItemClick && onItemClick(opt, 'meal')}
                          onMouseEnter={hoverOn}
                          onMouseLeave={e => hoverOff(e, catColor, opt._isPrimary)}
                        >
                          <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                            {opt.image && <img src={opt.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                              onError={e => { e.target.style.display = 'none'; }} />}
                          </div>
                          <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                            <div style={{ fontSize: '10px', fontWeight: '700', color: opt._isPrimary ? catColor : '#9b9a97', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                              <span>{opt._emoji} {opt._label}</span>
                              {opt.option_label && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97' }}>{(L('option', lang) || 'Option') + ' ' + opt.option_label}</span>}
                            </div>
                            <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                              {getDisplayName(opt, lang)}
                              <RedNoteLink name={opt.name_local || opt.name_base} />
                            </div>
                            <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                              {opt.time && opt.time.start !== '00:00' && <div>{opt.time.start} – {opt.time.end}{opt.cost > 0 ? ' · ' + fmtCost(opt.cost, undefined, lang) : ''}</div>}
                              {!opt.time && opt.cost > 0 && <div>{fmtCost(opt.cost, undefined, lang)}</div>}
                              {getDisplayField(opt, 'cuisine', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(opt, 'cuisine', lang)}</div>}
                              {(opt.location_base || opt.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={opt} lang={lang} mapProvider={mapProvider} /></div>}
                            </div>
                            <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                              {lang === 'local' && opt.notes_local ? opt.notes_local : opt.notes_base}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div style={fadeStyle} />
                </div>
              </Section>

              {/* Cafe */}
              {day.cafe && day.cafe.length > 0 && (
                <Section title={L('cafe', lang)} icon="\u2615">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.cafe.map((c, i) => {
                        const catColor = categoryColors.cafe;
                        return (
                          <div key={i} style={cardStyle(catColor, false, c.optional)}
                            onClick={() => onItemClick && onItemClick(c, 'cafe')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, c.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#faf6f0', flexShrink: 0 }}>
                              {c.image && <img src={c.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>\u2615 {L('cafe', lang)}</span>
                                {c.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(c, lang)}
                                <RedNoteLink name={c.name_local || c.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {c.time && c.time.start !== '00:00' && <div>{c.time.start} \u2013 {c.time.end}{c.cost > 0 ? ' \u00b7 ' + fmtCost(c.cost, undefined, lang) : ''}</div>}
                                {!c.time && c.cost > 0 && <div>{fmtCost(c.cost, undefined, lang)}</div>}
                                {getDisplayField(c, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(c, 'type', lang)}</div>}
                                {getDisplayField(c, 'cuisine', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(c, 'cuisine', lang)}</div>}
                                {(c.location_base || c.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={c} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && c.notes_local ? c.notes_local : c.notes_base}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
              )}

              {/* Attractions */}
              {day.attractions && day.attractions.length > 0 && (
                <Section title={L('attractions', lang)} icon="📍">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.attractions.map((attr, i) => {
                        const catColor = categoryColors.attractions;
                        return (
                          <div key={i} style={cardStyle(catColor, false, attr.optional)}
                            onClick={() => onItemClick && onItemClick(attr, 'attraction')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, attr.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#eef4f9', flexShrink: 0 }}>
                              {attr.image && <img src={attr.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>📍 {L('attractions', lang)}</span>
                                {attr.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(attr, lang)}
                                <RedNoteLink name={attr.name_local || attr.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {attr.time && <div>{attr.time.start} – {attr.time.end}{attr.cost > 0 ? ' · ' + fmtCost(attr.cost, undefined, lang) : ''}</div>}
                                {!attr.time && attr.cost > 0 && <div>{fmtCost(attr.cost, undefined, lang)}</div>}
                                {getDisplayField(attr, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(attr, 'type', lang)}</div>}
                                {(attr.location_base || attr.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={attr} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && attr.notes_local ? attr.notes_local : attr.notes_base}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
              )}

              {/* Entertainment */}
              {day.entertainment?.length > 0 && (
                <Section title={L('entertainment', lang)} icon="🎭">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.entertainment.map((ent, i) => {
                        const catColor = categoryColors.entertainment;
                        return (
                          <div key={i} style={cardStyle(catColor, false, ent.optional)}
                            onClick={() => onItemClick && onItemClick(ent, 'entertainment')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, ent.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                              {ent.image && <img src={ent.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>🎭 {L('entertainment', lang)}</span>
                                {ent.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(ent, lang)}
                                <RedNoteLink name={ent.name_local || ent.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {ent.time && <div>{ent.time.start} – {ent.time.end}{ent.cost > 0 ? ' · ' + fmtCost(ent.cost, undefined, lang) : ''}</div>}
                                {!ent.time && ent.cost > 0 && <div>{fmtCost(ent.cost, undefined, lang)}</div>}
                                {getDisplayField(ent, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(ent, 'type', lang)}</div>}
                                {(ent.location_base || ent.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={ent} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && ent.notes_local ? ent.notes_local : (lang === 'local' && ent.note_local ? ent.note_local : ent.note_base)}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
              )}

              {/* Shopping */}
              {day.shopping && day.shopping.length > 0 && (
                <Section title={L('shopping', lang)} icon="🛍️">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {day.shopping.map((shop, i) => {
                        const catColor = categoryColors.shopping;
                        return (
                          <div key={i} style={cardStyle(catColor, false, shop.optional)}
                            onClick={() => onItemClick && onItemClick(shop, 'shopping')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false, shop.optional)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                              {shop.image && <img src={shop.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                                <span>🛍️ {L('shopping', lang)}</span>
                                {shop.optional && <span style={{ padding: '1px 4px', background: '#f5f5f3', borderRadius: '3px', fontSize: '9px', color: '#9b9a97', border: '1px solid #e0e0e0' }}>{L('optional', lang)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(shop, lang)}
                                <RedNoteLink name={shop.name_local || shop.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {shop.time && <div>{shop.time.start} – {shop.time.end}{shop.cost > 0 ? ' · ' + fmtCost(shop.cost, undefined, lang) : ''}</div>}
                                {!shop.time && shop.cost > 0 && <div>{fmtCost(shop.cost, undefined, lang)}</div>}
                                {getDisplayField(shop, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(shop, 'type', lang)}</div>}
                                {(shop.location_base || shop.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={shop} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && shop.notes_local ? shop.notes_local : shop.notes_base}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={fadeStyle} />
                  </div>
                </Section>
              )}

              {/* Accommodation */}
              {day.accommodation && (
                <Section title={L('accommodation', lang)} icon="🏨">
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {(day.accommodation ? [day.accommodation] : []).map((acc, i) => {
                        const catColor = categoryColors.accommodation;
                        return (
                          <div key={i} style={cardStyle(catColor, false)}
                            onClick={() => onItemClick && onItemClick(acc, 'accommodation')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false)}
                          >
                            <div style={{ width: '100%', height: imgH + 'px', overflow: 'hidden', background: '#f5f3ef', flexShrink: 0 }}>
                              {acc.image && <img src={acc.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={e => { e.target.style.display = 'none'; }} />}
                            </div>
                            <div style={{ padding: '8px 10px', flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '3px', flexShrink: 0 }}>
                                🏨 {L('accommodation', lang)}
                                {acc.stars > 0 && <span style={{ color: '#e9b200', marginLeft: '4px', letterSpacing: '1px' }}>{'★'.repeat(acc.stars)}</span>}
                              </div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#37352f', marginBottom: '3px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flexShrink: 0 }}>
                                {getDisplayName(acc, lang)}
                                <RedNoteLink name={acc.name_local || acc.name_base} />
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.6, flexShrink: 0 }}>
                                {acc.check_in && <div>{L('checkin', lang)}: {acc.check_in}{acc.check_out ? ' · ' + L('checkout', lang) + ': ' + acc.check_out : ''}</div>}
                                {acc.cost > 0 && <div>{fmtCost(acc.cost, undefined, lang)}</div>}
                                {getDisplayField(acc, 'type', lang) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getDisplayField(acc, 'type', lang)}</div>}
                                {(acc.location_base || acc.location_local) && <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}><MapLink item={acc} lang={lang} mapProvider={mapProvider} /></div>}
                              </div>
                              <div style={{ fontSize: '11px', color: '#9b9a97', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginTop: '3px' }}>
                                {lang === 'local' && acc.notes_local ? acc.notes_local : acc.notes_base}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </Section>
              )}

              {/* Transportation */}
              {(day.transportation || (day.intra_routes && day.intra_routes.length > 0)) && (
                <Section title={L('transportation', lang)} icon={(day.transportation && day.transportation.icon) || '✈️'}>
                  <div style={categoryRowStyle}>
                    <div style={scrollContainerStyle} className="category-scroll-container">
                      {[...(day.transportation ? [day.transportation] : []), ...(day.intra_routes || [])].map((tr, i) => {
                        const catColor = categoryColors.transportation;
                        return (
                          <div key={i} style={{...cardStyle(catColor, false), height: 'auto', minHeight: sm ? '160px' : '180px'}}
                            onClick={() => onItemClick && onItemClick(tr, 'transportation')}
                            onMouseEnter={hoverOn}
                            onMouseLeave={e => hoverOff(e, catColor, false)}
                          >
                            <div style={{ padding: '12px 14px', flex: 1 }}>
                              <div style={{ fontSize: '10px', fontWeight: '700', color: catColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
                                {tr.icon} {L('transportation', lang)}
                              </div>
                              <div style={{ fontSize: '14px', fontWeight: '600', color: '#37352f', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                {lang === 'local' && tr.from_local ? tr.from_local : tr.from_base}
                                {' → '}
                                {lang === 'local' && tr.to_local ? tr.to_local : tr.to_base}
                              </div>
                              <div style={{ fontSize: '11px', color: '#6b6b6b', lineHeight: 1.7 }}>
                                {tr.time && <div>{tr.time.start} – {tr.time.end}</div>}
                                {(tr.cost > 0 || tr.cost_type_base === 'prepaid') && <div>{fmtCost(tr.cost, tr.cost_type_base, lang)}</div>}
                                {getDisplayField(tr, 'type', lang) && <div>{getDisplayField(tr, 'type', lang)}</div>}
                                {getDisplayField(tr, 'company', lang) && <div>{getDisplayField(tr, 'company', lang)}</div>}
                                {tr.route_number && <div>{tr.route_number}</div>}
                              </div>
                              {getDisplayField(tr, 'status', lang) && (
                                <div style={{ marginTop: '4px' }}>
                                  <span style={{
                                    padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '600',
                                    background: tr.status_base?.includes('URGENT') ? '#fff4e6' : tr.status_base?.includes('VERIFIED') ? '#e9f5ec' : '#edf2fc',
                                    color: tr.status_base?.includes('URGENT') ? '#d97706' : tr.status_base?.includes('VERIFIED') ? '#1a7a32' : '#2b63b5'
                                  }}>
                                    {getDisplayField(tr, 'status', lang)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </Section>
              )}

              {/* Budget */}
              <Section title={L('budget', lang)} icon="💰">
                <div style={{
                  background: '#fff', borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.03)',
                  padding: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: sm ? 'center' : 'center', gap: '20px', flexDirection: sm ? 'column' : 'row' }}>
                    <Donut budget={day.budget} size={sm ? 72 : 88} onBudgetClick={onBudgetClick} day={day} />
                    <div style={{ fontSize: '13px', color: '#6b6b6b', lineHeight: 2, flex: 1, width: '100%' }}>
                      {[
                        { k: 'meals', l: L('meals', lang), c: '#f0b429' },
                        { k: 'attractions', l: L('attractions', lang), c: '#4a90d9' },
                        { k: 'entertainment', l: L('entertainment', lang), c: '#9b6dd7' },
                        { k: 'accommodation', l: L('accommodation', lang), c: '#45b26b' },
                        { k: 'shopping', l: L('shopping', lang), c: '#e07c5a' },
                        { k: 'cafe', l: L('cafe', lang), c: '#D4A574' },
                        { k: 'transportation', l: L('transport', lang), c: '#0ea5e9' }
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
                          <span style={{ fontWeight: '600', color: '#37352f' }}>{fmtCost(day.budget[r.k], undefined, lang)}</span>
                        </div>
                      ))}
                      <div style={{ borderTop: '1px solid #edece9', marginTop: '8px', paddingTop: '8px', fontWeight: '700', color: '#37352f', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{L('total', lang)}</span><span>{CURRENCY_SYMBOL}{day.budget.total.toFixed(0)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Section>
            </>
          );
        })()}

      </div>
    </div>
  );
};

// ============================================================
// TIMELINE OVERLAP DETECTION UTILITIES
// ============================================================

/**
 * Convert "HH:MM" to minutes since midnight for comparison
 */
const timeToMinutes = (timeStr) => {
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
};

/**
 * Check if two events overlap in time
 */
const eventsOverlap = (event1, event2) => {
  const start1 = timeToMinutes(event1.time.start);
  const end1 = timeToMinutes(event1.time.end);
  const start2 = timeToMinutes(event2.time.start);
  const end2 = timeToMinutes(event2.time.end);
  // Events overlap if one starts before the other ends
  return start1 < end2 && start2 < end1;
};

/**
 * Compute column layout for all events (Google Calendar style)
 * Uses greedy column assignment algorithm
 */
const computeColumnLayout = (entries) => {
  const entriesWithMinutes = entries.map(e => ({
    ...e,
    _startMin: timeToMinutes(e.time.start),
    _endMin: timeToMinutes(e.time.end)
  }));

  // Check if two events overlap using cached minutes
  const overlaps = (e1, e2) => {
    return (e1._startMin < e2._endMin) && (e2._startMin < e1._endMin);
  };

  // Greedy column assignment
  const result = [];
  for (let i = 0; i < entriesWithMinutes.length; i++) {
    const entry = entriesWithMinutes[i];
    const conflictingEntries = result.filter(e => overlaps(e, entry));
    const occupiedCols = new Set(conflictingEntries.map(e => e._column));

    let column = 0;
    while (occupiedCols.has(column)) column++;

    entry._column = column;
    result.push(entry);
  }

  // Calculate maxColumns for each conflict group
  for (let i = 0; i < result.length; i++) {
    const entry = result[i];
    const conflictingEntries = result.filter(e => overlaps(e, entry));
    const maxCol = Math.max(entry._column, ...conflictingEntries.map(e => e._column));
    entry._maxColumns = maxCol + 1;
  }

  return result;
};

// ============================================================
// TIMELINE VIEW
// ============================================================
const TimelineView = ({ day, bp, lang, mapProvider, onItemClick }) => {
  // Fix #6: Add z-index state for click handling of overlapping items
  const [topItemIndex, setTopItemIndex] = useState(null);
  const sm = bp === 'sm';
  const px = sm ? '16px' : bp === 'md' ? '32px' : '48px';
  const timeW = sm ? '48px' : '62px';

  const entries = [];
  const add = (item, type, label) => {
    // Only add if item has valid time with start and end
    // Filter out degenerate times: 00:00-00:00 (N/A items) and same start/end
    if (item?.time?.start && item?.time?.end
        && item.time.start !== '00:00'
        && item.time.end !== '00:00'
        && timeToMinutes(item.time.start) !== timeToMinutes(item.time.end)) {
      const e = { ...item, _type: type, _label: label };
      entries.push(e);
      return e;
    }
  };
  // Add transportation if exists (Fix Issue #8, #9: bilingual label respects lang toggle)
  if (day.transportation) {
    const tFrom = lang === 'local' && day.transportation.from_local ? day.transportation.from_local : day.transportation.from_base;
    const tTo = lang === 'local' && day.transportation.to_local ? day.transportation.to_local : day.transportation.to_base;
    add(day.transportation, 'transportation', `${tFrom} → ${tTo}`);
  }
  day.intra_routes?.forEach(r => {
    const label = (lang === 'local' && r.name_local) ? r.name_local : (r.name_base || r.route_number || '');
    add(r, 'transportation', label);
  });
  ['breakfast', 'brunch', 'lunch', 'dinner'].forEach(mealType => {
    const catKey = 'cat_' + mealType;
    const primary = day.meals?.[mealType];
    if (primary) {
      add(primary, 'meal', L(catKey, lang));
    }
  });
  day.attractions?.forEach(a => add(a, 'attraction', L('cat_attraction', lang)));
  day.entertainment?.forEach(e => add(e, 'entertainment', L('cat_entertainment', lang)));
  // Root cause fix: shopping items were missing from timeline - add them here
  day.shopping?.forEach(s => add(s, 'shopping', L('cat_shopping', lang)));
  day.cafe?.forEach(c => add(c, 'cafe', L('cat_cafe', lang)));
  // Fix issue #6: Add travel segments from timeline (includes return-to-hotel segment)
  day.travel_segments?.forEach(t => {
    const label = lang === 'local' && t.name_local ? t.name_local : (t.name_base || '');
    add(t, 'travel', label);
  });
  // Accommodation check-in: start after last activity/travel segment ends
  if (day.accommodation) {
    const accEntry = add(day.accommodation, 'accommodation', L('cat_checkin', lang));
    if (accEntry) {
      let latestEnd = 0;
      entries.forEach(e => {
        if (e._type !== 'accommodation') {
          const m = timeToMinutes(e.time.end);
          if (m > latestEnd) latestEnd = m;
        }
      });
      if (latestEnd > 0 && latestEnd >= timeToMinutes(accEntry.time.start)) {
        const startH = String(Math.floor(latestEnd / 60)).padStart(2, '0');
        const startM = String(latestEnd % 60).padStart(2, '0');
        const endMins = latestEnd + 30;
        const endH = String(Math.floor(endMins / 60)).padStart(2, '0');
        const endM = String(endMins % 60).padStart(2, '0');
        accEntry.time = { ...accEntry.time, start: startH + ':' + startM, end: endH + ':' + endM };
      }
    }
  }

  // Sort by start time
  entries.sort((a, b) => { const cmp = a.time.start.localeCompare(b.time.start); if (cmp !== 0) return cmp; const order = {transportation:0, travel:1, meal:2, attraction:3, cafe:4, entertainment:5, shopping:6, accommodation:7}; return (order[a._type] ?? 99) - (order[b._type] ?? 99); });

  // Deduplicate: for optional entertainment/shopping items sharing the same time slot
  // as another entry, keep only the first (primary) one in timeline view
  const seen = new Set();
  const deduped1 = entries.filter(e => {
    const slot = e.time.start + '-' + e.time.end;
    const name = e.name_base || e.title || e._label || '';
    const key = slot + ':' + e._type + ':' + name;
    if (e.optional && seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  // Cross-category dedup: same name_local on same day keeps highest-priority category only
  const typePriority = {transportation:0, meal:1, attraction:2, shopping:3, entertainment:4, accommodation:5, travel:6};
  const seenNames = {};
  const deduped = deduped1.filter(e => {
    const name = e.name_local || e.name_base || e.title || e._label || '';
    if (!name) return true;
    const prev = seenNames[name];
    if (!prev) { seenNames[name] = e; return true; }
    const prevP = typePriority[prev._type] ?? 99;
    const curP = typePriority[e._type] ?? 99;
    if (curP < prevP) { seenNames[name] = e; return true; }
    return false;
  });

  // Compute column layout for overlapping events
  const entriesWithLayout = computeColumnLayout(deduped);

  const firstH = entriesWithLayout.length ? (parseInt(entriesWithLayout[0].time.start) || 8) : 8;
  const lastH = entriesWithLayout.length
    ? Math.min(Math.max(...entriesWithLayout.map(e => parseInt(e.time.end) || (parseInt(e.time.start) + 1) || 9)), 24)
    : 20;
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

  const top = (t) => { const [h, m] = t.split(':').map(Number); return Math.max(0, (h - firstH) * hH + (m / 60) * hH); };
  const rawHgt = (s, e) => top(e) - top(s);

  // Apple Calendar style: 10-minute minimum height for clickability
  // Activities < 10 min get fixed 24px height (clickable), >= 10 min scale proportionally
  const hgt = (s, e) => {
    const raw = rawHgt(s, e);
    const durationMin = (raw / hH) * 60;  // Convert to minutes

    // < 10 minutes: fixed minimum clickable height
    if (durationMin < 10) {
      return 24;  // Minimum clickable height (≈ 2 small text lines)
    }

    // >= 10 minutes: proportional height, but not smaller than 24px
    return Math.max(raw, 24);
  };

  // Apple Calendar style: Font scaling calculation
  const calculateFontScale = (height) => {
    const fullSizeThreshold = 52;  // Height for full two-row display

    if (height >= fullSizeThreshold) {
      return 1.0;  // 100% standard font
    }

    // Linear scaling: smooth transition from 52px to 24px
    const minHeight = 24;
    const scale = (height - 8) / (fullSizeThreshold - 8);  // 8px for padding

    // Minimum scale 0.57 (14px * 0.57 ≈ 8px, still readable)
    return Math.max(scale, 0.57);
  };

  // Debug: log entries count
  if (entriesWithLayout.length === 0) {
    console.warn('Timeline has no entries for day:', day.day, day.location_base);
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
            {dayLabel(day, lang)}
          </h2>
        </div>

        {entriesWithLayout.length === 0 ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9b9a97' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏰</div>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>{L('no_timeline', lang)}</div>
            <div style={{ fontSize: '13px' }}>{L('no_timeline_sub', lang)}</div>
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

          <div style={{
            flex: 1,
            position: 'relative',
            borderLeft: '1px dashed #e5e4e1',
            minWidth: 0
          }}>
            {hours.map(h => <div key={h} style={{ height: hH, borderBottom: '1px solid #f5f5f3' }} />)}

            {entriesWithLayout.map((entry, i) => {
              const st = typeStyle[entry._type] || typeStyle.attraction;
              const t = top(entry.time.start);
              const entryH = hgt(entry.time.start, entry.time.end);

              // Column-based positioning for overlapping events
              const hasColumns = entry._maxColumns > 1;
              const colWidth = hasColumns ? (100 / entry._maxColumns) : 100;
              const colLeft = hasColumns ? (entry._column * colWidth) : 0;

              // Apple Calendar style: Calculate adaptive font scaling
              const fontScale = calculateFontScale(entryH);
              const baseTitleSize = sm ? 12 : 14;
              const baseTimeSize = 11;
              const baseDetailSize = 11;

              const titleFontSize = `${baseTitleSize * fontScale}px`;
              const timeFontSize = `${baseTimeSize * fontScale}px`;
              const detailFontSize = `${baseDetailSize * fontScale}px`;

              // Content display thresholds (based on scaled font)
              const showTitle = entryH >= 14;   // At least one line of title (14px * 0.57 ≈ 8px)
              const showTime = entryH >= 24;    // At least title + time (two lines)
              const showDetails = entryH >= 52; // Full height for details

              // Fix #6: Use dynamic z-index based on click state
              const isTop = topItemIndex === i;
              const zIdx = isTop ? 10 : 2;
              return (
                <div key={i} style={{
                  position: 'absolute',
                  top: t,
                  left: hasColumns ? `calc(10px + ${colLeft}%)` : '10px',
                  width: hasColumns ? `calc(${colWidth}% - 12px)` : 'calc(100% - 20px)',
                  height: entryH - 4,
                  background: st.bg, borderLeft: `3px ${(entry.optional || entry._isAlternative) ? 'dashed' : 'solid'} ${st.border}`,
                  borderRadius: '6px',
                  padding: sm ? '4px 6px' : '6px 8px',  // Smaller padding for scaled fonts
                  display: 'flex',
                  gap: '6px',
                  alignItems: 'flex-start',
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

                  {/* Apple Calendar style: Image only for full-height entries */}
                  {entry.image && !sm && showDetails && (
                    <div style={{ width: '50px', height: '50px', borderRadius: '6px', overflow: 'hidden', flexShrink: 0 }}>
                      <img src={entry.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
                    </div>
                  )}

                  <div style={{ flex: 1, minWidth: 0 }}>
                    {/* Time row (>= 24px) */}
                    {showTime && (
                      <div style={{ fontSize: timeFontSize, color: '#b4b4b4', lineHeight: 1.2 }}>
                        {entry.time.start} – {entry.time.end}
                      </div>
                    )}

                    {/* Title row (>= 14px) */}
                    {showTitle && (
                      <div style={{
                        fontSize: titleFontSize,
                        fontWeight: '600',
                        color: '#37352f',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        lineHeight: 1.2
                      }}>
                        {entry._type === 'transportation' || entry._type === 'travel' ? (
                          <span>{entry._type === 'transportation' ? entry.icon : (entry.icon || '🚶')} {entry._label}{entry.duration ? ` (${entry.duration})` : ''}</span>
                        ) : (
                          <span>{entry._label}: {getDisplayName(entry, lang)}</span>
                        )}
                        {(entry.optional || entry._isAlternative) && showDetails && (
                          <span style={{
                            fontSize: `${9 * fontScale}px`,
                            padding: '1px 4px',
                            background: entry._isAlternative ? '#edf2fc' : '#f5f5f3',
                            borderRadius: '3px',
                            color: entry._isAlternative ? '#2b63b5' : '#9b9a97',
                            marginLeft: '4px',
                            verticalAlign: 'middle'
                          }}>
                            {entry._isAlternative ? (lang === 'local' ? '备选' : 'Alt') : L('optional', lang)}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Details row (>= 52px) */}
                    {showDetails && (entry._type === 'transportation' ? (
                      <div style={{ fontSize: detailFontSize, color: '#9b9a97', marginTop: '2px', lineHeight: 1.3 }}>
                        <div>{lang === 'local' && entry.departure_point_local ? entry.departure_point_local : entry.departure_point_base} → {lang === 'local' && entry.arrival_point_local ? entry.arrival_point_local : entry.arrival_point_base}</div>
                        {entry.route_number && entry.route_number !== 'VERIFIED' && (
                          <div>{lang === 'local' && entry.type_local ? entry.type_local : entry.type_base} {entry.route_number}</div>
                        )}
                        {entry.status_base && (
                          <span style={{
                            display: 'inline-block',
                            marginTop: '2px',
                            padding: '2px 4px',
                            borderRadius: '3px',
                            fontSize: `${9 * fontScale}px`,
                            fontWeight: '600',
                            background: entry.status_base?.includes('URGENT') ? '#fff4e6' :
                                       entry.status_base?.includes('VERIFIED') ? '#e9f5ec' : '#edf2fc',
                            color: entry.status_base?.includes('URGENT') ? '#d97706' :
                                  entry.status_base?.includes('VERIFIED') ? '#1a7a32' : '#2b63b5'
                          }}>
                            {lang === 'local' && entry.status_local ? entry.status_local : entry.status_base}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: detailFontSize, color: '#9b9a97', flexWrap: 'wrap', marginTop: '2px', lineHeight: 1.3 }}>
                        {entry.recommended_duration && <span>⏱ {entry.recommended_duration}</span>}
                        {entry.cost !== undefined && Number(entry.cost) > 0 && (
                          <span style={{
                            padding: '1px 4px', borderRadius: '3px', fontWeight: '600',
                            background: '#f5f5f3',
                            color: '#37352f'
                          }}>
                            {fmtCost(entry.cost, undefined, lang)}
                          </span>
                        )}
                        {entry.stars > 0 && <span style={{ color: '#e9b200' }}>{'★'.repeat(entry.stars)}</span>}
                      </div>
                    ))}
                    {showDetails && entry._type !== 'transportation' && <LinksRow links={entry.links} compact={sm} />}
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
    } else if (category === 'cafe') {
      items = dayData.cafe || [];
      total = dayData.budget.cafe || 0;
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
        lang={lang}
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
              {m === 'kanban' ? L('kanban_view', lang) : L('timeline_view', lang)}
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
            <div style={{ marginTop: '4px' }}>{L('coming_soon', lang)}</div>
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
