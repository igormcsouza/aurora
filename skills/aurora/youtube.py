#!/usr/bin/env python3
"""YouTube bridge for Aurora: private upload + analytics pull. stdlib only.
  youtube.py auth                        one-time browser login; prints the channel it got access to
  youtube.py upload <video_dir> [--title N] [--category 22] [--synthetic yes|no] [--yes]
                                         upload package/ as PRIVATE (dry run without --yes), set thumbnail, fill published.json
  youtube.py pull                        analytics for every published video with a youtube_id -> aurora/analytics/<date>.json
  youtube.py selftest                    offline checks
Files: ~/.config/aurora/client_secret.json (Desktop OAuth client, from Google Cloud) and youtube_token.json (written by `auth`, mode 600).
Uploads are always private: unaudited API projects are forced private by YouTube anyway, and going public is the user's click in Studio.
Captions are not uploaded (captions.insert is costly; paste package/subtitles.srt in Studio).
"""
import base64, hashlib, http.client, http.server, json, os, re, secrets, sys, time, urllib.error, urllib.parse, urllib.request, webbrowser
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent)); import pkgmeta

CONF = Path(os.environ.get("AURORA_CONFIG", Path.home() / ".config" / "aurora"))
CLIENT, TOKEN = CONF / "client_secret.json", CONF / "youtube_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]
CHUNK = 8 * 1024 * 1024  # multiple of 256 KiB, as the resumable protocol requires

def die(msg): sys.exit(f"youtube.py: {msg}")

# ---------- auth ----------
def client():
    if not CLIENT.exists(): die(f"{CLIENT} missing: download the Desktop OAuth client JSON from Google Cloud and put it there (chmod 600)")
    j = json.loads(CLIENT.read_text()); return j.get("installed") or j.get("web") or die("client_secret.json: no 'installed' client (create a Desktop app client)")

def post_form(url, data):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, urllib.parse.urlencode(data).encode()), timeout=30) as r: return json.load(r)
    except urllib.error.HTTPError as e: return {"error": e.read().decode(errors="replace")}

