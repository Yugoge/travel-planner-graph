"""M6 Exporters: PDF + iCal generators for v2 trip bundles.

Consumes the M2 trip contract (`scripts/lib/trip_contract`). Reads only the
on-disk trip bundle + local image cache; never makes network calls.

Submodules:
    common         shared loaders, slot iteration, image lookup, atomic-write
    pdf_renderer   reportlab A4 portrait PDF (CJK font, TOC, one day/page)
    ical_renderer  icalendar VEVENT + VALARM with TZID, day-anchor fallback
"""

from .common import (
    EXPORTER_AGENT_IDS,
    SLOT_ANCHORS,
    SLOT_DEFAULT_DURATION_MIN,
    CITY_TZ_MAP,
    DEFAULT_TZ,
    DEFAULT_DAY_ANCHOR,
    Trip,
    load_trip_for_export,
    iter_day_slots,
    image_path_for_option,
    atomic_write_bytes,
    day_total_for_export,
    segments_for_day,
)

__all__ = [
    "EXPORTER_AGENT_IDS",
    "SLOT_ANCHORS",
    "SLOT_DEFAULT_DURATION_MIN",
    "CITY_TZ_MAP",
    "DEFAULT_TZ",
    "DEFAULT_DAY_ANCHOR",
    "Trip",
    "load_trip_for_export",
    "iter_day_slots",
    "image_path_for_option",
    "atomic_write_bytes",
    "day_total_for_export",
    "segments_for_day",
]
