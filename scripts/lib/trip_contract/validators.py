"""M2 cross-slot + state-machine + day-type validators.

Public:
  validate_meta_v2(meta) -> [ValidationError]
  validate_day_v2(day, meta, position, is_first_night) -> [ValidationError]
  validate_trip_v2(bundle) -> [ValidationError]

JSON Schema covers shape; this module covers cross-slot semantics that JSON
Schema cannot express. See M2-contract.md for the full rule list.
"""

from __future__ import annotations

from typing import Optional

from .constants import (
    ACCOMMODATION_SLOT,
    CITY_ROLES,
    NAMED_SLOTS,
    SCHEMA_VERSION,
    SKIP_THRESHOLDS,
    STAGE_INDEX,
    VALID_SKIP_REASONS,
)
from .day_type import expected_skips_for_day, _hhmm_to_minutes, _ts_to_hhmm
from .errors import ValidationError
from .legacy import detect_legacy_shape


def _slot_dict(day_dict: dict, slot_id: str) -> Optional[dict]:
    if slot_id == ACCOMMODATION_SLOT:
        return day_dict.get(ACCOMMODATION_SLOT)
    return day_dict.get("slots", {}).get(slot_id)


def _slot_options(slot: dict) -> list[dict]:
    return slot.get("options", []) or []


def _slot_path(position: str, slot_id: str) -> str:
    if slot_id in NAMED_SLOTS:
        return f"{position}.slots.{slot_id}"
    return f"{position}.{slot_id}"


def _option_path(position: str, slot_id: str, idx: int) -> str:
    return f"{_slot_path(position, slot_id)}.options[{idx}]"


def _check_city_context(opt: dict, path: str) -> list[ValidationError]:
    cc = opt.get("city_context")
    if not isinstance(cc, dict):
        return [ValidationError(
            code="CITY_CONTEXT_REQUIRED",
            path=f"{path}.city_context",
            message="every option must carry city_context (Q3c)",
        )]
    if cc.get("role") not in CITY_ROLES:
        return [ValidationError(
            code="CITY_CONTEXT_ROLE_INVALID",
            path=f"{path}.city_context.role",
            message=f"role must be one of {sorted(CITY_ROLES)}, got {cc.get('role')!r}",
        )]
    return []


def _check_fit_score(opt: dict, path: str) -> list[ValidationError]:
    fit = opt.get("fit_score")
    if not isinstance(fit, (int, float)) or not (0.0 <= float(fit) <= 1.0):
        return [ValidationError(
            code="FIT_SCORE_OUT_OF_RANGE",
            path=f"{path}.fit_score",
            message=f"fit_score must be in [0,1], got {fit!r}",
        )]
    return []


def _check_rationale(opt: dict, path: str) -> list[ValidationError]:
    errs: list[ValidationError] = []
    if not opt.get("why_fits_user"):
        errs.append(ValidationError(
            code="WHY_FITS_USER_REQUIRED",
            path=f"{path}.why_fits_user",
            message="non-empty rationale required (Q3h)",
        ))
    if not opt.get("source_agent"):
        errs.append(ValidationError(
            code="SOURCE_AGENT_REQUIRED",
            path=f"{path}.source_agent",
            message="source_agent must be set",
        ))
    return errs


def _validate_option(opt: dict, path: str) -> list[ValidationError]:
    """Per-option rule checks beyond JSON Schema."""
    errs: list[ValidationError] = []
    errs.extend(_check_city_context(opt, path))
    errs.extend(_check_fit_score(opt, path))
    errs.extend(_check_rationale(opt, path))
    return errs


def _check_legacy_shape(day_dict: dict, position: str) -> list[ValidationError]:
    legacy_paths = detect_legacy_shape(day_dict)
    return [
        ValidationError(
            code="LEGACY_SHAPE_FORBIDDEN",
            path=f"{position}.{p}",
            message="{primary, alternatives[]} legacy shape rejected; v2 uses options[] inside slot_envelope",
        )
        for p in legacy_paths
    ]


def _check_schema_version(day_dict: dict, position: str) -> list[ValidationError]:
    sv = day_dict.get("schema_version")
    if sv != SCHEMA_VERSION:
        return [ValidationError(
            code="SCHEMA_VERSION_MISMATCH",
            path=f"{position}.schema_version",
            message=f"expected {SCHEMA_VERSION!r}, got {sv!r}",
        )]
    return []


