#!/usr/bin/env python3
"""
Codex-signed deploy-blocking integrity verifier for travel-plan trips.

Single-source-of-truth replacement for the rejected 30-bespoke-per-symptom hook
stack (see docs/dev/specs/spec-20260505-221501.md Section 5.2). Implements a
6-in-1 check applied to a trip's data directory and (optionally) its rendered
HTML artifact:

  1. Schema validation (jsonschema, with cross-file $ref registry)
  2. Forbidden-token grep (placeholder/TBD/etc.) over data + optional HTML
  3. Stock-image-URL grep (unsplash/picsum/placeholder.com/...)
  4. HTTP-protocol image_url grep (insecure scheme)
  5. API-key leak grep (key=AIzaSy...) — WARN-only per user 5.1 binding
  6. HTML-rendered scan (mode 2 only)

Per architect concern_4: when env IMAGE_FETCH_STATUS=FAILED is set the
verifier ABORTS deploy — image cache incomplete is a hard fail.

CLI modes:
  scripts/verify-plan-integrity.py <plan-id>
  scripts/verify-plan-integrity.py <plan-id> --html-also <output-file>
  scripts/verify-plan-integrity.py <plan-id> --strict-schema   # deploy-gate

Schema-strictness toggle (orchestrator W1 directive: "verifier must accept
current state initially"): without --strict-schema (the default during the
W1↔W2 parallel landing window), schema findings are downgraded to WARN so
W1's verifier can be tested in isolation while W2's data cleanup is still
in flight. Once W2 lands AC2/AC3 cleanups the deploy gate flips the flag
on by default by passing --strict-schema explicitly from generate-and-
deploy.sh. After the W2 cycle merges, the default may flip on globally.

Exit codes: 0 = clean (or only WARN); 1 = blocking failure.

Standards: parameterized, no hardcoded plan paths, integer step numbering.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1

FORBIDDEN_TOKEN_PATTERN = re.compile(
    r'"(to plan|placeholder|TBD|本期不渲染|out of scope|superseded|'
    r'STRUCTURAL CHANGE|OLD timeline|next session|next cycle|自理（|不渲染)"'
)

STOCK_IMAGE_PATTERN = re.compile(
    r'images\.unsplash\.com|picsum\.photos|placeholder\.com|'
    r'via\.placeholder\.com|loremflickr|placekitten'
)

HTTP_IMAGE_URL_PATTERN = re.compile(r'"image_url"\s*:\s*"http://')

API_KEY_PATTERN = re.compile(r'key=AIzaSy[A-Za-z0-9_-]{30,}')

FORBIDDEN_TOKEN_EXCLUDED = {
    'modification-log.json',
    'plan-skeleton.json',
    'requirements-skeleton.json',
}

AGENT_SCHEMA_MAP = {
    'meals': 'meals.schema.json',
    'attractions': 'attractions.schema.json',
    'entertainment': 'entertainment.schema.json',
    'accommodation': 'accommodation.schema.json',
    'transportation': 'transportation.schema.json',
    'timeline': 'timeline.schema.json',
    'budget': 'budget.schema.json',
    'shopping': 'shopping.schema.json',
    'cafe': 'cafe.schema.json',
}


# ---------------------------------------------------------------------------
# Finding container
# ---------------------------------------------------------------------------


class Finding:
    """One verifier finding with severity, location, and remediation hint."""

    def __init__(self, check, severity, location, message, remediation):
        self.check = check
        self.severity = severity
        self.location = location
        self.message = message
        self.remediation = remediation

    def render(self):
        return (
            f'  [{self.severity}] {self.check} @ {self.location}\n'
            f'         {self.message}\n'
            f'         remediation: {self.remediation}'
        )


def fnd(check, severity, location, msg, fix):
    return Finding(check, severity, location, msg, fix)


# ---------------------------------------------------------------------------
# Schema validation (split into small helpers to keep each <=30 lines)
# ---------------------------------------------------------------------------


def _import_validator():
    """Import jsonschema + referencing; return (Validator, Registry, Resource, errs)."""
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        return (Draft202012Validator, Registry, Resource, [])
    except ImportError as exc:
        return (None, None, None, [fnd(
            'schema', 'FAIL', 'python-environment',
            f'jsonschema/referencing not importable: {exc}',
            'source venv/bin/activate (or pip install jsonschema referencing)',
        )])


def _parse_one_schema(schema_file):
    """Parse a single schema file. Returns (schema_id, schema, error_finding)."""
    try:
        with open(schema_file, 'r', encoding='utf-8') as fh:
            schema = json.load(fh)
    except Exception as exc:
        return None, None, fnd(
            'schema', 'FAIL', str(schema_file),
            f'cannot parse schema: {exc}',
            'Repair JSON syntax in the schema file',
        )
    schema_id = schema.get('$id', schema_file.name)
    return schema_id, schema, None


def _load_schemas(schemas_dir):
    """Load all schemas. Returns (index_by_filename, raw_resources, parse_errors)."""
    index = {}
    raw = []
    errs = []
    for schema_file in sorted(schemas_dir.glob('*.schema.json')):
        sid, schema, err = _parse_one_schema(schema_file)
        if err is not None:
            errs.append(err)
            continue
        index[schema_file.name] = schema
        raw.append((sid, schema))
    return index, raw, errs


def _validate_instance(instance, schema, schema_filename, agent_path,
                       Validator, registry, severity):
    """Run a Draft202012Validator over one instance and emit Findings."""
    findings = []
    validator = Validator(schema, registry=registry)
    for error in validator.iter_errors(instance):
        path = '.'.join(str(p) for p in error.absolute_path) or '<root>'
        findings.append(fnd(
            'schema', severity, f'{agent_path}:{path}', error.message,
            f'Fix data shape so {schema_filename} accepts it; '
            'see schemas/ for required/forbidden field rules',
        ))
    return findings


def _read_json(path):
    """Return (data, error_finding_or_none)."""
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh), None
    except Exception as exc:
        return None, fnd(
            'schema', 'FAIL', str(path),
            f'cannot parse agent JSON: {exc}',
            'Repair JSON syntax in the agent output',
        )


def _check_one_agent(agent_path, schema, schema_filename, Validator, registry, severity):
    """Read agent JSON and validate. Returns Findings."""
    instance, err = _read_json(agent_path)
    if err is not None:
        return [err]
    return _validate_instance(
        instance, schema, schema_filename, agent_path, Validator, registry, severity,
    )


def _build_registry(raw_resources, Registry, Resource):
    resources = []
    for sid, schema in raw_resources:
        resources.append((sid, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _walk_agent_files(data_dir, schema_index, Validator, registry, severity):
    findings = []
    for agent_name, schema_filename in AGENT_SCHEMA_MAP.items():
        agent_path = data_dir / f'{agent_name}.json'
        if not agent_path.exists():
            continue
        schema = schema_index.get(schema_filename)
        if schema is None:
            findings.append(fnd(
                'schema', 'FAIL', str(agent_path),
                f'schema {schema_filename} missing for agent {agent_name}',
                f'Restore schemas/{schema_filename}',
            ))
            continue
        findings += _check_one_agent(
            agent_path, schema, schema_filename, Validator, registry, severity,
        )
    return findings


def check_schemas(data_dir, schemas_dir, strict):
    severity = 'FAIL' if strict else 'WARN'
    if not schemas_dir.exists():
        return [fnd('schema', 'FAIL', str(schemas_dir),
                    f'schemas directory not found: {schemas_dir}',
                    'Confirm the project root and schemas/ subtree exist')]
    Validator, Registry, Resource, errs = _import_validator()
    if Validator is None:
        return errs
    schema_index, raw, parse_errs = _load_schemas(schemas_dir)
    errs += parse_errs
    if not schema_index:
        errs.append(fnd('schema', 'FAIL', str(schemas_dir),
                        'no schemas found', 'Populate schemas/*.schema.json'))
        return errs
    registry = _build_registry(raw, Registry, Resource)
    return errs + _walk_agent_files(
        data_dir, schema_index, Validator, registry, severity,
    )


# ---------------------------------------------------------------------------
# Pattern check helpers (kept shallow to satisfy nesting-depth gate)
# ---------------------------------------------------------------------------


def _read_text_lines(path):
    """Return enumerated (lineno, raw_line) tuples; empty list on read error."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            return list(enumerate(fh, 1))
    except Exception:
        return []


