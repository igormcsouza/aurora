"""Blender helpers for aurora hero scenes (Blender 4.0, headless, Eevee). Import from a scene script:
    import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from lib import *
Run:  blender -b -P scene.py -- anim <out_dir> [<fps_scale>]     (video)
      blender -b -P scene.py -- still <frame> <out.png>          (one frame; bakes physics first)
Everything is code: no GUI, no assets. Colours are linear RGB tuples. Time helpers take seconds."""
import bpy, math, sys
from mathutils import Vector

FPS = 30
def f(sec): return int(round(sec * FPS)) + 1

def setup(duration, w=1920, h=1080, samples=24, exposure=-0.8):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps, sc.frame_start, sc.frame_end = FPS, 1, f(duration) - 1
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.engine = 'BLENDER_EEVEE'
    e = sc.eevee
    e.taa_render_samples = samples; e.use_bloom = True; e.bloom_intensity = 0.1; e.bloom_threshold = 1.3
    e.use_gtao = True; e.use_ssr = True; e.use_ssr_refraction = False; e.use_soft_shadows = True
    e.use_motion_blur = True; e.motion_blur_shutter = 0.35
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = exposure
    r = sc.render.image_settings; r.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'; sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    return sc

def mat(color, emit=0.0, rough=0.3, metal=0.0, coat=0.0):
    m = bpy.data.materials.new("m"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color[:3], 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*color[:3], 1); b.inputs["Emission Strength"].default_value = emit
    return m

def world(top=(0.06, 0.04, 0.42), mid=(0.5, 0.12, 0.65), bottom=(1.0, 0.32, 0.42), strength=0.9):
    """Sky gradient: `bottom` at the horizon, `mid`, then `top` going up. Never black."""
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]
    tc, sep, mr, ramp = (nt.nodes.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeSeparateXYZ", "ShaderNodeMapRange", "ShaderNodeValToRGB"))
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.5, 0.8; mr.clamp = True
    nt.links.new(mr.outputs["Result"], ramp.inputs[0])
    cr = ramp.color_ramp; cr.elements[0].position, cr.elements[1].position = 0.0, 1.0
    cr.elements[0].color = (*bottom, 1); cr.elements[1].color = (*top, 1)
    cr.elements.new(0.5).color = (*mid, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = strength

def floor(color=(0.05, 0.03, 0.18), rough=0.12, size=120, passive=True):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0)); o = bpy.context.object
    o.data.materials.append(mat(color, rough=rough, metal=0.0, coat=1.0))
    if passive: bpy.ops.rigidbody.object_add(type='PASSIVE'); o.rigid_body.friction = 0.8
    return o

def light(kind, loc, energy, color=(1, 1, 1), rot=(0, 0, 0), size=4):
    bpy.ops.object.light_add(type=kind, location=loc, rotation=rot); o = bpy.context.object
    o.data.energy = energy; o.data.color = color
    if kind == 'AREA': o.data.size = size
    return o

def box(loc, size, color, bevel=0.06, emit=0.0, rough=0.25, coat=0.6, body='NONE', mass=1.0):
    """size = full extents (x, y, z). body: NONE | ACTIVE | PASSIVE."""
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2); bpy.ops.object.transform_apply(location=False, scale=True)
    bv = o.modifiers.new("b", 'BEVEL'); bv.width = bevel; bv.segments = 4; bv.limit_method = 'NONE'
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat(color, emit, rough, coat=coat))
    if body != 'NONE':
        bpy.ops.rigidbody.object_add(type=body); rb = o.rigid_body
        rb.collision_shape = 'BOX'; rb.mass = mass; rb.friction = 0.7; rb.restitution = 0.15
    return o

_FONT = None
def text(s, loc, size, color=(1, 1, 1), emit=2.0, extrude=0.03, parent=None, align='CENTER'):
    """Text facing -Y (toward the default camera). Parent keeps local offset."""
    global _FONT
    if _FONT is None: _FONT = bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0)); o = bpy.context.object
    o.data.body = s; o.data.font = _FONT; o.data.size = size; o.data.extrude = extrude; o.data.align_x = align
    o.data.materials.append(mat(color, emit, 0.5))
    if parent: o.parent = parent; o.matrix_parent_inverse.identity()   # loc is LOCAL to the parent
    return o

