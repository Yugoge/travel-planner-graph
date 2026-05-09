<!-- AUTO-GENERATED VIEW for ui-specialist | source: docs/dev/specs/spec-20260508-221237.md | extracted: 2026-05-09T00:00:00Z -->

# ui-specialist view of spec-20260508-221237

**Monolith**: docs/dev/specs/spec-20260508-221237.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> The interactive HTML output (`generate-html-interactive.py` and friends) must become the primary user-selection surface, not just a final report.

> Required UI features:

---

## §5.6 Web UI overhaul — drag-and-drop timeline

> 全面改进 web 端，使得全部候选的内容都可以被展示在 web 端并且用户可以自己拖拽内容到 timeline 视图（这要求 timeline 视图增加新的候选窗口）。同时 timeline 应该自动计算每一个景点相互之间的市内行程，即使用户不用，因为这样可以让用户在网页自定义行程的时候可以自动地计算任意两个地方的 timeline（自动匹配）。

The interactive HTML output (`generate-html-interactive.py` and friends) must become the primary user-selection surface, not just a final report.

Required UI features:

1. **Candidates panel** — a new pane in the timeline view that lists every `options[]` candidate produced by content agents for the current day, grouped by slot (meals/attractions/cafe/entertainment/shopping/accommodation), each card carrying name, location, cost, why-fits-user, source citation. The panel coexists with the timeline column.
2. **Drag-and-drop** — user can drag any candidate card from the panel onto the timeline at a chosen time slot. Dropping a card materializes it as a timeline item.
3. **Auto-routed gaps** — whenever two timeline items are adjacent (after a drop, move, or removal), the gap between them auto-fills with the intra-city travel segment connecting them. No manual recompute click; the connection updates live as items are reordered.
4. **Selection persistence** — drag/drop edits write back to the day's data file (or to a session-scoped working copy that is committed on user "save"). The schema must distinguish "auto-selected", "user-selected via drag-drop", and "agent-default" provenance.

## §5.7 B Web UI on locked nights — accommodation

- Web UI (§5.6): on locked nights, the candidates panel for accommodation is hidden or shows the locked hotel as a single non-draggable card with a "locked from day N" provenance label. User can still unlock by going back to day N and re-picking.

## §5.8 Slot grouping in the candidates panel

- Web UI candidates panel (§5.6) groups cards by these 6 slot names.

