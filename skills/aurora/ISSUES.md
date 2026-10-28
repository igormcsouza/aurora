# aurora: known issues and backlog

Tracked as GitHub issues in `igormcsouza/aurora` (label `enhancement`, `bug` or `documentation`); this file only indexes them and keeps the standing caveats. File new ones with `gh issue create --repo igormcsouza/aurora`.

| # | Topic |
|---|---|
| [#1](https://github.com/igormcsouza/aurora/issues/1) | YouTube API upload (private) + analytics pull |
| [#2](https://github.com/igormcsouza/aurora/issues/2) | Validate the reworked flows end to end on a real project |
| [#3](https://github.com/igormcsouza/aurora/issues/3) | Validate and tune the cost ladder (tiers, tether, privacy) |
| [#4](https://github.com/igormcsouza/aurora/issues/4) | Harden the web/Blender kit (mascot export, `common.py`, Blender hero) |
| [#5](https://github.com/igormcsouza/aurora/issues/5) | Script the `rebuild` command |
| [#6](https://github.com/igormcsouza/aurora/issues/6) | Validate `organize.py` on a real project, prune rules |
| [#7](https://github.com/igormcsouza/aurora/issues/7) | Recommended permission allow-list for subagents |
| [#8](https://github.com/igormcsouza/aurora/issues/8) | Parallel Manim renders clash on the media cache |
| [#9](https://github.com/igormcsouza/aurora/issues/9) | TTS engine configurable in `preferences.json` |
| [#10](https://github.com/igormcsouza/aurora/issues/10) | Cost tracking improvements |
| [#11](https://github.com/igormcsouza/aurora/issues/11) | Shorts improvements |
| [#12](https://github.com/igormcsouza/aurora/issues/12) | Self-contained: drop the dependency on gru |
| [#13](https://github.com/igormcsouza/aurora/issues/13) | install.sh: remove dangling symlinks after renames |

## Standing caveats (not bugs)
- TTS needs internet and a paid ElevenLabs key (about $0.45 per 6 min at `eleven_v4`).
- Audio quality, intonation, pronunciation and joke quality need the user's ears; the draft review is the real check. The contact sheet only catches layout.
- Draft clips are low bitrate on purpose; blocky playback on a laptop is usually the player's hardware decode (VLC `--avcodec-hw=none`), not the file.
- Agents added mid-session are not registered until a new session; use `general-purpose` plus the role brief file.
- Description limit is enforced as 5000 characters AND 5000 UTF-8 bytes; `<` and `>` are banned in titles, description and tags (so no `->` arrows).
- Playwright's Chromium (~150 MB, first preflight) and Node 20+ are required for the web engine.