def key(o, sec, loc=None, scale=None, rot=None, kinematic=None):
    fr = f(sec)
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=fr)
    if scale is not None: o.scale = scale if hasattr(scale, '__len__') else (scale,) * 3; o.keyframe_insert("scale", frame=fr)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=fr)
    if kinematic is not None: o.rigid_body.kinematic = kinematic; o.keyframe_insert("rigid_body.kinematic", frame=fr)

def hold(o, sec):
    """Make the keys at `sec` constant: the object stays put until the next key, then jumps (use to park off-screen)."""
    fr = f(sec)
    for fc in (o.animation_data.action.fcurves if o.animation_data and o.animation_data.action else []):
        for k in fc.keyframe_points:
            if int(k.co[0]) == fr: k.interpolation = 'CONSTANT'

def smooth(o):
    ad = o.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path.startswith("rigid_body"): 
                for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
                continue
            for k in fc.keyframe_points:
                if k.interpolation == 'CONSTANT': continue
                k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'

def pop(o, t0, s=1.0, dur=0.45):
    key(o, t0, scale=0.001); key(o, t0 + dur * 0.6, scale=s * 1.18); key(o, t0 + dur, scale=s); smooth(o)

def hide(o, t, s=1.0, dur=0.3):
    key(o, t, scale=s); key(o, t + dur, scale=0.001); smooth(o)

def camera(path, lens=35, fstop=2.8):
    """path = [(sec, (cam_x,y,z), (target_x,y,z)), ...] eased. Returns (cam, target)."""
    bpy.ops.object.empty_add(location=path[0][2]); tgt = bpy.context.object
    bpy.ops.object.camera_add(location=path[0][1]); cam = bpy.context.object; bpy.context.scene.camera = cam
    cam.data.lens = lens; cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = fstop
    c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    for t, cl, tl in path: key(cam, t, loc=cl); key(tgt, t, loc=tl)
    smooth(cam); smooth(tgt); return cam, tgt

def burst(origin, t0, n=60, colors=((1, .8, .2), (.2, .9, .6), (1, .3, .6), (.3, .8, 1)), spread=7.0, up=9.0, life=2.2, size=0.16):
    """Confetti on keyed ballistic paths (deterministic)."""
    import random; rnd = random.Random(3)
    for i in range(n):
        o = box(origin, (size, size, size * 0.3), colors[i % len(colors)], 0.01, emit=1.5)
        a = rnd.random() * 6.283; v = rnd.random() * spread; vz = up * (0.5 + rnd.random() * 0.6)
        key(o, t0 - 0.01, scale=0.001); key(o, t0, scale=1.0)
        for k in range(0, 13):
            u = life * k / 12
            key(o, t0 + u, loc=(origin[0] + math.cos(a) * v * u * .5, origin[1] + math.sin(a) * v * u * .5, max(0.1, origin[2] + vz * u - 4.9 * u * u)),
                rot=(u * 6 * (i % 3 + 1), u * 4, u * 5))
        key(o, t0 + life, scale=1.0); key(o, t0 + life + 0.3, scale=0.001)
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

def counter_handler(obj, fn):
    """fn(frame_seconds) -> str, applied to a text object before every frame."""
    def h(scene, *_): obj.data.body = fn((scene.frame_current - 1) / FPS)
    bpy.app.handlers.frame_change_pre.append(h); return h

def run(duration):
    """CLI: see module docstring. Call at the end of a scene script."""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['anim', '/tmp/aurora_blender']
    sc = bpy.context.scene
    if '--draft' in sys.argv: sc.render.resolution_percentage = 50; sc.eevee.taa_render_samples = 8; sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    if sc.rigidbody_world: 
        sc.rigidbody_world.substeps_per_frame = 20; sc.rigidbody_world.solver_iterations = 20
        sc.rigidbody_world.point_cache.frame_start, sc.rigidbody_world.point_cache.frame_end = 1, sc.frame_end
    if argv[0] == 'still':
        sc.frame_set(1)
        if sc.rigidbody_world: bpy.ops.ptcache.bake_all(bake=True)
        sc.frame_set(int(argv[1])); sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = argv[2]
        bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = argv[1].rstrip('/') + '/hero_'; sc.frame_set(1)
        if sc.rigidbody_world: bpy.ops.ptcache.bake_all(bake=True)   # unbaked physics diverges from stills in animation renders
        bpy.ops.render.render(animation=True)
