<!-- AUTO-GENERATED VIEW for qa | source: docs/dev/specs/spec-20260506-092951.md | extracted: 2026-05-05T23:38:00Z -->

# qa view of spec-20260506-092951

**Monolith**: docs/dev/specs/spec-20260506-092951.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> **Pipeline**: ba → dev → qa

> <!-- WHO WRITES: QA (after each verification) -->
> <!-- WHAT: Actual measured values -- pixel dimensions, computed CSS, console output, screenshot paths. -->
> <!-- This gives the next cycle's Dev concrete data to work with instead of vague "it failed". -->

> <!-- WHO WRITES: QA (when verdict is fail) -->
> <!-- WHAT: Specific gap between measured state (Section 4) and acceptance criterion (Section 5). -->
> <!-- Must include evidence: actual value vs expected value. -->

> <!-- WHO WRITES: QA (on fail) or PM-Retro -->
> <!-- WHAT: Prescriptive next step for this specific issue. Not generic advice -- a concrete action. -->

---

# Spec: Travel-planner harness root-cause hardening — block schema/semantic violations at write-time, fix accumulated data bugs, kill HEAD pollution

**Pipeline**: ba → dev → qa
**Session**: spec-20260506-092951
**Created**: 2026-05-06T09:29:51+00:00

---

## Section 4: Current State

<!-- WHO WRITES: QA (after each verification) -->
<!-- WHAT: Actual measured values -- pixel dimensions, computed CSS, console output, screenshot paths. -->
<!-- This gives the next cycle's Dev concrete data to work with instead of vague "it failed". -->

## Section 6: Why Not Met

<!-- WHO WRITES: QA (when verdict is fail) -->
<!-- WHAT: Specific gap between measured state (Section 4) and acceptance criterion (Section 5). -->
<!-- Must include evidence: actual value vs expected value. -->

## Section 7: What Must Be Done

<!-- WHO WRITES: QA (on fail) or PM-Retro -->
<!-- WHAT: Prescriptive next step for this specific issue. Not generic advice -- a concrete action. -->
<!-- Example: "Increase padding from 8px to 16px in Chat.tsx:42" not "fix the padding" -->

## Section 1: Verification Targets (Active Bugs to Confirm Fixed)

**Active data bugs** (codex-verified, in `data/china-20260412-092624/`):

1. **Stale 喜樂院子 hotel references** after Atour Yulin Huaxi rebooking
   - `timeline.json:1027, 1038, 1049, 1076, 1127, 1130, 1247`
   - `transportation.json:357-358`

2. **Day 8 traveler state internally contradictory**
   - `timeline.json:1027-1043` says "both/shared"
   - `meals.json:1261` says "Matilde solo"
   - `entertainment.json:370` English says "Both travelers"; `:371` 中文 says Matilde 单独

3. **Day 9 transportation location is `Beijing` but should be `Xi'an`**
   - `transportation.json:364-367`

4. **Budget arithmetic + stale assessment strings**
   - Day 3: categories sum 1105, total reads 980 (`budget.json:173-180`)
   - Day 15: categories sum 641, total reads 586 (`budget.json:1175-1181`)
   - Day 5: actual total 1230, assessment string says 980 (`budget.json:1270, 1274`)

5. **Timeline degenerate / inconsistent durations**
   - Same start_time/end_time with nonzero duration_minutes: `timeline.json:622-625, 786-789, 938-940`
   - Duration mismatch: `timeline.json:1308-1310` says 09:00-11:00 but 112 min (should be 120)
   - `transportation.json:251-253` says 18:00-18:30 but 24 min (should be 30)

6. **Bilingual `*_local` field corruption**
   - `name_local` containing English text or malformed/dangling parentheses: `timeline.json:676-677, 696-697, 829-830, 968-989, 998-999`

