"""Print world-space bounding boxes of every object and camera placement in a .blend.
Usage: blender -b <file.blend> --python mpfb_inspect_blend.py
"""
import bpy
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type == 'MESH':
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices):
            ws = [ev.matrix_world @ v.co for v in me.vertices]
            zs = [w.z for w in ws]; xs = [w.x for w in ws]; ys = [w.y for w in ws]
            print("%-32s verts=%6d  x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f] loc=%s parent=%s" % (
                o.name, len(me.vertices), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
                tuple(round(c, 3) for c in o.location), o.parent.name if o.parent else None))
        ev.to_mesh_clear()
    else:
        print("%-32s type=%s loc=%s rot=%s" % (o.name, o.type, tuple(round(c, 3) for c in o.location),
                                              tuple(round(c, 2) for c in o.rotation_euler)))
    if o.type == 'MESH':
        print("    modifiers:", [(m.name, m.type, m.show_viewport, m.show_render) for m in o.modifiers])
        print("    shapekeys:", len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0)
