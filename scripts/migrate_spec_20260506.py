#!/usr/bin/env python3
"""One-shot migration for spec-20260506-092951 (M5 + M4 + bug8).

Run under DEV_MIGRATION_BYPASS=spec-20260506-092951 so the new write-time
schema hook does not block the cleanup writes themselves.

Usage:
    DEV_MIGRATION_BYPASS=spec-20260506-092951 \
        python3 scripts/migrate_spec_20260506.py

Idempotent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'china-20260412-092624'
SCHEMAS = ROOT / 'schemas'
ATOUR_LOCAL = '亚朵酒店·成都玉林华西'
CJK_RE = re.compile(r'[一-鿿]')


def load(p): return json.loads(p.read_text(encoding='utf-8'))


def save(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n',
                 encoding='utf-8')


def _strip_pl(o):
    if isinstance(o, dict):
        o.pop('plan_label', None)
        for v in o.values():
            _strip_pl(v)
    elif isinstance(o, list):
        for v in o:
            _strip_pl(v)


def _purge_one_file(p):
    try:
        obj = load(p)
    except Exception:
        return False
    before = json.dumps(obj, ensure_ascii=False)
    _strip_pl(obj)
    if json.dumps(obj, ensure_ascii=False) == before:
        return False
    save(p, obj)
    return True


def m5_purge_plan_label():
    return sum(1 for p in sorted(DATA.glob('*.json')) if _purge_one_file(p))


def m5_strip_schema():
    p = SCHEMAS / 'timeline.schema.json'
    obj = load(p)
    props = obj.get('$defs', {}).get('timeline_activity', {}).get('properties', {})
    if 'plan_label' not in props:
        return False
    del props['plan_label']
    save(p, obj)
    return True


def _xile(s):
    return (s.replace('喜樂院子·影音民宿（玉林西路）', ATOUR_LOCAL)
             .replace('喜樂院子·影音民宿', ATOUR_LOCAL)
             .replace('喜樂院子', ATOUR_LOCAL)
             .replace('喜乐院子', ATOUR_LOCAL))


def _has_xile(v):
    return isinstance(v, str) and ('喜樂院子' in v or '喜乐院子' in v)


def _replace_one(o, k, v):
    if _has_xile(v):
        o[k] = _xile(v)
        return True
    return False


def _replace_in_dict(o):
    for k, v in list(o.items()):
        if not _replace_one(o, k, v):
            _replace_strs(v)


def _replace_strs(o):
    if isinstance(o, dict):
        _replace_in_dict(o)
    elif isinstance(o, list):
        _replace_in_list(o)


def _replace_in_list(lst):
    for i, v in enumerate(lst):
        if _has_xile(v):
            lst[i] = _xile(v)
        else:
            _replace_strs(v)


def _new_pairs(d):
    return [(_xile(k) if isinstance(k, str) else k, v) for k, v in d.items()]


def _maybe_rename(d):
    pairs = _new_pairs(d)
    olds = list(d.keys())
    if any(np != ok for (np, _), ok in zip(pairs, olds)):
        d.clear()
        for k, v in pairs:
            d[k] = v


def _recurse_rename(v):
    if isinstance(v, dict):
        _rename_keys(v)
    elif isinstance(v, list):
        for vi in v:
            _rename_keys(vi)


def _rename_keys(d):
    if not isinstance(d, dict):
        return
    _maybe_rename(d)
    for v in d.values():
        _recurse_rename(v)


def _bug1_one_file(name):
    p = DATA / name
    obj = load(p)
    before = json.dumps(obj, ensure_ascii=False)
    _replace_strs(obj)
    _rename_keys(obj)
    if json.dumps(obj, ensure_ascii=False) == before:
        return False
    save(p, obj)
    return True


def m4_bug1_atour():
    return any(_bug1_one_file(n) for n in ('timeline.json', 'transportation.json'))


def _annotate_one(item):
    if not isinstance(item, dict):
        return False
    nb = item.get('notes_base') or item.get('notes', '') or ''
    if 'Matilde solo' in nb and 'Jade departed' not in nb:
        item['notes_base'] = nb.replace(
            'Matilde solo',
            'Matilde solo (Jade departed Chengdu for Beijing afternoon of '
            '5/9; both share earlier slots)',
        )
        return True
    return False


def _items_of(v):
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return [v]
    return []


def _annotate_slot(day, slot):
    return any(_annotate_one(it) for it in _items_of(day.get(slot)))


def _annotate_day8_meals(day8):
    return any(_annotate_slot(day8, s) for s in ('breakfast', 'lunch', 'dinner'))


def _meals_day8(p_meals):
    obj = load(p_meals)
    days = obj.get('data', {}).get('days') or obj.get('days') or []
    if len(days) < 8 or not isinstance(days[7], dict):
        return False
    changed = _annotate_day8_meals(days[7])
    if changed:
        save(p_meals, obj)
    return changed


def m4_bug2_day8():
    changed = _meals_day8(DATA / 'meals.json')
    p = DATA / 'entertainment.json'
    obj = load(p)
    s = json.dumps(obj, ensure_ascii=False)
    new = s.replace(
        '"notes_local": "Matilde 单独"',
        '"notes_local": "下午Jade返京后Matilde 单独（早上为双人，下午Matilde 单独）"',
    ).replace(
        '"notes_base": "Both travelers"',
        '"notes_base": "Both travelers in morning; Matilde solo afternoon '
        '(Jade departed for Beijing on 5/9 afternoon flight 3U8893)"',
    )
    if new != s:
        save(p, json.loads(new))
        changed = True
    return changed


def _set_loc(d9):
    changed = False
    if d9.get('location') == 'Beijing':
        d9['location'] = "Xi'an"
        changed = True
    if d9.get('location_local') in ('北京', None):
        d9['location_local'] = '西安'
        changed = True
    return changed


def _intercity_seg():
    return {
        'from_base': 'Chengdu East Railway Station (成都东站)',
        'from_local': '成都东站',
        'to_base': "Xi'an North Railway Station (西安北站)",
        'to_local': '西安北站',
        'type_base': 'high-speed rail',
        'type_local': '高铁',
        'name_base': "Chengdu East -> Xi'an North HSR (Day 9 intercity)",
        'name_local': '成都东 → 西安北高铁（Day 9 城际段）',
        'duration_minutes': 240,
        'status': 'Not yet booked',
    }


def _has_seg(intercity):
    return any(isinstance(s, dict)
               and "Xi'an" in (s.get('to_base', '') or '')
               and 'Chengdu' in (s.get('from_base', '') or '')
               for s in intercity)


def _add_seg(d9):
    intercity = d9.get('intercity_segments')
    if intercity is None:
        d9['intercity_segments'] = []
        intercity = d9['intercity_segments']
    if _has_seg(intercity):
        return False
    intercity.append(_intercity_seg())
    return True


def m4_bug3_day9():
    p = DATA / 'transportation.json'
    obj = load(p)
    days = obj.get('data', {}).get('days') or obj.get('days') or []
    if len(days) < 9 or not isinstance(days[8], dict):
        return False
    d9 = days[8]
    changed = _set_loc(d9)
    if _add_seg(d9):
        changed = True
    if changed:
        save(p, obj)
    return changed


_CATS = ('meals', 'accommodation', 'activities', 'entertainment',
         'shopping', 'transportation', 'cafe')


def _sum_day(d):
    return int(round(sum(d.get(c, 0) for c in _CATS
                         if isinstance(d.get(c), (int, float)))))


def _maybe_980(d, key, actual):
    v = d.get(key)
    if isinstance(v, str) and re.search(r'\b980\b', v) and actual != 980:
        d[key] = re.sub(r'\b980\b', str(actual), v)
        return True
    return False


def _fix_budget_day(d):
    actual = _sum_day(d)
    changed = False
    if isinstance(d.get('total'), (int, float)) and d['total'] != actual:
        d['total'] = actual
        changed = True
    for key in ('assessment', 'assessment_local', 'notes', 'notes_local',
                'assessment_base', 'notes_base'):
        if _maybe_980(d, key, actual):
            changed = True
    return changed


def m4_bug4_budget():
    p = DATA / 'budget.json'
    obj = load(p)
    days = obj.get('data', {}).get('days') or obj.get('days') or []
    changed = any(_fix_budget_day(d) for d in days if isinstance(d, dict))
    if changed:
        save(p, obj)
    return changed


def _hhmm(s):
    if not isinstance(s, str):
        return None
    try:
        h, m = s.split(':')
        return int(h) * 60 + int(m)
    except Exception:
        return None


def _is_degenerate(a):
    s, e, d = a.get('start_time'), a.get('end_time'), a.get('duration_minutes', 0)
    return s == e and isinstance(d, (int, float)) and d > 0


def _fix_act(act):
    if not isinstance(act, dict):
        return False
    changed = False
    if _is_degenerate(act):
        act['duration_minutes'] = 0
        changed = True
    sm, em = _hhmm(act.get('start_time')), _hhmm(act.get('end_time'))
    if sm is not None and em is not None and em > sm:
        cur = act.get('duration_minutes')
        if isinstance(cur, (int, float)) and cur != em - sm:
            act['duration_minutes'] = em - sm
            changed = True
    return changed


def _fix_segs(segs):
    if isinstance(segs, list):
        for s in segs:
            _fix_act(s)
    elif isinstance(segs, dict):
        for s in segs.values():
            _fix_act(s)


def _fix_day_durations(day):
    if not isinstance(day, dict):
        return
    tl = day.get('timeline', {})
    if isinstance(tl, dict):
        for a in tl.values():
            _fix_act(a)
    for k in ('travel_segments', 'intra_city_routes', 'intercity_segments'):
        _fix_segs(day.get(k))


def _bug5_one_file(name):
    p = DATA / name
    obj = load(p)
    before = json.dumps(obj, ensure_ascii=False)
    for d in (obj.get('data', {}).get('days') or obj.get('days') or []):
        _fix_day_durations(d)
    if json.dumps(obj, ensure_ascii=False) == before:
        return False
    save(p, obj)
    return True


def m4_bug5_durations():
    return any(_bug5_one_file(n) for n in ('timeline.json', 'transportation.json'))


def _extract_chinese(item):
    nl, nb = item.get('name_local'), item.get('name_base', '')
    if not isinstance(nl, str) or CJK_RE.search(nl):
        return False
    if not (isinstance(nb, str) and CJK_RE.search(nb)):
        return False
    m = re.search(r'\(([^()]*[一-鿿][^()]*)\)', nb)
    if m:
        item['name_local'] = m.group(1)
        return True
    return False


def _strip_dangling(item):
    nl = item.get('name_local')
    if not isinstance(nl, str):
        return False
    if nl.count('(') + nl.count('（') == nl.count(')') + nl.count('）'):
        return False
    new = re.sub(r'[（(][^（()]*$', '', nl).strip()
    if new != nl:
        item['name_local'] = new
        return True
    return False


def _fix_local(item):
    if not isinstance(item, dict):
        return False
    return any([_extract_chinese(item), _strip_dangling(item)])


def _walk_local(o):
    changed = False
    if isinstance(o, dict):
        if _fix_local(o):
            changed = True
        for v in o.values():
            if _walk_local(v):
                changed = True
    elif isinstance(o, list):
        for v in o:
            if _walk_local(v):
                changed = True
    return changed


def _bug6_one_file(p):
    try:
        obj = load(p)
    except Exception:
        return False
    before = json.dumps(obj, ensure_ascii=False)
    _walk_local(obj)
    if json.dumps(obj, ensure_ascii=False) == before:
        return False
    save(p, obj)
    return True


def m4_bug6_cjk():
    return any(_bug6_one_file(p) for p in sorted(DATA.glob('*.json')))


def _fix_attr(item):
    if not isinstance(item, dict):
        return False
    base = item.get('name_base', '')
    if not isinstance(base, str):
        return False
    if 'Fangsuo' not in base and '方所' not in base:
        return False
    new = base.replace('[PLAN A - PRIMARY] Optional', '[PLAN B - ALTERNATIVE]')
    new = new.replace('PRIMARY] Optional', 'ALTERNATIVE]')
    changed = False
    if new != base:
        item['name_base'] = new
        changed = True
    if not item.get('optional'):
        item['optional'] = True
        changed = True
    return changed


def _fix_slot(slot):
    return any(_fix_attr(it) for it in _items_of(slot))


def _walk_attr(day):
    if not isinstance(day, dict):
        return False
    return any(_fix_slot(slot) for slot in day.values())


def m4_bug7_fangsuo():
    p = DATA / 'attractions.json'
    obj = load(p)
    days = obj.get('data', {}).get('days') or obj.get('days') or []
    changed = any(_walk_attr(d) for d in days)
    if changed:
        save(p, obj)
    return changed


def m4_bug8_shopping():
    p = DATA / 'shopping.json'
    obj = load(p)
    s = json.dumps(obj, ensure_ascii=False)
    new = s.replace('before departing for Beijing',
                    'before departing for Chengdu').replace('赴北京前', '赴成都前')
    if new == s:
        return False
    save(p, json.loads(new))
    return True


ACTIONS = (
    ('M5 plan_label purge from data', m5_purge_plan_label),
    ('M5 plan_label removal from schema', m5_strip_schema),
    ('M4 bug1 喜樂院子 -> Atour', m4_bug1_atour),
    ('M4 bug2 Day 8 traveler matrix', m4_bug2_day8),
    ("M4 bug3 Day 9 location Xi'an", m4_bug3_day9),
    ('M4 bug4 budget arithmetic', m4_bug4_budget),
    ('M4 bug5 timeline durations', m4_bug5_durations),
    ('M4 bug6 name_local CJK', m4_bug6_cjk),
    ('M4 bug7 Fangsuo PRIMARY/Optional', m4_bug7_fangsuo),
    ('M4 bug8 shopping Weidu', m4_bug8_shopping),
)


def main():
    for name, fn in ACTIONS:
        try:
            r = fn()
            print(f'  {name}: changed={r}')
        except Exception as exc:
            print(f'  {name}: ERROR {exc}', file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
