# Checkpoint Recovery — refs/checkpoints/<branch>

> Last updated: 2026-05-06
> Spec: docs/dev/specs/spec-20260506-092951.md §5.4

## Why this exists

Two auto-commit hooks used to advance `master` HEAD on every PostToolUse / Stop
event (`posttool-git-checkpoint.sh` + `stop-git-commit.sh`). In a 90-minute
session they produced 13+ `Auto-commit:` entries on master, drowning the real
project history in noise.

Per spec §5.4 the user demanded `Auto-commit 不应该淹没 git log` — auto-commit
should not pollute HEAD. Both hooks now write to a side-ref namespace
`refs/checkpoints/<current-branch>` via `git commit-tree` + `git update-ref`.
**HEAD on every branch advances ONLY on**:

1. Explicit user `git commit`
2. `/commit` slash command
3. `/merge` slash command

## How checkpoints are written

```
TMP_INDEX=$(mktemp …)                              # never touches user's index
GIT_INDEX_FILE=$TMP_INDEX git read-tree HEAD       # base on HEAD
GIT_INDEX_FILE=$TMP_INDEX git add -A               # stage everything
TREE=$(GIT_INDEX_FILE=$TMP_INDEX git write-tree)
PARENT=$(git rev-parse refs/checkpoints/<branch> || git rev-parse HEAD)
COMMIT=$(echo "checkpoint: …" | git commit-tree $TREE -p $PARENT)
git update-ref refs/checkpoints/<branch> $COMMIT
```

The result is a parallel commit graph rooted at the same HEAD that never
intersects the branch's published history.

## Inspecting checkpoints

```bash
# What checkpoints exist for the current branch?
git for-each-ref refs/checkpoints/

# Recent checkpoint history for master:
git log --oneline refs/checkpoints/master | head -50

# Diff a checkpoint against HEAD:
git diff HEAD refs/checkpoints/master

# Show files changed in the most recent checkpoint:
git show --stat refs/checkpoints/master

# Compare two checkpoints:
git log --oneline refs/checkpoints/master~5..refs/checkpoints/master
```

## Recovery scenarios

### 1. Session crashed, recover lost work into a fresh branch

```bash
# Find the checkpoint with the work you lost
git log --oneline refs/checkpoints/master | head

# Cherry-pick onto a recovery branch
git checkout -b recover-from-checkpoint
git cherry-pick <checkpoint-sha>
# Resolve any conflicts, then make a real commit on the recovery branch.
```

### 2. Restore one file from a checkpoint

```bash
git checkout refs/checkpoints/master -- path/to/lost/file.json
```

### 3. Reset the checkpoint pointer (drop accumulated noise)

```bash
git update-ref -d refs/checkpoints/master
# Next PostToolUse / Stop event will recreate it from HEAD.
```

### 4. Promote a checkpoint to a real commit

```bash
# Pick the checkpoint
git diff HEAD refs/checkpoints/master  # review
git checkout -b promote-checkpoint
git read-tree -u refs/checkpoints/master
git commit -m "feat: <real description of the work>"
# Then PR / merge as usual.
```

### 5. Push a checkpoint to a remote (e.g. for cross-machine recovery)

```bash
git push origin refs/checkpoints/master:refs/checkpoints/master
# On the other machine:
git fetch origin '+refs/checkpoints/*:refs/checkpoints/*'
git log --oneline refs/checkpoints/master
```

## Garbage-collection considerations

`refs/checkpoints/<branch>` is a real ref, so the commits it points at are
NOT garbage-collected. If you want to discard older snapshots, manually
move the ref forward (e.g. point it at the most recent checkpoint and let
older ones become unreachable, then `git gc`).

```bash
LATEST=$(git rev-parse refs/checkpoints/master)
git update-ref refs/checkpoints/master "$LATEST"
# (idempotent — the ref already points there; older snapshots are now
# unreachable from this ref)
```

## What still advances HEAD

| Action | Advances HEAD? | Notes |
|--------|---------------|-------|
| User `git commit` | yes | the only intended path |
| `/commit` slash command | yes | when explicit user-initiated commit is requested |
| `/merge` slash command | yes | merge commits |
| PostToolUse posttool-git-checkpoint.sh | NO | writes refs/checkpoints/<branch> |
| Stop stop-git-commit.sh | NO | writes refs/checkpoints/<branch> |
| Other hooks | NO | unless explicitly invoking `git commit` themselves (audit + flag) |

## Audit checklist (when you suspect HEAD pollution returned)

```bash
# Find any hook that still calls `git commit` (excluding documentation).
grep -rln 'git commit' .claude/hooks/

# Find any hook that calls `git push`.
grep -rln 'git push' .claude/hooks/

# Either should return nothing for the auto-commit hooks above.
```

If any hook reintroduces `git commit` on a branch ref, treat that as a spec
§5.4 regression and fix it back to the `commit-tree` + `update-ref` pattern.
