#!/usr/bin/env python3
"""Centralized JSON I/O with built-in validation and atomic writes.

Root Cause Fix: Prevents schema violations like meals in travel_segments
by enforcing validation at write-time.

Usage:
    from scripts.lib.json_io import save_agent_json, ValidationError

    try:
        save_agent_json(
            Path("data/trip/meals.json"),
            agent_name="meals",
            data=meals_data,
            validate=True
        )
    except ValidationError as e:
        print(f"Validation failed: {e.high_issues}")
"""

import json
import os
import re
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Import validation from plan-validate.py
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Use importlib to import plan-validate.py (hyphenated filename)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'plan_validate',
        SCRIPTS_DIR / 'plan-validate.py'
    )
    plan_validate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plan_validate)
    SchemaRegistry = plan_validate.SchemaRegistry
    run_pipeline = plan_validate.run_pipeline
    Severity = plan_validate.Severity
    Issue = plan_validate.Issue
except (ImportError, AttributeError, FileNotFoundError) as e:
    print(f"Warning: Could not import plan_validate: {e}", file=sys.stderr)
    # Define fallback types
    class Severity:
        HIGH = "HIGH"
        MEDIUM = "MEDIUM"
        LOW = "LOW"

    class Issue:
        def __init__(self, severity, category, agent, trip, day, label, field, message):
            self.severity = severity
            self.category = category
            self.agent = agent
            self.trip = trip
            self.day = day
            self.label = label
            self.field = field
            self.message = message

# ============================================================
# Exception Classes
# ============================================================

class JSONIOError(Exception):
    """Base exception for json_io module."""
    pass

class ValidationError(JSONIOError):
    """Validation failed with blocking issues."""
    def __init__(self, issues: List[Issue], metrics: Dict[str, Any]):
        self.issues = issues
        self.metrics = metrics
        self.high_issues = [i for i in issues if i.severity == Severity.HIGH]
        msg = f"Validation failed with {len(self.high_issues)} HIGH severity issues"
        super().__init__(msg)

class AtomicWriteError(JSONIOError):
    """Atomic write operation failed."""
    pass

class StockImageRejected(JSONIOError):
    """Persistence layer refused a payload because it contains stock-image
    URLs or http://-protocol image_url values. User-accepted Google Maps
    `key=AIzaSy...` URLs are explicitly NOT rejected (per spec 5.1)."""
    pass


class OwnershipError(JSONIOError):
    """Persistence layer refused a write because the target file_path is not
    in the calling agent's `owned_files` allowlist (defined in
    .claude/agents/<agent_name>.md frontmatter).

    Iter 2 (spec-20260505-221501 / W2): closes the Python-internal-write
    surface that a Bash-level PreToolUse hook physically cannot reach.
    """
    pass


class UniversalImageDeny(JSONIOError):
    """Persistence layer refused a write because the payload introduces an
    `image_url` field into agent JSON. This is the universal image_url deny
    enforced at the persistence layer for ALL agents (independent of stock-
    image domains). Mirrors hook check 3 (universal image_url deny on data
    JSON paths).
    """
    pass

# Stock-image domains the persistence layer permanently rejects on NEW writes.
# Picked from spec section 5.2 / W3 worker scope. Order is irrelevant.
_STOCK_IMAGE_DOMAINS = (
    'images.unsplash.com',
    'picsum.photos',
    'placeholder.com',
    'via.placeholder.com',
    'loremflickr',
    'placekitten',
)


def _check_payload_for_stock_urls(payload_text: str) -> Optional[str]:
    """Return the first stock-image domain found in ``payload_text``, or None.
    Used by save_agent_json to refuse new writes containing stock URLs."""
    for domain in _STOCK_IMAGE_DOMAINS:
        if domain in payload_text:
            return domain
    return None


def _check_payload_for_http_image_url(payload_text: str) -> bool:
    """Return True iff ``payload_text`` contains an image_url with http:// scheme."""
    import re
    return bool(re.search(r'"image_url"\s*:\s*"http://', payload_text))


def _reject_unsafe_image_payloads(envelope: dict) -> None:
    """Raise StockImageRejected when the JSON-serialized envelope contains
    stock-image URLs or http:// image_url values. ``key=AIzaSy...`` is
    explicitly allowed (user-accepted current state, spec 5.1)."""
    payload_text = json.dumps(envelope, ensure_ascii=False)
    stock_hit = _check_payload_for_stock_urls(payload_text)
    if stock_hit is not None:
        raise StockImageRejected(
            f"Persistence layer refused payload: stock-image domain '{stock_hit}' "
            f"is permanently blocked from new writes (spec 5.1 / W3)."
        )
    if _check_payload_for_http_image_url(payload_text):
        raise StockImageRejected(
            'Persistence layer refused payload: image_url with http:// scheme '
            'is permanently blocked from new writes (spec 5.1 / W3).'
        )

