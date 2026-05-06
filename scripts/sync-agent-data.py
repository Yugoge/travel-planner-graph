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
    source venv/bin/activate && python scripts/sync-agent-data.py <destination-slug>
    source venv/bin/activate && python scripts/sync-agent-data.py <destination-slug> --dry-run
    source venv/bin/activate && python scripts/sync-agent-data.py <destination-slug> --skip-html
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

# Route persistence through the canonical save layer so the iter-2 ownership
# rejector + universal image_url deny + stock-image deny all fire on every
# Python-internal write (sync-agent-data is invisible to Bash hooks).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_io import save_agent_json  # noqa: E402


CHECKIN_WINDOW_MINUTES = 60  # Default check-in duration for accommodation

# Sub-keys for split_day timeline structures (RC-3, 2026-05-04). When a day
# has `split_day: true`, parallel `shared`/`matilde`/`jade` dicts carry
# timeline entries in addition to (or instead of) `timeline`. These are
# merged into a single per-day timeline view by _build_timeline_by_day().
SPLIT_DAY_TIMELINE_KEYS = ("shared", "matilde", "jade")


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
        meal_item_ref = "#/$defs/meal_slot"
        meal_types = [k for k, v in day_props.items()
                      if isinstance(v, dict) and v.get("$ref") == meal_item_ref]
        return {
            "meal_types": meal_types,
        }

    def _merge_split_day_timeline(self, day_data: dict, base_tl: dict) -> dict:
        """Fold split_day sub-key timelines into the base view (RC-3)."""
        merged = dict(base_tl)
        for sk in SPLIT_DAY_TIMELINE_KEYS:
            sub = day_data.get(sk)
            if isinstance(sub, dict):
                merged.update(sub)
        return merged

    def _extract_day_timeline(self, day_data: dict) -> dict:
        """Per-day timeline dict, including split_day sub-keys when present.
        RC-3 isinstance-guarded against non-dict timeline values."""
        base_tl = day_data.get("timeline") or {}
        if not isinstance(base_tl, dict):
            base_tl = {}
        if day_data.get("split_day") is True:
            return self._merge_split_day_timeline(day_data, base_tl)
        return base_tl

    def _build_timeline_by_day(self, days: list) -> dict:
        """Build {day_num: merged_timeline_dict} for all days (RC-3)."""
        timeline_by_day = {}
        for day_data in days:
            day_num = day_data.get("day")
            if day_num is None:
                continue
            timeline_by_day[day_num] = self._extract_day_timeline(day_data)
        return timeline_by_day

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

        timeline_by_day = self._build_timeline_by_day(timeline["days"])

        print(f"Loaded timeline: {len(timeline_by_day)} days")

        # Sync each agent
        self._sync_meals(timeline_by_day)
        self._sync_attractions(timeline_by_day)
        self._sync_entertainment(timeline_by_day)
        self._sync_accommodation(timeline_by_day)
        self._sync_shopping(timeline_by_day)
        self._sync_cafe(timeline_by_day)

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
        """Save JSON file via the canonical persistence layer.

        Iter 2 (spec-20260505-221501 / W2): routes every write through
        json_io.save_agent_json so the per-agent ownership rejector,
        universal image_url deny, and stock-image deny all fire on this
        Python-internal write surface. Direct open()/json.dump() bypassed
        these gates entirely (B2 root cause).
        """
        if self.dry_run:
            return
        path = self.data_dir / filename
        agent_name = path.stem
        save_agent_json(
            path,
            agent_name=agent_name,
            data=data,
            validate=False,
            create_backup=False,
            allow_high_severity=True,
        )
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

    def _is_transit(self, key: str, val) -> bool:
        """Transit-segment check; RC-3 isinstance-guarded against non-dict val."""
        return isinstance(val, dict) and val.get("transit") is True

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
                # Name normalization only (time injection removed — timeline is single source of truth)
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
                # Time injection removed — timeline is single source of truth
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
                # Time injection removed — timeline is single source of truth
                if ent != original:
                    items[i] = ent
                    modified = True

        if modified:
            self._save_json("entertainment.json", data)
        else:
            print("  No changes needed")

    def _valid_end_time(self, entry) -> str:
        """Return entry.end_time if dict + valid HH:MM, else ''. RC-3 guard."""
        if not isinstance(entry, dict):
            return ""
        et = entry.get("end_time")
        return et if et and isinstance(et, str) and ":" in et else ""

    def _timeline_end_times(self, day_data: dict) -> list:
        """End times from non-accommodation timeline dict entries (RC-3)."""
        timeline = day_data.get("timeline", {})
        if not isinstance(timeline, dict):
            return []
        out = []
        for entry in timeline.values():
            if isinstance(entry, dict) and entry.get("accommodation_ref"):
                continue
            et = self._valid_end_time(entry)
            if et:
                out.append(et)
        return out

    def _collect_non_accom_end_times(self, day_data: dict) -> list:
        """Collect end_times from non-accommodation timeline + travel_segments."""
        end_times = self._timeline_end_times(day_data)
        for seg in day_data.get("travel_segments", []):
            et = self._valid_end_time(seg)
            if et:
                end_times.append(et)
        return end_times

    def _adjust_accom_entry(self, accom_entry: dict, max_end: str, day_num: int) -> bool:
        """Adjust accommodation entry timing if it starts before max_end. Returns True if modified."""
        old_start = accom_entry.get("start_time", "")
        if old_start >= max_end:
            return False
        h, m = map(int, max_end.split(":"))
        m += 30
        if m >= 60:
            h += 1
            m -= 60
        if h >= 24:
            h, m = 23, 59
        print(f"  Day {day_num}: accommodation check-in adjusted from {old_start} to {max_end}")
        accom_entry["start_time"] = max_end
        accom_entry["end_time"] = f"{h:02d}:{m:02d}"
        accom_entry["duration_minutes"] = 30
        return True

    def _find_accom_entry(self, timeline) -> dict:
        """Find accommodation_ref entry; RC-3 guarded against non-dict timeline/entries."""
        for e in (timeline or {}).values() if isinstance(timeline, dict) else ():
            if isinstance(e, dict) and e.get("accommodation_ref"):
                return e
        return None

    def _sync_accommodation(self, timeline_by_day: dict):
        """Fix accommodation check-in timing in timeline.json.

        Rule: accommodation start_time = MAX(all non-accommodation entry end_times).
        """
        print("Syncing accommodation...")
        timeline_data = self._load_json("timeline.json")
        if not timeline_data or "days" not in timeline_data:
            print("  Skipped (no timeline data)")
            return
        modified = False
        for day_data in timeline_data["days"]:
            day_num = day_data.get("day")
            accom_entry = self._find_accom_entry(day_data.get("timeline", {}))
            if not accom_entry:
                continue
            end_times = self._collect_non_accom_end_times(day_data)
            if end_times and self._adjust_accom_entry(accom_entry, max(end_times), day_num):
                modified = True
        if modified:
            self._save_json("timeline.json", timeline_data)
        else:
            print("  No accommodation timing adjustments needed")

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
                # Time injection removed — timeline is single source of truth

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

    def _sync_cafe(self, timeline_by_day: dict):
        """Sync cafe agent data with timeline."""
        print("Syncing cafe...")
        data = self._load_json("cafe.json")
        if not data or "days" not in data:
            print("  Skipped (no data)")
            return

        modified = False
        for day in data["days"]:
            day_num = day.get("day", 0)
            day_tl = timeline_by_day.get(day_num, {})
            items = day.get("cafe", [])

            for i, cafe_item in enumerate(items):
                original = deepcopy(cafe_item)
                # Time injection removed — timeline is single source of truth
                if cafe_item != original:
                    items[i] = cafe_item
                    modified = True

        if modified:
            self._save_json("cafe.json", data)
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
                "cafe",
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
        print("  source venv/bin/activate && python scripts/sync-agent-data.py china-feb-15-mar-7-2026-20260202-195429")
        print("  source venv/bin/activate && python scripts/sync-agent-data.py china-feb-15-mar-7-2026-20260202-195429 --dry-run")
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
