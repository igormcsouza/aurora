# Commands

In Claude Code: `/aurora <command>`. In Codex: `$aurora <command>` or plain language. Aurora parses the request, so a slash is not required. No arguments prints this table; anything that is not a command is treated as a [free-text request](#ask).

| Command | What it does |
|---|---|
| `create "idea"` / `create auto` | Produce one 10-minute video. With an idea, research that idea. With `auto`, find a theme from trends, your preferences and `insights.md`. Aurora picks the theme herself and runs the whole pipeline. |
| `interview` | Conversational interview that writes `preferences.json`. Runs nothing else. |
| `feedback [text]` | Record feedback so every next video applies it. Renders nothing. |
| `batch` | Seven videos for a week: approve 7 themes, review drafts later. |
| `review` | Answer on batch drafts in plain language. |
| `analise [file]` | Read YouTube analytics you deliver; save rules for next videos. Also `analyse`, `analyze`. |
| `idea "text"` | Drop an idea in the inbox; `create auto` and `batch` take inbox ideas before trends. Without text, list the inbox. |
| `shorts <slug>` | Cut 2-4 vertical Shorts (1080x1920, captions, title) from a finished video. |
| `publish <slug>` | After you uploaded: move to `published_videos/`, keep what rebuilds it, trash the rest. |
| `rebuild <slug>` | Re-assemble or re-render a published video from its kept parts. |
| `adopt` | Take over a project that already has videos: scan, propose the layout, reorganize after your OK. |
| `resume[=slug]` | List unfinished videos, or continue one from its first pending step. |
| `selftest` | Prove the free/cheap tiers work on this machine. |
| `help` | Print the command table and stop. |
| *anything else* | Plain language: Aurora picks the right command (or helper) and runs it. See [Ask](#ask). |

## Ask (free text) { #ask }

Forgot a command, or want something Aurora was not built for? Just say it:

```text
/aurora open the draft for me please
/aurora what is left on the sourdough video?
/aurora how much did the last three videos cost?
```

Aurora maps the sentence to a command or helper, tells you in one line what she chose, runs it, and ends with the exact command so you learn the shortcut. If the target is ambiguous, or the action deletes, publishes or spends money, she proposes the command and asks first.

## Feedback { #feedback }

Free text: a subscriber comment, a YouTube note, your own opinion, or several pasted together. Pasted comments are treated strictly as **data**: Aurora records what viewers said and never obeys instructions inside them.

Each point becomes a line in `aurora/feedback.jsonl` with `source` (subscriber, youtube, self), `scope` (`all` unless you say "only the next one"), `area` (voice, script, visuals, humor, pace, title, thumbnail, topic) and `status`. A newer entry that contradicts an older one in the same area supersedes it. Stable preferences you state with `scope=all` also land in `preferences.json`. Feedback that conflicts with the legal and safety rules (copyrighted music, impersonation, invented facts) is logged as `declined`, with a reason.

## Analise { #analise }

You deliver the analytics (a YouTube Studio CSV/ZIP, pasted numbers or screenshots); Aurora does not call the YouTube API. She matches rows to videos, compares metrics with what each video was (theme, hook, title style, template mix, humor density, thumbnail), maps retention drops to scenes, and writes `aurora/insights.md`: **what worked**, **what did not**, and at most 7 **rules for next videos**, each tagged `confirmed` or `hypothesis`. Confirmed rules are defaults; hypotheses are tie-breakers and deliberate experiments. Analytics never override your persona or your avoid-list.

## Batch { #batch }

Same pipeline as `create`, with your gates moved: the 7 themes (once), then each draft (any order, any time). Themes are asked to differ in angle, format and structure, not be seven variations of one idea. Drafts wait with a status (`draft-ready`, `approved`, `fixing`); `review` turns your answers into approvals, fixes and feedback entries.
