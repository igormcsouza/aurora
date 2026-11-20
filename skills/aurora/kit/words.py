#!/usr/bin/env python3
"""Word-level timings for the web engine (stdlib only).
  words.py <video_dir>     reads <video_dir>/asr/NN.json (ElevenLabs /with-timestamps character alignment, saved per scene)
                           and writes <video_dir>/scenes/words.json: {"<scene id>": [{"w": word, "s": start_s, "e": end_s}, ...]}
capture.mjs picks it up by spec.id; templates query it through the word clock (kinetic_words, anything that wants `clock.at(...)`).
Words are the TTS text: [tags] are dropped; tts_overrides respellings stay as spoken (the clock matches loosely and falls back to even spacing).
"""
import json, re, sys
from pathlib import Path

def words(al):
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, cur, s, e, depth = [], "", None, None, 0
    def flush():
        nonlocal cur, s, e
        if cur.strip("-'’"): out.append({"w": cur, "s": round(s, 3), "e": round(e, 3)})
        cur, s, e = "", None, None
    for c, a, b in zip(ch, st, en):
        if c == "[": depth += 1; continue
        if c == "]": depth = max(0, depth - 1); continue
        if depth: continue
        if c.isspace(): flush(); continue
        if s is None: s = a
        cur += c; e = b
    flush()
    return out

def main(d):
    d = Path(d); res = {}
    for f in sorted((d / "asr").glob("*.json")):
        j = json.loads(f.read_text()); w = words(j.get("alignment") or j.get("normalized_alignment") or j)
        res[f.stem] = w
        if f.stem.isdigit(): res[str(int(f.stem))] = w
    (d / "scenes").mkdir(exist_ok=True); (d / "scenes" / "words.json").write_text(json.dumps(res, ensure_ascii=False))
    print(f"scenes/words.json: {len(list((d / 'asr').glob('*.json')))} scenes")

def demo():
    al = {"characters": list("[calm] Olá, mundo!"), "character_start_times_seconds": [i / 10 for i in range(18)], "character_end_times_seconds": [(i + 1) / 10 for i in range(18)]}
    w = words(al); assert [x["w"] for x in w] == ["Olá,", "mundo!"] and w[0]["s"] == 0.7 and w[1]["e"] == 1.8, w

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest": demo(); print("ok")
    elif len(sys.argv) == 2: main(sys.argv[1])
    else: print(__doc__); sys.exit(2)
