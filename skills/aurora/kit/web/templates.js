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

AURORA_TEMPLATES.screenshot_zoom.camera = false; // it runs its own camera on the browser card

// ---- kinetic_words: key sentences whose words land ON the spoken word (use for claims, definitions, the punchline: a few per scene, not the whole narration).
// P {groups:[{text, emphasis?:[word|index], kind?:'rise'|'pop'|'squash'|'blade', at?:seconds, color?}], size?, hold?}
// A group starts at g.at, else beats[i], else where its words are found in the narration clock; each word then enters 2 frames before it is spoken.
// Without a clock it falls back to evenly spread beats, so the scene still plays.
AURORA_TEMPLATES.kinetic_words = ({ tl, el, D, P, beats, ACC, TH, clock, M }) => {
  const gs = (P.groups || []).map(g => typeof g === 'string' ? { text: g } : g), n = gs.length, LEAD = 2 / 30;
  let prev = 0; const plan = gs.map((g, gi) => {
    const tokens = g.text.split(/\s+/).filter(Boolean);
    let t0 = g.at ?? beats[gi] ?? (clock.has ? (clock.find(tokens.slice(0, 3).join(' '), prev)?.s ?? prev + 0.3) : 0.4 + gi * (D - 1.2) / Math.max(n, 1));
    const times = clock.has ? clock.align(tokens, t0) : tokens.map((_, k) => t0 + k * 0.28);
    prev = times[times.length - 1] + 0.1; return { g, tokens, times, t0 };
  });
  plan.forEach(({ g, tokens, times }, gi) => {
    const chars = g.text.length, size = P.size || Math.round(Math.min(160, 1250 / Math.sqrt(chars))), emph = new Set((g.emphasis || []).map(e => typeof e === 'number' ? e : tokens.findIndex(t => M.norm(t) === M.norm(e))));
    const box = el(`<div class="abs" style="left:210px;right:210px;top:0;bottom:0;display:flex;flex-wrap:wrap;align-content:center;justify-content:center;gap:.04em .26em;font-size:${size}px;line-height:1.12;text-align:center"></div>`);
    const kind = g.kind || ['rise', 'pop', 'squash', 'blade'][gi % 4], ink = g.color || TH.ink;
    tokens.forEach((tok, k) => {
      const E = emph.has(k), small = !E && M.norm(tok).length <= 3, t = Math.max(0, times[k] - LEAD), rot = (M.rand(gi * 31 + k) - .5) * 10;
      const w = el(`<span style="display:inline-block;position:relative;overflow:${kind === 'rise' && !E ? 'hidden' : 'visible'};padding:.06em ${E ? ".1em" : ".02em"};font-weight:${E ? 900 : small ? 600 : 800};font-style:${small ? 'italic' : 'normal'};font-size:${E ? 1.22 : small ? .8 : 1}em;color:${E ? (g.color || ACC[2]) : ink};opacity:${small ? .82 : 1};text-shadow:0 .07em 0 rgba(0,0,0,.25);letter-spacing:-.02em"><span class="in" style="display:inline-block">${E && tok.length <= 11 ? [...tok].map(c => `<span class="ch" style="display:inline-block">${c}</span>`).join('') : tok}</span></span>`, box), inn = w.firstElementChild;
      const kk = E ? (tok.length <= 11 ? 'letters' : 'pop') : kind;
      if (kk === 'letters') { const L = inn.querySelectorAll('.ch'); tl.fromTo(L, { y: -90, scale: .3, rotation: i => (i % 2 ? 14 : -14), opacity: 0 }, { y: 0, scale: 1, rotation: 0, opacity: 1, duration: M.pop.dur, ease: M.pop.ease, stagger: .035 }, t); }
      else if (kk === 'rise') tl.fromTo(inn, { yPercent: 115, opacity: 0 }, { yPercent: 0, opacity: 1, duration: M.smooth.dur, ease: M.smooth.ease }, t);
      else if (kk === 'squash') tl.fromTo(inn, { scaleX: 1.6, scaleY: .25, y: 40, opacity: 0 }, { scaleX: 1, scaleY: 1, y: 0, opacity: 1, duration: M.pop.dur, ease: M.pop.ease, transformOrigin: '50% 100%' }, t);
      else if (kk === 'blade') tl.fromTo(inn, { x: -260, skewX: -28, opacity: 0 }, { x: 0, skewX: 0, opacity: 1, duration: M.smooth.dur, ease: M.smooth.ease }, t);
      else tl.fromTo(inn, { scale: .2, rotation: rot * 2, opacity: 0 }, { scale: 1, rotation: 0, opacity: 1, duration: M.pop.dur, ease: M.pop.ease }, t);
      if (E) { const u = el(`<i style="position:absolute;left:0;right:0;bottom:-.02em;height:.1em;border-radius:99px;background:${ACC[1]};transform-origin:0 50%"></i>`, w); tl.fromTo(u, { scaleX: 0 }, { scaleX: 1, duration: .35, ease: 'power3.out' }, t + .22); }
    });
    const last = times[times.length - 1], nextT = plan[gi + 1] ? plan[gi + 1].times[0] - LEAD - 0.35 : D - 0.4;
    tl.to(box, { y: -70, opacity: 0, duration: .3, ease: 'power2.in' }, Math.max(last + 0.15, Math.min(nextT, last + (P.hold ?? 1.8)))); // leaves before the next group starts, even when the gap is short
  });
};

