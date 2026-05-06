<!-- AUTO-GENERATED VIEW for dev | source: docs/dev/specs/spec-20260506-092951.md | extracted: 2026-05-05T23:38:00Z -->

# dev view of spec-20260506-092951

**Monolith**: docs/dev/specs/spec-20260506-092951.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> **Pipeline**: ba → dev → qa

> <!-- WHO WRITES: Dev (after each implementation attempt) -->

> <!-- WHO WRITES: Dev (after each implementation) -->

---

# Spec: Travel-planner harness root-cause hardening — block schema/semantic violations at write-time, fix accumulated data bugs, kill HEAD pollution

**Pipeline**: ba → dev → qa
**Session**: spec-20260506-092951
**Created**: 2026-05-06T09:29:51+00:00

---

## Section 2: What Was Attempted

<!-- WHO WRITES: Dev (after each implementation attempt) -->
<!-- WHAT: Per-cycle record of what approach was tried, what the rationale was, and why it failed (if it failed). -->
<!-- This prevents the next cycle's Dev from repeating the same approach. -->

## Section 3: What Was Changed

<!-- WHO WRITES: Dev (after each implementation) -->
<!-- WHAT: Exact file changes with line numbers and old->new values. -->
<!-- FORMAT: - **file.tsx:42** -- `property: oldValue` -> `property: newValue` -->

## Section 1: Before — Concrete Targets

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

**Active harness failures** (line numbers refined by background Explore agent):
- `fetch-images-batch.py:408-411` (`except subprocess.TimeoutExpired: continue` / `except Exception: continue`) and `:433-436` (`except subprocess.TimeoutExpired: pass` / `except Exception: pass`) swallow ALL errors silently. Lines `:1151-1156` print unconditional `✅ Batch complete` banner regardless of failure rate. Path mismatch at `:390, :416` is currently masked by a symlink at `.claude/skills/gaode-maps` (fragile — symlink deletion → silent regression).
- Strict-schema validator at deploy is `verify-plan-integrity.py --strict-schema` (called from `scripts/generate-and-deploy.sh:160-162, 200-202`), **NOT** `plan-validate.py`. PostToolUse on Write/Edit at `.claude/settings.json:138-145` only runs `posttool-git-checkpoint.sh`, no schema validation. PreToolUse on Write/Edit currently has `pretool-quality-gate.py` (code quality) + `pretool-block-production-files.sh` (path-block) — neither does schema enforcement on data files.
- Auto-commit hook `.claude/hooks/posttool-git-checkpoint.sh:30-42, 44-51` advances HEAD via `git commit` and auto-pushes to origin (background) — produced 13+ Auto-commit entries on master in 90 minutes.
- `scripts/save.py` (698 lines) currently exposes `--trip`, `--agent`, `--input`, `--batch`, `--no-validate`, `--allow-high`, `--no-backup` — has **NO `--day` option**. Claude's previous "use save.py --day N" harness proposal is based on a non-existent API and must either extend `save.py` or build a new structured editor.
- HTML renderer `scripts/generate-html-interactive.py:3043-3053` reads `entry.optional || entry._isAlternative` for visual treatment (dashed border, "备选/Alt" badge with distinct color), but `_isAlternative` is **NEVER assigned anywhere** in the codebase — dead code suggesting Plan B/C distinct rendering that doesn't exist. `plan_label` field was written by data agents (in `timeline.json`, technically allowed by `timeline_activity.additionalProperties:true`) but is a **non-standard field Claude introduced unilaterally** — it was never in any schema as an authorized field, and renderer never reads it. Resolution per Section 5.6: delete `plan_label` from all data files and forbid future writes.
- Schemas are lax: `transportation.schema.json:193-196` `intra_city_routes` is `additionalProperties: true` with description "Freeform structure with route_N (or descriptor) keys; values are open dicts." `budget.json` `breakdown.*_detail` similarly allows arbitrary keys.
- `plan-validate.py` (1788 lines) supports `--json`, `--json-file`, `--min-severity`, `--agent`, but has **NO `--strict-schema` CLI flag** — would need extension or wrapper for write-time blocking. Currently the strict validator (`verify-plan-integrity.py`) is a separate script invoked only at deploy.

---

## Section 5: Implementation Requirements

### 5.1: Block schema-violating writes at the moment of write

