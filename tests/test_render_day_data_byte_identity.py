"""Merged-dict byte-identity invariant test (W7 / spec-20260513-085358 AC12).

Verifies that the post-refactor _merge_day_data produces the same merged
dict as the pre-refactor implementation for every input that does NOT
traverse Bug-1/2/3 code paths.

The invariant is checked against a baseline snapshot captured BEFORE the
refactor (stored in tests/data/baseline_merged_dicts_china_20260412.json).
The new keys added by Bug-1 (`meal_alternatives`) and Bug-3
(`unscheduled_optionals`) are stripped from the post-refactor dict before
comparison, since those keys did not exist pre-refactor.

Usage:
    python3 tests/test_render_day_data_byte_identity.py

Exit code 0 = invariant holds; 1 = one or more days diverge.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))


NEW_KEYS = {"meal_alternatives", "unscheduled_optionals"}


def _load_generator():
    """Import the InteractiveHTMLGenerator class lazily (hyphenated filename)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen", REPO / "scripts" / "generate-html-interactive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.InteractiveHTMLGenerator


def _capture_post(plan_id):
    """Capture merged dicts for all days using current code."""
    InteractiveHTMLGenerator = _load_generator()
    gen = InteractiveHTMLGenerator(plan_id)
    plan = gen._load_json("plan-skeleton.json")
    out = {}
    for ds in plan.get("days", []):
        merged = gen._merge_day_data(ds)
        out[ds.get("day")] = merged
    return out


def _strip_new_keys(merged):
    """Remove Bug-1/Bug-3 keys before comparing to pre-refactor baseline."""
    return {k: v for k, v in merged.items() if k not in NEW_KEYS}


def _normalize(merged):
    """json.dumps(sort_keys=True) representation."""
    return json.dumps(_strip_new_keys(merged), sort_keys=True, ensure_ascii=False)


def main():
    """Compare post-refactor merged dicts against baseline snapshot."""
    baseline_path = REPO / "tests" / "data" / "baseline_merged_dicts_china_20260412.json"
    if not baseline_path.exists():
        print(f"ERROR: baseline snapshot missing: {baseline_path}", file=sys.stderr)
        print("Capture it by running the pre-refactor code with the snapshotter.",
              file=sys.stderr)
        return 2
    baseline = json.loads(baseline_path.read_text())
    post = _capture_post("china-20260412-092624")
    diffs = []
    for day, merged in post.items():
        norm = _normalize(merged)
        base = baseline.get(str(day))
        if base is None:
            diffs.append((day, "baseline missing entry"))
            continue
        if norm != base:
            diffs.append((day, "mismatch"))
    if diffs:
        print(f"FAIL: {len(diffs)} day(s) diverge from baseline:")
        for d, why in diffs:
            print(f"  day {d}: {why}")
        return 1
    print(f"PASS: byte-identity holds for all {len(post)} days "
          "(after stripping meal_alternatives + unscheduled_optionals).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
