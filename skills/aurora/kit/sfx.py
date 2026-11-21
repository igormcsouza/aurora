#!/usr/bin/env python3
"""Sparse sound-effect track for a video (opt-in: preferences.json "sfx": true). stdlib only, no sound files to license: the sounds are synthesised.
  sfx.py <video_dir> [--gap 5] [--gain 0.12]   writes <video_dir>/sfx.wav (48 kHz mono, as long as the video) and prints the event list
Events: a soft whoosh at every scene change, a pop on scene beats (scenes/spec.json "beats", scene-relative), never closer than --gap seconds to the previous event
so ten minutes never turn into a constant effect. Peaks sit at --gain (0.12 = about -18 dBFS), well under the narration.
Mix into the final: ffmpeg -i video.mp4 -i sfx.wav -filter_complex "[0:a][1:a]amix=inputs=2:normalize=0:duration=first[a]" -map 0:v -map "[a]" -c:v copy out.mp4"""
import array, json, math, random, sys, wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import shorts
SR = 48000

def whoosh(g):
    r = random.Random(1); n = int(SR * .55); out = []; lp = 0.0
    for i in range(n):
        u = i / n; env = math.sin(math.pi * u) ** 2; k = 0.02 + 0.3 * u          # noise whose cutoff sweeps up: the "whoosh"
        lp += k * (r.uniform(-1, 1) - lp); out.append(lp * 2 * env * g)
    return out

def pop(g):
    n = int(SR * .18); return [math.sin(2 * math.pi * (300 + 700 * math.exp(-i / SR * 30)) * i / SR) * math.exp(-i / SR * 24) * g for i in range(n)]

def build(v, gap=5.0, gain=0.12):
    v = Path(v); scenes = shorts.load(v); total = scenes[-1]["end"]; spec = v / "scenes" / "spec.json"
    beats = {}
    if spec.exists():
        raw = json.loads(spec.read_text()); raw = raw if isinstance(raw, list) else raw.get("scenes", [])
        beats = {str(s["id"]): s.get("beats") or [] for s in raw}
    ev = []
    for i, s in enumerate(scenes):
        if i: ev.append((s["start"], "whoosh"))
        ev += [(s["start"] + b, "pop") for b in beats.get(str(s["id"]), [])[:1] if 0.8 < b < s["end"] - s["start"] - 1]   # one pop per scene: the first beat
    ev.sort(); keep, last = [], -1e9
    for t, k in ev:
        if t - last >= gap: keep.append((t, k)); last = t
    buf = array.array("h", [0]) * int((total + 1) * SR); snd = {"whoosh": whoosh(gain), "pop": pop(gain)}
    for t, k in keep:
        o = int(t * SR) - (int(SR * .25) if k == "whoosh" else 0)                     # the whoosh peaks ON the cut
        for j, x in enumerate(snd[k]):
            if 0 <= o + j < len(buf): buf[o + j] = max(-32767, min(32767, buf[o + j] + int(x * 32767)))
    with wave.open(str(v / "sfx.wav"), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(buf.tobytes())
    return keep

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    ev = build(a[0], float(a[a.index("--gap") + 1]) if "--gap" in a else 5.0, float(a[a.index("--gain") + 1]) if "--gain" in a else 0.12)
    print(f"sfx.wav: {len(ev)} events"); print(", ".join(f"{int(t // 60)}:{t % 60:04.1f} {k}" for t, k in ev))
