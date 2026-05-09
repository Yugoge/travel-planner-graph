# Specialist Consultation Findings — spec-20260508-221237

**Cycle**: 1 (whole-spec scope per user "全部")
**Specialists assessed**: ui-specialist, architect, product-owner, user — all 4 RELEVANT, all 4 invoked.
**Status**: observation-only; no files modified by specialists.

---

## specialists_assessed

```json
{
  "ui-specialist": "RELEVANT — §5.6 candidates panel + drag-drop + §5.10D budget panel + §5.13D mobile + validation UI",
  "architect": "RELEVANT — §5.13C harness multi-matcher, §5.2 pipeline reorder, §5.7/§5.8 schema migration, §5.13D server endpoints, §5.9 lazy routing/cache",
  "product-owner": "RELEVANT — §5.5 --auto, §5.11 exports, §5.13B day-type table, §5.7B accommodation lock — completeness/business-logic check",
  "user": "RELEVANT — review-gate, drag-drop, mobile, offline, validation feedback — end-to-end UX"
}
```

---

## Cross-cutting risks all four specialists flagged

1. **Server-backed app is required, not optional** (ui-specialist obs_1, architect arch-7, product-owner po-31, user-1/13/17/18)
   - Existing renderer `scripts/generate-html-interactive.py` (3376 lines) emits a single static React+babel-standalone HTML file with NO fetch/drag/autosave/server endpoints.
   - §5.13D demands a "small local web app" with 5+ REST endpoints (/api/route, /api/budget/recompute, /api/save, /api/trip/<id>, /api/export/pdf|ical). None exist. This is the largest single delivery gap.
   - Architect recommends Python (FastAPI/Flask, shares ~/.claude/venv) over Node to avoid 2nd toolchain. Single-worker uvicorn avoids multi-process cache coherence. Storage: filesystem (data/<trip>/...) atomic write per spec §5.13D #3.

2. **Day-state machine should be promoted to a per-day file** (architect arch-prop-2)
   - Current plan.md infers stage from file presence (`test -f meals.json`). With options-first this fails (content files exist before timeline runs but after user-review starts).
   - Proposed: `data/<trip>/day-states.json` mapping day_number → `{state, day_type, locked_to_day?}` per the §5.13B day-type table.
   - Validators, web server, and stage gates all read this single file.

3. **Gaode-ban hooks should NOT splinter into 5 ad-hoc hooks** (architect arch-prop-1)
   - Current `pretool-tool-policy.py` is the single PreToolUse-* hook with `lib/policy_registry.is_allowed(role, tool, target)` shape.
   - §5.13C demands six matcher surfaces (Skill name, Bash token, Bash resolved path, network host, env var, Read/Grep/Glob path). Naive: 5 new hook scripts. Better: extend tool-policy.v1.json with `denied_skill_prefixes`, `denied_bash_tokens`, `denied_network_hosts`, `denied_env_vars`, plus top-level `gaode_allowlist_canonical_agent_ids: ["timeline","transportation"]`. Single hook, single policy, single audit log shape.

4. **agent_id fail-open contradicts §5.13C #5 default-deny** (architect arch-2)
   - `pretool-tool-policy.py:96-99` exits 0 (allow) when role is unresolvable — deliberate for first-write race per LOW-10 fix.
   - §5.13C #5 demands default-DENY when agent_id is missing on the gaode hooks. Naive resolution is policy inconsistency between hooks. Resolve by introducing a fail-CLOSED sub-policy keyed only to the gaode tag-set, not changing the global posture.

5. **Pipeline reordering touches ≥7 spots in plan.md and obsoletes sync-agent-data.py reverse-injection** (architect arch-4, arch-11)
   - `plan.md:362,488,640,703,1117,1505,1827` all assume content→transportation→timeline→user-review.
   - Spec §5.2 inverts to options→user-review→timeline→transportation. `sync-agent-data.py`'s reverse time-injection (plan.md:1265-1270) becomes architecturally backward.
   - Inter-component contracts (content-agent → orchestrator → user-review → timeline → transportation → budget → exporters) need explicit JSON schemas — currently implicit and fragile.

