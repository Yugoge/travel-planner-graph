<!-- AUTO-GENERATED VIEW for qa | source: docs/dev/specs/spec-20260521-061307.md | extracted: 2026-05-21T08:58:00+00:00 -->

# qa view of 20260521-061307

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

> - QA should re-grep before signing off.

---

## Section 1: Before

### Cycle 1

**User-provided screenshot**: `/tmp/happy-attachments/5ba5a71f-5e1e-4997-a4bb-d7ea5d5afc5e-image.png` (Day "Jun 20 (Sat) – Kunming" view at `travel.life-ai.app/trip/beijing-lijiang-dali-20260418-100846`).

**Known gaps as of baseline** (user-observed, basis for this spec):
1. Visual style inconsistent across Kanban / Candidates / DayColumn panels (same data renders differently in different panels)
2. Cards dragged INTO a slot lose their image; right-side Candidates entries also missing images
3. After drag-replacing a slot's selection, the previously-selected option does NOT return to the Candidates panel (asymmetric swap)
4. Left-side DayColumn cards are not draggable (`draggable={isSelected}` gate in `scripts/lib/react_template.tpl` never enables DayColumn cards)
5. Drop-to-deselect does not work: cards in slots cannot be dragged BACK to the Candidates panel to unselect

**Cross-bug dependency**: Fix #4 MUST precede #5 (same fix). #1 and #2 are independent. #3 should be tested after #4/#5 because drag-out/replace flows share selection state.

**Codex live-DOM verification**: codex fetched the served page via Python HTTP GET + Playwright rendering and confirmed: `#candidates-groups` exists, `.card-candidate` exists, left/main `[data-slot-card]` cards exist, accommodation primary card has `data-slot-id="accommodation"` + `data-option-id="accommodation-1-2"` but NO `draggable` attribute. The bug is observable in production at travel.life-ai.app.

---

## Section 4: Current State

<!-- WHO WRITES: QA (after each verification) -->
<!-- WHAT: Actual measured values -- pixel dimensions, computed CSS, console output, screenshot paths. -->
<!-- This gives the next cycle's Dev concrete data to work with instead of vague "it failed". -->

### Cycle 1

_Not yet populated._

---

## Section 5: User's Acceptance Criterion

下一个session修复风格完全不统一，拖动进去的没有图片，并且拖动进去之后原来的酒店没有了，没有重新出现在候选栏，并且左侧区域没法拖动，只能拖进去没法拖出去

下一个session全部要修复的

---

## Section 6: Why Not Met

<!-- WHO WRITES: QA (when verdict is fail) -->
<!-- WHAT: Specific gap between measured state (Section 4) and acceptance criterion (Section 5). -->
<!-- Must include evidence: actual value vs expected value. -->

### Cycle 1

_Not yet populated._

---

## Section 7: What Must Be Done

<!-- WHO WRITES: QA (on fail) or PM-Retro -->
<!-- WHAT: Prescriptive next step for this specific issue. Not generic advice -- a concrete action. -->
<!-- Example: "Increase padding from 8px to 16px in Chat.tsx:42" not "fix the padding" -->

### Cycle 1

_Not yet populated._

---

## Section 8: Attention Notes

- QA should re-grep before signing off.
- Limit close-debate cycles to ≤2 — force-close + document as out-of-scope if codex catches a 3rd round of same-class issue.

**Backward-compat**: viewing a trip with no drag interaction must still render PLAN_DATA correctly. The 5 fixes target editor-mode UX; published-only render path must be unchanged.
