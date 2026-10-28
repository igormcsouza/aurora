#!/usr/bin/env python3
"""Per-video state in draft_videos/<slug>/state.json (legacy: videos/). stdlib only.
  state.py init <slug> <topic> <minutes> <velocity>
  state.py done <slug> <step> [note]     mark step done
  state.py list                          unfinished videos (+ finished count)
  state.py next <slug>                   first pending step
  state.py tokens <slug>                 Claude tokens used between init and package done (main + subagents)
  state.py reset <slug> <step> [...]     set steps back to pending (after user feedback redoes them)
  state.py meta <slug> key=value [...]   record reproducibility facts in state.json "meta" (tts_model, voice_id, seed, ...)
  state.py snapshot <slug>               record tool versions (kit, ffmpeg, blender, node, playwright, manim) in state.json meta.tools
  state.py cost <slug>                   write cost.json: TTS characters and estimated USD, Claude tokens if tokens.json exists
  state.py costs                         one line per video (draft + published) from cost.json
Works from any subfolder: draft_videos/ (or legacy videos/) is found by walking up from the cwd. Published videos live in published_videos/ (see organize.py).
"""
import json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path

STEPS = ["preflight", "topic", "plan", "script", "voice", "draft", "review", "final", "package"]
def find_root():
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        for name in ("draft_videos", "videos"):
            if (d / name).is_dir(): return d / name
    return cwd / "draft_videos"
ROOT = find_root()
now = lambda: time.strftime("%Y-%m-%dT%H:%M:%S")

PUB = ROOT.parent / "published_videos"
def vdir(slug):
    """draft_videos/<slug>, else published_videos/<slug> (the full folder name incl. date prefix)."""
    return ROOT / slug if (ROOT / slug).exists() or not (PUB / slug).exists() else PUB / slug
def load(slug): return json.loads((vdir(slug) / "state.json").read_text())
def save(slug, s):
    s["updated"] = now()
    (vdir(slug) / "state.json").write_text(json.dumps(s, indent=2, ensure_ascii=False))
def pending(s): return next((k for k in STEPS if s["steps"][k]["status"] != "done"), None)

def tokens(slug):
    """Sum usage from session logs in the window [created, package done|now]. Dedupe by message id (streaming repeats).
    ponytail: window-based, so unrelated chat inside the window is counted too; no OpenAI TTS/whisper usage."""
    s = load(slug); utc = lambda t: datetime.fromisoformat(t).astimezone(timezone.utc)
    t0, t1 = utc(s["created"]), utc(s["steps"]["package"].get("at") or now())
    logs = Path.home() / ".claude/projects" / re.sub(r"[^A-Za-z0-9]", "-", str(ROOT.parent))
    msgs = {}
    for f in logs.rglob("*.jsonl"):
        for line in f.open():
            try: d = json.loads(line)
            except ValueError: continue
            m = d.get("message") or {}
            if d.get("type") == "assistant" and m.get("usage") and t0 <= datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")) <= t1:
                msgs[m.get("id") or d["uuid"]] = ("sub" if "subagents" in f.parts else "main", m["usage"])
    out = {}
    for who, u in msgs.values():
        o = out.setdefault(who, dict(calls=0, input=0, cache_write=0, cache_read=0, output=0)); o["calls"] += 1
        o["input"] += u.get("input_tokens", 0); o["cache_write"] += u.get("cache_creation_input_tokens", 0)
        o["cache_read"] += u.get("cache_read_input_tokens", 0); o["output"] += u.get("output_tokens", 0)
    out["total"] = {k: sum(v[k] for v in out.values()) for k in ("calls", "input", "cache_write", "cache_read", "output")}
    (ROOT / slug / "tokens.json").write_text(json.dumps(out, indent=2))
    for k, v in out.items(): print(f"{k:<6}", *(f"{n}={c:,}" for n, c in v.items()))

PRICE_PER_1K = {"eleven_v4": 0.08, "eleven_v4_turbo": 0.04}   # USD per 1K characters, from the skill's notes; an estimate, not a bill

