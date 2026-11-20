# Render engines

Three engines, chosen **per scene** (`engine` in `plan.json`). Preflight sets them all up in `./video-kit/` in your project, never in your home directory.

| Engine | Best for | Notes |
|---|---|---|
| **web** | The default for most scenes: kinetic titles, stat reveals, layered builds, real screenshots and screen recordings | HTML/CSS + GSAP stepped frame by frame in headless Chromium (Playwright). Templates: `kinetic_title`, `layer_stack`, `screenshot_zoom`, `stat_reveal`. Theme from `preferences.json` `palette`. |
| **blender** | One or two hero moments, or the intro: physical metaphors, depth, physics | Headless Blender 4 with Eevee; scripts built on `video-kit/blender/lib.py`. Optional. |
| **manim** | Code, diffs, terminals, charts, exact geometry | JSON-driven templates: `code_diff`, `flow`, `reveal`, `terminal`, `chart`, `meme_card`, `hero`. |

## Choosing

| The scene needs to show | Use |
|---|---|
| A hook, claim, number or title card | web `kinetic_title` / `stat_reveal` |
| A sentence whose words should land on the spoken word (a claim, a definition, the punchline) | web `kinetic_words` |
| Something real: docs, repo, UI, dashboard | web `screenshot_zoom` (screenshot) or `record.mjs` (screen recording) |
| A process or build-up | web `layer_stack`, or Blender when depth sells it |
| The one memorable moment | Blender hero |
| Code, a diff, a terminal, a chart | Manim |

Target mix per 10-minute video: web 50-60% of runtime, Blender 10-20%, Manim 20-30%. Never more than two consecutive scenes with the same engine and template, and no static frame longer than about 2 seconds. When no template fits, add one to the kit instead of forcing it.

## Word clock, camera and motion

- **Word clock.** `python3 ~/.claude/skills/aurora/kit/words.py <video_dir>` turns the per-scene ElevenLabs alignment into `scenes/words.json`; `capture.mjs` hands it to every template. `kinetic_words` uses it so each word enters two frames before it is spoken. In a 10-minute video it is for the 2-4 moments per scene that deserve typography, not for the whole narration.
- **Camera.** Every web scene has one: a slow drift plus a quick push on each beat. Override with `camera: [{t,x,y,s,r}]` or turn it off with `camera: false`.
- **Motion blur.** Frames where the camera moves fast are shot as four sub-frames and averaged. Still frames cost nothing extra.
- **Motion presets** (`M.pop`, `M.smooth`, `M.soft` springs, `M.stagger`, `M.rand`) live in `kit/web/motion.js` for new templates.

## Speed

Drafts use `--draft` (web 1280x720, Blender half size, Manim `-ql`); the final renders once at full quality. Each scene is cached by a hash of its spec, audio and kit source: change anything in the kit and every scene re-renders.

## Screenshots and recordings

`node video-kit/web/record.mjs <url> <out_dir> <seconds> [--actions actions.json]` records a real, public page. Aurora rejects cookie banners, redacts personal data, records the URL and capture date in `visual_assets.md`, and credits the source on screen.

## Mascot

Optional. Two PNGs (mouth closed/open) plus speech windows from `cues.json` make the mascot lip-sync; she stays still otherwise, moves mainly at scene changes, and never covers text.
