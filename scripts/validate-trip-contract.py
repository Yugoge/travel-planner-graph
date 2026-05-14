#!/usr/bin/env python3
"""M2 v2 contract validator (spec-20260508-221237).

Validates the new options-first per-day file shape under data/<trip>/days/day-NN.json,
data/<trip>/meta.json, and data/<trip>/transportation.json against the v2 contract
defined in scripts/lib/trip_contract/.

Usage:
  python3 scripts/plan-validate-v2.py path/to/day-NN.json
  python3 scripts/plan-validate-v2.py path/to/meta.json
  python3 scripts/plan-validate-v2.py path/to/trip-dir/
  python3 scripts/plan-validate-v2.py --json path/to/...
  python3 scripts/plan-validate-v2.py --fixtures

Exit codes:
  0 = clean
  1 = at least one error
  2 = missing target / IO failure

This is a SEPARATE script from scripts/plan-validate.py; both coexist until M3
migrates content agents to emit v2 directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.lib import trip_contract as tc  # noqa: E402


def _try_sibling_meta(day_path: Path) -> dict:
    """Best-effort sibling meta.json lookup for is_first_night context."""
    if day_path.parent.name == "days":
        meta_path = day_path.parent.parent / "meta.json"
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


def _validate_target(target: Path) -> list:
    """Dispatch on path shape: meta.json, day-*.json, or trip directory."""
    if target.is_dir():
        bundle = tc.load_trip(target)
        return tc.validate_trip_v2(bundle)
    if not target.is_file():
        print(f"v2: not found: {target}", file=sys.stderr)
        return []
    payload = json.loads(target.read_text(encoding="utf-8"))
    if target.name == "meta.json":
        return tc.validate_meta_v2(payload)
    meta = _try_sibling_meta(target)
    return tc.validate_day_v2(payload, meta, position=f"$.{target.name}")


def _to_finding(err) -> dict:
    return {"code": err.code, "path": err.path, "message": err.message, "severity": err.severity}


def _emit_json(target: Path, errs: list) -> int:
    error_count = sum(1 for e in errs if e.severity == "error")
    warn_count = sum(1 for e in errs if e.severity == "warning")
    payload = {
        "target": str(target),
        "error_count": error_count,
        "warning_count": warn_count,
        "findings": [_to_finding(e) for e in errs],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return error_count


def _emit_text(target: Path, errs: list) -> int:
    error_count = sum(1 for e in errs if e.severity == "error")
    warn_count = sum(1 for e in errs if e.severity == "warning")
    for e in errs:
        print(e)
    verdict = "FAIL" if error_count else "OK"
    print(f"{verdict}: {target} ({error_count} error(s), {warn_count} warning(s))")
    return error_count


def _print_results(target: Path, errs: list, json_out: bool) -> int:
    if json_out:
        return _emit_json(target, errs)
    return _emit_text(target, errs)


EXPECTED_FAIL_FIXTURES = {"legacy-shape-day.json"}


def _classify_fixture_result(name: str, error_count: int) -> int:
    """Return 0 when result matches expectation, 1 when it does not."""
    if name in EXPECTED_FAIL_FIXTURES:
        if error_count == 0:
            print(f"UNEXPECTED PASS: {name} should have failed validation")
            return 1
        print(f"EXPECTED-FAIL OK: {name}")
        return 0
    return 1 if error_count else 0


def _run_fixtures() -> int:
    """Validate every JSON fixture; expected-fail fixtures invert exit contribution."""
    fix_dir = _PROJECT_ROOT / "tests" / "fixtures" / "trip-contract"
    if not fix_dir.is_dir():
        print(f"fixture dir not found: {fix_dir}", file=sys.stderr)
        return 2
    unexpected = 0
    for p in sorted(fix_dir.glob("*.json")):
        errs = _validate_target(p)
        error_count = _print_results(p, errs, json_out=False)
        unexpected += _classify_fixture_result(p.name, error_count)
    return 1 if unexpected else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="M2 v2 contract validator (spec-20260508-221237).",
    )
    parser.add_argument("targets", nargs="*", help="day-*.json | meta.json | trip directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--fixtures", action="store_true", help="Validate tests/fixtures/trip-contract/")
    args = parser.parse_args()

    if args.fixtures:
        return _run_fixtures()
    if not args.targets:
        parser.error("at least one target required (or --fixtures)")
    rc = 0
    for t in args.targets:
        p = Path(t).resolve()
        errs = _validate_target(p)
        rc += _print_results(p, errs, args.json)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
