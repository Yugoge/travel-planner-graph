<!-- AUTO-GENERATED VIEW for orchestrator | source: docs/dev/specs/spec-20260505-221501.md | extracted: 2026-05-05T22:15:01Z -->

# orchestrator view of spec-20260505-221501

**Monolith**: docs/dev/specs/spec-20260505-221501.md

---

## Spec Header

<!-- EXPLICIT source:L1-L5 sha256:a6990e0b15ac8062a0c50cb1bf8dfbd482b4ecda226849124f44a9108dc22554 -->
# Spec: Travel-planner harness 升级 — Codex 共识版后验方案

**Pipeline**: travel-planner / harness-upgrade
**Session**: 20260505-221501
**Created**: 2026-05-05T22:15:01+00:00

---

## Role Mandate (from spec)

> User said: "将以上保存为 spec" — saves the consolidated post-mortem + Codex-signed action plan from session-end debate. Below is the verbatim final consensus.

> **Orchestrator's failures stemmed not from any specific bug but from acting before researching the project's existing commands/scripts/skills.**

Defense Layer 0 (highest-priority): **Mandatory discovery preamble before any task action**:
```
ls .claude/commands/
read .claude/commands/INDEX.md
read .claude/commands/<matching-keyword>.md frontmatter + body
grep <user-keyword> scripts/*.{py,sh}
```
Without this preamble, every subsequent hook is corrective; with it, most failures don't occur.

---

## Pipeline Workflow

#### Codex-signed Next-session 10-step actionable plan

1. **Freeze deploy until current validator passes** — block `generate-and-deploy.sh` if 27 schema failures unresolved
2. ~~轮换 Google Maps API key + scrub data 里所有 key=~~ **CANCELED per 5.1** — user accepts current state
3. **Fix current 27 schema failures**: meal `name_local: null`, meal-slot extra `image_url` fields, transportation `location_change: null`, cafe coords missing lat/lng, timeline overlap classifications
4. **Fix official image pipeline**:
   - `fetch-images-batch.py:390,416` paths from `.claude/skills/...` → `.claude/commands/scripts/...`
   - mcp_client cleanup: pick one canonical copy, delete duplicates, ensure `__enter__/__exit__`
   - data persistence layer permanently rejects stock URLs / `http://` (per 5.1, accepts `key=` for now)
