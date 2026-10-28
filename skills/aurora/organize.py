#!/usr/bin/env python3
"""Project layout for aurora (stdlib only). Run from the channel project (any subfolder).
  organize.py scan [--published slug[:YYYY-MM-DD],...]   DRY RUN: find existing videos in any layout, classify, print a plan (JSON at the end)
  organize.py apply <plan.json> [--yes]                    run an approved plan (without --yes it only prints)
  organize.py publish <slug> [--date YYYY-MM-DD] [--url URL] [--yes]   draft_videos/<slug> -> published_videos/<date>_<slug>, prune what is not needed
  organize.py trash [--empty --yes]                        list .aurora_trash with sizes, or delete it for real
Nothing is ever deleted directly: "trash" means moved into .aurora_trash/<stamp>/ (same relative path), emptied only by `trash --empty --yes`.
Layout:  published_videos/  draft_videos/  aurora/  channel/  video-kit/  preferences.json
"""
import fnmatch, hashlib, json, re, shutil, sys, time
from pathlib import Path

DRAFT, PUB, TRASH, AUR = "draft_videos", "published_videos", ".aurora_trash", "aurora"
SKIP = {"video-kit", "channel", AUR, DRAFT, PUB, TRASH, ".git", "node_modules", ".venv", "__pycache__", ".claude", ".agents"}
# what a published video keeps so it can be rebuilt (scenes + audio + the texts), checked first
KEEP = ["package/*", "plan.json", "narration.md", "sources.md", "visual_assets.md", "state.json", "published.json", "tokens.json", "final.mp4", "final_nomusic.mp4",
        "assets/*", "asr/*.json", "scenes/spec.json", "scenes/cues.json", "scenes/durations.json", "scenes/tts_overrides.json", "scenes/*.mp3", "scenes/*.wav",
        "scenes/*.py", "scenes/hero_*", "scenes/final/*", "shorts/*", "cost.json"]
# what is not needed once the video is out
TRASH_PAT = ["voice_samples/*", "*contact*", "*sheet*", "qa.md", "*.log", "media/*", "*/__pycache__/*", "*_frames/*", "tmp/*", "temp/*", "renders/*", "drafts/*", "*partial_movie_files*",
             "draft*.mp4", "*draft*.srt", "scenes/*.mp4", "scenes/*.mov", "*.tmp", "*.DS_Store", "test_*", "*_test*", "test/*", "tests/*"]
STEPS = ["preflight", "topic", "plan", "script", "voice", "draft", "review", "final", "package"]

def root():
    cwd = Path.cwd()
    return next((d for d in [cwd, *cwd.parents] if (d / "preferences.json").exists() or (d / DRAFT).is_dir() or (d / PUB).is_dir() or (d / "videos").is_dir()), cwd)

def size(p):
    p = Path(p); return p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
def human(n):
    for u in "B KB MB GB".split():
        if n < 1024 or u == "GB": return f"{n:.0f}{u}" if u == "B" else f"{n:.1f}{u}"
        n /= 1024
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def match(rel, pats): return any(fnmatch.fnmatch(rel, p) for p in pats)

def classify(folder):
    """-> (keep, trash, review) lists of paths relative to `folder`; trash is reported as the topmost trashable dir/file."""
    folder, keep, trash, review = Path(folder), [], [], []
    pk = folder / "package" / "video.mp4"
    for f in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = f.relative_to(folder).as_posix()
        if rel == "final.mp4" and pk.exists() and f.stat().st_size == pk.stat().st_size and sha(f) == sha(pk): trash.append(rel)   # duplicate of the package copy
        elif match(rel, KEEP): keep.append(rel)
        elif match(rel, TRASH_PAT): trash.append(rel)
        else: review.append(rel)
    return keep, trash, review