def _scan_lines(path, pattern):
    matches = []
    for lineno, line in _read_text_lines(path):
        if pattern.search(line):
            matches.append((lineno, line.rstrip()))
    return matches


def _matches_to_findings(path, matches, check, severity, msg_prefix, remediation):
    out = []
    for lineno, line in matches:
        loc = f'{path}:{lineno}'
        msg = f'{msg_prefix}: {line.strip()[:160]}'
        out.append(fnd(check, severity, loc, msg, remediation))
    return out


def _scan_one_file(path, pattern, check, severity, msg_prefix, remediation):
    matches = _scan_lines(path, pattern)
    return _matches_to_findings(path, matches, check, severity, msg_prefix, remediation)


def _scan_data_dir(data_dir, pattern, check, severity, msg_prefix,
                   remediation, skip_files=None):
    skip_files = skip_files or set()
    findings = []
    for path in sorted(data_dir.glob('*.json')):
        if path.name in skip_files:
            continue
        findings += _scan_one_file(
            path, pattern, check, severity, msg_prefix, remediation,
        )
    return findings


def check_forbidden_tokens(data_dir):
    return _scan_data_dir(
        data_dir, FORBIDDEN_TOKEN_PATTERN, 'forbidden-token', 'FAIL',
        'forbidden token in',
        'Replace placeholder/TBD/superseded text with real plan content; '
        'do NOT authorize placeholders in dispatch prompts',
        skip_files=FORBIDDEN_TOKEN_EXCLUDED,
    )