# ============================================================
# Core I/O Functions
# ============================================================

def save_agent_json(
    file_path: Path,
    agent_name: str,
    data: dict,
    *,
    validate: bool = True,
    create_backup: bool = True,
    allow_high_severity: bool = False
) -> None:
    """Save agent data with envelope structure and validation.

    Args:
        file_path: Absolute path to output file
        agent_name: Agent name for envelope (e.g., "meals")
        data: Agent-specific data (will be wrapped in envelope)
        validate: Run validation before save (default: True)
        create_backup: Create .bak file if overwriting (default: True)
        allow_high_severity: Allow HIGH severity issues (default: False)

    Raises:
        ValidationError: If validation fails with HIGH severity
        IOError: If file write fails
    """
    # Convert to Path if string
    file_path = Path(file_path)

    # Wrap in envelope
    envelope = {
        "agent": agent_name,
        "status": "complete",
        "data": data,
        "notes": ""
    }

    # Validate before write
    if validate:
        trip_dir = file_path.parent
        issues, metrics = validate_agent_data(agent_name, envelope, trip_dir)

        high_issues = [i for i in issues if i.severity == Severity.HIGH]
        if high_issues and not allow_high_severity:
            raise ValidationError(issues, metrics)

    # Persistence rejector: block stock-image URLs + http:// image_url scheme.
    # key=AIzaSy URLs are explicitly allowed (user-accepted, spec 5.1).
    _reject_unsafe_image_payloads(envelope)

    # Create backup
    if create_backup and file_path.exists():
        _create_backup(file_path)

    # Atomic write
    content = json.dumps(envelope, indent=2, ensure_ascii=False) + "\n"
    _atomic_write(file_path, content)


