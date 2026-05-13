#!/usr/bin/env python3
"""Unified Data Saving Script — Batch Validation and Atomic Writes."""

import json
import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

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
CONTINUITY_AGENTS = {"timeline", "transportation", "plan-skeleton"}
POI_AGENTS = {"meals", "attractions", "entertainment", "shopping", "cafe"}
TIMELINE_FIELD = "timeline"
TRAVEL_SEGMENTS_FIELD = "travel_segments"

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
    acts = []
    for name, d in day.get(TIMELINE_FIELD, {}).items():
        if isinstance(d, dict) and d.get("start_time"):
            acts.append(_build_timeline_act(name, d))
    return acts

def _collect_segment_entries(day: dict) -> list:
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
    return _collect_timeline_entries(day) + _collect_segment_entries(day)

def _build_meal_act(m: dict, mt: str) -> Optional[dict]:
    return None  # Time fields removed from POI data

def _collect_meal_acts(sib_day: dict) -> list:
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
    return None  # Time fields removed from POI data

def _collect_poi_acts(sib_day: dict, agent: str) -> list:
    return [a for a in (
        _build_poi_act(poi, agent) for poi in sib_day.get(agent, [])
    ) if a is not None]

def _collect_sibling_day_acts(name: str, d: dict) -> list:
    if name == "meals":
        return _collect_meal_acts(d)
    return _collect_poi_acts(d, name)

def _find_sibling_day(data: dict, day_num: int) -> Optional[dict]:
    for d in data.get("data", {}).get("days", []):
        if d.get("day") == day_num:
            return d
    return None

def _collect_sibling_acts(siblings: dict, day_num: int) -> list:
    acts = []
    for name, data in siblings.items():
        d = _find_sibling_day(data, day_num)
        if d:
            acts.extend(_collect_sibling_day_acts(name, d))
    return acts

def _fmt_time(minutes: int) -> str:
    if minutes < 0:
        return "??:??"
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

def _get_category(act: dict) -> str:
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
    a_s, a_e = _parse_hhmm(a["s"]), _parse_hhmm(a["e"])
    b_s, b_e = _parse_hhmm(b["s"]), _parse_hhmm(b["e"])
    if min(a_s, a_e, b_s, b_e) < 0:
        return False
    return b_s >= a_s and b_e <= a_e

def _classify_overlap(a: dict, b: dict) -> str:
    if _is_fully_contained(a, b) or _is_fully_contained(b, a):
        return "warn"
    cats = {_get_category(a), _get_category(b)}
    if "transport" in cats:
        return "warn"
    return "block"

def _check_pair(a: dict, b: dict, day_num: int) -> Optional[tuple]:
    if not _times_overlap(a["s"], a["e"], b["s"], b["e"]):
        return None
    if a.get("optional") or b.get("optional"):
        return None
    kind = _classify_overlap(a, b)
    return (kind, {"day": day_num, "a": a, "b": b})

def _activity_pairs(activities: list):
    for i, a in enumerate(activities):
        for b in activities[i + 1:]:
            yield a, b

def _check_all_pairs(activities: list, day_num: int) -> list:
    return [r for a, b in _activity_pairs(activities)
            for r in [_check_pair(a, b, day_num)] if r]

def _detect_conflicts(activities: list, day_num: int) -> tuple:
    blocks, warnings = [], []
    pairs = _check_all_pairs(activities, day_num)
    for kind, entry in pairs:
        (blocks if kind == "block" else warnings).append(entry)
    return blocks, warnings

def _load_sibling_agents(trip_dir) -> dict:
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
    a, b = w["a"], w["b"]
    return (
        f'  Day {w["day"]}: '
        f'"{a["name"]}" ({a["ag"]}/{_get_category(a)}) '
        f'overlaps "{b["name"]}" '
        f'({b["ag"]}/{_get_category(b)}) '
        f'- warning only (containment or transport handoff)'
    )

