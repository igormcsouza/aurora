# aurora: known issues and backlog

Tracked as GitHub issues in `igormcsouza/claude-kit` (label `enhancement`, `bug` or `documentation`); this file only indexes them and keeps the standing caveats. File new ones with `gh issue create --repo igormcsouza/claude-kit`.

| # | Topic |
|---|---|
| [#3](https://github.com/igormcsouza/claude-kit/issues/3) | YouTube API upload (private) + analytics pull |
| [#4](https://github.com/igormcsouza/claude-kit/issues/4) | Validate the reworked flows end to end on a real project |
| [#5](https://github.com/igormcsouza/claude-kit/issues/5) | Validate and tune the cost ladder (tiers, tether, privacy) |
| [#6](https://github.com/igormcsouza/claude-kit/issues/6) | Harden the web/Blender kit (mascot export, `common.py`, Blender hero) |
| [#7](https://github.com/igormcsouza/claude-kit/issues/7) | Script the `rebuild` command |
| [#8](https://github.com/igormcsouza/claude-kit/issues/8) | Validate `organize.py` on a real project, prune rules |
| [#9](https://github.com/igormcsouza/claude-kit/issues/9) | `install.sh`: dangling symlinks after renames |
| [#10](https://github.com/igormcsouza/claude-kit/issues/10) | Recommended permission allow-list for subagents |
| [#11](https://github.com/igormcsouza/claude-kit/issues/11) | Parallel Manim renders clash on the media cache |
| [#12](https://github.com/igormcsouza/claude-kit/issues/12) | TTS engine configurable in `preferences.json` |
| [#13](https://github.com/igormcsouza/claude-kit/issues/13) | Cost tracking improvements |
| [#14](https://github.com/igormcsouza/claude-kit/issues/14) | Shorts improvements |

## Standing caveats (not bugs)
- TTS needs internet and a paid ElevenLabs key (about $0.45 per 6 min at `eleven_v4`).
- Audio quality, intonation, pronunciation and joke quality need the user's ears; the draft review is the real check. The contact sheet only catches layout.
- Draft clips are low bitrate on purpose; blocky playback on a laptop is usually the player's hardware decode (VLC `--avcodec-hw=none`), not the file.
- Agents added mid-session are not registered until a new session; use `general-purpose` plus the role brief file.
- Description limit is enforced as 5000 characters AND 5000 UTF-8 bytes; `<` and `>` are banned in titles, description and tags (so no `->` arrows).
- Playwright's Chromium (~150 MB, first preflight) and Node 20+ are required for the web engine.