def _check_slot_presence(day_dict: dict, position: str) -> list[ValidationError]:
    errs: list[ValidationError] = []
    slots = day_dict.get("slots", {})
    for slot_id in NAMED_SLOTS:
        if slot_id not in slots:
            errs.append(ValidationError(
                code="SLOT_REQUIRED_PRESENT",
                path=f"{position}.slots.{slot_id}",
                message=f"slot {slot_id!r} absent; v2 requires all 6 named slots present",
            ))
    if ACCOMMODATION_SLOT not in day_dict:
        errs.append(ValidationError(
            code="SLOT_REQUIRED_PRESENT",
            path=f"{position}.{ACCOMMODATION_SLOT}",
            message="accommodation slot absent; required by v2",
        ))
    return errs


def _check_skipped_actual(slot: dict, slot_id: str, expected_reason: Optional[str], position: str) -> list[ValidationError]:
    """Rules for a slot whose skipped=True."""
    errs: list[ValidationError] = []
    actual_reason = slot.get("skipped_reason")
    if actual_reason is None:
        errs.append(ValidationError(
            code="SKIPPED_REASON_REQUIRED",
            path=f"{position}.slots.{slot_id}.skipped_reason",
            message="skipped=true requires non-null skipped_reason",
        ))
    elif actual_reason not in VALID_SKIP_REASONS:
        errs.append(ValidationError(
            code="SKIPPED_REASON_INVALID",
            path=f"{position}.slots.{slot_id}.skipped_reason",
            message=f"reason {actual_reason!r} not in {sorted(VALID_SKIP_REASONS)}",
        ))
    elif expected_reason is None and actual_reason not in {"user-omit", "buffer-rest"}:
        errs.append(ValidationError(
            code="UNJUSTIFIED_SKIP",
            path=f"{position}.slots.{slot_id}",
            message=(
                f"slot skipped reason={actual_reason!r} but day_type does not require it; "
                "use 'user-omit' or 'buffer-rest' for discretionary skips"
            ),
        ))
    return errs


def _check_skipped_missing(slot_id: str, expected_reason: str, day_type: str, position: str) -> list[ValidationError]:
    """A slot is non-skipped but day_type+arrival_ts mandates skip."""
    return [ValidationError(
        code="MISSING_REQUIRED_SKIP",
        path=f"{position}.slots.{slot_id}",
        message=(
            f"day_type={day_type!r} with arrival_ts mandates "
            f"slot {slot_id!r} be skipped with reason={expected_reason!r}"
        ),
    )]


def _check_day_type_tolerance(day_dict: dict, position: str) -> list[ValidationError]:
    errs: list[ValidationError] = []
    expected = expected_skips_for_day(day_dict)
    day_type = day_dict.get("day_type", "normal")
    for slot_id in NAMED_SLOTS:
        slot = _slot_dict(day_dict, slot_id) or {}
        actual_skipped = bool(slot.get("skipped", False))
        expected_reason = expected.get(slot_id)
        if actual_skipped:
            errs.extend(_check_skipped_actual(slot, slot_id, expected_reason, position))
        elif expected_reason is not None:
            errs.extend(_check_skipped_missing(slot_id, expected_reason, day_type, position))
    return errs


def _check_late_arrival_dinner(day_dict: dict, position: str) -> list[ValidationError]:
    arr_hhmm = _ts_to_hhmm(day_dict.get("arrival_ts"))
    if arr_hhmm is None:
        return []
    threshold = _hhmm_to_minutes(SKIP_THRESHOLDS["dinner_late_placeholder_at_or_after"])
    if _hhmm_to_minutes(arr_hhmm) < threshold:
        return []
    dinner = day_dict.get("slots", {}).get("dinner", {}) or {}
    if dinner.get("skipped"):
        return [ValidationError(
            code="LATE_ARRIVAL_DINNER_NOT_SKIPPED",
            path=f"{position}.slots.dinner",
            message=f"arrival_ts {arr_hhmm} >= 21:00 means dinner is late-arrival placeholder, NOT skipped",
        )]
    if not dinner.get("late_arrival_placeholder"):
        return [ValidationError(
            code="LATE_ARRIVAL_PLACEHOLDER_REQUIRED",
            path=f"{position}.slots.dinner.late_arrival_placeholder",
            message=f"arrival_ts {arr_hhmm} >= 21:00 requires late_arrival_placeholder=true on dinner",
        )]
    return []