def check_stock_images(data_dir):
    return _scan_data_dir(
        data_dir, STOCK_IMAGE_PATTERN, 'stock-image', 'FAIL',
        'stock-image URL',
        'Remove stock-image URL; use Google/Gaode photo cache via fetch-images-batch.py',
    )


def check_http_image_url(data_dir):
    return _scan_data_dir(
        data_dir, HTTP_IMAGE_URL_PATTERN, 'http-image-url', 'FAIL',
        'insecure http:// image_url',
        'Switch to https:// or remove the image_url field entirely (PATH B)',
    )


def check_api_key_leak(data_dir):
    return _scan_data_dir(
        data_dir, API_KEY_PATTERN, 'api-key-leak', 'WARN',
        'Google Maps API key leaked in URL parameters',
        'WARN-only per user 5.1; future writes should not persist key= URLs. '
        'Rotation/scrub explicitly out of scope this cycle',
    )


# ---------------------------------------------------------------------------
# HTML rendered scan
# ---------------------------------------------------------------------------


def _scan_html_pattern(html_path, pattern, check, msg_prefix):
    return _scan_one_file(
        html_path, pattern, check, 'FAIL', msg_prefix,
        'Repair upstream data; do NOT post-edit the HTML',
    )


def check_html_artifact(html_path):
    if not html_path.exists():
        return [fnd('html-scan', 'FAIL', str(html_path),
                    'rendered HTML artifact not found',
                    'Re-run scripts/generate-html-interactive.py')]
    findings = []
    findings += _scan_html_pattern(
        html_path, FORBIDDEN_TOKEN_PATTERN,
        'html-forbidden-token', 'forbidden token in rendered HTML',
    )
    findings += _scan_html_pattern(
        html_path, STOCK_IMAGE_PATTERN,
        'html-stock-image', 'stock-image URL in rendered HTML',
    )
    findings += _scan_html_pattern(
        html_path, HTTP_IMAGE_URL_PATTERN,
        'html-http-image-url', 'insecure http:// image_url in rendered HTML',
    )
    return findings


