#!/bin/bash
# posttool-git-checkpoint.sh — refs/checkpoints/<branch> auto-checkpoint.
#
# Per spec-20260506-092951.md §5.4 (Auto-commit 不应该淹没 git log):
# this hook MUST NEVER advance HEAD. It writes only to
# refs/checkpoints/<current-branch> via git update-ref so that:
#   1. `git log <branch>` shows only logical commits the user authored.
#   2. Per-cycle recovery snapshots remain available under
#      `git log refs/checkpoints/<branch>`.
#
# Recovery: see docs/checkpoint-recovery.md.
# Migration note: previous implementation called `git commit` + `git push`
# (HEAD-advancing) — that behaviour is the regression this file fixes.

set -e

CHECKPOINT_THRESHOLD=${GIT_CHECKPOINT_THRESHOLD:-10}
SILENT_MODE=${GIT_CHECKPOINT_SILENT:-0}

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l)
MODIFIED=$(git diff --name-only 2>/dev/null | wc -l)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
TOTAL=$((STAGED + MODIFIED + UNTRACKED))

if [ "$TOTAL" -eq 0 ]; then
  exit 0
fi

if [ "$TOTAL" -lt "$CHECKPOINT_THRESHOLD" ]; then
  exit 0
fi

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
CHECKPOINT_REF="refs/checkpoints/${CURRENT_BRANCH}"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Use a temporary index so we never disturb the user's staging area or HEAD.
TMP_INDEX="$(mktemp -t claude-cp-index.XXXXXX)"
trap 'rm -f "$TMP_INDEX"' EXIT
GIT_INDEX_FILE="$TMP_INDEX" git read-tree HEAD 2>/dev/null || true
GIT_INDEX_FILE="$TMP_INDEX" git add -A 2>/dev/null

TREE=$(GIT_INDEX_FILE="$TMP_INDEX" git write-tree 2>/dev/null) || exit 0

if PARENT=$(git rev-parse "$CHECKPOINT_REF" 2>/dev/null); then
  :
elif PARENT=$(git rev-parse HEAD 2>/dev/null); then
  :
else
  PARENT=""
fi

MSG="checkpoint: posttool $TIMESTAMP

Files staged: $TOTAL
Branch: $CURRENT_BRANCH
Trigger: PostToolUse Write|Edit|NotebookEdit
Ref: $CHECKPOINT_REF (HEAD never advances)
"

if [ -n "$PARENT" ]; then
  COMMIT=$(echo "$MSG" | git commit-tree "$TREE" -p "$PARENT") || exit 0
else
  COMMIT=$(echo "$MSG" | git commit-tree "$TREE") || exit 0
fi

git update-ref "$CHECKPOINT_REF" "$COMMIT"

if [ "$SILENT_MODE" != "1" ]; then
  SHORT=$(git rev-parse --short "$COMMIT" 2>/dev/null || echo "$COMMIT")
  echo "checkpoint: $CHECKPOINT_REF -> $SHORT ($TOTAL files; HEAD untouched)"
fi

exit 0
