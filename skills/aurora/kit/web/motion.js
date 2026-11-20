// aurora motion kit: pure functions of time (no wall clock), shared by every web template.
//   MOTION.pop / MOTION.smooth   spring eases for GSAP: {ease, dur}  -> tl.to(el, {y:0, ease: pop.ease, duration: pop.dur}, t)
//   MOTION.stagger(i, step)      per-item delay; MOTION.rand(seed) repeatable noise
//   MOTION.clock(words, D)       the narration word clock (see below)
//   MOTION.camera(...)           the camera rig applied to #cam by engine.html
const MOTION = (() => {
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const mix = (t, x, y) => x + (y - x) * t;

  // Damped spring (same physics as Remotion's spring()): x(0)=0 -> 1. Returns {ease(p), dur}: p in 0..1 over `dur` seconds.
  const spring = (damping, stiffness, mass = 1) => {
    const w0 = Math.sqrt(stiffness / mass), z = damping / (2 * Math.sqrt(stiffness * mass));
    const x = t => {
      if (z < 1) { const wd = w0 * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + (z * w0 / wd) * Math.sin(wd * t)); }
      const s = Math.sqrt(z * z - 1), r1 = -w0 * (z - s), r2 = -w0 * (z + s);
      return z === 1 ? 1 - Math.exp(-w0 * t) * (1 + w0 * t) : 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
    };
    let dur = 0.05; for (let t = 0; t < 4; t += 0.01) if (Math.abs(x(t) - 1) > 0.003) dur = t + 0.01;
    return { dur, ease: p => p >= 1 ? 1 : x(p * dur) };
  };
  const pop = spring(12, 170, 0.8), smooth = spring(28, 170, 1), soft = spring(18, 120, 1);
  const stagger = (i, step = 0.06) => i * step;
  const rand = seed => { const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const squash = (t, amp = 0.35, decay = 6, freq = 18) => Math.sin(t * freq) * Math.exp(-t * decay) * amp; // damped wobble after an impact

  // ---- word clock: words = [{w, s, e}] in scene seconds (from scenes/words.json); empty clock is fine, every query falls back.
  const norm = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\p{L}\p{N}]+/gu, '');
  const clock = (words, D) => {
    const W = (words || []).map(x => ({ w: x.w, n: norm(x.w), s: x.s, e: x.e })).filter(x => x.n);
    return {
      words: W, has: W.length > 0,
      at: i => W[i] ? W[i].s : null, end: i => W[i] ? W[i].e : null,
      // first word starting at/after t (seconds) -> index, or -1
      from: t => W.findIndex(x => x.s >= t - 0.05),
      // find a phrase (string) after time `t0`: {i, j, s, e} of its first/last word, or null
      find(phrase, t0 = 0) {
        const tk = String(phrase).split(/\s+/).map(norm).filter(Boolean); if (!tk.length) return null;
        for (let i = Math.max(0, this.from(t0)); i >= 0 && i < W.length; i++) {
          if (W[i].n !== tk[0]) continue;
          let j = i, ok = true; for (let k = 1; k < tk.length; k++) { if (W[i + k] && W[i + k].n === tk[k]) j = i + k; else { ok = false; break; } }
          if (ok) return { i, j, s: W[i].s, e: W[j].e };
        }
        return null;
      },
      // times (seconds) at which each displayed token is spoken, scanning forward from t0; tokens that are not spoken
      // (digits, symbols, rewritten copy) get the previous time + 0.22 s so the line still builds in order.
      align(tokens, t0) {
        let p = Math.max(0, this.from(t0)), last = t0 - 0.22; const out = [];
        tokens.forEach(tok => {
          const n = norm(tok); let hit = -1;
          if (n && this.has) for (let k = p; k < Math.min(W.length, p + 6); k++) if (W[k].n === n) { hit = k; break; }
          if (hit >= 0) { out.push(W[hit].s); last = W[hit].s; p = hit + 1; } else { last += 0.22; out.push(last); }
        });
        return out;
      },
    };
  };

  // ---- camera rig. keys: [{t, x, y, s, r}] (seconds; x,y = px the camera looks away from centre; s = zoom; r = degrees).
  // Gap <= 0.9 s (about 26 frames) = a whip (fast bezier, with a small tilt); longer = a slow drift. Zoom interpolates in log space so it feels even.
  const whip = u => u < .5 ? 8 * u ** 4 : 1 - 8 * (1 - u) ** 4, drift = u => .5 - Math.cos(Math.PI * u) / 2;
  const camKeys = (keys, t) => {
    if (!keys.length) return { x: 0, y: 0, s: 1, r: 0 };
    if (t <= keys[0].t) return { x: 0, y: 0, s: 1, r: 0, ...keys[0] };
    const last = keys[keys.length - 1]; if (t >= last.t) return { x: 0, y: 0, s: 1, r: 0, ...last };
    let k = 0; while (keys[k + 1].t < t) k++;
    const a = { x: 0, y: 0, s: 1, r: 0, ...keys[k] }, b = { x: 0, y: 0, s: 1, r: 0, ...keys[k + 1] }, gap = b.t - a.t, u = clamp((t - a.t) / gap), fast = gap <= 0.9, e = fast ? whip(u) : drift(u);
    const tilt = fast ? Math.sin(Math.PI * u) * 1.6 * (b.x - a.x >= 0 ? 1 : -1) : 0;
    return { x: mix(e, a.x, b.x), y: mix(e, a.y, b.y), s: Math.exp(mix(e, Math.log(a.s), Math.log(b.s))), r: mix(e, a.r, b.r) + tilt };
  };
  // Auto camera for a scene of D seconds with narration beats: slow drift (never still for long, scenes run 20-40 s)
  // plus a quick push on every beat that decays like a real operator settling back.
  const camAuto = (D, beats) => {
    const keys = [{ t: 0, x: 0, y: 0, s: 1, r: 0 }], step = 6.5;
    for (let t = step, i = 0; t < D - 1; t += step, i++) keys.push({ t, x: (i % 2 ? -1 : 1) * (28 + 14 * rand(i + 1)), y: (i % 3 ? 1 : -1) * (14 + 10 * rand(i + 9)), s: 1 + 0.03 * (i % 2 ? 1 : 0.5), r: (i % 2 ? -1 : 1) * 0.35 });
    keys.push({ t: Math.max(D, keys[keys.length - 1].t + 1), x: 0, y: 0, s: 1, r: 0 });
    const bs = (beats || []).filter(b => b > 0.4 && b < D - 0.6);
    return t => {
      const c = camKeys(keys, t); let ls = Math.log(c.s), x = c.x, y = c.y, r = c.r;
      bs.forEach((b, i) => {
        const u = t - b + 0.05; if (u < 0) return;
        const env = u < 0.3 ? whip(u / 0.3) : Math.exp(-(u - 0.3) / 1.6), sg = i % 2 ? -1 : 1;
        ls += 0.04 * env; x += sg * 26 * env; y += -10 * env; r += -sg * 0.7 * env;
      });
      return { x, y, s: Math.exp(ls), r };
    };
  };
  // camera function for a spec: undefined -> auto, false -> still, array of keys -> explicit
  const camera = (spec, D, beats) => spec === false ? () => ({ x: 0, y: 0, s: 1, r: 0 }) : Array.isArray(spec) ? (t => camKeys(spec, t)) : camAuto(D, beats);
  // apparent speed in px/frame (centre-to-corner) between t-1/fps and t+1/fps: how much motion blur a frame needs
  const speed = (cam, t, fps = 30) => { const a = cam(Math.max(0, t - 0.5 / fps)), b = cam(t + 0.5 / fps); return Math.hypot(b.x - a.x, b.y - a.y) + Math.abs(Math.log(b.s / a.s)) * 1100 + Math.abs(b.r - a.r) * 19; };

  return { clamp, mix, spring, pop, smooth, soft, stagger, rand, squash, clock, camera, speed, norm };
})();
if (typeof module !== 'undefined') module.exports = MOTION;
