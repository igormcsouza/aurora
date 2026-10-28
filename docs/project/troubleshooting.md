# Troubleshooting

**`/aurora` is unknown.** Skills load at session start. Run `./install.sh`, check `ls -l ~/.claude/skills/aurora`, start a new session.

**`SKIPPED ... exists and is not a symlink`.** A real file or directory with that name is in `~/.claude`. Move it away (for example an old copy of the skill), rerun `./install.sh`.

**Agents not found mid-session.** Agents added during a session are not registered until the next one. Aurora falls back to a general agent plus the role brief.

**Preflight exits 1.** System packages missing. It prints the exact `sudo apt install` line; run it and retry. Exit 2 means the Python setup failed; read the last 30 log lines.

**Blocky or corrupted draft playback.** Drafts are low bitrate on purpose. Check the file with `ffmpeg -v error -i file -f null -` (clean output = file is fine), then disable hardware decoding in the player (`vlc --avcodec-hw=none file`).

**Doubled subtitles.** Players auto-load a same-name `.srt`. Aurora names the draft subtitles differently; keep it that way.

**Voice slides into another accent in long scenes.** Sentence-by-sentence requests with context and a fixed seed prevent it (the default). Retakes go to `voice_samples/` for you to pick by ear.

**YouTube rejects the description.** No `<` or `>` (arrows count), at most 5000 characters and 5000 UTF-8 bytes. `slop_check.py` checks both.

**Parallel Manim renders clash.** Known: the media cache is shared. Render Manim scenes one at a time for now.

**Stale scenes after a kit update.** Any kit change invalidates every scene hash; re-render all scenes.

**Nothing from a free model.** Run `/aurora selftest`. A failure that is not the card's fault is data: Aurora retries on another harness at the same tier.
