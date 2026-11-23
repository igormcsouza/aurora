"""Blender scenario engine: low-poly people acting out an idea in a built world (office, empty stage, or your own set).
  blender -b -P scenario.py -- <spec.json> still <sec> <out.png>
  blender -b -P scenario.py -- <spec.json> range <f0> <f1> <out_dir> [--draft]      (frames f_NNNN.png; scenario_render.py drives this in parallel)
Spec (all times in seconds, positions in metres, z up, camera-facing = -Y):
  duration, fps?, set: "office" | "stage" | "none", set_script?: path (python exec'd in this module; build your world with bx/cyl/sph/empty/C/light),
  sky?: {top, mid, bottom} hex, actors: {id: {sp, look:{shirt,skin,hair,pants,tie?,hairstyle: cap|long|bald|spiky,tall?}, path:[[t,x,y,"stand"|"sit"]], faces:[[t,[x,y]]], run?:[t0,t1]}},
  lines: [{sp, start, end, text?, words?:[{w,s,e}]}]  (words from kit/words.py; without words the text is spread evenly), or words_file + words_id (aurora scenes/words.json) + speaker,
  shots: [{t0, t1, from:[x,y,z], to:[x,y,z], target: "actor_id" | "actor_id.body" | [x,y,z], lens?}], labels?: [{text, at:[x,y,z], t0, t1, size?, color?}]
Actors lip-sync and gesture on the word clock of their own `sp` lines; they walk along `path` (a hop of more than 0.01 m over its time = walking)."""
import bpy, sys, os, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from lib import *

