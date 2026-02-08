#!/usr/bin/env python3
"""
Agent Data Synchronization Script

Single Source of Truth: timeline.json
Purpose: After any agent updates, this script:
  1. Normalizes time formats across all agent JSONs (str -> {start, end})
  2. Injects authoritative times from timeline.json into agent data
  3. Normalizes bilingual name fields (name -> name_base/name_local)
  4. Regenerates HTML output
  5. Generates sync report

Usage:
    python scripts/sync-agent-data.py <destination-slug>
    python scripts/sync-agent-data.py <destination-slug> --dry-run
    python scripts/sync-agent-data.py <destination-slug> --skip-html
"""

import json
import sys
import os
import re
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from copy import deepcopy


class AgentDataSyncer:
    """Synchronize agent data using timeline.json as Single Source of Truth."""

    # Transit prefixes to exclude from POI matching
    TRANSIT_PREFIXES = (
        "travel to", "walk to", "drive to", "taxi to", "bus to",
        "train to", "metro to", "subway to", "transfer to",
        "travel from", "walk from", "drive from",
        "travel back", "return to", "board train",
        "hotel check", "check luggage", "wake up", "arrive ",
        "return home", "free time", "settle in",
    )

    def __init__(self, plan_id: str, dry_run: bool = False):
        self.plan_id = plan_id
        self.dry_run = dry_run
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data" / plan_id
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "plan_id": plan_id,
            "dry_run": dry_run,
            "time_normalizations": [],
            "timeline_injections": [],
            "name_normalizations": [],
            "unmatched_items": [],
            "errors": [],
        }

    def run(self, skip_html: bool = False) -> dict:
        """Execute full sync pipeline."""
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Syncing agent data for: {self.plan_id}")
        print(f"Data dir: {self.data_dir}")

        if not self.data_dir.exists():
            self.report["errors"].append(f"Data directory not found: {self.data_dir}")
            return self.report

        # Load timeline (Single Source of Truth)
        timeline = self._load_json("timeline.json")
        if not timeline or "days" not in timeline:
            self.report["errors"].append("timeline.json missing or has no 'days' array")
            return self.report

        timeline_by_day = {}
        for day_data in timeline["days"]:
            day_num = day_data.get("day")
            if day_num is not None:
                timeline_by_day[day_num] = day_data.get("timeline", {})

        print(f"Loaded timeline: {len(timeline_by_day)} days")

        # Sync each agent
        self._sync_meals(timeline_by_day)
        self._sync_attractions(timeline_by_day)
        self._sync_entertainment(timeline_by_day)
        self._sync_accommodation(timeline_by_day)
        self._sync_shopping(timeline_by_day)

        # Post-sync schema validation gate (report but don't fail)
        self._validate_synced_data()

        # Print report summary
        self._print_report()

        # Regenerate HTML
        if not skip_html and not self.dry_run:
            self._regenerate_html()

        return self.report

    def _load_json(self, filename: str) -> dict:
        """Load JSON file, extracting nested 'data' if present."""
        path = self.data_dir / filename
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Unwrap nested 'data' field if present
            if "data" in data and isinstance(data["data"], dict):
                return data["data"]
            return data
        except (json.JSONDecodeError, Exception) as e:
            self.report["errors"].append(f"Error loading {filename}: {e}")
            return {}

    def _save_json(self, filename: str, data: dict):
        """Save JSON file, wrapping in 'data' envelope."""
        if self.dry_run:
            return
        path = self.data_dir / filename
        # Read original to preserve metadata
        original = {}
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    original = json.load(f)
            except Exception:
                pass

        # Wrap in data envelope if original had one
        if "data" in original and isinstance(original["data"], dict):
            original["data"] = data
            output = original
        else:
            output = {"data": data}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {filename}")

    def _normalize_time(self, time_val, default_duration_hours: float = 1.0) -> dict:
        """Normalize time value to {start, end} dict format.

        Handles:
          - dict with start/end -> pass through
          - "HH:MM" string -> add default duration
          - "HH:MM-HH:MM" string -> split into start/end
          - None -> return None
        """
        if time_val is None:
            return None
        if isinstance(time_val, dict):
            if time_val.get("start") and time_val.get("end"):
                return time_val
            return None
        if isinstance(time_val, str):
            time_val = time_val.strip()
            if "-" in time_val and ":" in time_val:
                parts = time_val.split("-")
                if len(parts) == 2:
                    return {"start": parts[0].strip(), "end": parts[1].strip()}
            elif ":" in time_val:
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

    def _is_transit(self, key: str) -> bool:
        """Check if a timeline key is a transit/travel entry (not a POI)."""
        return key.lower().startswith(self.TRANSIT_PREFIXES)

    def _find_timeline_item(self, item_name: str, day_timeline: dict,
                            time_hint: str = None) -> dict:
        """Find timeline entry for item name using precise multi-tier matching.

        Tier 1: Exact match
        Tier 2: Base-name exact match (strip parenthetical suffixes)
        Tier 3: Substring match (POI entries only, exclude transit)

        When multiple entries match (e.g. "Family Home" as lunch and dinner),
        uses time_hint to disambiguate.
        Args:
            time_hint: "breakfast"/"lunch"/"dinner" or "HH:MM"
        """
        if not day_timeline or not item_name:
            return None

        hint_ranges = {
            "breakfast": (5, 10),
            "lunch": (10, 15),
            "dinner": (17, 23),
        }

        def _time_in_range(tl_val: dict, hint: str) -> bool:
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
            try:
                hint_h = int(hint.split(":")[0])
                return abs(h - hint_h) <= 2
            except (ValueError, IndexError):
                return True

        def _pick_best(candidates):
            if not candidates:
                return None
            if len(candidates) == 1 or not time_hint:
                return candidates[0][1]
            for key, val in candidates:
                if _time_in_range(val, time_hint):
                    return val
            return candidates[0][1]

        # Tier 1: Exact match
        exact = [(k, v) for k, v in day_timeline.items() if k == item_name]
        if exact:
            return _pick_best(exact)

        # Tier 2: Base-name exact match
        item_base = item_name.split("(")[0].strip().split("（")[0].strip()
        tier2 = []
        for tl_key, tl_val in day_timeline.items():
            if self._is_transit(tl_key):
                continue
            tl_base = tl_key.split("(")[0].strip().split("（")[0].strip()
            if item_base.lower() == tl_base.lower():
                tier2.append((tl_key, tl_val))
        if tier2:
            return _pick_best(tier2)

        # Tier 3: Substring match (POI only)
        tier3 = []
        for tl_key, tl_val in day_timeline.items():
            if self._is_transit(tl_key):
                continue
            tl_base = tl_key.split("(")[0].strip().lower()
            if item_base.lower() in tl_key.lower() or tl_base in item_base.lower():
                tier3.append((tl_key, tl_val))
        if tier3:
            return _pick_best(tier3)

        return None

    def _inject_time(self, item: dict, day_timeline: dict, agent: str, day_num: int,
                     default_duration: float = 1.0, time_hint: str = None) -> dict:
        """Inject authoritative time from timeline into an item.

        Priority:
          1. timeline.json lookup (Single Source of Truth)
          2. Existing time in item (normalize format)
          3. None (skip)
        Args:
            time_hint: "breakfast"/"lunch"/"dinner" or "HH:MM" for disambiguation
        """
        item_name = item.get("name_base", item.get("name", ""))
        # Also try name_local for matching
        item_name_local = item.get("name_local", "")

        # Try matching with name_base first, then name_local
        tl_item = self._find_timeline_item(item_name, day_timeline, time_hint=time_hint)
        if not tl_item and item_name_local:
            tl_item = self._find_timeline_item(item_name_local, day_timeline, time_hint=time_hint)

        if tl_item and "start_time" in tl_item and "end_time" in tl_item:
            new_time = {"start": tl_item["start_time"], "end": tl_item["end_time"]}
            old_time = item.get("time")
            if old_time != new_time:
                self.report["timeline_injections"].append({
                    "agent": agent,
                    "day": day_num,
                    "item": item_name,
                    "old_time": old_time,
                    "new_time": new_time,
                })
            item["time"] = new_time
            return item

        # Normalize existing time if present
        existing = item.get("time")
        if existing is not None:
            normalized = self._normalize_time(existing, default_duration)
            if normalized and normalized != existing:
                self.report["time_normalizations"].append({
                    "agent": agent,
                    "day": day_num,
                    "item": item_name,
                    "old": existing,
                    "new": normalized,
                })
                item["time"] = normalized
        elif day_timeline:
            # Time is None and we couldn't match - report it
            self.report["unmatched_items"].append({
                "agent": agent,
                "day": day_num,
                "item": item_name,
                "reason": "no timeline match, time is None",
            })

        return item

    def _sync_meals(self, timeline_by_day: dict):
        """Sync meals agent data with timeline."""
        print("Syncing meals...")
        data = self._load_json("meals.json")
        if not data or "days" not in data:
            print("  Skipped (no data)")
            return

        modified = False
        for day in data["days"]:
            day_num = day.get("day", 0)
            day_tl = timeline_by_day.get(day_num, {})

            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_type)
                if not meal or not isinstance(meal, dict):
                    continue

                original = deepcopy(meal)
                self._inject_time(meal, day_tl, "meals", day_num,
                                  default_duration=1.0, time_hint=meal_type)
                if meal != original:
                    day[meal_type] = meal
                    modified = True

        if modified:
            self._save_json("meals.json", data)
        else:
            print("  No changes needed")

    def _sync_attractions(self, timeline_by_day: dict):
        """Sync attractions agent data with timeline."""
        print("Syncing attractions...")
        data = self._load_json("attractions.json")
        if not data or "days" not in data:
            print("  Skipped (no data)")
            return

        modified = False
        for day in data["days"]:
            day_num = day.get("day", 0)
            day_tl = timeline_by_day.get(day_num, {})
            attractions = day.get("attractions", [])

            for i, attr in enumerate(attractions):
                original = deepcopy(attr)
                self._inject_time(attr, day_tl, "attractions", day_num,
                                  default_duration=2.0)
                if attr != original:
                    attractions[i] = attr
                    modified = True

        if modified:
            self._save_json("attractions.json", data)
        else:
            print("  No changes needed")

    def _sync_entertainment(self, timeline_by_day: dict):
        """Sync entertainment agent data with timeline."""
        print("Syncing entertainment...")
        data = self._load_json("entertainment.json")
        if not data or "days" not in data:
            print("  Skipped (no data)")
            return

        modified = False
        for day in data["days"]:
            day_num = day.get("day", 0)
            day_tl = timeline_by_day.get(day_num, {})
            items = day.get("entertainment", [])

            for i, ent in enumerate(items):
                original = deepcopy(ent)
                self._inject_time(ent, day_tl, "entertainment", day_num,
                                  default_duration=1.5)
                if ent != original:
                    items[i] = ent
                    modified = True

        if modified:
            self._save_json("entertainment.json", data)
        else:
            print("  No changes needed")

    def _sync_accommodation(self, timeline_by_day: dict):
        """Sync accommodation agent data with timeline."""
        print("Syncing accommodation...")
        data = self._load_json("accommodation.json")
        if not data or "days" not in data:
            print("  Skipped (no data)")
            return

        modified = False
        for day in data["days"]:
            day_num = day.get("day", 0)
            day_tl = timeline_by_day.get(day_num, {})
            accom = day.get("accommodation")
            if not accom or not isinstance(accom, dict):
                continue

            # Accommodation typically has check_in/check_out, not time
            # But sync name format if needed
            original = deepcopy(accom)
            # Try to find check-in time from timeline
            accom_name = accom.get("name_base", accom.get("name", ""))
            tl_item = self._find_timeline_item(accom_name, day_tl)
            if tl_item and "start_time" in tl_item:
                if not accom.get("check_in_time"):
                    accom["check_in_time"] = tl_item["start_time"]
                    self.report["timeline_injections"].append({
                        "agent": "accommodation",
                        "day": day_num,
                        "item": accom_name,
                        "old_time": None,
                        "new_time": tl_item["start_time"],
                        "field": "check_in_time",
                    })

            if accom != original:
                day["accommodation"] = accom
                modified = True

        if modified:
            self._save_json("accommodation.json", data)
        else:
            print("  No changes needed")

    def _sync_shopping(self, timeline_by_day: dict):
        """Sync shopping agent data with timeline."""
        print("Syncing shopping...")
        data = self._load_json("shopping.json")
        if not data or "days" not in data:
            print("  Skipped (no data)")
            return

        modified = False
        for day in data["days"]:
            day_num = day.get("day", 0)
            day_tl = timeline_by_day.get(day_num, {})
            items = day.get("shopping", [])

            for i, shop in enumerate(items):
                original = deepcopy(shop)
                self._inject_time(shop, day_tl, "shopping", day_num,
                                  default_duration=1.5)

                # Also normalize bilingual name fields if using old format
                if "name" in shop and "name_base" not in shop:
                    name = shop["name"]
                    # Try to split "English Name (中文名)" pattern
                    match = re.match(r'^(.+?)\s*[(\uff08](.+?)[)\uff09]\s*$', name)
                    if match:
                        shop["name_base"] = match.group(1).strip()
                        shop["name_local"] = match.group(2).strip()
                        self.report["name_normalizations"].append({
                            "agent": "shopping",
                            "day": day_num,
                            "old_name": name,
                            "name_base": shop["name_base"],
                            "name_local": shop["name_local"],
                        })

                if shop != original:
                    items[i] = shop
                    modified = True

        if modified:
            self._save_json("shopping.json", data)
        else:
            print("  No changes needed")

    def _validate_synced_data(self):
        """Validate synced data against JSON schemas (report-only, non-blocking).

        Uses validate-agent-outputs.py's load_schemas/validate_against_schema
        to catch any schema violations introduced by the sync process.
        """
        print("\nValidating synced data against schemas...")
        try:
            # Import validate-agent-outputs.py (hyphenated filename requires importlib)
            validator_path = Path(__file__).parent / "validate-agent-outputs.py"
            if not validator_path.exists():
                print("  Skipped (validator script not found)")
                return

            spec = importlib.util.spec_from_file_location(
                "validate_agent_outputs", str(validator_path)
            )
            validator_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validator_module)

            schemas, registry = validator_module.load_schemas(self.base_dir)

            validation_errors = []
            agents_to_check = [
                "meals", "attractions", "entertainment",
                "accommodation", "transportation", "timeline", "budget", "shopping",
            ]

            for agent_name in agents_to_check:
                agent_file = self.data_dir / f"{agent_name}.json"
                if not agent_file.exists():
                    continue
                schema = schemas.get(agent_name)
                if not schema:
                    continue
                try:
                    with open(agent_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    errors = validator_module.validate_against_schema(
                        data, schema, registry, agent_name
                    )
                    validation_errors.extend(errors)
                except Exception as e:
                    validation_errors.append(f"[{agent_name}] Load error: {e}")

            if validation_errors:
                print(f"  WARNING: {len(validation_errors)} schema violation(s) after sync:")
                for err in validation_errors[:10]:
                    print(f"    {err}")
                if len(validation_errors) > 10:
                    print(f"    ... and {len(validation_errors) - 10} more")
                self.report["schema_violations"] = validation_errors
            else:
                print("  All synced data passes schema validation")

        except Exception as e:
            # Non-blocking: if validation itself fails, just report and continue
            print(f"  Schema validation skipped due to error: {e}")
            self.report["errors"].append(f"Post-sync validation error: {e}")

    def _regenerate_html(self):
        """Regenerate HTML output using generate-html-interactive.py."""
        print("\nRegenerating HTML...")
        script = self.base_dir / "scripts" / "generate-html-interactive.py"
        if not script.exists():
            self.report["errors"].append(f"HTML generator not found: {script}")
            return

        try:
            result = subprocess.run(
                [sys.executable, str(script), self.plan_id],
                capture_output=True, text=True, timeout=60,
                cwd=str(self.base_dir),
            )
            if result.returncode == 0:
                print("  HTML regenerated successfully")
                # Print any output file path from stdout
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        print(f"  {line.strip()}")
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.report["errors"].append(f"HTML generation failed: {error_msg}")
                print(f"  ERROR: {error_msg}")
        except subprocess.TimeoutExpired:
            self.report["errors"].append("HTML generation timed out")
            print("  ERROR: Timed out")
        except Exception as e:
            self.report["errors"].append(f"HTML generation error: {e}")
            print(f"  ERROR: {e}")

    def _print_report(self):
        """Print sync report summary."""
        print("\n" + "=" * 60)
        print("SYNC REPORT")
        print("=" * 60)

        injections = self.report["timeline_injections"]
        normalizations = self.report["time_normalizations"]
        name_norms = self.report["name_normalizations"]
        unmatched = self.report["unmatched_items"]
        errors = self.report["errors"]

        print(f"Timeline injections:  {len(injections)}")
        for inj in injections:
            old = inj.get("old_time", "None")
            new = inj.get("new_time", "?")
            print(f"  Day {inj['day']} [{inj['agent']}] {inj['item']}: {old} -> {new}")

        print(f"Time normalizations:  {len(normalizations)}")
        for norm in normalizations:
            print(f"  Day {norm['day']} [{norm['agent']}] {norm['item']}: {norm['old']} -> {norm['new']}")

        print(f"Name normalizations:  {len(name_norms)}")
        for nn in name_norms:
            print(f"  Day {nn['day']} [{nn['agent']}] {nn['old_name']} -> base={nn['name_base']}, local={nn['name_local']}")

        print(f"Unmatched items:      {len(unmatched)}")
        for um in unmatched:
            print(f"  Day {um['day']} [{um['agent']}] {um['item']}: {um['reason']}")

        if errors:
            print(f"Errors:               {len(errors)}")
            for err in errors:
                print(f"  {err}")

        total_changes = len(injections) + len(normalizations) + len(name_norms)
        print(f"\nTotal changes: {total_changes}")
        if self.dry_run:
            print("(DRY RUN - no files modified)")
        print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: sync-agent-data.py <destination-slug> [--dry-run] [--skip-html]")
        print()
        print("Synchronizes agent data using timeline.json as Single Source of Truth.")
        print("Normalizes time formats, injects timeline times, and regenerates HTML.")
        print()
        print("Examples:")
        print("  python scripts/sync-agent-data.py china-feb-15-mar-7-2026-20260202-195429")
        print("  python scripts/sync-agent-data.py china-feb-15-mar-7-2026-20260202-195429 --dry-run")
        sys.exit(1)

    plan_id = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    skip_html = "--skip-html" in sys.argv

    syncer = AgentDataSyncer(plan_id, dry_run=dry_run)
    report = syncer.run(skip_html=skip_html)

    # Save report
    if not dry_run:
        report_path = Path(__file__).parent.parent / "data" / plan_id / "sync-report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"\nReport saved: {report_path}")

    # Exit code based on errors
    sys.exit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