def save_token(t):
    fd = os.open(TOKEN, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f: json.dump(t, f)
    os.chmod(TOKEN, 0o600)

def pkce():
    v = secrets.token_urlsafe(64)
    return v, base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()

def cmd_auth():
    c = client(); CONF.mkdir(parents=True, exist_ok=True)
    verifier, challenge = pkce(); state = secrets.token_urlsafe(16); got = {}
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.update({k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()})
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
            self.wfile.write(b"Aurora: login done, you can close this tab.")
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H); redirect = f"http://127.0.0.1:{srv.server_port}"
    url = c["auth_uri"] + "?" + urllib.parse.urlencode({"client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    print("Open this URL (trying to open it for you; pick the account that OWNS the channel):\n" + url); webbrowser.open(url)
    srv.timeout = 300
    while not got: srv.handle_request()
    if got.get("state") != state or "code" not in got: die(f"login failed: {got}")
    t = post_form(c["token_uri"], {"code": got["code"], "client_id": c["client_id"], "client_secret": c.get("client_secret", ""),
        "redirect_uri": redirect, "grant_type": "authorization_code", "code_verifier": verifier})
    if "refresh_token" not in t: die(f"no refresh token: {t}")
    t["expires_at"] = time.time() + t.get("expires_in", 3600) - 60; save_token(t)
    ch = api("GET", "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true")
    items = ch.get("items") or []
    print("Logged in. Channel:", items[0]["snippet"]["title"] if items else "NONE (this account has no channel: re-run with the channel owner)")
    print("If the consent screen is in 'Testing', this token dies in 7 days: re-run `auth` then.")

def access_token():
    if not TOKEN.exists(): die("not logged in: run `youtube.py auth`")
    t = json.loads(TOKEN.read_text())
    if t.get("expires_at", 0) > time.time(): return t["access_token"]
    c = client(); n = post_form(c["token_uri"], {"client_id": c["client_id"], "client_secret": c.get("client_secret", ""),
        "refresh_token": t["refresh_token"], "grant_type": "refresh_token"})
    if "access_token" not in n: die(f"refresh failed (Testing-mode tokens expire after 7 days): run `youtube.py auth` again. {n}")
    t.update(n, expires_at=time.time() + n.get("expires_in", 3600) - 60); save_token(t); return t["access_token"]

def api(method, url, body=None, raw=None, ctype=None):
    h = {"Authorization": "Bearer " + access_token()}
    data = raw
    if body is not None: data, h["Content-Type"] = json.dumps(body).encode(), "application/json"
    if ctype: h["Content-Type"] = ctype
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, h, method=method), timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: raise RuntimeError(f"{e.code} {url.split('?')[0]}: {e.read().decode(errors='replace')[:400]}")

def find_project(start=None):
    for d in [Path(start or Path.cwd()).resolve(), *Path(start or Path.cwd()).resolve().parents]:
        if (d / "published_videos").is_dir() or (d / "draft_videos").is_dir(): return d
    return Path.cwd()

# ---------- upload ----------
def resumable_put(loc, path):
    size = path.stat().st_size; u = urllib.parse.urlparse(loc); off = 0; fails = 0
    with open(path, "rb") as f:
        while True:
            f.seek(off); chunk = f.read(CHUNK); end = off + len(chunk) - 1
            try:
                conn = http.client.HTTPSConnection(u.netloc, timeout=120)
                conn.request("PUT", u.path + "?" + u.query, chunk, {"Content-Length": str(len(chunk)), "Content-Range": f"bytes {off}-{end}/{size}"})
                r = conn.getresponse(); body = r.read()
            except OSError: r = None
            if r and r.status in (200, 201): return json.loads(body)
            if r and r.status == 308:
                rng = r.getheader("Range"); off = int(rng.split("-")[1]) + 1 if rng else 0; fails = 0
                print(f"  {off * 100 // size}%", end="\r", flush=True); continue
            fails += 1
            if fails > 5 or (r and r.status < 500 and r.status != 429): die(f"upload failed: {r.status if r else 'connection'} {body[:300] if r else ''}")
            time.sleep(2 ** fails)
            try:  # ask the server how far it got
                conn = http.client.HTTPSConnection(u.netloc, timeout=60)
                conn.request("PUT", u.path + "?" + u.query, b"", {"Content-Length": "0", "Content-Range": f"bytes */{size}"})
                q = conn.getresponse(); q.read(); rng = q.getheader("Range"); off = int(rng.split("-")[1]) + 1 if rng else 0
            except OSError: pass

def cmd_upload(args):
    yes = "--yes" in args; opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in ("--title", "--category", "--synthetic"))]
    if not pos: die("upload <video_dir>")
    v = Path(pos[0]).resolve(); mp4 = v / "package" / "video.mp4"
    m = pkgmeta.load(v / "package") or die(f"{v}/package/package.yml missing: run the package step first")
    mp4.exists() or die(f"{mp4} missing: run the package step first")
    titles, desc, tags = [t["text"] for t in m["titles"]], m["description"], m["tags"]
    n = int(opt("--title", m["chosen"]))
    if n == 0: die("no title approved yet: the user approves draft + title + thumbnail first (pkgmeta.py choose <video_dir> N), or pass --title N")
    if not 1 <= n <= len(titles): die(f"--title {n}: package has {len(titles)} titles")
    title = titles[n - 1]; thumb = v / "package" / (m["titles"][n - 1].get("thumbnail") or "thumbnail.png")
    if m["chosen"] == n and (v / "package" / "thumbnail.png").exists(): thumb = v / "package" / "thumbnail.png"
    if not desc or len(title) > 100 or len(desc.encode()) > 5000 or re.search(r"[<>]", title + desc + ",".join(tags)): die("package.yml breaks YouTube limits: run slop_check.py first")
    pj = v / "published.json"; meta = json.loads(pj.read_text()) if pj.exists() else {}
    if meta.get("youtube_id"): die(f"already uploaded as {meta['youtube_id']} (published.json); delete the key to force")
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if opt("--synthetic"): status["containsSyntheticMedia"] = opt("--synthetic") == "yes"
    body = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": opt("--category", "22")}, "status": status}
    print(f"{'UPLOAD' if yes else 'DRY RUN'} PRIVATE: {mp4} ({mp4.stat().st_size // 2**20} MB)\n  title: {title}\n  tags: {len(tags)}  description: {len(desc)} chars  thumbnail: {thumb.exists()}  status: {status}")
    if not yes: return print("Re-run with --yes to upload.")
    tok = access_token()
    conn = http.client.HTTPSConnection("www.googleapis.com", timeout=60)
    conn.request("POST", "/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", json.dumps(body).encode(),
        {"Authorization": "Bearer " + tok, "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(mp4.stat().st_size)})
    r = conn.getresponse(); b = r.read()
    if r.status != 200: die(f"could not start upload: {r.status} {b[:400]}")
    res = resumable_put(r.getheader("Location"), mp4); vid = res["id"]
    meta.update(slug=meta.get("slug", v.name), youtube_id=vid, url=f"https://youtu.be/{vid}", title=title, uploaded=date.today().isoformat(),
                privacy=res.get("status", {}).get("privacyStatus", "private"), title_option=n)
    pj.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\nUploaded: {meta['url']}  (privacy: {meta['privacy']}; published.json updated)")
    if thumb.exists():
        try: api("POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", raw=thumb.read_bytes(), ctype="image/png"); print("Thumbnail set.")
        except RuntimeError as e: print("Thumbnail NOT set (custom thumbnails need a phone-verified channel):", e)
    print("Next: set visibility in Studio, paste package/subtitles.srt, then `/aurora publish <slug>`.")

# ---------- analytics ----------
def scene_bounds(durs):
    """[(scene_id, start, end)] from durations.json: dict {id: sec}, list of sec, or list of {id, duration}."""
    items = list(durs.items()) if isinstance(durs, dict) else [(x.get("id", i + 1), x.get("duration", x.get("seconds", 0))) if isinstance(x, dict) else (i + 1, x) for i, x in enumerate(durs)]
    out, t = [], 0.0
    for sid, d in items: out.append((sid, t, t + float(d))); t += float(d)
    return out

def drops(curve, total, bounds, top=3):
    """curve = [(elapsedVideoTimeRatio, audienceWatchRatio)] -> the biggest falls between neighbouring points, mapped to scenes."""
    curve = sorted(curve); res = []
    for (r0, w0), (r1, w1) in zip(curve, curve[1:]):
        t = r1 * total
        res.append({"t": round(t, 1), "drop": round(w0 - w1, 4), "scene": next((s for s, a, b in bounds if a <= t < b), None)})
    return sorted(res, key=lambda x: -x["drop"])[:top]

def q(**kw):
    kw = {"ids": "channel==MINE", **kw}
    return api("GET", "https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(kw))

def rows(r): return [dict(zip([h["name"] for h in r["columnHeaders"]], row)) for row in r.get("rows", [])]

def cmd_pull():
    root = find_project(); out = {"pulled": date.today().isoformat(), "videos": {}}
    for pj in sorted((root / "published_videos").glob("*/published.json")):
        m = json.loads(pj.read_text()); vid = m.get("youtube_id")
        if not vid: print(f"skip {pj.parent.name}: no youtube_id"); continue
        start = m.get("date") or m.get("uploaded") or "2005-04-23"; f = dict(startDate=start, endDate=date.today().isoformat(), filters=f"video=={vid}"); v = {"title": m.get("title"), "slug": pj.parent.name}
        try:
            v["totals"] = (rows(q(metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares", **f)) or [{}])[0]
            v["traffic"] = rows(q(metrics="views,estimatedMinutesWatched", dimensions="insightTrafficSourceType", sort="-views", **f))
            curve = rows(q(metrics="audienceWatchRatio,relativeRetentionPerformance", dimensions="elapsedVideoTimeRatio", **f)); v["retention"] = curve
            dj = pj.parent / "scenes" / "durations.json"
            b = scene_bounds(json.loads(dj.read_text())) if dj.exists() else []
            tot = b[-1][2] if b else (v["totals"].get("averageViewDuration", 0) / max(v["totals"].get("averageViewPercentage", 0), 1) * 100)
            v["biggest_drops"] = drops([(c["elapsedVideoTimeRatio"], c["audienceWatchRatio"]) for c in curve], tot, b)
        except RuntimeError as e: v["error"] = str(e)
        out["videos"][vid] = v; print(f"{pj.parent.name}: {'ERROR ' + v['error'][:120] if 'error' in v else v['totals'].get('views', 0)} views")
    d = root / "aurora" / "analytics"; d.mkdir(parents=True, exist_ok=True); f = d / f"{date.today().isoformat()}.json"
    f.write_text(json.dumps(out, indent=2, ensure_ascii=False)); print(f"Wrote {f}  (CTR/impressions are not in this API: use the Studio CSV for those)")

# ---------- selftest ----------
def selftest():
    pkgmeta.selftest()
    b = scene_bounds({"01": 10, "02": 20}); assert b == [("01", 0, 10.0), ("02", 10.0, 30.0)], b
    assert scene_bounds([5, 5]) == [(1, 0, 5.0), (2, 5.0, 10.0)] and scene_bounds([{"id": "a", "duration": 4}])[0] == ("a", 0, 4.0)
    dr = drops([(0, 1.0), (0.25, 0.9), (0.5, 0.4), (1.0, 0.3)], 30, b); assert dr[0] == {"t": 15.0, "drop": 0.5, "scene": "02"}, dr
    v, c = pkce(); assert base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode() == c
    assert rows({"columnHeaders": [{"name": "a"}, {"name": "b"}], "rows": [[1, 2]]}) == [{"a": 1, "b": 2}]
    print("selftest ok")

if __name__ == "__main__":
    a = sys.argv[1:]
    {"auth": lambda: cmd_auth(), "upload": lambda: cmd_upload(a[1:]), "pull": lambda: cmd_pull(), "selftest": selftest}.get(a[0] if a else "", lambda: print(__doc__))()
