<!-- AUTO-GENERATED VIEW for qa | source: docs/dev/specs/spec-20260505-221501.md | extracted: 2026-05-05T22:15:01Z -->

# qa view of spec-20260505-221501

**Monolith**: docs/dev/specs/spec-20260505-221501.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> subagent reports include verbatim grep command output for each AC (not summary "0 matches")

> orchestrator must run the same grep before accepting subagent's PASS report

> Single consolidated `verify-plan-integrity.py` is the authoritative check; subagents that report PASS without invoking it → orchestrator rejects

---

## Section 1: Before — Live state at spec creation time

**Live state at spec creation time** (`https://travel.life-ai.app/china/2026-04-12/`):
- 15 days of Mathilde + Jade China itinerary
- 0 unsplash stock photos in deployed HTML
- 0 `http://` image src
- 0 `placeholder/TBD/to plan` strings
- 0 `珍宝` ghosts (cycle 20260505-123425's 11 residue resolved in iter 3)
- Real Gaode photos for Day 5 (白家肥肠粉, 院8里少城) + Days 6-15 via official `python scripts/fetch-images-batch.py X 0 999 --day N --force`

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

## Section 5.1: User's Acceptance Criterion — API key

> 取消 google api key 轮换，就用现在

User explicitly **cancels** the P0 security recommendation. The 396 leaked `key=AIzaSy...` URLs in `data/*/images.json` are accepted as-is. Do NOT scrub. Do NOT rotate.

---

## Section 5.2: 保留全 session 后验 + Codex 共识方案

User said: "将以上保存为 spec" — saves the consolidated post-mortem + Codex-signed action plan from session-end debate. Below is the verbatim final consensus.

---

## Bug accounting (this session, full) — what QA must catch in future cycles

**A. Data pollution (orchestrator-induced) — 12 categories**
- A1. plan-skeleton.json Day 4/9/10/11 location overwritten to wrong city
- A2. transportation.json Day 4 fabricated DAY-level `location_short` + `location_local`
- A3. transportation.json multiple days `location` written as composite prose
- A4. transportation.json Day 12 fabricated `passengers_jade` + `booking_status_jade`
- A5. timeline.json travel_segment extras (origin/destination/route_details/optional) — 33 instances
- A6. accommodation.json fabricated DAY-level `accommodation_jade` + `split_day`
- A7. accommodation.json fabricated ITEM-level `out_of_scope` + `gaode_id`
- A8. accommodation.json phantom `自行安排` entries
- A9. meals.json Days 9-11 wrongly replaced Mathilde Xi'an content with Wudaokou
- A10. attractions.json Days 9-11 wrongly deleted Xi'an attractions
- A11. entertainment.json Days 9-11 wrongly deleted
- A12. shopping.json Day 11 wrongly deleted

**B. Timeline placeholder regression**
- B1. cycle 20260505-123425 timeline subagent wrote `(to plan in Day N review)` placeholder KEYS replacing 7 real Day 7 POIs (青城山 / 人民公园 / 鹤鸣茶社 / 宽窄巷子 / 荣乐园 / 来汤圆 / 带江草堂); same for Days 5/6/12/13/14/15
- B2. AC2 grep alternations across cleanup cycles (123425 + 174743) NEVER included `to plan|placeholder|TBD` so 30+ placeholder KEYS lingered through 3 PASS verdicts
- B3. orchestrator's own dispatch prompt cycle 123425 explicitly authorized "include placeholder entries" → root authorization

**C. Renderer band-aids (10)**
- C1-C10 listed in cycle 20260505-123425 close report

**D. Workspace pollution**
- 1 tracked .bak (3351 lines) + 9 data/*.bak

**E. Image-system multi-layer failures (10)**
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

**F. Diagnosis errors (orchestrator)**
- F1. used `poi-search.py` (real: `poi_search.py`) → declared skill broken
- F2. 3 consecutive QA cycles reported PASS with incomplete grep alternations
- F3. BA spec inventories under-counted (timeline travel_segment 11 vs actual 33; gaode_id 10 vs actual 6 misplaced)
- F4. orchestrator never `cat` of `.claude/commands/review.md` to learn the documented image-fetch substep before improvising
- F5. orchestrator's own dispatch prompts contained the seeds of every later "pollution"

**G. Process failures**
- G1-G5 listed in original session debate prompt

**Codex-found defects orchestrator missed**:
- 27 schema validation failures + 13 warnings on current trip (validate-agent-outputs.py)
- 396 instances of leaked Google Maps API key in `data/*/images.json` URLs (USER ACCEPTED — see 5.1)
- transportation.schema.json + accommodation.schema.json still `additionalProperties: true`
- prompt-purity hook warning-only (lines 57-60, 437-461)
- fetch-images-batch.py path reference wrong (`.claude/skills/...` vs `.claude/commands/scripts/...`)
- Renderer ignores `item.image_url` for meals/attractions/entertainment

---

## Codex-signed Top 5 controls — QA verification standards

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

5. **Acceptance evidence standard**
   - subagent reports include verbatim grep command output for each AC (not summary "0 matches")
   - orchestrator must run the same grep before accepting subagent's PASS report
   - Single consolidated `verify-plan-integrity.py` is the authoritative check; subagents that report PASS without invoking it → orchestrator rejects

---

## Section 8: Attention Notes — verification implications

**User rejects token-rotation as part of accepting the live state**: per 5.1, do NOT propose key rotation in any later cycle. The current Google Maps API key in `data/*/images.json` is a known-accepted state. New defenses target prevention of new leaks (block `key=` in NEW writes via `verify-plan-integrity.py` warn-mode), not retroactive scrubbing.

**Codex consensus is binding**: any cycle proposing to add bespoke hooks "for each symptom" must justify why it's not papering over symptoms. Default position: extend the single `verify-plan-integrity.py` instead of writing a new hook.