7. **Plan/time rendering edge cases**
   - Optional-looking timeline entries lack `optional:true`: `timeline.json:617-621, 1049-1052`
   - Fangsuo Bookstore tagged `[PLAN A - PRIMARY] Optional` in attractions (`attractions.json:913, 925, 928`) but no timeline match → renders without time

8. **Stale itinerary text outside core flow**
   - `shopping.json:133` says Weidu Antique City "before departing for Beijing" but Day 4 now flies to Chengdu

**Active transit duplicates** (codex-confirmed):
- G5415 HSR appears in both `timeline.json:734` AND `transportation.json:204`
- 五通桥 taxi appears in `timeline.json:765`, `timeline.json:839`, AND `transportation.json:242`

---

## Section 5: Acceptance Criteria for Verification

> 将以上全部总结为一个spec，永久根本性地彻底修复

### 5.1: Block schema-violating writes at the moment of write

**Acceptance**:
- A test write that adds a non-schema field (e.g. `plan_label` on an `attraction_item`) is BLOCKED with a clear error pointing at the violating field.
- A test write that sets a required string field to `null` (e.g. `name_local: null`) is BLOCKED.
- A test write that emits `location_change: null` for an optional `object` field is BLOCKED (recommend deletion or empty-object).
- A test write that emits an empty `coordinates: {}` is BLOCKED (must satisfy `{lat, lng}`).
- The hook runs BEFORE the auto-commit / checkpoint hook so dirty data never reaches a checkpoint ref.
- Explicit error messages name the file path, JSON path of the violation, and the schema rule that rejected it.
- Schemas themselves must be tightened where they are currently lax — at minimum, decide whether `transportation.intra_city_routes` and `budget.breakdown.*_detail` should remain `additionalProperties:true` or be promoted to `false` with documented allowed keys (BA decides; document the rationale in the resulting spec view).

### 5.2: Image fetcher must fail loudly, not silently

**Acceptance**:
- Removing the symlink at `.claude/skills/gaode-maps` reproduces the original failure → script now exits non-zero with a clear "helper not found at <path>" error instead of `Total fetched: 0/0 ✓ Updated 0 POIs` happy banner.
- Cache-hit-only scenario (everything already in cache, 0 fetches needed) exits 0 with explicit "cache hit, no fetches required" banner — distinct from failure.
- Mock 100% Gaode fail scenario exits non-zero.
- The `408-411` and `433-436` broad exception swallowing is replaced with: catch specific expected exceptions (network/timeout) → record failure; let unexpected exceptions propagate.

### 5.3: Permanently ban batch / multi-day data operations

**Acceptance**:
- `Write` tool attempt on `data/china-*/timeline.json` is BLOCKED by PreToolUse hook with message pointing to the structured API.
- `Edit` tool attempt that uses `replace_all: true` on a data file is BLOCKED.
- `scripts/save.py` (or successor) gains a mandatory `--day N` argument; absence of `--day` exits non-zero.
- Bulk regex search-replace by Claude (the "Matilde solo → Both together" pattern that damaged Day 8/9) is structurally impossible because the only allowed write path is `--day N`.
- Documented escape hatch: human user (NOT Claude) can override with explicit `--bypass-day-guard` flag, but agent invocations MUST NOT have access to this flag.

### 5.4: Auto-commit moves to refs/checkpoints/<branch>, never advances HEAD

**Acceptance**:
- Running 13+ tool-use cycles on master produces ZERO new entries in `git log master`.
- `git log refs/checkpoints/master` shows the per-cycle checkpoints (preserving recovery capability).
- `git log` default view shows only logical/intentional commits.
- The current implementation in `.claude/hooks/posttool-git-checkpoint.sh:29-46` is REPLACED, not just documented.
- Recovery procedure documented: how to inspect / cherry-pick from `refs/checkpoints/<branch>` if a session crashes.

### 5.5: Eight residual data bugs in `data/china-20260412-092624/` must be fixed

