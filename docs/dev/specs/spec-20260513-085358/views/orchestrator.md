<!-- AUTO-GENERATED VIEW for orchestrator | source: docs/dev/specs/spec-20260513-085358.md | extracted: 2026-05-13T09:00:00Z -->

# orchestrator view of spec-20260513-085358

**Monolith**: docs/dev/specs/spec-20260513-085358.md

---

## Role Mandate (from spec)

<!-- WHO WRITES: PM (autonomous mode) or User (user-spec mode) or BA (if Section 1 empty and BA has context) -->
<!-- WHAT: Screenshot path + text description of the current state BEFORE any fix attempt. -->
<!-- This establishes the baseline so later cycles can compare. -->

<!-- WHO WRITES: PM-Retro -->
<!-- WHAT: Issue-specific traps, warnings, and things to watch out for in the next cycle/session. -->
<!-- Example: "This file is imported by 12 components -- changes here cascade widely" -->

---

## Pipeline Workflow

---

## Spec Header

# Spec: M2 prerequisite — systematic bugs surfaced during 2026-05-13 china-20260412-092624 review

**Pipeline**: travel-planner
**Session**: spec-20260513-085358
**Created**: 2026-05-13T08:53:58Z

---

## Acceptance Criterion (verbatim)

User directive (verbatim): "📝 把这些bug记成新spec 暨M2前置spec"

Context: the user is requesting that the systematic bugs and improvement opportunities surfaced during the 2026-05-13 `/review china/2026-04-12/` session be recorded as a new spec, intended as a prerequisite to the deferred M2-M5 milestones of spec-20260508-221237 (drag-and-drop web UI overhaul). The bug enumeration the user is asking me to record follows verbatim from my immediately-prior message to the user:

---

## Agent Relevance Analysis

| Agent | Relevant | Reason |
|-------|----------|--------|
| ui-specialist | no | No visual/UX design work; spec is about renderer logic, schema, hooks |
| ba | yes | Section 5 acceptance criterion and Section 1 baseline require decomposition |
| dev | yes | All bugs are concrete code/script/hook fixes with file:line anchors |
| qa | yes | 13-item bug enumeration is verification scope; needs measurement against acceptance |
| pm | no | Priorities/timeline not in scope; spec records bugs, not scheduling |
| architect | yes | Entity-ID system, schema unification, script-split are architectural |
| product-owner | no | No business-requirements-clarification needed |
| user | no | No end-user scenario translation required |
| cleaner | no | No cleanup-execution scope |
| cleanliness-inspector | no | No file-organization inspection in scope |
| git-edge-case-analyst | no | No git-history concerns |
| prompt-inspector | no | No agent-prompt audit in scope |
| rule-inspector | no | No folder-rule discovery in scope |
| style-inspector | no | No coding-standard audit in scope (though quality-gate caps are referenced) |
| test-executor | no | No explicit test-suite execution mandated |
| test-validator | no | No test-validation scope |

## Views Created

- ba.md
- dev.md
- qa.md
- architect.md
- orchestrator.md

## Monolith Sections

## Section 1: Before
### Cycle 1

## Section 2: What Was Attempted
### Cycle 1

## Section 3: What Was Changed
### Cycle 1

## Section 4: Current State
### Cycle 1

## Section 5: User's Acceptance Criterion
User directive (verbatim): "📝 把这些bug记成新spec 暨M2前置spec"

## Section 6: Why Not Met
### Cycle 1

## Section 7: What Must Be Done
### Cycle 1

## Section 8: Attention Notes
_Not yet populated._
