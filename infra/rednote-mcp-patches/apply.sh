#!/bin/bash
# Apply rednote-mcp patches for XHS proxy support + stealth fragments
#
# Run after: npm install -g rednote-mcp@0.2.3
#
# Pipeline:
#   1. Legacy patches (authManager.patch + rednoteTools.patch) via patch -p0.
#   2. Stealth fragments under stealth.patch.d/*.diff in `sort -V` order.
#      The aggregator-input/ subdirectory is NOT recursed (shell glob excludes it).
#
# Strip-level detection (per-fragment):
#   - `--- a/usr/lib/...` headers -> -p1 -d /
#   - `--- a/dist/...`    headers -> -p1 -d /usr/lib/node_modules/rednote-mcp
#
# Idempotency:
#   The script writes a marker file `$TARGET/.stealth-applied-fragments` listing
#   the basenames of fragments that were successfully applied this run. On a
#   subsequent run, fragments named in that marker are skipped. The marker lives
#   inside $TARGET so an `npm install -g rednote-mcp@…` (which replaces $TARGET)
#   automatically wipes both the patches AND the marker — re-run after reinstall
#   correctly re-applies everything from scratch.
#
#   For fragments NOT in the marker, the script tries `patch --dry-run --forward`
#   first; if that exits 0 with no "previously applied" sentinel the fragment is
#   applied. If forward dry-run reports "Reversed (or previously applied) patch"
#   the fragment is treated as already-applied (legacy state — pre-marker). If
#   both gates fail the fragment is reported as ERROR and exit 1.
#
#   The marker mechanism is necessary because (a) downstream fragments edit
#   context lines used by upstream fragments' hunks, breaking pure reverse-dry-run
#   detection, and (b) several fragments add try/catch blocks whose closing
#   `} catch (e) {}` repeats throughout the file — `patch --forward` with default
#   fuzz happily re-applies them at offset positions, producing duplicate code.
#
# Exit codes:
#   0 = all legacy patches and all stealth fragments applied (or skipped) cleanly
#   1 = any legacy patch or stealth fragment failed both forward and reverse dry-run
#
# Override target via env (used by sandbox tests):
#   REDNOTE_MCP_DIST=/path/to/dist  bash apply.sh
#
# References:
#   - docs/dev/close-report-20260424-210207.md  (R2 NO verdict — actionable gaps 1-3)
#   - docs/dev/ba-spec-20260424-230451.md       (apply_sh_spec)
#   - docs/dev/specs/spec-20260423-080000.md    (parent spec)
#
set -euo pipefail
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${REDNOTE_MCP_DIST:-/usr/lib/node_modules/rednote-mcp/dist}"
STEALTH_DIR="$PATCH_DIR/stealth.patch.d"
# When REDNOTE_MCP_DIST overrides TARGET, the strip-level base for `a/usr/lib/...`
# headers should also be relocated under that sandbox root. STRIP_USR_BASE is the
# directory that contains the `usr/lib/...` tree; STRIP_DIST_BASE is the directory
# that contains the `dist/...` tree. By default both resolve to the production
# layout (/ and /usr/lib/node_modules/rednote-mcp respectively).
STRIP_USR_BASE="${REDNOTE_STRIP_USR_BASE:-/}"
STRIP_DIST_BASE="${REDNOTE_STRIP_DIST_BASE:-/usr/lib/node_modules/rednote-mcp}"

if [ ! -d "$TARGET" ]; then
  echo "Error: rednote-mcp not found at $TARGET" >&2
  echo "Install first: npm install -g rednote-mcp@0.2.3" >&2
  exit 1
fi

# Marker file lives inside $TARGET so it shares lifetime with the dist (npm
# reinstall wipes $TARGET and resets stealth state simultaneously).
MARKER_FILE="$TARGET/.stealth-applied-fragments"
touch "$MARKER_FILE"

marker_has() {
  local name="$1"
  grep -Fxq "$name" "$MARKER_FILE" 2>/dev/null
}

