#!/usr/bin/env python3
"""
Unified Data Saving Script - Batch Validation and Atomic Writes
================================================================
Single script for all agent data saving with mandatory validation.

This script replaces all individual save scripts and enforces:
  - Automatic validation (plan-validate.py)
  - Atomic writes (.tmp to rename)
  - Automatic backups (.bak)
  - Batch operations with rollback
  - HIGH severity issues block saves

Usage:
  python3 scripts/save.py --trip TRIP_SLUG --agent meals --input data.json
  cat data.json | python3 scripts/save.py --trip TRIP_SLUG --agent meals
  python3 scripts/save.py --trip TRIP_SLUG --batch agents_data.json
"""

import json
import sys
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.json_io import (
    save_agent_json,
    load_agent_json,
    merge_agent_slots,
    ValidationError,
    AtomicWriteError,
    validate_agent_data
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLAN_VALIDATE = PROJECT_ROOT / "scripts" / "plan-validate.py"


def _derive_meal_types():
    """Derive meal types from meals schema."""
    schema_path = Path(__file__).parent.parent / "schemas" / "meals.schema.json"
    if schema_path.exists():
        schema = json.loads(schema_path.read_text())
        day_props = schema.get("$defs", {}).get("day_entry", {}).get("properties", {})
        return [k for k, v in day_props.items() if v.get("$ref") == "#/$defs/meal_slot"]
    return ["breakfast", "lunch", "dinner"]


MEAL_TYPES = _derive_meal_types()
SCHEDULE_AGENTS = {"timeline", "segment"}
POI_AGENTS = {"meals", "attractions", "entertainment", "shopping", "cafe"}
TIMELINE_FIELD = "timeline"
TRAVEL_SEGMENTS_FIELD = "travel_segments"


def _load_image_fetcher(trip_slug: str):
    """Load BatchImageFetcher from fetch-images-batch.py. None on failure."""
    try:
        import importlib.util
        batch_script = Path(__file__).resolve().parent / "fetch-images-batch.py"
        spec = importlib.util.spec_from_file_location("fetch_images_batch", batch_script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.BatchImageFetcher(trip_slug)
    except Exception as e:
        print(f"Image fetcher unavailable: {e}", file=sys.stderr)
        return None


def _collect_day_pois(day: dict, agent: str) -> list:
    """Collect POIs from a day entry based on agent type."""
    if agent == "meals":
        return [day[mt] for mt in MEAL_TYPES if isinstance(day.get(mt), dict)]
    if agent == "accommodation":
        acc = day.get("accommodation")
        return [acc] if isinstance(acc, dict) else []
    if agent in ["attractions", "entertainment", "shopping", "cafe"]:
        return list(day.get(agent, []))
    return []


def _fetch_poi_image(fetcher, poi: dict, city: str) -> bool:
    """Try to fetch image for a single POI. Returns True if updated."""
    photo_url = fetcher.fetch_poi_photo(
        poi_name=poi.get("name_base", ""),
        city=city,
        name_local=poi.get("name_local"),
        location_local=poi.get("location_local"),
        poi_coordinates=poi.get("coordinates"),
    )
    if photo_url:
        poi["image_url"] = photo_url
        return True
    return False


def _fill_missing_images(fetcher, pois: list, city: str) -> int:
    """Fetch images for POIs missing image_url. Returns count updated."""
    updated = 0
    for poi in pois:
        if not isinstance(poi, dict) or poi.get("image_url"):
            continue
        if _fetch_poi_image(fetcher, poi, city):
            updated += 1
    return updated


def extract_image_urls(agent: str, data: Dict[str, Any], trip_slug: str) -> None:
    """Auto-extract image_url for POIs missing it."""
    if agent not in (POI_AGENTS | {"accommodation"}):
        return
    fetcher = _load_image_fetcher(trip_slug)
    if not fetcher:
        return
    total = 0
    for day in data.get("days", []):
        pois = _collect_day_pois(day, agent)
        total += _fill_missing_images(fetcher, pois, day.get("location", ""))
    if total > 0:
        print(f"Auto-extracted {total} image URLs", file=sys.stderr)


def _extract_high_issues(issues: list) -> list:
    """Filter HIGH severity issues from a list."""
    def _is_high(i):
        sev = i.severity.value if hasattr(i.severity, 'value') else i.severity
        return sev == "HIGH"
    return [i for i in issues if _is_high(i)]


def _report_high_issues(issues: list) -> None:
    """Print HIGH severity issues to stderr."""
    high = _extract_high_issues(issues)
    print(f"Validation failed with {len(high)} HIGH severity issues:", file=sys.stderr)
    for issue in high[:10]:
        print(f"  - {issue.label}: {issue.field} - {issue.message}", file=sys.stderr)
    if len(high) > 10:
        print(f"  ... and {len(high) - 10} more", file=sys.stderr)


def _handle_validation_error(e, allow_high):
    """Handle a ValidationError, returning (success, issues, metrics)."""
    if allow_high:
        print("WARNING: HIGH issues present but --allow-high specified", file=sys.stderr)
        return True, e.issues, e.metrics
    _report_high_issues(e.issues)
    return False, e.issues, e.metrics


def validate_data(
    trip_slug: str, agent: str, data: Dict[str, Any],
    skip_validation: bool = False, allow_high: bool = False,
) -> tuple:
    """Run validation. Returns (success, issues, metrics)."""
    if skip_validation:
        print("WARNING: Validation skipped (--no-validate)", file=sys.stderr)
        return True, [], {}
    try:
        trip_dir = DATA_DIR / trip_slug
        issues, metrics = validate_agent_data(agent, data, trip_dir)
        if _extract_high_issues(issues) and not allow_high:
            raise ValidationError(issues, metrics)
        return True, [], {}
    except ValidationError as e:
        return _handle_validation_error(e, allow_high)


def _parse_hhmm(t: str) -> int:
    """Parse HH:MM to minutes since midnight. -1 if invalid."""
    if not t or ":" not in t:
        return -1
    try:
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return -1


def _times_overlap(s1: str, e1: str, s2: str, e2: str) -> bool:
    """Check if two HH:MM ranges overlap (exclusive endpoints)."""
    m1s, m1e = _parse_hhmm(s1), _parse_hhmm(e1)
    m2s, m2e = _parse_hhmm(s2), _parse_hhmm(e2)
    if min(m1s, m1e, m2s, m2e) < 0:
        return False
    return m1s < m2e and m2s < m1e


def _build_timeline_act(name: str, d: dict) -> dict:
    """Build an activity dict from a timeline entry."""
    act = {
        "ag": "timeline", "name": name,
        "s": d["start_time"], "e": d.get("end_time", ""),
        "optional": d.get("optional", False),
    }
    for ref_key in ("meal_ref", "transport_ref", "accommodation_ref"):
        if d.get(ref_key):
            act[ref_key] = d[ref_key]
    return act


def _collect_timeline_entries(day: dict) -> list:
    """Collect timeline dict entries as activity dicts."""
    acts = []
    for name, d in day.get(TIMELINE_FIELD, {}).items():
        if isinstance(d, dict) and d.get("start_time"):
            acts.append(_build_timeline_act(name, d))
    return acts


def _collect_segment_entries(day: dict) -> list:
    """Collect travel_segments as activity dicts."""
    acts = []
    for i, seg in enumerate(day.get(TRAVEL_SEGMENTS_FIELD, [])):
        if not (isinstance(seg, dict) and seg.get("start_time")):
            continue
        acts.append({
            "ag": "segment",
            "name": seg.get("name_base", f"seg-{i}"),
            "s": seg["start_time"],
            "e": seg.get("end_time", ""),
            "optional": seg.get("optional", False),
            "transport_ref": True,
        })
    return acts


def _collect_timeline_activities(day: dict) -> list:
    """Extract activities from a timeline day entry."""
    return _collect_timeline_entries(day) + _collect_segment_entries(day)


def _build_meal_act(m: dict, mt: str) -> Optional[dict]:
    """Build an activity dict from a meal slot, or None.
    Time fields no longer exist in POI data — conflict detection uses timeline only.
    """
    return None


def _collect_meal_acts(sib_day: dict) -> list:
    """Extract meal activities from a meals day entry."""
    acts = []
    for mt in MEAL_TYPES:
        m = sib_day.get(mt, {})
        if not isinstance(m, dict):
            continue
        act = _build_meal_act(m, mt)
        if act:
            acts.append(act)
    return acts


def _build_poi_act(poi: dict, agent: str) -> Optional[dict]:
    """Build an activity dict from a POI, or None.
    Time fields no longer exist in POI data — conflict detection uses timeline only.
    """
    return None


def _collect_poi_acts(sib_day: dict, agent: str) -> list:
    """Extract POI activities from a day entry."""
    return [a for a in (
        _build_poi_act(poi, agent) for poi in sib_day.get(agent, [])
    ) if a is not None]


def _collect_sibling_day_acts(name: str, d: dict) -> list:
    """Collect activities from a single sibling day."""
    if name == "meals":
        return _collect_meal_acts(d)
    return _collect_poi_acts(d, name)


def _find_sibling_day(data: dict, day_num: int) -> Optional[dict]:
    """Find the day entry matching day_num in sibling data."""
    for d in data.get("data", {}).get("days", []):
        if d.get("day") == day_num:
            return d
    return None


def _collect_sibling_acts(siblings: dict, day_num: int) -> list:
    """Collect activities from sibling agent files for a day."""
    acts = []
    for name, data in siblings.items():
        d = _find_sibling_day(data, day_num)
        if d:
            acts.extend(_collect_sibling_day_acts(name, d))
    return acts


def _fmt_time(minutes: int) -> str:
    """Format minutes since midnight back to HH:MM."""
    if minutes < 0:
        return "??:??"
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _get_category(act: dict) -> str:
    """Derive activity category from data."""
    if act.get("meal_ref"):
        return "meal"
    if act.get("transport_ref"):
        return "transport"
    if act.get("accommodation_ref"):
        return "accommodation"
    ag = act.get("ag", "")
    cat_map = {
        "meals": "meal", "attractions": "attraction",
        "entertainment": "entertainment", "shopping": "shopping",
        "segment": "transport",
    }
    return cat_map.get(ag, "activity")


def _is_fully_contained(a: dict, b: dict) -> bool:
    """True if b's time range is fully within a's."""
    a_s, a_e = _parse_hhmm(a["s"]), _parse_hhmm(a["e"])
    b_s, b_e = _parse_hhmm(b["s"]), _parse_hhmm(b["e"])
    if min(a_s, a_e, b_s, b_e) < 0:
        return False
    return b_s >= a_s and b_e <= a_e


def _classify_overlap(a: dict, b: dict) -> str:
    """Classify an overlap: 'warn' (containment/transport handoff) or 'block'."""
    if _is_fully_contained(a, b) or _is_fully_contained(b, a):
        return "warn"
    cats = {_get_category(a), _get_category(b)}
    if "transport" in cats:
        return "warn"
    return "block"


def _check_pair(a: dict, b: dict, day_num: int) -> Optional[tuple]:
    """Check a pair of activities for conflict. Returns (kind, entry) or None."""
    if not _times_overlap(a["s"], a["e"], b["s"], b["e"]):
        return None
    if a.get("optional") or b.get("optional"):
        return None
    kind = _classify_overlap(a, b)
    return (kind, {"day": day_num, "a": a, "b": b})


def _activity_pairs(activities: list):
    """Generate all unique pairs of activities."""
    for i, a in enumerate(activities):
        for b in activities[i + 1:]:
            yield a, b


def _check_all_pairs(activities: list, day_num: int) -> list:
    """Check all activity pairs for conflicts. Returns list of (kind, entry)."""
    return [r for a, b in _activity_pairs(activities)
            for r in [_check_pair(a, b, day_num)] if r]


def _detect_conflicts(activities: list, day_num: int) -> tuple:
    """Detect time conflicts. Returns (blocks, warnings) lists."""
    blocks, warnings = [], []
    pairs = _check_all_pairs(activities, day_num)
    for kind, entry in pairs:
        (blocks if kind == "block" else warnings).append(entry)
    return blocks, warnings


def _load_sibling_agents(trip_dir) -> dict:
    """Load sibling agent JSON files gracefully."""
    result = {}
    for name in POI_AGENTS:
        p = trip_dir / f"{name}.json"
        if not p.exists():
            continue
        try:
            result[name] = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return result


def _format_warning(w: dict) -> str:
    """Format a conflict warning as a string."""
    a, b = w["a"], w["b"]
    return (
        f'  Day {w["day"]}: '
        f'"{a["name"]}" ({a["ag"]}/{_get_category(a)}) '
        f'overlaps "{b["name"]}" '
        f'({b["ag"]}/{_get_category(b)}) '
        f'- warning only (containment or transport handoff)'
    )


def _format_block(c: dict) -> str:
    """Format a conflict block as a string."""
    a, b = c["a"], c["b"]
    a_range = f'{_fmt_time(_parse_hhmm(a["s"]))}-{_fmt_time(_parse_hhmm(a["e"]))}'
    b_range = f'{_fmt_time(_parse_hhmm(b["s"]))}-{_fmt_time(_parse_hhmm(b["e"]))}'
    return f'  Day {c["day"]}: "{a["name"]}" ({a_range}) overlaps "{b["name"]}" ({b_range})'


def _gather_day_conflicts(days, siblings) -> tuple:
    """Gather all blocks and warnings across all days."""
    all_blocks, all_warnings = [], []
    for day in days:
        day_num = day.get("day", "?")
        activities = _collect_timeline_activities(day)
        activities.extend(_collect_sibling_acts(siblings, day_num))
        blocks, warnings = _detect_conflicts(activities, day_num)
        all_blocks.extend(blocks)
        all_warnings.extend(warnings)
    return all_blocks, all_warnings


def _print_conflict_results(all_blocks, all_warnings) -> None:
    """Print all conflict warnings and blocks to stderr."""
    for w in all_warnings:
        print(f"  W  {_format_warning(w)}", file=sys.stderr)
    for c in all_blocks:
        print(f"  X  {_format_block(c)}", file=sys.stderr)
    if all_blocks:
        msg = f"\nSAVE BLOCKED: {len(all_blocks)} time conflict(s). Fix timeline."
        print(msg, file=sys.stderr)
    if all_warnings:
        print(f"{len(all_warnings)} overlap warning(s) (non-blocking)", file=sys.stderr)


def check_time_conflicts(agent_data, trip_dir, agent: str) -> list:
    """Hard-block saves with non-optional time conflicts."""
    if agent not in SCHEDULE_AGENTS:
        return []
    days = agent_data.get("data", {}).get("days", agent_data.get("days", []))
    if not days:
        return []
    siblings = _load_sibling_agents(trip_dir)
    all_blocks, all_warnings = _gather_day_conflicts(days, siblings)
    _print_conflict_results(all_blocks, all_warnings)
    return all_blocks


def _merge_existing_slots(agent_file, agent_data, data):
    """Merge update into existing multi-day file at the slot/key level.

    Automatic default behavior: called whenever the target file exists.
    Preserves sibling slots and day metadata not present in the update.
    Safe for both partial-day (POI) and complete-day (timeline) payloads.
    """
    existing_data = load_agent_json(agent_file, validate=False)
    merged = merge_agent_slots(existing_data, agent_data, agent_file.stem)
    day_count = len(data.get('data', {}).get('days', []))
    print(f"Merge mode (slots): Merged {day_count} day(s) at slot level", file=sys.stderr)
    return merged


def _do_save(agent_file, agent, agent_data, create_backup, issues):
    """Perform atomic write and report result. Returns True on success."""
    try:
        save_agent_json(
            file_path=agent_file, agent_name=agent,
            data=agent_data, validate=False, create_backup=create_backup,
        )
    except (AtomicWriteError, Exception) as e:
        kind = "Write" if isinstance(e, AtomicWriteError) else "Unexpected"
        print(f"{kind} error: {e}", file=sys.stderr)
        return False
    print(f"Saved: {agent_file}", file=sys.stderr)
    _report_save_warnings(issues)
    return True


def _report_save_warnings(issues: list) -> None:
    """Print MEDIUM/LOW warning counts after successful save."""
    if not issues:
        return
    med = len([i for i in issues if i.severity.value == "MEDIUM"])
    low = len([i for i in issues if i.severity.value == "LOW"])
    if med or low:
        print(f"   Warnings: {med} MEDIUM, {low} LOW", file=sys.stderr)


def _prepare_agent_data(data, agent_file, trip_slug):
    """Unwrap envelope, auto-merge if file exists, extract images.

    Slot-level merge is the sole merge path: when the target file already
    exists on disk, _merge_existing_slots() fires automatically. No flag needed.
    """
    agent_data = data.get("data") if "data" in data else data
    if agent_file.exists():
        agent_data = _merge_existing_slots(agent_file, agent_data, data)
    extract_image_urls(agent_file.stem, agent_data, trip_slug)
    return agent_data


def save_single_agent(
    trip_slug: str, agent: str, data: Dict[str, Any],
    skip_validation: bool = False, allow_high: bool = False,
    create_backup: bool = True,
) -> bool:
    """Save single agent data with validation."""
    trip_dir = DATA_DIR / trip_slug
    if not trip_dir.exists():
        print(f"Error: Trip directory not found: {trip_dir}", file=sys.stderr)
        return False
    agent_file = trip_dir / f"{agent}.json"
    try:
        agent_data = _prepare_agent_data(data, agent_file, trip_slug)
    except Exception as e:
        print(f"Merge failed: {e}", file=sys.stderr)
        return False
    envelope = {"agent": agent, "status": "complete", "data": agent_data}
    ok, issues, _ = validate_data(trip_slug, agent, envelope, skip_validation, allow_high)
    if not ok:
        print(f"\nSave aborted due to validation errors", file=sys.stderr)
        return False
    if check_time_conflicts(envelope, trip_dir, agent):
        return False
    return _do_save(agent_file, agent, agent_data, create_backup, issues)


def _validate_all_agents(trip_slug, batch_data, skip_validation, allow_high):
    """Phase 1: validate all agents. Returns dict of results."""
    print(f"\nPhase 1: Validating {len(batch_data)} agents...", file=sys.stderr)
    results = {}
    for agent, data in batch_data.items():
        print(f"   Validating {agent}...", end=" ", file=sys.stderr)
        ok, issues, metrics = validate_data(trip_slug, agent, data, skip_validation, allow_high)
        results[agent] = (ok, issues, metrics)
        print("OK" if ok else "FAIL", file=sys.stderr)
    return results


def _create_batch_backups(trip_dir, batch_data) -> dict:
    """Phase 2: create backups for existing files."""
    print(f"\nPhase 2: Creating backups...", file=sys.stderr)
    backups = {}
    for agent in batch_data.keys():
        agent_file = trip_dir / f"{agent}.json"
        if agent_file.exists():
            backup = agent_file.with_suffix(".json.bak")
            shutil.copy2(agent_file, backup)
            backups[agent] = backup
            print(f"   {agent}: {backup.name}", file=sys.stderr)
    return backups


def _save_batch_agent(trip_dir, agent, data) -> Optional[str]:
    """Save one agent in batch mode. Returns error string or None."""
    try:
        save_agent_json(
            file_path=trip_dir / f"{agent}.json", agent_name=agent,
            data=data.get("data") if "data" in data else data,
            validate=False, create_backup=False,
        )
        print(f"   {agent}: OK", file=sys.stderr)
        return None
    except Exception as e:
        print(f"   {agent}: FAIL {e}", file=sys.stderr)
        return str(e)


def _save_all_agents(trip_dir, batch_data) -> list:
    """Phase 3: save all agents. Returns list of (agent, error) tuples."""
    print(f"\nPhase 3: Saving {len(batch_data)} agents...", file=sys.stderr)
    errors = []
    for agent, data in batch_data.items():
        err = _save_batch_agent(trip_dir, agent, data)
        if err:
            errors.append((agent, err))
    return errors


def _rollback_batch(backup_paths, trip_dir) -> None:
    """Phase 4: restore all files from backups."""
    print(f"\nPhase 4: Rolling back...", file=sys.stderr)
    for agent, backup in backup_paths.items():
        shutil.copy2(backup, trip_dir / f"{agent}.json")
        print(f"   {agent}: restored from backup", file=sys.stderr)
    print(f"\nBatch save failed, all changes rolled back", file=sys.stderr)


def _report_batch_warnings(results) -> None:
    """Report total MEDIUM/LOW warnings from batch validation."""
    total = sum(
        len([i for i in iss if i.severity.value in ("MEDIUM", "LOW")])
        for _, iss, _ in results.values()
    )
    if total:
        print(f"   Total warnings: {total}", file=sys.stderr)


def save_batch(
    trip_slug: str, batch_data: Dict[str, Any],
    skip_validation: bool = False, allow_high: bool = False,
) -> bool:
    """Save multiple agents with rollback on failure."""
    trip_dir = DATA_DIR / trip_slug
    if not trip_dir.exists():
        print(f"Error: Trip directory not found: {trip_dir}", file=sys.stderr)
        return False
    print(f"Batch save: {len(batch_data)} agents", file=sys.stderr)
    results = _validate_all_agents(trip_slug, batch_data, skip_validation, allow_high)
    failed = [a for a, (ok, _, _) in results.items() if not ok]
    if failed:
        print(f"\nValidation failed: {', '.join(failed)}", file=sys.stderr)
        return False
    backups = _create_batch_backups(trip_dir, batch_data)
    errors = _save_all_agents(trip_dir, batch_data)
    if errors:
        _rollback_batch(backups, trip_dir)
        return False
    print(f"\nBatch save successful: {len(batch_data)} agents", file=sys.stderr)
    _report_batch_warnings(results)
    return True


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Unified data saving script with mandatory validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--trip", required=True, help="Trip slug")
    parser.add_argument("--agent", help="Agent name")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--batch", help="Batch input JSON file")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    parser.add_argument("--allow-high", action="store_true", help="Allow HIGH issues")
    parser.add_argument("--no-backup", action="store_true", help="Skip backups")
    return parser


def _validate_args(args) -> None:
    """Validate mutually exclusive argument combinations."""
    if args.batch and args.agent:
        print("Error: Cannot specify both --batch and --agent", file=sys.stderr)
        sys.exit(1)
    if not args.batch and not args.agent:
        print("Error: Must specify either --batch or --agent", file=sys.stderr)
        sys.exit(1)
    if args.batch and args.input:
        print("Error: --batch and --input are mutually exclusive", file=sys.stderr)
        sys.exit(1)


def _load_input(args) -> Dict[str, Any]:
    """Load input JSON from --input file or stdin."""
    if args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"Error: Input file not found: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return json.load(sys.stdin)


def _run_batch(args) -> bool:
    """Execute batch save mode."""
    batch_path = Path(args.batch)
    if not batch_path.exists():
        print(f"Error: Batch file not found: {batch_path}", file=sys.stderr)
        sys.exit(1)
    with open(batch_path, encoding="utf-8") as f:
        return save_batch(args.trip, json.load(f), args.no_validate, args.allow_high)


def main():
    args = _build_parser().parse_args()
    _validate_args(args)
    if args.batch:
        success = _run_batch(args)
    else:
        data = _load_input(args)
        success = save_single_agent(
            trip_slug=args.trip, agent=args.agent, data=data,
            skip_validation=args.no_validate, allow_high=args.allow_high,
            create_backup=not args.no_backup,
        )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
