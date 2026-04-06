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

    def __init__(self, plan_id: str, dry_run: bool = False):
        self.plan_id = plan_id
        self.dry_run = dry_run
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data" / plan_id
        self._config = self._load_config()
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

    def _load_config(self) -> dict:
        """Load validation config. meal_types derived from meals schema (single source of truth)."""
        cfg_path = self.base_dir / "config" / "validation.json"
        schema_path = self.base_dir / "schemas" / "meals.schema.json"
        with open(cfg_path, 'r') as f:
            val = json.load(f)
        with open(schema_path, 'r') as f:
            meals_schema = json.load(f)
        # Derive meal_types from meals.schema.json day_entry properties
        day_props = meals_schema["$defs"]["day_entry"]["properties"]
        meal_item_ref = "#/$defs/meal_item"
        meal_types = [k for k, v in day_props.items()
                      if isinstance(v, dict) and v.get("$ref") == meal_item_ref]
        return {
            "meal_types": meal_types,
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

    def _is_transit(self, key: str, val: dict) -> bool:
        """Check if a timeline entry is a transit/travel segment (not a POI)."""
        return val.get("transit") is True

    def _find_timeline_item(self, item_name: str, day_timeline: dict) -> dict:
        """Find timeline entry for item name using precise multi-tier matching.

        Tier 1: Exact match
        Tier 2: Base-name exact match (strip parenthetical suffixes)
        Tier 3: Substring match (POI entries only, exclude transit)
        """
        if not day_timeline or not item_name:
            return None

        def _first(candidates):
            return candidates[0][1] if candidates else None

        # Tier 1: Exact match
        exact = [(k, v) for k, v in day_timeline.items() if k == item_name]
        if exact:
            return _first(exact)

        # Tier 2: Base-name exact match
        item_base = item_name.split("(")[0].strip().split("（")[0].strip()
        tier2 = []
        for tl_key, tl_val in day_timeline.items():
            if self._is_transit(tl_key, tl_val):
                continue
            tl_base = tl_key.split("(")[0].strip().split("（")[0].strip()
            if item_base.lower() == tl_base.lower():
                tier2.append((tl_key, tl_val))
        if tier2:
            return _first(tier2)

        # Tier 3: Substring match (POI only)
        tier3 = []
        for tl_key, tl_val in day_timeline.items():
            if self._is_transit(tl_key, tl_val):
                continue
            tl_base = tl_key.split("(")[0].strip().lower()
            if item_base.lower() in tl_key.lower() or tl_base in item_base.lower():
                tier3.append((tl_key, tl_val))
        if tier3:
            return _first(tier3)

        return None

    def _inject_time(self, item: dict, day_timeline: dict, agent: str, day_num: int,
                     default_duration: float = 1.0) -> dict:
        """Inject authoritative time from timeline into an item.

        Priority:
          1. timeline.json lookup (Single Source of Truth)
          2. Existing time in item (normalize format)
          3. None (skip)
        """
        item_name = item.get("name_base", item.get("name", ""))
        # Also try name_local for matching
        item_name_local = item.get("name_local", "")

        # Try matching with name_base first, then name_local
        tl_item = self._find_timeline_item(item_name, day_timeline)
        if not tl_item and item_name_local:
            tl_item = self._find_timeline_item(item_name_local, day_timeline)

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

            for meal_type in self._config["meal_types"]:
                meal_slot = day.get(meal_type)
                if not meal_slot or not isinstance(meal_slot, dict):
                    continue

                # Dual-read: new format has meal_slot.primary; old format is meal_item directly
                is_nested = "primary" in meal_slot
                meal = meal_slot.get("primary", meal_slot)

                original = deepcopy(meal)
                # Direct meal_ref lookup — timeline entries tagged with meal_ref field
                tl_item = next((v for v in day_tl.values() if v.get("meal_ref") == meal_type), None)
                if tl_item and "start_time" in tl_item and "end_time" in tl_item:
                    item_name = meal.get("name_base", meal.get("name", ""))
                    new_time = {"start": tl_item["start_time"], "end": tl_item["end_time"]}
                    old_time = meal.get("time")
                    if old_time != new_time:
                        self.report["timeline_injections"].append({
                            "agent": "meals",
                            "day": day_num,
                            "item": item_name,
                            "old_time": old_time,
                            "new_time": new_time,
                        })
                    meal["time"] = new_time
                else:
                    # Fallback: name-based lookup (no time_hint needed)
                    self._inject_time(meal, day_tl, "meals", day_num, default_duration=1.0)
                if meal != original:
                    if is_nested:
                        meal_slot["primary"] = meal
                    day[meal_type] = meal_slot
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

            # Accommodation needs time: {start, end} for HTML renderer.
            # Source of truth: return-to-hotel travel_segment end_time in timeline,
            # or the accommodation entry itself if found directly in timeline.
            original = deepcopy(accom)
            accom_name = accom.get("name_base", accom.get("name", ""))

            # Strategy 1: find "Return to [Hotel]" travel segment end_time
            return_seg_time = None
            day_obj = None
            # We need raw timeline day data (travel_segments), not just dict keys
            # timeline_by_day is keyed by day_num and contains the timeline dict
            # Travel segments are in the parent day object — access via self._load_json
            tl_data = self._load_json("timeline.json")
            if tl_data and "days" in tl_data:
                for tl_day in tl_data["days"]:
                    if tl_day.get("day") == day_num:
                        day_obj = tl_day
                        break
            if day_obj:
                # Use the LAST travel segment that explicitly says "Return to" or "返回酒店"
                # (not just any segment going to a hotel, e.g. arrival from airport)
                for seg in day_obj.get("travel_segments", []):
                    seg_name = seg.get("name_base", "")
                    seg_local = seg.get("name_local", "")
                    is_return = (
                        seg_name.lower().startswith("return to") or
                        "返回" in seg_local
                    )
                    if is_return:
                        return_seg_time = seg.get("end_time")
                        # Don't break — use the LAST matching segment

            # Strategy 2: find accommodation directly in timeline dict
            tl_item = self._find_timeline_item(accom_name, day_tl)

            # Determine check-in start time
            checkin_start = None
            if return_seg_time:
                checkin_start = return_seg_time
            elif tl_item and "start_time" in tl_item:
                checkin_start = tl_item["start_time"]
            elif accom.get("check_in"):
                checkin_start = accom["check_in"]

            if checkin_start:
                old_time = accom.get("time")
                # Build end time = start + 60 min (capped at 23:59)
                try:
                    h, m = map(int, checkin_start.split(":"))
                    total_min = h * 60 + m + 60
                    if total_min >= 24 * 60:
                        checkin_end = "23:59"
                    else:
                        checkin_end = f"{total_min // 60:02d}:{total_min % 60:02d}"
                except Exception:
                    checkin_end = checkin_start
                new_time = {"start": checkin_start, "end": checkin_end}
                if accom.get("time") != new_time:
                    accom["time"] = new_time
                    accom["check_in_time"] = checkin_start
                    self.report["timeline_injections"].append({
                        "agent": "accommodation",
                        "day": day_num,
                        "item": accom_name,
                        "old_time": old_time,
                        "new_time": new_time,
                        "field": "time",
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
        """Regenerate HTML and deploy via generate-and-deploy.sh."""
        print("\nRegenerating HTML and deploying...")
        deploy_script = self.base_dir / "scripts" / "generate-and-deploy.sh"
        if deploy_script.exists():
            self._run_deploy(deploy_script)
        else:
            self._run_html_only()

    def _run_deploy(self, script):
        """Run generate-and-deploy.sh (HTML + deploy to web + GitHub)."""
        try:
            result = subprocess.run(
                ["bash", str(script), self.plan_id],
                capture_output=True, text=True, timeout=300,
                cwd=str(self.base_dir),
            )
            if result.returncode == 0:
                print("  HTML generated and deployed")
                self._print_deploy_highlights(result.stdout)
            else:
                msg = (result.stderr or result.stdout)[:200]
                self.report["errors"].append(f"Deploy failed: {msg}")
                print(f"  ERROR: {msg}")
        except subprocess.TimeoutExpired:
            self.report["errors"].append("Deploy timed out (300s)")
            print("  ERROR: Timed out")

    def _run_html_only(self):
        """Fallback: HTML-only generation without deploy."""
        script = self.base_dir / "scripts" / "generate-html-interactive.py"
        if not script.exists():
            self.report["errors"].append("No HTML generator found")
            return
        print("  Warning: HTML-only fallback (no deploy)")
        try:
            result = subprocess.run(
                [sys.executable, str(script), self.plan_id],
                capture_output=True, text=True, timeout=60,
                cwd=str(self.base_dir),
            )
            if result.returncode == 0:
                print("  HTML regenerated (no deployment)")
            else:
                msg = result.stderr or result.stdout
                self.report["errors"].append(f"HTML failed: {msg}")
                print(f"  ERROR: {msg}")
        except subprocess.TimeoutExpired:
            self.report["errors"].append("HTML timed out")
            print("  ERROR: Timed out")

    def _print_deploy_highlights(self, stdout):
        """Print key deploy output lines."""
        for line in stdout.strip().split("\n"):
            s = line.strip()
            if s and any(k in s for k in ["Live", "URL", "Complete"]):
                print(f"  {s}")

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
