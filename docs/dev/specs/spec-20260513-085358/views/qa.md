<!-- AUTO-GENERATED VIEW for qa | source: docs/dev/specs/spec-20260513-085358.md | extracted: 2026-05-13T09:15:00Z -->

# qa view of spec-20260513-085358

**Monolith**: docs/dev/specs/spec-20260513-085358.md
**Extraction**: content-block level (no section-level mapping)

---

## Acceptance Criterion

User directive (verbatim): "📝 把这些bug记成新spec 暨M2前置spec"

---

## Baseline Observations (Section 1, measurable)

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
