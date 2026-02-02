#!/usr/bin/env python3
"""Preloaded TodoList for /plan workflow."""

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
            "content": "Step 2: BA Requirement Interview",
            "activeForm": "Step 2: Conducting Interview",
            "status": "pending"
        },
        {
            "content": "Step 3: Validate Day Completion",
            "activeForm": "Step 3: Validating Day Completion",
            "status": "pending"
        },
        {
            "content": "Step 4: Init Requirements Skeleton",
            "activeForm": "Step 4: Initializing Requirements Skeleton",
            "status": "pending"
        },
        {
            "content": "Step 5: Init Plan Skeleton with Location Detection",
            "activeForm": "Step 5: Initializing Plan Skeleton",
            "status": "pending"
        },
        {
            "content": "Step 6: Orchestrate Parallel Agents (6 agents)",
            "activeForm": "Step 6: Orchestrating Parallel Agents",
            "status": "pending"
        },
        {
            "content": "Step 7: Orchestrate Serial Agents (timeline + budget)",
            "activeForm": "Step 7: Orchestrating Serial Agents",
            "status": "pending"
        },
        {
            "content": "Step 8: Validate and Generate HTML",
            "activeForm": "Step 8: Validating and Generating HTML",
            "status": "pending"
        },
        {
            "content": "Step 9: Present Plan and Offer Refinement",
            "activeForm": "Step 9: Presenting Plan",
            "status": "pending"
        },
        {
            "content": "Step 10: Wait for User Refinement Request",
            "activeForm": "Step 10: Waiting for User Response",
            "status": "pending"
        },
        {
            "content": "Step 11: Parse Refinement Request (day scope, domain, nature)",
            "activeForm": "Step 11: Parsing Refinement Request",
            "status": "pending"
        },
        {
            "content": "Step 12: Classify Refinement Type (Type 1/2/3)",
            "activeForm": "Step 12: Classifying Refinement Type",
            "status": "pending"
        },
        {
            "content": "Step 13: Handle Type 3 Informational Query (if applicable)",
            "activeForm": "Step 13: Handling Informational Query",
            "status": "pending"
        },
        {
            "content": "Step 14: Build Refinement Context for Agent Delegation",
            "activeForm": "Step 14: Building Refinement Context",
            "status": "pending"
        },
        {
            "content": "Step 15: Re-invoke Specialist Agent(s) with Day Scope",
            "activeForm": "Step 15: Re-invoking Specialist Agents",
            "status": "pending"
        },
        {
            "content": "Step 16: Re-invoke Dependent Agents (timeline + budget)",
            "activeForm": "Step 16: Re-invoking Dependent Agents",
            "status": "pending"
        },
        {
            "content": "Step 17: Regenerate HTML with Version Suffix",
            "activeForm": "Step 17: Regenerating HTML",
            "status": "pending"
        },
        {
            "content": "Step 18: Present Updated Plan to User",
            "activeForm": "Step 18: Presenting Updated Plan",
            "status": "pending"
        }
    ]

if __name__ == "__main__":
    import json
    print(json.dumps(get_todos(), indent=2, ensure_ascii=False))