marker_add() {
  local name="$1"
  marker_has "$name" || printf '%s\n' "$name" >> "$MARKER_FILE"
}

# Counters for the end-of-run summary.
COUNT_TOTAL=0
COUNT_APPLIED=0
COUNT_SKIPPED=0
COUNT_FAILED=0

# Apply a legacy -p0 patch with an explicit single-file target.
#
# Idempotency strategy (per architect Q5):
#   1. forward dry-run — if exit 0 with no "Reversed" sentinel, fragment is fresh -> apply.
#   2. forward dry-run output contains "Reversed (or previously applied) patch" -> SKIP.
#   3. reverse dry-run as belt-and-braces fallback for already-applied detection.
#   4. otherwise ERROR.
apply_legacy() {
  local patchfile="$1" target_file="$2" bn out fwd_rc
  bn="$(basename "$patchfile")"
  COUNT_TOTAL=$((COUNT_TOTAL + 1))
  if marker_has "$bn"; then
    echo "[SKIP]    $bn (already applied)"
    COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
    return 0
  fi
  out="$(patch -p0 --dry-run --forward "$target_file" < "$patchfile" 2>&1)" && fwd_rc=0 || fwd_rc=$?
  if [ "$fwd_rc" -eq 0 ]; then
    patch -p0 --forward "$target_file" < "$patchfile" >/dev/null
    marker_add "$bn"
    echo "[APPLIED] $bn"
    COUNT_APPLIED=$((COUNT_APPLIED + 1))
    return 0
  fi
  if printf '%s\n' "$out" | grep -q "Reversed (or previously applied) patch detected"; then
    marker_add "$bn"
    echo "[SKIP]    $bn (already applied)"
    COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
    return 0
  fi
  if patch -p0 --dry-run --reverse --force "$target_file" < "$patchfile" >/dev/null 2>&1; then
    marker_add "$bn"
    echo "[SKIP]    $bn (already applied)"
    COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
    return 0
  fi
  echo "[ERROR]   $bn — neither forward nor reverse dry-run succeeded; manual review required" >&2
  COUNT_FAILED=$((COUNT_FAILED + 1))
  return 1
}

# Detect strip level for a stealth fragment by inspecting its `--- a/...`
# header. Echoes the patch options as a single string (intended to be word-split
# at the call site).
detect_strip_opts() {
  local fragment="$1"
  if grep -q '^--- a/usr/lib/' "$fragment"; then
    echo "-p1 -d $STRIP_USR_BASE"
    return 0
  fi
  if grep -q '^--- a/dist/' "$fragment"; then
    echo "-p1 -d $STRIP_DIST_BASE"
    return 0
  fi
  return 1
}

