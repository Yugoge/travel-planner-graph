<!-- AUTO-GENERATED VIEW for dev | source: docs/dev/specs/spec-20260508-221237.md | extracted: 2026-05-09T00:00:00Z -->

# dev view of spec-20260508-221237

**Monolith**: docs/dev/specs/spec-20260508-221237.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> 1. **Harness layer (authoritative)**: a PreToolUse hook MUST block any `Skill` tool call whose skill name matches `gaode-maps*` / `scripts:gaode-maps*` when the calling subagent is not in the allowlist `{timeline, transportation}`. Harness rejection is the source of truth — prompt rules alone are insufficient (see global lessons §11, "must explicitly list what is FORBIDDEN, not just what is allowed").

> 2. **Prompt layer (defense-in-depth)**: every affected agent definition file under `.claude/agents/` MUST contain an explicit `## DO NOT` section naming `gaode-maps` / `高德地图` / `scripts:gaode-maps*` as forbidden, with the rationale and the allowed alternatives (e.g., rednote for content discovery; google-maps where applicable).

---

## Section 1 — implementation files to modify (cross-ref ba.md baseline)

- Skill definition: `/root/travel-planner/.claude/skills/gaode-maps/skill.md` (user-invocable: true; allowed_tools = `Task, Read, Bash`).
- Entrypoint: `.claude/commands/plan.md`.

## §5.2 state-machine implementation requirements

- A documented day-planning state machine: `draft-options → user-review → user-selected → timeline → transportation → finalized`. State transitions are explicit; downstream stages refuse to run on a day still in `draft-options` or `user-review`.
- Schema additions: per-slot `options[]` array with selection marker (`selected: true|false` or `selected_option_id`); validator rejects a day entering `timeline` stage with any slot lacking a selection.
- Content agent prompts updated to emit `options[]` with the agreed minimum count and per-option metadata.
- Plan/review presentation step exists (command or rendered view) that lists every slot × every option for one day in one place.

### 5.4: Harness enforcement covers Bash invocation, not just Skill tool

