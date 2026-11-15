#!/usr/bin/env python3
"""Reads package/package.yml (what gets published) with a tiny YAML subset parser, stdlib only.
  pkgmeta.py show <video_dir>          print the parsed package
  pkgmeta.py choose <video_dir> <N>    record the approved title N (1-based): sets `chosen: N`, copies its thumbnail to
                                       package/thumbnail.png, moves the other thumbnails out to <video_dir>/thumbnails_unused/
  pkgmeta.py selftest

package.yml shape (quote strings that contain `: ` or ` #`; description is a `|` block, so hashtags and URLs are fine there):
  titles:                      # 5 options, each a different angle
    - text: "Title"
      angle: "why this one"
      thumbnail: thumbnail_1.png      # its rendered miniature, in package/
      thumbnail_text: "MAX 3 WORDS"
  chosen: 0                    # 1-5 once the user approved draft + title + thumbnail; 0 = not approved yet
  description: |
    plain paste-ready text
  tags: [a, b, c]              # or a block list
  pinned_comment: "question"
Subset: mappings, lists of scalars or of mappings, inline [a, b] lists, "double" and 'single' quoted strings, | block scalars, ints, true/false, # comments.
Legacy package.md (## Titles / ## Description / ## Tags) is still read, so published videos keep working.
"""
import csv, json, re, shutil, sys
from pathlib import Path

KEY = re.compile(r"^([A-Za-z_][\w-]*):(?:\s+(.*))?$")

def scalar(v):
    v = v.strip()
    if v[:1] == '"': return json.loads(v)
    if v[:1] == "'": return v[1:-1].replace("''", "'")
    if v[:1] == "[" and v[-1:] == "]":
        inner = v[1:-1].strip()
        return [scalar(x) for x in next(csv.reader([inner], skipinitialspace=True, quotechar='"'))] if inner else []
    v = re.split(r"\s#", v)[0].strip()
    if re.fullmatch(r"-?\d+", v): return int(v)
    return {"true": True, "false": False, "null": None, "~": None}.get(v, v)

def parse_yaml(text):
    L = text.expandtabs(2).splitlines(); pos = [0]
    ind = lambda s: len(s) - len(s.lstrip(" "))
    def skip():
        while pos[0] < len(L) and (not L[pos[0]].strip() or L[pos[0]].lstrip().startswith("#")): pos[0] += 1
    def val(v, base):
        v = v.strip()
        if v == "|":
            buf = []
            while pos[0] < len(L) and (not L[pos[0]].strip() or ind(L[pos[0]]) > base): buf.append(L[pos[0]]); pos[0] += 1
            used = [x for x in buf if x.strip()]; w = min(map(ind, used)) if used else 0
            return "\n".join(x[w:] for x in buf).strip("\n")
        if v == "" or v.startswith("#"):
            skip()
            return node(ind(L[pos[0]])) if pos[0] < len(L) and ind(L[pos[0]]) > base else None
        return scalar(v)
    def node(n):
        skip()
        if pos[0] >= len(L): return None
        if L[pos[0]].lstrip().startswith("- ") or L[pos[0]].strip() == "-":
            res = []
            while True:
                skip()
                if pos[0] >= len(L) or ind(L[pos[0]]) != n or not L[pos[0]].lstrip().startswith("-"): return res
                body = L[pos[0]].lstrip()[1:]; rest = body.lstrip(); off = n + 1 + len(body) - len(rest)
                if KEY.match(rest): L[pos[0]] = " " * off + rest; res.append(node(off))
                else: pos[0] += 1; res.append(val(rest, n))
        res = {}
        while True:
            skip()
            if pos[0] >= len(L) or ind(L[pos[0]]) != n: return res
            m = KEY.match(L[pos[0]].strip())
            if not m: raise ValueError(f"package.yml line {pos[0] + 1}: not 'key: value': {L[pos[0]].strip()[:60]!r} (quote strings that contain ': ')")
            pos[0] += 1; res[m.group(1)] = val(m.group(2) or "", n)
    out = node(0) if any(l.strip() and not l.lstrip().startswith("#") for l in L) else {}
    return out

