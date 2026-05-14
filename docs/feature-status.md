# Feature Status Dashboard

> Project-wide milestone and bug-tracker status. Auto-maintained per `/dev` cycle.
> Last updated: 2026-05-13 (cycle task-id `20260513-090000`, spec-20260513-085358)

This page is the single source of truth for:

1. **M1-M5 spec milestones** (origin: `docs/dev/specs/spec-20260508-221237.md` — gaode-maps systematic ban + options-first day planning flow)
2. **Per-bug status** for the 13-bug M2-prerequisite cycle (origin: `docs/dev/specs/spec-20260513-085358.md` Section 5)
3. **Infrastructure constraints** that are deliberate non-implementations (e.g., Cloudflare cache purge)

---

## M1-M5 Spec Milestones

Source: `docs/dev/specs/spec-20260508-221237.md`. M1 has landed in production; M2-M5 are deferred to subsequent cycles per the spec's own milestone decomposition.

| Milestone | Scope | Status | Landed in commit(s) | Notes |
|-----------|-------|--------|---------------------|-------|
| **M1** | Gaode-maps systematic ban for non-geo agents (harness + per-agent DO-NOT prompt block) | **completed** | `e2c5949`, `8b934b8` | Cycle 1 landed harness + agent prompts; cycle 4 moved harness from global dot-claude to project-local per user directive. |
| **M2** | Options-first day planning flow (user-selection-gated candidate space) | **deferred** | — | Deferred per BA milestone decomposition. M2-prerequisite hardening tracked in spec-20260513-085358 (this cycle). |
| **M3** | Web UI overhaul — drag-and-drop timeline with all-pairs intra-city routing | **deferred** | — | Deferred. Depends on M2 candidate-space model. |
| **M4** | Live budget recompute on every web-UI edit + export (PDF, iCal) | **deferred** | — | Deferred. Depends on M3 web UI surface. |
| **M5** | Day slot model with 6 fixed slots per day, flexible times, lazy intra-city routing (supersedes earlier slot-time clauses per §5.9) | **deferred** | — | Deferred. Schema and persistence contract pre-requisites tracked under M2. |

---

## Bug Tracker — spec-20260513-085358 (13-bug M2-prerequisite cycle, task-id 20260513-090000)

Source: `docs/dev/specs/spec-20260513-085358.md` Section 5. Per BA ticket `docs/dev/ticket-20260513-090000.md`, this cycle dispatched 8 file-disjoint dev workers (W1-W8) addressing all 13 bugs. Zero bugs deferred at the spec level; Bug 8 is documented as a deliberate non-implementation (see "Infrastructure Constraints" below).