C = lambda h: tuple(((int(h.lstrip('#')[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4)) if isinstance(h, str) else tuple(h)
def cyl(loc, r, h, color, parent=None, rough=0.6, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts); o = bpy.context.object; bpy.ops.object.shade_smooth(); o.data.materials.append(mat(C(color), rough=rough))
    if parent: o.parent = parent; o.matrix_parent_inverse.identity()
    return o
def sph(loc, r, color, parent=None, scale=(1, 1, 1), rough=0.6, emit=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=20, ring_count=12); o = bpy.context.object; o.scale = scale; bpy.ops.object.shade_smooth(); o.data.materials.append(mat(C(color), emit=emit, rough=rough))
    if parent: o.parent = parent; o.matrix_parent_inverse.identity()
    return o
def bx(loc, size, color, rough=0.5, bevel=0.02, emit=0.0): return box(loc, size, C(color), bevel=bevel, rough=rough, coat=0.0, emit=emit)
def empty(loc=(0, 0, 0), parent=None):
    bpy.ops.object.empty_add(location=loc); o = bpy.context.object
    if parent: o.parent = parent; o.matrix_parent_inverse.identity()
    return o

# ---------------- sets ----------------
def set_stage():
    bx((0, 0, -0.05), (40, 40, 0.1), '#c9d3df', rough=0.7); light('SUN', (0, 0, 10), 3.0, rot=(math.radians(40), 0, math.radians(-30))); light('AREA', (0, -4, 6), 600, size=12)
def set_office():
    bx((0, 0, -0.05), (16, 11, 0.1), '#6d7a8c', rough=0.9); bx((11, 0, -0.06), (15, 24, 0.1), '#3a3d45', rough=0.95)
    for k in range(-4, 5): bx((10.5, k * 2.4, 0.0), (3.6, 0.12, 0.02), '#e8e8e8', rough=0.8)
    W = '#e9e2d3'
    bx((0, 5.1, 1.5), (14.2, 0.2, 3), W); bx((0, -5.1, 1.5), (14.2, 0.2, 3), W); bx((-7.1, 0, 1.5), (0.2, 10.2, 3), W)
    bx((7.1, -3.2, 1.5), (0.2, 3.6, 3), W); bx((7.1, 3.2, 1.5), (0.2, 3.6, 3), W); bx((7.1, 0, 2.55), (0.2, 2.8, 0.9), W)   # east wall, door gap at y=0
    for wx in (-4, 0, 4): bx((wx, 5.0, 1.7), (2.2, 0.1, 1.2), '#9cc9e8', rough=0.1, emit=0.6)
    bx((-7.0, 0, 2.7), (0.1, 10, 0.12), '#2b6cb0')
    def desk(x, y, side=1):
        bx((x, y, 0.72), (1.7, 0.8, 0.06), '#8b5e3c'); [bx((x + sx * 0.78, y + sy * 0.33, 0.36), (0.06, 0.06, 0.72), '#4a4a4a') for sx in (-1, 1) for sy in (-1, 1)]
        bx((x + 0.55, y, 0.98), (0.4, 0.05, 0.34), '#15151a', rough=0.2); bx((x + 0.55, y, 0.8), (0.1, 0.1, 0.1), '#333333'); bx((x, y - 0.15, 0.76), (0.45, 0.16, 0.03), '#222222')
        bx((x, y + side * 0.75, 0.45), (0.5, 0.5, 0.08), '#2d3748'); bx((x, y + side * 1.0, 0.78), (0.5, 0.08, 0.6), '#2d3748')
    desk(-3, 3.4); desk(1, 3.4); desk(4.5, 3.4); desk(-3, -3.4, -1)
    bx((-6.5, -3, 0.95), (0.9, 0.8, 1.9), '#c53030'); bx((-6.5, -1.2, 0.55), (0.45, 0.45, 1.1), '#dfe6ee'); sph((-6.5, -1.2, 1.25), 0.22, '#8ec9ff', rough=0.1)
    for px, py in ((-6.5, 4.3), (6.4, 4.3), (6.4, -4.4)): cyl((px, py, 0.25), 0.25, 0.5, '#8a4b2a'); sph((px, py, 0.85), 0.4, '#2f855a', scale=(1, 1, 1.3))
    bx((-1.5, -4.4, 0.5), (1.0, 0.7, 1.0), '#a0aec0'); bx((0, 0, 0.012), (5, 3.2, 0.02), '#4a5568', rough=0.95)
    bx((6.95, 0, 1.25), (0.08, 1.4, 2.5), '#3182ce', rough=0.4); bx((6.9, 0, 2.2), (0.06, 0.9, 0.22), '#38a169', emit=2.0)
    for lx, ly in ((-4, -2), (0, -2), (4, -2), (-4, 2), (0, 2), (4, 2)): bx((lx, ly, 2.95), (1.6, 0.5, 0.05), '#fffbe8', emit=2.0)
    light('SUN', (0, 0, 10), 2.0, color=(1, 0.95, 0.85), rot=(math.radians(35), 0, math.radians(-30))); light('AREA', (0, 0, 2.8), 350, color=(1, 0.96, 0.9), size=10); light('AREA', (11, 0, 5), 200, size=12)
    for cx, cy, col in ((10.5, 5.5, '#e53e3e'), (10.5, -6, '#2b6cb0'), (14, 2.4, '#d69e2e'), (14.2, -2.5, '#718096')):
        bx((cx, cy, 0.5), (1.8, 4.0, 0.7), col, rough=0.3, bevel=0.15); bx((cx, cy - 0.1, 1.05), (1.5, 2.0, 0.55), col, rough=0.3, bevel=0.15); bx((cx, cy - 0.1, 1.07), (1.52, 1.9, 0.4), '#9cc9e8', rough=0.05, bevel=0.1)
        for wx in (-0.85, 0.85):
            for wy in (-1.2, 1.2): cyl((cx + wx, cy + wy, 0.3), 0.3, 0.2, '#111111', rough=0.9).rotation_euler = (0, math.radians(90), 0)
SETS = {'office': set_office, 'stage': set_stage, 'none': lambda: None}

# ---------------- people ----------------
class P:
    """A low-poly person: torso, head, eyes, mouth (scaled for lip-sync), arm and leg pivots. Origin on the floor, faces -Y at rotation 0."""
    def __init__(s, name, shirt, skin, hair, pants, tie=None, tall=1.0, hairstyle='cap', sp=None):
        s.name, s.sp = name, sp; s.root = empty(); s.body = empty((0, 0, 0), s.root); s.root.scale = (tall,) * 3
        s.torso = cyl((0, 0, 1.12), 0.26, 0.62, shirt, s.body); s.torso.scale = (1, 0.7, 1)
        s.hips = cyl((0, 0, 0.82), 0.26, 0.14, pants, s.body); s.hips.scale = (1, 0.7, 1)
        s.head = empty((0, 0, 1.62), s.body); sph((0, 0, 0), 0.21, skin, s.head, scale=(1, 0.95, 1.08))
        if hairstyle == 'cap': sph((0, 0.03, 0.08), 0.215, hair, s.head, scale=(1, 0.95, 0.85))
        elif hairstyle == 'long': sph((0, 0.06, 0.04), 0.23, hair, s.head, scale=(1.02, 1.0, 1.0)); cyl((0, 0.17, -0.12), 0.2, 0.5, hair, s.head)
        elif hairstyle == 'spiky': sph((0, 0.03, 0.1), 0.22, hair, s.head, scale=(1, 0.95, 0.8)); [cyl((k * 0.08, 0.0, 0.26), 0.03, 0.12, hair, s.head) for k in (-1, 0, 1)]
        for k in (-1, 1): sph((k * 0.075, -0.18, 0.04), 0.03, '#111111', s.head)
        s.mouth = sph((0, -0.195, -0.08), 0.045, '#7a1f1f', s.head, scale=(1.6, 0.5, 0.2))
        if tie: t = bx((0, -0.18, 1.12), (0.07, 0.03, 0.4), tie); t.parent = s.body
        s.arms, s.legs = [], []
        for k in (-1, 1):
            sh = empty((k * 0.33, 0, 1.38), s.body); cyl((0, 0, -0.27), 0.065, 0.55, shirt, sh); sph((0, 0, -0.58), 0.07, skin, sh); s.arms.append(sh)
            hp = empty((k * 0.13, 0, 0.82), s.body); cyl((0, 0, -0.4), 0.09, 0.8, pants, hp); sph((0, -0.05, -0.82), 0.09, '#222222', hp, scale=(1, 1.5, 0.7)); s.legs.append(hp)

def seg(t, wp):
    """wp = [(t, x, y, mode)] -> (x, y, moving, speed m/s, mode). Eased between waypoints."""
    if t <= wp[0][0]: return wp[0][1], wp[0][2], 0, 0, wp[0][3]
    for a, b in zip(wp, wp[1:]):
        if t <= b[0]:
            u = (t - a[0]) / max(1e-6, b[0] - a[0]); d = math.hypot(b[1] - a[1], b[2] - a[2]); sp = d / max(1e-6, b[0] - a[0])
            if d < 0.01: return a[1], a[2], 0, 0, a[3] if u < 0.5 else b[3]
            u = u * u * (3 - 2 * u) * 0.35 + u * 0.65
            return a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, 1, sp, 'stand'
    return wp[-1][1], wp[-1][2], 0, 0, wp[-1][3]

def normalise_lines(S):
    """-> [{sp, start, end, words:[{w,s,e}]}]; words are even-spread from text when no alignment is given."""
    L = list(S.get('lines', []))
    if S.get('words_file'):
        W = json.load(open(S['words_file'])).get(str(S.get('words_id', '')), [])
        if W: L.append({'sp': S.get('speaker', 'N'), 'start': W[0]['s'], 'end': W[-1]['e'], 'words': W})
    for l in L:
        if not l.get('words'):
            ws = (l.get('text') or '').split(); tot = sum(len(w) + 1 for w in ws) or 1; t = l['start']; l['words'] = []
            for w in ws: d = (l['end'] - l['start']) * (len(w) + 1) / tot; l['words'].append({'w': w, 's': t, 'e': t + d * 0.85}); t += d
    return L

def animate(p, S, A, L):
    FPSN = int(S['duration'] * FPS); wp = [tuple(w) for w in A['path']]; faces = [(t, tuple(v)) for t, v in A.get('faces', [])]; run = A.get('run')
    mine = [l for l in L if l['sp'] == p.sp]
    speaking = lambda t: any(l['start'] - 0.05 <= t <= l['end'] + 0.1 and any(w['s'] - 0.03 <= t <= w['e'] + 0.03 for w in l['words']) for l in mine)
    active = lambda t: any(l['start'] <= t <= l['end'] for l in mine)
    phase = h = 0.0; lastp = None
    for fr in range(1, FPSN + 1):
        t = (fr - 1) / FPS; x, y, mv, spd, mode = seg(t, wp)
        if mv and lastp: dx, dy = x - lastp[0], y - lastp[1]; th = math.atan2(dx, -dy) if math.hypot(dx, dy) > 1e-4 else h
        else:
            ft = next((q for q in reversed(faces) if q[0] <= t), None); th = math.atan2(ft[1][0] - x, -(ft[1][1] - y)) if ft else h
        d = (th - h + math.pi) % (2 * math.pi) - math.pi; h += d * (0.35 if mv else 0.12); lastp = (x, y)
        if mv: phase += spd * 2.6 / FPS
        sit = mode == 'sit'; talk = speaking(t); act = active(t); fast = bool(run and run[0] <= t <= run[1] and mv)
        p.root.location = (x, y, -0.45 if sit else 0); p.root.rotation_euler = (0, 0, h)
        ph = math.sin(phase * 2 * math.pi) * ((0.75 if fast else 0.5) if mv else 0)
        for i, leg in enumerate(p.legs): leg.rotation_euler = (-math.radians(88) if sit else (ph if i else -ph), 0, 0)
        for i, arm in enumerate(p.arms):
            a = (-ph if i else ph) * 0.8 if mv else 0.0
            if act and not mv: a = (-0.9 + math.sin(t * 3.2 + i) * 0.45) if i == 1 else (-0.25 + math.sin(t * 2.1) * 0.15)
            elif sit and not act: a = -0.8
            arm.rotation_euler = (a, 0, (1 if i else -1) * 0.12)
        p.body.rotation_euler = (0.08 if fast else 0, 0, 0); p.head.rotation_euler = (math.sin(t * 2.3) * 0.04 + (0.08 if talk else 0), 0, math.sin(t * 1.7) * 0.08 if act else 0)
        p.mouth.scale = (1.6, 0.5, 0.2 + (0.9 * abs(math.sin(t * 2 * math.pi * 4.5)) if talk else 0))
        for o, paths in ((p.root, ('location', 'rotation_euler')), (p.body, ('rotation_euler',)), (p.head, ('rotation_euler',)), (p.mouth, ('scale',)), *[(l_, ('rotation_euler',)) for l_ in p.legs], *[(a_, ('rotation_euler',)) for a_ in p.arms]):
            for dp in paths: o.keyframe_insert(dp, frame=fr)
    for o in [p.root, p.body, p.head, p.mouth, *p.legs, *p.arms]:
        if o.animation_data:
            for fc in o.animation_data.action.fcurves:
                for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ---------------- build ----------------
argv = sys.argv[sys.argv.index('--') + 1:]; S = json.load(open(argv[0])); mode = argv[1]; draft = '--draft' in argv
DUR = S['duration']; W, H = (1280, 720) if draft else (1920, 1080)
sc = setup(DUR, W, H, samples=10 if draft else 20, exposure=S.get('exposure', -0.9)); sc.render.image_settings.file_format = 'PNG'; sc.eevee.use_motion_blur = False
sk = S.get('sky', {}); world(top=C(sk.get('top', '#5a9ef2')), mid=C(sk.get('mid', '#99c7f2')), bottom=C(sk.get('bottom', '#e5eef2')), strength=0.7)
SETS[S.get('set', 'stage')]()
if S.get('set_script'): exec(compile(open(S['set_script']).read(), S['set_script'], 'exec'), globals())
L = normalise_lines(S); actors = {}
for aid, A in S.get('actors', {}).items():
    lk = A.get('look', {}); p = P(aid, lk.get('shirt', '#2b6cb0'), lk.get('skin', '#e0ac88'), lk.get('hair', '#3b2a20'), lk.get('pants', '#2d3748'), lk.get('tie'), lk.get('tall', 1.0), lk.get('hairstyle', 'cap'), A.get('sp', aid))
    animate(p, S, A, L); actors[aid] = p
def target(t):
    if isinstance(t, str): a, _, part = t.partition('.'); return getattr(actors[a], 'body' if part == 'body' else 'head')
    return empty(tuple(t))
shots = []
for i, s in enumerate(S['shots']):
    bpy.ops.object.camera_add(location=s['from']); cam = bpy.context.object; cam.data.lens = s.get('lens', 35); cam.data.dof.use_dof = False
    c = cam.constraints.new('TRACK_TO'); c.target = target(s['target']); c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    cam.location = s['from']; cam.keyframe_insert('location', frame=f(s['t0'])); cam.location = s['to']; cam.keyframe_insert('location', frame=f(s['t1']))
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    m = sc.timeline_markers.new(f'c{i}', frame=f(s['t0'])); m.camera = cam; shots.append(s)
def cam_at(t):
    s = next((q for q in reversed(shots) if q['t0'] <= t), shots[0]); u = min(1, max(0, (t - s['t0']) / max(1e-6, s['t1'] - s['t0'])))
    return [a + (b - a) * u for a, b in zip(s['from'], s['to'])]
for lb in S.get('labels', []):      # 3D captions that always face the current camera, popping in/out
    o = text(lb['text'], tuple(lb['at']), lb.get('size', 0.3), C(lb.get('color', '#ff2d55')), emit=2.0); base = tuple(lb['at']); R = 0.4
    for fr in range(1, int(DUR * FPS) + 1):
        t = (fr - 1) / FPS; c = cam_at(t); on = lb['t0'] <= t <= lb['t1']; u = min(1, (t - lb['t0']) / 0.3, (lb['t1'] - t) / 0.3) if on else 0
        o.rotation_euler = (math.radians(90), 0, math.atan2(c[0] - base[0], -(c[1] - base[1]))); o.scale = (max(0.001, u),) * 3
        o.keyframe_insert('rotation_euler', frame=fr); o.keyframe_insert('scale', frame=fr)

if mode == 'still':
    sc.frame_set(f(float(argv[2]))); sc.render.filepath = argv[3]; bpy.ops.render.render(write_still=True)
elif mode == 'range':
    sc.frame_start, sc.frame_end = int(argv[2]), int(argv[3]); sc.render.filepath = argv[4].rstrip('/') + '/f_'; bpy.ops.render.render(animation=True)
