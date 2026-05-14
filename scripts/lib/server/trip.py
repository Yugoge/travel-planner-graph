"""GET /api/trip/<trip_id> hydration handler.

Calls trip_contract.load_trip to assemble meta + days + transportation +
route_cache into a single response payload (M2-contract.md §9 TripResponse).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import TripStore


def hydrate_trip(store: TripStore, trip_id: str) -> dict[str, Any]:
    """Return TripResponse dict per M2-contract §9.

    Errors propagate: FileNotFoundError if meta.json absent.
    """
    # Import lazily so unit tests on common.py do not require trip_contract.
    from lib import trip_contract as tc  # type: ignore  # noqa: E402

    trip_dir = store.trip_dir(trip_id)
    bundle = tc.load_trip(trip_dir)
    return {
        "meta": bundle.meta,
        "days": bundle.days,
        "transportation": bundle.transportation,
        "route_cache": bundle.route_cache,
    }
