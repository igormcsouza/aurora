#!/usr/bin/env python3
"""Cut vertical Shorts (1080x1920) from a finished long video. stdlib + ffmpeg/ffprobe.
  shorts.py list  <video_dir>                          scenes with absolute start/end in package/video.mp4 + jokes/narration, to pick moments
  shorts.py cut   <video_dir> --start S --end E --title "TEXT" [--out shorts/01.mp4] [--no-captions]
  shorts.py check <video_dir>                          every shorts/*.mp4: 1080x1920, <= 180 s; shorts/shorts.md has no < or >
<video_dir> = draft_videos/<slug> or published_videos/<date>_<slug>. Layout: blurred full-bleed background, the 16:9 video centered, title on top, burned captions from scenes/cues.json."""
import json, re, subprocess, sys, tempfile, textwrap
from pathlib import Path

def load(v):
    v = Path(v); plan = json.loads((v / "plan.json").read_text()); sc = v / "scenes"
    durs, cues = json.loads((sc / "durations.json").read_text()), json.loads((sc / "cues.json").read_text())
    out, t = [], 0.0
    for i, s in enumerate(plan["scenes"]):
        k = str(s["id"]); d = float(durs[k] if isinstance(durs, dict) and k in durs else durs[i] if isinstance(durs, list) else durs[i])
        c = cues.get(k) if isinstance(cues, dict) else cues[i]
        out.append({"id": s["id"], "start": t, "end": t + d, "cues": c or [], "joke": s.get("joke", ""), "text": s.get("narration", "")}); t += d
    return out

def srt_time(x): h, r = divmod(max(x, 0), 3600); m, s = divmod(r, 60); return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

def captions(scenes, a, b):
    rows, n = [], 0
    for s in scenes:
        for c in s["cues"]:
            cs, ce = s["start"] + c["start"], s["start"] + c["end"]
            if ce <= a or cs >= b: continue
            n += 1; rows.append(f"{n}\n{srt_time(max(cs, a) - a)} --> {srt_time(min(ce, b) - a)}\n" + "\n".join(textwrap.wrap(c["text"], 24)[:3]) + "\n")
    return "\n".join(rows)

def cut(v, a, b, title, out, caps):
    v = Path(v); src = v / "package" / "video.mp4"; out = Path(out) if out else v / "shorts" / f"{len(list((v / 'shorts').glob('*.mp4'))) + 1 if (v / 'shorts').is_dir() else 1:02}.mp4"
    out = out if out.is_absolute() else v / out; out.parent.mkdir(parents=True, exist_ok=True)
    if re.search(r"[<>]", title): sys.exit("title contains < or > (YouTube rejects them)")
    if b - a > 180: sys.exit("a Short is at most 3 minutes; aim for 20-45 s")
    font = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans:bold"], capture_output=True, text=True).stdout
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); (td / "title.txt").write_text("\n".join(textwrap.wrap(title, 18)[:3]))
        vf = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v0];"
              f"[v0]drawtext=fontfile={font}:textfile={td / 'title.txt'}:fontcolor=white:fontsize=78:line_spacing=12:box=1:boxcolor=black@0.45:boxborderw=24:x=(w-text_w)/2:y=170[v1]")
        if caps:
            (td / "cap.srt").write_text(captions(load(v), a, b))
            vf += f";[v1]subtitles={td / 'cap.srt'}:force_style='Alignment=2,MarginV=55,FontSize=11,Bold=1,Outline=3,Shadow=0'[v]"
        else: vf += ";[v1]null[v]"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", str(src), "-filter_complex", vf, "-map", "[v]", "-map", "0:a", "-af", f"afade=t=in:d=0.15,afade=t=out:st={b - a - 0.2}:d=0.2",
                            "-r", "30", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)])
    if r.returncode: sys.exit("ffmpeg failed")
    print(out)

def probe(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "json", str(f)], capture_output=True, text=True)
    j = json.loads(r.stdout); return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])

def main(a):
    cmd, v = a[0], a[1]; g = lambda k, d="": a[a.index(k) + 1] if k in a else d
    if cmd == "list":
        for s in load(v): print(f"{s['id']!s:>4}  {s['start']:7.1f}-{s['end']:7.1f}  {'[joke] ' if s['joke'] else ''}{s['text'][:90]}")
    elif cmd == "cut": cut(v, float(g("--start")), float(g("--end")), g("--title"), g("--out"), "--no-captions" not in a)
    elif cmd == "check":
        bad = 0
        for f in sorted((Path(v) / "shorts").glob("*.mp4")):
            w, h, d = probe(f); ok = (w, h) == (1080, 1920) and d <= 180; bad += not ok; print(("PASS" if ok else "FAIL"), f.name, f"{w}x{h}", f"{d:.0f}s")
        md = Path(v) / "shorts" / "shorts.md"
        if md.exists() and re.search(r"[<>]", md.read_text()): print("FAIL shorts.md contains < or >"); bad += 1
        sys.exit(1 if bad else 0)
    else: print(__doc__)

main(sys.argv[1:])