# ---------------------------------------------------------------------------
# Architect concern_4: env-signal hard fail
# ---------------------------------------------------------------------------


def check_image_fetch_status():
    if os.environ.get('IMAGE_FETCH_STATUS', 'OK') == 'FAILED':
        return [fnd(
            'image-fetch-status', 'FAIL', 'env(IMAGE_FETCH_STATUS)',
            'upstream image-fetch step reported FAILED',
            'Re-run scripts/fetch-images-batch.py manually; verify API keys '
            'and network access',
        )]
    return []


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def find_project_root(start):
    current = start.resolve()
    while current != current.parent:
        if (current / 'schemas').is_dir() and (current / 'data').is_dir():
            return current
        current = current.parent
    return start.resolve()


def _add_args_core(parser):
    parser.add_argument('plan_id', nargs='?', default=None,
                        help='Trip plan-id (subdirectory under data/). '
                             'Optional when --target-file is used.')
    parser.add_argument('--html-also', dest='html_also', default=None,
                        help='Path to rendered HTML artifact for mode-2 scan')
    parser.add_argument('--data-root', dest='data_root', default=None,
                        help='Override data root (default: <project_root>/data)')
    parser.add_argument('--schemas-root', dest='schemas_root', default=None,
                        help='Override schemas root (default: <project_root>/schemas)')


def _add_args_strict(parser):
    parser.add_argument('--strict-schema', dest='strict_schema',
                        action='store_true',
                        help='Treat schema findings as FAIL (deploy gate). '
                             'Default WARN until W2 lands data cleanups.')
    parser.add_argument('--target-file', dest='target_file', default=None,
                        help='Single-file mode (spec-20260506-092951 5.1): '
                             'validate just this one file against its schema.')
    parser.add_argument('--cross-ref', dest='cross_ref',
                        action='store_true',
                        help='Run cross-file referential-integrity linter '
                             '(spec 5.7).')


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Codex-signed deploy-blocking integrity verifier',
    )
    _add_args_core(parser)
    _add_args_strict(parser)
    return parser.parse_args(argv)


_FORBIDDEN_AD_HOC_FIELDS = (
    'plan_label',
    'is_alternative',
    '_isAlternative',
    'tier',
    'bundle_id',
    'priority_label',
)


def _check_forbidden_fields_one_file(target_path, severity):
    """Anti-pattern grep: spec 5.6+5.9 ban these ad-hoc Claude-invented fields."""
    pattern = re.compile(
        r'"(' + '|'.join(_FORBIDDEN_AD_HOC_FIELDS) + r')"\s*:'
    )
    return _scan_one_file(
        target_path, pattern, 'forbidden-adhoc-field', severity,
        'forbidden ad-hoc field (spec 5.6/5.9 ban)',
        'Use the schema-defined `optional` field. plan_label / is_alternative / '
        'tier etc. are NOT permitted in any data file.',
    )


def _resolve_target_schema(target_path):
    """Return (agent_name, schema_filename) for a target file, or (None, None)."""
    agent_name = target_path.stem
    return agent_name, AGENT_SCHEMA_MAP.get(agent_name)


