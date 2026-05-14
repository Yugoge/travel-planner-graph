"""§5.13 B red-eye ownership rule (cp-07): owning_day == depart_day, always."""

from __future__ import annotations

from .errors import TripContractError


def pick_owning_day(segment: dict) -> int:
    """Return the day to which a transportation segment is attributed.

    For all segments (including red-eye crossing midnight), owning_day equals
    depart_day. The arrive_day renders a read-only 'arriving from prior day'
    header item with no duplicate budget contribution.
    """
    if "depart_day" not in segment:
        seg_id = segment.get("segment_id", "<no id>")
        raise TripContractError(f"segment missing depart_day: {seg_id}")
    return int(segment["depart_day"])
