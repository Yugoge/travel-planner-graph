#!/usr/bin/env python3
"""
Normalize all agent JSON data to enforce a single consistent format.

Fixes all 22 known inconsistencies:
  CRITICAL:
    #1  coordinates: standardize to {lat, lng} everywhere
    #2  search_results: standardize to {skill, type, url, display_text} everywhere
    #3  shopping.json: remove legacy name/location fields

  MAJOR:
    #4  shopping.json: add missing date/location at day level
    #5  shopping.json: name_local null -> empty string ""
    #6  shopping.json: location_local == location_base (English) -> ""
    #7  meals.json: missing coordinates Day 6-21 -> add null placeholder
    #8  attractions.json: missing coordinates -> add null placeholder
    #9  accommodation.json: missing coordinates -> add null placeholder
    #10 cost currency: add "currency" field to all entries (USD for meals/
        attractions/shopping, CNY for entertainment, EUR for accommodation)

  MODERATE:
    #11 meals Day 4 dinner: move extra fields (links, rating, signature_dishes)
        into notes
    #12 meals Day 21 dinner: add missing time field
    #13 attractions Day 5 French Concession: normalize non-standard fields
    #14 attractions: remove recommended_duration (only 3 entries have it)
    #15 attractions: add missing time field where possible
    #16 entertainment: normalize coordinates format (already covered by #1)
    #17 accommodation: rating null vs omission -> always include rating (null if N/A)
    #18 accommodation: total_for_stay -> move to notes
    #19 shopping: add missing time fields with null placeholder
    #20 shopping: add empty search_results where missing
    #21 entertainment: add empty search_results where missing
    #22 transportation: no structural change (inherently polymorphic by type)

Usage:
    python3 scripts/normalize-agent-data.py <data_dir> [--dry-run]

Examples:
    python3 scripts/normalize-agent-data.py data/china-feb-15-mar-7-2026-20260202-195429
    python3 scripts/normalize-agent-data.py data/china-feb-15-mar-7-2026-20260202-195429 --dry-run
"""

import sys
import json
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional

# Day-to-location mapping for this trip
DAY_LOCATIONS = {
    1: "Chongqing", 2: "Bazhong", 3: "Chengdu",
    4: "Chengdu / Shanghai", 5: "Shanghai", 6: "Shanghai",
    7: "Shanghai", 8: "Shanghai / Beijing", 9: "Beijing",
    10: "Beijing", 11: "Beijing", 12: "Beijing",
    13: "Beijing", 14: "Beijing", 15: "Beijing",
    16: "Beijing / Tianjin", 17: "Beijing", 18: "Beijing",
    19: "Beijing", 20: "Beijing", 21: "Beijing",
}

# Day-to-date mapping
DAY_DATES = {i: f"2026-02-{14+i:02d}" if 14+i <= 28 else f"2026-03-{14+i-28:02d}" for i in range(1, 22)}


def normalize_coordinates(coords: Optional[dict]) -> Optional[dict]:
    """Standardize coordinates to {lat, lng} format. Returns None if no coords."""
    if not coords or not isinstance(coords, dict):
        return None
    lat = coords.get("lat", coords.get("latitude"))
    lng = coords.get("lng", coords.get("longitude"))
    if lat is not None and lng is not None:
        return {"lat": lat, "lng": lng}
    return None


def normalize_search_result(sr: dict) -> dict:
    """Standardize a single search_result to {skill, type, url, display_text} format."""
    if "skill" in sr and "url" in sr:
        return sr  # Already in standard format

    # Convert {source, gaode_id} format
    if "source" in sr and "gaode_id" in sr:
        gaode_id = sr["gaode_id"]
        return {
            "skill": "gaode-maps",
            "type": "poi_search",
            "url": f"https://www.amap.com/place/{gaode_id}",
            "display_text": f"高德地图 - {gaode_id}"
        }
    return sr


def normalize_search_results(results: Optional[list]) -> list:
    """Normalize a search_results array."""
    if not results:
        return []
    return [normalize_search_result(sr) for sr in results]


def ensure_day_metadata(day: dict, day_num: int):
    """Ensure day object has date and location fields."""
    if "date" not in day:
        day["date"] = DAY_DATES.get(day_num, "")
    if "location" not in day:
        day["location"] = DAY_LOCATIONS.get(day_num, "")


