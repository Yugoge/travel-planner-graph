<!-- AUTO-GENERATED VIEW for dev | source: docs/dev/specs/spec-20260521-061307.md | extracted: 2026-05-21T08:58:00+00:00 -->

# dev view of 20260521-061307

**Monolith**: docs/dev/specs/spec-20260521-061307.md
**Extraction**: content-block level (no section-level mapping)

---

# Spec: travel.life-ai.app drag-and-drop UX polish (5 issues from user 1★ feedback on task 20260520-200804)

**Pipeline**: BA → dev → QA (single-cycle expected; UX polish, not new features)
**Session**: c59044cd-0bea-4cf9-9b55-61a7bb1d9f65
**Created**: 2026-05-21T06:13:07+00:00

---

## Role Mandate

> **Pipeline**: BA → dev → QA (single-cycle expected; UX polish, not new features)

> - Dev should run the verification grep that QA + close-debate will run, before declaring complete.

---

## Section 1: Before

### Cycle 1

Affected file (primary): `/root/travel-planner/scripts/lib/react_template.tpl` (single file, ~45-60 line changes).

**Codex-verified root causes** (log: `/var/tmp/codex-outputs/codex-output-2070882-1779344693.txt`):

| Bug | Root cause file:line | Fix scope |
|-----|---------------------|-----------|
| 1 (style fragmentation) | Independent inline styles at L2418-2424 (accommodation), L2473-2478 (meals), L2524-2529 (activities) vs Kanban `cardStyle()` factory at L816-824 | Extract `candidateCardStyle()` helper; 3 sites replace inline with helper call |
| 2 (no image on drag-in) | Slot cards check `image` only (L870, L960, L1048, L1133, L1274, L1828-1830); Candidates accommodation checks `cover_image \|\| image` at L2427-2429 — mismatch when v2 option carries `cover_image` but not `image` | 6 sites: `image` → `cover_image \|\| image` |
| 3 (replaced option disappears) | Bridge at L2769-2773 writes new selection, saves one mutation at L2795, accommodation merge at L2063-2069 overwrites the single rendered hotel object — no demotion path. Candidate lists are sourced from `editorDay.accommodation.options.map(...)` at L2398 and `slot.options.map(...)` at L2504 — if previously-selected option isn't in `bucket.options`, it cannot reappear | Bridge captures `prevId` before writing, pushes old option object into `bucket.options[]` if absent |
| 4 (left/main not draggable) | Accommodation primary card at L1265-1272 has **NO** `draggable`, `onDragStart`, or `onDragEnd` attributes — meals/activities have them at L862-864, L952-954, L1040-1042, L1125-1127 | Add `draggable={!!selectedAccId}` + `onDragStart` setting `direction:'board'` payload + `onDragEnd` |
| 5 (can't drag out) | Same root cause as #4 — Candidates drop target at L2381-2383 and `handleSidebarDrop` at L2335-2338 work correctly; accommodation never emits the required `direction:'board'` payload because it has no dragstart handler | Fix #4 resolves this automatically |

**Cross-bug dependency**: Fix #4 MUST precede #5 (same fix). #1 and #2 are independent. #3 should be tested after #4/#5 because drag-out/replace flows share selection state.

**Codex live-DOM verification**: codex fetched the served page via Python HTTP GET + Playwright rendering and confirmed: `#candidates-groups` exists, `.card-candidate` exists, left/main `[data-slot-card]` cards exist, accommodation primary card has `data-slot-id="accommodation"` + `data-option-id="accommodation-1-2"` but NO `draggable` attribute. The bug is observable in production at travel.life-ai.app.

---

## Section 2: What Was Attempted

<!-- WHO WRITES: Dev (after each implementation attempt) -->
<!-- WHAT: Per-cycle record of what approach was tried, what the rationale was, and why it failed (if it failed). -->
<!-- This prevents the next cycle's Dev from repeating the same approach. -->

### Cycle 1

_Not yet populated._

---

## Section 3: What Was Changed

<!-- WHO WRITES: Dev (after each implementation) -->
<!-- WHAT: Exact file changes with line numbers and old->new values. -->
<!-- FORMAT: - **file.tsx:42** -- `property: oldValue` -> `property: newValue` -->

### Cycle 1

_Not yet populated._

---

## Section 8: Attention Notes

**From iteration-burnout memory (feedback_iteration_burnout.md)**: prior cycles 20260519-161933 + 20260520-200804 burned 3 close-debate rounds each on incomplete-fix iteration. For THIS cycle:
- BA must specify "grep entire file for the symptom pattern" not "fix L<N>". Same-class issues across multiple sites must enumerate ALL sites, not a subset.
- Dev should run the verification grep that QA + close-debate will run, before declaring complete.
- QA should re-grep before signing off.
- Limit close-debate cycles to ≤2 — force-close + document as out-of-scope if codex catches a 3rd round of same-class issue.

**File scope**: changes confined to `scripts/lib/react_template.tpl`. No data files modified (user's binding directive: "除了云南之外之前的travel plan全部保留不要动" still applies). No schema changes. No new files.

**Backward-compat**: viewing a trip with no drag interaction must still render PLAN_DATA correctly. The 5 fixes target editor-mode UX; published-only render path must be unchanged.

**Reference memory**: `/root/.claude/projects/-root-travel-planner/memory/project_next_session_drag_bugs.md` for the user's original 5-bug enumeration with line-number pointers.
