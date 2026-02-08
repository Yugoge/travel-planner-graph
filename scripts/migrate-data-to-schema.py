#!/usr/bin/env python3
"""
Migrate agent data to conform to JSON Schema contracts.

Scans all agent JSON files in a plan's data directory and fixes:
  1. Missing name_base/name_local (from name, name_cn, name_chinese, name_english)
  2. Missing location_base/location_local (from location, address)
  3. Missing duration_minutes (from recommended_duration, recommended_duration_hours)
  4. Missing cost (from cost_cny, ticket_price_eur, price_per_night_eur)
  5. Missing type (from category)
  6. Normalizes coordinates format
  7. Adds currency field where detectable

Usage:
    python3 scripts/migrate-data-to-schema.py <plan-id>
    python3 scripts/migrate-data-to-schema.py <plan-id> --dry-run
    python3 scripts/migrate-data-to-schema.py --all
    python3 scripts/migrate-data-to-schema.py --all --dry-run
"""

import json
import sys
import re
from pathlib import Path
from copy import deepcopy


class DataMigrator:
    """Migrate agent data to conform to JSON Schema contracts."""

    def __init__(self, data_dir: Path, dry_run: bool = False):
        self.data_dir = data_dir
        self.dry_run = dry_run
        self.fixes = []
        self.errors = []

    def run(self):
        """Execute all migrations."""
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Migrating: {self.data_dir.name}")

        self._migrate_meals()
        self._migrate_attractions()
        self._migrate_entertainment()
        self._migrate_accommodation()
        self._migrate_shopping()
        self._migrate_transportation()

        print(f"  Total fixes: {len(self.fixes)}")
        if self.errors:
            print(f"  Errors: {len(self.errors)}")
            for e in self.errors:
                print(f"    {e}")
        return len(self.fixes)

    def _load(self, filename: str) -> dict:
        path = self.data_dir / filename
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, filename: str, data: dict):
        if self.dry_run:
            return
        path = self.data_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _extract_days(self, data: dict) -> list:
        if "data" in data and isinstance(data["data"], dict):
            return data["data"].get("days", [])
        return data.get("days", [])

    def _set_days(self, data: dict, days: list):
        if "data" in data and isinstance(data["data"], dict):
            data["data"]["days"] = days
        else:
            data["days"] = days

    def _fix_bilingual_name(self, item: dict, agent: str, day_num: int) -> bool:
        """Ensure name_base and name_local exist."""
        changed = False

        if "name_base" not in item:
            # Try various legacy field names
            name = item.get("name", "")
            name_en = item.get("name_english", item.get("name_en", ""))
            name_cn = item.get("name_chinese", item.get("name_cn", item.get("name_local", "")))

            if name_en:
                item["name_base"] = name_en
            elif name:
                # Check if name contains both English and Chinese
                # Pattern: "English Name (中文名)" or "English Name"
                match = re.match(r'^([A-Za-z][\w\s\'-]+?)(?:\s*[(\uff08](.+?)[)\uff09])?\s*$', name)
                if match and match.group(2):
                    item["name_base"] = match.group(1).strip()
                    if not name_cn:
                        name_cn = match.group(2).strip()
                else:
                    item["name_base"] = name
            else:
                item["name_base"] = ""
                self.errors.append(f"[{agent}] Day {day_num}: no name found for item")

            if "name_local" not in item:
                item["name_local"] = name_cn if name_cn else None

            self.fixes.append(f"[{agent}] Day {day_num}: added name_base='{item.get('name_base', '')[:30]}'")
            changed = True

        elif "name_local" not in item:
            name_cn = item.get("name_chinese", item.get("name_cn", ""))
            item["name_local"] = name_cn if name_cn else None
            self.fixes.append(f"[{agent}] Day {day_num}: added name_local")
            changed = True

        return changed

    def _fix_bilingual_location(self, item: dict, agent: str, day_num: int) -> bool:
        """Ensure location_base and location_local exist."""
        changed = False

        if "location_base" not in item:
            loc = item.get("location", item.get("address", ""))
            item["location_base"] = loc
            self.fixes.append(f"[{agent}] Day {day_num}: added location_base")
            changed = True

        if "location_local" not in item:
            # Try to find Chinese location
            loc = item.get("location", item.get("address", ""))
            # If location contains Chinese characters, use it as local
            if loc and re.search(r'[\u4e00-\u9fff]', loc):
                item["location_local"] = loc
            else:
                item["location_local"] = item.get("location_base", loc)
            self.fixes.append(f"[{agent}] Day {day_num}: added location_local")
            changed = True

        return changed

    def _fix_duration(self, item: dict, agent: str, day_num: int) -> bool:
        """Ensure duration_minutes exists for attractions."""
        if "duration_minutes" in item:
            return False

        # Try to extract from other fields
        rec_dur = item.get("recommended_duration", "")
        rec_dur_h = item.get("recommended_duration_hours", 0)

        if rec_dur_h and isinstance(rec_dur_h, (int, float)):
            item["duration_minutes"] = int(rec_dur_h * 60)
            self.fixes.append(f"[{agent}] Day {day_num}: duration_minutes={item['duration_minutes']} from hours={rec_dur_h}")
            return True

        if rec_dur and isinstance(rec_dur, str):
            # Parse "1h", "1.5h", "2-3 hours", "30 minutes", "1.5 hours"
            h_match = re.search(r'(\d+\.?\d*)\s*h', rec_dur.lower())
            m_match = re.search(r'(\d+)\s*min', rec_dur.lower())
            if h_match:
                item["duration_minutes"] = int(float(h_match.group(1)) * 60)
                self.fixes.append(f"[{agent}] Day {day_num}: duration_minutes={item['duration_minutes']} from '{rec_dur}'")
                return True
            elif m_match:
                item["duration_minutes"] = int(m_match.group(1))
                self.fixes.append(f"[{agent}] Day {day_num}: duration_minutes={item['duration_minutes']} from '{rec_dur}'")
                return True

        # Default based on type
        item_type = item.get("type", "").lower()
        if "walk" in item_type or "stroll" in item_type:
            item["duration_minutes"] = 60
        elif "museum" in item_type or "gallery" in item_type:
            item["duration_minutes"] = 120
        else:
            item["duration_minutes"] = 90  # reasonable default
        self.fixes.append(f"[{agent}] Day {day_num}: duration_minutes={item['duration_minutes']} (default)")
        return True

    def _fix_cost(self, item: dict, agent: str, day_num: int, eur_rate: float = 8.0) -> bool:
        """Ensure cost field exists and is numeric."""
        changed = False

        if "cost" not in item:
            # Try EUR-based fields
            cost_eur = item.get("ticket_price_eur", item.get("price_per_night_eur", item.get("cost_eur", 0)))
            cost_cny = item.get("cost_cny", 0)

            if cost_eur and isinstance(cost_eur, (int, float)):
                item["cost"] = round(cost_eur * eur_rate, 2)
                item["currency"] = "CNY"
                self.fixes.append(f"[{agent}] Day {day_num}: cost={item['cost']} CNY from EUR={cost_eur}")
                changed = True
            elif cost_cny and isinstance(cost_cny, (int, float)):
                item["cost"] = cost_cny
                item["currency"] = "CNY"
                self.fixes.append(f"[{agent}] Day {day_num}: cost={item['cost']} from cost_cny")
                changed = True
            else:
                item["cost"] = 0
                self.fixes.append(f"[{agent}] Day {day_num}: cost=0 (no source found)")
                changed = True

        # Ensure cost is a number, not string
        if isinstance(item.get("cost"), str):
            try:
                item["cost"] = float(item["cost"])
                changed = True
            except ValueError:
                item["cost"] = 0
                changed = True

        return changed

    def _fix_type(self, item: dict, agent: str, day_num: int) -> bool:
        """Ensure type field exists."""
        if "type" in item:
            return False
        category = item.get("category", "")
        if category:
            item["type"] = category
            self.fixes.append(f"[{agent}] Day {day_num}: type='{category}' from category")
            return True
        item["type"] = "Other"
        self.fixes.append(f"[{agent}] Day {day_num}: type='Other' (default)")
        return True

    def _fix_search_results(self, item: dict, agent: str, day_num: int) -> bool:
        """Fix search_results entries missing required url field."""
        results = item.get("search_results", [])
        if not results:
            return False
        changed = False
        for sr in results:
            if isinstance(sr, dict) and "url" not in sr:
                sr["url"] = ""
                changed = True
        if changed:
            self.fixes.append(f"[{agent}] Day {day_num}: fixed search_results missing url")
        return changed

    def _migrate_poi_items(self, items: list, agent: str, day_num: int) -> bool:
        """Apply all POI fixes to a list of items."""
        changed = False
        for item in items:
            if not isinstance(item, dict):
                continue
            changed |= self._fix_bilingual_name(item, agent, day_num)
            changed |= self._fix_bilingual_location(item, agent, day_num)
            changed |= self._fix_cost(item, agent, day_num)
            changed |= self._fix_search_results(item, agent, day_num)
        return changed

    def _migrate_meals(self):
        data = self._load("meals.json")
        if not data:
            return
        days = self._extract_days(data)
        changed = False
        for day in days:
            day_num = day.get("day", "?")
            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_type)
                if not meal or not isinstance(meal, dict):
                    continue
                changed |= self._fix_bilingual_name(meal, f"meals.{meal_type}", day_num)
                changed |= self._fix_bilingual_location(meal, f"meals.{meal_type}", day_num)
                changed |= self._fix_cost(meal, f"meals.{meal_type}", day_num)
                changed |= self._fix_search_results(meal, f"meals.{meal_type}", day_num)
                # Ensure cuisine exists
                if "cuisine" not in meal:
                    meal["cuisine"] = meal.get("type", "Local")
                    changed = True
        if changed:
            self._save("meals.json", data)
            print(f"  meals.json: updated")

    def _migrate_attractions(self):
        data = self._load("attractions.json")
        if not data:
            return
        days = self._extract_days(data)
        changed = False
        for day in days:
            day_num = day.get("day", "?")
            attractions = day.get("attractions", [])
            for attr in attractions:
                if not isinstance(attr, dict):
                    continue
                changed |= self._fix_bilingual_name(attr, "attractions", day_num)
                changed |= self._fix_bilingual_location(attr, "attractions", day_num)
                changed |= self._fix_cost(attr, "attractions", day_num)
                changed |= self._fix_duration(attr, "attractions", day_num)
                changed |= self._fix_search_results(attr, "attractions", day_num)
                if "type" not in attr:
                    attr["type"] = "Attraction"
                    changed = True
        if changed:
            self._save("attractions.json", data)
            print(f"  attractions.json: updated")

    def _migrate_entertainment(self):
        data = self._load("entertainment.json")
        if not data:
            return
        days = self._extract_days(data)
        changed = False
        for day in days:
            day_num = day.get("day", "?")
            items = day.get("entertainment", [])
            changed |= self._migrate_poi_items(items, "entertainment", day_num)
            for item in items:
                if isinstance(item, dict) and "type" not in item:
                    item["type"] = "Entertainment"
                    changed = True
        if changed:
            self._save("entertainment.json", data)
            print(f"  entertainment.json: updated")

    def _migrate_accommodation(self):
        data = self._load("accommodation.json")
        if not data:
            return
        days = self._extract_days(data)
        changed = False
        for day in days:
            day_num = day.get("day", "?")
            acc = day.get("accommodation")
            if not acc or not isinstance(acc, dict):
                continue
            changed |= self._fix_bilingual_name(acc, "accommodation", day_num)
            changed |= self._fix_bilingual_location(acc, "accommodation", day_num)
            changed |= self._fix_cost(acc, "accommodation", day_num)
            changed |= self._fix_search_results(acc, "accommodation", day_num)
            changed |= self._fix_type(acc, "accommodation", day_num)
            # Ensure amenities exists
            if "amenities" not in acc:
                highlights = acc.get("highlights", [])
                if isinstance(highlights, list):
                    acc["amenities"] = highlights
                else:
                    acc["amenities"] = []
                changed = True
        if changed:
            self._save("accommodation.json", data)
            print(f"  accommodation.json: updated")

    def _migrate_shopping(self):
        data = self._load("shopping.json")
        if not data:
            return
        days = self._extract_days(data)
        changed = False
        for day in days:
            day_num = day.get("day", "?")
            items = day.get("shopping", [])
            changed |= self._migrate_poi_items(items, "shopping", day_num)
            for item in items:
                if isinstance(item, dict) and "type" not in item:
                    item["type"] = "Shopping"
                    changed = True
        if changed:
            self._save("shopping.json", data)
            print(f"  shopping.json: updated")

    def _migrate_transportation(self):
        data = self._load("transportation.json")
        if not data:
            return
        days = self._extract_days(data)
        changed = False
        for day in days:
            day_num = day.get("day", "?")
            lc = day.get("location_change")
            if not lc or not isinstance(lc, dict):
                continue
            # Ensure departure_time/arrival_time are HH:MM format
            for field in ["departure_time", "arrival_time"]:
                val = lc.get(field, "")
                if val and not re.match(r'^[0-2]\d:[0-5]\d$', str(val)):
                    # Try to extract HH:MM from longer strings
                    time_match = re.search(r'(\d{1,2}:\d{2})', str(val))
                    if time_match:
                        lc[field] = time_match.group(1).zfill(5)
                        self.fixes.append(f"[transportation] Day {day_num}: {field}='{lc[field]}' from '{val[:30]}'")
                        changed = True
                    else:
                        # Use placeholder
                        lc[field] = "09:00" if field == "departure_time" else "12:00"
                        self.fixes.append(f"[transportation] Day {day_num}: {field}='{lc[field]}' (placeholder, was '{val[:30]}')")
                        changed = True
            # Ensure duration_minutes exists
            if "duration_minutes" not in lc:
                dur = lc.get("flight_duration_minutes", lc.get("duration_hours", 0))
                if isinstance(dur, (int, float)) and dur > 0:
                    lc["duration_minutes"] = int(dur * 60) if dur < 24 else int(dur)
                    changed = True
            # Ensure cost exists
            if "cost" not in lc:
                cost_cny = lc.get("cost_cny", lc.get("cost_eur", 0))
                lc["cost"] = cost_cny if isinstance(cost_cny, (int, float)) else 0
                changed = True
        if changed:
            self._save("transportation.json", data)
            print(f"  transportation.json: updated")


def main():
    dry_run = "--dry-run" in sys.argv
    run_all = "--all" in sys.argv

    project_root = Path(__file__).parent.parent
    data_root = project_root / "data"

    if run_all:
        plans = [d.name for d in data_root.iterdir() if d.is_dir() and not d.name.startswith(".")]
    elif len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
        plans = [sys.argv[1]]
    else:
        print(__doc__)
        sys.exit(1)

    total_fixes = 0
    for plan_id in sorted(plans):
        data_dir = data_root / plan_id
        if not data_dir.exists():
            print(f"Skipping {plan_id}: not found")
            continue
        migrator = DataMigrator(data_dir, dry_run=dry_run)
        fixes = migrator.run()
        total_fixes += fixes
        print()

    print(f"{'[DRY RUN] ' if dry_run else ''}Migration complete. Total fixes: {total_fixes}")


if __name__ == "__main__":
    main()