**Acceptance** (per-bug, all must pass):
1. No reference to `喜樂院子` remains in `timeline.json` Days 4-9 or `transportation.json` Days 4-9 — replaced with Atour Yulin Huaxi (or removed if accommodation-orthogonal).
2. Day 8 traveler matrix is internally consistent across `timeline.json`, `meals.json`, `entertainment.json` (all three say the same thing for each slot).
3. `transportation.json:364-367` Day 9 location is `Xi'an`, and a Chengdu→Xi'an intercity segment exists (HSR or flight, BOOKED status as appropriate).
4. For every day in `budget.json`: `budget.total == sum(budget.{meals, accommodation, activities, entertainment, shopping, transportation, cafe})`. Assessment strings reference the same numeric values (no stale 980 references when actual is 1230).
5. No timeline activity has `start_time == end_time` with `duration_minutes > 0`. Every entry's `duration_minutes` matches `(end - start) in minutes`.
6. Every `name_local` field in China-trip data files contains at least one Chinese character (CJK Unified Ideographs range) AND has no dangling/unmatched parentheses.
7. Every Plan A/B/C attraction either has a matching `timeline.json` entry with non-degenerate time OR is removed from the attractions array. Items tagged "PRIMARY" cannot also be tagged "Optional" (mutually exclusive).
8. `shopping.json:133` Weidu Antique City note is updated to reflect the actual Day 4 destination (Chengdu) or removed.

### 5.6: Delete the unauthorized `plan_label` field from all data files

**Acceptance**:
- `grep -rn '"plan_label"' data/china-20260412-092624/` returns zero matches.
- 5.1's strict-schema PreToolUse hook BLOCKS any future write that introduces `plan_label` to any data file (it remains non-standard forever).
- Spec 5.7's referential-integrity linter no longer special-cases `plan_label`.

### 5.7: Cross-file referential integrity + plan completeness invariant

**Acceptance**:
- Reproduce the Plan-C-hollowed scenario (move all but one Plan-C attraction to Plan-A) → linter blocks the write.
- Reproduce the G5415 / 五通桥 triple-duplication → linter blocks the write.
- Reproduce a renamed timeline key (e.g. `[Optional Plan B]` middle insertion) → linter flags the broken reference.

### 5.9: User-language vs machine-schema boundary — translation is mandatory, ad-hoc field introduction is forbidden

**Acceptance**:
- `grep -rnE '"(plan_label|is_alternative|_isAlternative|tier|bundle_id|priority_label)"' data/china-*/` returns zero matches across all trip data.
- save.py rejects any structured-input JSON that contains keys not present in the corresponding schema, with error message naming the unknown field.
- Future agent prompts using "Plan A/B/C" terminology are translated by the orchestrator (or save.py wrapper) into `optional` flags before any data write — no agent is permitted to write the literal string `plan_label` or similar.
- 5.1's strict-write hook BLOCKs any non-schema field at write time as defense-in-depth.

### 5.8: Out-of-scope (explicitly excluded by user)

The following are NOT to be implemented in this spec, per user's directives:
- Agent post-hoc output auditing (e.g. verifying RedNote URLs after agent claims "RedNote ONLY") — relying on script + prompt strictness instead.
- HTML render visual validation automation (Playwright snapshots, viewport diff) — human inspection.
- Sub-agent shared decision cache / context inheritance — over-engineering.
- Attribution-bias diagnostics for Claude's behavior — accepted as a behavioral limitation.

---

## Section 8: Attention Notes for QA

**Implementation order matters**:
1. **5.1 (schema hook) MUST land before 5.5 (data bug fixes)** — otherwise the data fixes themselves can re-introduce schema violations and there's no automated catch.
2. **5.4 (auto-commit→checkpoint ref) MUST land before any large dev cycle** — otherwise the implementation churn pollutes HEAD and rerunning becomes painful.
3. **5.3 (batch ban) MUST land before 5.5 (data bug fixes)** — the data fixes touch multiple days and the dev should be FORCED to do them per-day, not via batch regex.
