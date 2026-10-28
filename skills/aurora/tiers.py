#!/usr/bin/env python3
"""Cost ladder for aurora: which tier starts a task, and a ledger of what each tier did. stdlib only.
  tiers.py route <task>                              start tier + models for a task (honors preferences.json min_tier/free_tier and past results); never returns tier 3
  tiers.py log <video> <task> <tier> <model> <harness> <attempt> <pass|fail|stall> [secs] [tokens]   append to aurora/tiers.jsonl
  tiers.py report [video]                            per tier: cards, passes, failures, tokens, seconds; escalation count
  tiers.py tasks                                     the task catalog with start tier and acceptance gate
Tiers: 0 free (tether first, else opencode *-free) | 1 cheap (haiku) | 2 sonnet | 3 opus/fable: ONLY with the user's explicit OK, each time.
Models: aurora/tiers.json {"tiers": {"0": [...], ...}} else .claude/gru.json "tiers", else the defaults below (refresh them: `opencode models`, `tether_stats`)."""
import json, sys, time
from pathlib import Path

DEFAULT_MODELS = {"0": ["opencode/glm-5.3-flash-free", "opencode/deepseek-v4.1-flash-free"], "1": ["anthropic/claude-haiku-5-5"], "2": ["anthropic/claude-sonnet-5-5"], "3": ["opus/fable: ask the user first"]}
# task -> (start tier, acceptance gate the main chat runs before accepting; never trust the minion's "done")
CATALOG = {
    "split_feedback": (0, "output JSONL parses, each line has date/source/scope/area/text/status, text under 300 chars; main chat reads the lines"),
    "dedupe_themes": (0, "no theme in the output matches a line of aurora/topics.log or a draft_videos/ folder name"),
    "analytics_table": (0, "prefer a plain python script; totals in the table equal the source CSV totals"),
    "sources_md": (0, "every URL in sources.md appears in plan.json claims[].source_urls; none invented"),
    "shorts_texts": (0, "no < or >, titles <= 100 chars, at most 3 hashtags; main chat reads them"),
    "package_texts": (1, "slop_check.py package checks pass; main chat reads the 3 titles and the first 2 description lines for honesty"),
    "research": (1, "every URL was actually fetched (spot-check 2); no claim without a source; main chat picks"),
    "spec_json": (1, "valid against the template props; capture --draft renders without PAGE ERROR; one contact sheet looked at"),
    "thumbnails": (1, "slop_check.py thumbnail size/format checks pass; main chat looks at all 3 images"),
    "assembly_scripts": (1, "ffprobe: audio/video lengths match, about -16 LUFS, true peak <= -1.5 dBTP, no trailing silence"),
    "plan_json": (2, "slop_check.py claims checks pass; main chat spot-checks 3 claims against their sources"),
    "script": (2, "1400-1600 spoken words, persona voice, one core_point; main chat reads hook and ending in full"),
    "blender_hero": (2, "still frames first, then the full render; main chat looks at 4 frames and the physics"),
    "new_template": (2, "sample spec renders in draft; existing templates still render"),
}
ROOT_MARK = ("preferences.json", "aurora", "draft_videos")

def project():
    cwd = Path.cwd()
    return next((d for d in [cwd, *cwd.parents] if any((d / m).exists() for m in ROOT_MARK)), cwd)
def prefs(P):
    f = P / "preferences.json"
    try: return json.loads(f.read_text()) if f.exists() else {}
    except ValueError: return {}
def models(P):
    for f, key in ((P / "aurora" / "tiers.json", "tiers"), (P / ".claude" / "gru.json", "tiers")):
        try:
            if f.exists(): return {**DEFAULT_MODELS, **{str(k): v for k, v in json.loads(f.read_text()).get(key, {}).items()}}
        except ValueError: pass
    return DEFAULT_MODELS
def history(P):
    f = P / "aurora" / "tiers.jsonl"; out = []
    for line in (f.read_text().splitlines() if f.exists() else []):
        try: out.append(json.loads(line))
        except ValueError: pass
    return out

def route(task):
    P = project()
    if task not in CATALOG: sys.exit(f"unknown task '{task}'. Known: {', '.join(CATALOG)}. Unlisted work stays with the main chat or goes to tier 2.")
    tier, gate = CATALOG[task]; pf = prefs(P); why = []
    if pf.get("free_tier") is False and tier == 0: tier = 1; why.append("preferences free_tier=false")
    if pf.get("min_tier", 0) > tier: tier = pf["min_tier"]; why.append(f"preferences min_tier={tier}")
    h = [r for r in history(P) if r["task"] == task and r["tier"] == tier][-5:]
    fails, passes = sum(r["result"] != "pass" for r in h), sum(r["result"] == "pass" for r in h)
    if len(h) >= 2 and fails >= 2 and passes == 0: tier += 1; why.append(f"last {len(h)} tier-{tier - 1} runs of this task failed")
    if tier >= 3: print(json.dumps({"task": task, "tier": 3, "action": "ASK_USER", "why": why + ["tier 3 needs the user's explicit OK"]})); return
    print(json.dumps({"task": task, "tier": tier, "models": models(P)[str(tier)], "harness": "tether first, else opencode (sandboxed)" if tier == 0 else "native Agent with model override, or opencode/tether", "gate": gate, "why": why}, ensure_ascii=False))

def log(a):
    video, task, tier, model, harness, attempt, result = a[:7]
    if result not in ("pass", "fail", "stall"): sys.exit("result must be pass|fail|stall")
    P = project(); (P / "aurora").mkdir(exist_ok=True)
    row = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "video": video, "task": task, "tier": int(tier), "model": model, "harness": harness, "attempt": int(attempt), "result": result,
           "secs": float(a[7]) if len(a) > 7 else 0, "tokens": int(a[8]) if len(a) > 8 else 0}
    with open(P / "aurora" / "tiers.jsonl", "a") as f: f.write(json.dumps(row) + "\n")

def report(video=None):
    rows = [r for r in history(project()) if not video or r["video"] == video]
    if not rows: print("no tier runs logged"); return
    for t in range(4):
        r = [x for x in rows if x["tier"] == t]
        if r: print(f"tier {t}: {len(r):>3} runs, {sum(x['result'] == 'pass' for x in r):>3} pass, {sum(x['result'] != 'pass' for x in r):>3} fail/stall, {sum(x['tokens'] for x in r):>9,} tokens, {sum(x['secs'] for x in r) / 60:5.1f} min")
    esc = sum(1 for k in {(x["video"], x["task"]) for x in rows} if len({x["tier"] for x in rows if (x["video"], x["task"]) == k}) > 1)
    print(f"escalated tasks: {esc}")

def main(a):
    cmd = a[0] if a else ""
    if cmd == "route" and len(a) > 1: route(a[1])
    elif cmd == "log" and len(a) >= 8: log(a[1:])
    elif cmd == "report": report(a[1] if len(a) > 1 else None)
    elif cmd == "tasks":
        for k, (t, g) in CATALOG.items(): print(f"{k:<16} tier {t}  gate: {g}")
    else: print(__doc__)

main(sys.argv[1:])
