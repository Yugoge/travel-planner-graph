"""POST /api/save autosave handler (spec §5.13 D #3-#5, M2-contract §9).

Receives a batch of mutations for a single day. Applies them to day-NN.json
under per-trip lock. Updates meta.json with schema_version, last_saved_ts,
current_editor_session. Returns 409-soft if editor_session mismatches the
recorded current_editor_session (last-writer-wins, soft warning).

Lock posture (codex Q2): per-trip lock held for the read-modify-write of
day.json + meta.json. Debounce is client-side (300ms per §5.13 D #2); server
treats every call as authoritative.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    TripStore,
    atomic_write_json,
    load_json_or_default,
    iso_now,
)
from lib.trip_contract.state_machine import validate_state_transition
from lib.trip_contract.errors import StateMachineError
from lib.trip_contract.constants import STAGES as _STAGES

SCHEMA_VERSION = "v2.0"


def _meta_path(store: TripStore, trip_id: str) -> Path:
    return store.trip_dir(trip_id) / "meta.json"


def _day_path(store: TripStore, trip_id: str, day_n: int) -> Path:
    return store.trip_dir(trip_id) / "days" / f"day-{day_n:02d}.json"


def _load_meta(store: TripStore, trip_id: str) -> dict:
    return load_json_or_default(
        _meta_path(store, trip_id),
        {"schema_version": SCHEMA_VERSION},
    )


def _is_session_conflict(meta: dict, editor_session: str) -> bool:
    current = meta.get("current_editor_session")
    if current is None or current == "":
        return False
    return current != editor_session


def _apply_select_mutation(day: dict, mut: dict) -> None:
    slot_id = mut.get("slot")
    option_id = mut.get("option_id")
    if not slot_id:
        return
    slot = day.setdefault("slots", {}).setdefault(slot_id, {"slot_id": slot_id, "options": []})
    slot["selected_option_id"] = option_id


def _apply_skip_mutation(day: dict, mut: dict) -> None:
    slot_id = mut.get("slot")
    if not slot_id:
        return
    slot = day.setdefault("slots", {}).setdefault(slot_id, {"slot_id": slot_id, "options": []})
    extra = mut.get("extra") or {}
    slot["skipped"] = bool(extra.get("skipped", True))
    slot["skipped_reason"] = extra.get("skipped_reason")


def _apply_stage_mutation(day: dict, mut: dict) -> None:
    to_stage = mut.get("to_stage")
    if not to_stage:
        return
    old_stage = day.get("stage", "")
    reason = validate_state_transition(old_stage, to_stage, has_user_consent=False)
    if reason is not None:
        raise StateMachineError(reason)
    day["stage"] = to_stage


def _apply_route_ref_mutation(day: dict, mut: dict) -> None:
    """Append/update intra_city_routes[] ref for a (from,to,mode) pair."""
    extra = mut.get("extra") or {}
    ref = {
        "from_option_id": extra.get("from_option_id"),
        "to_option_id": extra.get("to_option_id"),
        "mode": extra.get("mode"),
    }
    if not all(ref.values()):
        return
    refs = day.setdefault("intra_city_routes", [])
    _upsert_route_ref(refs, ref)


def _upsert_route_ref(refs: list[dict], ref: dict) -> None:
    for i, r in enumerate(refs):
        if _same_ref(r, ref):
            refs[i] = ref
            return
    refs.append(ref)


def _same_ref(a: dict, b: dict) -> bool:
    return (
        a.get("from_option_id") == b.get("from_option_id")
        and a.get("to_option_id") == b.get("to_option_id")
        and a.get("mode") == b.get("mode")
    )


_MUTATION_HANDLERS = {
    "select": _apply_select_mutation,
    "skip": _apply_skip_mutation,
    "stage": _apply_stage_mutation,
    "route_ref": _apply_route_ref_mutation,
    # drag-drop is a UI-level reorder; the server treats it as an opaque
    # mutation that the client should re-render. The server still records the
    # event in mutation_log for audit, but it does not mutate slot state.
}


def _apply_one_mutation(day: dict, mut: dict) -> None:
    handler = _MUTATION_HANDLERS.get(mut.get("type", ""))
    if handler is not None:
        handler(day, mut)


def _apply_mutations(day: dict, mutations: list[dict]) -> dict:
    for m in mutations:
        _apply_one_mutation(day, m)
    return day


def _write_day_and_meta(
    store: TripStore,
    trip_id: str,
    day_n: int,
    day: dict,
    editor_session: str,
    saved_ts: str,
) -> None:
    atomic_write_json(_day_path(store, trip_id, day_n), day)
    meta = _load_meta(store, trip_id)
    meta["schema_version"] = SCHEMA_VERSION
    meta["last_saved_ts"] = saved_ts
    meta["current_editor_session"] = editor_session
    atomic_write_json(_meta_path(store, trip_id), meta)


def _do_save_under_lock(
    store: TripStore, req: dict, saved_ts: str
) -> dict[str, Any]:
    trip_id = req["trip_id"]
    day_n = req["day"]
    editor_session = req["editor_session"]
    mutations = req.get("mutations", [])
    meta = _load_meta(store, trip_id)
    conflict = "409-soft" if _is_session_conflict(meta, editor_session) else None
    day = load_json_or_default(_day_path(store, trip_id, day_n), {})
    day = _apply_mutations(day, mutations)
    _write_day_and_meta(store, trip_id, day_n, day, editor_session, saved_ts)
    return {"saved_ts": saved_ts, "conflict": conflict}


def handle_save(store: TripStore, req: dict) -> dict[str, Any]:
    """Handle POST /api/save. Returns SaveResponse-shaped dict.

    Concurrent editor_session triggers 409-soft response (last-writer-wins;
    UI shows yellow banner). The save still PROCEEDS -- 409-soft is advisory,
    not a hard reject (§5.13 D #5).
    """
    saved_ts = iso_now()
    with store.lock(req["trip_id"]):
        return _do_save_under_lock(store, req, saved_ts)
