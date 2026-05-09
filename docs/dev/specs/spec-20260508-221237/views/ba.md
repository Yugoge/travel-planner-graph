<!-- AUTO-GENERATED VIEW for ba | source: docs/dev/specs/spec-20260508-221237.md | extracted: 2026-05-09T00:00:00Z -->

# ba view of spec-20260508-221237

**Monolith**: docs/dev/specs/spec-20260508-221237.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

> Verbatim requirement (zh): all subagents EXCEPT `timeline` and `transportation` (inter-city transport) must be **systematically and completely** prohibited from invoking any gaode-maps skill (高德地图 / amap). Enforcement is required at **TWO** layers:

> Verbatim requirement (zh): the underlying logic of travel-planner is to be changed so that:

---

## Section 1: Before

<!-- WHO WRITES: PM (autonomous mode) or User (user-spec mode) or BA (if Section 1 empty and BA has context) -->
<!-- WHAT: Screenshot path + text description of the current state BEFORE any fix attempt. -->
<!-- This establishes the baseline so later cycles can compare. -->

### Cycle 1

**A. Current gaode-maps access surface**

- Skill definition: `/root/travel-planner/.claude/skills/gaode-maps/skill.md` (user-invocable: true; allowed_tools = `Task, Read, Bash`).
- **Critical**: in subagent context, gaode-maps is NOT invoked through the `Skill` tool — agents shell out via Bash to scripts under `/root/travel-planner/.claude/commands/scripts/gaode-maps/scripts/*.py` (e.g. `poi_search.py`, routing scripts). A Skill-matcher hook alone would NOT block current usage.
- Agents that currently reference gaode-maps in their prompt (must be banned except where allowlisted):
  - `transportation.md` — KEEP (allowlist; lines 88-94 use Gaode routing for inter-city; SECONDS→minutes conversion warning).
  - `meals.md` (lines 83-84) — BAN.
  - `attractions.md` (lines 82-85, category code `110000`) — BAN.
  - `accommodation.md` — BAN.
  - `cafe.md` — BAN.
  - `entertainment.md` — BAN.
  - `shopping.md` — BAN.
  - `timeline.md` (lines 312-440) — KEEP (allowlist; intra-city `travel_segments` API-driven).
- Current harness enforcement: NONE per-skill. `.claude/hooks/pretool-subagent-enforce.py` enforces workflow-phase sequencing (Gate 4) but does not gate skill/script names.

**B. Current planning flow (single-plan, post-hoc review — opposite of target)**

- Entrypoint: `.claude/commands/plan.md`.
  - Phase 1 — BA requirement + skeleton.
  - Phase 2 — skeleton init + validation.
  - **Phase 3 (Step 8)** — 6 content agents run in parallel; `transportation` runs alongside them (NOT as a downstream step).
  - **Phase 3 (Step 10)** — `timeline` runs serially **after** all content agents, automatically. No user approval required before timeline runs.
  - **Phase 4 (lines 668-856)** — day-by-day USER REVIEW happens AFTER timeline+transport are already built. User sees the assembled day and can: accept / request changes (re-invokes content agents via Step 15) / accept-all-remaining.
- Output shape:
  - `meals.json` per day: `{breakfast:{primary, alternatives[]}, lunch:{...}, dinner:{...}}`. The `alternatives` field is in the schema but typically empty in real data (e.g. `data/dali-kunming-test-20260504-142555/meals.json`).
  - `attractions / entertainment / shopping / cafe / accommodation`: similar `primary` + optional `alternatives` pattern, but alternatives unpopulated in practice.
  - `transportation.json`: a single optimal option per location-change day (no alternatives surface).
- Mismatch with target flow:
  - Current order = **content → transportation → timeline → user-review** (review is post-hoc).
  - Target order (§5.2) = **content (multi-option) → user-review (selection) → timeline (intra-city) → transportation (inter-city)**.
  - Current `transportation` runs in parallel with content agents; target makes it strictly downstream of user selection.
  - Current `timeline` runs before user approval; target makes user approval a hard gate before timeline.
  - `alternatives` field exists for content agents but is treated as optional decoration; target makes multi-option **mandatory** and the basis of the user-selection UI.

