#!/usr/bin/env python3
"""
Parse agent JSON response and display summary, warnings, errors.

Usage: echo "$agent_response" | python3 scripts/parse-agent-json.py

Exit codes:
- 0: Valid JSON parsed successfully
- 1: Invalid JSON (graceful degradation - not an error)
"""

import json
import sys

def main():
    try:
        # Read agent response from stdin
        agent_response = sys.stdin.read().strip()

        # Try to parse as JSON
        data = json.loads(agent_response)

        # Extract fields
        agent_name = data.get('agent', 'unknown')
        status = data.get('status', 'unknown')
        summary = data.get('summary', {})
        warnings = data.get('warnings', [])
        errors = data.get('errors', [])

        # Display errors (critical)
        if errors:
            print(f"❌ {agent_name} reported errors:", file=sys.stderr)
            for error in errors:
                print(f"   - {error}", file=sys.stderr)

        # Display warnings (important)
        if warnings:
            print(f"⚠️  {agent_name} warnings:")
            for warning in warnings:
                print(f"   - {warning}")

        # Display summary key changes (informational)
        key_changes = summary.get('key_changes', [])
        if key_changes:
            print(f"✓ {agent_name} summary:")
            for change in key_changes:
                print(f"   - {change}")

        # Exit 0 for valid JSON
        sys.exit(0)

    except json.JSONDecodeError:
        # Graceful fallback - agent returned "complete" string or invalid JSON
        # This is NOT an error condition - orchestrator will fall back to file reading
        sys.exit(1)
    except Exception as e:
        # Unexpected error during parsing
        print(f"Error parsing agent response: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
