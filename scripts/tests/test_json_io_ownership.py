#!/usr/bin/env python3
"""Integration tests for json_io ownership + universal image_url deny.

Iter 2 (spec-20260505-221501 / W2): verifies the persistence-layer
counterparts to pretool-block-production-files.sh:

  - _reject_unauthorized_ownership: closes the Python-internal-write
    surface that the Bash hook physically cannot reach. Every call to
    save_agent_json now reads .claude/agents/<agent_name>.md frontmatter
    `owned_files` regex list and rejects writes whose file_path does
    not match.

  - _reject_universal_image_url: mirrors hook Check 3. ANY image_url
    field in the payload is rejected at the persistence layer, ensuring
    Python-internal writes via sync-agent-data / strip-image-url-fields
    / save.py cannot bypass it.

Run with:
    source venv/bin/activate && python scripts/tests/test_json_io_ownership.py
or:
    python3 scripts/tests/test_json_io_ownership.py
"""

import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.json_io import (  # noqa: E402
    OwnershipError,
    StockImageRejected,
    UniversalImageDeny,
    save_agent_json,
)


# ---------- temp-trip helpers ----------

def _make_temp_trip_dir() -> Path:
    """Create a sandboxed data/<trip>/ inside the project so the hook +
    json_io rel_path resolver agree on the path."""
    project_root = Path(__file__).resolve().parent.parent.parent
    trip_slug = f"json-io-ownership-test-{os.getpid()}"
    trip_dir = project_root / "data" / trip_slug
    trip_dir.mkdir(parents=True, exist_ok=True)
    return trip_dir


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def _cleanup_trip_dir(trip_dir: Path) -> None:
    """Remove sandboxed trip directory + all contents."""
    if not trip_dir.exists():
        return
    for child in trip_dir.iterdir():
        _safe_unlink(child)
    try:
        trip_dir.rmdir()
    except OSError:
        pass


def _save(trip_dir, filename, agent_name, data):
    """Convenience wrapper invoking save_agent_json with standard flags."""
    target = trip_dir / filename
    save_agent_json(
        target,
        agent_name=agent_name,
        data=data,
        validate=False,
        create_backup=False,
        allow_high_severity=True,
    )
    return target


def _expect_raises(callable_, expected_types):
    """Run callable_; return (raised: bool, exc_or_none)."""
    try:
        callable_()
    except expected_types as exc:
        return True, exc
    return False, None


# ---------- AC-OWNERSHIP sub-cases ----------

def test_authorized_write_succeeds(trip_dir: Path) -> None:
    """meals agent writing data/<trip>/meals.json with clean payload -> OK."""
    target = _save(trip_dir, "meals.json", "meals", {"days": []})
    assert target.exists(), "expected meals.json to be written"
    target.unlink()


def test_cross_agent_write_raises_ownership_error(trip_dir: Path) -> None:
    """meals agent writing data/<trip>/timeline.json -> OwnershipError."""
    target = trip_dir / "timeline.json"
    raised, exc = _expect_raises(
        lambda: _save(trip_dir, "timeline.json", "meals", {"days": []}),
        OwnershipError,
    )
    assert raised, "expected OwnershipError for cross-agent write"
    assert "meals" in str(exc), f"expected agent name in message, got: {exc}"
    assert "timeline.json" in str(exc), \
        f"expected target path in message, got: {exc}"
    assert not target.exists(), "file should not have been written on rejection"


def test_image_url_payload_raises(trip_dir: Path) -> None:
    """meals agent writing meals.json with image_url payload -> rejected."""
    target = trip_dir / "meals.json"
    payload = {"days": [{"day": 1, "breakfast": {"image_url": "x"}}]}
    raised, exc = _expect_raises(
        lambda: _save(trip_dir, "meals.json", "meals", payload),
        (UniversalImageDeny, StockImageRejected),
    )
    assert raised, "expected image-url payload to be rejected"
    msg = str(exc).lower()
    assert "image_url" in msg or "stock" in msg, \
        f"expected image-related rejection message, got: {exc}"
    assert not target.exists(), "file should not have been written on rejection"


def test_unknown_agent_raises_ownership_error(trip_dir: Path) -> None:
    """Agent name with no .claude/agents/<name>.md file -> OwnershipError."""
    raised, exc = _expect_raises(
        lambda: _save(
            trip_dir, "meals.json", "nonexistent-agent-xyz", {"days": []}
        ),
        OwnershipError,
    )
    assert raised, "expected OwnershipError for unknown agent"
    assert "nonexistent-agent-xyz" in str(exc), \
        f"expected unknown agent name in message, got: {exc}"


# ---------- minimal test harness (lets the file run standalone) ----------

TESTS = [
    test_authorized_write_succeeds,
    test_cross_agent_write_raises_ownership_error,
    test_image_url_payload_raises,
    test_unknown_agent_raises_ownership_error,
]


def _run_one(fn, trip_dir):
    """Execute a single test; return (passed: bool, message: str)."""
    try:
        fn(trip_dir)
        return True, ""
    except AssertionError as exc:
        return False, f"FAIL: {exc}"
    except Exception as exc:  # pylint: disable=broad-except
        return False, f"ERROR: {type(exc).__name__}: {exc}"


def _record_result(fn, trip_dir, failed):
    """Run one test, print outcome, append failure name when applicable."""
    ok, msg = _run_one(fn, trip_dir)
    tag = "PASS " if ok else "FAIL "
    suffix = f" -- {msg}" if msg else ""
    print(f"  {tag} {fn.__name__}{suffix}")
    if not ok:
        failed.append(fn.__name__)


def _run_all() -> int:
    trip_dir = _make_temp_trip_dir()
    failed = []
    try:
        for fn in TESTS:
            _record_result(fn, trip_dir, failed)
    finally:
        _cleanup_trip_dir(trip_dir)

    print()
    if failed:
        print(f"{len(failed)} test(s) failed: {failed}")
        return 1
    print(f"All {len(TESTS)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run_all())
