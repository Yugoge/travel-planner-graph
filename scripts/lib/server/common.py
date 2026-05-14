"""Shared utilities for the M4a server (spec-20260508-221237 §5.13 D).

Provides:
  TripStore           per-trip mutex registry (codex Q2 single-writer)
  atomic_write_json   .tmp + fsync + rename atomic write (§5.13 D #3)
  load_json_or_default
  new_session_id      uuid4 hex for current_editor_session
  iso_now             ISO 8601 timestamp with +08:00 (Asia/Shanghai)
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


_SHANGHAI = timezone(timedelta(hours=8))


def iso_now() -> str:
    return datetime.now(_SHANGHAI).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def new_session_id() -> str:
    return uuid.uuid4().hex


def load_json_or_default(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_and_fsync(tmp: Path, data: Any) -> None:
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.flush()
        os.fsync(f.fileno())


def atomic_write_json(path: Path, data: Any) -> None:
    """Atomic JSON write: .tmp + fsync + rename (§5.13 D #3)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    _write_and_fsync(tmp, data)
    os.replace(tmp, path)


def _get_or_create_lock(registry: dict, trip_id: str) -> threading.Lock:
    lk = registry.get(trip_id)
    if lk is None:
        lk = threading.Lock()
        registry[trip_id] = lk
    return lk


class TripStore:
    """Per-trip mutex registry (codex Q2 single-writer per-trip).

    /save holds the lock while writing day.json + meta.json.
    /route holds the lock ONLY while writing route_cache.json after the gaode
    call returns (lock released during the network round-trip).
    /budget/recompute holds the lock for a consistent read snapshot.
    """

    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root
        self._locks: dict[str, threading.Lock] = {}
        self._registry_lock = threading.Lock()

    def trip_dir(self, trip_id: str) -> Path:
        if not trip_id or "/" in trip_id or trip_id.startswith("."):
            raise ValueError(f"invalid trip_id: {trip_id!r}")
        return self.data_root / trip_id

    def lock(self, trip_id: str) -> threading.Lock:
        with self._registry_lock:
            return _get_or_create_lock(self._locks, trip_id)
