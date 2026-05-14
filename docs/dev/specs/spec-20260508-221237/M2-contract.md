# M2 Contract — spec-20260508-221237

> Locked schema, state machine, day-type tolerance, and 5-endpoint API shape for
> the options-first day-planning system. Authoritative reference for M3-M7
> dev workers.

**Schema version**: `v2.0`
**Task**: `20260514-103616`
**Author cycle**: 2026-05-14

---

## 1. Per-trip on-disk layout (Q3a)

```
data/<trip_id>/
  meta.json                      # trip-level metadata, schema_version, legs
  days/
    day-01.json                  # one file per day; schema = v2 day.schema.json
    day-02.json
    ...
  transportation.json            # inter-city segments with owning_day = depart_day
  route_cache.json               # lazy /api/route results, keyed by from:to:mode
  exports/
    <trip_id>.pdf                # M6 output
    <trip_id>.ics                # M6 output
  cache/
    images/                      # M3 content agents populate; M6 PDF reads only
```

Legacy trips under `data/<trip>/{meals,attractions,...}.json` are NOT loaded by the
new pipeline (§5.12). Legacy renderer `scripts/generate-html-interactive.py` keeps
serving those for read-only viewing.

---

## 2. Schema files

All v2 schemas live in `schemas/v2/`. They are JSON Schema 2020-12 documents.
Cross-slot semantics that JSON Schema cannot express live in
`scripts/lib/trip_contract/`.

| File | Used for |
|---|---|
| `schemas/v2/poi-common.schema.json` | shared `$defs` (city_context, slot_envelope, option_base, provenance) |
| `schemas/v2/day.schema.json`        | one `data/<trip>/days/day-NN.json` |
| `schemas/v2/meta.schema.json`       | `data/<trip>/meta.json` |
| `schemas/v2/transportation.schema.json` | `data/<trip>/transportation.json` |
| `schemas/v2/route_cache.schema.json` | `data/<trip>/route_cache.json` |
| `schemas/v2/budget.schema.json`     | in-memory `/api/budget/recompute` response shape |
| `schemas/v2/timeline.schema.json`   | per-day timeline items returned by M3 timeline agent |
| `schemas/v2/meals.schema.json`      | option category extension (composes option_base) |
| `schemas/v2/accommodation.schema.json` | ditto |
| `schemas/v2/attractions.schema.json` | ditto |
| `schemas/v2/cafe.schema.json`       | ditto |
| `schemas/v2/entertainment.schema.json` | ditto |
| `schemas/v2/shopping.schema.json`   | ditto |

The legacy per-agent envelope schemas under `schemas/*.schema.json` (without `v2/`)
remain valid until M3 migrates content agents.

**Category schemas role**: the per-category v2 schemas (`meals.schema.json`,
`accommodation.schema.json`, etc.) are documented option-shape REFERENCES used
by M3 content agents for self-validation and for IDE autocomplete. The runtime
v2 day validator (`scripts/lib/trip_contract/validators.py`) only enforces
`option_base` shape; per-category extension fields (cuisine, accommodation_type,
etc.) are NOT cross-validated against the slot's `slot_id`. M3 content agents
own the category-vs-slot consistency check (e.g. dinner option must extend
meal_item with `meal_kind="dinner"`) when emitting per-day files.

---

## 3. The `option` shape (locked Q3c)

Every option in `slot.options[]` is an `option_base` (poi-common.schema.json) plus
the category-specific extension. Required fields:

| Field | Type | Required |
|---|---|---|
| `option_id` | string slug | yes |
| `name` | string | yes |
| `name_local` | string | optional |
| `location_summary` | string | yes |
| `coordinates` | `{lat,lng}` | optional but recommended |
| `cost` | number or null | yes (null renders as "cost: unknown") |
| `currency_local` | ISO 4217 | optional (inherits from meta) |
| `fit_score` | number 0..1 | yes |
| `why_fits_user` | string | yes |
| `source_agent` | enum | yes |
| `source_citation` | array | optional |
| `city_context` | object | YES — locked Q3c |
| `provenance` | object | set when selected |
| `is_home` | bool | optional |

### `city_context` (codex Q1: per-OPTION not per-slot)

```jsonc
{
  "city_id": "lijiang",                 // canonical slug
  "city_name": "Lijiang",
  "leg_index": 1,                       // index into meta.legs[]
  "role": "destination",                // origin | destination | en_route | overnight
  "valid_after_ts": "2026-06-03T15:30:00+08:00",   // optional
  "valid_before_ts": "2026-06-02T22:30:00+08:00"   // optional
}
```

