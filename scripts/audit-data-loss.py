#!/usr/bin/env python3
"""Audit git history for silent POI data loss.

Root Cause: Before merge_agent_slots() (added 2026-04-16), POI agents that
emitted a partial day (e.g., only `dinner`) would overwrite the whole day
object via merge_agent_days(), silently wiping sibling slots. Confirmed
data loss: commit 47fccd4 (2026-04-13 13:14) in
data/china-20260412-092624/meals.json — Day 2 breakfast + lunch disappeared.

This script iterates the git history of POI JSON files (default: all six
POI agents) for a given trip, counts populated slots per day per commit,
and flags any commit where the populated-slot count decreased without an
explicit deletion intent recorded in the modification log (`log` field of
the envelope) or an obvious `days[i].X` removal listed in `changed_fields`.

Usage:
    audit-data-loss.py --trip <slug-or-path>  [--agent meals]  [--all]

Examples:
    python scripts/audit-data-loss.py --trip china-20260412-092624
    python scripts/audit-data-loss.py --trip data/china-20260412-092624 --agent accommodation
    python scripts/audit-data-loss.py --all

Exit codes:
    0 = success (audit ran; findings are printed if any)
    1 = bad arguments or target path not found
    2 = git not available / not a git repo
"""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Named-slot agents: each key counts independently
NAMED_SLOT_KEYS: Dict[str, List[str]] = {
    "meals": ["breakfast", "lunch", "dinner"],
    "accommodation": ["accommodation"],
}

# Array-based agents: the top-level key holds a list; we count len(list)
ARRAY_KEYS: Dict[str, str] = {
    "attractions": "attractions",
    "entertainment": "entertainment",
    "shopping": "shopping",
    "cafe": "cafe",
}


def _run_git(args: List[str], cwd: Path) -> Optional[str]:
    """Run a git subcommand; return stdout or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(cwd), check=True,
            capture_output=True, text=True,
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _resolve_trip_dir(project_root: Path, trip_arg: str) -> Optional[Path]:
    """Resolve --trip argument to an absolute directory path."""
    candidate = Path(trip_arg)
    if candidate.is_absolute() and candidate.is_dir():
        return candidate
    direct = project_root / trip_arg
    if direct.is_dir():
        return direct
    via_data = project_root / "data" / trip_arg
    if via_data.is_dir():
        return via_data
    return None


def _trip_has_any_poi_json(trip_dir: Path) -> bool:
    """True if the trip dir has any recognized POI JSON file."""
    agents = list(NAMED_SLOT_KEYS.keys()) + list(ARRAY_KEYS.keys())
    return any((trip_dir / f"{a}.json").exists() for a in agents)


def _list_all_trips(project_root: Path) -> List[Path]:
    """Return every data/<slug>/ directory that contains at least one POI JSON."""
    data_dir = project_root / "data"
    if not data_dir.is_dir():
        return []
    trips = []
    for child in sorted(data_dir.iterdir()):
        if child.is_dir() and _trip_has_any_poi_json(child):
            trips.append(child)
    return trips


def _commit_history(project_root: Path, rel_path: str) -> List[str]:
    """List commits (newest-first) that touched `rel_path`, or [] if none."""
    out = _run_git(["log", "--format=%H", "--", rel_path], project_root)
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _read_json_at_commit(
    project_root: Path, commit: str, rel_path: str
) -> Optional[dict]:
    """Read `rel_path` as JSON at the given commit; return None if unreadable."""
    raw = _run_git(["show", f"{commit}:{rel_path}"], project_root)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _unwrap_envelope(payload: dict) -> dict:
    """Return the inner `data` dict, or the payload itself if not wrapped."""
    if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], dict):
        return payload["data"]
    return payload


def _modification_log(payload: dict) -> List[dict]:
    """Return the log entries recorded in the envelope (if any)."""
    if not isinstance(payload, dict):
        return []
    log = payload.get("log")
    return log if isinstance(log, list) else []


def _is_populated(value) -> bool:
    """A named slot counts as populated when it is a non-empty dict or list."""
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return False


def _count_day_slots(day: dict, agent: str) -> int:
    """Count populated slots on one day entry for a given agent type."""
    if agent in NAMED_SLOT_KEYS:
        return sum(1 for key in NAMED_SLOT_KEYS[agent] if _is_populated(day.get(key)))
    array_key = ARRAY_KEYS.get(agent)
    if array_key is not None:
        value = day.get(array_key)
        if isinstance(value, list):
            return len(value)
    return 0


def _slot_counts_per_day(data: dict, agent: str) -> Dict[int, int]:
    """Map day number -> populated slot count."""
    counts: Dict[int, int] = {}
    if not isinstance(data, dict):
        return counts
    for day in data.get("days", []) or []:
        if not isinstance(day, dict):
            continue
        num = day.get("day")
        if isinstance(num, int):
            counts[num] = _count_day_slots(day, agent)
    return counts


def _deletion_intent_fields(log_entries: Iterable[dict]) -> List[str]:
    """Collect all `changed_fields` entries that plausibly denote deletion intent."""
    hits: List[str] = []
    for entry in log_entries:
        if not isinstance(entry, dict):
            continue
        for field in entry.get("changed_fields", []) or []:
            hits.append(str(field))
        action = str(entry.get("action", "")).lower()
        if "delete" in action or "remove" in action or "clear" in action:
            hits.append(f"<action:{action}>")
    return hits


def _log_mentions_slot(log_fields: List[str], day_num: int, slot: str) -> bool:
    """Heuristic: does the log mention this day's slot? E.g. `days[1].dinner`."""
    needle_indexed = f"days[{day_num - 1}].{slot}".lower()
    needle_named = f"day{day_num}.{slot}".lower()
    for field in log_fields:
        low = field.lower()
        if needle_indexed in low or needle_named in low:
            return True
        if slot.lower() in low and (f"day {day_num}" in low or f"d{day_num}" in low):
            return True
    return False


