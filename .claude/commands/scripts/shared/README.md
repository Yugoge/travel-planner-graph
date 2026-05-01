# Shared Skill Utilities

This directory contains shared utility modules used by multiple skills.

## Purpose

To avoid code duplication across individual skill directories, common functionality is centralized here.

## Modules

### `load_env.py`

Centralized environment variable loader for all skill scripts.

Each skill directory has a compatibility wrapper that imports from this shared module.