def _format_block(c: dict) -> str:
    a, b = c["a"], c["b"]
    a_range = f'{_fmt_time(_parse_hhmm(a["s"]))}-{_fmt_time(_parse_hhmm(a["e"]))}'
    b_range = f'{_fmt_time(_parse_hhmm(b["s"]))}-{_fmt_time(_parse_hhmm(b["e"]))}'
    return f'  Day {c["day"]}: "{a["name"]}" ({a_range}) overlaps "{b["name"]}" ({b_range})'

def _gather_day_conflicts(days, siblings) -> tuple:
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
    for w in all_warnings:
        print(f"  W  {_format_warning(w)}", file=sys.stderr)
    for c in all_blocks:
        print(f"  X  {_format_block(c)}", file=sys.stderr)
    if all_blocks:
        msg = f"\nSAVE BLOCKED: {len(all_blocks)} time conflict(s). Fix timeline."
        print(msg, file=sys.stderr)
    if all_warnings:
        print(f"{len(all_warnings)} overlap warning(s) (non-blocking)", file=sys.stderr)

def _norm_city(name: str) -> str:
    s = name.strip().lower()
    for ch in ("'", "\u2019", "\u2018", "`", " "):
        s = s.replace(ch, "")
    return s

def _get_day_end_location(day_info: dict, transport_day: dict) -> str:
    end = day_info.get("location", "")
    t_lc = transport_day.get("location_change") if transport_day else None
    if isinstance(t_lc, dict) and t_lc.get("to_base"):
        end = t_lc["to_base"]
    ps_lc = day_info.get("location_change")
    if isinstance(ps_lc, dict) and (ps_lc.get("to") or ps_lc.get("to_base")):
        end = ps_lc.get("to") or ps_lc.get("to_base")
    return end

def _day_has_incoming_lc(day_info: dict, transport_day: dict) -> bool:
    t_lc = transport_day.get("location_change") if transport_day else None
    if isinstance(t_lc, dict) and t_lc.get("from_base"):
        return True
    ps_lc = day_info.get("location_change")
    if isinstance(ps_lc, dict) and (ps_lc.get("from") or ps_lc.get("from_base")):
        return True
    return False

