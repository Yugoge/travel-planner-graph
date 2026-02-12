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
    # Phase 1: Validate all
    all_issues = []
    if validate:
        for file_path, agent_name, data in saves:
            envelope = {"agent": agent_name, "status": "complete", "data": data}
            issues, _ = validate_agent_data(agent_name, envelope, Path(file_path).parent)
            all_issues.extend(issues)

        high_issues = [i for i in all_issues if i.severity == Severity.HIGH]
        if high_issues:
            raise ValidationError(all_issues, {})

    # Phase 2: Backup all
    if create_backup:
        for file_path, _, _ in saves:
            file_path = Path(file_path)
            if file_path.exists():
                _create_backup(file_path)

    # Phase 3: Write all to .tmp
    tmp_files = []
    try:
        for file_path, agent_name, data in saves:
            file_path = Path(file_path)
            envelope = {"agent": agent_name, "status": "complete", "data": data}
            content = json.dumps(envelope, indent=2, ensure_ascii=False) + "\n"

            tmp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            tmp_path.write_text(content, encoding='utf-8')
            tmp_files.append((tmp_path, file_path))

        # Phase 4: Atomic rename all
        for tmp_path, final_path in tmp_files:
            tmp_path.replace(final_path)

    except Exception as e:
        # Rollback: delete all .tmp files
        for tmp_path, _ in tmp_files:
            if tmp_path.exists():
                tmp_path.unlink()
        raise AtomicWriteError(f"Batch save failed: {e}") from e


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

    # Write to actual agent file location for validation
    # plan-validate.py expects files to exist at <trip_dir>/<agent>.json
    agent_file = trip_dir / f"{agent_name}.json"
    backup_existed = agent_file.exists()
    backup_content = None

    if backup_existed:
        backup_content = agent_file.read_text(encoding='utf-8')

    try:
        # Write file temporarily for validation
        agent_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8')

        # Try to use plan-validate.py
        try:
            registry = SchemaRegistry()
            issues, metrics = run_pipeline(
                trip_dirs=[trip_dir],
                registry=registry,
                agent_filter=agent_name
            )
            return issues, metrics
        except (NameError, AttributeError):
            # Fallback if plan-validate.py not available
            print(f"Warning: Validation skipped (plan-validate.py not available)", file=sys.stderr)
            return [], {}

    finally:
        # Restore original file or delete temp file
        if backup_existed and backup_content is not None:
            agent_file.write_text(backup_content, encoding='utf-8')
        elif not backup_existed and agent_file.exists():
            agent_file.unlink()


# ============================================================
# Utility Functions
# ============================================================

def _atomic_write(file_path: Path, content: str) -> None:
    """Write file atomically using temp file + rename."""
    file_path = Path(file_path)
    tmp_path = file_path.with_suffix(file_path.suffix + '.tmp')

    try:
        tmp_path.write_text(content, encoding='utf-8')
        tmp_path.replace(file_path)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise AtomicWriteError(f"Failed to write {file_path}: {e}") from e


def _create_backup(file_path: Path) -> None:
    """Create .bak backup of existing file."""
    file_path = Path(file_path)
    bak_path = file_path.with_suffix(file_path.suffix + '.bak')
    if file_path.exists():
        shutil.copy2(file_path, bak_path)
