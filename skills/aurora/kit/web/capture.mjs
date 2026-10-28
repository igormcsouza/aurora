#!/usr/bin/env node
// node capture.mjs <spec.json> <out.mp4> [--draft] [--fps 30]
// Renders one scene (silent) frame by frame: seek(t) -> screenshot -> ffmpeg. Draft = 1280x720 q-low, final = 1920x1080 CRF 17.
import { chromium } from 'playwright'; import fs from 'fs'; import path from 'path'; import { spawnSync } from 'child_process'; import { fileURLToPath, pathToFileURL } from 'url';
const [specPath, out] = process.argv.slice(2), draft = process.argv.includes('--draft'), fps = process.argv.includes('--fps') ? +process.argv[process.argv.indexOf('--fps') + 1] : 30;
if (!specPath || !out) { console.error('usage: capture.mjs <spec.json> <out.mp4> [--draft] [--fps 30]'); process.exit(2); }
const here = path.dirname(fileURLToPath(import.meta.url)), spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
spec.base = pathToFileURL(path.dirname(path.resolve(specPath))).href + '/';
const tmp = out.replace(/\.mp4$/, '') + '_frames'; fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp, { recursive: true });
const b = await chromium.launch({ args: ['--font-render-hinting=none', '--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: draft ? 2 / 3 : 1 });
p.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exitCode = 1; });
await p.addInitScript(s => { window.__SPEC__ = s; }, spec);
await p.goto(pathToFileURL(path.join(here, 'engine.html')).href); await p.evaluate(() => window.settle()); await p.waitForTimeout(300);
const frames = Math.round(spec.duration * fps);
for (let i = 0; i < frames; i++) {
  await p.evaluate(t => window.seek(t), i / fps); await p.evaluate(() => window.settle());
  await p.screenshot({ path: path.join(tmp, String(i).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: draft ? 75 : 94 });
}
await b.close();
const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-i', path.join(tmp, '%05d.jpg'), '-c:v', 'libx264', '-crf', draft ? '27' : '17', '-pix_fmt', 'yuv420p', '-an', out], { stdio: 'inherit' });
fs.rmSync(tmp, { recursive: true, force: true }); process.exit(r.status || process.exitCode || 0);