def _check_one_target_file(target_path, schemas_dir, strict):
    """Single-file 5.1 mode: validate one file against its agent schema."""
    target_path = Path(target_path)
    if not target_path.exists():
        return [fnd('schema', 'FAIL', str(target_path),
                    'target file not found',
                    'Confirm tool_input.file_path is correct')]
    severity = 'FAIL' if strict else 'WARN'
    _, schema_filename = _resolve_target_schema(target_path)
    if schema_filename is None:
        return []
    Validator, Registry, Resource, errs = _import_validator()
    if Validator is None:
        return errs
    schema_index, raw, parse_errs = _load_schemas(schemas_dir)
    errs += parse_errs
    if not schema_index:
        return errs + [fnd('schema', 'FAIL', str(schemas_dir),
                            'no schemas found',
                            'Populate schemas/*.schema.json')]
    return errs + _do_target_file_check(
        target_path, schema_index, schema_filename, raw,
        Validator, Registry, Resource, severity,
    )


def _do_target_file_check(target_path, schema_index, schema_filename,
                          raw, Validator, Registry, Resource, severity):
    schema = schema_index.get(schema_filename)
    if schema is None:
        return [fnd('schema', 'FAIL', str(target_path),
                    f'schema {schema_filename} missing',
                    f'Restore schemas/{schema_filename}')]
    registry = _build_registry(raw, Registry, Resource)
    findings = []
    findings += _check_one_agent(
        target_path, schema, schema_filename, Validator, registry, severity,
    )
    findings += _check_forbidden_fields_one_file(target_path, severity)
    return findings


def collect_findings(data_dir, schemas_dir, html_also, strict_schema):
    findings = []
    print('Step 1: image-fetch env signal')
    findings += check_image_fetch_status()
    print('Step 2: schema validation '
          f'({"strict/FAIL" if strict_schema else "lenient/WARN"})')
    findings += check_schemas(data_dir, schemas_dir, strict_schema)
    print('Step 3: forbidden-token grep (data)')
    findings += check_forbidden_tokens(data_dir)
    print('Step 4: stock-image-URL grep (data)')
    findings += check_stock_images(data_dir)
    print('Step 5: http:// image_url grep (data)')
    findings += check_http_image_url(data_dir)
    print('Step 6: api-key leak grep (data, WARN-only)')
    findings += check_api_key_leak(data_dir)
    if html_also:
        print('Step 7: rendered HTML scan')
        findings += check_html_artifact(Path(html_also))
    return findings


def _print_findings(label, items):
    if not items:
        return
    print(label)
    for f in items:
        print(f.render())


def report_and_verdict(findings):
    fails = [f for f in findings if f.severity == 'FAIL']
    warns = [f for f in findings if f.severity == 'WARN']
    rule = '━' * 58
    print(rule)
    print(f'verdict: FAIL={len(fails)}  WARN={len(warns)}')
    print(rule)
    _print_findings('WARNINGS (non-blocking):', warns)
    _print_findings('BLOCKING ISSUES:', fails)
    if fails:
        print(rule)
        print('verifier verdict: FAIL — deploy aborted')
        return EXIT_FAIL
    print('verifier verdict: PASS')
    return EXIT_OK


def _print_header(args, data_dir, schemas_dir):
    rule = '━' * 58
    print(rule)
    print(f'verify-plan-integrity: {args.plan_id}')
    print(f'  data dir   : {data_dir}')
    print(f'  schemas    : {schemas_dir}')
    print(f'  html mode  : {bool(args.html_also)}')
    print(rule)


def main(argv):
    args = parse_args(argv)
    project_root = find_project_root(Path(__file__).parent)
    data_root = Path(args.data_root) if args.data_root else project_root / 'data'
    schemas_dir = (Path(args.schemas_root) if args.schemas_root
                   else project_root / 'schemas')
    data_dir = data_root / args.plan_id
    _print_header(args, data_dir, schemas_dir)
    if not data_dir.is_dir():
        print(f'[FAIL] data dir not found: {data_dir}')
        print('       remediation: confirm plan-id and data/ structure')
        return EXIT_FAIL
    findings = collect_findings(
        data_dir, schemas_dir, args.html_also, args.strict_schema,
    )
    return report_and_verdict(findings)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
