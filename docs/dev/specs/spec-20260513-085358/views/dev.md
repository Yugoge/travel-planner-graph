<!-- AUTO-GENERATED VIEW for dev | source: docs/dev/specs/spec-20260513-085358.md | extracted: 2026-05-13T09:15:00Z -->

# dev view of spec-20260513-085358

**Monolith**: docs/dev/specs/spec-20260513-085358.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

## Section 2: What Was Attempted

<!-- WHO WRITES: Dev (after each implementation attempt) -->
<!-- WHAT: Per-cycle record of what approach was tried, what the rationale was, and why it failed (if it failed). -->
<!-- This prevents the next cycle's Dev from repeating the same approach. -->

### Cycle 1

_Not yet populated._

## Section 3: What Was Changed

<!-- WHO WRITES: Dev (after each implementation) -->
<!-- WHAT: Exact file changes with line numbers and old->new values. -->
<!-- FORMAT: - **file.tsx:42** -- `property: oldValue` -> `property: newValue` -->

### Cycle 1

_Not yet populated._

---

## Acceptance Criterion

User directive (verbatim): "📝 把这些bug记成新spec 暨M2前置spec"

---

## Explore-Verified Code Anchors

**Explore-verified code anchors (integrated 2026-05-13T08:55Z)**:

- `scripts/generate-html-interactive.py:643` confirms `meal = meal_slot.get("primary", meal_slot)`. Falls back to raw slot if no `primary` key — alternatives silently dropped.
- `scripts/generate-html-interactive.py:599-1179` — `_merge_day_data` spans **581 lines** (cap 30 → refactor mandatory before any incremental fix).
- `scripts/generate-html-interactive.py:470-508` — `_get_timeline_time(name_base, name_local, day_timeline)` three-tier fallback: exact match (479-483) → parenthetical-stripped base match (484-495) → substring match (496-507). Returns `{"start","end"}` or `None`. All tiers are string-similarity heuristics.
- `scripts/generate-html-interactive.py:2792-2797` — Timeline JS template: `const primary = day.meals?.[mealType]; if (primary) { add(primary, 'meal', L(catKey, lang)); }`. Single primary read, no alternatives loop.
- `scripts/fetch-images-batch.py:62, 271` — `.claude/skills/google-maps/scripts/places.py` hardcoded twice. Symlink to `.claude/commands/scripts/google-maps/` was created mid-session to unblock the review; not yet committed.
- `.claude/hooks/pretool-quality-gate.py:19-20` — `MAX_FILE_LINES = 800`, `MAX_FUNC_LINES = 30`. Search across `.claude/hooks/*.py` for `BYPASS_QUALITY_GATE`: **not found**. Override flag is documented but unwired.
- `scripts/save.py` and `scripts/lib/save_translate.py` — `save.py` has no `trip_total` logic; `save_translate.py` is user-language → schema mapping only. No post-merge aggregate recompute loop. `budget.json` exhibits `days[].budget.total` per day with no top-level recalc trigger.
- `.claude/hooks/pretool-validate-data-write.py` — no hardcoded banned-key list; delegates to `verify-plan-integrity.py` for schema. Zero semantic checks (no dedup, primary-state-machine, name-consistency lint).
- `scripts/generate-and-deploy.sh:39-54` — `while [ "$#" -gt 1 ]` does NOT shift `$1` before option loop; one shift inside `--day` case at line 46 consumes `$2` only, leaving `--day` token itself unshifted. `--day` flag is consequently a no-op when first positional arg is the plan id.

---

## Round-2 Evidence Anchors (Implementation Targets)

**Round-2 evidence anchors (addressing Codex pass-with-notes 2026-05-13T21:06Z)**:

- **Cloudflare purge absence (Section 5 item 8)**: confirmed via `find /root/travel-planner/scripts /root/deploy /root/travel-planner/.claude -name "*purge*" -o -name "*cf-cache*" -o -name "*cloudflare*"`. Zero matches in repo deployment paths. The two hits under `.claude/worktrees/overnight-20260412-c6ec78c9/infra/cloudflare-xhs-proxy` and `node_modules/@cloudflare` are unrelated to the travel-planner deployment pipeline. Environment scan `env | grep -iE "CLOUDFLARE|CF_"` empty. `scripts/deploy-travel-plans.sh` and `scripts/generate-and-deploy.sh` contain no Cloudflare API calls — deploy relies solely on Cloudflare's `cf-cache-status: DYNAMIC` pass-through.