5. **Fix renderer consistency**: pick one of two paths — either renderer honors `item.image_url` for ALL POI types, or `image_url` is NEVER written into data (cache is sole source). No coexistence.
6. **Write `scripts/verify-plan-integrity.py`** + invoke from `generate-and-deploy.sh` before HTML generation
7. **Update `.claude/commands/*.md` frontmatter** to declare `uses_scripts/dispatches/mutates_files`; auto-regenerate `INDEX.md`
8. **Add hard prompt-purity block** for agent dispatch positively authorizing `placeholder/TBD/stub/include later/to plan` (orchestrator's own seed words)
9. **Add per-agent owned-file rules** in `.claude/agents/*.md` + pretool-write hook enforcement; schema validation before subagent reports success
10. **Document the cycle contract** as a section in existing `docs/dev/cycle-<task-id>.md` artifact (NOT a separate parallel paper trail per Codex)

---

## Anti-Patterns

#### Codex's REJECTED items (do NOT implement)

- Original 30+ bespoke hook list (one hook per symptom) — Codex called this "papering over symptoms"
- HK-1 as semantic "purpose matching" — too brittle; replaced by HARN-1 mandatory preamble
- HK-8 timeline-POI crossref as hard-block — high false-positive risk; start as validator/report
- HK-11 hook-stack "verifies-promised" — too complex; replaced by single `verify-plan-integrity.py`
- CT-1/CT-2 separate parallel contract docs — duplicates dev/spec logs; embed in existing cycle artifacts
- OA-4 ratifying `@plugin/amap-maps` as alias — wrong; fix fetch script's broken path internally
- CMD-3 全文禁 `placeholder` — too broad; scope to positive authorization in dispatch templates only

**F. Diagnosis errors (orchestrator)**
- F1. used `poi-search.py` (real: `poi_search.py`) → declared skill broken
- F2. 3 consecutive QA cycles reported PASS with incomplete grep alternations
- F3. BA spec inventories under-counted (timeline travel_segment 11 vs actual 33; gaode_id 10 vs actual 6 misplaced)
- F4. orchestrator never `cat` of `.claude/commands/review.md` to learn the documented image-fetch substep before improvising
- F5. orchestrator's own dispatch prompts contained the seeds of every later "pollution"

---

## Hard Rules Relevant to Orchestrator

> 取消 google api key 轮换，就用现在

User explicitly **cancels** the P0 security recommendation. The 396 leaked `key=AIzaSy...` URLs in `data/*/images.json` are accepted as-is. Do NOT scrub. Do NOT rotate.

3. **Command discovery + canonical invocation contract**
   - First action of any orchestrator session: `ls .claude/commands/ + read INDEX.md + read selected command frontmatter`
   - Each `.claude/commands/*.md` declares YAML frontmatter: `uses_scripts: [...]`, `dispatches: [agent...]`, `mutates_files: [...]`
   - `INDEX.md` auto-regenerated from frontmatter (posttool-doc-sync hook)
   - Orchestrator must use canonical command lines from command body — NOT improvise (e.g., `/review` substep at L516 is the source of truth for `fetch-images-batch.py` invocation)

4. **Agent ownership + image-pipeline lock**
   - Each `.claude/agents/*.md` declares `owned_files: [regex]`
   - pretool-write hook: subagent can only write to owned files
   - **No agent (any type) may directly write `image_url` field**; images go through `scripts/fetch-images-batch.py` only
   - Data agents (meals/attractions/etc) cannot call Gaode/Google API directly

5. **Acceptance evidence standard**
   - subagent reports include verbatim grep command output for each AC (not summary "0 matches")
   - orchestrator must run the same grep before accepting subagent's PASS report
   - Single consolidated `verify-plan-integrity.py` is the authoritative check; subagents that report PASS without invoking it → orchestrator rejects

**Codex consensus is binding**: any cycle proposing to add bespoke hooks "for each symptom" must justify why it's not papering over symptoms. Default position: extend the single `verify-plan-integrity.py` instead of writing a new hook.

**User rejects token-rotation as part of accepting the live state**: per 5.1, do NOT propose key rotation in any later cycle. The current Google Maps API key in `data/*/images.json` is a known-accepted state. New defenses target prevention of new leaks (block `key=` in NEW writes via `verify-plan-integrity.py` warn-mode), not retroactive scrubbing.

---

## Agent Relevance Analysis

| Agent | Relevant | Reason |
|-------|----------|--------|
| ui-specialist | no | Spec contains zero visual design content; no CSS, color, motion, icons. |
| ba | yes | Spec defines acceptance criteria (5.1, 5.2), constraint enumeration, prior-attempt history. |
| dev | yes | Heavy implementation: write verify-plan-integrity.py, fix schemas, fix fetch-images-batch.py paths, renderer consistency, frontmatter, hook enforcement. |
| qa | yes | Explicit verification standards ("verbatim grep command output for each AC"); deploy-blocking verifier is QA gate. |
| pm | no | No priority rankings beyond Top 5 / 10-step (technical-execution ordering, not PM scope). |
| architect | yes | Section 8 calls out per-traveler dimension as "the recurring root architecture problem"; schemas/additionalProperties + command-discovery contract are architectural. |
| product-owner | no | No business stories or feature scope; user gave one explicit acceptance criterion. |
| user | no | No end-user scenarios; "user" here is the orchestrator developer. |
| cleaner | no | .bak files mentioned only as a known-deferred defect; no approved cleanup actions. |
| cleanliness-inspector | no | File organization not the focus. |
| git-edge-case-analyst | no | No git history concerns. |
| prompt-inspector | no | Prompt-purity hook mentioned but no inspection task requested. |
| rule-inspector | no | No folder-rule discovery requested. |
| style-inspector | no | No coding-standards audit requested. |
| test-executor | no | No explicit test execution. |
| test-validator | no | No test syntax/dependency validation. |

## Views Created

- ba.md
- dev.md
- qa.md
- architect.md
- orchestrator.md

## Monolith Sections

- Section 1: Before — Live state at spec creation time + DEFERRED defects
- Section 2: What Was Attempted — _Not yet populated._
- Section 3: What Was Changed — _Not yet populated._
- Section 4: Current State — _Not yet populated._
- Section 5: User's Acceptance Criterion — 5.1 (cancel key rotation) + 5.2 (Codex consensus, Bug accounting A-G, Top 5 controls, 10-step plan, REJECTED items, lesson, file paths)
- Section 6: Why Not Met — _Not yet populated._
- Section 7: What Must Be Done — _Not yet populated._
- Section 8: Attention Notes — per-traveler architecture problem, key-rotation rejection, Codex consensus is binding
