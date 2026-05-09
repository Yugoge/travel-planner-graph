<!-- AUTO-GENERATED VIEW for qa | source: docs/dev/specs/spec-20260508-221237.md | extracted: 2026-05-09T00:00:00Z -->

# qa view of spec-20260508-221237

**Monolith**: docs/dev/specs/spec-20260508-221237.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> **Acceptance evidence**:

> - Negative test: a non-allowlisted subagent invoking `Skill(skill="scripts:gaode-maps:tools:routing", ...)` is blocked with a clear error message naming the policy.
> - Positive test: `timeline` and `transportation` invocations of gaode-maps skills proceed normally.

---

## §5.1 Acceptance evidence — gaode skill ban

**Allowlist (only these two agents may call gaode-maps skills)**: `timeline`, `transportation`.

**Out-of-scope agents (must be banned)**: `meals`, `attractions`, `accommodation`, `cafe`, `entertainment`, `shopping`, `ba`, `qa`, `dev`, `pm`, `product-owner`, `ui-specialist`, `budget`, `user`, plus any other agent not on the allowlist (default-deny).

**Acceptance evidence**:
- Hook file exists and is wired under PreToolUse with `matcher: Skill`.
- Hook decision logged with `agent_id`, attempted skill name, allow/deny verdict.
- Negative test: a non-allowlisted subagent invoking `Skill(skill="scripts:gaode-maps:tools:routing", ...)` is blocked with a clear error message naming the policy.
- Positive test: `timeline` and `transportation` invocations of gaode-maps skills proceed normally.
- All affected agent prompt files contain the DO-NOT block (grep verification).

## §5.2 Acceptance evidence — options-first state machine

**Acceptance evidence**:
- A documented day-planning state machine: `draft-options → user-review → user-selected → timeline → transportation → finalized`. State transitions are explicit; downstream stages refuse to run on a day still in `draft-options` or `user-review`.
- Schema additions: per-slot `options[]` array with selection marker (`selected: true|false` or `selected_option_id`); validator rejects a day entering `timeline` stage with any slot lacking a selection.
- Content agent prompts updated to emit `options[]` with the agreed minimum count and per-option metadata.
- Plan/review presentation step exists (command or rendered view) that lists every slot × every option for one day in one place.
- Negative test: invoking `timeline` on a day with un-selected slots is rejected with a clear error pointing at the missing selections.
- Positive test: a full day passes through draft → review → user-pick → timeline → transportation, with each stage's input being the prior stage's signed output.

## §5.4 Hook coverage — Bash + Skill matchers

Mandatory enforcement scope:
1. PreToolUse **Bash** matcher: pattern-match the command for any path or token under the gaode-maps surface (`gaode-maps/`, `gaode_maps/`, `amap`, `高德`) and reject when `agent_id` ∉ `{timeline, transportation}`.
2. PreToolUse **Skill** matcher: defense-in-depth (catches `scripts:gaode-maps:*` and any future `gaode-maps:*` namespace).
3. Both matchers exempt the allowlisted agents and log every decision with `{agent_id, tool, matched_pattern, verdict, ts}`.
4. Hook is registered globally for the project; new agents inherit default-deny without per-agent edits.

## §5.7 Validator enforcement floors

**A. Per-slot option floor — meals**

- Per-meal floor: `breakfast.options[].length >= 2`, `lunch.options[].length >= 2`, `dinner.options[].length >= 2`.
- Per-day total floor across the three meal slots: `>= 6` distinct restaurants per day.
- Validator must enforce both the per-slot AND per-day totals; a day failing either fails plan validation.

**B. Per-slot option floor — accommodation, with same-city auto-lock**

- For the FIRST night in a city: `options[].length >= 3` distinct hotels surfaced to user.
- "Same city" continuation rule: if day N's accommodation is in city X and day N+1 stays in city X, day N+1's accommodation slot auto-locks to the day-N selection (no re-prompt, no candidate panel for that slot).
- City-change detection key: city name on the skeleton (or stay-block boundary). When the city changes, the next night re-opens the 3-option choice.

## §5.8 Acceptance — slot model evidence

Acceptance evidence augmenting §5.6:
- Each day's data has the 6 named slot keys, each with `options[]`.
- `intra-city-matrix.json` covers all unique POIs that appear in any slot's `options[]` for that day.
- Validator rejects a day missing any of the 6 slots OR with under-min candidates per meal slot.

## §5.9 E. Acceptance evidence (revising §5.6)

- No `intra-city-matrix.json` file is produced or required at plan time.
- Drag-drop reorder fires a backend request; segment populates within a reasonable interaction time (target: <1 s typical).
- Re-dropping the same pair within a session is served from cache (no second gaode call observed).
- Days saved with un-resolved segments still load and display the "unknown — retry" affordance.

## §5.10 E. Acceptance evidence — live budget

- Drag-drop a more expensive restaurant in: per-day total and per-trip total both rise, breakdown shows the new line item.
- Remove an attraction: total drops, intra-city segment cost involving that POI also drops out.
- A lazy gaode segment arrives with a cost: budget reflects it on next recompute without user intervention.
- `budget` agent issues no gaode calls (verified via the harness Bash hook from §5.4 — `agent_id: "budget"` invoking gaode would be denied; observation: zero deny-events expected because budget never tries).

## §5.11 D. Acceptance evidence — exports

- PDF: open the file → all days present, paginated, costs match the budget panel, CJK text renders, no broken images.
- iCal: import the `.ics` into Apple Calendar / Google Calendar → events appear at the right times, in the right zones, with locations resolvable.
- Negative test: invoking either exporter as `agent_id: "pdf-export"` (or however the script is identified) tries to call gaode → blocked by the harness hook from §5.4 → exporter falls back to unresolved-segment rendering, does not crash.