// ---- draw_on: whiteboard. Strokes trace themselves in with a pen following the tip (explainers, diagrams, "how it works" in a full video).
// P {board?:false (draw straight on the theme background), items:[{kind:'rect'|'circle'|'line'|'arrow'|'path'|'text', x,y, w,h | r | x2,y2 | d | text,size, color?, at?, dur?, say?:'phrase'}]}  (1920x1080 coords)
// An item starts at item.at, else when its `say` phrase is spoken, else beats[i], else spread over the scene. Pen = a dot at the stroke tip.
AURORA_TEMPLATES.draw_on = ({ tl, el, D, P, beats, ACC, TH, clock, M }) => {
  const items = P.items || [], board = P.board !== false, ink = board ? '#23204a' : TH.ink, NS = 'http://www.w3.org/2000/svg';
  if (board) { const b = el(`<div class="abs" style="left:110px;top:90px;right:110px;bottom:90px;border-radius:26px;background:#f7f4ea;box-shadow:0 40px 100px rgba(10,5,40,.55)"></div>`); tl.fromTo(b, { y: 80, opacity: 0 }, { y: 0, opacity: 1, duration: .7, ease: 'power3.out' }, 0); }
  const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', '0 0 1920 1080'); svg.setAttribute('style', 'position:absolute;inset:0;width:1920px;height:1080px;overflow:visible'); document.getElementById('world').appendChild(svg);
  const mk = (tag, a) => { const n = document.createElementNS(NS, tag); Object.entries(a).forEach(([k, v]) => n.setAttribute(k, v)); svg.appendChild(n); return n; };
  let prev = board ? 0.9 : 0.4; const segs = [];
  items.forEach((it, i) => {
    const col = it.color || ACC[i % ACC.length], sw = it.w2 || 9, at = it.at ?? (it.say && clock.find(it.say, 0)?.s) ?? beats[i] ?? prev, k = it.kind || 'path';
    let node, len, dur = it.dur ?? (k === 'text' ? Math.max(.7, (it.text || '').length * .07) : 0.9), pt;
    if (k === 'text') {
      const size = it.size || 64, tx = mk('text', { x: it.x, y: it.y, 'font-size': size, 'font-weight': 800, fill: it.color || ink, 'font-family': "Noto Sans,DejaVu Sans,sans-serif" }); tx.textContent = it.text;
      const wd = tx.getComputedTextLength() || it.text.length * size * .56, id = 'clip' + i, cp = mk('clipPath', { id }), r = document.createElementNS(NS, 'rect'); r.setAttribute('x', it.x - 6); r.setAttribute('y', it.y - size); r.setAttribute('height', size * 1.4); r.setAttribute('width', 0); cp.appendChild(r); tx.setAttribute('clip-path', `url(#${id})`);
      tl.fromTo(r, { attr: { width: 0 } }, { attr: { width: wd + 14 }, duration: dur, ease: 'none' }, at); pt = u => ({ x: it.x + wd * u, y: it.y - size * .25 });
    } else {
      const d = k === 'rect' ? `M${it.x} ${it.y}H${it.x + it.w}V${it.y + it.h}H${it.x}Z` : k === 'circle' ? `M${it.x - it.r} ${it.y}a${it.r} ${it.r} 0 1 1 ${it.r * 2} 0a${it.r} ${it.r} 0 1 1 ${-it.r * 2} 0` : k === 'line' || k === 'arrow' ? `M${it.x} ${it.y}L${it.x2} ${it.y2}` : it.d;
      node = mk('path', { d, fill: 'none', stroke: col, 'stroke-width': sw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }); len = node.getTotalLength(); node.style.strokeDasharray = len; node.style.strokeDashoffset = len;
      tl.fromTo(node, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: dur, ease: 'power1.inOut' }, at); pt = u => node.getPointAtLength(len * u);
      if (k === 'arrow') { const a = Math.atan2(it.y2 - it.y, it.x2 - it.x), h = 34, hd = mk('path', { d: `M${it.x2 - h * Math.cos(a - .5)} ${it.y2 - h * Math.sin(a - .5)}L${it.x2} ${it.y2}L${it.x2 - h * Math.cos(a + .5)} ${it.y2 - h * Math.sin(a + .5)}`, fill: 'none', stroke: col, 'stroke-width': sw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0 }); tl.to(hd, { opacity: 1, duration: .05 }, at + dur); }
      if (it.fill) { const f = mk('path', { d, fill: col, 'fill-opacity': 0, stroke: 'none' }); svg.insertBefore(f, node); tl.to(f, { attr: { 'fill-opacity': it.fill }, duration: .4 }, at + dur); }
    }
    segs.push({ at, dur, pt, ease: k === 'text' ? (u => u) : (u => u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2) }); prev = at + dur + .35;
  });
  const pen = mk('circle', { r: 11, fill: '#ff5ea8', stroke: '#fff', 'stroke-width': 4, opacity: 0 });
  return t => {
    const s = segs.find(g => t >= g.at && t <= g.at + g.dur + .25); if (!s) { pen.setAttribute('opacity', 0); return; }
    const p = s.pt(clamp(s.ease(clamp((t - s.at) / s.dur, 0, 1)), 0, 1)); pen.setAttribute('cx', p.x); pen.setAttribute('cy', p.y); pen.setAttribute('opacity', t <= s.at + s.dur ? 1 : 1 - (t - s.at - s.dur) / .25);
  };
};

