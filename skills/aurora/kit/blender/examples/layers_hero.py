"""EXAMPLE content (Portuguese, a software topic): copy this file per video and replace every label, colour and timing with the video's own. Nothing here is a default.
Reference hero (20 s): a fat image tower is built, the useful slab is lifted out, the tower is tipped off, the slab lands on a small pedestal.
Copy and edit per video: labels, colours, timings. Sizes are illustrative."""
import sys, os, math
KIT = os.environ.get('AURORA_KIT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(KIT, 'blender')); from lib import *

D = 20
sc = setup(D)
sc.rigidbody_world is None and bpy.ops.rigidbody.world_add()
world(); floor()
light('SUN', (6, -8, 14), 3.2, (1.0, 0.85, 0.75), (math.radians(48), math.radians(8), math.radians(28)))
light('AREA', (-9, -6, 5), 2500, (1.0, 0.3, 0.8), (math.radians(80), 0, math.radians(-50)), 6)
light('AREA', (10, -5, 4), 2500, (0.2, 0.8, 1.0), (math.radians(80), 0, math.radians(60)), 6)

LAB = [("FROM node:20", (0.15, 0.7, 1.0)), ("apt install gcc make", (1.0, 0.25, 0.65)), ("npm ci  (node_modules)", (1.0, 0.75, 0.2)),
       ("COPY . .  (tests, docs)", (0.3, 0.9, 0.5)), ("npm run build", (0.6, 0.4, 1.0)), ("cache e temporários", (1.0, 0.5, 0.2))]
TX, PX = -3.8, 4.2
OFF = 60  # parking spot far off-screen: pieces wait there so they never overlap before release
plat = box((TX, 0, 0.15), (5.6, 2.8, 0.3), (0.2, 0.2, 0.35), 0.05, body='PASSIVE'); plat.rigid_body.kinematic = True
ped = box((PX, 0, 0.15), (3.8, 2.4, 0.3), (0.1, 0.5, 0.35), 0.05, body='PASSIVE')
slabs = []
for i, (lab, col) in enumerate(LAB):
    z_land = 0.3 + 0.28 + i * 0.58
    s = box((TX + OFF, 0, 5 + i), (4.8, 2.0, 0.55), col, 0.07, emit=0.25, body='ACTIVE', mass=2.0)
    text(lab, (0, -1.02, 0), 0.36, (0.05, 0.02, 0.22), 0.0, parent=s)
    t_drop = 4.5 + i * 0.9
    drop = (TX + (0.15 if i % 2 else -0.12), 0, z_land + 2.6); rot = (0, 0, math.radians(3 if i % 2 else -3)); dt = 1 / FPS
    key(s, 0, loc=(TX + OFF, 0, 5 + i), kinematic=True); key(s, t_drop - 5 * dt, loc=(TX + OFF, 0, 5 + i), kinematic=True)
    key(s, t_drop - 4 * dt, loc=drop, rot=rot, kinematic=True)   # jump into place a few frames BEFORE release: a sim body keeps its last position, and a jump right at release gives it a huge velocity
    key(s, t_drop, loc=drop, rot=rot, kinematic=False)
    for tt in (0, t_drop - 5 * dt, t_drop - 4 * dt, t_drop): hold(s, tt)
    smooth(s); slabs.append(s)
# the one worth keeping: copy of slab 4 in gold, lifted from the tower, lands on the pedestal
app = box((TX + OFF, 0, 12), (2.6, 1.4, 0.45), (1.0, 0.72, 0.1), 0.07, emit=1.0, body='ACTIVE', mass=1.0)
text("app", (0, -0.72, 0), 0.42, (0.15, 0.08, 0.0), 0.0, parent=app)
key(app, 0, loc=(TX + OFF, 0, 12), kinematic=True); key(app, 10.36, loc=(TX + OFF, 0, 12), kinematic=True); hold(app, 0); hold(app, 10.36)
key(app, 10.4, loc=(TX, 0, 5.2), kinematic=True)
for k in range(0, 9):
    u = k / 8; key(app, 10.6 + 1.6 * u, loc=(TX + (PX - TX) * u, 0, 5.2 + 2.6 * math.sin(math.pi * u) - 4.6 * u * u * 0.0 - 3.9 * u), rot=(0, math.radians(25) * math.sin(math.pi * u), 0), kinematic=True)
key(app, 12.3, loc=(PX, 0, 0.3 + 0.23 + 0.4), kinematic=True); key(app, 12.35, loc=(PX, 0, 0.3 + 0.23 + 0.4), kinematic=False); hold(app, 12.3); smooth(app)
# tilt the platform at 12.6 so the tower slides off, then retire the pieces
key(plat, 12.4, rot=(0, 0, 0), kinematic=True); key(plat, 13.6, rot=(0, math.radians(-38), 0), kinematic=True); smooth(plat)
for i, s in enumerate(slabs): hide(s, 15.6 + 0.08 * i, 1.0, 0.3)
hide(plat, 15.4, 1.0, 0.3)
# floating copy
t_hook = text("Sua imagem Docker\ntem 1 GB?", (0, 0, 7.4), 1.1, (1, 1, 1), 1.2, extrude=0.12)
key(t_hook, 0, scale=0.001); key(t_hook, 0.6, scale=1.15); key(t_hook, 1.0, scale=1.0); key(t_hook, 3.7, scale=1.0); key(t_hook, 4.2, scale=0.001); smooth(t_hook)
num = text("", (TX, -1.4, 6.6), 1.2, (1, 0.35, 0.4), 2.5, extrude=0.1); key(num, 0, scale=0.001); key(num, 4.5, scale=0.001); key(num, 4.9, scale=1.0)
def val(t):
    if t < 4.5: return ""
    v = 1100 * min(1.0, (t - 4.5) / 5.5) if t < 12.5 else max(90, 1100 - (t - 12.5) * 700)
    return f"{v/1000:.1f} GB" if v >= 1000 else f"{int(v)} MB"
counter_handler(num, val)
key(num, 14.0, loc=(TX, -1.4, 6.6)); key(num, 14.6, loc=(PX, -1.6, 3.8)); smooth(num)
t_ped = text("runtime", (PX, -1.3, 0.12), 0.26, (1, 1, 1), 2.0); pop(t_ped, 10.0)
t_pay = text("só o que importa", (PX - 1.0, -1.5, 5.8), 0.95, (1, 0.85, 0.3), 2.4, extrude=0.1); pop(t_pay, 16.3, 1.0, 0.6)
t_note = text("tamanhos ilustrativos", (0, -1.8, 0.35), 0.28, (1, 1, 1), 0.8); pop(t_note, 17.0)
burst((PX, -0.5, 2.0), 16.2)
camera([(0, (0, -17, 5), (0, 0, 4.5)), (4.0, (-5, -15, 5.5), (TX, 0, 2.5)), (9.0, (-10, -12.5, 5), (TX, 0, 2.8)), (11.0, (0, -18, 6), (0, 0, 3.0)),
        (13.5, (7, -14, 3.5), (1, 0, 1.2)), (16.5, (PX + 0.5, -10.5, 3.2), (PX, 0, 2.2)), (19.9, (PX, -9.5, 2.8), (PX, 0, 2.2))])
run(D)
