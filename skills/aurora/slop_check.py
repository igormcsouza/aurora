#!/usr/bin/env python3
"""Pre-publish 'inauthentic / AI slop' checks for draft_videos/<slug>/ or published_videos/<slug>/ (stdlib only). Run from the project.
  slop_check.py <slug>      prints PASS/WARN/FAIL lines; exit 1 if any FAIL
Checks what YouTube's policy names: templated/repetitive structure vs your other videos, claims without
sources, thin commentary, misleading metadata, missing AI disclosure note. It cannot judge originality: a human does.
"""
import json, re, sys
from pathlib import Path

def project():
    cwd = Path.cwd()
    return next((d for d in [cwd, *cwd.parents] if (d / "draft_videos").is_dir() or (d / "videos").is_dir()), cwd)

def root():
    P = project(); return P / "draft_videos" if (P / "draft_videos").is_dir() else P / "videos"

def grams(t, n=5):
    w = re.findall(r"\w+", t.lower()); return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}

def prefs_json(P):
    f = P / "preferences.json"
    try: return json.loads(f.read_text()) if f.exists() else {}
    except ValueError: return {}

def balance(plan, others, P, add):
    """Engine/template balance: Aurora should mix engines, show real evidence, and not look like the last videos."""
    sc = plan["scenes"]; eng = [s.get("engine") for s in sc]
    if not all(eng): add("WARN", "scenes without an 'engine' (web|blender|manim): the visual mix cannot be checked"); return
    secs = lambda s: s.get("secs") or 1
    tot = sum(secs(s) for s in sc); share = {e: sum(secs(s) for s in sc if s["engine"] == e) / tot for e in set(eng)}
    top = max(share, key=share.get)
    if len(share) < 2: add("WARN", f"only one engine ({top}) in the whole video: mix web, blender and manim")
    elif share[top] > 0.7: add("WARN", f"engine '{top}' carries {share[top]:.0%} of the runtime: rebalance (target: no engine above 70%)")
    else: add("PASS", "engine mix " + ", ".join(f"{e} {v:.0%}" for e, v in sorted(share.items())))
    run = best = 1
    for a, b in zip(sc, sc[1:]):
        run = run + 1 if (a["engine"], a["template"]) == (b["engine"], b["template"]) else 1; best = max(best, run)
    if best > 2: add("WARN", f"{best} consecutive scenes with the same engine+template: vary adjacent scenes")
    if sum(1 for s in sc if s["template"] == "screenshot_zoom") < 2: add("WARN", "fewer than 2 evidence scenes (screenshot_zoom with a real screenshot or recording): show the real docs/repo/UI when there is one")
    prefs = P / "preferences.json"; noblender = prefs.exists() and json.loads(prefs.read_text() or "{}").get("blender") is False
    if not noblender and "blender" not in eng: add("WARN", "no blender hero moment (set \"blender\": false in preferences.json to silence)")
    if sc[0]["template"] != "kinetic_title" and sc[0]["engine"] != "blender": add("WARN", "the video does not open with a kinetic or 3D hook scene")
    prev = sorted(others, key=lambda o: (o / "plan.json").stat().st_mtime)[-2:]
    doms = []
    for o in prev:
        ps = json.loads((o / "plan.json").read_text()).get("scenes", [])
        if ps and all(x.get("engine") for x in ps):
            t = sum(secs(x) for x in ps); sh = {e: sum(secs(x) for x in ps if x["engine"] == e) / t for e in {x["engine"] for x in ps}}; doms.append(max(sh, key=sh.get))
    if len(doms) == 2 and doms[0] == doms[1] == top and share[top] > 0.5: add("WARN", f"'{top}' dominated the last 3 videos: change the mix on purpose")

