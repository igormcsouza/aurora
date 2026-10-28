#!/usr/bin/env bash
# Install Aurora. One command:
#   curl -fsSL https://raw.githubusercontent.com/igormcsouza/aurora/main/install.sh | bash
# Choose the host non-interactively with:  ... | bash -s -- --target claude|codex|both|other [--skills DIR --agents DIR]
# Idempotent; symlinks only (so `git pull` updates the live skill); never overwrites a real file/dir.
set -eu

REPO_URL="${AURORA_REPO:-https://github.com/igormcsouza/aurora.git}"
TARGET=""; SKILLS_DIR=""; AGENTS_DIR=""; REPO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="$2"; shift 2;;
    --skills) SKILLS_DIR="$2"; shift 2;;
    --agents) AGENTS_DIR="$2"; shift 2;;
    --dir) REPO="$2"; shift 2;;
    -h|--help) sed -n 2,5p "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 2;;
  esac
done

# 1. Find or fetch the repo. Run from a clone: use it. Piped from curl: clone to ~/.aurora (or --dir).
if [ -z "$REPO" ]; then
  SELF="${BASH_SOURCE[0]:-}"
  if [ -n "$SELF" ] && [ -f "$SELF" ] && [ -d "$(dirname "$SELF")/skills/aurora" ]; then REPO="$(cd "$(dirname "$SELF")" && pwd)"
  else REPO="${AURORA_HOME:-$HOME/.aurora}"; fi
fi
if [ ! -d "$REPO/skills/aurora" ]; then
  command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 2; }
  git clone --depth 1 "$REPO_URL" "$REPO"
elif [ -d "$REPO/.git" ] && [ -z "$(git -C "$REPO" status --porcelain)" ]; then
  git -C "$REPO" pull --ff-only -q || echo "note: could not update $REPO (continuing with what is there)"
fi

# 2. Ask where to install (a pipe has no stdin, so read from the terminal).
ask() { # ask <prompt> <default> -> answer on stdout
  if [ -r /dev/tty ] && : 2>/dev/null </dev/tty; then printf '%s' "$1" >/dev/tty; read -r a </dev/tty || a=""; echo "${a:-$2}"
  else echo "$2"; fi
}
if [ -z "$TARGET" ]; then
  TARGET=$(ask "Install Aurora for: [1] Claude Code  [2] Codex  [3] both  [4] other (you give the folders)  (default 1): " 1)
fi
case "$TARGET" in 1|claude) TARGET=claude;; 2|codex) TARGET=codex;; 3|both) TARGET=both;; 4|other) TARGET=other;;
  *) echo "unknown target: $TARGET (use claude, codex, both or other)" >&2; exit 2;; esac

rc=0
link() { # link <source> <target>
  if [ -L "$2" ]; then
    [ "$(readlink "$2")" = "$1" ] && { echo "ok       $2"; return; }
    ln -sfn "$1" "$2" && echo "relinked $2 -> $1"
  elif [ -e "$2" ]; then echo "SKIPPED  $2 exists and is not a symlink (move it away first)"; rc=1
  else ln -s "$1" "$2" && echo "linked   $2 -> $1"; fi
}
install_into() { # install_into <skills dir> <agents dir>
  mkdir -p "$1" "$2"
  link "$REPO/skills/aurora" "$1/aurora"
  for f in "$REPO"/agents/*.md; do link "$f" "$2/$(basename "$f")"; done
}

case "$TARGET" in
  claude|both) install_into "${CLAUDE_HOME:-$HOME/.claude}/skills" "${CLAUDE_HOME:-$HOME/.claude}/agents";;
esac
case "$TARGET" in
  codex|both) install_into "${CODEX_SKILLS:-$HOME/.agents/skills}" "${CODEX_AGENTS:-$HOME/.agents/agents}";;
esac
if [ "$TARGET" = other ]; then
  [ -n "$SKILLS_DIR" ] || SKILLS_DIR=$(ask "Skills folder of your host (the skill is linked as <folder>/aurora): " "")
  [ -n "$AGENTS_DIR" ] || AGENTS_DIR=$(ask "Folder for the role briefs (default: <skills folder>/../agents): " "$(dirname "$SKILLS_DIR")/agents")
  [ -n "$SKILLS_DIR" ] || { echo "a skills folder is required for 'other'" >&2; exit 2; }
  install_into "$SKILLS_DIR" "$AGENTS_DIR"
  echo "Other hosts: point the host at $SKILLS_DIR/aurora/SKILL.md; the role briefs in $AGENTS_DIR are plain Markdown."
fi

echo "Aurora is in $REPO. Start a new session in your host so the skill loads, cd into your channel project and run: aurora interview"
exit $rc
