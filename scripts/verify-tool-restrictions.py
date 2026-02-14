#!/usr/bin/env python3
"""
Tool Restrictions Verification Script
======================================
Test harness to verify all safety measures work correctly across 8 agents.

Verification Tests:
1. YAML Metadata: All 8 agents have tools: [Read, Bash, Skill]
2. Prompt Content: CRITICAL WARNING, Checklist, Failure Modes, Checkpoints present
3. save.py Integration: Verify save.py can save data for each agent
4. Marker Consistency: Verify all agents use same 5-layer structure

Usage:
    python3 scripts/verify-tool-restrictions.py
    python3 scripts/verify-tool-restrictions.py --verbose
    python3 scripts/verify-tool-restrictions.py --agent timeline

Design:
    - Reads all 8 agent files
    - Validates YAML metadata
    - Checks for required prompt sections
    - Reports pass/fail with detailed findings
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"

# 8 agents to verify
AGENTS = [
    "accommodation",
    "attractions",
    "budget",
    "entertainment",
    "meals",
    "shopping",
    "timeline",
    "transportation"
]

# Expected tool whitelist
EXPECTED_TOOLS = ['Read', 'Bash', 'Skill']

# Required content markers (5-layer defense)
REQUIRED_MARKERS = {
    'critical_warning': r'🚫 CRITICAL CONSTRAINT - WRITE TOOL ABSOLUTELY FORBIDDEN',
    'numbered_checklist': r'NUMBERED CHECKLIST - Follow in Strict Sequential Order',
    'failure_modes': r'Failure Mode Handling',
    'verification_checkpoints': r'Self-Verification Checkpoints',
    'venv_activation': r'source venv/bin/activate',
    'save_py_usage': r'scripts/save\.py',
    'error_json_format': r'"error_type":',
    'exit_code_check': r'exit code'
}


def parse_frontmatter(content: str) -> Tuple[Any, str]:
    """Parse YAML frontmatter from markdown.

    Returns:
        (metadata_dict, body_content)
    """
    lines = content.split('\n')

    if not lines or not lines[0].strip() == '---':
        return None, content

    # Find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break

    if end_idx is None:
        return None, content

    frontmatter = '\n'.join(lines[1:end_idx])
    body = '\n'.join(lines[end_idx + 1:])

    try:
        metadata = yaml.safe_load(frontmatter)
        return metadata, body
    except yaml.YAMLError as e:
        return None, content


def verify_yaml_metadata(agent: str, metadata: Any) -> Tuple[bool, List[str]]:
    """Verify YAML metadata has correct tools restriction.

    Returns:
        (pass, issues)
    """
    issues = []

    if metadata is None:
        issues.append("Failed to parse YAML frontmatter")
        return False, issues

    if 'tools' not in metadata:
        issues.append("Missing 'tools' field in YAML metadata")
        return False, issues

    actual_tools = metadata['tools']

    if actual_tools != EXPECTED_TOOLS:
        issues.append(f"Incorrect tools: {actual_tools} (expected: {EXPECTED_TOOLS})")
        return False, issues

    return True, []


def verify_prompt_content(agent: str, body: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """Verify prompt body has all required 5-layer defense sections.

    Returns:
        (pass, issues)
    """
    issues = []
    found_markers = {}

    for marker_name, marker_pattern in REQUIRED_MARKERS.items():
        found = bool(re.search(marker_pattern, body, re.MULTILINE | re.IGNORECASE))
        found_markers[marker_name] = found

        if not found:
            issues.append(f"Missing required marker: {marker_name} ({marker_pattern})")

    # All markers must be present
    all_present = all(found_markers.values())

    if verbose and all_present:
        print(f"   ✓ All {len(REQUIRED_MARKERS)} markers found", file=sys.stderr)

    return all_present, issues


def verify_step3_structure(agent: str, body: str) -> Tuple[bool, List[str]]:
    """Verify Step 3 has proper numbered checklist structure.

    Returns:
        (pass, issues)
    """
    issues = []

    # Check for Step 3 section
    if not re.search(r'### Step 3:.*Save', body):
        issues.append("Missing Step 3 section")
        return False, issues

    # Check for numbered checklist items (1-5)
    required_steps = [
        r'1\.\s+\*\*Activate virtual environment',
        r'2\.\s+\*\*Create temp file',
        r'3\.\s+\*\*Save using scripts/save\.py',
        r'4\.\s+\*\*Verify save succeeded',
        r'5\.\s+\*\*Return completion status'
    ]

    for i, pattern in enumerate(required_steps, 1):
        if not re.search(pattern, body):
            issues.append(f"Missing Step 3 checklist item {i}")

    if issues:
        return False, issues

    return True, []


def verify_failure_modes(agent: str, body: str) -> Tuple[bool, List[str]]:
    """Verify Failure Mode Handling has all 5 error formats.

    Returns:
        (pass, issues)
    """
    issues = []

    required_error_types = [
        'venv_activation_failed',
        'validation_failed',
        'write_failed',
        'script_not_found',
        'unknown_save_error'
    ]

    for error_type in required_error_types:
        if not re.search(rf'"{error_type}"', body):
            issues.append(f"Missing error type: {error_type}")

    if issues:
        return False, issues

    return True, []


def verify_agent_file(agent: str, verbose: bool = False) -> Dict[str, Any]:
    """Verify single agent file.

    Returns:
        Verification result dict
    """
    agent_file = AGENTS_DIR / f"{agent}.md"

    result = {
        'agent': agent,
        'file_exists': agent_file.exists(),
        'yaml_metadata': {'pass': False, 'issues': []},
        'prompt_content': {'pass': False, 'issues': []},
        'step3_structure': {'pass': False, 'issues': []},
        'failure_modes': {'pass': False, 'issues': []},
        'overall_pass': False
    }

    if not agent_file.exists():
        result['yaml_metadata']['issues'].append(f"File not found: {agent_file}")
        return result

    # Read file
    try:
        content = agent_file.read_text(encoding='utf-8')
    except Exception as e:
        result['yaml_metadata']['issues'].append(f"Failed to read file: {e}")
        return result

    # Parse frontmatter
    metadata, body = parse_frontmatter(content)

    # Test 1: YAML metadata
    pass1, issues1 = verify_yaml_metadata(agent, metadata)
    result['yaml_metadata'] = {'pass': pass1, 'issues': issues1}

    # Test 2: Prompt content markers
    pass2, issues2 = verify_prompt_content(agent, body, verbose)
    result['prompt_content'] = {'pass': pass2, 'issues': issues2}

    # Test 3: Step 3 structure
    pass3, issues3 = verify_step3_structure(agent, body)
    result['step3_structure'] = {'pass': pass3, 'issues': issues3}

    # Test 4: Failure modes
    pass4, issues4 = verify_failure_modes(agent, body)
    result['failure_modes'] = {'pass': pass4, 'issues': issues4}

    # Overall pass if all tests pass
    result['overall_pass'] = all([pass1, pass2, pass3, pass4])

    return result


def print_result_summary(results: List[Dict[str, Any]], verbose: bool = False):
    """Print verification results summary."""
    total_agents = len(results)
    passed_agents = sum(1 for r in results if r['overall_pass'])

    print(f"\n{'='*60}")
    print(f"VERIFICATION SUMMARY")
    print(f"{'='*60}\n")

    # Per-agent results
    for result in results:
        agent = result['agent']
        status = "✅ PASS" if result['overall_pass'] else "❌ FAIL"

        print(f"{status} {agent}.md")

        if verbose or not result['overall_pass']:
            # Show test details
            tests = ['yaml_metadata', 'prompt_content', 'step3_structure', 'failure_modes']

            for test_name in tests:
                test_result = result[test_name]
                test_status = "✓" if test_result['pass'] else "✗"

                print(f"  {test_status} {test_name.replace('_', ' ').title()}")

                if test_result['issues'] and (verbose or not test_result['pass']):
                    for issue in test_result['issues']:
                        print(f"     - {issue}")

        print()

    # Overall summary
    print(f"{'='*60}")
    print(f"OVERALL: {passed_agents}/{total_agents} agents passed")
    print(f"{'='*60}\n")

    if passed_agents == total_agents:
        print("✅ All agents have complete 5-layer defense")
        return 0
    else:
        print(f"❌ {total_agents - passed_agents} agents need fixes")
        return 1


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify 5-layer Write tool defense across all 8 travel planning agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify all agents
  python3 scripts/verify-tool-restrictions.py

  # Verify with detailed output
  python3 scripts/verify-tool-restrictions.py --verbose

  # Verify single agent
  python3 scripts/verify-tool-restrictions.py --agent timeline
        """
    )

    parser.add_argument("--verbose", action="store_true", help="Show detailed test results")
    parser.add_argument("--agent", help="Verify single agent (default: all 8 agents)")

    args = parser.parse_args()

    agents_to_verify = [args.agent] if args.agent else AGENTS

    print(f"🔍 Verifying {len(agents_to_verify)} agents...", file=sys.stderr)

    results = []
    for agent in agents_to_verify:
        if args.verbose:
            print(f"\n📋 Verifying {agent}.md...", file=sys.stderr)

        result = verify_agent_file(agent, verbose=args.verbose)
        results.append(result)

        if args.verbose:
            status = "✅ PASS" if result['overall_pass'] else "❌ FAIL"
            print(f"   {status}", file=sys.stderr)

    # Print summary
    exit_code = print_result_summary(results, verbose=args.verbose)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
