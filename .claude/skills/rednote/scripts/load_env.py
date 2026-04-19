#!/usr/bin/env python3
"""
Load environment variables from .env file in project root.

DEPRECATED: This file is kept for backwards compatibility.
All skills use the centralized version at .claude/skills/shared/load_env.py.

This shim loads the shared module by absolute path via importlib so it does
not depend on sys.path ordering.
"""

import importlib.util
from pathlib import Path

_shared_path = Path(__file__).parent.parent.parent / 'shared' / 'load_env.py'
_spec = importlib.util.spec_from_file_location('_shared_load_env', _shared_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

load_env = _mod.load_env
__all__ = ['load_env']
