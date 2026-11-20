#!/usr/bin/env node
// node capture.mjs <spec.json> <out.mp4> [--draft] [--fps 30] [--no-blur]
// Renders one scene (silent) frame by frame: seek(t) -> screenshot -> ffmpeg. Draft = 1280x720 q-low, final = 1920x1080 CRF 17.
// Words: spec.words = [{w,s,e}] (scene seconds), or, when absent, words.json (from kit/words.py) next to the spec or one folder up, key = spec.id.
// Motion blur: frames where the camera moves fast are shot as 4 sub-frames and averaged by ffmpeg (180 degree shutter); still frames cost nothing extra.
import { chromium } from 'playwright'; import fs from 'fs'; import path from 'path'; import { spawnSync } from 'child_process'; import { fileURLToPath, pathToFileURL } from 'url';
const [specPath, out] = process.argv.slice(2), draft = process.argv.includes('--draft'), fps = process.argv.includes('--fps') ? +process.argv[process.argv.indexOf('--fps') + 1] : 30;
if (!specPath || !out) { console.error('usage: capture.mjs <spec.json> <out.mp4> [--draft] [--fps 30] [--no-blur]'); process.exit(2); }
const here = path.dirname(fileURLToPath(import.meta.url)), spec = JSON.parse(fs.readFileSync(specPath, 'utf8')), specDir = path.dirname(path.resolve(specPath));
spec.base = pathToFileURL(specDir).href + '/';
if (!spec.words && spec.id !== undefined) for (const f of [path.join(specDir, 'words.json'), path.join(specDir, '..', 'words.json')]) if (fs.existsSync(f)) { spec.words = JSON.parse(fs.readFileSync(f, 'utf8'))[spec.id]; break; }
const tmp = out.replace(/\.mp4$/, '') + '_frames'; fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp, { recursive: true });
const b = await chromium.launch({ args: ['--font-render-hinting=none', '--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: draft ? 2 / 3 : 1 });
p.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exitCode = 1; });
await p.addInitScript(s => { window.__SPEC__ = s; }, spec);
await p.goto(pathToFileURL(path.join(here, 'engine.html')).href); await p.evaluate(() => window.settle()); await p.waitForTimeout(300);
const frames = Math.round(spec.duration * fps), SUB = 4, THR = 3; // px/frame of camera motion above which a frame gets sub-frames
const speeds = process.argv.includes('--no-blur') ? [] : await p.evaluate(f => window.camSpeeds(f), fps);
const blurred = speeds.filter(v => v > THR).length, q = draft ? 75 : 94, name = n => path.join(tmp, String(n).padStart(6, '0') + '.jpg');
const shot = async (t, n) => { await p.evaluate(t => window.seek(t), t); await p.evaluate(() => window.settle()); await p.screenshot({ path: name(n), type: 'jpeg', quality: q }); };
for (let i = 0; i < frames; i++) {
  if (!blurred) { await shot(i / fps, i); continue; }
  if (speeds[i] > THR) for (let j = 0; j < SUB; j++) await shot(i / fps + ((j + 0.5) / SUB - 0.5) * 0.5 / fps, i * SUB + j);
  else { await shot(i / fps, i * SUB); for (let j = 1; j < SUB; j++) fs.linkSync(name(i * SUB), name(i * SUB + j)); }
}
await b.close();
if (blurred) console.error(`motion blur on ${blurred}/${frames} frames`);
const vf = blurred ? ['-framerate', String(fps * SUB), '-i', path.join(tmp, '%06d.jpg'), '-vf', `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/(${fps}*TB)`, '-r', String(fps)] : ['-framerate', String(fps), '-i', path.join(tmp, '%06d.jpg')];
const r = spawnSync('ffmpeg', ['-v', 'error', '-y', ...vf, '-c:v', 'libx264', '-crf', draft ? '27' : '17', '-pix_fmt', 'yuv420p', '-an', out], { stdio: 'inherit' });
fs.rmSync(tmp, { recursive: true, force: true }); process.exit(r.status || process.exitCode || 0);
