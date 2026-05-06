<!-- AUTO-GENERATED VIEW for orchestrator | source: docs/dev/specs/spec-20260506-092951.md | extracted: 2026-05-05T23:38:00Z -->

# orchestrator view of spec-20260506-092951

**Monolith**: docs/dev/specs/spec-20260506-092951.md

---

## Role Mandate (from spec)

> **Pipeline**: ba → dev → qa

> **Session**: spec-20260506-092951

---

## Pipeline Workflow

> **Pipeline**: ba → dev → qa

> <!-- WHO WRITES: PM (autonomous mode) or User (user-spec mode) or BA (if Section 1 empty and BA has context) -->
> <!-- WHAT: Screenshot path + text description of the current state BEFORE any fix attempt. -->
> <!-- This establishes the baseline so later cycles can compare. -->

> <!-- WHO WRITES: Dev (after each implementation attempt) -->
> <!-- WHAT: Per-cycle record of what approach was tried, what the rationale was, and why it failed (if it failed). -->
> <!-- This prevents the next cycle's Dev from repeating the same approach. -->

> <!-- WHO WRITES: Dev (after each implementation) -->
> <!-- WHAT: Exact file changes with line numbers and old->new values. -->

> <!-- WHO WRITES: QA (after each verification) -->
> <!-- WHAT: Actual measured values -- pixel dimensions, computed CSS, console output, screenshot paths. -->

> <!-- WHO WRITES: BA (on first analysis) -->
> <!-- WHAT: Verbatim quote from user's requirement or focus string. -->

> <!-- WHO WRITES: QA (when verdict is fail) -->
> <!-- WHAT: Specific gap between measured state (Section 4) and acceptance criterion (Section 5). -->

> <!-- WHO WRITES: QA (on fail) or PM-Retro -->
> <!-- WHAT: Prescriptive next step for this specific issue. Not generic advice -- a concrete action. -->

---

## Anti-Patterns

> **Behavioral pattern (informational, NOT a fix-target)**: Claude repeatedly preferred surface-level fixes (regex global replace, "0 fetched assumed cache hit", "user must hard-refresh") over root-cause investigation. User explicitly said behavioral fixes are out of scope — the goal is harness enforcement, not Claude's discipline.

> The following are NOT to be implemented in this spec, per user's directives:
> - Agent post-hoc output auditing (e.g. verifying RedNote URLs after agent claims "RedNote ONLY") — relying on script + prompt strictness instead.
> - HTML render visual validation automation (Playwright snapshots, viewport diff) — human inspection.
> - Sub-agent shared decision cache / context inheritance — over-engineering.
> - Attribution-bias diagnostics for Claude's behavior — accepted as a behavioral limitation.

---

## Hard Rules Relevant to Orchestrator

<!-- WHO WRITES: PM-Retro -->
<!-- WHAT: Issue-specific traps, warnings, and things to watch out for in the next cycle/session. -->
<!-- Example: "This file is imported by 12 components -- changes here cascade widely" -->


> User explicitly demanded:
> - 批量操作永久禁止 (batch operations permanently banned, not "guarded")
> - Auto-commit 不应该淹没 git log (auto-commit should not pollute HEAD)

> The user explicitly excluded:
> - Agent-output post-hoc auditing ("无所谓，只要脚本约束足够严格并且用户指定的方法足够严格就行")
> - HTML render visual validation ("人工验证，不需要你验证")
> - Behavioral attribution-bias diagnostics (acknowledged as Claude being stubborn — out of scope)
> - Over-engineering generally

> **Implementation order matters**:
> 1. **5.1 (schema hook) MUST land before 5.5 (data bug fixes)** — otherwise the data fixes themselves can re-introduce schema violations and there's no automated catch.
> 2. **5.4 (auto-commit→checkpoint ref) MUST land before any large dev cycle** — otherwise the implementation churn pollutes HEAD and rerunning becomes painful.
> 3. **5.3 (batch ban) MUST land before 5.5 (data bug fixes)** — the data fixes touch multiple days and the dev should be FORCED to do them per-day, not via batch regex.

> **`docs/incidents-2026-04-04.md`** describes prior production catastrophes — Lesson 13 ("NEVER let a single subagent handle multiple tasks") is directly relevant to 5.3 (batch ban). Cross-reference when implementing.

---

## Agent Relevance Analysis

| Agent | Relevant | Reason |
|-------|----------|--------|
| ui-specialist | no | Spec defines ba->dev->qa pipeline; no UI/visual design work. User explicitly excluded HTML render visual validation. |
| ba | yes | Named first in pipeline. Owes Section 5 acceptance criterion authoring + schema-tightening decisions. |
| dev | yes | Named second in pipeline. Implements 5.1-5.7, 5.9 hooks/scripts and 5.5 data bug fixes. |
| qa | yes | Named third in pipeline. Verifies all Section 5 acceptance criteria. |
| pm | no | Spec defines explicit pipeline; no PM stage named. |
| architect | no | Spec defines explicit pipeline; no architect stage named. |
| product-owner | no | Spec defines explicit pipeline; no product-owner stage named. |
| user | no | Spec defines explicit pipeline; user-facing scenario validation is excluded by 5.8. |
| cleaner | no | No cleanup execution scope defined. |
| cleanliness-inspector | no | No file-organization inspection scope defined. |
| git-edge-case-analyst | no | Auto-commit-to-refs is an implementation task for dev, not git-history forensics. |
| prompt-inspector | no | Out of scope per 5.8 (no agent post-hoc auditing). |
| rule-inspector | no | No folder rule discovery scope defined. |
| style-inspector | no | No coding-standards audit scope defined. |
| test-executor | no | QA owns verification per pipeline. |
| test-validator | no | QA owns verification per pipeline. |

## Views Created

- ba.md
- dev.md
- qa.md
- orchestrator.md

## Monolith Sections

- ## Section 1: Before
  **Trigger session**: 2026-05-05/06 `/review china/2026-04-12/` ran ~5 hours. User extremely frustrated with iterative failures. Two retrospectives produced (Claude self-audit) plus codex CLI second-opinion audit. This spec consolidates ALL findings.
- ## Section 2: What Was Attempted
  _Not yet populated._
- ## Section 3: What Was Changed
  _Not yet populated._
- ## Section 4: Current State
  _Not yet populated._
- ## Section 5: User's Acceptance Criterion
  > 将以上全部总结为一个spec，永久根本性地彻底修复
- ## Section 6: Why Not Met
  _Not yet populated._
- ## Section 7: What Must Be Done
  _Not yet populated._
- ## Section 8: Attention Notes
  **Implementation order matters**:
