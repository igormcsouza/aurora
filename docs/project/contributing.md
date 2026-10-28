# Contributing

Aurora is a skill: most changes are edits to Markdown prompts, the rest are small helper scripts. Both get review.

The full guide is [CONTRIBUTING.md](https://github.com/igormcsouza/aurora/blob/main/CONTRIBUTING.md). The short version:

- **No channel-specific facts in the repo.** They belong in a project's `preferences.json`.
- **Deterministic rules go in scripts**, not prose.
- **Keep SKILL.md tight.** It is read on every run. Delete before you add.
- **Verify before claiming.** Prompts should make the model check files, not trust reports.

```bash
git clone https://github.com/igormcsouza/aurora.git && cd aurora && ./install.sh
bash -n install.sh skills/aurora/preflight.sh skills/aurora/kit/polish.sh
python3 -m py_compile skills/aurora/*.py skills/aurora/kit/*.py skills/aurora/kit/blender/*.py
uv sync --only-group docs && uv run mkdocs build --strict
```

## Repository map

| Path | What |
|---|---|
| `skills/aurora/SKILL.md` | The program: commands, pipeline, rules |
| `skills/aurora/state.py` | Per-video state, cost and token reports |
| `skills/aurora/tiers.py` | Cost-ladder router and run ledger |
| `skills/aurora/organize.py` | Scan, adopt, publish, trash |
| `skills/aurora/slop_check.py` | Anti-slop and metadata gate |
| `skills/aurora/preflight.sh` | Dependency check and `video-kit` setup |
| `skills/aurora/kit/` | Web, Blender and Manim render helpers, Shorts |
| `agents/` | `video-researcher`, `video-scriptwriter`, `video-animator`, `video-producer` |
