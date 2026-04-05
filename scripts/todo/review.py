#!/usr/bin/env python3
"""Preloaded TodoList for /review command workflow."""

def get_todos():
    """Return workflow steps for /review command."""
    return [
        {"content": "Parse starting day from arguments", "activeForm": "Parsing starting day", "status": "pending"},
        {"content": "Load review skeleton and verify all agent files", "activeForm": "Loading review data", "status": "pending"},
        {"content": "Fetch images for current day", "activeForm": "Fetching images for current day", "status": "pending"},
        {"content": "Present complete day review for review", "activeForm": "Presenting day review", "status": "pending"},
        {"content": "Process user choice (perfect/changes/accept all)", "activeForm": "Processing user choice", "status": "pending"},
        {"content": "Re-invoke agents with day-scoped changes", "activeForm": "Re-invoking agents", "status": "pending", "subagent_call": {"agent": "{domain}", "subagent_type": "{domain}-agent"}},
        {"content": "Re-invoke timeline and budget agents", "activeForm": "Re-calculating timeline and budget", "status": "pending", "subagent_call": [{"agent": "timeline", "subagent_type": "timeline-agent"}, {"agent": "budget", "subagent_type": "budget-agent"}]},
        {"content": "Present updated day review for next iteration", "activeForm": "Presenting updated review", "status": "pending"},
        {"content": "Generate HTML locally (manual deployment)", "activeForm": "Generating HTML", "status": "pending"},
        {"content": "Present completion summary with booking checklist", "activeForm": "Presenting completion summary", "status": "pending"}
    ]



if __name__ == "__main__":
    import json
    print(json.dumps(get_todos(), indent=2, ensure_ascii=False))