6. **Schema migration is a hard break** (architect arch-5)
   - Existing meals.schema.json `meal_slot` shape is `{primary, alternatives[]}` with `primary` REQUIRED.
   - §5.7A demands `breakfast/lunch/dinner.options[]` with floor 2 each, day-total floor 6, no privileged `primary`. Same for attractions/cafe/entertainment/shopping/accommodation.
   - §5.8 introduces 6 NAMED slots — current schema partitions by AGENT, new schema partitions by SLOT. Cross-agent slot merging needs orchestrator step.
   - §5.12 explicitly waives backwards compatibility — recommend single hard cutover (no shim) with `schema_version >= 2` discriminator on plan-skeleton.json so renderer chooses legacy-static or new-interactive path.

7. **Lazy routing cache key shape is under-specified** (architect arch-8)
   - Spec key is `(from_poi_id, to_poi_id, mode)`. But `poi_id` is not a stable identifier in current data (POIs emitted by `name_base + coordinates`).
   - Recommendation: hash `(round(lat,5), round(lng,5))` into the key directly — coordinate changes naturally produce a new key, no explicit invalidation needed.
   - Cache directionality: gaode routes are NOT symmetric A→B vs B→A; preserve order. Persistence: file-system cache `data/<trip>/route-cache.json` per §5.13D #4.
   - Single shared module `scripts/lib/route_resolver.py` consumed by BOTH timeline subagent (plan-time) AND web server's lazy endpoint — closes the auto-mode empty-cache problem at export time (architect arch-prop-3, product-owner po-15).

8. **Drag stack: Pointer Events handcrafted + tap-to-place mobile mode REQUIRED** (ui-specialist finding 2)
   - HTML5 Drag is disqualified by §5.13D #8 (no touch support).
   - Pointer Events handcrafted: zero-dep, spec-endorsed, ~200-400 lines careful code, missing keyboard-driven equivalent for WCAG 2.1.1.
   - @dnd-kit/core: production-grade fallback if dev estimates Pointer Events >2 days; adds a UMD <script> dependency.
   - Tap-to-place at <640px: MANDATORY regardless, emits same mutation events as drag-drop. useBreakpoint() at line 1508 already provides the gate.