| Bug | Summary | Status (this cycle) | Worker | AC reference |
|-----|---------|---------------------|--------|--------------|
| 1 | Renderer drops `meal_slot.alternatives[]` (Day 12 lunch `沈大成`/`光明邨` not in HTML) | implemented | W2 | AC1 |
| 2 | `_get_timeline_time()` brittle three-tier string match; no `gaode_id` fast-path | implemented (fast-path only; full entity-ID migration deferred to M2) | W2 | AC2 |
| 3 | Optional items without timeline.json entries silently dropped by `add()` filter | implemented | W2 | AC3 |
| 4 | `scripts/generate-html-interactive.py` is 3376 lines; `_merge_day_data` is 581 lines; exceeds `MAX_FILE_LINES=800` / `MAX_FUNC_LINES=30` quality-gate caps | implemented (mechanical refactor into 9 helpers in `scripts/lib/render_day_data.py`; merged-dict byte-identical invariant per codex round-2 Q1) | W7 | AC12 |
| 5 | `BYPASS_QUALITY_GATE` documented but unwired in `.claude/hooks/pretool-quality-gate.py` | implemented (env-var wired; stderr log on activation; not default-enabled) | W1 | AC4 |
| 6 | `scripts/fetch-images-batch.py` helper path resolution broken on clean checkout (`.claude/skills/google-maps` is uncommitted absolute symlink) | implemented (relative-symlink OR path-constant migration; absolute-symlink-commit branch REJECTED per OBJ-6) | W3 | AC5 |
| 7 | `scripts/generate-and-deploy.sh` `--day` flag parser exits 1 with `Unknown option <plan-id>` (missing initial shift before case loop) | implemented | W4 | AC6 |
| 8 | No Cloudflare cache purge path in deploy chain | **N/A — deliberate non-implementation** (see Infrastructure Constraints below) | W6 | AC11 |
| 9 | `data.trip_total` not auto-recomputed; lives stale (23416 vs sum-of-days 13044 in china-20260412-092624) | implemented (recompute on every save touching budget data) | W5 | AC7 |
| 10 | Schema asymmetry: meals nested (`primary`+`alternatives[]`) vs attractions/shopping/entertainment flat (`optional:true`). No explicit reject for ad-hoc `alternatives[]` on flat shapes | implemented (schemas reject `alternatives[]` via agent-scoped `BANNED_AD_HOC_KEYS` in `save_translate.py`; `_normalize_to_canonical_record()` shape-normalizer added; renderer takes NO Bug-10 changes per codex round-2 Q2; full unification deferred to M2) | W8 | AC13 |
| 11 | No cross-domain dedup; same item appears in attractions + shopping for same day (e.g., Day 12 Wukang Road) | implemented (WARN-level cross-domain dedup using W8 shape-normalizer) | W5 | AC8 |
| 12 | Meals-agent default behavior preserves old primary as alternative on primary-replacement; user must explicitly `删除` | implemented (default = drop old primary unless explicitly listed in incoming alternatives[]; stderr audit line) | W5 | AC9 |
| 13 | No top-level feature-status dashboard; only unrelated `image-fallback-status.md` exists | implemented (this file + README link + `docs/index.md` root-level-files entry) | W6 | AC10 |

**Worker dispatch summary**: W1 ran FIRST sequential (BYPASS gate-bypass prerequisite). W2-W6 ran in parallel after W1. W7 ran sequential AFTER W2 (shared file `scripts/generate-html-interactive.py`). W8 ran sequential AFTER W5 (shared file `scripts/lib/save_translate.py`). Zero deferred bugs at the spec/worker level.

---

## Infrastructure Constraints

This section documents deliberate non-implementations — items that look like missing features but are intentional given infrastructure constraints. They are NOT action items for this cycle or M2.

### Cloudflare cache purge — N/A

**Status**: N/A (deliberate non-implementation, not an absence).

**Rationale**:

- No Cloudflare API token exists in the repo or in the deployment environment.
- Adding a purge integration would require provisioning a `CLOUDFLARE_API_TOKEN` secret and zone-ID configuration — out of repo scope.
- The current deployment relies on Cloudflare `cf-cache-status: DYNAMIC` pass-through; the origin serves fresh HTML on every request, so cache invalidation is not required for content updates to be visible.
- Repository-wide search confirms zero hits for `purge`, `cf-cache`, or `cloudflare` in `scripts/` or `/root/deploy/` (excluding unrelated worktree/node_modules paths) and no `CLOUDFLARE_*` / `CF_*` env vars in deployment.

**Not an action item** for this cycle (spec-20260513-085358 / task-id 20260513-090000) or for M2 (spec-20260508-221237 milestone decomposition). If a future milestone requires hard cache invalidation (e.g., CDN-cached static asset rewrite), the integration would be re-evaluated then with explicit token provisioning.

---

## Update Conventions

- Each `/dev` cycle that closes additional bugs from spec-20260513-085358 SHOULD update the Bug Tracker table's "Status" column.
- When a new spec is added (e.g., M2 prerequisite spec follow-up), append a new section below "Bug Tracker" with the same table format.
- M1-M5 milestone status updates when a milestone lands in commit(s); cite the commit hash in the "Landed in commit(s)" column.
- Infrastructure-constraint entries (e.g., Cloudflare) stay until the underlying infrastructure constraint changes (e.g., token provisioning) — they are not removed silently.