def _flag_day_drop(
    agent: str, day_num: int, prev_count: int, curr_count: int,
    log_fields: List[str],
) -> Optional[dict]:
    """If `curr < prev`, return a flag dict unless the log explains the drop."""
    if curr_count >= prev_count:
        return None
    slots = NAMED_SLOT_KEYS.get(agent) or [ARRAY_KEYS.get(agent) or agent]
    if any(_log_mentions_slot(log_fields, day_num, slot) for slot in slots):
        return None
    return {
        "day": day_num,
        "prev_count": prev_count,
        "curr_count": curr_count,
        "delta": curr_count - prev_count,
    }


def _diff_counts(
    agent: str, commit: str, rel_path: str,
    prev: Dict[int, int], curr: Dict[int, int], log_fields: List[str],
) -> List[dict]:
    """Compare prev/curr day counts; produce findings for each unexplained drop."""
    findings: List[dict] = []
    for day_num, curr_count in curr.items():
        prev_count = prev.get(day_num, 0)
        flag = _flag_day_drop(agent, day_num, prev_count, curr_count, log_fields)
        if flag is None:
            continue
        flag.update({"commit": commit, "path": rel_path, "agent": agent})
        findings.append(flag)
    return findings


def _audit_file(
    project_root: Path, trip_dir: Path, agent: str,
) -> List[dict]:
    """Walk git history of `<trip>/<agent>.json` and return a list of findings."""
    rel_path = str((trip_dir / f"{agent}.json").relative_to(project_root))
    commits = _commit_history(project_root, rel_path)
    if len(commits) < 2:
        return []
    findings: List[dict] = []
    # Iterate oldest-first so we can reason about each "previous -> next" step
    prev_counts: Dict[int, int] = {}
    for commit in reversed(commits):
        payload = _read_json_at_commit(project_root, commit, rel_path)
        if payload is None:
            continue
        inner = _unwrap_envelope(payload)
        curr_counts = _slot_counts_per_day(inner, agent)
        log_fields = _deletion_intent_fields(_modification_log(payload))
        findings.extend(_diff_counts(
            agent, commit, rel_path, prev_counts, curr_counts, log_fields,
        ))
        prev_counts = curr_counts
    return findings