Discovered during background exploration: current gaode-maps usage by content agents flows through **Bash → python3 .../gaode-maps/scripts/*.py**, not through the `Skill` tool. A hook scoped only to `matcher: Skill` would be a no-op against the real attack surface.

Mandatory enforcement scope:
1. PreToolUse **Bash** matcher: pattern-match the command for any path or token under the gaode-maps surface (`gaode-maps/`, `gaode_maps/`, `amap`, `高德`) and reject when `agent_id` ∉ `{timeline, transportation}`.
2. PreToolUse **Skill** matcher: defense-in-depth (catches `scripts:gaode-maps:*` and any future `gaode-maps:*` namespace).
3. Both matchers exempt the allowlisted agents and log every decision with `{agent_id, tool, matched_pattern, verdict, ts}`.
4. Hook is registered globally for the project; new agents inherit default-deny without per-agent edits.

### 5.5: `--auto` planning mode (agent-decides, no user gating)

Add an `--auto` flag (or equivalent) to the planning entrypoint that bypasses the user-selection gate from §5.2:

- In `--auto` mode, content agents still return `options[]` per slot (multi-option output is mandatory regardless of mode — the web UI depends on it; see §5.6).
- The agent layer (or orchestrator) auto-picks one option per slot using a documented selection policy (e.g. highest-ranked / cheapest / nearest / matches user-profile heuristics — exact policy decided in dev-plan).
- After auto-pick, `timeline` and `transportation` run as in §5.2's post-selection branch — the rest of the pipeline is unchanged.
- `--auto` selections are recorded with provenance: `selected_by: "auto"` plus the rule that fired, so a human can audit and override later in the web UI.

Default mode (without `--auto`) remains the user-gated flow from §5.2.

### 5.6: Web UI overhaul — backend / endpoint cross-cuts (UI specifics in ui-specialist.md)

The interactive HTML output (`generate-html-interactive.py` and friends) must become the primary user-selection surface, not just a final report.

Backend requirement enabling (3) — **all-pairs intra-city precompute**:

- For every day, `timeline` agent MUST compute the intra-city travel segment between every ordered pair of POIs that appear anywhere on that day — including all `options[]` candidates, not just the currently selected items.
- The precomputed N×N matrix is persisted alongside the day's data (e.g. `data/<trip>/day-<n>/intra-city-matrix.json` keyed by `from_poi_id × to_poi_id`, with mode/duration/distance/cost per cell).
- The web UI consumes the matrix to instantly render any drag-drop reorder without a round-trip to the agent.
- Matrix entries cite their gaode-maps source (since `timeline` is allowlisted to call gaode); cache invalidation is by POI-id + mode (re-compute only when a POI's coordinates change).
- `transportation` is unaffected by the matrix — it remains the inter-city designer (§5.2).

(Above bullets are **SUPERSEDED by §5.9 / §5.13 A** — kept here only as the formal record of what was revoked.)

**E resolution (all-pairs intra-city matrix)** — also superseded:

User's intent in providing the slot model is that the candidate space per day is naturally bounded:
- Per-day total candidates ≈ `2 (breakfast) + ~3 (morning) + 2 (lunch) + ~3 (afternoon) + 2 (dinner) + ~3 (evening) ≈ 15` POIs.
- All-pairs matrix size ≈ `15 × 15 = 225` cells, manageable within gaode rate limits given typical multi-day caching.

Therefore E is resolved as **option E1 by virtue of the slot model** (no explicit per-slot 5-cap is added beyond §5.7's per-slot floors; the ceiling falls out of the slot structure):
- `timeline` precomputes the full N×N intra-city matrix per day, where N = total POIs across all 6 slots' `options[]` ∪ accommodation.
- No artificial cap is imposed; the cap is structural (6 slots × small candidate count).
- If a future day exceeds a sensible upper bound (e.g. N > 25), `timeline` MAY fall back to lazy on-demand pair computation in the web UI; this is a dev-plan optimization, not a spec requirement.

### 5.9: Lazy intra-city routing — implementation

**A. All slot times are flexible (not just breakfast)**

- The 6 named slots from §5.8 (`breakfast`, `morning_activity`, `lunch`, `afternoon_activity`, `dinner`, `evening_activity`) define **sequence and category**, NOT clock hours.
- No slot has a hardcoded scheduled hour. The timeline shows items in user-arranged order; clock times are derived from (a) the user's drop position on the timeline canvas, OR (b) durations rolling forward from a single anchor (e.g. day-start time the user sets).
- Validators must NOT reject a day for missing fixed-time fields like "breakfast 08:00".
- Existing schemas that assert fixed times for a slot are relaxed: time fields become optional or derived.

**B. Intra-city routing is computed lazily on user drag-drop**

- `timeline` agent does NOT precompute the all-pairs N×N matrix.
- The persisted artifact `intra-city-matrix.json` (introduced in §5.6 / §5.8) is REMOVED from the spec. If `timeline` previously wrote one for any tooling, that step is dropped.
- Web UI behavior:
  - On every drag-drop reorder, insert, or removal that changes adjacency between two timeline items, the front-end fires a backend request naming the (from_poi, to_poi, mode) tuple.
  - The backend (delegated to `timeline` since it is on the gaode allowlist per §5.1) calls gaode-maps live and returns the segment (duration / distance / mode-detail / polyline if applicable).
  - The result is cached in a per-session or per-day cache keyed by `(from_poi_id, to_poi_id, mode)` so a re-drop of the same pair does not re-hit gaode.
- Loading state: while a freshly dropped pair is being computed, the connection between items shows a transient "computing…" indicator; UI does not block other interactions.
- Failure mode: if gaode call fails, the segment renders as "unknown — retry" with a one-click retry; the user can still save the day, the segment metadata simply records `status: "unresolved"`.

**C. What `timeline` agent computes at plan time (revised)**

- `timeline` STILL builds the day's sequenced timeline from the user-selected items (§5.2 step 4).
- `timeline` STILL computes intra-city travel segments BUT only for the **currently-selected sequence** (what's on the timeline at save time), not for every option pair.
- New role: `timeline` exposes a request handler / endpoint that the web UI calls during drag-drop for ad-hoc pair lookups. The handler is the only path that calls gaode for intra-city routing post-plan.

**D. Caching and rate-limit posture**

- Cache key: `(from_poi_id, to_poi_id, mode)` → segment object. Cache lives for the duration of the trip's active editing session (or longer if the user opts into persistent cache; dev-plan decides storage).
- Cache invalidation: a POI's coordinate change invalidates all cache entries involving that POI.
- Rate-limit guard: backend coalesces simultaneous requests for the same key (in-flight de-dup) to avoid duplicate gaode hits when the user drags rapidly.

### 5.10: Live budget recompute — implementation

**A. Triggers (every event recomputes)**

The budget recomputes automatically on each of:
- Drag-drop reorder, insert, or removal of any timeline item.
- Slot-level selection change (user swaps which option is selected for a slot).
- Accommodation selection change (including same-city auto-lock propagation per §5.7 B).
- Intra-city segment cost arrives or changes (each lazy gaode result from §5.9 may carry a cost field; arrival re-triggers a budget pass for that day).
- Inter-city `transportation` segment edits (handled by the existing `transportation` agent; budget consumes its output).

**B. What is summed (per-day and per-trip)**

- Per-day total = Σ selected meal options + Σ selected activity options + accommodation cost + Σ intra-city travel-segment costs + Σ same-day inter-city transportation cost (if any).
- Per-trip total = Σ per-day totals.
- Budget output exposes a per-slot breakdown so the UI can render a stacked bar / pie of where the day's money goes.

**C. Compute path (no gaode required for budget itself)**

- `budget` is NOT on the gaode allowlist (§5.1) and MUST NOT call gaode. It is a pure aggregator: it consumes `cost` fields already attached to each option (set by content agents), each intra-city segment (set by `timeline`'s lazy lookup, §5.9), and each inter-city segment (set by `transportation`).
- Therefore budget recompute is local CPU work — no external API, no rate limit. Suitable for synchronous response on every UI event.
- For perf, the budget endpoint accepts a delta (changed slot/segment) and returns both the per-day total and the affected breakdown lines, so the front-end can patch the display without a full re-render.

### 5.11: Export — PDF and iCal — implementation

**A. PDF export (printable / share-friendly itinerary)**

- One PDF for the entire trip, paginated by day (one day starts on a new page).
- Per-day content: day header (date + city), the 6 slot sequence with times, each item's name + image thumbnail + brief description + cost, intra-city travel segments between items (mode + duration), inter-city transportation segments on city-change days, accommodation card, per-day total cost.
- Trip-level header: trip title, traveler names, dates, trip total cost, mini map of cities visited (optional — if no map renderer is wired, omit; do not call gaode for the map since `pdf` exporter is not on the allowlist).
- Trip-level footer: index / table of contents linking to each day.
- Format choice: A4 portrait by default, single column. Chinese + English mixed text must render correctly (CJK font embedded).
- Trigger: a "Export PDF" button in the web UI; outputs a downloadable file. CLI parity: `python3 scripts/export-pdf.py --trip <trip-id>`.
- Out of scope: editable PDF forms; all output is read-only.

**B. iCal export (.ics for calendar apps)**

- One `.ics` file for the whole trip; each timeline item becomes a `VEVENT`.
- Event fields: SUMMARY (item name), DTSTART/DTEND (computed from the user-edited timeline; see §5.9 — slot times are flexible but must resolve to clock times at export), LOCATION (item address or coordinates), DESCRIPTION (cost + intra-city travel hint to the next item if any), CATEGORIES (slot name).
- Inter-city transportation segments are also events, with SUMMARY like "HSR G123 Beijing → Xi'an", DTSTART/DTEND from the segment's depart/arrive times.
- Time zones: each event carries the local time zone of its city (Asia/Shanghai for mainland China; allow other zones for non-China trips).
- Reminders: include a `VALARM` 30 minutes before each event (default; user can strip in their calendar app).
- Time anchor requirement: iCal requires absolute times. If a day has un-anchored items (e.g. user never set a start time), the exporter prompts for a day-start time and rolls durations forward; alternatively dev-plan can default to a per-trip anchor (e.g. 09:00 local) to avoid blocking export.
- Trigger: "Export iCal" button in the web UI; CLI parity: `python3 scripts/export-ical.py --trip <trip-id>`.

**C. Common requirements**

- Both exporters MUST NOT call gaode-maps directly (they are not on the allowlist per §5.1; the harness Bash + Skill matchers from §5.4 will block any attempt). All routing data they include must come pre-resolved from `timeline`'s lazy results (§5.9) and `transportation`'s segments. Items without resolved travel data render with the same `unknown` placeholder used in the web UI.
- Both exporters consume the same data files content agents + timeline + transportation + budget produce — no separate authoring step.
- File naming: `<trip-id>.pdf` and `<trip-id>.ics` written to a documented output directory (e.g. `data/<trip-id>/exports/`).
- Re-export overwrites previous output for the same trip-id (atomic write recommended: write to `.tmp` then rename).

### 5.12: No backwards compatibility

- Old trip HTML outputs were **static, non-interactive** documents. They are frozen artifacts and remain viewable as-is regardless of any new architecture. Nothing the new pipeline does breaks them.
- Therefore: **NO backwards-compatibility requirement** for old trip data (e.g. `data/china-20260412-092624/`) into the new options-first pipeline.
- Old trips are NOT loaded into the new code paths. They remain readable via their existing static HTML output, but the new orchestrator / web UI / validators / agents do not need to ingest their schema.

**Operational consequences:**

- Validators for the new schema MAY assume the new shape (per-slot `options[]`, named slots, etc.) and reject any file that doesn't match — they do NOT need a legacy-shape branch.
- The new web UI does NOT need a legacy renderer — old trips keep their existing static HTML; the new UI only handles trips authored by the new pipeline.
- Test suites do NOT need legacy-fixture coverage. Acceptance evidence everywhere may assume "trips authored under the new pipeline."
- If a user wants an old trip re-rendered in the new UI, the answer is "re-run the planner" — no automatic upgrade path is owed.

### 5.13: Codex audit follow-up — supersession + day-type + expanded ban + persistence

#### A. Explicit supersession markers (codex must-fix #1)

- **§5.6 backend block "all-pairs intra-city precompute"** (the bullets that say `timeline` MUST compute the N×N matrix and persist `intra-city-matrix.json`) — **SUPERSEDED by §5.9**. Do NOT implement matrix precompute. Do NOT produce `intra-city-matrix.json`. Do NOT write tests against either.
- **§5.6 acceptance bullet "`intra-city-matrix.json` exists per day and contains entries for all POI pairs in `options[]` ∪ selected items"** — **REVOKED**. Replaced by §5.9 acceptance ("no matrix produced; lazy on-demand routing serves the UI").
- **§5.8 E resolution paragraph "Therefore E is resolved as option E1 by virtue of the slot model… `timeline` precomputes the full N×N intra-city matrix per day"** — **SUPERSEDED by §5.9**. The slot-model description in §5.8 (the 6 named slots, flexible time anchor commentary) remains valid; only the all-pairs matrix portion is dead.
- **§5.8 acceptance bullet "`intra-city-matrix.json` covers all unique POIs that appear in any slot's `options[]` for that day"** — **REVOKED**.

Implementer rule: when §5.6 / §5.8 conflict with §5.9, **§5.9 wins**.

#### B. Day-type behavior table — validator implications

| Day type | breakfast | morning_activity | lunch | afternoon_activity | dinner | evening_activity | accommodation | transportation |
|---|---|---|---|---|---|---|---|---|
| Normal same-city | required | required | required | required | required | required | required (locked if continuation) | N/A |
| Arrival day (afternoon/evening arrival) | skipped (`pre-arrival`) | skipped (`pre-arrival`) | skipped/required (depends on arrival time) | required | required | required | required (first night in city) | required (inter-city inbound) |
| Departure / return-home day | required | required (if time permits) | required (if time permits) | skipped/required | skipped (`post-departure`) | skipped (`post-departure`) | skipped (no last night) OR required (extra night) | required (inter-city outbound) |
| City-change mid-day | required | required (origin city) | required (origin or destination city) | required (destination city) | required (destination) | required (destination) | required (destination, new lock) | required (inter-city) |
| Red-eye / overnight cross-midnight | "owning day" rule below | — | — | — | — | — | "owning day" rule below | spans Day N→N+1 |
| Transit-only day (full-day HSR/flight) | required (origin) | skipped (`in-transit`) | required (en-route or destination) | skipped (`in-transit`) | required (destination) | skipped/required | required (destination if arriving) | required |
| Buffer / rest day | required | optional | required | optional | required | optional | required (locked) | N/A |

**Red-eye / cross-midnight ownership rule**: an inter-city segment whose `depart_ts` is on Day N and `arrive_ts` is on Day N+1 belongs to Day N for budget and timeline purposes (cost, validator, PDF page). On Day N+1, the segment appears as a read-only "arriving from prior day" header item; no duplicate budget. Accommodation lock for Day N+1 is determined by the destination city (the lock unlocks because the city changes).

**Validator updates**:
- Per-slot floor (§5.7 A meals ≥2, §5.8 activities) applies ONLY to non-skipped slots.
- A day where ALL of `breakfast`, `lunch`, `dinner` are skipped is a hard error (no day is purely transit without at least one meal).
- `transportation` is REQUIRED on city-change / arrival / departure / transit days; otherwise N/A.
- `timeline` is REQUIRED on every day with at least one non-skipped activity slot; on transit-only days it may consist solely of transportation segments + meal items at en-route stops.

#### C. Expanded gaode-maps enforcement — additional hook surfaces

§5.1 + §5.4 covered Skill + Bash. Audit identified additional surfaces; the harness MUST also block these for non-allowlisted agents (allowlist remains `{timeline, transportation}` per §5.1):

1. **Read / Grep / Glob on gaode skill source paths** — block any read of:
   - `.claude/skills/gaode-maps/**`
   - `.claude/commands/scripts/gaode-maps/**`
   - any path containing `gaode-maps` / `gaode_maps` / `amap`
   Rationale: prevent a banned agent from reading API patterns to roll its own client. PreToolUse Read/Grep/Glob matchers added.
2. **Direct REST / network egress** — block any Bash, WebFetch, or other network tool whose target contains:
   - `restapi.amap.com`, `webapi.amap.com`, `restsdk.amap.com`, `*.amap.com`
   - `lbs.amap.com`
   - any URL with `gaode` / `amap` in host or path
   PreToolUse matchers on Bash (curl/wget/python `requests`/`urllib`) AND on WebFetch / network MCP tools.
3. **Environment variables** — block Bash commands referencing `AMAP_*`, `GAODE_*`, `AMAP_KEY`, `AMAP_TOKEN`, `GAODE_KEY` env-vars (export, echo, parameter substitution, command-line argument).
4. **Wrapper / indirect script paths** — when matching Bash, the hook resolves the invoked path (via `readlink`/`realpath` on the first non-flag token if it looks like a script) and blocks if the resolved target is under any gaode tree. This catches `bash wrapper.sh` / `python -m wrapper` patterns where the visible token is innocent.
5. **Backend identity model (web app drag-drop endpoint)** — the §5.9 lazy-routing endpoint runs server-side and must invoke `timeline` with a verifiable `agent_id`. The harness MUST default-deny when `agent_id` is missing/unknown on the gaode hooks. The endpoint code is responsible for setting `agent_id="timeline"` on outbound calls; if it doesn't, the hook denies and the UI shows "unknown — retry" per §5.9. No fail-open path.
6. **Allowlist canonicalization** — the allowlist binds to canonical agent IDs `timeline` and `transportation` (NOT shorthand "transport"). The hook MUST compare on the canonical form; any alias resolves to the canonical name before the check. New agents are default-deny until explicitly added to the canonical allowlist.

#### D. Web app persistence and concurrency contract — backend API

The web UI (§5.6, §5.9, §5.10, §5.11) requires a non-trivial persistence model. Specify the following minimal contract:

1. **Server vs static** — the web UI is **server-backed** (a small local web app, not a `file://` HTML page). The server hosts the lazy gaode routing endpoint (§5.9), the live budget endpoint (§5.10), the export endpoints (§5.11), and the trip JSON store. Static HTML alone cannot satisfy these; this clarifies the implicit assumption.
2. **Save semantics** — **autosave** on every committed UI mutation (drop, reorder, slot selection change, manual edit), with a 300 ms debounce window per day to coalesce rapid edits. A "saved <Nm ago>" indicator in the header. Explicit "Save now" button forces immediate flush. No "discard" — unwanted changes are reverted via undo (out of scope; deferred).
3. **Persistence shape** — autosave writes to the canonical day data files (`data/<trip>/day-<n>/...`) atomically (write to `.tmp`, fsync, rename). A `meta.json` per trip records `schema_version`, `last_saved_ts`, `current_editor_session` (UUID set by the active browser tab on first edit).
4. **Refresh recovery** — on page reload the UI reads back the persisted state. Lazy-routing cache and unresolved-segment status are persisted alongside the day data so reload renders the same timeline as before. No client-only ephemeral state survives refresh — anything important is server-side.
5. **Concurrent edits / multi-tab** — last-writer-wins with a soft warning. The server tracks `current_editor_session` in `meta.json`; if a save arrives from a session that doesn't match, the server accepts but emits a `409-soft` response, and the UI shows a yellow banner "Another tab edited this trip — refresh to see latest." No automatic merge.
6. **Async race (lazy route stale results)** — every routing request carries a monotonic `request_seq` per (from_poi, to_poi) pair. The UI ignores responses whose `request_seq` is lower than the latest committed for that pair. The server does not need to know about this; it is a UI-side filter.
7. **Backend API contract (minimum)**:
   - `POST /api/route` — body `{trip_id, day, from_poi_id, to_poi_id, mode, request_seq}` → returns `{segment, request_seq, status: "ok"|"unknown"|"error"}`. `agent_id="timeline"` is enforced server-side per §5.13 C #5.
   - `POST /api/budget/recompute` — body `{trip_id, day, delta?}` → returns `{day_total, trip_total, breakdown[]}`. No gaode involvement; pure aggregation.
   - `POST /api/save` — body `{trip_id, day, mutations[]}` → returns `{saved_ts, conflict?: "409-soft"}`. Idempotent on identical mutations.
   - `GET /api/trip/<trip_id>` — returns the full trip JSON for initial load and for refresh recovery.
   - `POST /api/export/pdf` and `POST /api/export/ical` — return the file path / blob; gaode-blocked per §5.13 C and §5.11.
8. **Mobile drag-drop** — required to work on touch devices; use HTML5 Pointer Events or a touch-aware drag-drop library (dev-plan picks). On screens narrower than 640 px, the candidates panel collapses behind a tab; drag-drop replaced by tap-to-select + tap-to-place workflow that emits the same mutations as drag-drop.
9. **Offline mode** — explicitly **out of scope**. If the server is unreachable, the UI shows a banner "Offline — changes paused" and disables editing controls until reconnect. No local queue.
10. **Validation feedback in UI** — when validators (§5.13 B) reject a state, the UI shows the failing slot in red with the validator's error message inline and disables export until resolved. Skip-state edits that would leave a hard-error (e.g. all three meals skipped) are rejected at the UI level before reaching the server.

### 5.3: Cross-cutting constraints — implementation rules

- **Default-deny posture**: both the gaode-maps skill ban (§5.1) and the timeline/transportation gate (§5.2) follow default-deny; new agents added later inherit the ban automatically and inherit the gate automatically (no opt-out without explicit allowlist edit + spec amendment).
- **No emoji in code/comments/commit messages** (project-wide rule, restated for the implementing dev).
- **Auto-commit safety**: changes flow through the `refs/checkpoints/<branch>` mechanism per `docs/checkpoint-mechanism.md`; HEAD master never advances on PostToolUse.