// ---- fake_ui: a terminal / app window that plays a scripted session: typed commands, output, button clicks. Pure function of time.
// P {title?, steps:[{cmd:'text typed'} | {out:'line', color?} | {click:'Button label'} | {wait:seconds}], size?, at?}   step i starts at step.at, else beats[i], else right after the previous one.
AURORA_TEMPLATES.fake_ui = ({ tl, el, D, P, beats, ACC, TH }) => {
  const steps = P.steps || [], fs = P.size || 34, lh = Math.round(fs * 1.5), CPS = 26, H = 720;
  const win = el(`<div class="abs" style="left:230px;right:230px;top:180px;height:${H}px;border-radius:22px;overflow:hidden;background:#12101f;box-shadow:0 50px 120px rgba(10,5,40,.6)"><div style="height:46px;background:#25223a;display:flex;align-items:center;gap:10px;padding-left:18px"><i style="width:14px;height:14px;border-radius:50%;background:#ff5f57"></i><i style="width:14px;height:14px;border-radius:50%;background:#febc2e"></i><i style="width:14px;height:14px;border-radius:50%;background:#28c840"></i><span style="color:#9a96c0;font:600 20px sans-serif;margin-left:18px">${P.title || 'terminal'}</span></div><div class="body" style="position:absolute;left:34px;right:34px;top:68px;font:600 ${fs}px/${lh}px 'DejaVu Sans Mono',monospace;color:#e8e6ff;white-space:pre-wrap"></div></div>`);
  const body = win.querySelector('.body'); tl.fromTo(win, { y: 120, opacity: 0, rotationX: 12 }, { y: 0, opacity: 1, rotationX: 0, duration: .7, ease: 'power3.out' }, 0);
  const cap = Math.floor((H - 110) / lh); let t = P.at ?? 0.9, row = 0; const typed = [], cur = el(`<svg class="abs" style="left:0;top:0;width:34px;height:34px;opacity:0" viewBox="0 0 24 24"><path d="M3 2l7 19 3-8 8-3z" fill="#fff" stroke="#000" stroke-width="1.5"/></svg>`), rg = el(`<div class="abs" style="width:24px;height:24px;border:5px solid #ffd166;border-radius:50%;opacity:0"></div>`);
  const scroll = (r, at) => { if (r >= cap) tl.to(body, { y: -(r - cap + 1) * lh, duration: .25, ease: 'power2.out' }, at); };
  steps.forEach((s, i) => {
    const at = s.at ?? beats[i] ?? t;
    if (s.wait) { t = at + s.wait; return; }
    const line = document.createElement('div'); line.style.cssText = 'min-height:' + lh + 'px'; body.appendChild(line); tl.set(line, { opacity: 0 }, 0).set(line, { opacity: 1 }, at);
    if (s.cmd !== undefined) { const dur = s.cmd.length / CPS; typed.push({ line, text: s.cmd, at, dur }); scroll(row, at); t = at + dur + .35; }
    else if (s.out !== undefined) { line.textContent = s.out; if (s.color) line.style.color = s.color; scroll(row, at); t = at + .3; }
    else if (s.click !== undefined) {
      const bw = s.click.length * fs * .62 + 70, b = document.createElement('span'); b.textContent = s.click; b.style.cssText = `display:inline-block;padding:6px 28px;border-radius:12px;background:${ACC[0]};color:#12101f;font-weight:800`; line.appendChild(b); scroll(row, at);
      const bx = 230 + 34 + bw / 2, by = 180 + 68 + row * lh + lh / 2 + (row >= cap ? -(row - cap + 1) * lh : 0);
      tl.set(cur, { x: 1300, y: 200, opacity: 1 }, at).to(cur, { x: bx, y: by, duration: .8, ease: 'power2.inOut' }, at).to(b, { scale: .92, duration: .08, yoyo: true, repeat: 1 }, at + .85)
        .fromTo(rg, { x: bx - 12, y: by - 12, scale: .3, opacity: 1 }, { scale: 3, opacity: 0, duration: .5 }, at + .85).to(cur, { opacity: 0, duration: .3 }, at + 1.4); t = at + 1.2;
    }
    row++;
  });
  return t0 => typed.forEach(o => { const n = Math.floor(clamp((t0 - o.at) / o.dur, 0, 1) * o.text.length), blink = Math.floor(t0 * 2) % 2 === 0; o.line.textContent = t0 < o.at ? '' : '$ ' + o.text.slice(0, n) + (n < o.text.length || blink ? '▌' : ''); });
};
