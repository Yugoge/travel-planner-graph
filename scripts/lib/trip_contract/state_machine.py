"""§5.2 per-day planning state machine.

Per codex Q2: gating uses min(day.stage), NOT max. A trip may only advance to a
downstream pipeline stage (timeline / transportation / finalized) when EVERY
day has reached that stage.
"""

from __future__ import annotations

from typing import Optional

from .constants import STAGES, STAGE_INDEX
from .errors import TripContractError


def validate_state_transition(
    old_stage: str,
    new_stage: str,
    has_user_consent: bool = False,
) -> Optional[str]:
    """Return None if transition is legal; otherwise a string explaining the rejection.

    - Same stage is always allowed (idempotent re-save).
    - Forward transitions are always allowed.
    - Backward transitions require has_user_consent=True (e.g. user re-edits a
      finalized day; only the M4 server may set this).
    """
    if old_stage not in STAGE_INDEX:
        return f"unknown old_stage: {old_stage!r}"
    if new_stage not in STAGE_INDEX:
        return f"unknown new_stage: {new_stage!r}"
    if old_stage == new_stage:
        return None
    old_i = STAGE_INDEX[old_stage]
    new_i = STAGE_INDEX[new_stage]
    if new_i > old_i:
        return None
    if has_user_consent:
        return None
    return (
        f"backward transition {old_stage!r} -> {new_stage!r} requires explicit user consent"
    )


def blocking_stage(days: list[dict]) -> str:
    """min(day.stage); used to gate timeline/transportation/finalize."""
    if not days:
        return STAGES[0]
    return min(
        (d.get("stage", STAGES[0]) for d in days),
        key=lambda s: STAGE_INDEX.get(s, -1),
    )


def furthest_stage(days: list[dict]) -> str:
    """max(day.stage); for display only, never use for gating."""
    if not days:
        return STAGES[0]
    return max(
        (d.get("stage", STAGES[0]) for d in days),
        key=lambda s: STAGE_INDEX.get(s, -1),
    )


def all_days_at_least(days: list[dict], min_stage: str) -> bool:
    """True iff every day's stage >= min_stage."""
    if min_stage not in STAGE_INDEX:
        raise TripContractError(f"unknown min_stage: {min_stage!r}")
    floor = STAGE_INDEX[min_stage]
    for d in days:
        s = d.get("stage", STAGES[0])
        if STAGE_INDEX.get(s, -1) < floor:
            return False
    return True
