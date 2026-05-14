"""JSON Schema runner for the v2 contract.

Loads schemas/v2/*.schema.json and runs the appropriate one against a payload.
Resolves $ref relatives via a Python-side resolver. Returns ValidationError list.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema  # type: ignore

from .errors import ValidationError


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCHEMA_DIR = _PROJECT_ROOT / "schemas" / "v2"


def _load_v2_schema(filename: str) -> dict:
    return json.loads((_SCHEMA_DIR / filename).read_text(encoding="utf-8"))


def _build_registry() -> dict[str, dict]:
    """Build a {short_id: schema} registry for cross-file $ref resolution."""
    registry: dict[str, dict] = {}
    for p in _SCHEMA_DIR.glob("*.schema.json"):
        registry[p.name] = json.loads(p.read_text(encoding="utf-8"))
    return registry


def _make_validator(schema: dict, registry: dict[str, dict]) -> jsonschema.Draft202012Validator:
    """Build a validator with a resolver that maps short filenames to schemas."""
    base_uri = "https://travel-planner/schemas/v2/"
    store = {f"{base_uri}{name}": s for name, s in registry.items()}
    # Also add the bare filename (some $refs use 'poi-common.schema.json')
    for name, s in registry.items():
        store[name] = s
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=schema, store=store)
    return jsonschema.Draft202012Validator(schema, resolver=resolver)


def _to_validation_error(err: jsonschema.ValidationError, position: str) -> ValidationError:
    path_parts = list(err.absolute_path)
    pretty = position + ("" if not path_parts else "." + ".".join(str(p) for p in path_parts))
    return ValidationError(
        code="JSON_SCHEMA_VIOLATION",
        path=pretty,
        message=err.message,
    )


def validate_against_v2_schema(payload: dict, schema_filename: str, position: str = "$") -> list[ValidationError]:
    """Run JSON Schema validation. Returns ValidationError list (one per Schema error)."""
    registry = _build_registry()
    schema = registry.get(schema_filename)
    if schema is None:
        return [ValidationError(
            code="SCHEMA_FILE_MISSING",
            path=position,
            message=f"v2 schema {schema_filename!r} not found under schemas/v2/",
        )]
    validator = _make_validator(schema, registry)
    return [_to_validation_error(e, position) for e in validator.iter_errors(payload)]