9. **State management shape (framework-agnostic)** (ui-specialist finding 3)
   - Required atoms: `trip` tree, `perDayDirty`, `lastSavedAt`, `pendingSave` (300ms debounce), `currentEditorSession`, `softConflictBanner`, `selectedCandidate`, `routePairCache` (key `from::to::mode`), `routePairLatestSeq` (monotonic per pair, §5.13D #6 stale filter), `routePairInflight` (AbortController for re-drop cancel), `validationErrors`, `exportDisabled`, `online`.
   - Mutation pipeline: emit → reducer → schedule lazy lookups (new request_seq) → debounce save → validators → budget recompute → on-save 200/409-soft/network-fail.

10. **PDF/iCal exporter "all routing pre-resolved" hidden contract** (architect arch-10, product-owner po-29)
    - Spec §5.11C forbids exporters from calling gaode. They consume only pre-resolved cache.
    - In --auto mode (§5.5), the cache is empty if user never drag-drops → every segment exports as "unknown".
    - Either auto-mode pre-warms cache (timeline plan-time call per §5.9C) OR exporter triggers a one-shot batch warm-up (needs the `route_resolver.py` shared module, which is allowed via timeline canonical id).
    - PDF library trade-offs: weasyprint (HTML→PDF, CJK via @font-face, plays with existing static generator) vs reportlab (smaller dep, more setup) vs headless Chromium (high quality, heavy runtime).
    - iCal: `icalendar` library handles VTIMEZONE for Asia/Shanghai natively, VALARM for 30min reminders.
    - CJK font: ship Noto Sans CJK (~20MB, license-clear) for PDF embedding.

---

## Critical UX contradictions surfaced (resolve at spec level, not dev-plan)

### C1. Cascade vs Undo (HIGHEST stakes)
- §5.7B same-city accommodation auto-lock cascades day-N pick to N+1, N+2, ... up to next city change. A single user click silently mutates up to 10+ day pages.
- §5.13D #2 explicitly defers undo ("out of scope; deferred").
- **Implication**: highest-stakes mutation has zero recovery affordance. INFJ user trust collapses on first surprise cascade.
- **Recommendation**: either (a) ship a 10-second toast undo for cascade only, OR (b) require explicit confirm modal "propagate to days 6-12?" before cascade fires. Spec must commit at this level.

### C2. iCal time-anchor: prompt or default?
- §5.9A makes ALL slot times flexible by default → every day is un-anchored at first export.
- §5.11B leaves "prompt per day" vs "per-trip default 09:00" choice to dev-plan.
- "Prompt per day" = 15 modals in a row at first 15-day-trip export. "Default 09:00" with unresolved-segment durations = collapses all 6 events to 09:00 cluster on Day 1.
- **Recommendation**: spec must commit to a single "set anchors" panel BEFORE first export, with per-trip default + per-day override in one scrollable view, not modal cascade.

### C3. --auto override path missing
- §5.5 records `selected_by: "auto"` but spec doesn't say HOW user discovers/overrides specific picks in web UI.
- If candidates panel is hidden, no override path. If shown, --auto value-prop ("trust the agent") is destroyed.
- **Recommendation**: panel default-collapsed with "auto-picked: see N alternatives" link per slot. Provenance must include fit_score COMPONENTS (e.g. "matched: 文艺温馨=0.9, no-touristy-chain=1.0, location=0.7; missed: cost-target=0.3"), not just opaque score.

### C4. 409-soft "refresh" is wrong primary action
- §5.13D #5: tab B sees tab A wrote → banner "refresh to see latest" → refresh wipes tab B's in-progress local state (multi-day power user with 3 tabs open loses all current edits).
- **Recommendation**: distinguish cross-day no-conflict (auto-merge OK) from same-day same-slot conflict (then prompt with diff modal).

### C5. Offline mid-drag silent loss
- §5.13D #9 "no local queue". Mid-drag network drop = drop completes locally, autosave silently fails, user moves on, change is lost.
- **Recommendation**: on offline-detected, immediately revert any in-flight unsynced mutation visually OR show clear "this change was not saved — reconnect to retry" chip.

### C6. Drag semantics undefined for swap and cross-type drops
- §5.6 specifies single drops only. Swap (lunch ↔ afternoon_activity) requires 3 manual drags, which is not a "swap" affordance.
- Dropping a meal card on `morning_activity` (typed slot) — silent acceptance? silent rejection? auto-coerce? Undefined.
- **Recommendation**: spec must define (a) timeline-to-timeline drag for swap, (b) reject-with-toast for cross-type drops.

---

## Feature gaps absent from spec (PO + user identified)

- **No trips-list / dashboard landing page** (po-31 critical) — web UI has no entrypoint as currently spec'd; how does user reach /trip/<id>?
- **No multi-traveler attribution** (po-7) — Matilde-Jade with Jade's class days requires per-day-per-traveler attendance modeling. Documented user need (commit 1441e52 surgically fixed Day 8 Matilde-solo).
- **No undo despite autosave** (po-3) — paired with C1 above.
- **No compare/diff side-by-side** (po-1) — 3 hotels side-by-side comparison is the natural decision UI; not spec'd.
- **No re-roll / "request more options"** (po-2) — only un-skip path is spec'd; user disliking all 3 candidates has no escape.
- **No cost-cap / dietary filter** (po-4, po-5) — table-stakes for any travel planner.
- **No image on candidate cards** (po-8) — §5.6 fields lack image; §5.11A PDF includes thumbnail (inconsistency).
- **No KML / 高德 list export** (po-27) — for in-the-moment navigation handoff. iCal alone is insufficient.
- **No share-link / read-only public URL** (po-26) — modern share primitive; PDF-only is heavyweight.
- **No "add custom item" affordance** (user-20) — friend recommends a place not in rednote results; user has no path.
- **Skipped/loading/failed slot states visually undifferentiated** (user-11) — three states need distinct visual treatments.
- **Per-day save indicator missing** (user-17) — single header "saved Nm ago" hides which day failed.

## Day-type table edge cases not covered

- **Multi-leg same-day inter-city** (po-17): morning HSR Beijing→Xi'an + evening HSR Xi'an→Chengdu. Two transportation entries, three cities, slot ownership undefined.
- **Cancelled flight / rebook flow** (po-18): no "plan disrupted, replan from now" day type; spec must explicitly mark out of scope or define.
- **Half-day arrival into transit hub** (po-19): arrival + departure on same day, both rows apply, conflicting required/skipped values.
- **Sleeper-train accommodation** (po-20): K/Z train sleeper IS the accommodation; no slot state expresses this.

---

## What is dead and must NOT be implemented (per §5.13A supersession)

- All-pairs intra-city matrix precompute (`intra-city-matrix.json` file) — §5.6 backend block, §5.8 E resolution, all related acceptance bullets. Replaced by §5.9 lazy on-demand.
- §5.3 "backwards compatibility with existing trips" — REVOKED by §5.12. No shim, no migration script, no auto-load. Old trips remain readable via existing static HTML; new code paths simply do not load them.

---

## Recommended milestone breakdown (BA's call to refine)

Specialists collectively suggest the spec naturally decomposes into 4-5 independent dev cycles. Order recommendation:

**M1 — Harness ban (foundation, ~1 cycle)**:
- §5.1, §5.4, §5.13C six matcher surfaces.
- Extend `tool-policy.v1.json` with new `denied_skill_prefixes/denied_bash_tokens/denied_network_hosts/denied_env_vars/gaode_allowlist_canonical_agent_ids` (architect arch-prop-1).
- Add `## DO NOT` block to every non-allowlisted agent .md.
- Negative + positive tests per §5.13C acceptance.

**M2 — Schema + state machine + pipeline reorder (~1-2 cycles)**:
- New schemas: per-slot `options[]`, named 6 slots, `selected_by` provenance, skipped state, `day-states.json` (architect arch-prop-2).
- Plan.md inverted: content (multi-option) → user-review → timeline → transportation.
- `--auto` mode + fit_score components surfaced in provenance.
- Validator extension for §5.13B day-type table.
- Cross-agent slot merging (morning_activity from attractions+cafe+entertainment+shopping).
- `route_resolver.py` shared module (architect arch-prop-3).

**M3 — Web UI MVP (~1-2 cycles)**:
- FastAPI server + 5 REST endpoints + atomic file save + `meta.json` with `current_editor_session`.
- Trips-list landing page (close po-31 gap).
- React rewrite: candidates panel by 6 slots + Pointer Events drag layer + tap-to-place mobile mode.
- Live budget panel (debounced).
- Lazy routing on adjacency change with computing/unknown/retry states.
- `selected_by` visual provenance treatment + cascade undo toast (resolves C1).

**M4 — Exports (~1 cycle)**:
- `route_resolver.py` warm-up call from --auto / pre-export.
- weasyprint PDF with CJK font + per-day pages + ToC + cost summary page (close po-28 gap).
- icalendar iCal with VTIMEZONE + VALARM + per-trip-default time anchor + per-day override panel BEFORE export (resolves C2).
- KML / 高德 list export (close po-27 gap).

**M5 — Polish (deferred items, ~1 cycle)**:
- Multi-traveler attribution (close po-7 gap).
- Compare/diff + re-roll (close po-1, po-2).
- Cost-cap + dietary filter (close po-4, po-5).
- Custom-card injection (close user-20).
- Share-link read-only URL (close po-26).

---

## Minimum spec amendments BA should request from user before any dev cycle

1. **C1 cascade undo policy** (toast-based undo OR confirm-modal-before-cascade)
2. **C2 iCal time-anchor model** (per-trip-default + per-day-override panel; commit at spec, not dev-plan)
3. **C3 --auto override surface** (panel default-collapsed with "see alternatives" link per slot; fit_score components in provenance)
4. **C4 409-soft semantics** (cross-day auto-merge vs same-day prompt-with-diff)
5. **C6 drag semantics** (define swap and cross-type rejection)
6. **po-31 trips-list landing page** (in scope or explicit out-of-scope?)
7. **po-7 multi-traveler attribution** (in scope or explicit out-of-scope?)

Without resolutions, dev will inherit the contradictions and ship a UX-broken v1.
