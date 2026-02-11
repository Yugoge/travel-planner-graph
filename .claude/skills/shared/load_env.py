#!/usr/bin/env python3
"""
Load environment variables from .env file in project root.
This is called by all skill scripts to ensure API keys are available.

Centralized version for skill scripts - maintained in .claude/skills/shared/
to avoid duplication across individual skill directories.
"""

import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file if it exists."""
    # Find project root (travel-planner directory)
    current = Path(__file__).resolve()
    project_root = None

    # Traverse up to find travel-planner root
    for parent in current.parents:
        if parent.name == 'travel-planner' or (parent / '.env').exists():
            project_root = parent
            break

    if not project_root:
        return  # No .env file found, use system environment variables

    env_file = project_root / '.env'
    if not env_file.exists():
        return  # No .env file, use system environment variables

    # Read and parse .env file
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Only set if not already in environment (system env takes precedence)
                if key and not os.environ.get(key):
                    os.environ[key] = value


# Auto-load on import
load_env()