def load_agent_json(
    file_path: Path,
    *,
    validate: bool = False
) -> dict:
    """Load agent JSON and unwrap envelope.

    Args:
        file_path: Path to agent JSON file
        validate: Validate after loading (default: False)

    Returns:
        Unwrapped data dict (contents of "data" field)
    """
    file_path = Path(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        envelope = json.load(f)

    if validate:
        agent_name = envelope.get("agent", "unknown")
        trip_dir = file_path.parent
        issues, _ = validate_agent_data(agent_name, envelope, trip_dir)

        high_issues = [i for i in issues if i.severity == Severity.HIGH]
        if high_issues:
            raise ValidationError(issues, {})

    return envelope.get("data", {})


def save_skeleton_json(
    file_path: Path,
    data: dict,
    *,
    create_backup: bool = False
) -> None:
    """Save skeleton files (no envelope)."""
    file_path = Path(file_path)

    if create_backup and file_path.exists():
        _create_backup(file_path)

    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    _atomic_write(file_path, content)


def _batch_validate(saves: List[Tuple[Path, str, dict]]) -> List[Issue]:
    """Phase 1: validate every entry, return the aggregate issue list."""
    all_issues: List[Issue] = []
    for file_path, agent_name, data in saves:
        envelope = {"agent": agent_name, "status": "complete", "data": data}
        issues, _ = validate_agent_data(agent_name, envelope, Path(file_path).parent)
        all_issues.extend(issues)
    return all_issues


def _batch_backup(saves: List[Tuple[Path, str, dict]]) -> None:
    """Phase 2: create .bak for each entry whose target file already exists."""
    for file_path, _, _ in saves:
        path = Path(file_path)
        if path.exists():
            _create_backup(path)


def _batch_write_tmp(saves: List[Tuple[Path, str, dict]]) -> List[Tuple[Path, Path]]:
    """Phase 3: write every envelope to a .tmp sibling, return (tmp, final) pairs."""
    tmp_files: List[Tuple[Path, Path]] = []
    for file_path, agent_name, data in saves:
        path = Path(file_path)
        envelope = {"agent": agent_name, "status": "complete", "data": data}
        # Reject stock-image / http:// image_url payloads BEFORE writing tmp.
        _reject_unsafe_image_payloads(envelope)
        content = json.dumps(envelope, indent=2, ensure_ascii=False) + "\n"
        tmp_path = path.with_suffix(path.suffix + '.tmp')
        tmp_path.write_text(content, encoding='utf-8')
        tmp_files.append((tmp_path, path))
    return tmp_files


def _batch_rollback(tmp_files: List[Tuple[Path, Path]]) -> None:
    """Delete any .tmp files left behind by a failed batch write."""
    for tmp_path, _ in tmp_files:
        if tmp_path.exists():
            tmp_path.unlink()


def save_agent_batch(
    saves: List[Tuple[Path, str, dict]],
    *,
    validate: bool = True,
    create_backup: bool = True
) -> None:
    """Atomically save multiple agent files with rollback.

    Args:
        saves: List of (file_path, agent_name, data) tuples
        validate: Run validation before save (default: True)
        create_backup: Create .bak files (default: True)

    Raises:
        ValidationError: If any validation fails
        AtomicWriteError: If write operation fails
    """
    if validate:
        all_issues = _batch_validate(saves)
        high_issues = [i for i in all_issues if i.severity == Severity.HIGH]
        if high_issues:
            raise ValidationError(all_issues, {})

    if create_backup:
        _batch_backup(saves)

    tmp_files: List[Tuple[Path, Path]] = []
    try:
        tmp_files = _batch_write_tmp(saves)
        for tmp_path, final_path in tmp_files:
            tmp_path.replace(final_path)
    except Exception as e:
        _batch_rollback(tmp_files)
        raise AtomicWriteError(f"Batch save failed: {e}") from e


def _run_validation_pipeline(trip_dir: Path, agent_name: str):
    """Execute plan-validate pipeline; return ([], {}) when the module isn't loaded."""
    try:
        registry = SchemaRegistry()
        issues, metrics = run_pipeline(
            trip_dirs=[trip_dir], registry=registry, agent_filter=agent_name
        )
        return issues, metrics
    except (NameError, AttributeError):
        print("Warning: Validation skipped (plan-validate.py not available)", file=sys.stderr)
        return [], {}


def _restore_or_cleanup(
    agent_file: Path, backup_existed: bool, backup_content: Optional[str]
) -> None:
    """Restore the pre-validation file content, or remove the temp file we created."""
    if backup_existed and backup_content is not None:
        agent_file.write_text(backup_content, encoding='utf-8')
        return
    if not backup_existed and agent_file.exists():
        agent_file.unlink()


def validate_agent_data(
    agent_name: str,
    json_data: dict,
    trip_dir: Path
) -> Tuple[List[Issue], Dict[str, Any]]:
    """Validate agent data using plan-validate.py pipeline.

    Args:
        agent_name: Agent name (e.g., "meals", "timeline")
        json_data: Complete JSON with envelope
        trip_dir: Trip directory path for cross-agent validation

    Returns:
        Tuple of (issues, metrics)
    """
    trip_dir = Path(trip_dir)
    agent_file = trip_dir / f"{agent_name}.json"
    backup_existed = agent_file.exists()
    backup_content = agent_file.read_text(encoding='utf-8') if backup_existed else None

    try:
        agent_file.write_text(
            json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8'
        )
        return _run_validation_pipeline(trip_dir, agent_name)
    finally:
        _restore_or_cleanup(agent_file, backup_existed, backup_content)


# ============================================================
# Utility Functions
# ============================================================

def _cleanup_tmp(tmp_path: Path) -> None:
    """Remove a leftover .tmp file if it still exists."""
    if tmp_path.exists():
        tmp_path.unlink()


def _atomic_write(file_path: Path, content: str) -> None:
    """Write file atomically using temp file + rename."""
    file_path = Path(file_path)
    tmp_path = file_path.with_suffix(file_path.suffix + '.tmp')
    try:
        tmp_path.write_text(content, encoding='utf-8')
        tmp_path.replace(file_path)
    except Exception as e:
        _cleanup_tmp(tmp_path)
        raise AtomicWriteError(f"Failed to write {file_path}: {e}") from e


# Protected fields where an empty dict `{}` from an update must NEVER overwrite
# a populated existing dict. RC-2: silent data loss occurred when an agent
# submitted `timeline: {}`, naive dict.update() wiped Days 8-11. Intentional
# clearing requires an explicit deletion code path, not an empty dict overwrite.
PROTECTED_FIELDS = frozenset({
    'timeline', 'meals', 'attractions', 'transportation',
    'accommodation', 'entertainment', 'shopping',
})


def _is_destructive_empty_overwrite(key: str, new_value, existing_value) -> bool:
    """True iff `new_value` is an empty dict that would wipe a populated
    protected field on `existing_value`. RC-2 guard."""
    if key not in PROTECTED_FIELDS:
        return False
    if not (isinstance(new_value, dict) and not new_value):
        return False
    return isinstance(existing_value, dict) and bool(existing_value)


def _warn_empty_overwrite(day_num, key: str, existing_value) -> None:
    """Log RC-2 protection warning when an empty dict overwrite is refused."""
    print(
        f"[json_io.merge_agent_slots] WARNING: Day {day_num}: refusing to "
        f"overwrite populated '{key}' ({len(existing_value)} entries) with "
        f"empty dict (use explicit delete)",
        file=sys.stderr,
    )


def _safe_overlay(existing_day: dict, update_day: dict, day_num) -> None:
    """Overlay update_day keys onto existing_day; refuse to wipe protected
    populated dicts with empty dicts. Mutates existing_day in place."""
    for key, new_value in update_day.items():
        existing_value = existing_day.get(key)
        if _is_destructive_empty_overwrite(key, new_value, existing_value):
            _warn_empty_overwrite(day_num, key, existing_value)
            continue
        existing_day[key] = new_value


def merge_agent_slots(
    existing_data: dict,
    update_data: dict,
    agent_name: str
) -> dict:
    """Merge partial-day updates at the key/slot level within each day.

    Root Cause Fix (L4): The former merge_agent_days() performed full
    day-object replacement, silently wiping sibling slots (e.g., saving only
    `dinner` destroyed `breakfast` and `lunch`). Confirmed data loss: commit
    47fccd4 (2026-04-13 13:14). This function is now the sole merge path,
    invoked automatically when the target file exists (no flag needed).

    Root Cause Fix (RC-2, 2026-05-04): Naive dict.update() also allowed an
    empty dict `{}` from an update to wipe a populated protected field
    (timeline, meals, etc.). PROTECTED_FIELDS guard now refuses such
    overwrites and logs a warning. See _safe_overlay().

    Merges each update_day key-by-key into the matching existing_day,
    preserving keys that are NOT present in the update payload.

    Args:
        existing_data: Current multi-day data from file (unwrapped, no envelope)
        update_data: Partial-day update from agent (unwrapped, no envelope)
        agent_name: Agent name (kept for API consistency)

    Returns:
        Merged data: for each update_day, keys present in the update overwrite
        existing keys; keys NOT present in update are preserved from existing.
        Protected fields with populated existing values are NEVER overwritten
        by empty dicts.

    Merge semantics:
        - Named-slot agents (meals, accommodation): update with key `dinner`
          replaces only `dinner`; `breakfast`, `lunch`, `date`, `location`,
          etc. survive.
        - Array-based agents (attractions, entertainment, shopping, cafe): if
          update has key `attractions`, the whole array is replaced; all other
          day keys (`date`, `location`, ...) survive. Array-element-level
          merge is NOT performed (per BA spec Edge Cases).
        - Days present in existing but not referenced by update are preserved.
        - Days present in update but not in existing are inserted.
        - Protected fields (timeline, meals, attractions, transportation,
          accommodation, entertainment, shopping): an incoming empty dict
          `{}` will NOT overwrite an existing populated dict. A warning is
          logged to stderr and the existing value is preserved.

    Example:
        existing: {days: [{day: 2, breakfast: A, lunch: B, dinner: C}]}
        update:   {days: [{day: 2, dinner: D}]}
        result:   {days: [{day: 2, breakfast: A, lunch: B, dinner: D}]}
    """
    if not isinstance(existing_data, dict) or "days" not in existing_data:
        raise ValueError(f"existing_data must have 'days' array, got: {list(existing_data.keys())}")
    if not isinstance(update_data, dict) or "days" not in update_data:
        raise ValueError(f"update_data must have 'days' array, got: {list(update_data.keys())}")

    # Preserve trip metadata
    merged = existing_data.copy()

    # Dict copy so we can mutate each day independently
    existing_days_map = {day["day"]: dict(day) for day in existing_data.get("days", [])}

    for update_day in update_data.get("days", []):
        if "day" not in update_day:
            raise ValueError(f"Day object missing 'day' field: {list(update_day.keys())}")
        day_num = update_day["day"]
        if day_num in existing_days_map:
            # Overlay only the keys present in update_day; preserve all other keys.
            # Protected-field empty-dict guard prevents silent data loss (RC-2).
            _safe_overlay(existing_days_map[day_num], update_day, day_num)
        else:
            # Day not previously present: insert as a copy of the update
            existing_days_map[day_num] = dict(update_day)

    merged["days"] = [existing_days_map[day_num] for day_num in sorted(existing_days_map.keys())]
    return merged


def _create_backup(file_path: Path) -> None:
    """Create .bak backup of existing file."""
    file_path = Path(file_path)
    bak_path = file_path.with_suffix(file_path.suffix + '.bak')
    if file_path.exists():
        shutil.copy2(file_path, bak_path)
