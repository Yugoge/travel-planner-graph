#!/bin/bash
# stop-git-commit.sh — Stop-hook: snapshot to refs/checkpoints/<branch> only.
#
# Per spec-20260506-092951.md §5.4 (Auto-commit 不应该淹没 git log):
# the prior version of this script ran `git add -A && git commit && git push`
# on every Stop event, producing 13+ Auto-commit entries on master in 90
# minutes. The new contract:
#
#   * NEVER call `git commit` (HEAD-advancing).
#   * NEVER call `git push` (would publish unauthored snapshots).
#   * Snapshot the working tree to refs/checkpoints/<current-branch> via
#     `git commit-tree` + `git update-ref`.
#
# Recovery: see docs/checkpoint-recovery.md.
# HEAD advances ONLY on explicit user `git commit`, /commit, or /merge.

set -e

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
if git diff --quiet && git diff --cached --quiet && [ "$UNTRACKED" -eq 0 ]; then
  exit 0
fi

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
CHECKPOINT_REF="refs/checkpoints/${CURRENT_BRANCH}"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

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

TOTAL=$(GIT_INDEX_FILE="$TMP_INDEX" git diff --cached --name-only HEAD 2>/dev/null | wc -l)

MSG="checkpoint: stop $TIMESTAMP

Files staged: $TOTAL
Branch: $CURRENT_BRANCH
Trigger: Stop hook
Ref: $CHECKPOINT_REF (HEAD never advances)
"

if [ -n "$PARENT" ]; then
  COMMIT=$(echo "$MSG" | git commit-tree "$TREE" -p "$PARENT") || exit 0
else
  COMMIT=$(echo "$MSG" | git commit-tree "$TREE") || exit 0
fi

git update-ref "$CHECKPOINT_REF" "$COMMIT"

SHORT=$(git rev-parse --short "$COMMIT" 2>/dev/null || echo "$COMMIT")
echo "stop checkpoint: $CHECKPOINT_REF -> $SHORT ($TOTAL files; HEAD untouched)"

exit 0
