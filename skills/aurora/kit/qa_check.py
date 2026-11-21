#!/usr/bin/env python3
"""Automatic QA on a draft or final. stdlib + ffmpeg/ffprobe.
  qa_check.py <video.mp4> [--target -14]
Checks: (1) end of audio: audio is not cut off (audio length within 0.5 s of video length) and the last 1.5 s is not a loud cut;
(2) muted preview: no frozen picture longer than 3 s (a viewer with sound off must always see something change);
(3) dead air: no silence longer than 4 s in the middle; (4) loudness within 1.5 LU of target, true peak <= -1 dBTP.
Exit 1 and one line per problem with a timestamp; prints OK otherwise."""
import re, subprocess, sys

def ff(*a): return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *a], capture_output=True, text=True).stderr
def dur(f, s): return float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", s, "-show_entries", "stream=duration", "-of", "csv=p=0", f], text=True).split()[0])
def ts(x): return f"{int(x // 60)}:{int(x % 60):02d}"

def check(f, target=-14.0):
    bad, V, A = [], dur(f, "v:0"), dur(f, "a:0")
    if abs(V - A) > 0.5: bad.append(f"end of audio: video {V:.1f}s vs audio {A:.1f}s ({'audio cut off' if A < V else 'audio runs past the picture'})")
    fz = ff("-i", f, "-vf", "freezedetect=n=-55dB:d=3", "-an", "-f", "null", "-"); st = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", fz)]; du = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", fz)]
    for i, s0 in enumerate(st): bad.append(f"muted preview: picture frozen {du[i] if i < len(du) else V - s0:.1f}s at {ts(s0)}")
    sil = re.findall(r"silence_start: ([\d.]+).*?silence_duration: ([\d.]+)", ff("-i", f, "-vn", "-af", "silencedetect=n=-45dB:d=4", "-f", "null", "-"), re.S)
    for s, d in sil:
        if float(s) + float(d) < A - 1.0: bad.append(f"dead air: {float(d):.1f}s of silence at {ts(float(s))}")
    o = ff("-i", f, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"); I = re.findall(r"I:\s+(-?[\d.]+) LUFS", o); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", o)
    if I and abs(float(I[-1]) - target) > 1.5: bad.append(f"loudness {I[-1]} LUFS, target {target}")
    if P and float(P[-1]) > -1.0: bad.append(f"true peak {P[-1]} dBTP, above -1")
    tail = re.findall(r"mean_volume: (-?[\d.]+)", ff("-ss", str(max(A - 1.5, 0)), "-i", f, "-vn", "-af", "volumedetect", "-f", "null", "-"))
    if tail and float(tail[-1]) > -20: bad.append(f"end of audio: last 1.5 s is loud ({tail[-1]} dB mean): likely cut mid-sound, add a tail or fade")
    return bad

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    b = check(a[0], float(a[a.index("--target") + 1]) if "--target" in a else -14.0)
    print("\n".join(b) if b else "OK"); sys.exit(1 if b else 0)