def load(pkg_dir):
    """-> {titles:[{text,angle,thumbnail,thumbnail_text}], chosen:int, description:str, tags:[str], pinned_comment:str} or None if no package file."""
    pkg_dir = Path(pkg_dir); y = pkg_dir / "package.yml"; md = pkg_dir / "package.md"
    if y.exists():
        d = parse_yaml(y.read_text()) or {}
        titles = [t if isinstance(t, dict) else {"text": str(t)} for t in (d.get("titles") or [])]
        tags = d.get("tags") or []; tags = [x.strip() for x in re.split(r"[,\n]", tags) if x.strip()] if isinstance(tags, str) else [str(x) for x in tags]
        return {"titles": titles, "chosen": int(d.get("chosen") or 0), "description": (d.get("description") or "").strip(), "tags": tags,
                "pinned_comment": d.get("pinned_comment") or "", "source": "package.yml"}
    if md.exists():
        t = md.read_text(); sec = lambda n: (re.search(rf"## {n}\s*\n(.+?)(?=\n## |\Z)", t, re.S) or [None, ""])[1]
        titles = [{"text": re.sub(r"^\s*(\d+[.)]|[-*])\s*", "", l).strip()} for l in sec("Titles").splitlines() if l.strip()]
        return {"titles": titles, "chosen": 1 if titles else 0, "description": sec("Description").strip(),
                "tags": [x.strip() for x in re.split(r"[,\n]", sec("Tags")) if x.strip()], "pinned_comment": sec("Pinned comment").strip(), "source": "package.md"}
    return None

def choose(video_dir, n):
    v = Path(video_dir); pkg = v / "package"; y = pkg / "package.yml"
    m = load(pkg)
    if not m or m["source"] != "package.yml": sys.exit(f"{y} missing")
    if not 1 <= n <= len(m["titles"]): sys.exit(f"choose 1..{len(m['titles'])}")
    th = m["titles"][n - 1].get("thumbnail")
    if not th or not (pkg / th).exists(): sys.exit(f"title {n} has no thumbnail file in package/ ({th})")
    txt = y.read_text()
    txt = re.sub(r"(?m)^chosen:.*$", f"chosen: {n}", txt) if re.search(r"(?m)^chosen:", txt) else txt.rstrip("\n") + f"\nchosen: {n}\n"
    y.write_text(txt)
    if th != "thumbnail.png": shutil.copyfile(pkg / th, pkg / "thumbnail.png")
    spare = v / "thumbnails_unused"; spare.mkdir(exist_ok=True)
    for t in m["titles"]:
        f = t.get("thumbnail")
        if f and f != th and f != "thumbnail.png" and (pkg / f).exists(): shutil.move(str(pkg / f), str(spare / f))
    (pkg / th).unlink() if th != "thumbnail.png" else None
    print(f"chosen {n}: {m['titles'][n - 1]['text']}  (package/thumbnail.png set, others in {spare.name}/)")

def selftest():
    import tempfile
    y = '''# c
titles:
  - text: "Um: dois"
    angle: 'it''s'
    thumbnail: thumbnail_1.png
  - text: Plain title
    thumbnail: thumbnail_2.png
chosen: 0
description: |
  line one #hash

  https://x.y/z#a: b
tags: [a, "b c", d]
pinned_comment: "Q?"
flag: true
list:
  - 1
  - two
'''
    d = parse_yaml(y)
    assert d["titles"][0] == {"text": "Um: dois", "angle": "it's", "thumbnail": "thumbnail_1.png"}, d["titles"][0]
    assert d["titles"][1]["text"] == "Plain title" and d["chosen"] == 0 and d["flag"] is True and d["list"] == [1, "two"]
    assert d["description"] == "line one #hash\n\nhttps://x.y/z#a: b", repr(d["description"])
    assert d["tags"] == ["a", "b c", "d"] and d["pinned_comment"] == "Q?"
    with tempfile.TemporaryDirectory() as t:
        v = Path(t); (v / "package").mkdir(); (v / "package" / "package.yml").write_text(y)
        for i in (1, 2): (v / "package" / f"thumbnail_{i}.png").write_bytes(bytes([i]))
        m = load(v / "package"); assert len(m["titles"]) == 2 and m["tags"] == ["a", "b c", "d"] and m["chosen"] == 0
        choose(v, 2); m = load(v / "package")
        assert m["chosen"] == 2 and (v / "package" / "thumbnail.png").read_bytes() == b"\x02" and (v / "thumbnails_unused" / "thumbnail_1.png").exists()
        assert not (v / "package" / "thumbnail_2.png").exists()
        (v / "legacy").mkdir(); (v / "legacy" / "package.md").write_text("## Titles\n1. A\n2. B\n\n## Description\nd\n\n## Tags\nx, y\n")
        l = load(v / "legacy"); assert [x["text"] for x in l["titles"]] == ["A", "B"] and l["description"] == "d" and l["tags"] == ["x", "y"]
    print("pkgmeta selftest ok")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["show"]: print(json.dumps(load(Path(a[1]) / "package"), indent=2, ensure_ascii=False))
    elif a[:1] == ["choose"]: choose(a[1], int(a[2]))
    elif a[:1] == ["selftest"]: selftest()
    else: print(__doc__)
