"""iCal exporter tests: validity, red-eye ownership, day-anchor fallback, alarms."""

from __future__ import annotations

from pathlib import Path

import icalendar

from scripts.lib.exporters.common import load_trip_for_export
from scripts.lib.exporters.ical_renderer import export_ical, render_ical_bytes


def _parse(ics_bytes: bytes) -> icalendar.Calendar:
    return icalendar.Calendar.from_ical(ics_bytes)


def test_ical_normal_trip_parses(normal_trip: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    out_path = export_ical(trip)
    assert out_path.exists()
    cal = _parse(out_path.read_bytes())
    events = [c for c in cal.walk() if c.name == "VEVENT"]
    # 6 slots × 3 days = 18 slot events; no segments
    assert len(events) == 18, f"expected 18 VEVENT, got {len(events)}"


def test_ical_atomic_write_no_tmp_residue(normal_trip: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    out_path = export_ical(trip)
    tmp_residue = list(out_path.parent.glob("*.tmp"))
    assert tmp_residue == []


def test_ical_alarms_present(normal_trip: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    data = render_ical_bytes(trip)
    cal = _parse(data)
    for event in cal.walk("VEVENT"):
        alarms = [c for c in event.subcomponents if c.name == "VALARM"]
        assert len(alarms) >= 1, f"VEVENT missing VALARM: {event.get('UID')}"
        trigger = alarms[0].get("TRIGGER")
        assert "PT30M" in str(trigger).upper() or "-PT30M" in str(trigger).upper(), (
            f"Expected 30-minute trigger, got {trigger}"
        )


def test_ical_day_anchor_fallback_09_00(normal_trip: Path) -> None:
    """Codex Q2: first untimed slot anchors at 09:00 local."""
    trip = load_trip_for_export(str(normal_trip))
    cal = _parse(render_ical_bytes(trip))
    breakfast_events = [
        e for e in cal.walk("VEVENT")
        if "breakfast" in str(e.get("SUMMARY")).lower()
    ]
    assert breakfast_events, "expected breakfast events"
    first = breakfast_events[0]
    dtstart = first["DTSTART"].dt
    assert dtstart.hour == 9 and dtstart.minute == 0, (
        f"breakfast (first slot) should anchor at 09:00, got {dtstart}"
    )


def test_ical_roll_forward_90min(normal_trip: Path) -> None:
    """Codex Q2: subsequent slots roll forward by 90 minutes (SLOT_DEFAULT_DURATION_MIN)."""
    trip = load_trip_for_export(str(normal_trip))
    cal = _parse(render_ical_bytes(trip))
    summaries = {}
    for e in cal.walk("VEVENT"):
        summaries[str(e.get("SUMMARY"))] = e["DTSTART"].dt
    bf = next(v for k, v in summaries.items() if "Breakfast:" in k)
    ma = next(v for k, v in summaries.items() if "Morning Activity:" in k)
    delta_min = (ma - bf).total_seconds() / 60.0
    assert delta_min == 90, f"morning_activity should be +90min, got {delta_min}"


def test_ical_red_eye_segment_dtstart_on_owning_day(red_eye_trip: Path) -> None:
    """§5.13 B: segment VEVENT DTSTART on Day N (depart_day = 2)."""
    trip = load_trip_for_export(str(red_eye_trip))
    cal = _parse(render_ical_bytes(trip))
    transit_events = [
        e for e in cal.walk("VEVENT") if "Transit" in str(e.get("SUMMARY"))
    ]
    assert len(transit_events) == 1, f"expected 1 transit event, got {len(transit_events)}"
    dtstart = transit_events[0]["DTSTART"].dt
    assert dtstart.day == 2, f"red-eye DTSTART should be on Day 2 (owning), got day {dtstart.day}"
    assert dtstart.hour == 23 and dtstart.minute == 30


def test_ical_arrival_marker_on_next_day(red_eye_trip: Path) -> None:
    """§5.13 B: Day N+1 has a read-only 'Arriving from prior day' marker."""
    trip = load_trip_for_export(str(red_eye_trip))
    cal = _parse(render_ical_bytes(trip))
    arrivals = [
        e for e in cal.walk("VEVENT")
        if "Arriving from prior day" in str(e.get("SUMMARY"))
    ]
    assert len(arrivals) == 1, f"expected 1 arrival marker, got {len(arrivals)}"


def test_ical_default_output_path(normal_trip: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    out_path = export_ical(trip)
    assert out_path.parent.name == "exports"
    assert out_path.name == f"{trip.trip_id}.ics"
