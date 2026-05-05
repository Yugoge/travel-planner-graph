<!-- AUTO-GENERATED VIEW for dev | source: docs/dev/specs/spec-20260505-221501.md | extracted: 2026-05-05T22:15:01Z -->

# dev view of spec-20260505-221501

**Monolith**: docs/dev/specs/spec-20260505-221501.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> User explicitly **cancels** the P0 security recommendation. The 396 leaked `key=AIzaSy...` URLs in `data/*/images.json` are accepted as-is. Do NOT scrub. Do NOT rotate.

---

## Section 1: Before — Known but DEFERRED defects

- 27 schema validation failures + 13 warnings on current trip
- 396 occurrences of `key=AIzaSy...` Google Maps API key embedded in `data/*/images.json` URLs
- transportation/accommodation schemas still `additionalProperties: true`
- prompt-purity hook is warning-only (not blocking)
- fetch-images-batch.py:390,416 reference `.claude/skills/...` (real path: `.claude/commands/scripts/...`)
- renderer ignores `item.image_url` for some POI types
- Untracked `.bak` files remain in workspace
- `_inject_intra_routes` band-aid still in renderer (parallel data path)

---

## Section 5.1: User's Acceptance Criterion (binding constraint on any image/data work)

> 取消 google api key 轮换，就用现在

User explicitly **cancels** the P0 security recommendation. The 396 leaked `key=AIzaSy...` URLs in `data/*/images.json` are accepted as-is. Do NOT scrub. Do NOT rotate.

---

<!-- EXPLICIT source:L126-L126 sha256:placeholder -->
#### Codex-signed Top 5 controls (catches ~80% of failure modes)

1. **Single deploy-blocking verifier**
   - File: `scripts/verify-plan-integrity.py`
   - Called by: `scripts/generate-and-deploy.sh` BEFORE HTML generation
   - Checks (6-in-1):
     - Schema validation against `schemas/*.schema.json` (additionalProperties:false strict)
     - Forbidden-token grep on data + rendered HTML: `to plan|placeholder|TBD|本期不渲染|out of scope|superseded|STRUCTURAL CHANGE|OLD timeline|next session|next cycle|自理（|不渲染`
     - Stock-image-URL grep: `images.unsplash.com|picsum.photos|placeholder.com|via.placeholder.com|loremflickr|placekitten`
     - HTTP-protocol grep: `"image_url"\s*:\s*"http://`
     - API-key leak grep: `key=AIzaSy[A-Za-z0-9_-]{30,}` (NOTE: per 5.1, currently passes through — flag but don't block; user-accepted)
     - HTML-rendered scan after generate
   - Verdict: any FAIL → abort deploy, print exact line + remediation hint

2. **Schema-aware writes + 严格 schema**
   - All `schemas/*.schema.json` permanently `additionalProperties: false` (currently transportation/accommodation are `true` — must fix)
   - `lib/json_io.py` validates against schema before save; any violation → reject
   - Stage A: fix current data to pass validation (27 failures)
   - Stage B: tighten schemas globally

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

---

## Codex-signed Next-session 10-step actionable plan

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

## File paths referenced

- BA spec template: `~/.claude/templates/overnight-spec.md`
- Renderer: `/root/travel-planner/scripts/generate-html-interactive.py`
- Sync: `/root/travel-planner/scripts/sync-agent-data.py`
- Save: `/root/travel-planner/scripts/lib/json_io.py`
- Validator: `/root/travel-planner/scripts/validate-agent-outputs.py`
- Fetch images: `/root/travel-planner/scripts/fetch-images-batch.py`
- Working Gaode skill: `/root/travel-planner/.claude/commands/scripts/gaode-maps/scripts/poi_search.py`
- Image-fetch substep doc: `/root/travel-planner/.claude/commands/review.md` line 510-540
- Schemas: `/root/travel-planner/schemas/*.schema.json`
- Existing prompt-purity hook (warning-only): `~/.claude/hooks/pretool-orchestrator-prompt-purity.py:57-60,437-461`
- Codex audit transcript: `/var/tmp/codex-outputs/codex-final-*.txt`

---

## Image-system multi-layer failures (avoid regressing)

- E1. agent directly called Gaode/Google API bypassing `scripts/fetch-images-batch.py`
- E2. wrong fetch script invocation (orchestrator improvised parameters vs review.md L516 canonical)
- E3. scripts/lib/mcp_client.py was missing from import path
- E4. mcp_client.py copy lacked `__enter__/__exit__`
- E5. orchestrator INCORRECTLY declared "fetch subsystem broken" — review.md works
- E6. config/fallback-images.json default contained unsplash stock URLs
- E7. images.json cache had 21 unsplash-poisoned entries
- E8. 6 image_urls used `http://` (Mixed Content blocked)
- E9. renderer ignored `acc.image_url` field
- E10. renderer line 603 NameError: `meal_name` undefined

---

## The single most important lesson

> **Orchestrator's failures stemmed not from any specific bug but from acting before researching the project's existing commands/scripts/skills.**

Defense Layer 0 (highest-priority): **Mandatory discovery preamble before any task action**:
```
ls .claude/commands/
read .claude/commands/INDEX.md
read .claude/commands/<matching-keyword>.md frontmatter + body
grep <user-keyword> scripts/*.{py,sh}
```
Without this preamble, every subsequent hook is corrective; with it, most failures don't occur.