def _check_one_meal_slot(slot: dict, meal_slot: str, position: str) -> tuple[list[ValidationError], int]:
    opts = _slot_options(slot)
    errs: list[ValidationError] = []
    if len(opts) < 2:
        errs.append(ValidationError(
            code="MEAL_SLOT_FLOOR",
            path=f"{position}.slots.{meal_slot}.options",
            message=f"meal slot needs >=2 options, got {len(opts)} (§5.7 A)",
        ))
    return errs, len(opts)


def _check_meal_floors(day_dict: dict, position: str) -> list[ValidationError]:
    """Per spec: each meal slot >=2 options; per-day floor = 2 * non_skipped_count."""
    errs: list[ValidationError] = []
    slots = day_dict.get("slots", {})
    total = 0
    non_skipped = 0
    for meal_slot in ("breakfast", "lunch", "dinner"):
        slot = slots.get(meal_slot, {}) or {}
        if slot.get("skipped"):
            continue
        non_skipped += 1
        slot_errs, count = _check_one_meal_slot(slot, meal_slot, position)
        errs.extend(slot_errs)
        total += count
    floor = 2 * non_skipped
    if non_skipped > 0 and total < floor:
        errs.append(ValidationError(
            code="MEAL_DAY_FLOOR",
            path=f"{position}.slots",
            message=(
                f"day needs >=2 options per non-skipped meal slot ({non_skipped} active "
                f"-> floor={floor}), got {total} (§5.7 A)"
            ),
        ))
    return errs


def _check_first_night_accommodation(day_dict: dict, position: str, is_first_night: bool) -> list[ValidationError]:
    if not is_first_night:
        return []
    acc = day_dict.get(ACCOMMODATION_SLOT, {}) or {}
    if acc.get("skipped"):
        return []
    opts = _slot_options(acc)
    if len(opts) < 3:
        return [ValidationError(
            code="ACCOMMODATION_FIRST_NIGHT_FLOOR",
            path=f"{position}.{ACCOMMODATION_SLOT}.options",
            message=f"first-night accommodation needs >=3 options, got {len(opts)} (§5.7 B)",
        )]
    return []


def _check_stage_gate(day_dict: dict, position: str) -> list[ValidationError]:
    """If stage >= user-selected, every non-skipped slot must have selected_option_id."""
    stage = day_dict.get("stage", "draft-options")
    stage_idx = STAGE_INDEX.get(stage, 0)
    user_selected_idx = STAGE_INDEX["user-selected"]
    if stage_idx < user_selected_idx:
        return []
    errs: list[ValidationError] = []
    for slot_id in NAMED_SLOTS + [ACCOMMODATION_SLOT]:
        slot = _slot_dict(day_dict, slot_id) or {}
        if slot.get("skipped"):
            continue
        if slot.get("selected_option_id") is None:
            errs.append(ValidationError(
                code="STAGE_GATE_VIOLATION",
                path=f"{_slot_path(position, slot_id)}.selected_option_id",
                message=f"stage={stage!r} requires non-skipped slot {slot_id!r} to have selected_option_id",
            ))
    return errs


def _check_all_options(day_dict: dict, position: str) -> list[ValidationError]:
    errs: list[ValidationError] = []
    for slot_id in NAMED_SLOTS + [ACCOMMODATION_SLOT]:
        slot = _slot_dict(day_dict, slot_id) or {}
        for i, opt in enumerate(_slot_options(slot)):
            errs.extend(_validate_option(opt, _option_path(position, slot_id, i)))
    return errs


def validate_day_v2(
    day_dict: dict,
    meta_dict: dict,
    position: str = "$",
    is_first_night: bool = False,
) -> list[ValidationError]:
    """Orchestrator: run all M2 cross-slot validations on one day."""
    errs: list[ValidationError] = []
    errs.extend(_check_legacy_shape(day_dict, position))
    errs.extend(_check_schema_version(day_dict, position))
    errs.extend(_check_slot_presence(day_dict, position))
    errs.extend(_check_day_type_tolerance(day_dict, position))
    errs.extend(_check_late_arrival_dinner(day_dict, position))
    errs.extend(_check_meal_floors(day_dict, position))
    errs.extend(_check_first_night_accommodation(day_dict, position, is_first_night))
    errs.extend(_check_stage_gate(day_dict, position))
    errs.extend(_check_all_options(day_dict, position))
    return errs


