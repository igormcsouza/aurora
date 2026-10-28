// aurora web templates. Each: ({tl, el, W, D, P, beats, U, ACC, TH, gsap}) => optional render(t) for values that are a pure function of time.
// `beats` = seconds (scene time) for the key moments, taken from scenes/cues.json; every template has sane fallbacks spread over D.
const AURORA_TEMPLATES = {};
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const fmtMB = mb => mb >= 1000 ? (mb / 1000).toFixed(1).replace(/\.0$/, '') + ' GB' : Math.round(mb) + ' MB';

// ---- kinetic_title: P {lines:[{text,color?}], size?}  beats[i] = entry time of line i
AURORA_TEMPLATES.kinetic_title = ({ tl, el, D, P, beats, TH }) => {
  const lines = (P.lines || []).map(l => typeof l === 'string' ? { text: l } : l);
  const longest = Math.max(...lines.map(l => l.text.length)), size = Math.min(P.size || 150, Math.floor(1700 / (longest * 0.6)));
  const t = el(`<div class="abs" style="left:0;right:0;top:${540 - lines.length * size * 0.58}px;text-align:center"></div>`);
  lines.forEach((l, i) => {
    const s = el(`<div><span class="word" style="font-size:${size}px;color:${l.color || TH.ink}">${l.text}</span></div>`, t).firstElementChild, at = beats[i] ?? 0.25 + i * 0.4;
    tl.fromTo(s, { y: 260, scale: .2, rotation: i % 2 ? 12 : -12, opacity: 0 }, { y: 0, scale: 1, rotation: 0, opacity: 1, duration: .55, ease: 'back.out(2.2)' }, at);
    tl.to(s, { y: -1200, rotation: i % 2 ? -8 : 8, duration: .5, ease: 'power3.in' }, D - 0.7 + i * .08 - lines.length * .08);
  });
  if (P.shake !== false && lines.length) tl.fromTo(t.lastChild.firstElementChild, { x: -8 }, { x: 8, duration: .06, repeat: 9, yoyo: true, ease: 'none' }, (beats[lines.length - 1] ?? .25 + (lines.length - 1) * .4) + .7);
  tl.fromTo('#world', { rotateY: -4, rotateX: 2 }, { rotateY: 5, rotateX: -2, duration: D, ease: 'sine.inOut' }, 0);
};

