"""Debug: why does cordura_material render near-white? Four spheres, albedo 0.1 olive:
A plain Principled no sheen | B plain + Sheen Weight 0.35 | C cordura_material() as is | D cordura_material() with sheen 0.
blender -b --python proto_dbg_sheen.py -- [samples] [resx]
"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import proto_common as pc

SAMPLES, RESX = pc.argv()
pc.reset_scene(SAMPLES, RESX, resy=RESX // 4)
pc.world_hdri(0.6, rot_z=math.radians(90))
OLIVE = (0.115, 0.105, 0.062)
objs = []
mats = []
m, nodes, links, b = pc.base_material("A.plain"); b.inputs["Base Color"].default_value = (*OLIVE, 1); b.inputs["Roughness"].default_value = 0.72; mats.append(m)
m, nodes, links, b = pc.base_material("B.sheen035"); b.inputs["Base Color"].default_value = (*OLIVE, 1); b.inputs["Roughness"].default_value = 0.72
b.inputs["Sheen Weight"].default_value = 0.35; b.inputs["Sheen Roughness"].default_value = 0.6; mats.append(m)
mats.append(pc.cordura_material("C.cordura", OLIVE))
m = pc.cordura_material("D.cordura.nosheen", OLIVE); m.node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 0.0; mats.append(m)
for i, m in enumerate(mats):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=48, ring_count=24, location=(-0.105 + 0.07 * i, 0, 0))
    o = bpy.context.active_object; o.name = m.name; o.data.shade_smooth(); o.data.materials.append(m); objs.append(o)
pc.ground(-0.03)
pc.key_light((0, 0, 0), direction=(-0.6, -1, 0.9), dist=0.6, size=0.3)
pc.camera_fit(objs, direction=(0, -1, 0.15), margin=0.62, lens=60)
pc.render(os.path.join(pc.OUT_DIR, "proto_dbg_sheen.png"), "sheen debug")
