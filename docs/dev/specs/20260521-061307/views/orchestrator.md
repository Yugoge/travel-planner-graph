<!-- AUTO-GENERATED VIEW for orchestrator | source: docs/dev/specs/spec-20260521-061307.md | extracted: 2026-05-21T08:58:00+00:00 -->

# orchestrator view of 20260521-061307

**Monolith**: docs/dev/specs/spec-20260521-061307.md

---

## Role Mandate (from spec)

> **Pipeline**: BA → dev → QA (single-cycle expected; UX polish, not new features)

---

## Pipeline Workflow

> **Pipeline**: BA → dev → QA (single-cycle expected; UX polish, not new features)

> **Cross-bug dependency**: Fix #4 MUST precede #5 (same fix). #1 and #2 are independent. #3 should be tested after #4/#5 because drag-out/replace flows share selection state.

---

## Anti-Patterns

> **From iteration-burnout memory (feedback_iteration_burnout.md)**: prior cycles 20260519-161933 + 20260520-200804 burned 3 close-debate rounds each on incomplete-fix iteration. For THIS cycle:
> - BA must specify "grep entire file for the symptom pattern" not "fix L<N>". Same-class issues across multiple sites must enumerate ALL sites, not a subset.
> - Dev should run the verification grep that QA + close-debate will run, before declaring complete.
> - QA should re-grep before signing off.
> - Limit close-debate cycles to ≤2 — force-close + document as out-of-scope if codex catches a 3rd round of same-class issue.

---

## Hard Rules Relevant to Orchestrator

> **File scope**: changes confined to `scripts/lib/react_template.tpl`. No data files modified (user's binding directive: "除了云南之外之前的travel plan全部保留不要动" still applies). No schema changes. No new files.

> **Backward-compat**: viewing a trip with no drag interaction must still render PLAN_DATA correctly. The 5 fixes target editor-mode UX; published-only render path must be unchanged.

---

## Agent Relevance Analysis

| Agent | Relevant | Reason |
|-------|----------|--------|
| ui-specialist | no | Bug #1 is style fragmentation but spec provides explicit code recipe (extract candidateCardStyle() helper); mechanical refactor, no design judgment needed. Pipeline declares BA → dev → QA only. |
| ba | yes | Pipeline names BA; Section 5 acceptance criterion present; Section 8 has BA directive. |
| dev | yes | Pipeline names dev; Section 1 codex table provides file:line:fix-scope; Section 8 has dev directive. |
| qa | yes | Pipeline names QA; Section 8 has QA directive; pixel-layer verification needed. |
| pm | no | Not in declared pipeline; no spec content addresses PM. |
| architect | no | No architecture/structure content; single-file 45-60 line UX polish. |
| product-owner | no | Not in declared pipeline; UX polish on existing feature, no scope/business decision. |
| user | no | User acceptance criterion captured in Section 5; no review-gate content. |
| cleaner | no | No cleanup actions in spec. |
| cleanliness-inspector | no | No file-organization content. |
| git-edge-case-analyst | no | No git-history content. |
| prompt-inspector | no | Not in declared pipeline. |
| rule-inspector | no | No folder-rule discovery content. |
| style-inspector | no | No coding-standard audit content. |
| test-executor | no | Pipeline declares QA for verification (Playwright on live service); no explicit test-execution stage. |
| test-validator | no | No test files to validate. |

## Views Created

- ba.md (45 lines)
- dev.md (35 lines)
- qa.md (32 lines)
- orchestrator.md (this file)

## Monolith Sections

- Section 1: Before — User-provided screenshot, baseline state, root-cause table
- Section 2: What Was Attempted — Not yet populated
- Section 3: What Was Changed — Not yet populated
- Section 4: Current State — Not yet populated
- Section 5: User's Acceptance Criterion — Chinese verbatim user need
- Section 6: Why Not Met — Not yet populated
- Section 7: What Must Be Done — Not yet populated
- Section 8: Attention Notes — Iteration-burnout warnings, file scope, backward-compat