Codex Q1 rationale: city-change / transit / red-eye days routinely contain
options with DIFFERENT roles (one option in origin city before departure, another
in destination city after arrival). Hoisting to slot-level loses this granularity.

### `provenance`

```jsonc
{
  "selected_by": "user|auto|locked-from-day-N|system",
  "selected_reason": "fit_score=0.91; tied=false",
  "selected_at": "2026-05-14T11:00:00+08:00",
  "locked_from_day": null               // integer when selected_by == 'locked-from-day-N'
}
```

---

## 4. The `slot` envelope

Every slot — the 6 named time-slots PLUS the orthogonal `accommodation` slot —
is the same shape:

```jsonc
{
  "slot_id": "lunch",                   // enum: 6 named + 'accommodation'
  "options": [ /* option_base[] */ ],
  "selected_option_id": "l1" | null,
  "skipped": false,
  "skipped_reason": null,               // required non-null when skipped=true
  "late_arrival_placeholder": false     // dinner-only marker
}
```

The 6 named slots (§5.8): `breakfast`, `morning_activity`, `lunch`,
`afternoon_activity`, `dinner`, `evening_activity`. All 6 keys MUST be present
on every day file even when `skipped=true`; this prevents silent omission.

### Floors (§5.7 A/B)

| Slot | Floor |
|---|---|
| each non-skipped meal slot | `options.length >= 2` |
| per-day total across non-skipped meals | `>= 2 * non_skipped_count` (so 3 active meals = 6) |
| first-night accommodation | `options.length >= 3` |
| same-city night N+1 accommodation | auto-locked to N's selection (§5.7 B) |

### Skip semantics (Q3b)

| Condition | Required slot state |
|---|---|
| `arrival_ts >= 13:30` | `lunch.skipped=true, skipped_reason='pre-arrival'` |
| `arrival_ts >= 16:00` | `afternoon_activity.skipped=true, skipped_reason='pre-arrival'` |
| `arrival_ts >= 21:00` | `dinner.skipped=false, late_arrival_placeholder=true` (NOT skipped — codex Q3 correction) |
| `day_type='transit-only'` | every slot `skipped=true, skipped_reason='in-transit'` |
| `day_type='red-eye'` | accommodation may be `skipped=true, reason='red-eye-spans-prior-day'` |
| `day_type='buffer'`  | discretionary skips allowed with `skipped_reason='buffer-rest'` |

### `skipped_reason` enum (closed)

`pre-arrival | post-departure | in-transit | city-change | red-eye-spans-prior-day | user-omit | buffer-rest`

Validator REJECTS any other value (`SKIPPED_REASON_INVALID`).

---

## 5. Day-type tolerance (§5.13 B)

| `day_type` | Typical pattern |
|---|---|
| `normal` | all 6 slots active; no required skips |
| `arrival` | breakfast/morning pre-arrival; lunch/afternoon by threshold |
| `departure` | dinner/evening post-departure if depart < 17:00 / 19:00 |
| `city-change` | departure side has NO required skips (after arrival, destination slots are LIVE); only arrival-side skips apply |
| `red-eye` | accommodation may be skipped; evening_activity is the airport transfer |
| `transit-only` | all 6 slots `in-transit` skipped |
| `buffer` | rest day; discretionary skips with `buffer-rest` |

The validator computes EXPECTED skips from `day_type + arrival_ts + departure_ts`
and rejects mismatches as `MISSING_REQUIRED_SKIP` or `UNJUSTIFIED_SKIP`. It NEVER
auto-mutates (codex Q3 correction).

---

## 6. State machine (§5.2)

```
draft-options -> user-review -> user-selected -> timeline -> transportation -> finalized
```

Field: `day.stage`. Per-day, NOT per-trip (codex Q2).

### Gating rules

- **Forward transitions**: always allowed.
- **Backward transitions**: forbidden unless `has_user_consent=True` (only the
  M4 server may set this; the API exposes an explicit demote action).
- **Trip-level rollups** (codex Q2 correction):
  - `blocking_stage(days) = min(day.stage)` — used to GATE pipeline advancement.
    Timeline cannot run until ALL days reach `user-selected`.
  - `furthest_stage(days) = max(day.stage)` — for DISPLAY ONLY; never for gating.
- **Demote semantics**: editing a finalized day demotes ONLY that day plus
  invalidates adjacent route_cache entries and transportation segments touching
  it. Other finalized days remain finalized.

### Stage gate enforcement (validator rule `STAGE_GATE_VIOLATION`)

