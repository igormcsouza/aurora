#!/usr/bin/env node
// Screen-record a real page into a numbered JPEG sequence for the screenshot_zoom template (P.video).
// node record.mjs <url> <out_dir> <seconds> [--actions actions.json] [--fps 10] [--width 1600] [--height 1000]
// actions.json: [{"at":1.0,"scroll":600},{"at":2.5,"click":"text=Multi-stage"},{"at":4,"hover":"a.foo"}]  (times in seconds, scroll = px, relative smooth)
// Rejects cookie banners when a "Reject all"/"Reject All" button exists. Review what was captured: redact personal data before use.
import { chromium } from 'playwright'; import fs from 'fs'; import path from 'path';
const [url, out, secs] = process.argv.slice(2), arg = (k, d) => process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d;
const fps = +arg('--fps', 10), W = +arg('--width', 1600), H = +arg('--height', 1000), actions = arg('--actions') ? JSON.parse(fs.readFileSync(arg('--actions'), 'utf8')) : [];
fs.mkdirSync(out, { recursive: true }); const b = await chromium.launch(), p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await p.goto(url, { waitUntil: 'networkidle' }); const rej = p.getByRole('button', { name: /reject all/i }); if (await rej.count()) await rej.first().click(); await p.waitForTimeout(500);
let ai = 0; const t0 = Date.now(), n = Math.round(secs * fps);
for (let i = 0; i < n; i++) {
  const t = i / fps; while (ai < actions.length && actions[ai].at <= t) { const a = actions[ai++]; if (a.scroll) await p.mouse.wheel(0, a.scroll); if (a.click) await p.click(a.click).catch(() => {}); if (a.hover) await p.hover(a.hover).catch(() => {}); }
  await p.screenshot({ path: path.join(out, String(i + 1).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 90 }); await p.waitForTimeout(Math.max(0, (i + 1) * 1000 / fps - (Date.now() - t0 - 0)));
}
await b.close(); console.log(`${n} frames -> ${out} (fps ${fps}, ${W}x${H})`);