**Goal**: PostToolUse hook on `Write`/`Edit` to `data/**/*.json` runs strict-mode `plan-validate.py` (with `additionalProperties:false` enforcement and explicit-null rejection for typed fields) BEFORE the file is allowed to persist into checkpoint. If validation fails, the write is rolled back / blocked, not warned.

**Acceptance**:
- A test write that adds a non-schema field (e.g. `plan_label` on an `attraction_item`) is BLOCKED with a clear error pointing at the violating field.
- A test write that sets a required string field to `null` (e.g. `name_local: null`) is BLOCKED.
- A test write that emits `location_change: null` for an optional `object` field is BLOCKED (recommend deletion or empty-object).
- A test write that emits an empty `coordinates: {}` is BLOCKED (must satisfy `{lat, lng}`).
- The hook runs BEFORE the auto-commit / checkpoint hook so dirty data never reaches a checkpoint ref.
- Explicit error messages name the file path, JSON path of the violation, and the schema rule that rejected it.
- Schemas themselves must be tightened where they are currently lax — at minimum, decide whether `transportation.intra_city_routes` and `budget.breakdown.*_detail` should remain `additionalProperties:true` or be promoted to `false` with documented allowed keys (BA decides; document the rationale in the resulting spec view).

### 5.2: Image fetcher must fail loudly, not silently

**Goal**: `scripts/fetch-images-batch.py` exits non-zero on any of the following:
- Required helper script path missing at startup (`assert os.path.exists(SKILL_PATH)` raises before any work).
- Total fetch attempts > 0 AND success rate < threshold (suggest 50% as starting threshold; tunable).
- Helper subprocess emits stderr that indicates failure (network error, auth error, JSON parse failure).
- 0 fetches AND non-empty input target list (distinguishes "all cached" from "all failed" by exit code).

**Acceptance**:
- Removing the symlink at `.claude/skills/gaode-maps` reproduces the original failure → script now exits non-zero with a clear "helper not found at <path>" error instead of `Total fetched: 0/0 ✓ Updated 0 POIs` happy banner.
- Cache-hit-only scenario (everything already in cache, 0 fetches needed) exits 0 with explicit "cache hit, no fetches required" banner — distinct from failure.
- Mock 100% Gaode fail scenario exits non-zero.
- The `408-411` and `433-436` broad exception swallowing is replaced with: catch specific expected exceptions (network/timeout) → record failure; let unexpected exceptions propagate.

### 5.3: Permanently ban batch / multi-day data operations

