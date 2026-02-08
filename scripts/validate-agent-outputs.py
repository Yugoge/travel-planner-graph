#!/usr/bin/env python3
"""
JSON Schema-based validation of all agent outputs.

Validates each agent JSON against its corresponding schema in schemas/,
then runs additional semantic checks (cost sanity, timeline overlaps,
budget sum verification, coordinate bounds).

Usage: validate-agent-outputs.py <data_dir>
Exit codes:
  0 = all valid
  1 = critical issues found (schema violations, missing data)
  2 = warnings only (semantic issues)

Examples:
  python3 validate-agent-outputs.py data/china-feb-15-mar-7-2026-20260202-195429
  python3 validate-agent-outputs.py /path/to/project/data/trip
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource


# Agent files mapped to their schema names
AGENT_SCHEMA_MAP = {
    "meals": "meals.schema.json",
    "attractions": "attractions.schema.json",
    "entertainment": "entertainment.schema.json",
    "accommodation": "accommodation.schema.json",
    "transportation": "transportation.schema.json",
    "timeline": "timeline.schema.json",
    "budget": "budget.schema.json",
    "shopping": "shopping.schema.json",
}

# China coordinate bounds for geographic sanity checks
CHINA_LAT_RANGE = (18.0, 54.0)
CHINA_LNG_RANGE = (73.0, 136.0)


def load_schemas(project_root: Path) -> Tuple[Dict[str, dict], Registry]:
    """Load all schemas from schemas/ directory and build a referencing Registry.

    Returns:
        Tuple of (schema_dict keyed by agent name, Registry for $ref resolution)
    """
    schema_dir = project_root / "schemas"
    if not schema_dir.exists():
        raise FileNotFoundError(f"Schema directory not found: {schema_dir}")

    # Load all schema files into a registry for cross-schema $ref resolution
    resources = []
    all_schema_files = {}
    for schema_file in schema_dir.glob("*.schema.json"):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
        schema_id = schema.get("$id", schema_file.name)
        all_schema_files[schema_file.name] = schema
        resources.append((schema_id, Resource.from_contents(schema)))

    registry = Registry().with_resources(resources)

    # Map agent names to their loaded schema objects
    schemas = {}
    for agent_name, schema_filename in AGENT_SCHEMA_MAP.items():
        if schema_filename in all_schema_files:
            schemas[agent_name] = all_schema_files[schema_filename]

    return schemas, registry


def validate_against_schema(
    data: dict, schema: dict, registry: Registry, filename: str
) -> List[str]:
    """Validate data against a JSON Schema using Draft 2020-12.

    Returns a list of human-readable error strings with JSON path info.
    """
    errors = []
    validator = Draft202012Validator(schema, registry=registry)

    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        # Build a readable JSON path from the error's path
        path_parts = list(error.absolute_path)
        if path_parts:
            json_path = ".".join(str(p) for p in path_parts)
        else:
            json_path = "(root)"

        # Skip overly verbose oneOf sub-errors; report the parent
        if error.context:
            # For oneOf/anyOf failures, summarize rather than listing every sub-error
            errors.append(f"[{filename}] {json_path}: {error.message}")
        else:
            errors.append(f"[{filename}] {json_path}: {error.message}")

    return errors


def semantic_checks(data_dir: Path) -> Tuple[List[str], List[str]]:
    """Run semantic checks beyond what JSON Schema can enforce.

    Checks:
      1. Cost sanity: accommodation cost < 200 with no currency field -> WARN
      2. Timeline overlap detection
      3. Budget sum verification: category sum should match total
      4. Coordinate bounds for China trips: lat 18-54, lng 73-136

    Returns:
        Tuple of (critical_errors, warnings)
    """
    errors = []
    warnings = []

    # 1. Cost sanity check on accommodation
    _check_cost_sanity(data_dir, warnings)

    # 2. Timeline overlap detection
    _check_timeline_overlaps(data_dir, errors)

    # 3. Budget sum verification
    _check_budget_sums(data_dir, warnings)

    # 4. Coordinate bounds for China trips
    _check_coordinate_bounds(data_dir, warnings)

    return errors, warnings


def _load_agent_data(data_dir: Path, filename: str) -> dict:
    """Load an agent JSON file, returning empty dict on failure."""
    path = data_dir / f"{filename}.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return {}


def _extract_days(data: dict) -> list:
    """Extract the days array from agent data (handles nested 'data' envelope)."""
    if "data" in data and isinstance(data["data"], dict):
        return data["data"].get("days", [])
    return data.get("days", [])


def _check_cost_sanity(data_dir: Path, warnings: List[str]):
    """Warn if accommodation cost < 200 and no currency field is present.

    Root cause: costs may be in EUR instead of CNY when no currency is specified.
    """
    data = _load_agent_data(data_dir, "accommodation")
    if not data:
        return

    days = _extract_days(data)
    for day in days:
        acc = day.get("accommodation", {})
        if not acc:
            continue

        cost = acc.get("cost", 0)
        currency = acc.get("currency")
        day_num = day.get("day", "?")

        if cost > 0 and cost < 200 and not currency:
            warnings.append(
                f"[accommodation] Day {day_num}: cost={cost} with no currency field "
                f"- may be in wrong currency (EUR instead of CNY?)"
            )


def _check_timeline_overlaps(data_dir: Path, errors: List[str]):
    """Detect overlapping activities in timeline.json."""
    data = _load_agent_data(data_dir, "timeline")
    if not data:
        return

    days = _extract_days(data)
    for day in days:
        day_num = day.get("day", "?")
        timeline = day.get("timeline", {})
        if not timeline:
            continue

        # Collect activities with valid start/end times
        timed_activities = []
        for activity_name, schedule in timeline.items():
            if not isinstance(schedule, dict):
                continue
            start = schedule.get("start_time", "")
            end = schedule.get("end_time", "")
            if start and end:
                timed_activities.append((activity_name, start, end))

        # Sort by start time and check for overlaps
        timed_activities.sort(key=lambda x: x[1])
        for i in range(len(timed_activities) - 1):
            curr_name, curr_start, curr_end = timed_activities[i]
            next_name, next_start, next_end = timed_activities[i + 1]
            if curr_end > next_start:
                errors.append(
                    f"[timeline] Day {day_num}: '{curr_name}' ({curr_start}-{curr_end}) "
                    f"overlaps '{next_name}' ({next_start}-{next_end})"
                )


def _check_budget_sums(data_dir: Path, warnings: List[str]):
    """Verify that budget category sums equal the stated total."""
    data = _load_agent_data(data_dir, "budget")
    if not data:
        return

    days = _extract_days(data)
    categories = ["meals", "accommodation", "activities", "shopping", "transportation"]

    for day in days:
        day_num = day.get("day", "?")
        budget = day.get("budget", {})
        if not budget:
            continue

        stated_total = budget.get("total", 0)
        if stated_total == 0:
            continue

        computed_sum = sum(budget.get(cat, 0) for cat in categories)

        # Allow a small tolerance for floating-point rounding
        if abs(computed_sum - stated_total) > 1.0:
            warnings.append(
                f"[budget] Day {day_num}: category sum={computed_sum:.2f} "
                f"!= stated total={stated_total:.2f} (diff={abs(computed_sum - stated_total):.2f})"
            )


def _check_coordinate_bounds(data_dir: Path, warnings: List[str]):
    """Verify that coordinates fall within China's bounding box.

    Checks meals, attractions, entertainment, and accommodation.
    """
    agents_with_coords = {
        "meals": lambda day: [
            (mt, day.get(mt, {}))
            for mt in ["breakfast", "lunch", "dinner"]
            if day.get(mt)
        ],
        "attractions": lambda day: [
            (f"attraction[{i}]", a)
            for i, a in enumerate(day.get("attractions", []))
        ],
        "entertainment": lambda day: [
            (f"entertainment[{i}]", e)
            for i, e in enumerate(day.get("entertainment", []))
        ],
        "accommodation": lambda day: [
            ("accommodation", day.get("accommodation", {}))
        ] if day.get("accommodation") else [],
    }

    for agent_name, items_extractor in agents_with_coords.items():
        data = _load_agent_data(data_dir, agent_name)
        if not data:
            continue

        days = _extract_days(data)
        for day in days:
            day_num = day.get("day", "?")
            items = items_extractor(day)

            for item_label, item_data in items:
                if not isinstance(item_data, dict):
                    continue
                coords = item_data.get("coordinates", {})
                if not coords:
                    continue

                # Handle both coordinate formats
                lat = coords.get("latitude", coords.get("lat"))
                lng = coords.get("longitude", coords.get("lng"))

                if lat is not None and lng is not None:
                    name = item_data.get("name_base", item_data.get("name", item_label))
                    if not (CHINA_LAT_RANGE[0] <= lat <= CHINA_LAT_RANGE[1]):
                        warnings.append(
                            f"[{agent_name}] Day {day_num} '{name}': "
                            f"latitude {lat} outside China range {CHINA_LAT_RANGE}"
                        )
                    if not (CHINA_LNG_RANGE[0] <= lng <= CHINA_LNG_RANGE[1]):
                        warnings.append(
                            f"[{agent_name}] Day {day_num} '{name}': "
                            f"longitude {lng} outside China range {CHINA_LNG_RANGE}"
                        )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    data_dir = Path(sys.argv[1])

    # Allow relative paths by resolving against project root
    if not data_dir.is_absolute():
        # Try from CWD first, then from project root
        if not data_dir.exists():
            project_root = Path(__file__).parent.parent
            data_dir = project_root / data_dir

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    if not data_dir.is_dir():
        print(f"Error: {data_dir} is not a directory", file=sys.stderr)
        return 2

    # Determine project root (parent of scripts/ directory)
    project_root = Path(__file__).parent.parent

    print(f"Validating agent outputs in: {data_dir}")
    print(f"Using schemas from: {project_root / 'schemas'}")
    print()

    # Load schemas and build registry
    try:
        schemas, registry = load_schemas(project_root)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Loaded {len(schemas)} agent schemas")
    print()

    all_schema_errors = []
    all_semantic_errors = []
    all_warnings = []

    # Step 1: Schema validation for each agent
    print("--- Schema Validation ---")
    for agent_name, schema in schemas.items():
        agent_file = data_dir / f"{agent_name}.json"
        if not agent_file.exists():
            print(f"  {agent_name}: SKIP (file not found)")
            continue

        try:
            with open(agent_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            all_schema_errors.append(f"[{agent_name}] Invalid JSON: {e}")
            print(f"  {agent_name}: FAIL (invalid JSON)")
            continue

        errors = validate_against_schema(data, schema, registry, agent_name)
        if errors:
            all_schema_errors.extend(errors)
            print(f"  {agent_name}: {len(errors)} schema error(s)")
        else:
            print(f"  {agent_name}: OK")

    print()

    # Step 2: Semantic checks (beyond schema validation)
    print("--- Semantic Checks ---")
    semantic_errs, semantic_warns = semantic_checks(data_dir)
    all_semantic_errors.extend(semantic_errs)
    all_warnings.extend(semantic_warns)

    if semantic_errs:
        print(f"  {len(semantic_errs)} semantic error(s)")
    if semantic_warns:
        print(f"  {len(semantic_warns)} semantic warning(s)")
    if not semantic_errs and not semantic_warns:
        print("  All semantic checks passed")

    print()

    # Step 3: Report results
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    total_errors = all_schema_errors + all_semantic_errors

    if total_errors:
        print(f"\nCRITICAL ISSUES ({len(total_errors)}):")
        for err in total_errors:
            print(f"  {err}")

    if all_warnings:
        print(f"\nWARNINGS ({len(all_warnings)}):")
        for warn in all_warnings:
            print(f"  {warn}")

    if not total_errors and not all_warnings:
        print("\nAll agent outputs validated successfully.")
        return 0
    elif total_errors:
        print(f"\nValidation FAILED: {len(total_errors)} critical issue(s), {len(all_warnings)} warning(s)")
        return 1
    else:
        print(f"\nValidation PASSED with {len(all_warnings)} warning(s)")
        return 2


if __name__ == "__main__":
    sys.exit(main())
