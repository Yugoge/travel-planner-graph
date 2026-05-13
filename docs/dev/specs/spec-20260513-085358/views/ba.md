<!-- AUTO-GENERATED VIEW for ba | source: docs/dev/specs/spec-20260513-085358.md | extracted: 2026-05-13T09:15:00Z -->

# ba view of spec-20260513-085358

**Monolith**: docs/dev/specs/spec-20260513-085358.md
**Extraction**: content-block level (no section-level mapping)

---

## Spec Header

# Spec: M2 prerequisite — systematic bugs surfaced during 2026-05-13 china-20260412-092624 review

**Pipeline**: travel-planner
**Session**: spec-20260513-085358
**Created**: 2026-05-13T08:53:58Z

---

## Acceptance Criterion (Section 5 verbatim)

User directive (verbatim): "📝 把这些bug记成新spec 暨M2前置spec"

Context: the user is requesting that the systematic bugs and improvement opportunities surfaced during the 2026-05-13 `/review china/2026-04-12/` session be recorded as a new spec, intended as a prerequisite to the deferred M2-M5 milestones of spec-20260508-221237 (drag-and-drop web UI overhaul). The bug enumeration the user is asking me to record follows verbatim from my immediately-prior message to the user:

---

## Agent-Behaviour Requirements (Bugs 11-12)

**Agent行为**

11. 没有跨域dedup — Day 12 timeline中"Huaihai-Wukang-Shaanxi Walk + Moller Villa" 和 "Wukang Road & Anfu Road — Boutique Stroll" 同时段同活动，attractions-agent和shopping-agent各加一遍。
12. demoted primary 默认保留为 alternative — 你换primary后老的成"被淘汰餐馆" alt，需要你显式说"删除"。

---

## Spec/Implementation Gap (Bug 13)

**Spec/implementation脱节**

13. M1-M5 进度无dashboard — 你不查spec/completion文档就不知道drag-drop只是spec里写过。Feature status应该有可见标记。

---

## Why Hooks Failed to Block "Garbage Schema"

**为什么hook没拦住"垃圾schema"**

`pretool-validate-data-write.py` 实际拦的：banned keys (`plan_label`, `is_alternative`, `_isAlternative`, `tier`, `bundle_id`, `priority_label`); null required fields; empty coordinates; null location_change. `save.py` + `save_translate.py` 实际做的：user-language → schema translation; banned-keys rejection; slot-level merge (按day). 这些都是字段级语法检查。但本session加的"垃圾"是：timeline key 用了描述性后缀 (例如 `"Shanghai Tower Observatory (上海中心大厦) — Morning Alternative"`、`"Wukang Road & Anfu Road — Boutique Stroll (Primary)"`) — 字段级 schema 合法（key是string，value有 `start_time/end_time/duration_minutes/optional`），但命名规范是garbage (描述性labels混进venue name namespace); attractions/shopping/entertainment 跨域重复同一活动 — 字段级合法，语义层重复; agents 把demoted primaries留作alts — 字段级合法，业务逻辑错误。
