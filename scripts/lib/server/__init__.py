"""M4a server lib for spec-20260508-221237 §5.13 D.

Sub-modules:
  common  - per-trip mutex registry, atomic write, JSON helpers
  trip    - GET /api/trip/<trip_id> hydration via trip_contract.load_trip
  route   - POST /api/route lazy gaode dispatch (agent_id=timeline forced)
  budget  - POST /api/budget/recompute pure aggregation
  save    - POST /api/save autosave + 409-soft concurrency
  export  - POST /api/export/{pdf,ical} subprocess to M6 exporters

All write paths are serialized per-trip via common.trip_lock().
"""

from .common import (
    TripStore,
    atomic_write_json,
    load_json_or_default,
    new_session_id,
    iso_now,
)
from .trip import hydrate_trip
from .route import handle_route
from .budget import handle_budget
from .save import handle_save
from .export import handle_export

__all__ = [
    "TripStore",
    "atomic_write_json",
    "load_json_or_default",
    "new_session_id",
    "iso_now",
    "hydrate_trip",
    "handle_route",
    "handle_budget",
    "handle_save",
    "handle_export",
]
