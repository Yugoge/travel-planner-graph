<!-- AUTO-GENERATED VIEW for ba | source: docs/dev/specs/spec-20260521-061307.md | extracted: 2026-05-21T08:58:00+00:00 -->

# ba view of 20260521-061307

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

> - BA must specify "grep entire file for the symptom pattern" not "fix L<N>". Same-class issues across multiple sites must enumerate ALL sites, not a subset.

---

## Section 1: Before

<!-- WHO WRITES: PM (autonomous mode) or User (user-spec mode) or BA (if Section 1 empty and BA has context) -->
<!-- WHAT: Screenshot path + text description of the current state BEFORE any fix attempt. -->
<!-- This establishes the baseline so later cycles can compare. -->

### Cycle 1

**User-provided screenshot**: `/tmp/happy-attachments/5ba5a71f-5e1e-4997-a4bb-d7ea5d5afc5e-image.png` (Day "Jun 20 (Sat) – Kunming" view at `travel.life-ai.app/trip/beijing-lijiang-dali-20260418-100846`).

**Baseline state** (after task `20260520-200804` shipped at commit `14f72e30`):
- Unified viewer/editor live at `travel.life-ai.app`
- Drag-and-drop event pipeline functional (events fire, payload transfers, POST /api/save 200)
- Gated/incompatible-slot drag-reject visual feedback works (red flash, fixed in 20260520-200804)
- Cross-meal Timeline survival fixed (entry._slotId tagging)
- Sidebar ✓ tracks `editor_selections` (R2 of 20260519-161933)

**Known gaps as of baseline** (user-observed, basis for this spec):
1. Visual style inconsistent across Kanban / Candidates / DayColumn panels (same data renders differently in different panels)
2. Cards dragged INTO a slot lose their image; right-side Candidates entries also missing images
3. After drag-replacing a slot's selection, the previously-selected option does NOT return to the Candidates panel (asymmetric swap)
4. Left-side DayColumn cards are not draggable (`draggable={isSelected}` gate in `scripts/lib/react_template.tpl` never enables DayColumn cards)
5. Drop-to-deselect does not work: cards in slots cannot be dragged BACK to the Candidates panel to unselect

Affected file (primary): `/root/travel-planner/scripts/lib/react_template.tpl` (single file, ~45-60 line changes).

**Cross-bug dependency**: Fix #4 MUST precede #5 (same fix). #1 and #2 are independent. #3 should be tested after #4/#5 because drag-out/replace flows share selection state.

---

## Section 5: User's Acceptance Criterion

<!-- WHO WRITES: BA (on first analysis) -->
<!-- WHAT: Verbatim quote from user's requirement or focus string. -->
<!-- This is the single source of truth for what "done" means. Do not paraphrase. -->

下一个session修复风格完全不统一，拖动进去的没有图片，并且拖动进去之后原来的酒店没有了，没有重新出现在候选栏，并且左侧区域没法拖动，只能拖进去没法拖出去

下一个session全部要修复的

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