---

## Section 5: User's Acceptance Criterion

### 5.1: Systematically forbid gaode-maps skill for all non-geo subagents

> 系统性彻底禁止除了 timeline 和 transport 以外的 subagent 使用任何高德地图 skill。使用 harness 原则，并且在 prompt 中也禁止。

Verbatim requirement (zh): all subagents EXCEPT `timeline` and `transportation` (inter-city transport) must be **systematically and completely** prohibited from invoking any gaode-maps skill (高德地图 / amap). Enforcement is required at **TWO** layers:

1. **Harness layer (authoritative)**: a PreToolUse hook MUST block any `Skill` tool call whose skill name matches `gaode-maps*` / `scripts:gaode-maps*` when the calling subagent is not in the allowlist `{timeline, transportation}`. Harness rejection is the source of truth — prompt rules alone are insufficient (see global lessons §11, "must explicitly list what is FORBIDDEN, not just what is allowed").
2. **Prompt layer (defense-in-depth)**: every affected agent definition file under `.claude/agents/` MUST contain an explicit `## DO NOT` section naming `gaode-maps` / `高德地图` / `scripts:gaode-maps*` as forbidden, with the rationale and the allowed alternatives (e.g., rednote for content discovery; google-maps where applicable).

**Allowlist (only these two agents may call gaode-maps skills)**: `timeline`, `transportation`.

**Out-of-scope agents (must be banned)**: `meals`, `attractions`, `accommodation`, `cafe`, `entertainment`, `shopping`, `ba`, `qa`, `dev`, `pm`, `product-owner`, `ui-specialist`, `budget`, `user`, plus any other agent not on the allowlist (default-deny).

### 5.2: Refactor day-planning flow to options-first / user-selection-gated

> 然后修 travel-planner 的底层逻辑为，meals 等实际业务 agent 应该为每一个计划提供较多的选择，然后在每一天 Plan/review 的时候全面展示然后由用户选择，最后由用户同意之后呼唤 timeline 制作时间线设计市内交通和 transport agent 设计（市际）交通。

Verbatim requirement (zh): the underlying logic of travel-planner is to be changed so that:

1. **Content agents produce multiple options, not a single pick.** Each business / content subagent (`meals`, `attractions`, `accommodation`, `cafe`, `entertainment`, `shopping`) MUST return **several** candidate options for every slot/plan they own — not a single locked-in recommendation. Minimum count and option schema to be defined in the dev plan; default expectation: ≥3 options per slot where the candidate pool exists, with each option carrying enough metadata (name, location summary, why-fits-user, rough cost, source citation) for the user to choose.
2. **Day-level Plan/review presents all options.** During each day's Plan/review step, ALL options across all slots are surfaced to the user in a unified, scannable view. This is the user-facing decision surface.
3. **User selection is a hard gate.** No downstream timing/routing work runs until the user explicitly picks one option per slot (or accepts a default).
4. **After user approval, timeline + transportation are invoked in sequence:**
   - `timeline` agent: builds the day's chronological timeline AND designs **intra-city** (市内) transit between the user-chosen items.
   - `transportation` agent: designs **inter-city** (市际) transport segments (HSR, flights, long-distance ground) on days that change cities.
5. The two geo agents (`timeline`, `transportation`) are the ONLY agents permitted to call gaode-maps (cross-reference §5.1).

### 5.5: `--auto` planning mode (agent-decides, no user gating)

> 同时增加 --auto 模式，就是 agent 自己决定。

Add an `--auto` flag (or equivalent) to the planning entrypoint that bypasses the user-selection gate from §5.2:

- In `--auto` mode, content agents still return `options[]` per slot (multi-option output is mandatory regardless of mode — the web UI depends on it; see §5.6).
- The agent layer (or orchestrator) auto-picks one option per slot using a documented selection policy (e.g. highest-ranked / cheapest / nearest / matches user-profile heuristics — exact policy decided in dev-plan).
- After auto-pick, `timeline` and `transportation` run as in §5.2's post-selection branch — the rest of the pipeline is unchanged.
- `--auto` selections are recorded with provenance: `selected_by: "auto"` plus the rule that fired, so a human can audit and override later in the web UI.

Default mode (without `--auto`) remains the user-gated flow from §5.2.

### 5.7: User-confirmed parameters (2026-05-09 follow-up)

User answered 4 of 5 outstanding parameter questions in plain language. Captured here verbatim with the operationalization the spec is committing to.

**A. Per-slot option floor — meals**
> 每天至少6家餐厅，早餐午餐晚餐每一顿至少两家

- Per-meal floor: `breakfast.options[].length >= 2`, `lunch.options[].length >= 2`, `dinner.options[].length >= 2`.
- Per-day total floor across the three meal slots: `>= 6` distinct restaurants per day.
- Validator must enforce both the per-slot AND per-day totals; a day failing either fails plan validation.

**B. Per-slot option floor — accommodation, with same-city auto-lock**
> 每晚至少3家酒店推荐，但是同一个地方默认使用同一家酒店，比如我在day5选了酒店A，那么day 6在同一个城市我的酒店就锁定

- For the FIRST night in a city: `options[].length >= 3` distinct hotels surfaced to user.
- "Same city" continuation rule: if day N's accommodation is in city X and day N+1 stays in city X, day N+1's accommodation slot auto-locks to the day-N selection (no re-prompt, no candidate panel for that slot).
- City-change detection key: city name on the skeleton (or stay-block boundary). When the city changes, the next night re-opens the 3-option choice.
- Web UI (§5.6): on locked nights, the candidates panel for accommodation is hidden or shows the locked hotel as a single non-draggable card with a "locked from day N" provenance label. User can still unlock by going back to day N and re-picking.
- `--auto` mode (§5.5) follows the same lock — auto-pick once on the first night, propagate across same-city continuation.

**C. Old trip data backwards-compatibility**
> 不管

- User explicitly does NOT care about migrating existing trip data (e.g. `data/china-20260412-092624/`). Dev may pick whichever path is cheapest:
  - auto-shim (`primary → options=[primary], selected=true, selected_by="legacy"`), OR
  - one-shot migration script + halt, OR
  - mark old trips read-only and don't load them into the new pipeline at all.
- No acceptance test on legacy data is required. Spec is silent on this except to confirm it is out of scope.

**D. `--auto` selection policy**
> 最符合用户需求的

- Primary sort key: best match to the user's profile / requirement context — i.e. the same "fit-to-user" reasoning that the content agent already produces per option (the `why-fits-user` justification field).
- Operational definition: each `option` carries a numeric or rank-ordered "fit score" derived from the agent's matching logic against the user's stated requirements + memory profile (Matilde+Jade INFJ / 文艺温馨 / no-touristy-chains, etc.). `--auto` picks the option with the highest fit score per slot.
- Tie-breakers (in order): cost (cheaper wins), distance to current base (nearer wins).
- Provenance: `selected_by: "auto"`, plus `selected_reason: "fit_score=<n>; tied=<bool>; tiebreaker=<key>"`.

**E. All-pairs intra-city matrix size cap — UNRESOLVED**

User has not yet answered. Default placeholder pending confirmation: cap candidates at 5 per slot to bound matrix size, OR compute matrix lazily (only on user drag-drop). Final value to be locked before dev-plan.

### 5.8: Day slot model — 6 fixed slots per day, bounded candidate space, E resolved

User clarification (2026-05-09):
> 早餐一个槽位（但是时间不要fixed）只有两个2，上午的行程一个槽位，午餐一个槽位，下午一个槽位，晚餐一个槽位，晚间活动一个槽位，实际上可能性没有那么多