**Goal**: Raw `Write`/`Edit` to `data/**/*.json` is BLOCKED. Data edits MUST go through a structured per-day API that:
- Takes a single `--day N` argument (no `--days "1-5,8"` ranges, no `--all-days` flag).
- Performs schema validation before write.
- Performs old-value check on each modified field (refuse if old-value doesn't match expected, to prevent unintended overwrites).
- Cannot be invoked across multiple days in a single call.

**Acceptance**:
- `Write` tool attempt on `data/china-*/timeline.json` is BLOCKED by PreToolUse hook with message pointing to the structured API.
- `Edit` tool attempt that uses `replace_all: true` on a data file is BLOCKED.
- `scripts/save.py` (or successor) gains a mandatory `--day N` argument; absence of `--day` exits non-zero.
- Bulk regex search-replace by Claude (the "Matilde solo → Both together" pattern that damaged Day 8/9) is structurally impossible because the only allowed write path is `--day N`.
- Documented escape hatch: human user (NOT Claude) can override with explicit `--bypass-day-guard` flag, but agent invocations MUST NOT have access to this flag.

### 5.4: Auto-commit moves to refs/checkpoints/<branch>, never advances HEAD

**Goal**: `posttool-git-checkpoint.sh` writes only to `refs/checkpoints/<current-branch>` via `git update-ref`. HEAD advances ONLY on:
- Explicit user `git commit`
- `/commit` slash command (closed-task or `--force` mode)
- `/merge`

**Acceptance**:
- Running 13+ tool-use cycles on master produces ZERO new entries in `git log master`.
- `git log refs/checkpoints/master` shows the per-cycle checkpoints (preserving recovery capability).
- `git log` default view shows only logical/intentional commits.
- The current implementation in `.claude/hooks/posttool-git-checkpoint.sh:29-46` is REPLACED, not just documented.
- Recovery procedure documented: how to inspect / cherry-pick from `refs/checkpoints/<branch>` if a session crashes.

### 5.5: Eight residual data bugs in `data/china-20260412-092624/` must be fixed

**Goal**: All eight active bugs listed in Section 1 are resolved.

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

**Resolution (no longer a choice — user has decided)**:
- `plan_label` is a non-standard field Claude unilaterally introduced. DELETE it from every data file: `attractions.json`, `meals.json`, `entertainment.json`, `shopping.json`, `transportation.json`, `timeline.json`, `cafe.json`, `accommodation.json`, `budget.json` (search-and-strip across the entire trip data tree).
- Plan A/B/C remain only as **literal conceptual labels** expressed via:
  - `optional: false` for Plan A (primary) items
  - `optional: true` for Plan B/C (alternative) items
  - Optional human-readable prefix in `notes_base` like `[PLAN A]` / `[PLAN B - ALTERNATIVE]` / `[PLAN C - ALTERNATIVE]` (free-text, NOT a schema field)
- HTML renderer continues using only `optional`. No visual distinction between Plan B and Plan C — both render as `optional` (dashed border, "Optional" badge).
- `_isAlternative` is dead code in `scripts/generate-html-interactive.py:3043-3053` (read but never assigned). Delete the dead branches OR leave as-is (orchestrator-internal cleanup, low priority).
- DO NOT add `plan_label` to any schema. DO NOT promote it to standard. Treat any future agent attempt to write `plan_label` as a schema violation under 5.1's strict-write enforcement.

**Acceptance**:
- `grep -rn '"plan_label"' data/china-20260412-092624/` returns zero matches.
- 5.1's strict-schema PreToolUse hook BLOCKS any future write that introduces `plan_label` to any data file (it remains non-standard forever).
- Spec 5.7's referential-integrity linter no longer special-cases `plan_label`.

### 5.7: Cross-file referential integrity + plan completeness invariant

**Goal**: A linter (`scripts/check-plan-integrity.py` or similar) runs as part of the schema hook (5.1) and rejects:
- Any `name_base` in attractions/meals/entertainment/shopping that has no matching key in `timeline.timeline` for that day (substring-match acceptable, but exact match preferred).
- Any day where a Plan label (A/B/C) has fewer than 2 items, unless explicitly marked as single-item with a documented reason.
- Any duplicate route/segment that appears in BOTH `transportation.intra_city_routes` AND `timeline.travel_segments` AND `timeline.timeline` for the same day at overlapping times.

### 5.9: User-language vs machine-schema boundary — translation is mandatory, ad-hoc field introduction is forbidden

**The single write path is `scripts/save.py`** (post-extension per 5.3 with `--day N`). save.py is responsible for:
- Accepting structured input that maps onto existing schema fields only
- Rejecting input fields that aren't in the schema
- Translating common user-language synonyms (e.g., `"primary": true` → `optional: false` if writer used user phrasing)

---

## Section 8: Attention Notes

**Implementation order matters**:
1. **5.1 (schema hook) MUST land before 5.5 (data bug fixes)** — otherwise the data fixes themselves can re-introduce schema violations and there's no automated catch.
2. **5.4 (auto-commit→checkpoint ref) MUST land before any large dev cycle** — otherwise the implementation churn pollutes HEAD and rerunning becomes painful.
3. **5.3 (batch ban) MUST land before 5.5 (data bug fixes)** — the data fixes touch multiple days and the dev should be FORCED to do them per-day, not via batch regex.

**`scripts/save.py` does NOT have `--day` option currently** — Claude's previous proposal was based on a non-existent API. Either extend `save.py` or build a new structured editor as part of 5.3. Do not pretend the API exists.

**Pre-existing PreToolUse hooks on Write/Edit** (`pretool-quality-gate.py`, `pretool-block-production-files.sh`) do code-quality + path-block but NOT schema validation. New hook for 5.1 / 5.3 must compose with these without conflicts.

**Path mismatch already partially mitigated by symlink** — but symlink is fragile (deleted accidentally → silent failure returns). 5.2 must include a hard `os.path.exists` check at script startup so future symlink deletion fails LOUDLY.

**`_isAlternative` is dead code** — never assigned anywhere in the renderer. Either wire it up (Option A in 5.6) or delete (Option B). Don't leave it as zombie code that suggests functionality that doesn't exist.

**Codex audit raw output**: `/var/tmp/codex-outputs/codex-output-1263055-1778057849.txt` — referenced for evidence of all eight Section-1 active bugs. Will be auto-cleaned in 7 days; mirror to `docs/dev/specs/spec-20260506-092951/codex-audit.txt` as part of the dev cycle if persistent reference is needed.
