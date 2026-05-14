"""File loaders for the per-trip on-disk layout (Q3a):
data/<trip>/{meta.json, days/day-NN.json, transportation.json, route_cache.json,
            exports/, cache/images/}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .constants import SCHEMA_VERSION


@dataclass
class TripBundle:
    """In-memory bundle of all v2 trip files."""
    trip_dir: Path
    meta: dict
    days: list[dict]
    transportation: dict
    route_cache: dict


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_meta(trip_dir: Path) -> dict:
    """Load data/<trip>/meta.json. Raises FileNotFoundError if missing."""
    return _load_json(trip_dir / "meta.json")


def load_day(trip_dir: Path, day_n: int) -> dict:
    """Load data/<trip>/days/day-<NN>.json (zero-padded 2 digits)."""
    return _load_json(trip_dir / "days" / f"day-{day_n:02d}.json")


def load_transportation(trip_dir: Path) -> dict:
    """Load data/<trip>/transportation.json. Returns empty bundle if absent."""
    p = trip_dir / "transportation.json"
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "segments": []}
    return _load_json(p)


def load_route_cache(trip_dir: Path) -> dict:
    """Load data/<trip>/route_cache.json. Returns empty bundle if absent."""
    p = trip_dir / "route_cache.json"
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": {}}
    return _load_json(p)


def load_trip(trip_dir: Path) -> TripBundle:
    """Load the full v2 trip bundle. Raises FileNotFoundError if meta.json missing."""
    meta = load_meta(trip_dir)
    day_count = meta["day_count"]
    days = [load_day(trip_dir, n) for n in range(1, day_count + 1)]
    return TripBundle(
        trip_dir=trip_dir,
        meta=meta,
        days=days,
        transportation=load_transportation(trip_dir),
        route_cache=load_route_cache(trip_dir),
    )