**Canonical day slot list** (every day's `options[]` and timeline are organized around these 6 slots, in this sequential order):

1. `breakfast` — meal slot. Min 2 candidates (§5.7 A). **Time NOT fixed** — no hardcoded clock hour; the timeline places it based on the day's first activity, not on a fixed 08:00.
2. `morning_activity` (上午行程) — single slot. Candidates may be drawn from `attractions`, `cafe`, `shopping`, `entertainment`, depending on the day's plan; surfaced together in this one slot.
3. `lunch` — meal slot. Min 2 candidates.
4. `afternoon_activity` (下午行程) — single slot. Same candidate pool rule as `morning_activity`.
5. `dinner` — meal slot. Min 2 candidates.
6. `evening_activity` (晚间活动) — single slot. Same candidate pool rule as `morning_activity` (typically `entertainment` / `cafe` / `shopping`).

Plus the orthogonal accommodation slot (§5.7 B), which is per-night, NOT per day-segment, and locks across same-city continuation.

**Implications for the schema and pipeline**:
- Content agents emit candidates **into** one of these 6 named slots, not as free-floating items. `meals` agent owns `breakfast`/`lunch`/`dinner`; `attractions`/`cafe`/`entertainment`/`shopping` agents contribute candidates to `morning_activity`/`afternoon_activity`/`evening_activity` based on what fits each slot.
- `morning_activity`/`afternoon_activity`/`evening_activity` candidates may come from MULTIPLE content agents — the orchestrator merges them into a single per-slot `options[]` array, with each option labeled by its source agent (provenance: `source_agent: "attractions"` etc.).
- Per-slot floor for activity slots: TBD in dev-plan, but the bounded candidate space means small numbers (e.g. 3-5) are sufficient — full flexibility is not needed because slots are pre-typed.
- Web UI candidates panel (§5.6) groups cards by these 6 slot names.

### 5.9: Revision — all slot times are flexible; intra-city routing is lazy/on-demand (supersedes §5.8 E resolution)

User clarification (2026-05-09):
> 所有槽位时间都不固定。算了我们修改为这样子，每一次用户拖动时间轴重新安排之后，都是后台重新获取高德数据实时计算，这样就避免了无效计算

This sub-section **supersedes** the E resolution in §5.8. The all-pairs matrix precompute is REMOVED from the spec; in its place, intra-city travel segments are computed **lazily** at user interaction time.

**A. All slot times are flexible (not just breakfast)**

- The 6 named slots from §5.8 (`breakfast`, `morning_activity`, `lunch`, `afternoon_activity`, `dinner`, `evening_activity`) define **sequence and category**, NOT clock hours.
- No slot has a hardcoded scheduled hour. The timeline shows items in user-arranged order; clock times are derived from (a) the user's drop position on the timeline canvas, OR (b) durations rolling forward from a single anchor (e.g. day-start time the user sets).
- Validators must NOT reject a day for missing fixed-time fields like "breakfast 08:00".
- Existing schemas that assert fixed times for a slot are relaxed: time fields become optional or derived.

### 5.12: No backwards compatibility — supersedes §5.3 backcompat clause

User clarification (2026-05-09):
> 我质疑一点，过去的html没有交互功能即使我们现在彻底架构更新也不会影响过去的trip的！不需要向后兼容！

**Authoritative resolution of the §5.7 C ↔ §5.3 contradiction surfaced by audit:**

- Old trip HTML outputs were **static, non-interactive** documents. They are frozen artifacts and remain viewable as-is regardless of any new architecture. Nothing the new pipeline does breaks them.
- Therefore: **NO backwards-compatibility requirement** for old trip data (e.g. `data/china-20260412-092624/`) into the new options-first pipeline.
- Old trips are NOT loaded into the new code paths. They remain readable via their existing static HTML output, but the new orchestrator / web UI / validators / agents do not need to ingest their schema.

**Explicit overrides of earlier sub-sections:**

- §5.3 bullet "Backwards compatibility with existing trips: `data/china-20260412-092624/` and similar in-flight trip data must continue to load …" — **REVOKED**. Old data is out of scope; no shim, no migration script, no auto-load.
- §5.7 C ("user does not care about migrating existing trip data") is now the authoritative position.

**Operational consequences:**

- Validators for the new schema MAY assume the new shape (per-slot `options[]`, named slots, etc.) and reject any file that doesn't match — they do NOT need a legacy-shape branch.
- The new web UI does NOT need a legacy renderer — old trips keep their existing static HTML; the new UI only handles trips authored by the new pipeline.
- Test suites do NOT need legacy-fixture coverage. Acceptance evidence everywhere may assume "trips authored under the new pipeline."
- If a user wants an old trip re-rendered in the new UI, the answer is "re-run the planner" — no automatic upgrade path is owed.

**Net effect on the spec**: every other clause in this document that implies legacy support is to be read as superseded by §5.12. Future readers should treat old trips as read-only, frozen, and outside the new pipeline's responsibility.

### 5.13: Codex audit follow-up — supersession markers, day-type table, expanded gaode ban, web app persistence contract

User decision (2026-05-09) following codex audit: address must-fix items #1, #3, #4, #5 (item #2 already resolved by §5.12).

#### A. Explicit supersession markers (codex must-fix #1)

The following earlier text is explicitly marked SUPERSEDED so a future implementer or test author does not accidentally implement the obsolete behavior:

- **§5.6 backend block "all-pairs intra-city precompute"** (the bullets that say `timeline` MUST compute the N×N matrix and persist `intra-city-matrix.json`) — **SUPERSEDED by §5.9**. Do NOT implement matrix precompute. Do NOT produce `intra-city-matrix.json`. Do NOT write tests against either.
- **§5.6 acceptance bullet "`intra-city-matrix.json` exists per day and contains entries for all POI pairs in `options[]` ∪ selected items"** — **REVOKED**. Replaced by §5.9 acceptance ("no matrix produced; lazy on-demand routing serves the UI").
- **§5.8 E resolution paragraph "Therefore E is resolved as option E1 by virtue of the slot model… `timeline` precomputes the full N×N intra-city matrix per day"** — **SUPERSEDED by §5.9**. The slot-model description in §5.8 (the 6 named slots, flexible time anchor commentary) remains valid; only the all-pairs matrix portion is dead.
- **§5.8 acceptance bullet "`intra-city-matrix.json` covers all unique POIs that appear in any slot's `options[]` for that day"** — **REVOKED**.

Implementer rule: when §5.6 / §5.8 conflict with §5.9, **§5.9 wins**.

#### B. Day-type behavior table (codex must-fix #3)

The 6-slot model (§5.8) and the user-selection-then-timeline-then-transportation flow (§5.2) MUST tolerate the following day types. For each, the schema admits **skipped** and **N/A** slot states (provenance: `skipped: true` with `reason: "<day-type>"`); validators MUST NOT reject a day for missing slots when the day type explicitly skips them.

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

### 5.3: Cross-cutting constraints

- **Default-deny posture**: both the gaode-maps skill ban (§5.1) and the timeline/transportation gate (§5.2) follow default-deny; new agents added later inherit the ban automatically and inherit the gate automatically (no opt-out without explicit allowlist edit + spec amendment).
- **Backwards compatibility with existing trips**: `data/china-20260412-092624/` and similar in-flight trip data must continue to load; migration logic for any data still in the old single-plan shape must either auto-shim (treat the existing pick as `options=[<existing>]` with `selected=true`) or fail loud with a documented one-shot migration script. Choice between shim and migration script is a dev-plan decision.
- **No emoji in code/comments/commit messages** (project-wide rule, restated for the implementing dev).
- **Auto-commit safety**: changes flow through the `refs/checkpoints/<branch>` mechanism per `docs/checkpoint-mechanism.md`; HEAD master never advances on PostToolUse.