When `day.stage` is in `{user-selected, timeline, transportation, finalized}`,
every non-skipped slot (including accommodation) MUST have
`selected_option_id != null`, AND that id MUST exist in `slot.options[]`
(rule `SELECTED_OPTION_ID_NOT_IN_OPTIONS`). Slot option_ids must be unique
within the slot (rule `OPTION_ID_DUPLICATE`).

### Demote-edit dependency calculation (M4 server contract)

When the user re-edits a finalized day N, the server MUST:
1. Demote `day_N.stage` from finalized -> user-selected (or earlier per the
   user action) using `validate_state_transition(..., has_user_consent=True)`.
2. Invalidate intra-day route_cache entries where `from_option_id` or
   `to_option_id` references any option_id in day N.
3. Invalidate transportation segments with `owning_day == N` AND segments where
   `arrive_day == N` (the cross-day arrivals).
4. If day N's accommodation was selected via `selected_by="locked-from-day-N"`
   and the source day's selection just changed, re-propagate the lock to N.
5. Day N+1...end remain finalized; ONLY day N demotes. The server MAY surface
   a UI banner ("This change affected day N; downstream days are still finalized
   but may need review") but it does not auto-demote them.

This dependency rule lives here in M2 contract so M4 implements it consistently.

---

## 7. Inter-city transportation (§5.13 B red-eye rule)

Schema: `schemas/v2/transportation.schema.json`. File: `data/<trip>/transportation.json`.

`pick_owning_day(segment) === segment.depart_day` (cp-07). A segment with
`depart_ts` on Day N and `arrive_ts` on Day N+1 is attributed to Day N for
budget+timeline+PDF+iCal. Day N+1 renders a read-only "arriving from prior day"
header item with no duplicate budget contribution.

Validator rule: `OWNING_DAY_NOT_DEPART_DAY` if `owning_day != depart_day`.

---

## 8. Lazy intra-city routing (§5.9; supersedes all-pairs matrix)

NO precompute. The `intra_city_routes` map on a day file is lazily populated by
`POST /api/route` calls fired on user drag-drop. The route_cache file is keyed
by `<from_option_id>:<to_option_id>:<mode>` and survives across sessions.

Cache invalidation: any POI coordinate change invalidates entries referencing
that option_id.

---

## 9. The 5 API endpoints (§5.13 D #7)

Server-side dataclasses live in `scripts/lib/trip_contract/api_contract.py`.
M4 server (`scripts/serve-trip.py`) implements; M3 timeline.md / budget.md
consume the route_pair / recompute_day signatures.

### `POST /api/route` (lazy intra-city)

```jsonc
// REQUEST
{
  "trip_id": "fixture-trip",
  "day": 3,
  "from_option_id": "aa1",
  "to_option_id": "d1",
  "mode": "walk",
  "request_seq": 7
}
// RESPONSE
{
  "request_seq": 7,
  "status": "ok",        // ok | unknown | error
  "segment": { "duration_min": 12, "distance_km": 0.9, "polyline": "..." }
}
```

UI ignores any response with `request_seq < latest_seen_seq` for that pair
(monotonic ordering avoids stale-paint races).

### `POST /api/budget/recompute`

```jsonc
// REQUEST
{ "trip_id": "fixture-trip", "day": 3, "delta": null }
// RESPONSE
{
  "schema_version": "v2.0",
  "trip_id": "fixture-trip",
  "trip_total": 8420.00,
  "currency_local": "CNY",
  "days": [
    {
      "day": 3,
      "day_total": 1820.00,
      "breakdown": {
        "meals": { "amount": 380, "unknown_count": 0 },
        "accommodation": { "amount": 600, "unknown_count": 0 },
        "transportation": { "amount": 540, "unknown_count": 0 }
      }
    }
  ]
}
```

Server is single-writer. Recompute < 100ms typical (§5.10).

### `POST /api/save` (autosave)

```jsonc
// REQUEST (debounced 300ms client-side)
{
  "trip_id": "fixture-trip",
  "day": 3,
  "editor_session": "sess-abc-123",
  "mutations": [
    { "type": "select", "slot": "lunch", "option_id": "l2" },
    { "type": "drag-drop", "extra": { "from_pos": 2, "to_pos": 4 } }
  ]
}
// RESPONSE (200 OK)
{ "saved_ts": "2026-05-14T11:23:00+08:00", "conflict": null }
// RESPONSE (409 soft-conflict)
{ "saved_ts": "2026-05-14T11:23:00+08:00", "conflict": "409-soft" }
```

`current_editor_session` mismatch -> `409-soft`; UI shows yellow banner
"Another tab edited this trip — refresh to see latest" (§5.13 D #5).

### `GET /api/trip/<trip_id>` (full hydration on page load)

```jsonc
{
  "meta": { /* meta.json content */ },
  "days": [ /* day-NN.json contents */ ],
  "transportation": { /* transportation.json */ },
  "route_cache": { /* route_cache.json */ }
}
```

### `POST /api/export/{pdf|ical}`

```jsonc
// REQUEST
{ "trip_id": "fixture-trip" }
// RESPONSE (202 Accepted; exporters run out-of-band)
{ "file_path": "data/fixture-trip/exports/fixture-trip.pdf", "bytes_written": 287541 }
```

Exporters run with `agent_id="pdf-export"` or `"ical-export"` — NOT in the
gaode allowlist, so they MUST consume only `route_cache.json` (no live gaode
calls). M5 hook verifies zero deny events from exporter agent_ids.

---

## 10. Validator rule catalog

All rules implemented in `scripts/lib/trip_contract/validators.py`. Run via
`scripts/plan-validate-v2.py` (or `scripts/plan-validate.py --v2` which
forwards). Codes are stable for downstream tooling.

| Code | Severity | Trigger |
|---|---|---|
| `LEGACY_SHAPE_FORBIDDEN` | error | `{primary, alternatives[]}` anywhere in payload |
| `SCHEMA_VERSION_MISMATCH` | error | top-level `schema_version != "v2.0"` |
| `SLOT_REQUIRED_PRESENT` | error | one of 6 named slots or `accommodation` absent |
| `SKIPPED_REASON_REQUIRED` | error | `skipped=true` with null `skipped_reason` |
| `SKIPPED_REASON_INVALID` | error | `skipped_reason` not in canonical enum |
| `MISSING_REQUIRED_SKIP` | error | `day_type+arrival_ts` mandates skip; slot is non-skipped |
| `UNJUSTIFIED_SKIP` | error | slot skipped but `day_type` does not require it (use `user-omit` / `buffer-rest`) |
| `LATE_ARRIVAL_DINNER_NOT_SKIPPED` | error | dinner skipped when arrival_ts >= 21:00 (should be late_arrival_placeholder instead) |
| `LATE_ARRIVAL_PLACEHOLDER_REQUIRED` | error | arrival_ts >= 21:00 without dinner.late_arrival_placeholder=true |
| `MEAL_SLOT_FLOOR` | error | non-skipped meal slot has `len(options) < 2` |
| `MEAL_DAY_FLOOR` | error | total options across non-skipped meals < `2 * non_skipped_count` |
| `ACCOMMODATION_FIRST_NIGHT_FLOOR` | error | first-night accommodation has < 3 options |
| `STAGE_GATE_VIOLATION` | error | stage >= user-selected with non-skipped slot lacking `selected_option_id` |
| `CITY_CONTEXT_REQUIRED` | error | option missing `city_context` |
| `CITY_CONTEXT_ROLE_INVALID` | error | role not in `{origin, destination, en_route, overnight}` |
| `FIT_SCORE_OUT_OF_RANGE` | error | fit_score not in [0,1] |
| `WHY_FITS_USER_REQUIRED` | error | option missing `why_fits_user` rationale (Q3h) |
| `SOURCE_AGENT_REQUIRED` | error | option missing `source_agent` |
| `OWNING_DAY_NOT_DEPART_DAY` | error | transportation segment owning_day mismatch |
| `LEGS_NOT_CONTIGUOUS` | error | meta.legs not contiguous from day 1 |
| `LEG_INVERTED` | error | leg.last_day < leg.first_day |
| `LEGS_DAY_COUNT_MISMATCH` | error | sum of leg days != meta.day_count |
| `DAY_LEG_INDEX_MISMATCH` | error | day.leg_index does not match meta-derived leg |
| `SAME_CITY_ACCOMMODATION_DRIFT` | warning | day N+1 same-city as N but selected different accommodation |

---

## 11. Public Python API

```python
from scripts.lib import trip_contract as tc

# Constants
tc.SCHEMA_VERSION       # "v2.0"
tc.STAGES               # ['draft-options', ..., 'finalized']
tc.NAMED_SLOTS          # 6 named time-slots
tc.SKIP_THRESHOLDS      # Q3b thresholds

# Loaders
bundle = tc.load_trip(Path("data/my-trip"))
day = tc.load_day(Path("data/my-trip"), 3)

# State machine
err = tc.validate_state_transition("draft-options", "user-selected")
gate = tc.blocking_stage(bundle.days)
all_ready = tc.all_days_at_least(bundle.days, "user-selected")

# Day-type
expected = tc.expected_skips_for_day(day)
skipped = tc.is_slot_skipped(day, "lunch")

# Transportation
own_day = tc.pick_owning_day(segment)

# Validators
errs = tc.validate_day_v2(day, bundle.meta, position="$.days[3]", is_first_night=False)
errs = tc.validate_trip_v2(bundle)

# Legacy detection
legacy_paths = tc.detect_legacy_shape(any_obj)

# API contract dataclasses (M4 server)
from scripts.lib.trip_contract.api_contract import RouteRequest, BudgetResponse
```

---

## 12. Test fixtures

Six fixtures under `tests/fixtures/trip-contract/`:

| File | Day-type | Validator outcome |
|---|---|---|
| `meta.json`              | trip meta            | PASS |
| `normal-day.json`        | normal day-1         | PASS |
| `arrival-day.json`       | arrival 15:30        | PASS |
| `city-change-day.json`   | depart 08:30 / arrive 11:00 | PASS |
| `red-eye-day.json`       | depart 22:30         | PASS |
| `late-arrival-day.json`  | arrival 21:30        | PASS |
| `legacy-shape-day.json`  | smuggled `{primary, alternatives[]}` | FAIL with `LEGACY_SHAPE_FORBIDDEN` |

Run: `python3 -m pytest tests/test_trip_contract_fixtures.py -v` or
`python3 scripts/plan-validate-v2.py --fixtures`.

---

## 13. Phase B consumer guide

| Worker | Reads | Writes |
|---|---|---|
| **M3 (agents+orchestrator)** | this doc + `scripts/lib/trip_contract/` API | content agents emit `slot.options[]` per the option_base shape; plan.md gates pipeline on `blocking_stage(days) >= 'user-selected'`; --auto sets `provenance.selected_by='auto'` |
| **M4 (web app)** | this doc §9 API + `scripts/lib/trip_contract/api_contract.py` dataclasses | implements 5 endpoints; uses `tc.load_trip` to hydrate; uses `tc.validate_state_transition(..., has_user_consent=True)` on demote actions |
| **M5 (harness)** | this doc §11 (server agent_id) | extends `pretool-gaode-policy.py` to deny when agent_id missing/unknown on /api/route paths |
| **M6 (exporters)** | `tc.load_trip` + `tc.pick_owning_day` for red-eye | reads route_cache only; never calls gaode |

---

## 14. Decisions index (locked from BA ticket Q3)

| ID | Decision |
|---|---|
| Q3a | per-day file boundary; `data/<trip>/{meta.json, days/day-NN.json, transportation.json, route_cache.json, exports/, cache/images/}` |
| Q3b | lunch skip >=13:30; afternoon skip >=16:00; dinner late-arrival placeholder >=21:00 |
| Q3c | city_context mandatory on EACH option (codex Q1 confirms) |
| Q3d | undo/redo deferred |
| Q3e | local-only no-auth; bind 127.0.0.1; current_editor_session is concurrency identity, NOT auth |
| Q3f | PDF reads images from `data/<trip>/cache/images/` only; placeholder for missing |
| Q3g | empty state: skipped=muted; required-empty=red+error+export-disabled; route=unknown->retry; cost=line continues |
| Q3h | rationale required (`fit_score` + `selected_reason`); diff view deferred; bulk override deferred |
| Q3i | explicit per-day "Approve day selections & build timeline" button; drag/drop alone does NOT advance stage |
| Q3j | planning entry `/plan "<req>" [--auto]`; web review via `python3 scripts/serve-trip.py --trip <id>` |

---

## 15. Codex consultation summary

Consulted gpt-5.5 xhigh BEFORE writing code. Picks adopted:
1. `city_context` per-OPTION (not slot-level) — option is the atomic unit.
2. Per-day `day.stage`; gating uses `min(day.stage)`, NOT `max`.
3. Validator REQUIRES explicit `skipped:true` + matching reason; never auto-mutates.
   Dinner >=21:00 is `late_arrival_placeholder`, NOT `skipped`.
4. Keep legacy agent-envelope schemas valid in M2; v2 schemas are SEPARATE.
   `LEGACY_SHAPE_FORBIDDEN` applies only to v2-context documents.

See dev-report-20260514-103616-m2.json `codex_consult` field for full feedback.
