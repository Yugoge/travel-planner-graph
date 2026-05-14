"""LEGACY_SHAPE_FORBIDDEN detection.

Walks any JSON-shaped object and returns paths where the legacy
{primary, alternatives[]} shape appears. Used by validators.py to raise
LEGACY_SHAPE_FORBIDDEN errors on v2 documents that smuggle the old shape in.
"""

from __future__ import annotations

from typing import Any


def _is_legacy_meal_slot(d: dict) -> bool:
    """True if a dict matches the legacy meal_slot shape ({primary[, alternatives]})."""
    keys = set(d.keys())
    if "primary" not in keys:
        return False
    return "alternatives" in keys or len(keys) == 1


def detect_legacy_shape(obj: Any, prefix: str = "") -> list[str]:
    """Return all JSON paths where {primary, alternatives[]} appears."""
    found: list[str] = []
    if isinstance(obj, dict):
        if _is_legacy_meal_slot(obj):
            found.append(prefix or "<root>")
        for k, v in obj.items():
            sub = f"{prefix}.{k}" if prefix else k
            found.extend(detect_legacy_shape(v, sub))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            sub = f"{prefix}[{i}]"
            found.extend(detect_legacy_shape(v, sub))
    return found
