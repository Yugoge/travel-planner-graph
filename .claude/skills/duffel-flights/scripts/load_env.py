#!/usr/bin/env python3
"""
Load environment variables from .env file in project root.
This is called by all skill scripts to ensure API keys are available.

DEPRECATED: This file is kept for backwards compatibility.
All skills now use the centralized version at .claude/skills/shared/load_env.py
"""

import sys
from pathlib import Path

# Import centralized load_env from skills shared
shared_path = Path(__file__).parent.parent.parent / 'shared'
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from load_env import load_env

# Re-export for backwards compatibility
__all__ = ['load_env']
