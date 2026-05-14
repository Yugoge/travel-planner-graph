"""User-language to machine-schema translation for save.py (spec 5.9).

User-facing terms ('primary', 'Plan A', '主行程' etc.) map onto the
existing schema's `optional` boolean. Banned ad-hoc keys (plan_label,
is_alternative, tier, bundle_id, priority_label, _isAlternative) are
rejected with explicit error.

W8 (spec-20260513-085358 AC13) adds agent-scoped rejection of
`alternatives` on attractions/shopping/entertainment (flat shape).
Meals exempted (legitimately uses primary+alternatives[] per
schemas/meals.schema.json $defs.meal_slot). Plus shape-normalizer
_normalize_to_canonical_record() so cross-shape callers can operate
shape-agnostically; round-trip is lossless via _denormalize().
"""

from __future__ import annotations

import sys

USER_LANG_OPTIONAL_FALSE = (
    'primary', 'plan_a', 'plan-a', 'plana', '主行程', '套餐 a', '套餐a',
    'must do', 'must-do', 'mustdo', 'non-negotiable', 'nonnegotiable',
)
USER_LANG_OPTIONAL_TRUE = (
    'plan_b', 'plan-b', 'planb', 'plan_c', 'plan-c', 'planc',
    'alternative', 'optional', '备选', '可选', 'plan b', 'plan c',
    'skip if tired', 'skip-if-tired', 'nice-to-have', 'nice to have',
)
BANNED_AD_HOC_KEYS = (
    'plan_label', 'is_alternative', '_isAlternative',
    'tier', 'bundle_id', 'priority_label',
)

# W8 AC13: agent-scoped rejection. The literal field 'alternatives' is
# REJECTED on these three flat-shape domains because their schemas do
# not yet support primary+alternatives[]. Meals is exempted because its
# schema explicitly defines meal_slot = {primary, alternatives[]}.
AGENT_SCOPED_BANNED_KEYS = {
    'attractions': ('alternatives',),
    'shopping': ('alternatives',),
    'entertainment': ('alternatives',),
}

# Canonical-record shape names used by _normalize_to_canonical_record().
SHAPE_MEALS_NESTED = 'meals_nested'
SHAPE_FLAT_OPTIONAL = 'flat_optional'


def _norm(s):
    return s.strip().lower() if isinstance(s, str) else s


def _translate_one_dict(item):
    # Spec 5.9: 'primary': true → optional=false (user-language to schema).
    # Only translate when 'primary' is a bool — meals/attractions schemas
    # legitimately use 'primary' as a slot KEY whose value is a nested dict
    # (e.g. meals.json: {"breakfast": {"primary": {name_base, ...}}}).
    # Translating those would pop the slot subtree (cycle-1 latent bug fix).
    if isinstance(item.get('primary'), bool):
        item['optional'] = not bool(item.pop('primary'))
    if 'plan' not in item:
        return
    plan = _norm(item.pop('plan'))
    if plan in USER_LANG_OPTIONAL_FALSE:
        item['optional'] = False
    elif plan in USER_LANG_OPTIONAL_TRUE:
        item['optional'] = True


def walk_translate(o):
    if isinstance(o, dict):
        _translate_one_dict(o)
        for v in o.values():
            walk_translate(v)
    elif isinstance(o, list):
        for v in o:
            walk_translate(v)


def _collect_banned_in_dict(o, found):
    for k in o.keys():
        if k in BANNED_AD_HOC_KEYS:
            found.append(k)
    for v in o.values():
        _collect_banned(v, found)


def _collect_banned(o, found):
    if isinstance(o, dict):
        _collect_banned_in_dict(o, found)
    elif isinstance(o, list):
        for v in o:
            _collect_banned(v, found)


def _scoped_in_dict(o, banned_keys, found):
    for k in o.keys():
        if k in banned_keys:
            found.append(k)
    for v in o.values():
        _collect_agent_scoped_banned(v, banned_keys, found)


def _collect_agent_scoped_banned(o, banned_keys, found):
    """Recursively collect any of banned_keys appearing as a dict key."""
    if isinstance(o, dict):
        _scoped_in_dict(o, banned_keys, found)
    elif isinstance(o, list):
        for v in o:
            _collect_agent_scoped_banned(v, banned_keys, found)


def _agent_scoped_guidance(agent, found_unique):
    """W8 AC13 guiding error message for agent-scoped rejection."""
    return (
        f"Unknown field {found_unique} for agent '{agent}': not yet "
        "supported on attractions/shopping/entertainment shape (only "
        "meals uses primary+alternatives[]). Full unification is M2 "
        "spec scope; for this cycle, use the flat list + optional:true "
        "shape."
    )


def _reject_agent_scoped(agent, agent_data):
    """W8 AC13: agent-scoped rejection for alternatives[] on flat shapes."""
    scoped_keys = AGENT_SCOPED_BANNED_KEYS.get(agent)
    if not scoped_keys:
        return
    found = []
    _collect_agent_scoped_banned(agent_data, scoped_keys, found)
    if not found:
        return
    msg = _agent_scoped_guidance(agent, sorted(set(found)))
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def reject_banned(agent: str, agent_data) -> None:
    found = []
    _collect_banned(agent_data, found)
    if found:
        unique = sorted(set(found))
        msg = (f"Unknown field(s) {unique} for agent '{agent}': not in "
               "schema. Use the schema-defined `optional` field instead "
               "(spec-20260506-092951 §5.9).")
        print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1)
    _reject_agent_scoped(agent, agent_data)
