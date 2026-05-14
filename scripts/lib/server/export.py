"""POST /api/export/{pdf,ical} handler (spec §5.11, M2-contract §9).

Invokes scripts/export-pdf.py or scripts/export-ical.py (M6 worker output)
as a subprocess. Per §5.11 C + §5.13 C: the subprocess runs with
agent_id=pdf-export or ical-export, neither of which is on the gaode
allowlist; the harness denies any gaode call from these contexts.

If the M6 exporter scripts are not yet installed, returns 503-equivalent JSON
{ "error": "exporter-not-installed", "kind": "<pdf|ical>" }. Caller should
treat this as a soft failure.

Lock posture (codex Q2): export reads the trip files but writes only to the
trip's exports/ directory. We hold the per-trip lock around the subprocess
invocation to prevent a concurrent /save from mutating mid-export.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .common import TripStore

_EXPORTER_SCRIPTS = {
    "pdf": "scripts/export-pdf.py",
    "ical": "scripts/export-ical.py",
}

_EXPORTER_AGENT_IDS = {
    "pdf": "pdf-export",
    "ical": "ical-export",
}

_EXPORT_FILE_SUFFIXES = {"pdf": ".pdf", "ical": ".ics"}


def _resolve_exporter(project_dir: Path, kind: str) -> Path | None:
    rel = _EXPORTER_SCRIPTS.get(kind)
    if rel is None:
        return None
    candidate = project_dir / rel
    if not candidate.exists():
        return None
    return candidate


def _expected_output_path(store: TripStore, trip_id: str, kind: str) -> Path:
    suffix = _EXPORT_FILE_SUFFIXES[kind]
    return store.trip_dir(trip_id) / "exports" / f"{trip_id}{suffix}"


def _build_export_env(project_dir: Path, kind: str) -> dict:
    env = os.environ.copy()
    env["CLAUDE_AGENT_ID"] = _EXPORTER_AGENT_IDS[kind]
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return env


def _run_exporter(
    script: Path, trip_id: str, env: dict, timeout_s: float
) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["python3", str(script), "--trip", trip_id],
            env=env, capture_output=True, text=True,
            timeout=timeout_s, check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def _exporter_error(reason: str, kind: str) -> dict:
    return {"error": reason, "kind": kind}


def _file_size_or_zero(p: Path) -> int:
    try:
        return p.stat().st_size
    except OSError:
        return 0


def _success_response(out_path: Path) -> dict:
    return {
        "file_path": str(out_path),
        "bytes_written": _file_size_or_zero(out_path),
    }


def _do_export_under_lock(
    store: TripStore,
    trip_id: str,
    kind: str,
    project_dir: Path,
    timeout_s: float,
) -> dict[str, Any]:
    script = _resolve_exporter(project_dir, kind)
    if script is None:
        return _exporter_error("exporter-not-installed", kind)
    env = _build_export_env(project_dir, kind)
    result = _run_exporter(script, trip_id, env, timeout_s)
    if result is None:
        return _exporter_error("exporter-timeout", kind)
    if result.returncode != 0:
        return _exporter_error("exporter-failed", kind)
    out_path = _expected_output_path(store, trip_id, kind)
    if not out_path.exists():
        return _exporter_error("output-missing", kind)
    return _success_response(out_path)


def handle_export(
    store: TripStore,
    kind: str,
    req: dict,
    project_dir: Path,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    """Handle POST /api/export/{pdf,ical}. Returns ExportResponse-shaped dict.

    `kind` must be 'pdf' or 'ical'. Per-trip lock held around the subprocess.
    """
    if kind not in _EXPORTER_SCRIPTS:
        return _exporter_error("unknown-export-kind", kind)
    with store.lock(req["trip_id"]):
        return _do_export_under_lock(
            store, req["trip_id"], kind, project_dir, timeout_s
        )
