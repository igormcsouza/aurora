# Quickstart

Run everything from your channel project root. Every step has a worked example with the output to expect in [Examples](../guide/examples.md).

## 1. Tell Aurora about the channel

```text
/aurora interview
```

A short conversation (usually 8-15 exchanges): audience, niche, language, the narrator persona and her story, tone and humor, voice, palette, mascot, topics you love or avoid, how involved you want to be. Aurora then writes [`preferences.json`](../guide/preferences.md) and adds a `## Video preferences` section to your `CLAUDE.md` / `AGENTS.md`.

Optional, once per machine:

```text
/aurora selftest
```

It runs one trivial task on each free/cheap model tier to prove they work here (a few cents).

## 2. Make a video

=== "From your idea"

    ```text
    /aurora create "why sourdough starters fail"
    ```

=== "Let Aurora find the theme"

    ```text
    /aurora create auto
    ```

    She searches trends filtered by your `topics_like` / `topics_avoid` and by what `aurora/insights.md` says works, picks a theme, tells you in one line, and carries on.

Aurora runs preflight, researches, plans, writes the script, records the voice, and renders a **low-quality draft** with the scene number burned into the top-right corner.

## 3. Review the draft

You get the draft path, a summary, and what is verified versus unverified (audio is always unverified by the assistant: only your ear judges it). Answer by scene:

```text
scene 10: the joke is too slow
```

Only the named scenes are redone. General notes ("voice too fast") are stored as [feedback](../guide/commands.md#feedback) for all next videos.

## 4. Final and package

Once you approve, Aurora renders the final (no badge), mixes loudness, and builds `package/`: `video.mp4`, three thumbnails, `subtitles.srt` and `package.md` with titles, description, tags and pinned comment. The anti-slop gate runs first and a FAIL blocks packaging.

## 5. Upload, then publish

Upload in YouTube Studio using `package.md`, then:

```text
/aurora publish <slug>
```

This moves the video to `published_videos/`, keeps what rebuilds it and trashes the rest (reversibly). Later, feed results back:

```text
/aurora analise ~/Downloads/studio-export.zip
```

## A week at a time

```text
/aurora batch
```

You approve 7 themes once; Aurora builds seven drafts; you review them whenever you like with `/aurora review` ("drafts 1, 3 approved; draft 2 has an issue at scene 5").
