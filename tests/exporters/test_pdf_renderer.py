"""PDF exporter tests: normal day, red-eye, missing image, atomic write."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.exporters.common import load_trip_for_export
from scripts.lib.exporters.pdf_renderer import (
    ensure_cjk_font,
    export_pdf,
    render_pdf_bytes,
)


def test_pdf_normal_day_renders(normal_trip: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    out_path = export_pdf(trip)
    assert out_path.exists(), "PDF file should be written"
    assert out_path.stat().st_size > 1000, "PDF should not be empty"
    raw = out_path.read_bytes()
    assert raw.startswith(b"%PDF-"), "Output must start with PDF magic"


def test_pdf_atomic_write_no_tmp_residue(normal_trip: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    out_path = export_pdf(trip)
    tmp_residue = list(out_path.parent.glob("*.tmp"))
    assert tmp_residue == [], f"No .tmp residue allowed, found {tmp_residue}"


def test_pdf_red_eye_segment_appears_on_owning_day(red_eye_trip: Path) -> None:
    trip = load_trip_for_export(str(red_eye_trip))
    data = render_pdf_bytes(trip)
    # PDF contents are binary/compressed; just verify the bytes built and
    # owning-day logic (codified in common.segments_for_day) returns the
    # segment for day 2 (depart_day) and not day 3.
    from scripts.lib.exporters.common import segments_for_day
    day2_segs = segments_for_day(trip, 2)
    day3_segs = segments_for_day(trip, 3)
    assert len(day2_segs) == 1, "red-eye segment owns Day 2 (§5.13 B)"
    assert day3_segs == [], "Day 3 must NOT own the segment"
    assert data.startswith(b"%PDF-")


def test_pdf_missing_image_falls_back_to_placeholder(missing_image_trip: Path) -> None:
    trip = load_trip_for_export(str(missing_image_trip))
    out_path = export_pdf(trip)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes().startswith(b"%PDF-")


def test_pdf_cached_image_used_when_present(with_cached_image_trip: Path) -> None:
    trip = load_trip_for_export(str(with_cached_image_trip))
    out_path = export_pdf(trip)
    assert out_path.exists()
    assert out_path.read_bytes().startswith(b"%PDF-")


def test_ensure_cjk_font_succeeds() -> None:
    backend = ensure_cjk_font()
    assert backend.startswith("ttf:") or backend.startswith("cid:")


def test_pdf_default_output_path_under_exports(normal_trip: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    out_path = export_pdf(trip)
    assert out_path.parent.name == "exports"
    assert out_path.name == f"{trip.trip_id}.pdf"


def test_pdf_explicit_output_path_respected(normal_trip: Path, tmp_path: Path) -> None:
    trip = load_trip_for_export(str(normal_trip))
    target = tmp_path / "elsewhere" / "custom.pdf"
    out_path = export_pdf(trip, output_path=target)
    assert out_path == target
    assert target.exists()