def infer_state(folder):
    f = Path(folder); sc = f / "scenes"; has = lambda *g: any(list(f.glob(x)) for x in g)
    done = {"preflight": has("plan.json", "narration.md"), "topic": has("plan.json", "narration.md"), "plan": (f / "plan.json").exists(), "script": (f / "narration.md").exists(),
            "voice": bool(list(sc.glob("*.mp3"))) and (sc / "cues.json").exists(), "draft": has("draft*.mp4", "scenes/*.mp4"), "review": has("scenes/final/*.mp4", "final*.mp4"),
            "final": has("scenes/final/*.mp4", "final.mp4", "package/video.mp4"), "package": (f / "package" / "package.md").exists() and (f / "package" / "video.mp4").exists()}
    t = time.strftime("%Y-%m-%dT%H:%M:%S")
    return {"slug": f.name, "topic": f.name.replace("-", " "), "minutes": 10, "velocity": "serial", "created": t, "updated": t,
            "steps": {k: ({"status": "done", "at": t, "note": "inferred from files by organize.py"} if done[k] else {"status": "pending"}) for k in STEPS}}

def video_dirs(R):
    """Candidate video folders anywhere in the project (depth <= 2), except the tool dirs."""
    out = []
    def looks(d): return any((d / m).exists() for m in ("plan.json", "narration.md", "state.json", "scenes", "package")) or any(d.glob("final*.mp4"))
    for top in sorted(p for p in R.iterdir() if p.is_dir() and p.name not in SKIP and not p.name.startswith(".")):
        if looks(top): out.append(top)
        else: out += [c for c in sorted(top.iterdir()) if c.is_dir() and not c.name.startswith(".") and looks(c)]
    for p in sorted((R / DRAFT).glob("*")) if (R / DRAFT).is_dir() else []:
        if p.is_dir(): out.append(p)
    for p in sorted((R / PUB).glob("*")) if (R / PUB).is_dir() else []:
        if p.is_dir(): out.append(p)
    return out

def scan(R, published):
    pub = {}
    for item in published:
        slug, _, date = item.partition(":"); pub[slug] = date
    plan = {"root": str(R), "moves": [], "trash": [], "infer_state": [], "review": [], "ask_published": [], "notes": []}
    for d in video_dirs(R):
        rel = d.relative_to(R).as_posix()
        if rel.startswith(DRAFT + "/") or rel.startswith(PUB + "/"): continue      # already in place
        slug = d.name; ready = any((d / x).exists() for x in ("package/video.mp4", "final.mp4")) or any((d / "scenes" / "final").glob("*.mp4"))
        if slug in pub:
            date = pub[slug] or time.strftime("%Y-%m-%d", time.localtime((d / "package" / "video.mp4").stat().st_mtime if (d / "package" / "video.mp4").exists() else d.stat().st_mtime))
            dest = f"{PUB}/{date}_{slug}"; keep, trash, review = classify(d)
            plan["trash"] += [{"path": f"{rel}/{t}", "bytes": size(d / t)} for t in trash]; plan["review"] += [f"{rel}/{r}" for r in review]
        else:
            dest = f"{DRAFT}/{slug}"
            if ready: plan["ask_published"].append(slug)
        plan["moves"].append({"from": rel, "to": dest, "kind": "video"})
        if not (d / "state.json").exists(): plan["infer_state"].append(dest)
        pk = d / "package" / "package.md"
        if pk.exists() and "## Description" not in pk.read_text(): plan["notes"].append(f"{rel}: package.md is in the old format (no '## Description'); re-run the producer's package step before publishing")
    for name, dest in (("topics.log", "topics.log"), ("_research.md", "research.md"), ("_batch.md", "batch.md")):
        for base in ("videos", "video", DRAFT):
            p = R / base / name
            if p.exists(): plan["moves"].append({"from": f"{base}/{name}", "to": f"{AUR}/{dest}", "kind": "file"})
    loose = [p.relative_to(R).as_posix() for p in R.glob("*.mp4")] + [p.relative_to(R).as_posix() for p in R.glob("*.srt")]
    if loose: plan["review"] += loose; plan["notes"].append("loose media files at the project root are left alone: tell Aurora which video they belong to")
    return plan

