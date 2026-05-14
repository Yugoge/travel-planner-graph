#!/usr/bin/env python3
"""CLI entry for M6 iCal exporter (spec-20260508-221237 §5.11 A).

Usage: python3 scripts/export-ical.py --trip <trip_id>
       python3 scripts/export-ical.py --trip <trip_id> --output <path>

Exit codes: 0 = success, 1 = failure.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.lib.exporters.common import load_trip_for_export  # noqa: E402
from scripts.lib.exporters.ical_renderer import export_ical  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export trip to iCalendar (.ics)")
    p.add_argument("--trip", required=True, help="Trip id or path to trip dir")
    p.add_argument("--output", default=None, help="Override output ICS path")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        trip = load_trip_for_export(args.trip)
        out_path = Path(args.output) if args.output else None
        result = export_ical(trip, output_path=out_path)
    except Exception as exc:
        sys.stderr.write(f"export-ical failed: {exc}\n")
        traceback.print_exc(file=sys.stderr)
        return 1
    size = result.stat().st_size
    print(f"wrote {result} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
