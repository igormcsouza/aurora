#!/usr/bin/env bash
# Idempotent pre-run: check components, set up ./video-kit (project root). Prints only problems + a final status line.
# Exit 0 = ready, 1 = system packages missing (command printed), 2 = python setup failed.
set -u
KIT="${VIDEO_KIT:-$PWD/video-kit}"
missing_apt=()

need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1"; missing_apt+=("$2"); }; }
need python3 python3
need ffmpeg ffmpeg
need ffprobe ffmpeg
need pkg-config pkg-config
need gcc build-essential
for lib in cairo pangocairo; do
  pkg-config --exists "$lib" 2>/dev/null || { echo "MISSING: $lib dev files"; missing_apt+=(libcairo2-dev libpango1.0-dev); }
done
[ -f /usr/include/python3*/Python.h ] 2>/dev/null || ls /usr/include/python3*/Python.h >/dev/null 2>&1 || missing_apt+=(python3-dev)
command -v blender >/dev/null 2>&1 || echo "note: blender not installed (optional, intro/outro only)"

if [ ${#missing_apt[@]} -gt 0 ]; then
  pkgs=$(printf '%s\n' "${missing_apt[@]}" | sort -u | tr '\n' ' ')
  echo "ACTION: ask the user to run: sudo apt install -y $pkgs"
  exit 1
fi

mkdir -p draft_videos published_videos aurora
if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
  touch .gitignore; for l in "video-kit/.venv/" "video-kit/web/node_modules/" ".aurora_trash/"; do grep -qxF "$l" .gitignore || echo "$l" >> .gitignore; done
  echo "note: big media (mp4, mp3, frames) in draft_videos/ and published_videos/ is not git-ignored; use Git LFS or ignore them if the repo should stay small"
fi
mkdir -p "$KIT/music"
if command -v uv >/dev/null 2>&1; then
  RUN="uv run --project $KIT"
  [ -f "$KIT/pyproject.toml" ] || (cd "$KIT" && uv init --bare --name video-kit >/dev/null) || exit 2
  (cd "$KIT" && uv add --quiet manim pillow) || exit 2
else
  echo "note: uv not found, using python3 venv + pip (install uv to prefer it)"
  [ -d "$KIT/.venv" ] || python3 -m venv "$KIT/.venv" || exit 2
  "$KIT/.venv/bin/pip" install -q manim pillow || exit 2
  RUN="$KIT/.venv/bin"
fi

if [ -d "$KIT/.venv" ]; then
  if command -v uv >/dev/null 2>&1; then
    uv run --project "$KIT" python -c "import manim, PIL" || exit 2
  else
    "$KIT/.venv/bin/python" -c "import manim, PIL" || exit 2
  fi
fi
# --- visual kit: web engine (GSAP + Playwright), Blender helpers, polish script. Copied from the skill into the project's video-kit/.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; SRC="$HERE/kit"
command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 || { echo "ACTION: ask the user to install Node.js 20+ (nvm or apt install nodejs npm); the web scene engine needs it"; exit 1; }
mkdir -p "$KIT/web" "$KIT/blender/examples"
if [ "${1:-}" = "--refresh" ] || [ ! -f "$KIT/KIT_VERSION" ]; then
  # first run or explicit refresh: overwrite the shared kit files (project files like common.py are never touched)
  cp -f "$SRC"/web/{engine.html,templates.js,capture.mjs,record.mjs,package.json} "$KIT/web/"
  cp -f "$SRC"/blender/lib.py "$KIT/blender/"; cp -f "$SRC"/blender/examples/*.py "$KIT/blender/examples/"; cp -f "$SRC"/polish.sh "$KIT/"; cp -f "$SRC"/VERSION "$KIT/KIT_VERSION"
elif ! cmp -s "$SRC/VERSION" "$KIT/KIT_VERSION"; then
  echo "NOTE: the skill's visual kit is newer (v$(cat "$SRC/VERSION") vs v$(cat "$KIT/KIT_VERSION")). Run preflight.sh --refresh to update video-kit/web, blender and polish.sh (every scene clip becomes stale)."
fi
(cd "$KIT/web" && npm install --silent --no-audit --no-fund) || { echo "web kit: npm install failed"; exit 2; }
probe() { (cd "$KIT/web" && node -e "import('playwright').then(async m=>{const b=await m.chromium.launch();await b.close()})" >/dev/null 2>&1); }
probe || { echo "note: installing Playwright's Chromium (one-time, ~150 MB)"; (cd "$KIT/web" && npx --yes playwright install chromium >/dev/null 2>&1); probe || { echo "web kit: Chromium would not launch (read: cd $KIT/web && npx playwright install chromium)"; exit 2; }; }
command -v blender >/dev/null 2>&1 && BL="blender -b -P" || BL=""
for t in opencode tether bwrap; do command -v $t >/dev/null 2>&1 && TI="${TI:-}$t=yes " || TI="${TI:-}$t=NO "; done
echo "tiers: ${TI}(tier 0/1 minions need opencode or tether; opencode also needs bwrap; run /aurora selftest once)"
# Role agents are global (~/.claude/agents, symlinked from the aurora repo); nothing to copy per project.
echo "READY kit=$KIT run_prefix='$RUN' web='node $KIT/web/capture.mjs <spec.json> <out.mp4> [--draft]' blender='${BL:-unavailable} <script.py> -- anim <dir> [--draft]' polish='$KIT/polish.sh'"
