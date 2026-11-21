#!/usr/bin/env node
// node render_web.mjs <scenes_dir> <out_dir> [--draft] [--jobs N] [--only id,id] [--force]
// Renders every web scene of <scenes_dir>/spec.json (array, or {scenes:[...]}) with capture.mjs, N at a time, skipping scenes whose cache hash is unchanged.
// Hash = scene spec + custom scene file + its words + files named in props + engine/motion/templates/capture source + draft flag. Sidecar: <out_dir>/<id>.hash
// (audio is not part of it: web clips are silent; duration is in the spec.)
import fs from 'fs'; import path from 'path'; import os from 'os'; import crypto from 'crypto'; import { spawn } from 'child_process'; import { fileURLToPath } from 'url';
const a = process.argv.slice(2), flag = n => a.includes(n), val = n => flag(n) ? a[a.indexOf(n) + 1] : null;
const [dir, out] = a.filter((x, i) => !x.startsWith('--') && !(i && ['--jobs', '--only'].includes(a[i - 1])));
if (!dir || !out) { console.error('usage: render_web.mjs <scenes_dir> <out_dir> [--draft] [--jobs N] [--only id,id] [--force]'); process.exit(2); }
const here = path.dirname(fileURLToPath(import.meta.url)), draft = flag('--draft'), jobs = +(val('--jobs') || Math.max(1, Math.min(4, Math.floor(os.cpus().length / 2)))), only = val('--only')?.split(',');
const raw = JSON.parse(fs.readFileSync(path.join(dir, 'spec.json'), 'utf8')), all = Array.isArray(raw) ? raw : raw.scenes || [];
const words = fs.existsSync(path.join(dir, 'words.json')) ? JSON.parse(fs.readFileSync(path.join(dir, 'words.json'), 'utf8')) : {};
const kit = ['engine.html', 'motion.js', 'templates.js', 'capture.mjs'].map(f => fs.readFileSync(path.join(here, f))).join('');
const files = (v, acc = []) => { if (typeof v === 'string') { const f = path.join(dir, v); try { if (fs.statSync(f).isFile()) acc.push(fs.readFileSync(f)); } catch {} } else if (v && typeof v === 'object') Object.values(v).forEach(x => files(x, acc)); return acc; };
export const hashOf = s => crypto.createHash('sha1').update(JSON.stringify([s, words[s.id], draft, kit, files(s).map(b => crypto.createHash('sha1').update(b).digest('hex'))])).digest('hex').slice(0, 16);
fs.mkdirSync(out, { recursive: true });
const todo = all.filter(s => (s.engine || 'web') === 'web' && (!only || only.includes(String(s.id))));
let ok = 0, skipped = 0, failed = [], i = 0;
const run = s => new Promise(res => {
  const id = s.id, mp4 = path.join(out, `${id}.mp4`), hf = path.join(out, `${id}.hash`), h = hashOf(s);
  if (!flag('--force') && fs.existsSync(mp4) && fs.existsSync(hf) && fs.readFileSync(hf, 'utf8') === h) { skipped++; return res(); }
  const sp = path.join(dir, `.spec_${id}.json`); fs.writeFileSync(sp, JSON.stringify(s));
  const t0 = Date.now(), c = spawn('node', [path.join(here, 'capture.mjs'), sp, mp4, ...(draft ? ['--draft'] : [])], { stdio: ['ignore', 'ignore', 'inherit'] });
  c.on('exit', code => { fs.rmSync(sp, { force: true }); if (code === 0) { fs.writeFileSync(hf, h); ok++; console.log(`scene ${id}: ${((Date.now() - t0) / 1000).toFixed(0)}s`); } else { failed.push(id); fs.rmSync(hf, { force: true }); } res(); });
});
await Promise.all(Array.from({ length: Math.min(jobs, todo.length) }, async () => { while (i < todo.length) await run(todo[i++]); }));
console.log(`web scenes: ${ok} rendered, ${skipped} cached${failed.length ? ', FAILED: ' + failed.join(',') : ''}`); process.exit(failed.length ? 1 : 0);