def _load_json_file(path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

def _build_skeleton_day_info(skeleton: dict) -> dict:
    return {
        d.get("day", 0): {
            "location": d.get("location", ""),
            "location_change": d.get("location_change"),
        }
        for d in skeleton.get("days", [])
    }

def _check_day_pair_continuity(dn, dn1, day_info, transport_days) -> Optional[str]:
    """Check one adjacent day pair for a location gap. Returns message or None."""
    end_loc = _get_day_end_location(day_info[dn], transport_days.get(dn, {}))
    start_loc = day_info[dn1].get("location", "")
    if not end_loc or not start_loc:
        return None
    if _norm_city(end_loc) == _norm_city(start_loc):
        return None
    if _day_has_incoming_lc(day_info[dn1], transport_days.get(dn1, {})):
        return None
    return (
        f"Location continuity gap: Day {dn} ends in {end_loc} "
        f"but Day {dn1} starts in {start_loc}. "
        f"Run update-skeleton.py --fix-continuity to repair."
    )

def _find_continuity_gaps(day_info: dict, transport_days: dict) -> list:
    """Scan adjacent day pairs for location gaps. Returns gap messages."""
    sorted_nums = sorted(day_info.keys())
    gaps = []
    for i in range(len(sorted_nums) - 1):
        dn, dn1 = sorted_nums[i], sorted_nums[i + 1]
        if dn1 != dn + 1:
            continue
        msg = _check_day_pair_continuity(dn, dn1, day_info, transport_days)
        if msg:
            gaps.append(msg)
    return gaps

def _report_continuity_gaps(gaps: list) -> None:
    """Print continuity gap block messages to stderr."""
    print(f"\nSAVE BLOCKED: {len(gaps)} location continuity gap(s):", file=sys.stderr)
    for g in gaps:
        print(f"  X  {g}", file=sys.stderr)

def check_location_continuity(agent: str, agent_data: dict, trip_dir) -> list:
    """Block saves with location discontinuities. Returns gap messages (non-empty = block)."""
    if agent not in CONTINUITY_AGENTS:
        return []
    skeleton = _load_json_file(trip_dir / "plan-skeleton.json")
    if not skeleton:
        return []
    t_data = agent_data if agent == "transportation" else _load_json_file(
        trip_dir / "transportation.json")
    t_days = t_data.get("data", {}).get("days", t_data.get("days", []))
    transport_days = {d.get("day", 0): d for d in t_days}
    day_info = _build_skeleton_day_info(skeleton)
    gaps = _find_continuity_gaps(day_info, transport_days)
    if gaps:
        _report_continuity_gaps(gaps)
    return gaps

def _load_plan_currency(trip_dir) -> str:
    """Load plan-level currency_local from requirements-skeleton.json."""
    req = _load_json_file(trip_dir / 'requirements-skeleton.json')
    return req.get('trip_summary', {}).get('currency_local', '')


def _load_skeleton_day_currencies(trip_dir) -> dict:
    """Load day-level currency_local overrides from plan-skeleton.json."""
    skel = _load_json_file(trip_dir / 'plan-skeleton.json')
    return {d.get('day', 0): d['currency_local'] for d in skel.get('days', []) if d.get('currency_local')}

def _collect_meal_currency_pois(day: dict) -> list:
    """Collect POIs from meal slots including alternatives."""
    pois = []
    for mt in ('breakfast', 'lunch', 'dinner'):
        m = day.get(mt)
        if not isinstance(m, dict):
            continue
        pois.append((mt, m.get('primary', m)))
        for i, a in enumerate(m.get('alternatives', [])):
            if isinstance(a, dict):
                pois.append((f'{mt}.alt[{i}]', a))
    return pois


def _collect_transport_currency_pois(day: dict) -> list:
    """Collect currency-bearing POIs from transportation day."""
    pois = []
    lc = day.get('location_change')
    if isinstance(lc, dict) and lc.get('currency_local'):
        pois.append(('location_change', lc))
    for rk, rv in (day.get('intra_city_routes') or {}).items():
        if isinstance(rv, dict) and rv.get('currency_local'):
            pois.append((rk, rv))
    return pois


def _collect_currency_pois(agent: str, day: dict) -> list:
    """Collect all POIs needing currency validation from a day."""
    if agent == 'accommodation':
        acc = day.get('accommodation')
        return [('accommodation', acc)] if isinstance(acc, dict) else []
    if agent == 'meals':
        return _collect_meal_currency_pois(day)
    if agent in ('attractions', 'entertainment', 'shopping', 'cafe'):
        return [(p.get('name_base', '?'), p) for p in day.get(agent, []) if isinstance(p, dict)]
    if agent == 'transportation':
        return _collect_transport_currency_pois(day)
    return []


def check_currency_mismatch(agent: str, agent_data: dict, trip_dir) -> list:
    """Block saves where POI currency doesn't match plan/day currency."""
    plan_currency = _load_plan_currency(trip_dir)
    if not plan_currency:
        return []
    day_currencies = _load_skeleton_day_currencies(trip_dir)
    mismatches = []
    days = agent_data.get('data', {}).get('days', agent_data.get('days', []))
    for day in days:
        if not isinstance(day, dict):
            continue
        dn = day.get('day', '?')
        expected = day_currencies.get(dn, plan_currency)
        for label, poi in _collect_currency_pois(agent, day):
            c = poi.get('currency_local', '')
            if c and c != expected:
                mismatches.append(f'Day {dn} {label}: currency_local={c} != expected {expected}')
    if mismatches:
        print(f"\nSAVE BLOCKED: {len(mismatches)} currency mismatch(es):", file=sys.stderr)
        for m in mismatches:
            print(f"  X  {m}", file=sys.stderr)
    return mismatches

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

    AC9: for meals, emits demoted-primary audit lines before the merge.
    """
    existing_data = load_agent_json(agent_file, validate=False)
    _emit_demoted_primary_audit_for_meals(agent_file.stem, existing_data, agent_data)
    merged = merge_agent_slots(existing_data, agent_data, agent_file.stem)
    day_count = len(data.get('data', {}).get('days', []))
    print(f"Merge mode (slots): Merged {day_count} day(s) at slot level", file=sys.stderr)
    return merged


def _emit_demoted_primary_audit_for_meals(stem, existing_data, update_data):
    """AC9 — meals only. Emit stderr audit lines for meal_slot primary
    replacements where the old primary is NOT explicitly listed in
    incoming alternatives[]. Save does NOT auto-preserve."""
    if stem != 'meals':
        return
    from lib.semantic_lint import audit_demoted_primaries
    msgs = audit_demoted_primaries(existing_data, update_data, MEAL_TYPES)
    for m in msgs:
        print(m, file=sys.stderr)

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

def _prepare_agent_data(data, agent_file, trip_slug, agent: str = ""):
    """Unwrap; spec 5.9 translate; auto-merge."""
    from lib.save_translate import walk_translate, reject_banned
    agent_data = data.get("data") if "data" in data else data
    walk_translate(agent_data)
    if agent:
        reject_banned(agent, agent_data)
    if agent_file.exists():
        agent_data = _merge_existing_slots(agent_file, agent_data, data)
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
        agent_data = _prepare_agent_data(data, agent_file, trip_slug, agent)
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
    if check_location_continuity(agent, envelope, trip_dir):
        return False
    if check_currency_mismatch(agent, envelope, trip_dir):
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
    for agent, data in batch_data.items():
        if check_currency_mismatch(agent, data, trip_dir):
            return False
    backups = _create_batch_backups(trip_dir, batch_data)
    errors = _save_all_agents(trip_dir, batch_data)
    if errors:
        _rollback_batch(backups, trip_dir)
        return False
    print(f"\nBatch save successful: {len(batch_data)} agents", file=sys.stderr)
    _report_batch_warnings(results)
    return True

def _add_core_args(parser):
    parser.add_argument("--trip", required=True, help="Trip slug")
    parser.add_argument("--agent", help="Agent name")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--batch", help="Batch input JSON file (DEPRECATED "
                        "per spec-20260506-092951 §5.3; gated behind "
                        "BYPASS_DAY_GUARD=1 - agents must NOT set this).")


def _add_flag_args(parser):
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    parser.add_argument("--allow-high", action="store_true", help="Allow HIGH issues")
    parser.add_argument("--no-backup", action="store_true", help="Skip backups")
    parser.add_argument("--day", type=int, default=None,
                        help="Per-day write (spec 5.3): integer 1..N. "
                             "MANDATORY for single-agent saves. --days "
                             "and --all-days do not exist by design.")


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Unified data saving script with mandatory validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_core_args(parser)
    _add_flag_args(parser)
    return parser


def _is_bypass_set() -> bool:
    """Spec 5.3 escape hatch: only the human user may set this; agents may not."""
    import os
    return os.environ.get('BYPASS_DAY_GUARD', '') == '1'


def _err_exit(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def _check_mutual_exclusion(args):
    if args.batch and args.agent:
        _err_exit("Cannot specify both --batch and --agent")
    if not args.batch and not args.agent:
        _err_exit("Must specify either --batch or --agent")
    if args.batch and args.input:
        _err_exit("--batch and --input are mutually exclusive")


def _check_batch_bypass(args):
    if args.batch and not _is_bypass_set():
        _err_exit("--batch is deprecated per spec-20260506-092951 §5.3 "
                  "(批量操作永久禁止). Use single-agent saves with --day N. "
                  "If you are the human user explicitly overriding, set "
                  "BYPASS_DAY_GUARD=1.")


def _check_day_arg(args):
    if args.agent and args.day is None:
        _err_exit("--day N is required for single-agent saves "
                  "(spec-20260506-092951 §5.3). Pass an integer 1..N.")
    if args.day is not None and args.day < 1:
        _err_exit(f"--day must be >= 1 (got {args.day})")


def _validate_args(args) -> None:
    """Validate mutually exclusive argument combinations."""
    _check_mutual_exclusion(args)
    _check_batch_bypass(args)
    _check_day_arg(args)

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
