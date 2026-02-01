#!/usr/bin/env python3
"""
Migrate all skill scripts to use project venv automatically.

This script adds venv activation code to all Python scripts that don't have it.
"""

import os
import sys
from pathlib import Path

# Venv activation code to insert
VENV_ACTIVATION_CODE = '''
# Auto-activate project venv if not already active
import sys
from pathlib import Path

def activate_venv():
    """Activate project venv if not already in it."""
    # Find project root
    script_path = Path(__file__).resolve()
    project_root = script_path
    while project_root.parent != project_root:
        if (project_root / 'venv').exists():
            break
        project_root = project_root.parent

    venv_python = project_root / 'venv' / 'bin' / 'python3'

    # If we're not using venv python, re-exec with it
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        import os
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)

activate_venv()
'''

def has_venv_activation(content):
    """Check if script already has venv activation code."""
    return 'activate_venv' in content or 'execv' in content

def migrate_script(script_path):
    """Add venv activation to a script if it doesn't have it."""
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Check if already has activation
    content = ''.join(lines)
    if has_venv_activation(content):
        return False, "Already has venv activation"

    # Find where to insert (after shebang and docstring)
    insert_line = 1  # After shebang

    # Skip past docstring if exists
    in_docstring = False
    for i, line in enumerate(lines[1:], 1):
        if '"""' in line or "'''" in line:
            if not in_docstring:
                in_docstring = True
            else:
                insert_line = i + 1
                break
        elif in_docstring:
            continue
        elif line.strip() and not line.strip().startswith('#'):
            insert_line = i
            break

    # Insert activation code
    new_lines = (
        lines[:insert_line] +
        [VENV_ACTIVATION_CODE] +
        lines[insert_line:]
    )

    # Write back
    with open(script_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return True, f"Added venv activation at line {insert_line}"

def main():
    """Migrate all skill scripts."""
    project_root = Path('/root/travel-planner')
    skills_dir = project_root / '.claude' / 'skills'

    print("=" * 70)
    print("MIGRATING SKILL SCRIPTS TO USE PROJECT VENV")
    print("=" * 70)
    print()

    # Find all Python scripts
    scripts = list(skills_dir.glob('*/scripts/*.py'))

    migrated = []
    skipped = []

    for script in scripts:
        if script.name in ['__init__.py', 'mcp_client.py', 'load_env.py']:
            skipped.append((script, "Utility module - skip"))
            continue

        try:
            success, message = migrate_script(script)
            if success:
                migrated.append((script, message))
                print(f"✅ {script.relative_to(project_root)}")
                print(f"   {message}")
            else:
                skipped.append((script, message))
                print(f"⏭️  {script.relative_to(project_root)}")
                print(f"   {message}")
        except Exception as e:
            print(f"❌ {script.relative_to(project_root)}")
            print(f"   Error: {e}")

    print()
    print("=" * 70)
    print(f"MIGRATION COMPLETE")
    print("=" * 70)
    print(f"Migrated: {len(migrated)} scripts")
    print(f"Skipped: {len(skipped)} scripts")
    print()

    if migrated:
        print("Migrated scripts will now:")
        print("  1. Auto-detect project venv")
        print("  2. Re-exec with venv python if needed")
        print("  3. Work correctly in any context (direct call, agent, etc.)")
        print()
        print("⚠️  NOTE: This uses os.execv() which replaces the current process")
        print("   This is necessary to ensure correct Python environment")

if __name__ == '__main__':
    main()