## §5.6 Original acceptance bullets

Acceptance evidence:
- HTML page loads with the candidates panel populated for every day.
- User can drag a candidate onto the timeline; the dropped item appears with auto-computed travel segments to its neighbors.
- Removing or reordering items updates adjacent travel segments live.
- `intra-city-matrix.json` exists per day and contains entries for all POI pairs in `options[]` ∪ selected items.
- Provenance fields (`selected_by`) populated correctly for auto vs user-drag selections.

## §5.13 A. Supersession enforcement

- **§5.6 backend block "all-pairs intra-city precompute"** (the bullets that say `timeline` MUST compute the N×N matrix and persist `intra-city-matrix.json`) — **SUPERSEDED by §5.9**. Do NOT implement matrix precompute. Do NOT produce `intra-city-matrix.json`. Do NOT write tests against either.
- **§5.6 acceptance bullet "`intra-city-matrix.json` exists per day and contains entries for all POI pairs in `options[]` ∪ selected items"** — **REVOKED**. Replaced by §5.9 acceptance ("no matrix produced; lazy on-demand routing serves the UI").
- **§5.8 E resolution paragraph "Therefore E is resolved as option E1 by virtue of the slot model… `timeline` precomputes the full N×N intra-city matrix per day"** — **SUPERSEDED by §5.9**. The slot-model description in §5.8 (the 6 named slots, flexible time anchor commentary) remains valid; only the all-pairs matrix portion is dead.
- **§5.8 acceptance bullet "`intra-city-matrix.json` covers all unique POIs that appear in any slot's `options[]` for that day"** — **REVOKED**.

Implementer rule: when §5.6 / §5.8 conflict with §5.9, **§5.9 wins**.

## §5.13 B. Day-type validator updates

| Day type | breakfast | morning_activity | lunch | afternoon_activity | dinner | evening_activity | accommodation | transportation |
|---|---|---|---|---|---|---|---|---|
| Normal same-city | required | required | required | required | required | required | required (locked if continuation) | N/A |
| Arrival day (afternoon/evening arrival) | skipped (`pre-arrival`) | skipped (`pre-arrival`) | skipped/required (depends on arrival time) | required | required | required | required (first night in city) | required (inter-city inbound) |
| Departure / return-home day | required | required (if time permits) | required (if time permits) | skipped/required | skipped (`post-departure`) | skipped (`post-departure`) | skipped (no last night) OR required (extra night) | required (inter-city outbound) |
| City-change mid-day | required | required (origin city) | required (origin or destination city) | required (destination city) | required (destination) | required (destination) | required (destination, new lock) | required (inter-city) |
| Red-eye / overnight cross-midnight | "owning day" rule below | — | — | — | — | — | "owning day" rule below | spans Day N→N+1 |
| Transit-only day (full-day HSR/flight) | required (origin) | skipped (`in-transit`) | required (en-route or destination) | skipped (`in-transit`) | required (destination) | skipped/required | required (destination if arriving) | required |
| Buffer / rest day | required | optional | required | optional | required | optional | required (locked) | N/A |

**Validator updates**:
- Per-slot floor (§5.7 A meals ≥2, §5.8 activities) applies ONLY to non-skipped slots.
- A day where ALL of `breakfast`, `lunch`, `dinner` are skipped is a hard error (no day is purely transit without at least one meal).
- `transportation` is REQUIRED on city-change / arrival / departure / transit days; otherwise N/A.
- `timeline` is REQUIRED on every day with at least one non-skipped activity slot; on transit-only days it may consist solely of transportation segments + meal items at en-route stops.

**Web UI consequences**: skipped slots render as a muted "skipped — reason" placeholder in the candidates panel; user can un-skip by drag-drop, which fires a re-research request to the appropriate content agent for that slot.

## §5.13 C. Expanded gaode ban — negative/positive test surfaces

Acceptance evidence:
- Negative tests for each surface above (Read on `.claude/skills/gaode-maps/skill.md` from `meals`, `curl https://restapi.amap.com/...` from `attractions`, `echo $AMAP_KEY` from `dev`, wrapper script invocation, missing-`agent_id` request, alias `transport` request) all blocked with a clear policy message.
- Positive tests for `timeline` and `transportation` invocations across all six surfaces still succeed.
- Hook log includes the matched surface (`skill | bash-token | bash-resolved-path | network-host | env-var | read-path | identity-default-deny | alias-blocked`).

## §5.13 D. Persistence + concurrency acceptance

Acceptance evidence:
- Drag-drop a candidate; refresh the page; the dropped item is still there (refresh recovery test).
- Open the same day in two browser tabs; edit in tab A; tab B shows the 409-soft banner (concurrency test).
- Rapid-fire 5 reorders; only the latest routing result is rendered, the 4 stale responses are silently dropped (race test).
- Mobile viewport (375×667) loads the trip; tap-to-place workflow produces the same data mutation as desktop drag-drop (mobile parity test).
- Server stopped mid-edit; UI shows "Offline" banner; controls disabled; reconnect resumes (offline behavior test).

## §5.12 — no backcompat tests

- Validators for the new schema MAY assume the new shape (per-slot `options[]`, named slots, etc.) and reject any file that doesn't match — they do NOT need a legacy-shape branch.
- Test suites do NOT need legacy-fixture coverage. Acceptance evidence everywhere may assume "trips authored under the new pipeline."

## §5.13 D #10 — UI validation feedback

10. **Validation feedback in UI** — when validators (§5.13 B) reject a state, the UI shows the failing slot in red with the validator's error message inline and disables export until resolved. Skip-state edits that would leave a hard-error (e.g. all three meals skipped) are rejected at the UI level before reaching the server.
