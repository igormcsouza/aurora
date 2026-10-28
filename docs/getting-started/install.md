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

```bash
git clone https://github.com/igormcsouza/aurora.git ~/Projects/aurora
cd ~/Projects/aurora
./install.sh
```

`install.sh` is idempotent and never overwrites a real file. It creates:

- `~/.claude/skills/aurora` pointing to `skills/aurora`
- `~/.claude/agents/video-*.md` pointing to the four role agents

A `SKIPPED` line means a real file already uses that name; move it away and rerun. Then **start a new Claude Code session**: skills and agents load at session start.

Because the install is a symlink, `git pull` in the repo updates the live skill.

## Verify

```bash
ls -l ~/.claude/skills/aurora ~/.claude/agents/video-*.md
```

In a new session, `/aurora help` prints the command table and runs nothing else.

## Per-project setup

Nothing to install per project. From your channel project root, Aurora's **preflight** creates `./video-kit/` (render tooling), `draft_videos/` and `published_videos/` on first use and tells you about anything missing.

In a git repo, preflight also keeps the repository small by adding to `.gitignore`: videos, audio, Blender files, render caches and frames under `draft_videos/` and `published_videos/`, plus `video-kit/.venv/` and `video-kit/web/node_modules/`. Plans, scripts, specs and `aurora/` memory stay versioned. It asks once whether to version logs too (`*.log`); your answer is stored in `aurora/git_logs`, and you can change it with `preflight.sh --logs=keep` or `--logs=ignore`.

## Codex { #codex }

Aurora's workflow is host-neutral. In Codex, symlink the skill into `.agents/skills/aurora` of your project and use plain language or `$aurora <command>`. Role briefs in `agents/` are read directly and passed to native subagents.

## Upgrading

```bash
cd ~/Projects/aurora && git pull
```

In an existing project, `preflight.sh --refresh` re-copies the shared kit files (your project's own `common.py` is never overwritten).