def show(plan):
    print(f"Project: {plan['root']}")
    for m in plan["moves"]: print(f"  MOVE   {m['from']}  ->  {m['to']}")
    t = sum(x["bytes"] for x in plan["trash"])
    if plan["trash"]: print(f"  TRASH  {len(plan['trash'])} items, {human(t)} (moved to {TRASH}/, reversible):"); [print(f"           {x['path']}  {human(x['bytes'])}") for x in plan["trash"][:40]]
    for p in plan["infer_state"]: print(f"  STATE  infer {p}/state.json from its files")
    for p in plan["review"][:40]: print(f"  KEEP?  not classified, left untouched: {p}")
    if plan["ask_published"]: print("  ASK    these look finished; which of them were published? " + ", ".join(plan["ask_published"]))
    for n in plan["notes"]: print(f"  NOTE   {n}")

def do_trash(R, paths, stamp):
    n = 0
    for rel in paths:
        src = R / rel
        if not src.exists(): continue
        dst = R / TRASH / stamp / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), str(dst)); n += 1
    return n

def compact_frames(folder, yes):
    """Frame sequences (record.mjs) -> one mp4 + a small json; the frames go to the caller's trash. Returns [(dir, mp4)]."""
    import subprocess
    out = []
    for d in sorted(p for p in Path(folder).rglob("*") if p.is_dir()):
        fr = sorted(d.glob("[0-9][0-9][0-9][0-9][0-9].jpg"))
        if len(fr) < 10: continue
        spec = Path(folder) / "scenes" / "spec.json"; fps = 10
        try:
            for sc in json.loads(spec.read_text()) if spec.exists() else []:
                v = (sc.get("props") or {}).get("video") or {}
                if v.get("dir") and Path(v["dir"]).name == d.name: fps = v.get("fps", 10)
        except Exception: pass
        mp4 = d.with_suffix(".mp4"); out.append((d, mp4, fps, len(fr)))
        if yes and not mp4.exists():
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(d / "%05d.jpg"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(mp4)])
            if r.returncode: sys.exit(f"compaction of {d} failed")
            mp4.with_suffix(".frames.json").write_text(json.dumps({"fps": fps, "count": len(fr), "pattern": "%05d.jpg", "rebuild": f"ffmpeg -i {mp4.name} -qscale:v 2 {d.name}/%05d.jpg"}))
    return out

def prune_empty(d):
    for p in sorted((x for x in Path(d).rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
        if not any(p.iterdir()): p.rmdir()

def apply(R, plan, yes):
    show(plan)
    if not yes: print("\nDRY RUN. Re-run with --yes after the user approved this plan."); return
    stamp = time.strftime("%Y%m%d-%H%M%S"); (R / DRAFT).mkdir(exist_ok=True); (R / PUB).mkdir(exist_ok=True); (R / AUR).mkdir(exist_ok=True)
    n = do_trash(R, [x["path"] for x in plan["trash"]], stamp)
    for m in plan["moves"]:
        src, dst = R / m["from"], R / m["to"]
        if dst.exists(): print(f"SKIP {m['to']} already exists"); continue
        if not src.exists(): print(f"SKIP {m['from']} is gone"); continue
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), str(dst))
    for p in plan["infer_state"]:
        f = R / p / "state.json"
        if (R / p).is_dir() and not f.exists(): f.write_text(json.dumps(infer_state(R / p), indent=2, ensure_ascii=False))
    for m in plan["moves"]:
        d = R / m["to"]
        if m["to"].startswith(PUB + "/") and d.is_dir():
            date, _, slug = d.name.partition("_"); mark_published(R, d, slug, date)
    for base in ("videos", "video"):
        if (R / base).is_dir(): prune_empty(R / base); (R / base).rmdir() if not any((R / base).iterdir()) else print(f"NOTE {base}/ still has files: {[p.name for p in (R / base).iterdir()][:8]}")
    print(f"\nDone: {len(plan['moves'])} moves, {n} items to {TRASH}/{stamp}. Empty the trash later with: organize.py trash --empty --yes")

