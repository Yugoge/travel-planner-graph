#!/usr/bin/env python3
"""Preloaded TodoList for /plan workflow.

Root cause reference: Commit 77dca06 introduced nested loop pattern for Step 14-15
to support iterative day refinement until user confirms perfect.

Updated to reflect current plan.md step numbering (Steps 0-20).
"""

def get_todos():
    return [
        {
            "content": "Step 0: Initialize Workflow",
            "activeForm": "Step 0: Initializing Workflow",
            "status": "pending"
        },
        {
            "content": "Step 1: Parse Destination Hint",
            "activeForm": "Step 1: Parsing Destination",
            "status": "pending"
        },
        {
            "content": "Step 2: Conduct Requirements Interview",
            "activeForm": "Step 2: Conducting Interview",
            "status": "pending"
        },
        {
            "content": "Step 3: Generate Requirements Skeleton",
            "activeForm": "Step 3: Generating Requirements Skeleton",
            "status": "pending"
        },
        {
            "content": "Step 4: Generate Plan Slug",
            "activeForm": "Step 4: Generating Plan Slug",
            "status": "pending"
        },
        {
            "content": "Step 5: Validate Day Completion",
            "activeForm": "Step 5: Validating Day Completion",
            "status": "pending"
        },
        {
            "content": "Step 6: Initialize Plan Skeleton",
            "activeForm": "Step 6: Initializing Plan Skeleton",
            "status": "pending"
        },
        {
            "content": "Step 7: Validate Location Continuity",
            "activeForm": "Step 7: Validating Location Continuity",
            "status": "pending"
        },
        {
            "content": "Step 8: Invoke Parallel Agents (6 agents)",
            "activeForm": "Step 8: Invoking Parallel Agents",
            "status": "pending"
        },
        {
            "content": "Step 9: Verify Agent Outputs",
            "activeForm": "Step 9: Verifying Agent Outputs",
            "status": "pending"
        },
        {
            "content": "Step 10: Invoke Timeline Agent (Serial)",
            "activeForm": "Step 10: Invoking Timeline Agent",
            "status": "pending"
        },
        {
            "content": "Step 11: Validate Timeline Consistency",
            "activeForm": "Step 11: Validating Timeline Consistency",
            "status": "pending"
        },
        {
            "content": "Step 12: Invoke Budget Agent (Serial)",
            "activeForm": "Step 12: Invoking Budget Agent",
            "status": "pending"
        },
        {
            "content": "Step 13: Budget Gate Check",
            "activeForm": "Step 13: Checking Budget Gate",
            "status": "pending"
        },
        {
            "content": "Step 14: Day-by-Day Refinement Loop (Nested Loop)",
            "activeForm": "Step 14: Executing Day-by-Day Refinement",
            "status": "pending"
        },
        {
            "content": "Step 15: Handle Day-Scoped Refinement",
            "activeForm": "Step 15: Handling Day-Scoped Refinement",
            "status": "pending"
        },
        {
            "content": "Step 16: Generate and Deploy (Atomic)",
            "activeForm": "Step 16: Generating and Deploying HTML",
            "status": "pending"
        },
        {
            "content": "Step 17: Verify Generation and Deployment",
            "activeForm": "Step 17: Verifying Generation and Deployment",
            "status": "pending"
        },
        {
            "content": "Step 18: Capture Live URL",
            "activeForm": "Step 18: Capturing Live URL",
            "status": "pending"
        },
        {
            "content": "Step 19: Present Final Plan",
            "activeForm": "Step 19: Presenting Final Plan",
            "status": "pending"
        },
        {
            "content": "Step 20: Handle User Refinements (Multi-turn Loop)",
            "activeForm": "Step 20: Handling User Refinements",
            "status": "pending"
        }
    ]

if __name__ == "__main__":
    import json
    print(json.dumps(get_todos(), indent=2, ensure_ascii=False))
