#!/usr/bin/env python3
"""Local review page for a draft. stdlib only.
  review.py <video_dir> [--port 8765]   serves the draft with a scene list (click = seek), one note box per scene, and Approve.
Saves <video_dir>/review.json: {"approved": bool, "notes": [{"scene": id, "at": "M:SS", "text": "..."}]}. Aurora's `review` step reads it:
approved + no notes = go to final; notes = route each to the owning role by scene id. Binds to 127.0.0.1 only."""
import json, re, sys, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); import shorts

def page(v, scenes):
    rows = "".join(f'<div class=r><a href="#" onclick="go({s["start"]});return false">scene {s["id"]} · {int(s["start"]//60)}:{int(s["start"]%60):02d}</a><span>{(s["text"] or "")[:90]}</span><textarea data-s="{s["id"]}" data-at="{int(s["start"]//60)}:{int(s["start"]%60):02d}" placeholder="what is wrong here?"></textarea></div>' for s in scenes)
    return f"""<!doctype html><meta charset=utf-8><title>aurora review</title><style>body{{font:15px system-ui;margin:0;display:flex;height:100vh;background:#15131f;color:#eee}}
#l{{width:62%;padding:16px}}video{{width:100%;border-radius:10px}}#r{{width:38%;overflow:auto;padding:16px}}.r{{margin-bottom:12px}}.r a{{color:#7ae582;font-weight:700}}.r span{{display:block;color:#aaa;font-size:13px}}
textarea{{width:100%;height:46px;background:#25223a;color:#eee;border:1px solid #444;border-radius:8px;padding:6px}}button{{padding:10px 18px;border:0;border-radius:8px;font-weight:700;cursor:pointer;margin-right:8px}}#ok{{background:#7ae582}}#s{{background:#ffd166}}</style>
<div id=l><video id=v src="/video" controls></video><p><button id=s onclick="save(false)">Save notes</button><button id=ok onclick="save(true)">Approve</button><span id=m></span></p></div><div id=r>{rows}</div>
<script>const v=document.getElementById('v');function go(t){{v.currentTime=t;v.play()}}
async function save(a){{const notes=[...document.querySelectorAll('textarea')].filter(t=>t.value.trim()).map(t=>({{scene:t.dataset.s,at:t.dataset.at,text:t.value.trim()}}));
await fetch('/save',{{method:'POST',body:JSON.stringify({{approved:a&&!notes.length,notes}})}});document.getElementById('m').textContent=a&&notes.length?'notes found: saved as notes, not approved':'saved'}}
fetch('/state').then(r=>r.json()).then(j=>(j.notes||[]).forEach(n=>{{const t=document.querySelector(`textarea[data-s="${{n.scene}}"]`);if(t)t.value=n.text}}))</script>"""

def serve(v, port):
    v = Path(v); scenes = shorts.load(v)
    vid = next((p for p in (v / "package" / "video.mp4", v / "draft.mp4", v / "final.mp4") if p.exists()), None)
    if not vid: sys.exit("no package/video.mp4, draft.mp4 or final.mp4 in " + str(v))
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def send(self, code, body, ct, extra=()):
            self.send_response(code); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(body)))
            [self.send_header(*e) for e in extra]; self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            if self.path == "/": return self.send(200, page(v, scenes).encode(), "text/html; charset=utf-8")
            if self.path == "/state":
                f = v / "review.json"; return self.send(200, f.read_bytes() if f.exists() else b"{}", "application/json")
            if self.path == "/video":
                size = vid.stat().st_size; m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
                a, b = (int(m.group(1) or 0), int(m.group(2)) if m.group(2) else size - 1) if m else (0, size - 1)
                with open(vid, "rb") as f: f.seek(a); body = f.read(b - a + 1)
                return self.send(206 if m else 200, body, "video/mp4", [("Accept-Ranges", "bytes"), ("Content-Range", f"bytes {a}-{b}/{size}")])
            self.send(404, b"", "text/plain")
        def do_POST(self):
            if self.path != "/save": return self.send(404, b"", "text/plain")
            d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            (v / "review.json").write_text(json.dumps({"approved": bool(d.get("approved")) and not d.get("notes"), "notes": d.get("notes", [])}, ensure_ascii=False, indent=1)); self.send(200, b"ok", "text/plain")
    print(f"review page: http://127.0.0.1:{port}/   (Ctrl+C to stop; saves {v / 'review.json'})"); ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    serve(a[0], int(a[a.index("--port") + 1]) if "--port" in a else 8765)
