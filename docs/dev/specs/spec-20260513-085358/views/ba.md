<!-- AUTO-GENERATED VIEW for ba | source: docs/dev/specs/spec-20260513-085358.md | extracted: 2026-05-13T09:00:00Z -->

# ba view of spec-20260513-085358

**Monolith**: docs/dev/specs/spec-20260513-085358.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

<!-- WHO WRITES: BA (on first analysis) -->
<!-- WHAT: Verbatim quote from user's requirement or focus string. -->
<!-- This is the single source of truth for what "done" means. Do not paraphrase. -->

---

# Spec: M2 prerequisite — systematic bugs surfaced during 2026-05-13 china-20260412-092624 review

**Pipeline**: travel-planner
**Session**: spec-20260513-085358
**Created**: 2026-05-13T08:53:58Z

---

## Section 1: Before

### Cycle 1

Baseline snapshot taken during user-driven `/review china/2026-04-12/ 从上海开始` session on 2026-05-13.

Triggering observations (live URL https://travel.life-ai.app/china/2026-04-12/, Day 12 + Day 13):

- Day 12 alternatives (沈大成 / 光明邨 / 1221) absent from Timeline View despite presence in `data/china-20260412-092624/meals.json`. Confirmed via `curl … | grep -c` returning 0.
- Day 12 optional attractions/shopping/entertainment items in their respective JSON files but ALSO absent from Timeline View until the user manually added per-item timeline.json entries to match Chengdu Day 5 pattern.
- Multiple agent-dispatched edits in the same session created divergent / duplicated timeline entries: e.g., "Huaihai-Wukang-Shaanxi Heritage Walk + Moller Villa" (from attractions-agent) and "Wukang Road & Anfu Road — Boutique Stroll (Primary)" (from shopping-agent) at the SAME 15:20-17:30 slot for Day 12.
- `scripts/fetch-images-batch.py` failed with `FileNotFoundError: image-fetch helper(s) missing: [PosixPath('/root/travel-planner/.claude/skills/google-maps/scripts/places.py')]` after commit 46a46d5 migrated the helper to `.claude/commands/scripts/google-maps/`; only `.claude/skills/gaode-maps` symlink was created, the `google-maps` counterpart was not.
- `scripts/generate-html-interactive.py` already at 3376 lines / `_merge_day_data` at 582 lines. `pretool-quality-gate.py` blocks any edit (caps are 800 / 30). One dev-agent attempt to add a 25-line meal-alternatives helper triggered the gate.
- The advertised `BYPASS_QUALITY_GATE=1` env override was reported by a dev-agent as not wired in the hook code.
- User-stated belief that drag-and-drop UI architecture had been implemented in this repo was disproved by: (a) `git status` clean before agent activity; (b) 20+ checkpoints back to 2026-05-10 all 3376-line baseline with zero `drag/sortable/onDrag/HTML5Backend/react-dnd/@dnd-kit` occurrences in any `.py` script or in deployed `output/*.html`; (c) `docs/dev/scratch-20260509-114002/specialist-findings.md` line 25 verbatim: "Existing renderer scripts/generate-html-interactive.py (3376 lines) emits a single static React+babel-standalone HTML file with NO fetch/drag/autosave/server endpoints"; (d) `commit-manifest-20260509-114002.json` listing only agent .md + hook .py + policy .json files, no renderer .py changes. `completion-20260509-114002.md` line 13: "This cycle delivered M1 only; M2-M5 are queued for future /dev invocations."
- `save.py` slot-merge does not update top-level aggregate fields. After Day 13 budget recompute, `trip_total` in `data/china-20260412-092624/budget.json` remained stale at 23416 vs. correct 23340.
- `scripts/generate-and-deploy.sh` `--day` flag silently ignored due to argument parser not shifting `$1` before option loop (lines 39-54 area).

The full bug enumeration produced during this session is captured verbatim in Section 5 below.

---

## Section 5: User's Acceptance Criterion

User directive (verbatim): "📝 把这些bug记成新spec 暨M2前置spec"

Context: the user is requesting that the systematic bugs and improvement opportunities surfaced during the 2026-05-13 `/review china/2026-04-12/` session be recorded as a new spec, intended as a prerequisite to the deferred M2-M5 milestones of spec-20260508-221237 (drag-and-drop web UI overhaul). The bug enumeration the user is asking me to record follows verbatim from my immediately-prior message to the user:

---

**Renderer / generate-html-interactive.py**

1. 餐厅alts硬编码丢弃 — line 643 `meal_slot.get("primary", meal_slot)` 直接丢 `alternatives[]`。所有日期的餐厅alts (包括成都Day 5周记牛王庙) 永远不渲染。Spec §5.6 期望多选项，但implementation只读primary。
2. time-attachment靠name字符串匹配 — `_get_timeline_time()` Tier1/2/3 fallback 全是字符串匹配。换个括号、加个后缀就失败。应该用entity ID。
3. optional项必须有timeline条目才能渲染 — 仅在域 JSON 标 `optional:true` 不够；Timeline JS line 2793 filter 没time就drop。没有自动从域JSON继承时间的机制。

**Quality gate**

4. `generate-html-interactive.py` 3376 lines, `_merge_day_data` 582 lines 都远超 cap (800/30)。任何edit都被gate拒。无法增量修复。
5. `BYPASS_QUALITY_GATE=1` env var 在文档里but no-op — dev agent发现实际code没wired这个flag。

**部署链**

6. `fetch-images-batch.py` 硬编码 `.claude/skills/google-maps/scripts/places.py` — commit 46a46d5 迁移到 `.claude/commands/scripts/google-maps/` 但只给gaode建了symlink，google-maps没建。silent fail。
7. `generate-and-deploy.sh --day` flag parser bug — line 39-54 没 shift `$1`。
8. Cloudflare无purge脚本 — 依赖 `cf-cache-status: DYNAMIC` pass-through，没控制权。
9. `save.py` slot-merge不更新top-level聚合 — Day 13 budget变了，`trip_total` 还是stale 23416 (应是23340)。

**Schema 不对称**

10. Meals用 `primary + alternatives[]` (嵌套), attractions/shopping/entertainment 用 flat list + `optional:true` — 这种不对称是所有混乱的根源。renderer/JS需要处理两套shape，agent经常混用。

**Agent行为**

11. 没有跨域dedup — Day 12 timeline中"Huaihai-Wukang-Shaanxi Walk + Moller Villa" 和 "Wukang Road & Anfu Road — Boutique Stroll" 同时段同活动，attractions-agent和shopping-agent各加一遍。
12. demoted primary 默认保留为 alternative — 你换primary后老的成"被淘汰餐馆" alt，需要你显式说"删除"。

**Spec/implementation脱节**

13. M1-M5 进度无dashboard — 你不查spec/completion文档就不知道drag-drop只是spec里写过。Feature status应该有可见标记。

**为什么hook没拦住"垃圾schema"**

`pretool-validate-data-write.py` 实际拦的：banned keys (`plan_label`, `is_alternative`, `_isAlternative`, `tier`, `bundle_id`, `priority_label`); null required fields; empty coordinates; null location_change. `save.py` + `save_translate.py` 实际做的：user-language → schema translation; banned-keys rejection; slot-level merge (按day). 这些都是字段级语法检查。但本session加的"垃圾"是：timeline key 用了描述性后缀 (例如 `"Shanghai Tower Observatory (上海中心大厦) — Morning Alternative"`、`"Wukang Road & Anfu Road — Boutique Stroll (Primary)"`) — 字段级 schema 合法（key是string，value有 `start_time/end_time/duration_minutes/optional`），但命名规范是garbage (描述性labels混进venue name namespace); attractions/shopping/entertainment 跨域重复同一活动 — 字段级合法，语义层重复; agents 把demoted primaries留作alts — 字段级合法，业务逻辑错误。

**总结的根本缺陷 — hook只做字段级语法验证，没做语义级验证**

- 没有 entity-ID — 一切靠 name string match，suffix污染namespace
- 没有跨域 dedup check — attractions+shopping+entertainment 可同时段同名
- 没有"primary替换→old primary必须explicitly保留/删除"的状态机
- 没有 timeline ↔ attractions/shopping/entertainment 的名字一致性 lint
- 没有 trip_total/aggregate 自动重算

**系统性修复建议 (M2 前置)**

- 加 entity-ID 系统 (例如 `poi_id: gaode_<id>` 或 UUID)，所有跨file引用用ID不用name string
- save.py 加 semantic linter：跨域dedup, primary状态机, aggregate recompute
- 拆 `generate-html-interactive.py` 把 `_merge_day_data` 拆 helpers
- 修 BYPASS_QUALITY_GATE 不一致 (要么wire，要么文档删除)
- google-maps symlink 修infra
- M5 dashboard：feature-status.md 标 spec vs implemented vs deferred
