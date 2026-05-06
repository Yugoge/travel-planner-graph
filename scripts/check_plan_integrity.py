"""Cross-file referential-integrity linter (spec-20260506-092951 §5.7)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_PLAN_PREFIX_RE = re.compile(r'\[PLAN\s*([ABC])\b')


class _Finding:
    """Mirrors verify-plan-integrity.Finding without importing it."""

    def __init__(self, check, severity, location, message, remediation):
        self.check = check
        self.severity = severity
        self.location = location
        self.message = message
        self.remediation = remediation

    def render(self):  # pragma: no cover
        return (f'  [{self.severity}] {self.check} @ {self.location}\n'
                f'         {self.message}\n'
                f'         remediation: {self.remediation}')


def _load(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return None


def _days_of(data: Any) -> list:
    if not isinstance(data, dict):
        return []
    inner = data.get('data')
    if isinstance(inner, dict):
        days = inner.get('days')
        if isinstance(days, list):
            return days
    days = data.get('days')
    return days if isinstance(days, list) else []


def _names_in_slot(slot) -> list:
    items = slot if isinstance(slot, list) else (
        [slot] if isinstance(slot, dict) else [])
    return [it['name_base'] for it in items
            if isinstance(it, dict) and isinstance(it.get('name_base'), str)]


def _extract_pois_for_day(data: Any, day_idx: int) -> list:
    days = _days_of(data)
    if day_idx >= len(days) or not isinstance(days[day_idx], dict):
        return []
    out = []
    for slot in days[day_idx].values():
        out.extend(_names_in_slot(slot))
    return out


def _timeline_keys_for_day(timeline_data: Any, day_idx: int) -> list:
    days = _days_of(timeline_data)
    if day_idx >= len(days) or not isinstance(days[day_idx], dict):
        return []
    timeline = days[day_idx].get('timeline', {})
    return list(timeline.keys()) if isinstance(timeline, dict) else []


def _name_matches_keys(name: str, keys: list) -> bool:
    if not name:
        return True
    joined = ' '.join(keys)
    if name in joined:
        return True
    return any(name in k or k in name for k in keys)


def _mk_orphan(target, name, day_idx, severity):
    return _Finding(
        'orphan-poi', severity, f'{target}:day{day_idx+1}',
        f'orphan POI: "{name}" has no matching timeline entry',
        'Add a timeline.timeline entry on this day or remove the POI.',
    )


def _orphans_for_day(target, names, keys, day_idx, severity):
    return [_mk_orphan(target, n, day_idx, severity)
            for n in names if not _name_matches_keys(n, keys)]


def _orphan_findings(target, target_data, timeline_data, severity):
    if target.stem not in {'attractions', 'meals', 'entertainment', 'shopping'}:
        return []
    days = _days_of(target_data)
    out = []
    for day_idx in range(len(days)):
        names = _extract_pois_for_day(target_data, day_idx)
        keys = _timeline_keys_for_day(timeline_data, day_idx)
        out += _orphans_for_day(target, names, keys, day_idx, severity)
    return out


def _label_from_item(item):
    if not isinstance(item, dict):
        return None
    base = item.get('name_base', '')
    if not isinstance(base, str):
        return None
    m = _PLAN_PREFIX_RE.search(base)
    return m.group(1) if m else None


def _items_of_slot(slot):
    if isinstance(slot, list):
        return slot
    if isinstance(slot, dict):
        return [slot]
    return []


def _labels_in_items(items):
    return [lbl for lbl in (_label_from_item(it) for it in items) if lbl]


def _count_plan_labels_in_day(day):
    labels = {}
    for slot in day.values():
        for label in _labels_in_items(_items_of_slot(slot)):
            labels[label] = labels.get(label, 0) + 1
    return labels


def _mk_hollow(target, label, day_idx, count, severity):
    return _Finding(
        'hollow-plan-branch', severity, f'{target}:day{day_idx+1}',
        f'hollow plan branch: Plan {label} on day {day_idx+1} has < 2 items '
        f'({count})',
        f'Add another Plan {label} item or drop the [PLAN {label}] prefix.',
    )


def _hollow_for_day(target, day, day_idx, severity):
    labels = _count_plan_labels_in_day(day)
    return [_mk_hollow(target, label, day_idx, count, severity)
            for label, count in labels.items() if count < 2]


def _hollow_plan_findings(target, target_data, severity):
    out = []
    for day_idx, day in enumerate(_days_of(target_data)):
        if isinstance(day, dict):
            out += _hollow_for_day(target, day, day_idx, severity)
    return out


def _add_seen(seen, name, day_idx, source):
    if name:
        seen.setdefault((name.lower(), day_idx), []).append(source)


def _intra_iter(intra):
    if not isinstance(intra, dict):
        return []
    return [v for v in intra.values() if isinstance(v, dict)]


def _add_intra_for_day(seen, day, day_idx):
    for v in _intra_iter(day.get('intra_city_routes', {})):
        _add_seen(seen, v.get('name_base', ''), day_idx,
                  'transportation.intra_city_routes')


def _add_intra_city_keys(seen, transportation_data):
    for day_idx, day in enumerate(_days_of(transportation_data)):
        if isinstance(day, dict):
            _add_intra_for_day(seen, day, day_idx)


def _segments_iter(day):
    return [s for s in (day.get('travel_segments', []) or [])
            if isinstance(s, dict)]


def _add_segments_for_day(seen, day, day_idx):
    for seg in _segments_iter(day):
        _add_seen(seen, seg.get('name_base', ''), day_idx,
                  'timeline.travel_segments')


def _timeline_iter(timeline):
    if isinstance(timeline, dict):
        return list(timeline.keys())
    return []


def _add_timeline_keys_for_day(seen, day, day_idx):
    for k in _timeline_iter(day.get('timeline', {})):
        _add_seen(seen, k, day_idx, 'timeline.timeline')


def _add_one_timeline_day(seen, day, day_idx):
    _add_segments_for_day(seen, day, day_idx)
    _add_timeline_keys_for_day(seen, day, day_idx)


def _add_timeline_keys(seen, timeline_data):
    for day_idx, day in enumerate(_days_of(timeline_data)):
        if isinstance(day, dict):
            _add_one_timeline_day(seen, day, day_idx)


def _collect_transit_keys(transportation_data, timeline_data):
    seen = {}
    if isinstance(transportation_data, dict):
        _add_intra_city_keys(seen, transportation_data)
    if isinstance(timeline_data, dict):
        _add_timeline_keys(seen, timeline_data)
    return seen


def _mk_dup(target, name, day, sources, severity):
    return _Finding(
        'duplicate-transit', severity, f'{target}:day{day+1}',
        f'duplicate transit segment: "{name}" appears in {len(sources)} '
        f'sources: {sorted(sources)}',
        'Pick one source-of-truth: route in intra_city_routes OR a '
        'travel_segment OR a timeline activity. Not all three.',
    )


def _duplicate_transit_findings(target, transportation_data,
                                timeline_data, severity):
    if not (transportation_data and timeline_data):
        return []
    seen = _collect_transit_keys(transportation_data, timeline_data)
    return [_mk_dup(target, name, day, set(sources), severity)
            for (name, day), sources in seen.items()
            if len(set(sources)) >= 3]


def cross_ref_findings_for_target(target_path: Path, severity: str = 'FAIL'):
    """Top-level: run all 3 cross-ref checks against a single target file."""
    findings = []
    target_path = Path(target_path)
    data_dir = target_path.resolve().parent
    target_data = _load(target_path)
    if not isinstance(target_data, dict):
        return findings
    timeline_data = _load(data_dir / 'timeline.json')
    transportation_data = _load(data_dir / 'transportation.json')
    findings += _orphan_findings(target_path, target_data, timeline_data, severity)
    findings += _hollow_plan_findings(target_path, target_data, severity)
    if target_path.name in ('timeline.json', 'transportation.json'):
        findings += _duplicate_transit_findings(
            target_path, transportation_data, timeline_data, severity,
        )
    return findings