// ---- layer_stack: a pile of layers grows (size counter), the one worth keeping flies to a small card, the rest falls.
// P {title?:[lines], code_title?, code_lines[], layers:[{label,color?}], keep (index), stage1?, stage2?, keep_label?, start_mb, end_mb, counter_label?, payoff?, note?}
// beats = [build start, keep flies, payoff]
AURORA_TEMPLATES.layer_stack = ({ tl, el, D, P, beats, ACC, TH }) => {
  const L = P.layers, n = L.length, k = D / 20, tB = beats[0] ?? 4.6 * k, tF = beats[1] ?? 10.4 * k, tP = beats[2] ?? Math.min(D - 3.4, tF + 6 * k);
  const keep = P.keep ?? n - 1, g = Math.max(.35, Math.min(.9, (tF - 1 - tB) / n)), tEnd = tB + n * g;
  if (P.title && tB > 2.2) AURORA_TEMPLATES.kinetic_title({ tl, el, D: tB + .3, P: { lines: P.title }, beats: [], TH });
  const lines = P.code_lines || [];
  const code = el(`<div class="abs glass code" style="left:120px;top:330px;height:${60 + lines.length * 41}px">${lines.map((l, i) => `<span class="l ${i === 0 && /^#/.test(l) ? 'c' : ''}">${l.replace(/\b(FROM|RUN|COPY|AS|CMD)\b/g, '<b class="k">$1</b>')}</span>`).join('')}</div>`);
  tl.fromTo(code, { x: -700, opacity: 0 }, { x: 0, opacity: 1, duration: .7, ease: 'power3.out' }, tB - .6);
  [...code.querySelectorAll('.l')].forEach((l, i) => tl.to(l, { width: 520, duration: .45, ease: 'none' }, tB - .1 + i * Math.max(.3, (tEnd - tB) / Math.max(lines.length, 1))));
  const slabs = L.map((l, i) => {
    const c = l.color || ACC[i % ACC.length], s = el(`<div class="abs glass slab" style="--c:${c};left:760px;top:${930 - (i + 1) * 88}px">${l.label}</div>`);
    tl.fromTo(s, { y: -900, rotation: i % 2 ? 6 : -6, opacity: 0 }, { y: 0, rotation: 0, opacity: 1, duration: .55, ease: 'bounce.out' }, tB + i * g); return s;
  });
  const num = el(`<div class="abs num" style="left:110px;top:90px;color:${TH.ink}"></div>`), lbl = el(`<div class="abs" style="left:120px;top:290px;font-size:30px;font-weight:700;opacity:0">${P.counter_label || ''}</div>`);
  tl.to(lbl, { opacity: .8, duration: .3 }, tB);
  const slim = el(`<div class="abs glass" style="left:1370px;top:760px;width:430px;height:150px;border-left:16px solid ${ACC[3]};display:flex;align-items:center;padding-left:30px;font:800 32px DejaVu Sans Mono,monospace">${P.keep_label || ''}</div>`);
  const chip = el(`<div class="abs chip" style="left:1370px;top:690px;opacity:0;${P.stage2 ? '' : 'display:none'}">${P.stage2 || ''}</div>`);
  tl.fromTo(slim, { scale: .01, opacity: 0 }, { scale: 1, opacity: 1, duration: .6, ease: 'back.out(2)' }, tF - .4).to(chip, { opacity: 1, duration: .3 }, tF - .2);
  const art = slabs[keep]; art.style.zIndex = 5; const dy = 835 - (930 - (keep + 1) * 88 + 39);
  tl.to(art, { keyframes: [{ x: 250, y: -220, rotation: -8, scale: 1.1, duration: .8, ease: 'power2.out' }, { x: 545, y: dy, rotation: 0, scale: .7, duration: .8, ease: 'power2.in' }] }, tF);
  tl.to(code, { opacity: 0, x: -300, duration: .5 }, tF + 1.6);
  slabs.forEach((s, i) => { if (i !== keep) tl.to(s, { y: 900 + i * 40, rotation: (i % 2 ? 1 : -1) * (30 + i * 5), opacity: 0, duration: .9, ease: 'power2.in' }, tF + 1.8 + i * .12); });
  tl.to(num, { color: ACC[3], duration: .3 }, tF + 3.4);
  const big = el(`<div class="abs" style="left:0;right:0;top:380px;text-align:center;opacity:0;font-weight:900;font-size:170px;text-shadow:0 12px 0 rgba(0,0,0,.25)">${P.payoff || ''}</div>`);
  tl.fromTo(big, { scale: .3, opacity: 0 }, { scale: 1, opacity: 1, duration: .6, ease: 'elastic.out(1,.5)' }, tP);
  for (let i = 0; i < 70; i++) {
    const d = el(`<div class="dot" style="left:960px;top:540px;background:${ACC[i % ACC.length]};opacity:0"></div>`), a = (i * 2.399) % 6.283, r = 300 + (i * 97) % 700;
    tl.set(d, { opacity: 1 }, tP - .1).to(d, { x: Math.cos(a) * r, y: Math.sin(a) * r * .7 + 250, rotation: (i * 53) % 720, duration: 1.8, ease: 'power3.out' }, tP - .1).to(d, { opacity: 0, duration: .6 }, tP + 1.3);
  }
  if (P.note) el(`<div class="abs" style="left:0;right:0;bottom:60px;text-align:center;font-size:28px;font-weight:700;opacity:.75">${P.note}</div>`);
  tl.fromTo('#world', { rotateY: -6, rotateX: 3, scale: 1 }, { rotateY: 7, rotateX: -2, scale: 1.05, duration: D, ease: 'sine.inOut' }, 0);
  const a = P.start_mb ?? 1100, b = P.end_mb ?? 90;
  return t => { const v = t < tB ? 0 : t < tEnd ? a * (t - tB) / (tEnd - tB) : t < tF + 1.6 ? a : t < tF + 3.6 ? a - (a - b) * (t - tF - 1.6) / 2 : b; num.textContent = t < tB ? '' : fmtMB(v); };
};

