<!-- AUTO-GENERATED VIEW for ba | source: docs/dev/specs/spec-20260506-092951.md | extracted: 2026-05-06T00:00:00Z -->

# ba view of spec-20260506-092951

**Monolith**: docs/dev/specs/spec-20260506-092951.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> **Pipeline**: ba → dev → qa

---

# Spec: Travel-planner harness root-cause hardening — block schema/semantic violations at write-time, fix accumulated data bugs, kill HEAD pollution

**Pipeline**: ba → dev → qa
**Session**: spec-20260506-092951
**Created**: 2026-05-06T09:29:51+00:00

## Section 5: User's Acceptance Criterion

<!-- WHO WRITES: BA (on first analysis) -->
<!-- WHAT: Verbatim quote from user's requirement or focus string. -->
<!-- This is the single source of truth for what "done" means. Do not paraphrase. -->

> 将以上全部总结为一个spec，永久根本性地彻底修复

User's intent (consolidated from this conversation): take the systemic findings (Claude's two retrospectives + codex's audit) and convert them into a permanent root-cause fix — both the harness mechanisms that allowed the failures AND the residual data bugs codex flagged. The user explicitly excluded:
- Agent-output post-hoc auditing ("无所谓，只要脚本约束足够严格并且用户指定的方法足够严格就行")
- HTML render visual validation ("人工验证，不需要你验证")
- Behavioral attribution-bias diagnostics (acknowledged as Claude being stubborn — out of scope)
- Over-engineering generally

User explicitly demanded:
- 批量操作永久禁止 (batch operations permanently banned, not "guarded")
- Auto-commit 不应该淹没 git log (auto-commit should not pollute HEAD)

### 5.5: Eight residual data bugs in `data/china-20260412-092624/` must be fixed

**Goal**: All eight active bugs listed in Section 1 are resolved.

### 5.6: Delete the unauthorized `plan_label` field from all data files

**User decision (verbatim from accumulation loop)**:
> plan_label 直接删除，这不是我们 schema 中的啊！我让你给 plan abc 仅仅是字面意义，同时 BC 加上 optional，并没有说要加入一个新的标准

**Resolution (no longer a choice — user has decided)**:
- `plan_label` is a non-standard field Claude unilaterally introduced. DELETE it from every data file: `attractions.json`, `meals.json`, `entertainment.json`, `shopping.json`, `transportation.json`, `timeline.json`, `cafe.json`, `accommodation.json`, `budget.json` (search-and-strip across the entire trip data tree).
- Plan A/B/C remain only as **literal conceptual labels** expressed via:
  - `optional: false` for Plan A (primary) items
  - `optional: true` for Plan B/C (alternative) items
  - Optional human-readable prefix in `notes_base` like `[PLAN A]` / `[PLAN B - ALTERNATIVE]` / `[PLAN C - ALTERNATIVE]` (free-text, NOT a schema field)
- HTML renderer continues using only `optional`. No visual distinction between Plan B and Plan C — both render as `optional` (dashed border, "Optional" badge).
- `_isAlternative` is dead code in `scripts/generate-html-interactive.py:3043-3053` (read but never assigned). Delete the dead branches OR leave as-is (orchestrator-internal cleanup, low priority).
- DO NOT add `plan_label` to any schema. DO NOT promote it to standard. Treat any future agent attempt to write `plan_label` as a schema violation under 5.1's strict-write enforcement.

### 5.9: User-language vs machine-schema boundary — translation is mandatory, ad-hoc field introduction is forbidden

**User decision (verbatim from accumulation loop)**:
> 是的，甚至 Plan A/B/C 都不是标准术语，只是用户语言，你只能用当前的 schema 用 save 脚本翻译成机器语言

**Principle**: Claude (orchestrator + sub-agents) MUST treat all user phrasing as **conversational / colloquial input** and translate it into the **existing machine schema**. Ad-hoc field introduction is forbidden, even via fields that the schema technically permits via `additionalProperties:true`.

**Translation rules** (illustrative, not exhaustive):
- "Plan A" / "primary" / "主行程" / "套餐 A" → `optional: false`
- "Plan B" / "Plan C" / "alternative" / "备选" / "可选" → `optional: true`
- "must do" / "non-negotiable" → `optional: false`
- "skip if tired" / "nice-to-have" → `optional: true`
- **No** `plan_label`, `is_alternative`, `_isAlternative`, `tier`, `priority`, `category_label`, `bundle_id`, or any similar Claude-invented attribute is permitted in any data file.
- The string `[PLAN A]` / `[PLAN B - ALTERNATIVE]` / `[PLAN C - ALTERNATIVE]` etc. in `notes_base` is **free-text annotation**, NOT a structured field. It is allowed only as human-readable prose, must not be parsed by any code, and must not become a de-facto enum.

**The single write path is `scripts/save.py`** (post-extension per 5.3 with `--day N`). save.py is responsible for:
- Accepting structured input that maps onto existing schema fields only
- Rejecting input fields that aren't in the schema
- Translating common user-language synonyms (e.g., `"primary": true` → `optional: false` if writer used user phrasing)

**Out-of-scope clarification**: this requirement does NOT mean Claude or agents cannot USE the words "Plan A/B/C" in user-facing summaries, prompts to sub-agents, or `notes_base` prose. It only means those words cannot become MACHINE-READABLE structured fields. The boundary is: **anything machine-parsed must already be in the schema; user language stays in prose**.

### 5.8: Out-of-scope (explicitly excluded by user)

The following are NOT to be implemented in this spec, per user's directives:
- Agent post-hoc output auditing (e.g. verifying RedNote URLs after agent claims "RedNote ONLY") — relying on script + prompt strictness instead.
- HTML render visual validation automation (Playwright snapshots, viewport diff) — human inspection.
- Sub-agent shared decision cache / context inheritance — over-engineering.
- Attribution-bias diagnostics for Claude's behavior — accepted as a behavioral limitation.

**Schema tightening risk**: making `transportation.intra_city_routes` strict will reject existing data. Migration step required: either widen schema to accept current shape, or normalize current data first. BA must decide and document.

**`scripts/save.py` does NOT have `--day` option currently** — Claude's previous proposal was based on a non-existent API. Either extend `save.py` or build a new structured editor as part of 5.3. Do not pretend the API exists.

**`plan-validate.py` does NOT have `--strict-schema` flag** — the strict validator is a separate script `verify-plan-integrity.py` only invoked at deploy. 5.1 must clarify whether to extend `plan-validate.py` with strict mode, or wire the existing `verify-plan-integrity.py` into PreToolUse, or build a new write-time validator. BA decides.

**Plan B/C visual distinction is a UI design decision, not a tech decision** — surface to the user before implementing. Defaulting to "renderer reads plan_label" is what Claude did unilaterally last time, and the result was schema violations + invisible Plan-C.