def mark_published(R, dest, slug, date, url=""):
    """published.json, state.json stamp, jokes ledger and topics log (shared by `publish` and by `apply` for adopted videos)."""
    pj = dest / "published.json"
    kv = R / "video-kit" / "KIT_VERSION"
    if not pj.exists(): pj.write_text(json.dumps({"slug": slug, "date": date, "url": url or "", "youtube_id": "", "kit_version": kv.read_text().strip() if kv.exists() else "",
                                                  "note": "fill url/youtube_id after upload; analise uses them"}, indent=2))
    sj = dest / "state.json"
    if sj.exists(): s = json.loads(sj.read_text()); s["published"] = date; sj.write_text(json.dumps(s, indent=2, ensure_ascii=False))
    (R / AUR).mkdir(exist_ok=True)
    pl = dest / "plan.json"
    if pl.exists():
        plan = json.loads(pl.read_text()); log = R / AUR / "topics.log"
        with open(R / AUR / "jokes.jsonl", "a") as f:
            for sc in plan.get("scenes", []):
                if sc.get("joke"): f.write(json.dumps({"video": slug, "scene": sc.get("id"), "joke": sc["joke"]}, ensure_ascii=False) + "\n")
        if not log.exists() or slug not in log.read_text(): open(log, "a").write(f"{date}\t{slug}\t{plan.get('title', slug)}\n")

def publish(R, slug, date, url, yes):
    src = R / DRAFT / slug
    if not src.is_dir(): sys.exit(f"{src} not found")
    pk = src / "package"
    miss = [x for x in ("video.mp4", "thumbnail.png", "subtitles.srt", "package.md") if not (pk / x).exists()]
    if miss: sys.exit(f"package/ is missing {miss}: finish the package step first")
    date = date or time.strftime("%Y-%m-%d"); dest = R / PUB / f"{date}_{slug}"
    keep, trash, review = classify(src)
    print(f"publish {slug} -> {dest.relative_to(R)}\n  keep {len(keep)} files {human(sum(size(src / k) for k in keep))}; trash {len(trash)} files {human(sum(size(src / t) for t in trash))}; unclassified (kept) {len(review)}")
    for t in trash[:30]: print(f"    trash  {t}  {human(size(src / t))}")
    for r in review[:30]: print(f"    keep?  {r}")
    for d, mp4, fps, n in compact_frames(src, False): print(f"    compact {d.relative_to(src)} ({n} frames) -> {mp4.name} (frames go to trash)")
    if dest.exists(): sys.exit(f"{dest} already exists")
    if not yes: print("\nDRY RUN. Re-run with --yes to publish (the trash stays recoverable in .aurora_trash until emptied)."); return
    stamp = time.strftime("%Y%m%d-%H%M%S"); do_trash(R, [f"{DRAFT}/{slug}/{t}" for t in trash], stamp)
    do_trash(R, [d.relative_to(R).as_posix() for d, *_ in compact_frames(src, True)], stamp)
    dest.parent.mkdir(exist_ok=True); shutil.move(str(src), str(dest)); prune_empty(dest)
    mark_published(R, dest, slug, date, url)
    print(f"\nPublished: {dest.relative_to(R)}. Fill published.json (url/youtube_id) after the upload.")

def trash_cmd(R, empty, yes):
    t = R / TRASH
    if not t.exists(): print("trash is empty"); return
    for s in sorted(t.iterdir()): print(f"  {s.name}  {human(size(s))}")
    if empty and yes: shutil.rmtree(t); print("trash emptied")
    elif empty: print("add --yes to really delete")

def main(a):
    R = root(); cmd = a[0] if a else ""
    if cmd == "scan":
        pub = a[a.index("--published") + 1].split(",") if "--published" in a else []
        plan = scan(R, pub); show(plan); print("\n" + json.dumps(plan, indent=1, ensure_ascii=False))
    elif cmd == "apply": apply(R, json.loads(Path(a[1]).read_text()), "--yes" in a)
    elif cmd == "publish":
        g = lambda k: a[a.index(k) + 1] if k in a else ""
        publish(R, a[1], g("--date"), g("--url"), "--yes" in a)
    elif cmd == "trash": trash_cmd(R, "--empty" in a, "--yes" in a)
    else: print(__doc__)

main(sys.argv[1:])
