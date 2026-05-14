# M4b Web UI — Manual Test Plan

> Spec: `spec-20260508-221237` §5.6 / §5.9 / §5.10 / §5.13 D
> Task: 20260514-103616 (M4b worker)
> Backend: M4a (`scripts/serve-trip.py`) — already shipped.

These tests cover the 10 acceptance criteria locked in
`docs/dev/ticket-20260514-103616.md` for the M4b deliverable. They are
intentionally manual: M4b is a vanilla-JS no-build module set, and the project
has no headless browser harness. All tests run in real Chrome desktop and Mobile
Safari iOS (or Chrome DevTools mobile-emulation) per BA spec viewport rules.

## Prerequisites

```bash
# 1. Ensure a v2-shape trip exists. Use the canonical fixture trip:
ls data/<trip_id>/meta.json data/<trip_id>/days/day-01.json

# 2. Start the M4a server (binds 127.0.0.1:8765):
python3 scripts/serve-trip.py --trip <trip_id> --port 8765

# 3. Open in browser:
#    Desktop: http://127.0.0.1:8765/trip/<trip_id> at 1440x900
#    Mobile : same URL at 375x667 (Chrome DevTools mobile emulation OK)
```

## AC #1 — Both viewports render

**Desktop (1440x900)**: candidates panel left, timeline center, budget right.
All three panes visible in a 3-column grid.

**Mobile (375x667)**: top bar with three tabs (Candidates / Timeline / Budget).
Only one pane visible at a time. Default = Candidates.

**Pass**: no horizontal scrollbar; trip title in header reflects
`meta.trip_name`; day-picker `<select>` populated from `state.days`.

## AC #2 — Drag-drop fires save + budget + route

1. Pick a candidate card (e.g. lunch slot category).
2. Drag onto the lunch slot drop area.
3. **Within 80ms** drop area shows `data-drop-active="true"` highlight.
4. **On drop**: card disappears (or just gets `card-selected` class), slot
   shows `.slot-selected` content with name + cost.
5. **Within 300ms**: `save-status` flips to "saving..." then "saved".
6. **Within ~1s**: budget panel `day-total` updates (Phase 1 local recompute).
7. **Within ~1s**: adjacent route gap shows `computing route...` then resolves
   to `<N> min` or `route unknown`.
8. **Phase 2**: budget recomputes again once route response arrives so
   transportation cost is included.

**Pass**: Network tab shows POST `/api/save` then POST `/api/budget/recompute`
then POST `/api/route` and a final `/api/budget/recompute` after route returns.

## AC #3 — Mobile parity

Repeat AC #2 in 375x667 viewport:

1. Tap a candidate card. Card gets `tap-selected` class. Compatible drop slots
   gain `data-tap-target="true"` (visible blue dashed border).
2. Tap one highlighted slot. Mutation commits identically to desktop drag.
3. Verify the network request body matches desktop shape:
   `{type:"select", slot:"lunch", option_id:"<id>"}`.

**Pass**: identical mutation payload between desktop drag and mobile tap.

## AC #4 — Approve-day button

1. Open a day with at least one required slot un-selected.
2. **Approve button is disabled.**
3. Fill all required slots (meals + accommodation).
4. **Approve button is enabled.**
5. Click. Network tab: POST `/api/save` with body containing
   `{type:"stage", to_stage:"user-selected"}`.
6. Re-render: `day.stage` flips to `user-selected` locally; button disables
   again (stage is no longer in `{draft-options, user-review}`).

## AC #5 — Refresh recovery

1. Drop several items into slots. Wait > 300ms.
2. Reload page (Ctrl-R).
3. Page hydrates via GET `/api/trip/<id>`.
4. **All previously selected items remain selected.**
5. Budget panel re-populates without user action.
6. Route cache entries (with `status: ok`) render existing minutes
   without firing a new `/api/route`.

**Beforeunload edge case**: drop an item AND immediately Ctrl-R within 300ms.
The `beforeunload` handler uses `navigator.sendBeacon` to flush the pending
mutation. After reload, the item is still there.

