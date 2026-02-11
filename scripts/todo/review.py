#!/usr/bin/env python3
"""Preloaded TodoList for /review command workflow."""

def get_todos():
    """Return workflow steps for /review command."""
    return [
        {"content": "Parse starting day from arguments", "activeForm": "Parsing starting day", "status": "pending"},
        {"content": "Load plan skeleton and verify all agent files", "activeForm": "Loading plan data", "status": "pending"},
        {"content": "Present complete day plan for review", "activeForm": "Presenting day plan", "status": "pending"},
        {"content": "Process user choice (perfect/changes/accept all)", "activeForm": "Processing user choice", "status": "pending"},
        {"content": "Re-invoke agents with day-scoped changes", "activeForm": "Re-invoking agents", "status": "pending"},
        {"content": "Re-invoke timeline and budget agents", "activeForm": "Re-calculating timeline and budget", "status": "pending"},
        {"content": "Present updated day plan for next iteration", "activeForm": "Presenting updated plan", "status": "pending"},
        {"content": "Generate HTML locally (manual deployment)", "activeForm": "Generating HTML", "status": "pending"},
        {"content": "Present completion summary with booking checklist", "activeForm": "Presenting completion summary", "status": "pending"}
    ]

if __name__ == "__main__":
    import json
    print(json.dumps(get_todos(), indent=2, ensure_ascii=False))