def _restore_suggestion(commit: str, rel_path: str) -> str:
    """Suggest a git-show command to recover the pre-loss version (parent commit)."""
    parent = f"{commit}~1"
    return (
        "git show "
        + shlex.quote(f"{parent}:{rel_path}")
        + " > /tmp/restore-"
        + Path(rel_path).stem
        + ".json"
    )


def _print_findings(trip_dir: Path, findings: List[dict]) -> None:
    """Print findings + restore suggestion commands."""
    if not findings:
        print(f"[{trip_dir.name}] No data loss detected across audited POI files.")
        return
    print(f"[{trip_dir.name}] FLAGGED {len(findings)} possible data-loss event(s):")
    for f in findings:
        print(
            f"  - agent={f['agent']}  day={f['day']}  "
            f"slot_count {f['prev_count']} -> {f['curr_count']}  "
            f"commit={f['commit'][:10]}  path={f['path']}"
        )
        print(f"      restore: {_restore_suggestion(f['commit'], f['path'])}")


def _agents_to_audit(explicit: Optional[str]) -> List[str]:
    """Resolve the --agent flag to a list of agents to audit."""
    if explicit:
        return [explicit]
    return list(NAMED_SLOT_KEYS.keys()) + list(ARRAY_KEYS.keys())


def _audit_trip(project_root: Path, trip_dir: Path, agents: List[str]) -> int:
    """Audit every relevant POI JSON in `trip_dir`; returns the finding count."""
    all_findings: List[dict] = []
    for agent in agents:
        if not (trip_dir / f"{agent}.json").exists():
            continue
        all_findings.extend(_audit_file(project_root, trip_dir, agent))
    _print_findings(trip_dir, all_findings)
    return len(all_findings)


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit git history for silent POI data loss",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--trip",
        help="Trip slug or absolute path; resolved against <repo>/data/ when relative",
    )
    parser.add_argument(
        "--agent",
        help=(
            "Restrict audit to one agent (meals, accommodation, attractions, "
            "entertainment, shopping, cafe). Default: all."
        ),
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Audit every trip under <repo>/data/ that has at least one POI JSON",
    )
    parser.add_argument(
        "--project-root", default=None,
        help="Path to repo root (default: parent of this script's scripts/ dir)",
    )
    return parser.parse_args(argv)


def _resolve_project_root(arg: Optional[str]) -> Path:
    if arg:
        return Path(arg).resolve()
    return Path(__file__).resolve().parent.parent


def _run_audit_all(project_root: Path, agents: List[str]) -> int:
    trips = _list_all_trips(project_root)
    if not trips:
        print("No trips with POI JSON found under data/.", file=sys.stderr)
        return 0
    for trip in trips:
        _audit_trip(project_root, trip, agents)
    return 0


def _run_audit_single(
    project_root: Path, trip_arg: str, agents: List[str]
) -> int:
    trip_dir = _resolve_trip_dir(project_root, trip_arg)
    if trip_dir is None:
        print(f"Error: cannot locate trip directory for '{trip_arg}'", file=sys.stderr)
        return 1
    _audit_trip(project_root, trip_dir, agents)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    project_root = _resolve_project_root(args.project_root)
    if not (project_root / ".git").exists():
        print(f"Error: {project_root} is not a git repo (no .git/)", file=sys.stderr)
        return 2
    agents = _agents_to_audit(args.agent)
    if args.all:
        return _run_audit_all(project_root, agents)
    if not args.trip:
        print("Error: --trip or --all is required", file=sys.stderr)
        return 1
    return _run_audit_single(project_root, args.trip, agents)


if __name__ == "__main__":
    sys.exit(main())
