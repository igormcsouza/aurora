# Examples

Each example shows what you type, what Aurora does, and what you should see. Wording of Aurora's replies varies; the files and the shape of the outcome do not. Every example uses `/aurora` (Claude Code); in Codex write `$aurora` or plain language.

## First run in a new project

```bash
mkdir my-channel && cd my-channel && git init
```

```text
/aurora interview
```

**Expected:** a chat of 8-15 short exchanges, then a 5-line summary and a request for corrections. Afterwards:

```text
preferences.json        # created
CLAUDE.md / AGENTS.md   # got a "## Video preferences" section
```

Nothing is rendered and no money is spent.

## Create a video from your idea

```text
/aurora create "why sourdough starters fail"
```

**Expected, in order:**

1. A **preflight** pass. First time only it installs the render kit into `./video-kit/` (a few minutes; Chromium is ~150 MB). The last line is `READY kit=... run_prefix='...'`. If something is missing you get an `ACTION:` line with the exact `sudo apt install ...` command; run it and rerun.
2. In a git repo, preflight updates `.gitignore` so videos, audio and render caches stay out of git. If it prints `ACTION: ask the user whether to version the logs`, Aurora asks you once; answer "keep" or "ignore".
3. A one-line theme statement ("Angle: your starter is not dead, your kitchen is cold") and then silence while the pipeline runs.
4. The **draft checkpoint**: path to the draft video, a short summary, what is verified and what is not (audio never is), minor open items.

```text
draft_videos/why-sourdough-starters-fail/
  state.json  plan.json  narration.md  sources.md
  scenes/  package/
```

Cost: the ElevenLabs voice (about $0.45 per 6 minutes) plus model tokens; `state.py cost <slug>` prints it at the end.

## Let Aurora choose the theme

```text
/aurora create auto
```

**Expected:** the same run, but Aurora searches (max 4 searches), filters by `topics_like` / `topics_avoid`, your inbox ideas and `aurora/insights.md`, then states the theme in one line before building. She does not ask which theme; if you do not like it, say so and she restarts the theme step.

## Review a draft

The draft has the scene number burned into the top-right corner. Answer by scene:

```text
scene 10: the joke is too slow, and scene 4 shows the wrong chart
```

**Expected:** "Redoing scenes 4 and 10." Only those scenes are re-rendered; you get the draft path again. Say `approved` and the final render, loudness mix and `package/` follow:

```text
package/video.mp4  thumbnail_a.png thumbnail_b.png thumbnail_c.png
package/subtitles.srt  package/package.md
```

## Feedback that sticks

```text
/aurora feedback "a subscriber says the voice is too fast; also, no more cooking puns please"
```

**Expected:** two lines saying 2 points were stored, both with `scope: all`, nothing declined. They are appended to `aurora/feedback.jsonl`, and the pace goes into `preferences.json`. Every next `create` and `batch` applies them and lists the applied entries in its summary. "Only for the next video" makes the scope `next`.

## A week of videos

```text
/aurora batch
```

**Expected:** a table of 7 themes (day, title, angle, takeaway) and the estimated voice cost of the week. Reply `ok`, or `swap 3 and 5`. Aurora then builds seven drafts one after the other and reports one line each:

```text
day 1 | why-sourdough-starters-fail | draft-ready | draft_videos/why-.../ | QA pass | audio unverified
```

Review whenever you like:

```text
/aurora review drafts 1, 3, 4 approved; draft 2 has an issue at the intro, the joke at scene 5 falls flat
```

## Resume where you stopped

```text
/aurora resume
```

**Expected:** one line per unfinished video, then a question if you gave no slug:

```text
why-sourdough-starters-fail     next=review   10min serial updated=2026-10-28  "why sourdough starters fail"
```

`/aurora resume=why-sourdough-starters-fail` continues at `next`; finished steps are never redone.

## Publish and tidy

```text
/aurora publish why-sourdough-starters-fail
```

**Expected:** Aurora asks for the YouTube URL and upload date, prints a **dry run** (what is kept, what goes to `.aurora_trash/`, with sizes) and waits for your OK. After it, the video lives in `published_videos/2026-10-28_why-sourdough-starters-fail/` with a `published.json`. Nothing is deleted for good; `.aurora_trash/` is emptied only when you say so.

## Shorts

```text
/aurora shorts why-sourdough-starters-fail
```

**Expected:** 2-4 vertical clips (1080x1920, captions, a title on top) and `shorts/shorts.md` with a title and description for each. You upload them yourself.

## Learn from analytics

```text
/aurora analise ~/Downloads/studio-export.zip
```

**Expected:** at most 5 lines: top findings, rules saved, and what data would sharpen the next analysis. The detail is in `aurora/insights.md`. With fewer than 5 videos every rule is marked `hypothesis`, and Aurora says so.

## Ask in plain language

```text
/aurora open the draft for me please
```

**Expected:** "Opening the draft of `why-sourdough-starters-fail` (most recently updated)", the video opens in your player, and the reply ends with the command that was run. More in [Ask](commands.md#ask).

## Bring an existing project

```text
/aurora adopt
```

**Expected:** a dry-run scan of your folders, then a question about which finished-looking videos you actually published (never guessed), then a plan with moves and a trash list. Nothing moves until you approve.
