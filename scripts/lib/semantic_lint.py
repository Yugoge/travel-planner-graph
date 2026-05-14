"""Semantic-level lints for save.py (W5 spec-20260513-085358).

Cross-domain duplicate detection (AC8), meal_slot demoted-primary audit
(AC9), trip_total aggregate recompute (AC7).

Shape-agnostic by minimal name normalization; W8 will provide the
canonical _normalize_to_canonical_record() in save_translate.py and
may replace this v1 normalizer.
"""

from __future__ import annotations

import sys


POI_FLAT_DOMAINS = ('attractions', 'shopping', 'entertainment')


def _norm_name(name):
    """Minimal shape-agnostic name normalizer for dedup comparison."""
    if not isinstance(name, str):
        return ''
    return ''.join(name.split()).lower()


def _extract_item_names(items):
    """Pull (name_base, name_local) tuples from a flat-shape POI list."""
    out = []
    if not isinstance(items, list):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append((item.get('name_base', ''), item.get('name_local', '')))
    return out


def _add_to_index(index, pair, domain):
    """Add both name_base/name_local entries to the cross-domain index."""
    for name in pair:
        nn = _norm_name(name)
        if nn:
            index.setdefault(nn, domain)


def _ingest_domain_into_index(index, domain, items):
    """For each item in a flat domain list, add its names to the index."""
    for pair in _extract_item_names(items):
        _add_to_index(index, pair, domain)


def _index_day_obj(day):
    """Build name-index for one day dict across all flat POI domains."""
    index = {}
    for domain in POI_FLAT_DOMAINS:
        _ingest_domain_into_index(index, domain, day.get(domain, []))
    return index


def _index_existing_day_names(existing_data, day_num):
    """Index name -> domain for POI domains on `day_num`."""
    days = existing_data.get('data', {}).get('days', existing_data.get('days', []))
    for d in days:
        if isinstance(d, dict) and d.get('day') == day_num:
            return _index_day_obj(d)
    return {}


def _scan_item_against_index(agent, day_num, pair, index):
    """Return one finding tuple for the first name in `pair` that collides."""
    for name in pair:
        nn = _norm_name(name)
        if not nn:
            continue
        sib = index.get(nn)
        if sib and sib != agent:
            return (day_num, name, agent, sib, nn)
    return None


def _scan_day_against_index(agent, day, sibling_index):
    """Return cross-domain collisions for one update day."""
    day_num = day.get('day', '?')
    findings = []
    for pair in _extract_item_names(day.get(agent, [])):
        f = _scan_item_against_index(agent, day_num, pair, sibling_index)
        if f:
            findings.append(f)
    return findings


def _read_domain_days(path):
    """Read a domain JSON file; return data.days list (empty on error)."""
    import json
    if not path.exists():
        return []
    try:
        content = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return []
    return content.get('data', {}).get('days', [])


def _ingest_domain_days(days_by_num, domain, days):
    """Mutate days_by_num to attach this domain's per-day arrays."""
    for d in days:
        dn = d.get('day')
        if dn is None:
            continue
        days_by_num.setdefault(dn, {'day': dn})[domain] = d.get(domain, [])


def _load_sibling_for_dedup(trip_dir, exclude_agent):
    """Load attractions/shopping/entertainment except `exclude_agent`."""
    days_by_num = {}
    for domain in POI_FLAT_DOMAINS:
        if domain == exclude_agent:
            continue
        path = trip_dir / f'{domain}.json'
        _ingest_domain_days(days_by_num, domain, _read_domain_days(path))
    return {'data': {'days': list(days_by_num.values())}}


def _scan_all_days(agent, days, sib_envelope):
    """Run cross-domain dedup over every update day; return all findings."""
    findings = []
    for day in days:
        if not isinstance(day, dict):
            continue
        idx = _index_existing_day_names(sib_envelope, day.get('day', -1))
        findings.extend(_scan_day_against_index(agent, day, idx))
    return findings


def check_cross_domain_dedup(agent, agent_data, trip_dir, strict=False):
    """AC8 — WARN (or BLOCK with --strict-dedup) on cross-domain
    same-day same-name duplicates between flat-list POI domains."""
    if agent not in POI_FLAT_DOMAINS:
        return []
    sib_envelope = _load_sibling_for_dedup(trip_dir, exclude_agent=agent)
    days = agent_data.get('data', {}).get('days', agent_data.get('days', []))
    findings = _scan_all_days(agent, days, sib_envelope)
    if findings:
        _emit_dedup_findings(findings, strict)
    return findings