// ---- screenshot_zoom: a real screenshot (P.image) or screen recording (P.video {dir, pattern:'%05d.jpg', count, fps}) in a browser window; camera zooms into regions with highlight, cursor and callout.
// P {image|video, w?, h?, url?, shots:[{region:[x,y,w,h], callout?}], credit?}   beats[i] = when zoom i starts
AURORA_TEMPLATES.screenshot_zoom = ({ tl, el, D, P, beats, U, TH }) => {
  const w = P.w || 1600, h = P.h || 1000, R = document.documentElement.style; R.setProperty('--cw', w + 'px'); R.setProperty('--ch', h + 'px');
  const V = P.video, src = V ? U(V.dir + '/' + (V.pattern || '%05d.jpg').replace('%05d', String(1).padStart(5, '0'))) : U(P.image);
  const win = el(`<div id="win" class="abs" style="inset:0"><div id="card"><div id="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><span style="color:#555;font:600 18px sans-serif;margin-left:20px">${P.url || ''}</span></div><div id="doc"><img class="shot" id="shot" src="${src}"><svg class="cursor" id="cur" viewBox="0 0 24 24"><path d="M3 2l7 19 3-8 8-3z" fill="#fff" stroke="#000" stroke-width="1.5"/></svg><div class="ring" id="rg"></div></div></div></div>`);
  const card = document.getElementById('card'), s0 = Math.min(1180 / w, 800 / (h + 36)), cam = { s: s0, cx: w / 2, cy: h / 2 };
  const apply = () => { card.style.transform = `translate(${960 - cam.s * cam.cx}px,${540 - cam.s * (cam.cy + 36)}px) scale(${cam.s})`; };
  tl.fromTo(win, { opacity: 0, rotationY: -25, y: 200 }, { opacity: 1, rotationY: 0, y: 0, duration: .9, ease: 'power3.out' }, 0);
  const shots = P.shots || [], n = shots.length, tEnd = D - 1.9, span = Math.max(1, (tEnd - 1.4)) / Math.max(n, 1);
  tl.set('#cur', { x: w - 200, y: 120 }, 0);
  shots.forEach((sh, i) => {
    const [rx, ry, rw, rh] = sh.region, ts = beats[i] ?? 1.4 + i * span, tNext = (beats[i + 1] ?? 1.4 + (i + 1) * span) - .3, s = clamp(Math.min(1500 / rw, 620 / rh), s0 * 1.3, 3.2);
    const hl = el(`<div class="hl" style="left:${rx - 8}px;top:${ry - 6}px;width:${rw + 16}px;height:${rh + 12}px"></div>`, document.getElementById('doc'));
    const co = sh.callout ? el(`<div class="callout" style="left:960px;top:${Math.min(1000, 540 + s * rh / 2 + 28)}px;transform:translateX(-50%)">${sh.callout}</div>`) : null;
    tl.to(cam, { s, cx: rx + rw / 2, cy: ry + rh / 2, duration: 1.4, ease: 'power3.inOut', onUpdate: apply }, ts);
    tl.to('#cur', { x: rx + rw * .25, y: ry + rh * .5, duration: 1.1, ease: 'power2.inOut' }, ts - .1);
    tl.fromTo('#rg', { x: rx + rw * .25 - 3, y: ry + rh * .5 + 8, scale: .2, opacity: 1 }, { scale: 3, opacity: 0, duration: .6 }, ts + 1.25);
    tl.to(hl, { opacity: 1, duration: .4 }, ts + 1.3); if (co) tl.to(co, { opacity: 1, y: -20, duration: .4, ease: 'back.out(2)' }, ts + 1.6);
    tl.to(hl, { opacity: 0, duration: .3 }, Math.max(ts + 2.2, tNext)); if (co) tl.to(co, { opacity: 0, duration: .3 }, Math.max(ts + 2.2, tNext));
  });
  tl.to(cam, { s: s0, cx: w / 2, cy: h / 2, duration: 1.4, ease: 'power3.inOut', onUpdate: apply }, tEnd);
  if (P.credit) { const cr = el(`<div class="abs" style="left:0;right:0;bottom:34px;text-align:center;font-size:26px;font-weight:700;opacity:0">${P.credit}</div>`); tl.to(cr, { opacity: .9, duration: .5 }, D - 1.2); }
  const img = document.getElementById('shot'); let cur = 1;
  return t => { apply(); if (V) { const i = clamp(Math.floor(t * (V.fps || 10)) + 1, 1, V.count); if (i !== cur) { cur = i; img.src = U(V.dir + '/' + (V.pattern || '%05d.jpg').replace('%05d', String(i).padStart(5, '0'))); } } };
};

// ---- stat_reveal: one big number counts up. P {value, unit?, label, sub?, color?}  beats[0] = start
AURORA_TEMPLATES.stat_reveal = ({ tl, el, D, P, beats, ACC, TH }) => {
  const t0 = beats[0] ?? .5, num = el(`<div class="abs num" style="left:0;right:0;top:300px;text-align:center;font-size:300px;color:${P.color || ACC[2]}"></div>`);
  const lab = el(`<div class="abs" style="left:0;right:0;top:640px;text-align:center;font-weight:900;font-size:80px;opacity:0">${P.label || ''}</div>`), sub = el(`<div class="abs" style="left:0;right:0;top:760px;text-align:center;font-weight:700;font-size:38px;opacity:0">${P.sub || ''}</div>`);
  tl.fromTo(lab, { y: 80, opacity: 0 }, { y: 0, opacity: 1, duration: .5, ease: 'back.out(2)' }, t0 + 1.4).to(sub, { opacity: .8, duration: .5 }, t0 + 2);
  tl.fromTo('#world', { scale: .94 }, { scale: 1.04, duration: D, ease: 'sine.inOut' }, 0);
  return t => { const u = clamp((t - t0) / 1.6, 0, 1), v = (P.value || 0) * (1 - Math.pow(1 - u, 3)); num.textContent = t < t0 ? '' : (Number.isInteger(P.value) ? Math.round(v) : v.toFixed(1)) + (P.unit || ''); };
};
