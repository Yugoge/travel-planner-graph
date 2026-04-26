# aggregator-input/

Historical source fragments consumed by `../P0-9-W5-composed-ctx.diff`.

These three `.diff` files anchor on the same vanilla `rednoteTools.js:24` line
(`const ctx = ... newContext({ serviceWorkers: 'block' })`) and were therefore
mutually exclusive — sequential `patch` could not apply them in any order:

- **P0-2.diff** — service worker flip + 93-line `addInitScript` evasion body
- **P0-4.diff** — service worker flip (duplicate of P0-2 hunk1) plus two
  independent `.close-circle` locator-click hunks (the latter extracted to
  `../P0-4-clicks.diff`)
- **P1.5-14.diff** — `Object.assign` proxy wrapper around the `newContext`
  options (rednoteTools.js hunk2) plus an independent authManager.js login
  proxy hunk (the latter re-anchored on post-P0-1 state and extracted to
  `../P1.5-14-auth.diff`)

The colliding hunks were composed into the single `P0-9-W5-composed-ctx.diff`
hunk, which produces the merged final state intended by all three fragments
jointly. These source files are kept as audit trail for diff-on-diff review;
the parent `apply.sh` glob (`stealth.patch.d/*.diff`) is non-recursive and
does NOT consume files in this directory.

References:
- `/root/docs/dev/close-report-20260424-210207.md` — R2 unanimous NO verdict
  describing the collision (lines 78–84)
- `/root/docs/dev/ba-spec-20260424-230451.md` — composed_hunk_spec
- `/root/docs/dev/architect-stealth-pipeline-review-20260424-230451.json` —
  Q3 Option B (compose into a single hunk)
- `/root/docs/dev/specs/spec-20260423-080000.md` Section 4 cycle 230451
