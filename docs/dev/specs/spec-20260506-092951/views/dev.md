<!-- AUTO-GENERATED VIEW for dev | source: docs/dev/specs/spec-20260506-092951.md | extracted: 2026-05-06T00:00:00Z -->

# dev view of spec-20260506-092951

**Monolith**: docs/dev/specs/spec-20260506-092951.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> **Pipeline**: ba → dev → qa

---

## Section 1: Before

<!-- WHO WRITES: PM (autonomous mode) or User (user-spec mode) or BA (if Section 1 empty and BA has context) -->
<!-- WHAT: Screenshot path + text description of the current state BEFORE any fix attempt. -->
<!-- This establishes the baseline so later cycles can compare. -->

### Cycle 1

**Trigger session**: 2026-05-05/06 `/review china/2026-04-12/` ran ~5 hours. User extremely frustrated with iterative failures. Two retrospectives produced (Claude self-audit) plus codex CLI second-opinion audit. This spec consolidates ALL findings.

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

**Behavioral pattern (informational, NOT a fix-target)**: Claude repeatedly preferred surface-level fixes (regex global replace, "0 fetched assumed cache hit", "user must hard-refresh") over root-cause investigation. User explicitly said behavioral fixes are out of scope — the goal is harness enforcement, not Claude's discipline.

## Section 2: What Was Attempted

<!-- WHO WRITES: Dev (after each implementation attempt) -->
<!-- WHAT: Per-cycle record of what approach was tried, what the rationale was, and why it failed (if it failed). -->
<!-- This prevents the next cycle's Dev from repeating the same approach. -->

### Cycle 1

_Not yet populated._

## Section 3: What Was Changed

<!-- WHO WRITES: Dev (after each implementation) -->
<!-- WHAT: Exact file changes with line numbers and old->new values. -->
<!-- FORMAT: - **file.tsx:42** -- `property: oldValue` -> `property: newValue` -->

### Cycle 1

_Not yet populated._

### 5.1: Block schema-violating writes at the moment of write

**Goal**: PostToolUse hook on `Write`/`Edit` to `data/**/*.json` runs strict-mode `plan-validate.py` (with `additionalProperties:false` enforcement and explicit-null rejection for typed fields) BEFORE the file is allowed to persist into checkpoint. If validation fails, the write is rolled back / blocked, not warned.

### 5.2: Image fetcher must fail loudly, not silently

**Goal**: `scripts/fetch-images-batch.py` exits non-zero on any of the following:
- Required helper script path missing at startup (`assert os.path.exists(SKILL_PATH)` raises before any work).
- Total fetch attempts > 0 AND success rate < threshold (suggest 50% as starting threshold; tunable).
- Helper subprocess emits stderr that indicates failure (network error, auth error, JSON parse failure).
- 0 fetches AND non-empty input target list (distinguishes "all cached" from "all failed" by exit code).

### 5.3: Permanently ban batch / multi-day data operations

**Goal**: Raw `Write`/`Edit` to `data/**/*.json` is BLOCKED. Data edits MUST go through a structured per-day API that:
- Takes a single `--day N` argument (no `--days "1-5,8"` ranges, no `--all-days` flag).
- Performs schema validation before write.
- Performs old-value check on each modified field (refuse if old-value doesn't match expected, to prevent unintended overwrites).
- Cannot be invoked across multiple days in a single call.

### 5.4: Auto-commit moves to refs/checkpoints/<branch>, never advances HEAD

**Goal**: `posttool-git-checkpoint.sh` writes only to `refs/checkpoints/<current-branch>` via `git update-ref`. HEAD advances ONLY on:
- Explicit user `git commit`
- `/commit` slash command (closed-task or `--force` mode)
- `/merge`

### 5.7: Cross-file referential integrity + plan completeness invariant

**Goal**: A linter (`scripts/check-plan-integrity.py` or similar) runs as part of the schema hook (5.1) and rejects:
- Any `name_base` in attractions/meals/entertainment/shopping that has no matching key in `timeline.timeline` for that day (substring-match acceptable, but exact match preferred).
- Any day where a Plan label (A/B/C) has fewer than 2 items, unless explicitly marked as single-item with a documented reason.
- Any duplicate route/segment that appears in BOTH `transportation.intra_city_routes` AND `timeline.travel_segments` AND `timeline.timeline` for the same day at overlapping times.

## Section 8: Attention Notes

<!-- WHO WRITES: PM-Retro -->
<!-- WHAT: Issue-specific traps, warnings, and things to watch out for in the next cycle/session. -->
<!-- Example: "This file is imported by 12 components -- changes here cascade widely" -->

**Implementation order matters**:
1. **5.1 (schema hook) MUST land before 5.5 (data bug fixes)** — otherwise the data fixes themselves can re-introduce schema violations and there's no automated catch.
2. **5.4 (auto-commit→checkpoint ref) MUST land before any large dev cycle** — otherwise the implementation churn pollutes HEAD and rerunning becomes painful.
3. **5.3 (batch ban) MUST land before 5.5 (data bug fixes)** — the data fixes touch multiple days and the dev should be FORCED to do them per-day, not via batch regex.

**Pre-existing PreToolUse hooks on Write/Edit** (`pretool-quality-gate.py`, `pretool-block-production-files.sh`) do code-quality + path-block but NOT schema validation. New hook for 5.1 / 5.3 must compose with these without conflicts.

**Path mismatch already partially mitigated by symlink** — but symlink is fragile (deleted accidentally → silent failure returns). 5.2 must include a hard `os.path.exists` check at script startup so future symlink deletion fails LOUDLY.

**`_isAlternative` is dead code** — never assigned anywhere in the renderer. Either wire it up (Option A in 5.6) or delete (Option B). Don't leave it as zombie code that suggests functionality that doesn't exist.

**`docs/incidents-2026-04-04.md`** describes prior production catastrophes — Lesson 13 ("NEVER let a single subagent handle multiple tasks") is directly relevant to 5.3 (batch ban). Cross-reference when implementing.

**Codex audit raw output**: `/var/tmp/codex-outputs/codex-output-1263055-1778057849.txt` — referenced for evidence of all eight Section-1 active bugs. Will be auto-cleaned in 7 days; mirror to `docs/dev/specs/spec-20260506-092951/codex-audit.txt` as part of the dev cycle if persistent reference is needed.
