#!/usr/bin/env python3
"""scenario_render.py <spec.json> <out.mp4> [--draft] [--jobs N]
Renders a Blender scenario (see scenario.py) as N parallel Blender processes over frame ranges, then encodes a silent 30 fps H.264 clip.
Frames are cached in <out>_frames/ (kept until the encode succeeds); resume by re-running."""
import json, os, subprocess, sys, shutil
from pathlib import Path

def main(a):
    if len(a) < 2: print(__doc__); return 2
    spec, out = Path(a[0]).resolve(), Path(a[1]).resolve(); draft = '--draft' in a; jobs = int(a[a.index('--jobs') + 1]) if '--jobs' in a else min(6, os.cpu_count() or 2)
    n = round(json.loads(spec.read_text())['duration'] * 30); tmp = out.with_name(out.stem + '_frames'); tmp.mkdir(exist_ok=True)
    per = -(-n // jobs); procs = []
    for j in range(jobs):
        f0, f1 = j * per + 1, min(n, (j + 1) * per)
        if f0 > f1 or all((tmp / f'f_{k:04d}.png').exists() for k in range(f0, f1 + 1)): continue
        procs.append(subprocess.Popen(['blender', '-b', '-P', str(Path(__file__).with_name('scenario.py')), '--', str(spec), 'range', str(f0), str(f1), str(tmp), *(['--draft'] if draft else [])], stdout=open(tmp / f'log_{j}.txt', 'w'), stderr=subprocess.STDOUT))
    if any(p.wait() for p in procs): print(f'blender failed: see {tmp}/log_*.txt'); return 1
    done = len(list(tmp.glob('f_*.png')))
    if done < n: print(f'only {done}/{n} frames rendered: see {tmp}/log_*.txt'); return 1
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', str(tmp / 'f_%04d.png'), '-vf', 'scale=1920:1080:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '27' if draft else '17', '-an', str(out)])
    if r.returncode == 0: shutil.rmtree(tmp)
    return r.returncode

if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
