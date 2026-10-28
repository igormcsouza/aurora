# Contributing to Aurora

Aurora is a skill: most changes are edits to Markdown prompts, and the rest are small helper scripts. Both deserve review.

## Ground rules

- **No channel-specific facts in the repo.** Voices, personas, palettes, channel names, paths of a particular project belong in a project's `preferences.json`, never in `skills/aurora/` or `agents/`.
- **Never claim what was not verified.** Prompts must make the model verify files on disk instead of trusting a delegate's report. Keep that tone.
- **Deterministic work goes in scripts.** If a rule can be checked by code (`slop_check.py`, `state.py`, `tiers.py`, `organize.py`), put it in code, not in prose.
- **Keep prompts tight.** SKILL.md is read on every run. Delete before you add.

## Setup

```bash
git clone https://github.com/igormcsouza/aurora.git
cd aurora && ./install.sh          # symlinks the skill and agents into ~/.claude
```

Because the install is a symlink, editing a file in the repo changes the live skill at once. Start a new Claude Code session to reload.

## Before you open a PR

```bash
bash -n install.sh skills/aurora/preflight.sh skills/aurora/kit/polish.sh
python3 -m py_compile skills/aurora/*.py skills/aurora/kit/*.py skills/aurora/kit/blender/*.py
uv sync --only-group docs && uv run mkdocs build --strict    # if you touched docs/
```

Try the change on a real or throwaway channel project (`/aurora selftest` is a cheap sanity check for the cost ladder). Say in the PR what you ran and what you could not verify (audio, for example, only a human ear can judge).

## What to work on

See [skills/aurora/ISSUES.md](skills/aurora/ISSUES.md) and the GitHub issues. Good first areas: new `web` templates in `kit/web/templates.js`, docs, and anything that makes a failure message clearer.

## License

By contributing you agree that your work is released under the [MIT license](LICENSE).
