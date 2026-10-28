# Install

## Requirements

| Needed for | What |
|---|---|
| Running Aurora | [Claude Code](https://claude.com/claude-code) (Codex also works, see [Tool compatibility](#codex)) |
| Voice | An `ELEVENLABS_API_KEY` in your environment (about $0.45 per 6 minutes at `eleven_v4`) |
| Assembly | `ffmpeg`, `ffprobe`, `python3` |
| Web engine | Node.js 20+; first preflight downloads Playwright's Chromium (~150 MB) |
| Manim engine | `libcairo2-dev libpango1.0-dev pkg-config python3-dev build-essential` (preflight prints the `apt` command) |
| Blender heroes | Blender 4.x, **optional** (`"blender": false` in preferences turns 3D off) |
| Free-model tiers | `tether` and/or `opencode`, plus `bwrap` for opencode, **optional** |

Never print or commit your API key. Put it in `~/.profile`:

```bash
export ELEVENLABS_API_KEY=...
```

## Install the skill

One command:

```bash
curl -fsSL https://raw.githubusercontent.com/igormcsouza/aurora/main/install.sh | bash
```

The installer clones Aurora to `~/.aurora` (override with `AURORA_HOME`) and asks which host to set up:

| Choice | Skill goes to | Role agents go to |
|---|---|---|
| 1. Claude Code (default) | `~/.claude/skills/aurora` | `~/.claude/agents/` |
| 2. Codex | `~/.agents/skills/aurora` | `~/.agents/agents/` |
| 3. Both | both of the above | both of the above |
| 4. Other | the folder you give | the folder you give (default: `agents` next to it) |

Skip the question by passing the choice:

```bash
curl -fsSL https://raw.githubusercontent.com/igormcsouza/aurora/main/install.sh | bash -s -- --target codex
curl -fsSL https://raw.githubusercontent.com/igormcsouza/aurora/main/install.sh | bash -s -- --target other --skills ~/.myhost/skills --agents ~/.myhost/agents
```

Expected output (one line per link; `ok` means it was already there):

```text
linked   /home/you/.claude/skills/aurora -> /home/you/.aurora/skills/aurora
linked   /home/you/.claude/agents/video-animator.md -> /home/you/.aurora/agents/video-animator.md
...
Aurora is in /home/you/.aurora. Start a new session in your host so the skill loads, ...
```

The installer is idempotent and never overwrites a real file: a `SKIPPED` line means a real file already uses that name; move it away and rerun. Then **start a new session** in your host: skills and agents load at session start. Prefer a manual install? `git clone` the repo anywhere and run `./install.sh` from it.

Because everything is symlinked, updating is rerunning the one-liner (it does a `git pull` in `~/.aurora`).

## Verify

```bash
ls -l ~/.claude/skills/aurora ~/.claude/agents/video-*.md
```

In a new session, `/aurora help` prints the command table and runs nothing else.

## Per-project setup

Nothing to install per project. From your channel project root, Aurora's **preflight** creates `./video-kit/` (render tooling), `draft_videos/` and `published_videos/` on first use and tells you about anything missing.

In a git repo, preflight also keeps the repository small by adding to `.gitignore`: videos, audio, Blender files, render caches and frames under `draft_videos/` and `published_videos/`, plus `video-kit/.venv/` and `video-kit/web/node_modules/`. Plans, scripts, specs and `aurora/` memory stay versioned. It asks once whether to version logs too (`*.log`); your answer is stored in `aurora/git_logs`, and you can change it with `preflight.sh --logs=keep` or `--logs=ignore`.

## Codex { #codex }

Aurora's workflow is host-neutral. `--target codex` links the skill into `~/.agents/skills/aurora` (for one project only, symlink it into that project's `.agents/skills/aurora` instead). Use plain language or `$aurora <command>`. Role briefs in `~/.agents/agents/` are read directly and passed to native subagents.

## Upgrading

```bash
curl -fsSL https://raw.githubusercontent.com/igormcsouza/aurora/main/install.sh | bash -s -- --target claude
```

(or `git pull` in `~/.aurora`). In an existing project, `preflight.sh --refresh` re-copies the shared kit files (your project's own `common.py` is never overwritten).
