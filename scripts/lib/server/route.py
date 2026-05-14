"""POST /api/route lazy intra-city routing handler (M2-contract.md §9).

Spec: spec-20260508-221237 §5.9 + §5.13 D #7.

Cache key is from_option_id:to_option_id:mode. Cache hits return immediately
without invoking gaode. Cache miss invokes the gaode-maps skill subprocess
with CLAUDE_AGENT_ID=timeline forced via env-var (per §5.13 C #5 server-side
identity hardcode); on success the new segment is persisted to
route_cache.json under the per-trip lock. The lock is released during the
external network round-trip (codex Q2). request_seq is echoed back unchanged
for UI race-filter (§5.13 D #6). day.json is NOT mutated here per codex Q1
pick (b): /api/route only writes route_cache.json.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from .common import TripStore, atomic_write_json, load_json_or_default


# Server-side hardcoded agent identity. Any agent_id in the request body is
# IGNORED (AC-M5.5 identity test).
TIMELINE_AGENT_ID = "timeline"

_GAODE_ROUTE_SCRIPT_HARDCODED = [
    Path(".claude/skills/gaode-maps/scripts/routing.py"),
    Path(".claude/skills/gaode-maps/scripts/route.py"),
    Path(".claude/skills/gaode-maps/scripts/inter-city-route.py"),
]


def _cache_key(from_id: str, to_id: str, mode: str) -> str:
    return f"{from_id}:{to_id}:{mode}"


def _route_cache_path(store: TripStore, trip_id: str) -> Path:
    return store.trip_dir(trip_id) / "route_cache.json"


def _load_cache(path: Path) -> dict[str, Any]:
    return load_json_or_default(path, {"schema_version": "v2.0", "entries": {}})


def _try_cache_hit(store: TripStore, req: dict) -> dict | None:
    cache = _load_cache(_route_cache_path(store, req["trip_id"]))
    key = _cache_key(req["from_option_id"], req["to_option_id"], req["mode"])
    hit = cache.get("entries", {}).get(key)
    if hit is None:
        return None
    return {
        "request_seq": req["request_seq"],
        "status": "ok",
        "segment": hit,
        "source": "cache",
    }


def _resolve_gaode_script(project_dir: Path) -> Path | None:
    checked = []
    for p in _GAODE_ROUTE_SCRIPT_CANDIDATES:
        candidate = p if p.is_absolute() else project_dir / p
        checked.append(candidate)
        if candidate.exists():
            return candidate
    logging.warning("gaode route script not found; checked: %s", checked)
    return None


def _build_gaode_env(project_dir: Path) -> dict:
    env = os.environ.copy()
    env["CLAUDE_AGENT_ID"] = TIMELINE_AGENT_ID
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return env


_MODE_TO_COMMAND = {
    "walk": "walking",
    "walking": "walking",
    "transit": "transit",
    "car": "driving",
    "taxi": "driving",
    "driving": "driving",
    "cycling": "cycling",
}


def _mode_to_command(mode: str) -> str:
    return _MODE_TO_COMMAND.get(mode, "driving")


def _coords_string(option_id: str, store: "TripStore", trip_id: str) -> str | None:
    """Return 'lon,lat' string for the given option_id by scanning day files.

    Gaode convention: longitude first.
    Returns None if the option cannot be resolved to coordinates.
    """
    trip_dir = store.trip_dir(trip_id)
    days_dir = trip_dir / "days"
    if not days_dir.exists():
        return None
    for day_file in sorted(days_dir.glob("day-*.json")):
        try:
            day = json.loads(day_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for slot in day.values():
            if not isinstance(slot, dict):
                continue
            for opt in slot.get("options", []):
                if opt.get("option_id") == option_id:
                    loc = opt.get("location_coords") or opt.get("coordinates")
                    if loc and isinstance(loc, dict):
                        lon = loc.get("lon") or loc.get("lng") or loc.get("longitude")
                        lat = loc.get("lat") or loc.get("latitude")
                        if lon is not None and lat is not None:
                            return f"{lon},{lat}"
    return None


def _run_gaode_subprocess(
    script: Path, command: str, from_coords: str, to_coords: str,
    env: dict, timeout_s: float
) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["python3", str(script), command, from_coords, to_coords],
            env=env, capture_output=True, text=True,
            timeout=timeout_s, check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def _parse_json_or_none(s: str) -> dict | None:
    try:
        return json.loads(s.strip())
    except (json.JSONDecodeError, ValueError):
        return None


def _invoke_gaode(
    script: Path, req: dict, store: "TripStore", project_dir: Path, timeout_s: float
) -> dict | None:
    command = _mode_to_command(req.get("mode", "driving"))
    from_coords = _coords_string(req["from_option_id"], store, req["trip_id"])
    to_coords = _coords_string(req["to_option_id"], store, req["trip_id"])
    if from_coords is None or to_coords is None:
        # Coordinates not resolvable from trip data; cannot call gaode
        return None
    env = _build_gaode_env(project_dir)
    result = _run_gaode_subprocess(script, command, from_coords, to_coords, env, timeout_s)
    if result is None or result.returncode != 0:
        return None
    return _parse_json_or_none(result.stdout)


def _persist_to_cache(
    store: TripStore, trip_id: str, key: str, segment: dict
) -> None:
    with store.lock(trip_id):
        cache_path = _route_cache_path(store, trip_id)
        cache = _load_cache(cache_path)
        cache.setdefault("entries", {})[key] = segment
        atomic_write_json(cache_path, cache)


def _unknown_response(req: dict, reason: str) -> dict:
    return {
        "request_seq": req["request_seq"],
        "status": "unknown",
        "segment": None,
        "reason": reason,
    }


def _error_response(req: dict, reason: str) -> dict:
    return {
        "request_seq": req["request_seq"],
        "status": "error",
        "segment": None,
        "reason": reason,
    }


def _ok_response(req: dict, segment: dict) -> dict:
    return {
        "request_seq": req["request_seq"],
        "status": "ok",
        "segment": segment,
        "source": "live",
    }


def handle_route(
    store: TripStore,
    req: dict,
    project_dir: Path,
    gaode_timeout_s: float = 10.0,
) -> dict[str, Any]:
    """Handle POST /api/route. Returns RouteResponse-shaped dict.

    Per AC-M5.5: any agent_id in `req` is IGNORED; server forces
    TIMELINE_AGENT_ID. Lock is held ONLY during the cache-write step.
    """
    cached = _try_cache_hit(store, req)
    if cached is not None:
        return cached
    script = _resolve_gaode_script(project_dir)
    if script is None:
        return _unknown_response(req, "gaode-skill-not-installed")
    segment = _invoke_gaode(script, req, store, project_dir, gaode_timeout_s)
    if segment is None:
        return _error_response(req, "gaode-call-failed")
    key = _cache_key(req["from_option_id"], req["to_option_id"], req["mode"])
    _persist_to_cache(store, req["trip_id"], key, segment)
    return _ok_response(req, segment)
