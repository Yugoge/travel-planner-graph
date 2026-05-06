<!-- AUTO-GENERATED VIEW for qa | source: docs/dev/specs/spec-20260506-092951.md | extracted: 2026-05-06T00:00:00Z -->

# qa view of spec-20260506-092951

**Monolith**: docs/dev/specs/spec-20260506-092951.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> **Pipeline**: ba → dev → qa

---

## Section 4: Current State

<!-- WHO WRITES: QA (after each verification) -->
<!-- WHAT: Actual measured values -- pixel dimensions, computed CSS, console output, screenshot paths. -->
<!-- This gives the next cycle's Dev concrete data to work with instead of vague "it failed". -->

### Cycle 1

_Not yet populated._

**Acceptance**:
- A test write that adds a non-schema field (e.g. `plan_label` on an `attraction_item`) is BLOCKED with a clear error pointing at the violating field.
- A test write that sets a required string field to `null` (e.g. `name_local: null`) is BLOCKED.
- A test write that emits `location_change: null` for an optional `object` field is BLOCKED (recommend deletion or empty-object).
- A test write that emits an empty `coordinates: {}` is BLOCKED (must satisfy `{lat, lng}`).
- The hook runs BEFORE the auto-commit / checkpoint hook so dirty data never reaches a checkpoint ref.
- Explicit error messages name the file path, JSON path of the violation, and the schema rule that rejected it.
- Schemas themselves must be tightened where they are currently lax — at minimum, decide whether `transportation.intra_city_routes` and `budget.breakdown.*_detail` should remain `additionalProperties:true` or be promoted to `false` with documented allowed keys (BA decides; document the rationale in the resulting spec view).

**Acceptance**:
- Removing the symlink at `.claude/skills/gaode-maps` reproduces the original failure → script now exits non-zero with a clear "helper not found at <path>" error instead of `Total fetched: 0/0 ✓ Updated 0 POIs` happy banner.
- Cache-hit-only scenario (everything already in cache, 0 fetches needed) exits 0 with explicit "cache hit, no fetches required" banner — distinct from failure.
- Mock 100% Gaode fail scenario exits non-zero.
- The `408-411` and `433-436` broad exception swallowing is replaced with: catch specific expected exceptions (network/timeout) → record failure; let unexpected exceptions propagate.

**Acceptance**:
- `Write` tool attempt on `data/china-*/timeline.json` is BLOCKED by PreToolUse hook with message pointing to the structured API.
- `Edit` tool attempt that uses `replace_all: true` on a data file is BLOCKED.
- `scripts/save.py` (or successor) gains a mandatory `--day N` argument; absence of `--day` exits non-zero.
- Bulk regex search-replace by Claude (the "Matilde solo → Both together" pattern that damaged Day 8/9) is structurally impossible because the only allowed write path is `--day N`.
- Documented escape hatch: human user (NOT Claude) can override with explicit `--bypass-day-guard` flag, but agent invocations MUST NOT have access to this flag.

**Acceptance**:
- Running 13+ tool-use cycles on master produces ZERO new entries in `git log master`.
- `git log refs/checkpoints/master` shows the per-cycle checkpoints (preserving recovery capability).
- `git log` default view shows only logical/intentional commits.
- The current implementation in `.claude/hooks/posttool-git-checkpoint.sh:29-46` is REPLACED, not just documented.
- Recovery procedure documented: how to inspect / cherry-pick from `refs/checkpoints/<branch>` if a session crashes.

**Acceptance** (per-bug, all must pass):
1. No reference to `喜樂院子` remains in `timeline.json` Days 4-9 or `transportation.json` Days 4-9 — replaced with Atour Yulin Huaxi (or removed if accommodation-orthogonal).
2. Day 8 traveler matrix is internally consistent across `timeline.json`, `meals.json`, `entertainment.json` (all three say the same thing for each slot).
3. `transportation.json:364-367` Day 9 location is `Xi'an`, and a Chengdu→Xi'an intercity segment exists (HSR or flight, BOOKED status as appropriate).
4. For every day in `budget.json`: `budget.total == sum(budget.{meals, accommodation, activities, entertainment, shopping, transportation, cafe})`. Assessment strings reference the same numeric values (no stale 980 references when actual is 1230).
5. No timeline activity has `start_time == end_time` with `duration_minutes > 0`. Every entry's `duration_minutes` matches `(end - start) in minutes`.
6. Every `name_local` field in China-trip data files contains at least one Chinese character (CJK Unified Ideographs range) AND has no dangling/unmatched parentheses.
7. Every Plan A/B/C attraction either has a matching `timeline.json` entry with non-degenerate time OR is removed from the attractions array. Items tagged "PRIMARY" cannot also be tagged "Optional" (mutually exclusive).
8. `shopping.json:133` Weidu Antique City note is updated to reflect the actual Day 4 destination (Chengdu) or removed.

**Acceptance**:
- `grep -rn '"plan_label"' data/china-20260412-092624/` returns zero matches.
- 5.1's strict-schema PreToolUse hook BLOCKS any future write that introduces `plan_label` to any data file (it remains non-standard forever).
- Spec 5.7's referential-integrity linter no longer special-cases `plan_label`.

**Acceptance**:
- Reproduce the Plan-C-hollowed scenario (move all but one Plan-C attraction to Plan-A) → linter blocks the write.
- Reproduce the G5415 / 五通桥 triple-duplication → linter blocks the write.
- Reproduce a renamed timeline key (e.g. `[Optional Plan B]` middle insertion) → linter flags the broken reference.

**Acceptance**:
- `grep -rnE '"(plan_label|is_alternative|_isAlternative|tier|bundle_id|priority_label)"' data/china-*/` returns zero matches across all trip data.
- save.py rejects any structured-input JSON that contains keys not present in the corresponding schema, with error message naming the unknown field.
- Future agent prompts using "Plan A/B/C" terminology are translated by the orchestrator (or save.py wrapper) into `optional` flags before any data write — no agent is permitted to write the literal string `plan_label` or similar.
- 5.1's strict-write hook BLOCKs any non-schema field at write time as defense-in-depth.

## Section 6: Why Not Met

<!-- WHO WRITES: QA (when verdict is fail) -->
<!-- WHAT: Specific gap between measured state (Section 4) and acceptance criterion (Section 5). -->
<!-- Must include evidence: actual value vs expected value. -->

### Cycle 1

_Not yet populated._

## Section 7: What Must Be Done

<!-- WHO WRITES: QA (on fail) or PM-Retro -->
<!-- WHAT: Prescriptive next step for this specific issue. Not generic advice -- a concrete action. -->
<!-- Example: "Increase padding from 8px to 16px in Chat.tsx:42" not "fix the padding" -->

### Cycle 1

_Not yet populated._
