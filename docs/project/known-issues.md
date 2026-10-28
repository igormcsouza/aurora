# Known issues

The backlog is tracked as [GitHub issues](https://github.com/igormcsouza/aurora/issues) and indexed in [`skills/aurora/ISSUES.md`](https://github.com/igormcsouza/aurora/blob/main/skills/aurora/ISSUES.md).

## Standing caveats (not bugs)

- Voice needs internet and a paid ElevenLabs key (about $0.45 per 6 minutes at `eleven_v4`).
- Audio quality, intonation, pronunciation and joke quality need your ears. The contact sheet only catches layout.
- Draft clips are low bitrate on purpose.
- Playwright's Chromium (~150 MB, first preflight) and Node 20+ are required for the web engine.
- A template-driven pipeline with a synthetic voice is exactly the risk profile YouTube's "inauthentic content" policy targets. Variation, real sourcing and your review are the defense; Aurora gates on them but cannot judge originality.
