#!/usr/bin/env python3
"""
Preloaded TodoList for plan workflow.

Auto-generated from workflow steps extraction.
"""


def get_todos():
    """
    Return list of todo items for TodoWrite.

    Returns:
        list[dict]: Todo items with content, activeForm, status
    """
    return [
    {"content": "Step 0: Initialize Workflow Checklist", "activeForm": "Step 0: Initializing Workflow", "status": "pending"},
    {"content": "Step 1: Parse Destination Hint", "activeForm": "Step 1: Parsing Destination Hint", "status": "pending"},
    {"content": "Step 2: Conduct BA-Style Requirement Interview", "activeForm": "Step 2: Conducting Requirement Interview", "status": "pending"},
    {"content": "Step 3: Initial Research Consultation", "activeForm": "Step 3: Consulting Research Subagent", "status": "pending"},
    {"content": "Step 4: Validate Research Quality", "activeForm": "Step 4: Validating Research Quality", "status": "pending"},
    {"content": "Step 5: Generate HTML Travel Plan", "activeForm": "Step 5: Generating HTML Travel Plan", "status": "pending"},
    {"content": "Step 6: Present Plan and Save to File", "activeForm": "Step 6: Presenting and Saving Plan", "status": "pending"},
    {"content": "Step 7: Offer Iterations and Refinements", "activeForm": "Step 7: Offering Iterations", "status": "pending"}
    ]


if __name__ == "__main__":
    # CLI: print todos as formatted list
    import json
    todos = get_todos()
    print(json.dumps(todos, indent=2, ensure_ascii=False))