- **Optional-no-time-drop precise filter location (Section 5 item 3)**: the rejection happens at `scripts/generate-html-interactive.py:2770-2781` in the `add()` closure of the Timeline JSX generator. Verbatim filter: `if (item?.time?.start && item?.time?.end && item.time.start !== '00:00' && item.time.end !== '00:00' && timeToMinutes(item.time.start) !== timeToMinutes(item.time.end))`. Upstream cause: `_get_timeline_time()` at `:508` returns `None` when name-string doesn't match any timeline.json key (`return None` end of Tier-3 substring fallback), the Python merge passes `time: null` into the per-day data, the JS `add()` then drops it silently. Anchors `:2792-2797` (meal loop) cited earlier are correct for the meal-only consumption pattern but NOT the filter — the filter is line 2770-2781.

- **Demoted-primary state-machine gap (Section 5 item 12) — direct session evidence**:
  - Iteration 1 (2026-05-13 early): meals-agent dispatched with "change Day 12 lunch primary to 裕兴记蟹黄面". Agent's output (this session): "Day 12 lunch alternatives: 老正兴菜馆(福州路) demoted to alt[0]; 沈大成 and 光明邨 preserved as alt[1]/alt[2]". Same pattern for dinner: "苏浙汇(新天地) demoted to alt[0]".
  - Iteration 2 (2026-05-13 user follow-up): user complaint verbatim "你回归了一堆被淘汰的餐馆" (you regressed eliminated restaurants). Required a separate dev-agent invocation to explicitly DELETE the demoted items.
  - Today's state: `grep -c '老正兴\|苏浙汇' data/china-20260412-092624/meals.json` Day 12 = 0 (cleaned). But no state machine in `scripts/save.py`, `scripts/lib/save_translate.py`, or any agent prompt prevents the same regression on the next primary-replacement turn. The default agent behaviour is "preserve old primary as alternative" — should be "delete unless explicitly retained".

---

## Renderer Bugs (Bugs 1-3)

**Renderer / generate-html-interactive.py**

1. 餐厅alts硬编码丢弃 — line 643 `meal_slot.get("primary", meal_slot)` 直接丢 `alternatives[]`。所有日期的餐厅alts (包括成都Day 5周记牛王庙) 永远不渲染。Spec §5.6 期望多选项，但implementation只读primary。
2. time-attachment靠name字符串匹配 — `_get_timeline_time()` Tier1/2/3 fallback 全是字符串匹配。换个括号、加个后缀就失败。应该用entity ID。
3. optional项必须有timeline条目才能渲染 — 仅在域 JSON 标 `optional:true` 不够；Timeline JS line 2793 filter 没time就drop。没有自动从域JSON继承时间的机制。

---

## Quality Gate Bugs (Bugs 4-5)

**Quality gate**

4. `generate-html-interactive.py` 3376 lines, `_merge_day_data` 582 lines 都远超 cap (800/30)。任何edit都被gate拒。无法增量修复。
5. `BYPASS_QUALITY_GATE=1` env var 在文档里but no-op — dev agent发现实际code没wired这个flag。

---

## Deploy-Chain Bugs (Bugs 6-9)

**部署链**

6. `fetch-images-batch.py` 硬编码 `.claude/skills/google-maps/scripts/places.py` — commit 46a46d5 迁移到 `.claude/commands/scripts/google-maps/` 但只给gaode建了symlink，google-maps没建。silent fail。
7. `generate-and-deploy.sh --day` flag parser bug — line 39-54 没 shift `$1`。
8. Cloudflare无purge脚本 — 依赖 `cf-cache-status: DYNAMIC` pass-through，没控制权。
9. `save.py` slot-merge不更新top-level聚合 — Day 13 budget变了，`trip_total` 还是stale 23416 (应是23340)。