def tool_versions():
    import subprocess
    kit = ROOT.parent / "video-kit"; out = {}
    def run(*c):
        try: return subprocess.run(c, capture_output=True, text=True, timeout=20).stdout.strip().splitlines()[0]
        except Exception: return ""
    if (kit / "KIT_VERSION").exists(): out["kit"] = (kit / "KIT_VERSION").read_text().strip()
    out["ffmpeg"] = run("ffmpeg", "-version"); out["blender"] = run("blender", "--version"); out["node"] = run("node", "--version")
    for n in ("playwright", "gsap"):
        f = kit / "web" / "node_modules" / n / "package.json"
        if f.exists(): out[n] = json.loads(f.read_text())["version"]
    py = kit / ".venv" / "bin" / "python"
    if py.exists(): out["manim"] = run(str(py), "-c", "import manim;print(manim.__version__)")
    return {k: v for k, v in out.items() if v}

def cost(slug):
    d = vdir(slug); s = load(slug); plan = json.loads((d / "plan.json").read_text())
    chars = sum(len(sc.get("narration", "")) for sc in plan["scenes"]); model = s.get("meta", {}).get("tts_model", "eleven_v4")
    c = {"tts_model": model, "tts_chars": chars, "tts_usd_est": round(chars / 1000 * PRICE_PER_1K.get(model, 0.08), 2), "note": "one full TTS pass; retakes and drafts add to this"}
    tl = ROOT.parent / "aurora" / "tiers.jsonl"
    if tl.exists():
        rows = [json.loads(x) for x in tl.read_text().splitlines() if x.strip()]; rows = [r for r in rows if r.get("video") == slug]
        c["tiers"] = {str(t): {"runs": sum(r["tier"] == t for r in rows), "fail": sum(r["tier"] == t and r["result"] != "pass" for r in rows), "tokens": sum(r["tokens"] for r in rows if r["tier"] == t)} for t in range(4) if any(r["tier"] == t for r in rows)}
    if (d / "tokens.json").exists(): c["claude_tokens"] = json.loads((d / "tokens.json").read_text()).get("total", {})
    (d / "cost.json").write_text(json.dumps(c, indent=2)); print(json.dumps(c))

def costs():
    for base in (ROOT, PUB):
        for f in sorted(base.glob("*/cost.json")) if base.is_dir() else []:
            c = json.loads(f.read_text()); t = c.get("claude_tokens", {})
            print(f"{f.parent.name:<40} tts ${c.get('tts_usd_est', 0):>5}  {c.get('tts_chars', 0):>6} chars  output tokens {t.get('output', '-')}")

def main(a):
    cmd = a[0] if a else "list"
    if cmd == "init":
        slug, topic, minutes, velocity = a[1:5]
        (ROOT / slug / "package").mkdir(parents=True, exist_ok=True)
        if not (ROOT / slug / "state.json").exists():
            save(slug, {"slug": slug, "topic": topic, "minutes": int(minutes), "velocity": velocity,
                        "created": now(), "steps": {k: {"status": "pending"} for k in STEPS}})
    elif cmd == "done":
        s = load(a[1]); s["steps"][a[2]] = {"status": "done", "at": now(), **({"note": a[3]} if len(a) > 3 else {})}
        save(a[1], s)
    elif cmd == "meta":
        s = load(a[1]); s.setdefault("meta", {}).update(dict(kv.split("=", 1) for kv in a[2:])); save(a[1], s)
    elif cmd == "snapshot":
        s = load(a[1]); s.setdefault("meta", {})["tools"] = tool_versions(); save(a[1], s); print(json.dumps(s["meta"]["tools"]))
    elif cmd == "cost": cost(a[1])
    elif cmd == "costs": costs()
    elif cmd == "tokens":
        tokens(a[1])
    elif cmd == "reset":
        s = load(a[1])
        for k in a[2:]: s["steps"][k] = {"status": "pending"}
        save(a[1], s)
    elif cmd == "next":
        print(pending(load(a[1])) or "finished")
    elif cmd == "list":
        done = 0
        for p in sorted(ROOT.glob("*/state.json")):
            s = json.loads(p.read_text()); n = pending(s)
            if n is None: done += 1; continue
            print(f"{s['slug']:<32} next={n:<9} {s['minutes']}min {s['velocity']} updated={s['updated']}  \"{s['topic']}\"")
        pub = ROOT.parent / "published_videos"
        print(f"({done} finished in draft, {len(list(pub.glob('*/state.json'))) if pub.is_dir() else 0} published)")

main(sys.argv[1:])
