#!/usr/bin/env bash
# Symlink the aurora skill and its role agents into ~/.claude. Idempotent; never overwrites a real file/dir.
set -eu
REPO="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_HOME:-$HOME/.claude}"
mkdir -p "$DEST/skills" "$DEST/agents"
rc=0
link() { # link <source> <target>
  if [ -L "$2" ]; then
    [ "$(readlink "$2")" = "$1" ] && { echo "ok       $2"; return; }
    ln -sfn "$1" "$2" && echo "relinked $2 -> $1"
  elif [ -e "$2" ]; then echo "SKIPPED  $2 exists and is not a symlink (move it away first)"; rc=1
  else ln -s "$1" "$2" && echo "linked   $2 -> $1"; fi
}
link "$REPO/skills/aurora" "$DEST/skills/aurora"
for f in "$REPO"/agents/*.md; do link "$f" "$DEST/agents/$(basename "$f")"; done
echo "Start a new Claude Code session so the skill and agents load."
exit $rc