**Canonical day slot list** (every day's `options[]` and timeline are organized around these 6 slots, in this sequential order):

1. `breakfast` — meal slot. Min 2 candidates (§5.7 A). **Time NOT fixed** — no hardcoded clock hour; the timeline places it based on the day's first activity, not on a fixed 08:00.
2. `morning_activity` (上午行程) — single slot. Candidates may be drawn from `attractions`, `cafe`, `shopping`, `entertainment`, depending on the day's plan; surfaced together in this one slot.
3. `lunch` — meal slot. Min 2 candidates.
4. `afternoon_activity` (下午行程) — single slot. Same candidate pool rule as `morning_activity`.
5. `dinner` — meal slot. Min 2 candidates.
6. `evening_activity` (晚间活动) — single slot. Same candidate pool rule as `morning_activity` (typically `entertainment` / `cafe` / `shopping`).

## §5.9 A. Flexible-time UI

- The 6 named slots from §5.8 (`breakfast`, `morning_activity`, `lunch`, `afternoon_activity`, `dinner`, `evening_activity`) define **sequence and category**, NOT clock hours.
- No slot has a hardcoded scheduled hour. The timeline shows items in user-arranged order; clock times are derived from (a) the user's drop position on the timeline canvas, OR (b) durations rolling forward from a single anchor (e.g. day-start time the user sets).

## §5.9 B. Drag-drop loading + failure UI

- Web UI behavior:
  - On every drag-drop reorder, insert, or removal that changes adjacency between two timeline items, the front-end fires a backend request naming the (from_poi, to_poi, mode) tuple.
  - The backend (delegated to `timeline` since it is on the gaode allowlist per §5.1) calls gaode-maps live and returns the segment (duration / distance / mode-detail / polyline if applicable).
  - The result is cached in a per-session or per-day cache keyed by `(from_poi_id, to_poi_id, mode)` so a re-drop of the same pair does not re-hit gaode.
- Loading state: while a freshly dropped pair is being computed, the connection between items shows a transient "computing…" indicator; UI does not block other interactions.
- Failure mode: if gaode call fails, the segment renders as "unknown — retry" with a one-click retry; the user can still save the day, the segment metadata simply records `status: "unresolved"`.

## §5.10 D. Live budget panel UI integration

**D. UI integration**

- A persistent budget panel is visible while editing a day; it updates within ~100 ms of any UI event. (Soft target — not a strict acceptance criterion.)
- A trip-level total is visible across all days (e.g. in a header or sidebar) and updates when any day changes.
- If a slot's selected option lacks a cost field (data hole), the panel marks that line `cost: unknown` and continues — does not blank the total.

## §5.11 PDF format & layout

**A. PDF export (printable / share-friendly itinerary)**

- One PDF for the entire trip, paginated by day (one day starts on a new page).
- Per-day content: day header (date + city), the 6 slot sequence with times, each item's name + image thumbnail + brief description + cost, intra-city travel segments between items (mode + duration), inter-city transportation segments on city-change days, accommodation card, per-day total cost.
- Trip-level header: trip title, traveler names, dates, trip total cost, mini map of cities visited (optional — if no map renderer is wired, omit; do not call gaode for the map since `pdf` exporter is not on the allowlist).
- Trip-level footer: index / table of contents linking to each day.
- Format choice: A4 portrait by default, single column. Chinese + English mixed text must render correctly (CJK font embedded).
- Trigger: a "Export PDF" button in the web UI; outputs a downloadable file. CLI parity: `python3 scripts/export-pdf.py --trip <trip-id>`.
- Out of scope: editable PDF forms; all output is read-only.

**B. iCal export (.ics for calendar apps)**

- Trigger: "Export iCal" button in the web UI; CLI parity: `python3 scripts/export-ical.py --trip <trip-id>`.

## §5.13 B. Web UI consequences for skipped slots

**Web UI consequences**: skipped slots render as a muted "skipped — reason" placeholder in the candidates panel; user can un-skip by drag-drop, which fires a re-research request to the appropriate content agent for that slot.

## §5.13 D. Web app — UI behaviors and mobile

2. **Save semantics** — **autosave** on every committed UI mutation (drop, reorder, slot selection change, manual edit), with a 300 ms debounce window per day to coalesce rapid edits. A "saved <Nm ago>" indicator in the header. Explicit "Save now" button forces immediate flush. No "discard" — unwanted changes are reverted via undo (out of scope; deferred).

5. **Concurrent edits / multi-tab** — last-writer-wins with a soft warning. The server tracks `current_editor_session` in `meta.json`; if a save arrives from a session that doesn't match, the server accepts but emits a `409-soft` response, and the UI shows a yellow banner "Another tab edited this trip — refresh to see latest." No automatic merge.

6. **Async race (lazy route stale results)** — every routing request carries a monotonic `request_seq` per (from_poi, to_poi) pair. The UI ignores responses whose `request_seq` is lower than the latest committed for that pair. The server does not need to know about this; it is a UI-side filter.

8. **Mobile drag-drop** — required to work on touch devices; use HTML5 Pointer Events or a touch-aware drag-drop library (dev-plan picks). On screens narrower than 640 px, the candidates panel collapses behind a tab; drag-drop replaced by tap-to-select + tap-to-place workflow that emits the same mutations as drag-drop.

9. **Offline mode** — explicitly **out of scope**. If the server is unreachable, the UI shows a banner "Offline — changes paused" and disables editing controls until reconnect. No local queue.

10. **Validation feedback in UI** — when validators (§5.13 B) reject a state, the UI shows the failing slot in red with the validator's error message inline and disables export until resolved. Skip-state edits that would leave a hard-error (e.g. all three meals skipped) are rejected at the UI level before reaching the server.

## §5.12 — UI scope vs legacy

- The new web UI does NOT need a legacy renderer — old trips keep their existing static HTML; the new UI only handles trips authored by the new pipeline.
