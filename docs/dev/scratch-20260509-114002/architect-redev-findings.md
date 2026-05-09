# Architect findings — /redev cycle for spec-20260508-221237 M1

**Cycle**: redev cycle 1 (after /close --codex returned CLOSE: NO)
**Mandate**: 永久彻底修复 — go beyond the 4 surfaced findings; identify ALL coverage gaps of the same architectural shape
**Codex required**: true (per /redev --codex flag)

---

## The 4 close-report findings (reminder)

1. **Glob pattern bypass** — `_check_gaode_read` reads `file_path`/`path` but ignores `Glob.pattern` field
2. **MCP network bypass** — `_check_gaode_webfetch` only matches `tool_name=='WebFetch'`; misses `mcp__playwright__browser_navigate(url=...)` and 36 other MCP tools
3. **AC6 verification gap** — `tool-policy.v1.json` has no `roles.timeline` / `roles.transportation` entries; standard role check fails before allowlist positive verification can run end-to-end
4. **BA-QA r2 JSON syntax error** — line 179 Chinese parenthetical breaks JSON string

## 11 architect findings (3 critical, 3 major, 5 minor)

### Critical

**arch-1**: Per-tool field-extraction is implementer-memory-bound. `pretool-tool-policy.py:_extract_targets` and the four `_check_gaode_*` functions extract tool input fields by hardcoded tool-name dispatch. Each function reads only the fields the implementer happened to remember. Concrete OTHER fields the current code does NOT consult that may carry a gaode-shaped string:
- `Edit.old_string` / `Edit.new_string` (current code only reads `Edit.file_path`)
- `MultiEdit.edits[].old_string` / `MultiEdit.edits[].new_string`
- `NotebookEdit.new_source` (current: only `notebook_path`)
- `Write.content` (current: only `file_path`)
- `Grep.pattern` (regex; current: only `Grep.path`)
- `Grep.glob` (file filter; current: only `Grep.path`)
- Bash heredoc body content (currently scanned as one string but not structurally decomposed)

**arch-2**: MCP network surface is enumerated by tool-name allowlist instead of by string-content scan. `_check_gaode_webfetch` line 127 narrows to `tool_name=='WebFetch'`. The Claude Code harness exposes mcp__playwright__* (37 tools), mcp__claude_ai_Gmail/Calendar/Drive/Notion, mcp__happy. Specific MCP bypass vectors:
- `mcp__playwright__browser_navigate(url='https://restapi.amap.com/...')` — Codex confirmed
- `mcp__playwright__browser_evaluate(function='() => fetch("https://restapi.amap.com/...")')` — fetch URL inside JS source string
- `mcp__playwright__browser_run_code(code='await page.goto("https://lbs.amap.com/api")')` — same pattern
- `mcp__playwright__browser_take_screenshot(filename='/.claude/skills/gaode-maps/leak.png')` — write under gaode read-path prefix
- `mcp__playwright__browser_file_upload(paths=['/.claude/skills/gaode-maps/skill.md'])` — exfiltrate gaode source
- `mcp__claude_ai_Gmail__send` — could exfiltrate AMAP_KEY env-var contents

**arch-3**: AC6 positive test structurally unverifiable. `tool-policy.v1.json:roles{}` contains 17 keys; `timeline` and `transportation` are NOT among them. Gaode allowlist NAMES canonical IDs that are not also valid policy roles. Consequence: gaode pre-check ALLOWS timeline-agent skill call (is_gaode_allowed True) → standard check `get_role_policy('timeline')` returns `_unknown_role:True` → hook exits 2 with "unknown role timeline". AC6 cannot pass end-to-end. **Three candidate fixes** (BA must choose):
- (A) Add `roles.timeline` + `roles.transportation` to tool-policy.v1.json with realistic allowed_tools/allowed_write_path_prefixes mirroring dev role. PRO: zero hook changes, single source of truth. CON: maintenance ownership unclear.
- (B) After gaode pre-check ALLOWS, short-circuit downstream is_allowed for gaode-tool surfaces only. PRO: no policy change. CON: silently bypasses standard tool-list/write-path checks for timeline/transportation.
- (C) Make unknown-role fallthrough fail-OPEN for timeline/transportation. PRO: minimal coupling. CON: invents new fail-open path contradicting `default_action:deny`.

Architect recommends (A) as architecturally cleanest.

### Major

**arch-4**: bash-resolved-path matcher is unreachable for allowlist roles — same root cause as arch-3. Banned-role denials work; allowlist-role positives fail before reaching it.

**arch-5**: Verification harness tests the helper, not the contract. Verify-gaode-ban.sh exercises `is_gaode_allowed()` in isolation; cannot detect (a) field shapes the caller never passes, (b) standard-policy fallthrough overriding the helper, (c) MCP enumeration drift, (d) hook ordering bugs. Same dev who wrote helper wrote verifier; same blind spots. **Process gap**: dev cycle, QA cycle, AND verifier all missed all 3 Codex findings.

**arch-6**: Bash command resolution misses module invocation, heredoc bodies, inline-script eval:
- `python3 -m gaode_module` — module name not path-shaped, won't match bash-resolved-path
- `bash <<EOF\npython3 .../gaode-maps/scripts/x.py\nEOF` — bash-token IS scanned (substring matches), but bash-resolved-path loses heredoc body
- `bash -c "$(cat gaode-wrapper.sh)"` — inner script invisible to shlex
- `python3 -c "import urllib.request; urllib.request.urlopen('https://restapi.amap.com/...')"` — URL inside Python string; bash-token MAY catch via 'amap' substring (depends on policy data)
- Variable-assembled URL: `AMAP_HOST=restapi.amap.com; curl https://$AMAP_HOST/...` — env-var matcher catches AMAP_HOST; network-host matcher only catches AFTER shell expansion (hook does NOT expand)