# Apply a single stealth fragment. Per-fragment errors are tallied; the loop
# continues so the operator sees every failing fragment in one run.
apply_fragment() {
  local fragment="$1" bn opts out fwd_rc
  bn="$(basename "$fragment")"
  COUNT_TOTAL=$((COUNT_TOTAL + 1))
  if marker_has "$bn"; then
    echo "[SKIP]    $bn (already applied)"
    COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
    return 0
  fi
  if ! opts="$(detect_strip_opts "$fragment")"; then
    echo "[ERROR]   $bn — unrecognised diff header prefix; cannot determine strip level" >&2
    COUNT_FAILED=$((COUNT_FAILED + 1))
    return 1
  fi
  # word-split is intentional for $opts (multi-token like "-p1 -d /")
  # --verbose is REQUIRED so GNU patch surfaces "Ignoring the trailing garbage"
  # and similar partial-application warnings; without it those warnings are
  # silently suppressed even though the hunks are dropped (exit code stays 0).
  out="$(patch $opts --dry-run --verbose --forward < "$fragment" 2>&1)" && fwd_rc=0 || fwd_rc=$?
  if [ "$fwd_rc" -eq 0 ]; then
    # Pre-real-apply gate: also screen the dry-run output. If the dry-run shows
    # any partial-application warning, refuse to proceed — the real apply would
    # silently apply only the surviving hunks, exit 0, and lock the broken
    # state into the marker file. Empirical bug from cycle 230451:
    # P1.5-14-auth.diff had a malformed hunk-1 header (`@@ -116,6 +116,15 @@`
    # instead of correct `@@ -116,7 +116,16 @@`); patch emitted "Ignoring the
    # trailing garbage" with --verbose, silently dropped hunk 2, exited 0 —
    # apply.sh wrote the marker and locked in the broken state. See
    # close-report-20260425-093300.md for the full reproduction.
    if printf '%s\n' "$out" | grep -Eq 'Ignoring the trailing garbage|Hunk #[0-9]+ FAILED|patch unexpectedly ends|saving rejects to file|malformed patch at line'; then
      echo "[ERROR]   $bn — patch dry-run emitted partial-application warning; marker NOT written" >&2
      printf '%s\n' "$out" | sed 's/^/  | /' >&2
      COUNT_FAILED=$((COUNT_FAILED + 1))
      return 1
    fi
    # Real apply: capture combined stderr+stdout (also with --verbose) so the
    # same warning patterns are screened on the actual application — defence in
    # depth in case dry-run and real-apply diverge.
    apply_out="$(patch $opts --verbose --forward < "$fragment" 2>&1)" && apply_rc=0 || apply_rc=$?
    if [ "$apply_rc" -ne 0 ] || printf '%s\n' "$apply_out" | grep -Eq 'Ignoring the trailing garbage|Hunk #[0-9]+ FAILED|patch unexpectedly ends|saving rejects to file|malformed patch at line'; then
      echo "[ERROR]   $bn — patch emitted warnings or non-zero exit; marker NOT written" >&2
      printf '%s\n' "$apply_out" | sed 's/^/  | /' >&2
      COUNT_FAILED=$((COUNT_FAILED + 1))
      return 1
    fi
    marker_add "$bn"
    echo "[APPLIED] $bn"
    COUNT_APPLIED=$((COUNT_APPLIED + 1))
    return 0
  fi
  if printf '%s\n' "$out" | grep -q "Reversed (or previously applied) patch detected"; then
    marker_add "$bn"
    echo "[SKIP]    $bn (already applied)"
    COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
    return 0
  fi
  if patch $opts --dry-run --reverse --force < "$fragment" >/dev/null 2>&1; then
    marker_add "$bn"
    echo "[SKIP]    $bn (already applied)"
    COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
    return 0
  fi
  echo "[ERROR]   $bn — neither forward nor reverse dry-run succeeded; check for anchor conflict or corrupt dist" >&2
  COUNT_FAILED=$((COUNT_FAILED + 1))
  return 1
}

echo "Applying legacy patches..."
apply_legacy "$PATCH_DIR/authManager.patch"  "$TARGET/auth/authManager.js"  || true
apply_legacy "$PATCH_DIR/rednoteTools.patch" "$TARGET/tools/rednoteTools.js" || true

if [ -d "$STEALTH_DIR" ]; then
  echo "Applying stealth fragments..."
  # `*.diff` glob is NOT recursive — aggregator-input/ subdirectory is excluded
  # by design. `sort -V` provides deterministic ordering (P0-1, P0-3, P0-3b,
  # P0-4-clicks, P0-9-W5-composed-ctx, P1.5-1..7, P1.5-14-auth).
  fragments=$(ls "$STEALTH_DIR"/*.diff 2>/dev/null | sort -V || true)
  if [ -z "$fragments" ]; then
    echo "(no fragments found in $STEALTH_DIR)"
  else
    for f in $fragments; do
      apply_fragment "$f" || true
    done
  fi
fi

echo "----- Summary -----"
echo "total=${COUNT_TOTAL} applied=${COUNT_APPLIED} skipped=${COUNT_SKIPPED} failed=${COUNT_FAILED}"

if [ "$COUNT_FAILED" -gt 0 ]; then
  echo "One or more patches failed. See [ERROR] lines above." >&2
  exit 1
fi
echo "Done. All patches applied to rednote-mcp."
exit 0
