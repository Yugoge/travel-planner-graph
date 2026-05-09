<!-- AUTO-GENERATED VIEW for orchestrator | source: docs/dev/specs/spec-20260508-221237.md | extracted: 2026-05-09T00:00:00Z -->

# orchestrator view of spec-20260508-221237

**Monolith**: docs/dev/specs/spec-20260508-221237.md

---

## Spec header (verbatim)

# Spec: gaode-maps harness ban (non-geo agents) + options-first day planning flow

**Pipeline**: travel-planner
**Session**: spec-20260508-221237
**Created**: 2026-05-08T22:12:37Z

---

## Empty section markers (cycle 1 not yet populated)

## Section 2: What Was Attempted

_Not yet populated._

## Section 3: What Was Changed

_Not yet populated._

## Section 4: Current State

_Not yet populated._

## Section 6: Why Not Met

_Not yet populated._

## Section 7: What Must Be Done

_Not yet populated._

## Section 8: Attention Notes

_Not yet populated._

---

## Role Mandate (from spec)

> 5. The two geo agents (`timeline`, `transportation`) are the ONLY agents permitted to call gaode-maps (cross-reference §5.1).

> Default mode (without `--auto`) remains the user-gated flow from §5.2.

---

## Pipeline Workflow

4. **After user approval, timeline + transportation are invoked in sequence:**
   - `timeline` agent: builds the day's chronological timeline AND designs **intra-city** (市内) transit between the user-chosen items.
   - `transportation` agent: designs **inter-city** (市际) transport segments (HSR, flights, long-distance ground) on days that change cities.

- A documented day-planning state machine: `draft-options → user-review → user-selected → timeline → transportation → finalized`. State transitions are explicit; downstream stages refuse to run on a day still in `draft-options` or `user-review`.

Mismatch with target flow:
  - Current order = **content → transportation → timeline → user-review** (review is post-hoc).
  - Target order (§5.2) = **content (multi-option) → user-review (selection) → timeline (intra-city) → transportation (inter-city)**.
  - Current `transportation` runs in parallel with content agents; target makes it strictly downstream of user selection.
  - Current `timeline` runs before user approval; target makes user approval a hard gate before timeline.
  - `alternatives` field exists for content agents but is treated as optional decoration; target makes multi-option **mandatory** and the basis of the user-selection UI.

---

## Anti-Patterns

- **§5.6 backend block "all-pairs intra-city precompute"** (the bullets that say `timeline` MUST compute the N×N matrix and persist `intra-city-matrix.json`) — **SUPERSEDED by §5.9**. Do NOT implement matrix precompute. Do NOT produce `intra-city-matrix.json`. Do NOT write tests against either.

Implementer rule: when §5.6 / §5.8 conflict with §5.9, **§5.9 wins**.

- §5.3 bullet "Backwards compatibility with existing trips: `data/china-20260412-092624/` and similar in-flight trip data must continue to load …" — **REVOKED**. Old data is out of scope; no shim, no migration script, no auto-load.

---

## Hard Rules Relevant to Orchestrator

- **Default-deny posture**: both the gaode-maps skill ban (§5.1) and the timeline/transportation gate (§5.2) follow default-deny; new agents added later inherit the ban automatically and inherit the gate automatically (no opt-out without explicit allowlist edit + spec amendment).
- **No emoji in code/comments/commit messages** (project-wide rule, restated for the implementing dev).
- **Auto-commit safety**: changes flow through the `refs/checkpoints/<branch>` mechanism per `docs/checkpoint-mechanism.md`; HEAD master never advances on PostToolUse.

3. **User selection is a hard gate.** No downstream timing/routing work runs until the user explicitly picks one option per slot (or accepts a default).

**Allowlist (only these two agents may call gaode-maps skills)**: `timeline`, `transportation`.

**Out-of-scope agents (must be banned)**: `meals`, `attractions`, `accommodation`, `cafe`, `entertainment`, `shopping`, `ba`, `qa`, `dev`, `pm`, `product-owner`, `ui-specialist`, `budget`, `user`, plus any other agent not on the allowlist (default-deny).

---

## Agent Relevance Analysis

| Agent | Relevant | Reason |
|-------|----------|--------|
| ui-specialist | yes | §5.6 candidates panel + drag-drop + §5.10D budget panel + §5.11 PDF/iCal triggers + §5.13D mobile and validation UI |
| ba | yes | Section 1 baseline + §5.1/§5.2/§5.7/§5.8/§5.12/§5.13 requirements decomposition and supersession resolution |
| dev | yes | Implementation scope: harness hooks (§5.1/§5.4/§5.13C), state machine (§5.2), --auto (§5.5), schema (§5.7/§5.8), lazy routing endpoint (§5.9), budget endpoint (§5.10), exporters (§5.11), persistence/API (§5.13D) |
| qa | yes | Acceptance evidence in §5.1, §5.2, §5.6, §5.8, §5.9, §5.10, §5.11, §5.13C, §5.13D |
| pm | no | Spec is a feature spec — no priority/scope/timeline/mandate triage content |
| architect | no | No explicit dependency/scalability/infrastructure analysis section beyond what dev needs |
| product-owner | no | No explicit business-requirements/user-stories block separate from BA scope |
| user | no | User is the spec author here; no end-user review-gate scenarios beyond what BA captures |
| cleaner | no | No cleanup/archive scope |
| cleanliness-inspector | no | No file-organization scope |
| git-edge-case-analyst | no | No git history concerns |
| prompt-inspector | no | No prompt-audit scope |
| rule-inspector | no | No folder-rule discovery scope |
| style-inspector | no | No style-audit scope |
| test-executor | no | No explicit pre-existing test execution scope |
| test-validator | no | No test-syntax/dependency validation scope |

## Views Created

- ba.md
- dev.md
- qa.md
- ui-specialist.md
- orchestrator.md

## Monolith Sections

- `## Section 1: Before` — current gaode access surface + current planning flow baseline
- `## Section 2: What Was Attempted` — Cycle 1 not yet populated
- `## Section 3: What Was Changed` — Cycle 1 not yet populated
- `## Section 4: Current State` — Cycle 1 not yet populated
- `## Section 5: User's Acceptance Criterion` — §5.1 through §5.13 (the bulk of the spec)
- `## Section 6: Why Not Met` — Cycle 1 not yet populated
- `## Section 7: What Must Be Done` — Cycle 1 not yet populated
- `## Section 8: Attention Notes` — Not yet populated