def _check_legs_contiguous(legs: list[dict], day_count: int) -> list[ValidationError]:
    errs: list[ValidationError] = []
    if not legs:
        return errs
    sorted_legs = sorted(legs, key=lambda L: L["leg_index"])
    prev_last = 0
    for leg in sorted_legs:
        if leg["first_day"] != prev_last + 1:
            errs.append(ValidationError(
                code="LEGS_NOT_CONTIGUOUS",
                path=f"$.legs[{leg['leg_index']}]",
                message=f"first_day={leg['first_day']} expected {prev_last + 1}",
            ))
        if leg["last_day"] < leg["first_day"]:
            errs.append(ValidationError(
                code="LEG_INVERTED",
                path=f"$.legs[{leg['leg_index']}]",
                message="last_day < first_day",
            ))
        prev_last = leg["last_day"]
    if prev_last != day_count:
        errs.append(ValidationError(
            code="LEGS_DAY_COUNT_MISMATCH",
            path="$.legs",
            message=f"sum of leg days {prev_last} != day_count {day_count}",
        ))
    return errs


def validate_meta_v2(meta_dict: dict) -> list[ValidationError]:
    """Cross-field rules for meta.json beyond JSON Schema."""
    errs: list[ValidationError] = []
    sv = meta_dict.get("schema_version")
    if sv != SCHEMA_VERSION:
        errs.append(ValidationError(
            code="SCHEMA_VERSION_MISMATCH",
            path="$.schema_version",
            message=f"expected {SCHEMA_VERSION!r}, got {sv!r}",
        ))
    legs = meta_dict.get("legs", [])
    day_count = meta_dict.get("day_count", 0)
    errs.extend(_check_legs_contiguous(legs, day_count))
    return errs


def _leg_for_day(legs: list[dict], day_n: int) -> Optional[dict]:
    for leg in legs:
        if leg["first_day"] <= day_n <= leg["last_day"]:
            return leg
    return None


def _check_same_city_continuation(prev: dict, curr: dict) -> list[ValidationError]:
    if not prev.get("city_id") or prev.get("city_id") != curr.get("city_id"):
        return []
    prev_acc = (prev.get(ACCOMMODATION_SLOT) or {}).get("selected_option_id")
    curr_acc = (curr.get(ACCOMMODATION_SLOT) or {}).get("selected_option_id")
    if prev_acc is None or curr_acc is None or prev_acc == curr_acc:
        return []
    return [ValidationError(
        code="SAME_CITY_ACCOMMODATION_DRIFT",
        path=f"$.days[{curr.get('day')}].accommodation.selected_option_id",
        message=(
            f"same-city continuation should auto-lock to day {prev.get('day')}'s accommodation "
            f"but selections differ: {prev_acc!r} vs {curr_acc!r} (§5.7 B)"
        ),
        severity="warning",
    )]


def _check_owning_day_segments(transportation: dict) -> list[ValidationError]:
    errs: list[ValidationError] = []
    for seg in transportation.get("segments", []):
        if seg.get("owning_day") != seg.get("depart_day"):
            errs.append(ValidationError(
                code="OWNING_DAY_NOT_DEPART_DAY",
                path=f"$.transportation.segments[{seg.get('segment_id')}]",
                message=(
                    f"owning_day={seg.get('owning_day')} must equal depart_day={seg.get('depart_day')} "
                    "(§5.13 B red-eye rule cp-07)"
                ),
            ))
    return errs


def validate_trip_v2(bundle) -> list[ValidationError]:
    """Validate the entire bundle: meta + every day + cross-day rules."""
    errs: list[ValidationError] = []
    errs.extend(validate_meta_v2(bundle.meta))
    legs = sorted(bundle.meta.get("legs", []), key=lambda L: L["leg_index"])

    for i, day in enumerate(bundle.days):
        day_n = day.get("day", i + 1)
        leg = _leg_for_day(legs, day_n)
        is_first_night = leg is not None and day_n == leg["first_day"]
        errs.extend(validate_day_v2(
            day,
            bundle.meta,
            position=f"$.days[{day_n}]",
            is_first_night=is_first_night,
        ))
        if leg is not None and day.get("leg_index") != leg["leg_index"]:
            errs.append(ValidationError(
                code="DAY_LEG_INDEX_MISMATCH",
                path=f"$.days[{day_n}].leg_index",
                message=f"day in leg {leg['leg_index']} but file says {day.get('leg_index')}",
            ))

    for prev, curr in zip(bundle.days, bundle.days[1:]):
        errs.extend(_check_same_city_continuation(prev, curr))

    errs.extend(_check_owning_day_segments(bundle.transportation))
    return errs
