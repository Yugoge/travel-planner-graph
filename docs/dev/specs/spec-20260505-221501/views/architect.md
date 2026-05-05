<!-- AUTO-GENERATED VIEW for architect | source: docs/dev/specs/spec-20260505-221501.md | extracted: 2026-05-05T22:15:01Z -->

# architect view of spec-20260505-221501

**Monolith**: docs/dev/specs/spec-20260505-221501.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> User said: "将以上保存为 spec" — saves the consolidated post-mortem + Codex-signed action plan from session-end debate. Below is the verbatim final consensus.

---

## Section 1: Before — structural defects

**Known but DEFERRED defects (verified by Codex audit 2026-05-05 21:55Z)**:
- 27 schema validation failures + 13 warnings on current trip
- 396 occurrences of `key=AIzaSy...` Google Maps API key embedded in `data/*/images.json` URLs
- transportation/accommodation schemas still `additionalProperties: true`
- prompt-purity hook is warning-only (not blocking)
- fetch-images-batch.py:390,416 reference `.claude/skills/...` (real path: `.claude/commands/scripts/...`)
- renderer ignores `item.image_url` for some POI types
- Untracked `.bak` files remain in workspace
- `_inject_intra_routes` band-aid still in renderer (parallel data path)

---

## Codex-signed Top 5 controls — architectural changes

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

---

## Codex's REJECTED items (do NOT implement)

- Original 30+ bespoke hook list (one hook per symptom) — Codex called this "papering over symptoms"
- HK-1 as semantic "purpose matching" — too brittle; replaced by HARN-1 mandatory preamble
- HK-8 timeline-POI crossref as hard-block — high false-positive risk; start as validator/report
- HK-11 hook-stack "verifies-promised" — too complex; replaced by single `verify-plan-integrity.py`
- CT-1/CT-2 separate parallel contract docs — duplicates dev/spec logs; embed in existing cycle artifacts
- OA-4 ratifying `@plugin/amap-maps` as alias — wrong; fix fetch script's broken path internally
- CMD-3 全文禁 `placeholder` — too broad; scope to positive authorization in dispatch templates only

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

## Section 8: Attention Notes — root architectural problems

**Per-traveler dimension is the recurring root architecture problem**: schema has no per-traveler dimension, so split-day (Mathilde + Jade in different cities/transports) keeps producing fabricated bolt-on fields (`accommodation_jade`, `passengers_jade`, `split_day`). Either formally extend schemas (add `traveler` enum to accommodation_item, ensure `passengers: []` array on every transport, add `split_day:bool` + `traveler:enum` documented at day_entry level), OR drop second-traveler rendering entirely (single-traveler view). Half-extension is the disease.

**User rejects token-rotation as part of accepting the live state**: per 5.1, do NOT propose key rotation in any later cycle. The current Google Maps API key in `data/*/images.json` is a known-accepted state. New defenses target prevention of new leaks (block `key=` in NEW writes via `verify-plan-integrity.py` warn-mode), not retroactive scrubbing.

**Codex consensus is binding**: any cycle proposing to add bespoke hooks "for each symptom" must justify why it's not papering over symptoms. Default position: extend the single `verify-plan-integrity.py` instead of writing a new hook.
