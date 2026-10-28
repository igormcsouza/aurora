# Aurora

**A YouTube content-creator assistant written in plain English.** No framework, no app, no server: Aurora is a [Claude Code](https://claude.com/claude-code) skill plus four role agents. You type `/aurora create "your idea"` and get back a finished 10-minute video with voice, animation, subtitles, three thumbnails and a paste-ready YouTube description.

[![License: MIT](https://img.shields.io/badge/License-MIT-7c3aed.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/Docs-igormcsouza.github.io%2Faurora-7c3aed)](https://igormcsouza.github.io/aurora/)
[![Runs on](https://img.shields.io/badge/Runs%20on-Claude%20Code%20%7C%20Codex-10b981)](#install)

---

## Why Aurora?

Most "AI video" tools are a pile of templates that stamp out the same video with swapped words. YouTube calls that slop, and demonetizes it. Aurora is built the other way round:

- **A narrator, not a voiceover.** Each channel defines a persona (name, story, lore, catchphrases) in one file. Aurora writes and narrates *as* that character, consistently, video after video.
- **Human in the loop at the right place.** One checkpoint per video: you review a draft with scene numbers burned into the corner ("scene 10: the joke is too slow"). Everything before runs unattended.
- **Facts are checked.** Every external claim carries a source URL or is cut or attributed. An anti-slop gate (`slop_check.py`) blocks packaging when the video looks templated, repeats earlier ones, or breaks YouTube's metadata rules.
- **It learns.** Feedback from subscribers or yourself and rules mined from your YouTube analytics are stored in your project and applied to every next video.
- **It is cheap to run.** A cost ladder pushes easy, bounded chores to free or small models and keeps the paid model for planning and checking.
- **It is software you can read.** The whole product is Markdown prompts plus a few small Python and Node helpers. Fork it, change a sentence, change the behavior.

## What you get per video

| Output | Details |
|---|---|
| `video.mp4` | 1080p, about 10 minutes, H.264, loudness-normalized |
| Voice | ElevenLabs narration with word-level timing, so visuals land on the right word |
| Visuals | Three engines picked per scene: **web** (HTML/GSAP via Playwright), **Blender** (3D hero moments) and **Manim** (code, charts, diagrams) |
| Subtitles | `subtitles.srt` built from the alignment |
| Thumbnails | Three variants (A/B/C) ready for YouTube's Test & compare |
| `package.md` | 3 title options, description with chapters and sources, tags, pinned comment |
| Shorts | 2-4 vertical clips cut from the finished video (`/aurora shorts`) |

## Commands

```text
/aurora interview                 # once per channel: persona, voice, palette, tone
/aurora create "why sourdough starters fail"
/aurora create auto               # theme from trends + your preferences + what worked before
/aurora feedback "the voice felt fast"
/aurora batch                     # a week of videos: approve 7 themes, review drafts later
/aurora analise ~/Downloads/studio-export.zip
/aurora shorts <slug>
/aurora publish <slug>
```

Full reference in the [docs](https://igormcsouza.github.io/aurora/guide/commands/).

## Install

```bash
git clone https://github.com/igormcsouza/aurora.git ~/Projects/aurora
cd ~/Projects/aurora && ./install.sh
```

`install.sh` symlinks the skill into `~/.claude/skills/` and the four agents into `~/.claude/agents/`. Start a new Claude Code session, `cd` into your channel project and run `/aurora interview`. You will need `ffmpeg`, Node.js 20+, Python 3 and an `ELEVENLABS_API_KEY`; Aurora's preflight checks everything and tells you exactly what is missing. See [Install](https://igormcsouza.github.io/aurora/getting-started/install/).

## How it is built

```text
skills/aurora/      SKILL.md (the program), state.py, tiers.py, organize.py, slop_check.py,
                    preflight.sh, kit/ (web, Blender and Manim render helpers)
agents/             video-researcher, video-scriptwriter, video-animator, video-producer
docs/               the mkdocs site
```

The skill is the program; the agents are its functions. Channel-specific facts never live here, they live in your project's `preferences.json`, so one install serves any number of channels in any language or niche.

## Contributing

Aurora is early and opinionated, and there is plenty to do: a YouTube API upload step, a configurable TTS engine, sturdier Blender heroes, more web templates, more engines. Read [CONTRIBUTING.md](CONTRIBUTING.md), pick something from the [known issues](skills/aurora/ISSUES.md), and open a PR. Improving a sentence in `SKILL.md` counts as a code change here.

## License

[MIT](LICENSE) © 2026 Igor Souza