def main(slug):
    R, V = root(), root() / slug
    plan, out = json.loads((V / "plan.json").read_text()), []
    add = lambda lvl, msg: out.append((lvl, msg))
    seq = [s["template"] for s in plan["scenes"]]
    narr = (V / "narration.md").read_text() if (V / "narration.md").exists() else " ".join(s["narration"] for s in plan["scenes"])
    # 1 template / repetition vs earlier videos
    P = project(); pubs = P / "published_videos"
    others = [p.parent for p in [*R.glob("*/plan.json"), *(pubs.glob("*/plan.json") if pubs.is_dir() else [])] if p.parent.name != slug]
    for o in others:
        oseq = [s.get("template") for s in json.loads((o / "plan.json").read_text())["scenes"]]
        same = sum(a == b for a, b in zip(seq, oseq)) / max(len(seq), len(oseq))
        og = grams((o / "narration.md").read_text()) if (o / "narration.md").exists() else set()
        ov = len(grams(narr) & og) / max(1, len(grams(narr)))
        if same > 0.6 or ov > 0.1: add("FAIL", f"too similar to {o.name}: scene-template order {same:.0%}, narration 5-gram overlap {ov:.0%}")
        elif same > 0.4: add("WARN", f"scene-template order {same:.0%} same as {o.name}: vary structure")
    if not others: add("PASS", "no earlier videos to compare for templated structure")
    if len(set(seq)) < 3: add("WARN", f"only {len(set(seq))} scene templates used: add variety")
    if not any(s["template"] == "hero" or s.get("engine") == "blender" for s in plan["scenes"]): add("WARN", "no custom hero scene (blender or hand-written): every scene is a stock template")
    balance(plan, others, P, add)
    # 2 claims / sources
    claims = plan.get("claims", [])
    if not claims: add("FAIL", "plan.json has no claims[]: nothing is fact-checked")
    bad = [c for c in claims if c.get("status") in ("verified", "attributed") and not c.get("source_urls")]
    if bad: add("FAIL", f"{len(bad)} claims without a source URL")
    elif claims: add("PASS", f"{len(claims)} claims, all with sources")
    if not (V / "sources.md").exists(): add("FAIL", "sources.md missing")
    # 3 commentary depth: opinion/analysis markers, not just reporting
    if not plan.get("aha"): add("FAIL", "plan.json has no 'aha' (the original insight of the video)")
    if not re.search(r"\b(minha opini|eu acho|na minha|o que importa|o que muda|faça|fa[cç]a|troque|use|evite|in my opinion|i think|what matters|what changes|try this|avoid|my take|en mi opini|lo que importa)\w*", narr, re.I): add("WARN", "no opinion or actionable takeaway wording found: is this just reading the news?")
    # 4 package metadata (YouTube limits: description 5000 chars/bytes, no < or > in title/description/tags)
    pk = V / "package" / "package.md"
    if pk.exists():
        t = pk.read_text()
        sec = lambda name: (re.search(rf"## {name}\s*\n(.+?)(?=\n## |\Z)", t, re.S) or [None, ""])[1]
        d = sec("Description").strip()
        tags = [x.strip() for x in re.split(r"[,\n]", sec("Tags")) if x.strip()]
        titles = [re.sub(r"^\s*(\d+[.)]|[-*])\s*", "", l).strip() for l in sec("Titles").splitlines() if l.strip()]
        if not d: add("FAIL", "package.md has no ## Description section")
        nb = len(d.encode())
        if len(d) > 5000 or nb > 5000: add("FAIL", f"description is {len(d)} chars / {nb} bytes: YouTube limit is 5000")
        elif nb > 4500: add("WARN", f"description is {nb} bytes: close to the 5000 limit")
        else: add("PASS", f"description {len(d)} chars / {nb} bytes")
        for name, txt in (("description", d), ("titles", "\n".join(titles)), ("tags", ",".join(tags))):
            if re.search(r"[<>]", txt): add("FAIL", f"{name} contains < or > (YouTube rejects them; also no arrows like ->)")
        if len(titles) != 3: add("WARN", f"{len(titles)} title options under '## Titles' (expected 3)")
        if any(len(x) > 100 for x in titles): add("FAIL", "a title is over 100 characters")
        if n := len(tags): 
            if n > 15: add("WARN", f"{n} tags: keep about 15 relevant ones, no keyword stuffing")
            if len(",".join(tags)) > 500 or any(len(x) > 30 for x in tags): add("FAIL", "tags over 500 characters total or a tag over 30")
        ch = re.findall(r"(?m)^\s*(\d+):(\d\d)(?::(\d\d))?\s+\S", d)
        secs = [int(a) * 3600 + int(b) * 60 + int(c) if c else int(a) * 60 + int(b) for a, b, c in ch]
        if len(secs) < 3 or secs[0] != 0 or secs != sorted(secs) or any(y - x < 10 for x, y in zip(secs, secs[1:])):
            add("FAIL", "chapters invalid: need 3+ lines 'M:SS Title', first at 0:00, increasing, each at least 10s")
        if len(re.findall(r"#\w+", d)) > 15: add("FAIL", "more than 15 hashtags: YouTube ignores all of them")
        if not (re.search(r"(?i)divulga|voz sint|narra[cç][aã]o (gerada|sint)|intelig[eê]ncia artificial|synthetic|artificial intelligence|\\bAI\\b|voz sint[eé]tica|inteligencia artificial", d) or re.search(r"\bIA\b", d)): add("WARN", "no AI-use note in the description (see Anti-slop section: disclosure decision)")
        if re.search(r"(?i)urgente|chocante|você não vai acreditar|apocalipse|shocking|you won.t believe|urgent|apocalypse|increíble|no vas a creer", t + d): add("WARN", "title/description has clickbait or fake-urgency words")
        labels = (prefs_json(P).get("labels") or {})
        src_words = {labels.get("sources", "Sources"), "Sources", "Fontes", "Fuentes", "Quellen", "Sources"}
        if not any(w.lower() in d.lower() for w in src_words): add("FAIL", "description has no sources section (label from preferences.json labels.sources, default 'Sources')")
        import struct
        th = sorted((V / "package").glob("thumbnail*.png"))
        for f in th:
            b = f.read_bytes()
            wh = struct.unpack(">II", b[16:24]) if b[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)
            if wh != (1280, 720): add("FAIL", f"{f.name} is {wh[0]}x{wh[1]}, expected 1280x720")
            if len(b) > 2 * 1024 * 1024: add("FAIL", f"{f.name} is over 2 MB (YouTube limit)")
        if not (V / "package" / "thumbnail.png").exists(): add("FAIL", "package/thumbnail.png (variant A) missing")
        elif len(th) < 2: add("WARN", "only one thumbnail: make thumbnail_b.png (and _c) with a different idea for YouTube's Test & compare; describe A/B/C under '## Thumbnail'")
    else: add("WARN", "package/package.md not built yet")
    for lvl, msg in out: print(f"{lvl:<5} {msg}")
    sys.exit(1 if any(l == "FAIL" for l, _ in out) else 0)

main(sys.argv[1])
