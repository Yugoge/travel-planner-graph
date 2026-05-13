<!-- AUTO-GENERATED VIEW for architect | source: docs/dev/specs/spec-20260513-085358.md | extracted: 2026-05-13T09:00:00Z -->

# architect view of spec-20260513-085358

**Monolith**: docs/dev/specs/spec-20260513-085358.md
**Extraction**: content-block level (no section-level mapping)

---

## Role Mandate

(No explicit architect role definition in monolith — section retained for structural conformance.)

---

## Structural / Architectural Anchors

- `scripts/generate-html-interactive.py:599-1179` — `_merge_day_data` spans **581 lines** (cap 30 → refactor mandatory before any incremental fix).
- `scripts/generate-html-interactive.py:470-508` — `_get_timeline_time(name_base, name_local, day_timeline)` three-tier fallback: exact match (479-483) → parenthetical-stripped base match (484-495) → substring match (496-507). Returns `{"start","end"}` or `None`. All tiers are string-similarity heuristics.
- Entity-ID baseline — only ID-like field is `gaode_id` (string, used as image-cache key prefix `gaode_{gaode_id}` at `generate-html-interactive.py:272-315, 672, 718, 759, 805`). No `poi_id`, `entity_id`, or UUID present in `attractions.json` / `meals.json` / `budget.json`. Cross-file linkage today is name-string based; introducing a unified entity-ID is a new field surface for M2 schema migration.

- **Schema asymmetry concrete data evidence (Section 5 item 10)**:
  - `data/china-20260412-092624/meals.json` Day 12 `lunch` top-level keys = `['primary', 'alternatives']` (nested dict-of-objects with sibling `alternatives:[]` array of 2 items).
  - `data/china-20260412-092624/attractions.json` Day 12 `attractions` = flat `list` of 3 items, every item carrying an `optional` boolean flag at the item level; no `primary`/`alternatives` keys anywhere in the file.
  - Same shape difference in `entertainment.json` (flat list + `optional`) and `shopping.json` (flat list + `optional`). The renderer therefore has two code paths: `_merge_day_data` calls `meal_slot.get("primary", meal_slot)` for meals at `:643` (drops alts) vs. flat-iteration `for attr in day_attractions["attractions"]` for attractions at `:735-ish` (includes every item; relies on Timeline `add()` filter for display gating).

---

## Schema Asymmetry

**Schema 不对称**

10. Meals用 `primary + alternatives[]` (嵌套), attractions/shopping/entertainment 用 flat list + `optional:true` — 这种不对称是所有混乱的根源。renderer/JS需要处理两套shape，agent经常混用。

---

## Root-Cause Architecture Defects

**总结的根本缺陷 — hook只做字段级语法验证，没做语义级验证**

- 没有 entity-ID — 一切靠 name string match，suffix污染namespace
- 没有跨域 dedup check — attractions+shopping+entertainment 可同时段同名
- 没有"primary替换→old primary必须explicitly保留/删除"的状态机
- 没有 timeline ↔ attractions/shopping/entertainment 的名字一致性 lint
- 没有 trip_total/aggregate 自动重算

---

## Systemic Architectural Fixes (M2 prerequisite)

**系统性修复建议 (M2 前置)**

- 加 entity-ID 系统 (例如 `poi_id: gaode_<id>` 或 UUID)，所有跨file引用用ID不用name string
- save.py 加 semantic linter：跨域dedup, primary状态机, aggregate recompute
- 拆 `generate-html-interactive.py` 把 `_merge_day_data` 拆 helpers
- 修 BYPASS_QUALITY_GATE 不一致 (要么wire，要么文档删除)
- google-maps symlink 修infra
- M5 dashboard：feature-status.md 标 spec vs implemented vs deferred