def _emit_one_finding(finding, level):
    day_num, our_name, our_domain, sib_domain, _nn = finding
    print(f'  {level}  Day {day_num}: "{our_name}" appears in '
          f'both {our_domain} (this save) and {sib_domain} '
          f'(sibling-existing)', file=sys.stderr)


def _emit_dedup_findings(findings, strict):
    level = 'BLOCK' if strict else 'WARN'
    print(f'\n[save] cross-domain dedup {level}: '
          f'{len(findings)} duplicate(s) detected:', file=sys.stderr)
    for finding in findings:
        _emit_one_finding(finding, level)
    if not strict:
        print('  (Use --strict-dedup to escalate WARN to BLOCK.)', file=sys.stderr)


# ---------- AC9: demoted-primary audit ----------


def _primary_name(slot):
    if not isinstance(slot, dict):
        return None
    p = slot.get('primary')
    if isinstance(p, dict):
        return p.get('name_base') or p.get('name_local')
    return None


def _alt_dict_to_name(a):
    if not isinstance(a, dict):
        return ''
    return a.get('name_base') or a.get('name_local') or ''


def _alternative_names(slot):
    if not isinstance(slot, dict):
        return []
    raw = slot.get('alternatives', []) or []
    return [n for n in (_alt_dict_to_name(a) for a in raw) if n]


def _audit_one_meal_slot(day_num, mt, existing_slot, update_slot):
    """If primary changes, return audit message; otherwise None."""
    old_p = _primary_name(existing_slot)
    new_p = _primary_name(update_slot)
    if not old_p or not new_p or old_p == new_p:
        return None
    new_alts = _alternative_names(update_slot)
    explicitly_retained = any(_norm_name(a) == _norm_name(old_p) for a in new_alts)
    if explicitly_retained:
        return None
    return (f'[save] demoted-primary policy: Day {day_num} {mt}: '
            f'dropped "{old_p}"; retained alternatives: {new_alts}')


def _audit_one_day(dn, ex_day, upd_day, meal_types):
    """Collect audit messages for every meal_type slot on this day."""
    out = []
    for mt in meal_types:
        msg = _audit_one_meal_slot(dn, mt, ex_day.get(mt), upd_day.get(mt))
        if msg:
            out.append(msg)
    return out


def _index_existing_by_day(existing_data):
    """Return {day_num: day_dict} from existing_data['days']."""
    out = {}
    for d in existing_data.get('days', []):
        if isinstance(d, dict):
            out[d.get('day')] = d
    return out


def audit_demoted_primaries(existing_data, update_data, meal_types):
    """AC9 — audit messages for every meal_slot whose primary is being
    replaced AND whose old primary is NOT explicitly listed in incoming
    alternatives[]."""
    if not isinstance(existing_data, dict) or not isinstance(update_data, dict):
        return []
    existing_by_day = _index_existing_by_day(existing_data)
    msgs = []
    for upd_day in update_data.get('days', []):
        if not isinstance(upd_day, dict):
            continue
        dn = upd_day.get('day')
        ex_day = existing_by_day.get(dn, {})
        msgs.extend(_audit_one_day(dn, ex_day, upd_day, meal_types))
    return msgs


# ---------- AC7: trip_total recompute ----------


def _coerce_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _day_budget_total(d):
    if not isinstance(d, dict):
        return None
    b = d.get('budget')
    if not (isinstance(b, dict) and 'total' in b):
        return None
    return _coerce_int(b['total'])


def _sum_day_budgets(days):
    """Return (total, saw_budget) over an iterable of day dicts."""
    total = 0
    saw = False
    for d in days:
        v = _day_budget_total(d)
        if v is not None:
            total += v
            saw = True
    return total, saw


def recompute_trip_total(agent_data):
    """AC7 — recompute data.trip_total as sum of data.days[].budget.total.

    Mutates `agent_data` in place. Returns the new total when applied;
    None when no recomputation was performed (different shape). Caller
    invokes only on budget save.
    """
    if not isinstance(agent_data, dict):
        return None
    days = agent_data.get('days')
    if not isinstance(days, list):
        return None
    total, saw = _sum_day_budgets(days)
    if not saw:
        return None
    agent_data['trip_total'] = total
    return total