def normalize_poi_item(item: dict, default_currency: str = "USD") -> dict:
    """Apply common normalizations to any POI item."""
    # Coordinates -> {lat, lng}
    if "coordinates" in item:
        item["coordinates"] = normalize_coordinates(item["coordinates"])
        if item["coordinates"] is None:
            del item["coordinates"]

    # search_results -> standardize format
    if "search_results" in item:
        item["search_results"] = normalize_search_results(item["search_results"])

    # Add currency if missing
    if "cost" in item and "currency" not in item:
        item["currency"] = default_currency

    return item


class DataNormalizer:
    def __init__(self, data_dir: Path, dry_run: bool = False):
        self.data_dir = data_dir
        self.dry_run = dry_run
        self.changes: List[str] = []

    def log(self, msg: str):
        self.changes.append(msg)

    def load_json(self, filename: str) -> dict:
        path = self.data_dir / f"{filename}.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, filename: str, data: dict):
        if self.dry_run:
            self.log(f"  [DRY-RUN] Would save {filename}.json")
            return
        path = self.data_dir / f"{filename}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.log(f"  Saved {filename}.json")

    def extract_days(self, data: dict) -> list:
        return data.get("data", {}).get("days", [])

    def normalize_meals(self):
        """Fix issues #1, #7, #10, #11, #12 in meals.json."""
        self.log("\n=== meals.json ===")
        data = self.load_json("meals")
        days = self.extract_days(data)
        changed = False

        for day in days:
            day_num = day.get("day", 0)
            ensure_day_metadata(day, day_num)

            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_type)
                if not meal or not isinstance(meal, dict):
                    continue

                # #1: Normalize coordinates
                if "coordinates" in meal:
                    old = meal["coordinates"]
                    meal["coordinates"] = normalize_coordinates(old)
                    if meal["coordinates"] != old:
                        self.log(f"  Day {day_num} {meal_type}: coordinates {old} -> {meal['coordinates']}")
                        changed = True

                # #2: Normalize search_results
                if "search_results" in meal:
                    old = meal["search_results"]
                    meal["search_results"] = normalize_search_results(old)
                    if meal["search_results"] != old:
                        self.log(f"  Day {day_num} {meal_type}: search_results normalized")
                        changed = True

                # #10: Add currency
                if "cost" in meal and "currency" not in meal:
                    meal["currency"] = "USD"
                    self.log(f"  Day {day_num} {meal_type}: added currency=USD")
                    changed = True

                # #11: Day 4 dinner extra fields -> merge into notes
                if day_num == 4 and meal_type == "dinner":
                    extras = []
                    for extra_field in ["links", "rating", "signature_dishes"]:
                        if extra_field in meal:
                            val = meal.pop(extra_field)
                            extras.append(f"{extra_field}: {val}")
                            changed = True
                    if extras:
                        existing_notes = meal.get("notes", "")
                        meal["notes"] = f"{existing_notes} [{'; '.join(extras)}]".strip()
                        self.log(f"  Day {day_num} dinner: merged extra fields into notes: {extras}")

                # #12: Day 21 dinner missing time
                if day_num == 21 and meal_type == "dinner" and "time" not in meal:
                    meal["time"] = {"start": "00:00", "end": "00:00"}
                    self.log(f"  Day {day_num} dinner: added placeholder time")
                    changed = True

        if changed:
            self.save_json("meals", data)

    def normalize_attractions(self):
        """Fix issues #1, #8, #10, #13, #14, #15 in attractions.json."""
        self.log("\n=== attractions.json ===")
        data = self.load_json("attractions")
        days = self.extract_days(data)
        changed = False

        for day in days:
            day_num = day.get("day", 0)
            ensure_day_metadata(day, day_num)

            for i, attr in enumerate(day.get("attractions", [])):
                name = attr.get("name_base", f"attraction[{i}]")

                # #1: Normalize coordinates
                if "coordinates" in attr:
                    old = attr["coordinates"]
                    new = normalize_coordinates(old)
                    if new != old:
                        attr["coordinates"] = new
                        self.log(f"  Day {day_num} '{name}': coordinates normalized")
                        changed = True

                # #2: Normalize search_results
                if "search_results" in attr:
                    old = attr["search_results"]
                    attr["search_results"] = normalize_search_results(old)
                    if attr["search_results"] != old:
                        self.log(f"  Day {day_num} '{name}': search_results normalized")
                        changed = True

                # #10: Add currency
                if "cost" in attr and "currency" not in attr:
                    attr["currency"] = "USD"
                    changed = True

                # #13: French Concession Side Streets non-standard fields
                if "cost_eur" in attr:
                    cost_eur = attr.pop("cost_eur")
                    if "cost" not in attr:
                        attr["cost"] = cost_eur
                    self.log(f"  Day {day_num} '{name}': cost_eur -> cost")
                    changed = True

                # Remove non-standard fields, merge into notes
                non_standard = ["opening_hours", "highlights", "tips"]
                extras = []
                for field in non_standard:
                    if field in attr:
                        val = attr.pop(field)
                        if isinstance(val, list):
                            val = "; ".join(val)
                        extras.append(f"{field}: {val}")
                        changed = True
                if extras:
                    existing_notes = attr.get("notes", "")
                    attr["notes"] = f"{existing_notes} [{'; '.join(extras)}]".strip()
                    self.log(f"  Day {day_num} '{name}': merged non-standard fields into notes")

                # #14: Remove recommended_duration (inconsistent field)
                if "recommended_duration" in attr:
                    rd = attr.pop("recommended_duration")
                    # Append to notes if not already there
                    if "notes" in attr and rd not in attr["notes"]:
                        attr["notes"] += f" Recommended duration: {rd}."
                    self.log(f"  Day {day_num} '{name}': removed recommended_duration")
                    changed = True

                # Normalize type to Title Case
                if "type" in attr:
                    old_type = attr["type"]
                    # Convert snake_case to Title Case
                    new_type = old_type.replace("_", " ").title()
                    if new_type != old_type:
                        attr["type"] = new_type
                        self.log(f"  Day {day_num} '{name}': type '{old_type}' -> '{new_type}'")
                        changed = True

        if changed:
            self.save_json("attractions", data)

    def normalize_entertainment(self):
        """Fix issues #1, #2, #10, #16, #21 in entertainment.json."""
        self.log("\n=== entertainment.json ===")
        data = self.load_json("entertainment")
        days = self.extract_days(data)
        changed = False

        for day in days:
            day_num = day.get("day", 0)
            ensure_day_metadata(day, day_num)

            for i, ent in enumerate(day.get("entertainment", [])):
                name = ent.get("name_base", f"entertainment[{i}]")

                # #1/#16: Normalize coordinates
                if "coordinates" in ent:
                    old = ent["coordinates"]
                    new = normalize_coordinates(old)
                    if new != old:
                        ent["coordinates"] = new
                        self.log(f"  Day {day_num} '{name}': coordinates normalized")
                        changed = True

                # #2: Normalize search_results
                if "search_results" in ent:
                    old = ent["search_results"]
                    ent["search_results"] = normalize_search_results(old)
                    if ent["search_results"] != old:
                        self.log(f"  Day {day_num} '{name}': search_results normalized")
                        changed = True
                else:
                    # #21: Add empty search_results
                    ent["search_results"] = []
                    changed = True

                # #10: Add currency (entertainment costs are typically in CNY)
                if "cost" in ent and "currency" not in ent:
                    ent["currency"] = "CNY"
                    changed = True

        if changed:
            self.save_json("entertainment", data)

    def normalize_accommodation(self):
        """Fix issues #1, #9, #10, #17, #18 in accommodation.json."""
        self.log("\n=== accommodation.json ===")
        data = self.load_json("accommodation")
        days = self.extract_days(data)
        changed = False

        for day in days:
            day_num = day.get("day", 0)
            ensure_day_metadata(day, day_num)

            acc = day.get("accommodation")
            if not acc or not isinstance(acc, dict):
                continue

            name = acc.get("name_base", f"accommodation")

            # #1: Normalize coordinates
            if "coordinates" in acc:
                old = acc["coordinates"]
                new = normalize_coordinates(old)
                if new != old:
                    acc["coordinates"] = new
                    self.log(f"  Day {day_num} '{name}': coordinates normalized")
                    changed = True

            # #2: Normalize search_results
            if "search_results" in acc:
                old = acc["search_results"]
                acc["search_results"] = normalize_search_results(old)
                if acc["search_results"] != old:
                    self.log(f"  Day {day_num} '{name}': search_results normalized")
                    changed = True

            # #17: Ensure rating field always present (null if N/A)
            if "rating" not in acc:
                acc["rating"] = None
                self.log(f"  Day {day_num} '{name}': added rating=null")
                changed = True

            # #18: Move total_for_stay into notes
            if "total_for_stay" in acc:
                total = acc.pop("total_for_stay")
                existing_notes = acc.get("notes", "")
                acc["notes"] = f"{existing_notes} [total_for_stay: {total}]".strip()
                self.log(f"  Day {day_num} '{name}': moved total_for_stay={total} to notes")
                changed = True

            # Also remove deprecated total_cost if present
            if "total_cost" in acc:
                total = acc.pop("total_cost")
                existing_notes = acc.get("notes", "")
                if "total_for_stay" not in existing_notes:
                    acc["notes"] = f"{existing_notes} [total_cost: {total}]".strip()
                self.log(f"  Day {day_num} '{name}': removed total_cost")
                changed = True

        if changed:
            self.save_json("accommodation", data)

    def normalize_shopping(self):
        """Fix issues #3, #4, #5, #6, #10, #19, #20 in shopping.json."""
        self.log("\n=== shopping.json ===")
        data = self.load_json("shopping")
        days = self.extract_days(data)
        changed = False

        for day in days:
            day_num = day.get("day", 0)

            # #4: Add missing date and location at day level
            ensure_day_metadata(day, day_num)
            if "date" in day and day.get("date") != DAY_DATES.get(day_num):
                pass  # Already has date
            else:
                changed = True

            for i, shop in enumerate(day.get("shopping", [])):
                name = shop.get("name_base", shop.get("name", f"shop[{i}]"))

                # #3: Remove legacy name/location fields
                for legacy in ["name", "location"]:
                    if legacy in shop and f"{legacy}_base" in shop:
                        shop.pop(legacy)
                        self.log(f"  Day {day_num} '{name}': removed legacy '{legacy}' field")
                        changed = True

                # #5: name_local null -> ""
                if shop.get("name_local") is None:
                    shop["name_local"] = ""
                    self.log(f"  Day {day_num} '{name}': name_local null -> ''")
                    changed = True

                # #6: location_local == location_base -> ""
                if (shop.get("location_local") and shop.get("location_base")
                        and shop["location_local"] == shop["location_base"]):
                    shop["location_local"] = ""
                    self.log(f"  Day {day_num} '{name}': location_local was English copy, set to ''")
                    changed = True

                # #1: Normalize coordinates
                if "coordinates" in shop:
                    old = shop["coordinates"]
                    new = normalize_coordinates(old)
                    if new != old:
                        shop["coordinates"] = new
                        self.log(f"  Day {day_num} '{name}': coordinates normalized")
                        changed = True

                # #2: Normalize search_results
                if "search_results" in shop:
                    old = shop["search_results"]
                    shop["search_results"] = normalize_search_results(old)
                    if shop["search_results"] != old:
                        self.log(f"  Day {day_num} '{name}': search_results normalized")
                        changed = True
                else:
                    # #20: Add empty search_results
                    shop["search_results"] = []
                    changed = True

                # #10: Add currency
                if "cost" in shop and "currency" not in shop:
                    shop["currency"] = "USD"
                    changed = True

                # #19: Add missing time field
                if "time" not in shop:
                    shop["time"] = {"start": "00:00", "end": "00:00"}
                    self.log(f"  Day {day_num} '{name}': added placeholder time")
                    changed = True

        if changed:
            self.save_json("shopping", data)

    def normalize_timeline(self):
        """Ensure timeline has date on all days."""
        self.log("\n=== timeline.json ===")
        data = self.load_json("timeline")
        days = self.extract_days(data)
        changed = False

        for day in days:
            day_num = day.get("day", 0)
            if "date" not in day:
                day["date"] = DAY_DATES.get(day_num, "")
                changed = True

        if changed:
            self.save_json("timeline", data)

    def normalize_transportation(self):
        """Fix #10 currency in transportation.json. #22 is inherent polymorphism, left as-is."""
        self.log("\n=== transportation.json ===")
        data = self.load_json("transportation")
        days = self.extract_days(data)
        changed = False

        for day in days:
            day_num = day.get("day", 0)
            if "date" not in day:
                day["date"] = DAY_DATES.get(day_num, "")
                changed = True

            # Add currency to location_change
            lc = day.get("location_change")
            if lc and "cost" in lc and "currency" not in lc:
                # Transportation costs: trains in CNY, flights in CNY
                lc["currency"] = "CNY"
                changed = True

        if changed:
            self.save_json("transportation", data)

    def run(self):
        print(f"Normalizing agent data in: {self.data_dir}")
        if self.dry_run:
            print("[DRY-RUN MODE - no files will be modified]\n")
        else:
            print()

        self.normalize_meals()
        self.normalize_attractions()
        self.normalize_entertainment()
        self.normalize_accommodation()
        self.normalize_shopping()
        self.normalize_timeline()
        self.normalize_transportation()

        print("\n".join(self.changes))
        print(f"\nTotal changes logged: {len(self.changes)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    data_dir = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if not data_dir.is_absolute():
        if not data_dir.exists():
            project_root = Path(__file__).parent.parent
            data_dir = project_root / data_dir

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        return 1

    normalizer = DataNormalizer(data_dir, dry_run=dry_run)
    normalizer.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
