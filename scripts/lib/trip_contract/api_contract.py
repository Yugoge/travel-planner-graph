"""API contract dataclasses for the 5 endpoints (§5.13 D #7).

Consumed by:
  - M4 server (scripts/serve-trip.py): request parsing + response shaping
  - M3 timeline.md / budget.md: route_pair / recompute_day signatures
  - M6 exporters: ExportRequest / ExportResponse
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RouteRequest:
    """POST /api/route — lazy intra-city routing on user drag-drop (§5.9)."""
    trip_id: str
    day: int
    from_option_id: str
    to_option_id: str
    mode: str           # walk | taxi | metro | bus | transit | car | ferry
    request_seq: int    # monotonic per (from,to) pair; UI ignores stale responses


@dataclass
class RouteResponse:
    request_seq: int
    status: str         # ok | unknown | error
    segment: Optional[dict] = None  # populated when status=ok


@dataclass
class BudgetRequest:
    """POST /api/budget/recompute — server-side single-writer (§5.10)."""
    trip_id: str
    day: Optional[int] = None
    delta: Optional[dict] = None


@dataclass
class BudgetResponse:
    schema_version: str
    trip_id: str
    trip_total: float
    currency_local: str
    days: list[dict]


@dataclass
class SaveMutation:
    """One mutation in a /api/save batch."""
    type: str
    slot: Optional[str] = None
    option_id: Optional[str] = None
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None
    extra: Optional[dict] = None


@dataclass
class SaveRequest:
    """POST /api/save — autosave with 300ms debounce (§5.13 D #2)."""
    trip_id: str
    day: int
    mutations: list[dict]
    editor_session: str


@dataclass
class SaveResponse:
    saved_ts: str
    conflict: Optional[str] = None  # '409-soft' on editor_session mismatch


@dataclass
class TripResponse:
    """GET /api/trip/<trip_id> — full hydration on page load."""
    meta: dict
    days: list[dict]
    transportation: dict
    route_cache: dict


@dataclass
class ExportRequest:
    """POST /api/export/{pdf|ical}."""
    trip_id: str


@dataclass
class ExportResponse:
    file_path: str
    bytes_written: int
