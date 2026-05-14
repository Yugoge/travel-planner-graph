"""iCal renderer for M6 (spec-20260508-221237 §5.11).

Produces a VCALENDAR with one VEVENT per selected slot + per inter-city
segment, with VALARM 30min before, TZID per city, and a day-anchor fallback
(09:00 Asia/Shanghai + 90min roll, per codex Q2 guidance 2026-05-14) when no
explicit start_time exists. Red-eye segments anchored on owning_day per §5.13 B.
Atomic write via common.atomic_write_bytes.
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from icalendar import Alarm, Calendar, Event

from .common import (
    DEFAULT_DAY_ANCHOR,
    DEFAULT_TZ,
    SLOT_DEFAULT_DURATION_MIN,
    Trip,
    arriving_from_prior_day,
    atomic_write_bytes,
    city_tz_for,
    iter_day_slots,
    segments_for_day,
    selected_option,
)


_PRODID = "-//travel-planner//M6 exporter//EN"


def _parse_iso_ts(value) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _day_date(day: dict) -> Optional[date_cls]:
    raw = day.get("date")
    if not raw:
        return None
    try:
        return date_cls.fromisoformat(str(raw))
    except ValueError:
        return None


def _day_tz(day: dict) -> ZoneInfo:
    return ZoneInfo(city_tz_for(day.get("city_id")))


def _day_anchor_dt(day: dict) -> Optional[datetime]:
    d = _day_date(day)
    if d is None:
        return None
    hh, mm = DEFAULT_DAY_ANCHOR
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=_day_tz(day))


def _alarm_30min() -> Alarm:
    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("trigger", timedelta(minutes=-30))
    alarm.add("description", "Reminder")
    return alarm


def _option_summary(opt: dict, slot_label: str) -> str:
    name = opt.get("name") or opt.get("name_local") or "(unnamed)"
    return f"{slot_label}: {name}"


def _option_description(opt: dict) -> str:
    parts: list[str] = []
    name_local = opt.get("name_local")
    if name_local and name_local != opt.get("name"):
        parts.append(str(name_local))
    if opt.get("location_summary"):
        parts.append(f"Location: {opt['location_summary']}")
    if opt.get("why_fits_user"):
        parts.append(str(opt["why_fits_user"]))
    if opt.get("cost") is not None:
        parts.append(f"Cost: {opt['cost']}")
    elif "cost" in opt:
        parts.append("Cost: unknown")
    return "\n".join(parts)


def _parse_hhmm(start_time) -> Optional[Tuple[int, int]]:
    try:
        parts = str(start_time).split(":")
        return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError, TypeError):
        return None


def _slot_explicit_dt(slot: dict, day: dict) -> Optional[datetime]:
    start_time = slot.get("start_time")
    d = _day_date(day)
    if not start_time or d is None:
        return None
    hhmm = _parse_hhmm(start_time)
    if hhmm is None:
        return None
    hh, mm = hhmm
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=_day_tz(day))


def _fallback_slot_dt(slot_index: int, day: dict) -> Optional[datetime]:
    """Codex Q2: first untimed slot at 09:00, roll +90min per next slot."""
    anchor = _day_anchor_dt(day)
    if anchor is None:
        return None
    return anchor + timedelta(minutes=SLOT_DEFAULT_DURATION_MIN * slot_index)


def _slot_duration_minutes(slot: dict) -> int:
    d = slot.get("duration_minutes")
    if isinstance(d, int) and d > 0:
        return d
    return SLOT_DEFAULT_DURATION_MIN


def _slot_dtstart(slot: dict, day: dict, slot_index: int) -> Optional[datetime]:
    return _slot_explicit_dt(slot, day) or _fallback_slot_dt(slot_index, day)


def _populate_event_location(ev: Event, opt: dict) -> None:
    if opt.get("location_summary"):
        ev.add("location", opt["location_summary"])


def _build_slot_event(
    trip: Trip, day: dict, slot_id: str, slot: dict, slot_index: int,
) -> Optional[Event]:
    if slot.get("skipped"):
        return None
    opt = selected_option(slot)
    if opt is None:
        return None
    dtstart = _slot_dtstart(slot, day, slot_index)
    if dtstart is None:
        return None
    dtend = dtstart + timedelta(minutes=_slot_duration_minutes(slot))
    ev = Event()
    uid = f"{trip.trip_id}-day{day.get('day')}-{slot_id}@travel-planner"
    ev.add("uid", uid)
    ev.add("summary", _option_summary(opt, slot_id.replace("_", " ").title()))
    ev.add("description", _option_description(opt))
    _populate_event_location(ev, opt)
    ev.add("dtstart", dtstart)
    ev.add("dtend", dtend)
    ev.add_component(_alarm_30min())
    return ev


def _segment_summary(seg: dict) -> str:
    from_city = seg.get("from_city") or seg.get("from") or "?"
    to_city = seg.get("to_city") or seg.get("to") or "?"
    mode = seg.get("mode") or "transit"
    return f"Transit ({mode}): {from_city} → {to_city}"


def _segment_description(seg: dict) -> str:
    parts: list[str] = []
    if seg.get("cost") is not None:
        parts.append(f"Cost: {seg['cost']}")
    if seg.get("distance_km") is not None:
        parts.append(f"Distance: {seg['distance_km']} km")
    status = seg.get("status")
    if status and status not in ("ok", "resolved"):
        parts.append(f"Status: {status} (placeholder)")
    return "\n".join(parts)


def _segment_dtstart(seg: dict, owning_day: dict) -> Optional[datetime]:
    return _parse_iso_ts(seg.get("depart_ts")) or _day_anchor_dt(owning_day)


def _segment_dtend(seg: dict, dtstart: Optional[datetime]) -> Optional[datetime]:
    dtend = _parse_iso_ts(seg.get("arrive_ts"))
    if dtend is not None or dtstart is None:
        return dtend
    dur_min = seg.get("duration_minutes") or 120
    return dtstart + timedelta(minutes=int(dur_min))


def _segment_uid(trip: Trip, seg: dict) -> str:
    seg_id = seg.get("segment_id") or (
        f"seg-{seg.get('depart_day')}-{seg.get('arrive_day')}"
    )
    return f"{trip.trip_id}-{seg_id}@travel-planner"


def _build_segment_event(trip: Trip, seg: dict, owning_day: dict) -> Optional[Event]:
    dtstart = _segment_dtstart(seg, owning_day)
    dtend = _segment_dtend(seg, dtstart)
    if dtstart is None or dtend is None:
        return None
    ev = Event()
    ev.add("uid", _segment_uid(trip, seg))
    ev.add("summary", _segment_summary(seg))
    desc = _segment_description(seg)
    if desc:
        ev.add("description", desc)
    ev.add("dtstart", dtstart)
    ev.add("dtend", dtend)
    ev.add_component(_alarm_30min())
    return ev


def _events_for_slots(trip: Trip, day: dict) -> list[Event]:
    out: list[Event] = []
    for idx, (slot_id, slot) in enumerate(iter_day_slots(day)):
        ev = _build_slot_event(trip, day, slot_id, slot, idx)
        if ev is not None:
            out.append(ev)
    return out


def _events_for_segments(trip: Trip, day: dict, day_n: int) -> list[Event]:
    out: list[Event] = []
    for seg in segments_for_day(trip, day_n):
        ev = _build_segment_event(trip, seg, day)
        if ev is not None:
            out.append(ev)
    return out


def _arrival_note_event(trip: Trip, seg: dict) -> Optional[Event]:
    """Read-only arrival header on Day N+1 for prior-day red-eye (§5.13 B)."""
    arrive_dt = _parse_iso_ts(seg.get("arrive_ts"))
    if arrive_dt is None:
        return None
    ev = Event()
    seg_id = seg.get("segment_id") or (
        f"seg-{seg.get('depart_day')}-{seg.get('arrive_day')}"
    )
    ev.add("uid", f"{trip.trip_id}-{seg_id}-arrival@travel-planner")
    ev.add("summary", f"Arriving from prior day: {seg.get('from_city') or '?'}")
    ev.add("description", "Read-only arrival marker; budget owned by depart day.")
    ev.add("dtstart", arrive_dt)
    ev.add("dtend", arrive_dt + timedelta(minutes=15))
    return ev


def _events_for_arrivals(trip: Trip, day_n: int) -> list[Event]:
    out: list[Event] = []
    for seg in arriving_from_prior_day(trip, day_n):
        ev = _arrival_note_event(trip, seg)
        if ev is not None:
            out.append(ev)
    return out


def _add_calendar_header(cal: Calendar, trip: Trip) -> None:
    cal.add("prodid", _PRODID)
    cal.add("version", "2.0")
    cal.add("x-wr-calname", str(trip.meta.get("title") or trip.trip_id))
    cal.add("x-wr-timezone", DEFAULT_TZ)


def build_calendar(trip: Trip) -> Calendar:
    cal = Calendar()
    _add_calendar_header(cal, trip)
    for day_index, day in enumerate(trip.days):
        day_n = day_index + 1
        events: list[Event] = []
        events.extend(_events_for_slots(trip, day))
        events.extend(_events_for_segments(trip, day, day_n))
        events.extend(_events_for_arrivals(trip, day_n))
        for ev in events:
            cal.add_component(ev)
    return cal


def render_ical_bytes(trip: Trip) -> bytes:
    cal = build_calendar(trip)
    return cal.to_ical()


def export_ical(trip: Trip, output_path: Optional[Path] = None) -> Path:
    """Write the trip iCal to data/<trip>/exports/<trip>.ics (atomic)."""
    if output_path is None:
        output_path = trip.trip_dir / "exports" / f"{trip.trip_id}.ics"
    data = render_ical_bytes(trip)
    atomic_write_bytes(output_path, data)
    return output_path