### Minor

**arch-7**: Identity fail-CLOSED depends on subagent_type field name with no test pinning.
**arch-8**: Skill matcher case-INSENSITIVE; allowlist canonicalization case-SENSITIVE — undocumented asymmetry.
**arch-9**: Network-host substring 'gaode' signal gated to scheme-bearing strings only.
**arch-10**: BA-QA r2 invalid JSON is symptom of missing PostToolUse JSON-syntax validator for docs/dev/*.json.
**arch-11**: `_GAODE_SURFACE_DISPATCH` table correct but undertests its branches (verify-gaode-ban.sh omits 'bash-resolved-path' key entirely).

## 3 architecture proposals

**arch-prop-1 — Replace per-tool field-list with content-based string scanner over tool_input**:
- Walk every string-valued leaf in tool_input (recursive over dict/list, depth-capped) and feed each string to the four content-based surface matchers (bash-token, network-host, env-var, read-path). The two structure-based surfaces (skill needs Skill.skill field; bash-resolved-path needs shlex of Bash.command) keep narrow per-tool dispatch.
- **Quantified benefit**: closes Glob.pattern (Codex #2), Edit.old_string, MultiEdit.edits, NotebookEdit.new_source, Write.content, all mcp__* string-valued inputs (closes Codex #3 by-construction). Today the matcher consults 5 hardcoded fields across 4 tool names; proposal consults all string leaves of all tools (~80 inputs the current code does not see across mcp__playwright__* alone).
- **Migration**: additive, dual-run for one cycle with telemetry, then remove per-tool functions.

**arch-prop-2 — Tier the verification harness: T1 unit + T2 integration + T3 contract**:
- T1 = current verify-gaode-ban.sh (helper-level isolated test)
- T2 = NEW `verify-gaode-ban-integration.sh` — spawns python3 pretool-tool-policy.py as subprocess, pipes JSON stdin, asserts (exit_code, stderr_json shape), for every (banned_role × allowlist_role) × (every tool name in roles[*].allowed_tools) × (gaode-target, non-gaode-target). ~340 cases bounded.
- T3 = NEW `verify-gaode-ban-contract.sh` — parses `~/.claude.json:mcpServers` + system MCP tool catalog (or fixture file), runs T2 against every mcp__* tool name. T3 is what would have caught arch-2.
- **Quantified benefit**: T2 would catch Codex finding #1 + #2; T3 would catch finding #3. 3-of-4 catchable BEFORE /close.

**arch-prop-3 — Add timeline + transportation as first-class roles in tool-policy.v1.json**:
- `roles.timeline` and `roles.transportation` with `allowed_tools = ['Read','Glob','Grep','Bash','Write','Edit','MultiEdit','Skill']` and `allowed_write_path_prefixes` restricted to `'*/data/<trip>/**'`, `'*/docs/dev/timeline-*'` / `'transportation-*'`.
- **Quantified benefit**: closes AC6 positive-test gap deterministically. Eliminates allowlist-vs-policy-roles dual-source-of-truth violation.
- **Migration**: pure addition of two role entries. policy_version bumps 2→3.

## Out-of-scope per "永久彻底修复" sanity-check

- Hostile evasion (base64-decoded payloads) — explicitly out of threat model per BA cycle 1; user's threat model is "agent forgets the rule", not "agent is adversarial". Architect concurs.

## What BA must decide for the redev ticket

1. **Adopt arch-prop-1 (content-based scanner)?** — closes arch-1 + arch-2 + bypass classes. Architect says YES.
2. **Adopt arch-prop-2 (3-tier verifier)?** — closes the process gap that let 3-of-4 Codex findings escape. Architect says YES.
3. **Adopt arch-prop-3A (add timeline/transportation roles)?** — closes arch-3 + arch-4. Architect recommends (A) over (B)/(C) on dual-source-of-truth grounds.
4. **Address arch-6 bash module/heredoc gaps?** — within scope of "永久彻底修复"; small policy-data additions to `gaode_denied_bash_tokens` (add `gaode_`, `amap_` prefixes for Python module names) plus heredoc body extraction.
5. **Address arch-10 (PostToolUse JSON validator for docs/dev/*.json)?** — symptomatic, not core. BA may defer to a separate cycle.
6. **Fix the BA-QA r2 JSON syntax** — trivial repair, in this cycle.
7. **Trim minor findings (arch-7/8/9/11)?** — BA judgment call; cleanup opportunities, not blockers.

## Recommended ticket scope (for BA to refine)

**Must Have** (永久彻底修复 core):
- arch-prop-1 content-based scanner (closes arch-1, arch-2, all MCP bypass vectors)
- arch-prop-3A timeline+transportation roles (closes arch-3, arch-4)
- Glob.pattern + Grep.pattern + Grep.glob + Edit.* + MultiEdit.* + NotebookEdit.new_source + Write.content all covered by arch-prop-1
- Fix `ba-qa-report-20260509-114002-r2.json:179` invalid JSON (close-report finding #4)
- Bash heredoc body extraction (arch-6 partial)

**Should Have**:
- arch-prop-2 T2 integration tier verifier
- arch-prop-2 T3 contract tier verifier
- gaode_denied_bash_tokens extended for Python module prefixes (`gaode_`, `amap_`)

**Could Have**:
- arch-10 PostToolUse JSON validator (separate cycle)
- arch-7/8/9/11 minor cleanup