## AC #6 — Two-tab concurrency (409-soft)

1. Open trip in Tab A.
2. Open same trip in Tab B (different `editor_session` ID auto-generated).
3. In Tab A: drop an item, wait for "saved".
4. In Tab B: drop a different item.
5. **Tab B receives `{conflict: "409-soft"}`** in /api/save response.
6. **Yellow banner appears in Tab B**: "Another tab edited this trip — refresh
   to see latest."
7. The save still succeeds (last-writer-wins per §5.13 D #5).

## AC #7 — Race / monotonic seq

1. Network throttle to "Slow 3G" in DevTools.
2. Rapidly change selections in slots N, N+1 (5 changes within 1s) so 5
   `/api/route` requests overlap for the same (from,to,mode) pair.
3. Check `state.route_cache[key]` after all return: should reflect ONLY the
   LAST issued request, even if responses arrive out of order.

**Implementation**: `_latestIssued` is set at request-time (not response-time)
in `web/js/routing.js`. A response with `seq < _latestIssued` is dropped.

## AC #8 — Offline banner

1. Stop the server (`Ctrl-C` in the serve-trip terminal).
2. Make a mutation in the UI (e.g. drop a card).
3. The first failed fetch starts the offline timer.
4. **Within 5s**: red banner "Offline — changes paused" appears.
5. `body[data-editing="disabled"]` is set; cards and drop zones are
   pointer-events: none.
6. Restart the server.
7. The reconnect probe (every 5s) hits `/api/trip/__probe__`. On any HTTP
   response (even 404), the banner clears and editing resumes.

## AC #9 — Schema-invalid red + Export disabled

1. Find a non-skipped meal slot with no selection.
2. Slot border is red; `.slot-error` paragraph reads "Selection required".
3. Both Export buttons (PDF, iCal) are disabled.
4. Fill the slot; click Approve-day; both Export buttons become enabled
   (assuming all days are at least `user-selected` and online).

## AC #10 — --auto rationale inline

1. Run `/plan` with `--auto` flag (M3 deliverable; assumes M3 has shipped).
2. Hydrate the resulting trip in M4b UI.
3. Each card with `provenance.selected_by="auto"` shows a `.card-rationale`
   block: "auto-selected: fit_score=<n>; tiebreaker=<key>".
4. NO diff view (deferred per Q3h).
5. NO bulk override (deferred per Q3h).

## Cross-cutting verifications

- **`getActiveDayNumber()`** returns the value of the day-picker `<select>`.
- **State reactive integrity**: every commit triggers
  `queueSave + renderAll + recomputeBudget` (search `state.js:commit`).
- **No hardcoded API URLs** outside relative paths (`/api/...`).
- **No emoji in code or UI strings** (project rule).
- **No framework**: no `<script>` references to React/Vue/Angular.

## Known cross-worker integration gaps (out of M4b scope, surface to M7)

These were flagged by codex during M4b dev. They live in M4a/M3 and require
M7 reconciliation. M4b implements the frontend half; the cross-worker contract
is the orchestrator's job:

1. **Budget aggregator slot path**: `scripts/lib/server/budget.py` reads
   `day.get("breakfast")` directly. If M3 emits canonical `day.slots.breakfast`,
   meal costs are missed. M4b reader handles BOTH shapes; the optimistic write
   targets top-level `day[slot_id]` to match M4a's save shape (codex finding #1).
2. **Trip-total semantics**: backend `handle_budget(day=N)` computes
   `trip_total` by summing the requested day only. UI displays whatever
   the server returns; if `trip_total` is wrong it's an M4a bug, not M4b.
3. **Validation depth**: Export gating uses the M4b client-side
   "all required slots filled" check. A schema-invalid-but-filled day (e.g.,
   meal floor violation with selection) still enables Export. Full
   `scripts/lib/trip_contract/validators.py` integration deferred to M7.
