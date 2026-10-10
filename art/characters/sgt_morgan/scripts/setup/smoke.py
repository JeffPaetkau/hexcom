"""Smoke test for a fresh setup (spec 18 §4.2.2 step 9): MPFB builds a human, Workbench and Cycles
render it, and the timings are printed and written beside the picture.

  blender -b --python-exit-code 1 --python scripts/setup/smoke.py -- --out cache/stamps/smoke.png

Runs with the project's user resources (BLENDER_USER_RESOURCES=cache/blender_user), where setup
installed MPFB. Cycles uses the device from lib/env.py (SGT_DEVICE or the setup probe).
"""
import argparse
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import env  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="cache/stamps/smoke.png")
ap.add_argument("--size", type=int, default=480)
ap.add_argument("--spp", type=int, default=32)
a = ap.parse_args(argv)
out = os.path.normpath(os.path.join(env.PROJECT_DIR, a.out))
os.makedirs(os.path.dirname(out), exist_ok=True)
times = {}
t = time.time()


def lap(name):
    global t
    times[name] = round(time.time() - t, 2)
    print(f"[smoke] {name}: {times[name]} s", flush=True)
    t = time.time()


bpy.ops.wm.read_factory_settings(use_empty=True)
mod = "bl_ext.user_default.mpfb"
if mod not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=mod)
from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
lap("mpfb enable")

human = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                  feet_on_ground=True, scale=0.1)
human.name = "Smoke.Human"
lap("mpfb create_human")
deps = bpy.context.evaluated_depsgraph_get()
zs = [(human.matrix_world @ v.co).z for v in human.evaluated_get(deps).data.vertices]
height = max(zs) - min(zs)

scene = bpy.context.scene
cam = bpy.data.objects.new("Smoke.Camera", bpy.data.cameras.new("Smoke.Camera"))
scene.collection.objects.link(cam)
cam.data.lens = 50
cam.location = Vector((0.0, -5.2, 1.0))
cam.rotation_euler = (math.radians(90), 0.0, 0.0)
scene.camera = cam
light = bpy.data.objects.new("Smoke.Key", bpy.data.lights.new("Smoke.Key", "AREA"))
light.data.energy, light.data.size = 600.0, 1.5
light.location = (1.5, -2.5, 2.5)
light.rotation_euler = (math.radians(50), 0.0, math.radians(30))
scene.collection.objects.link(light)
world = bpy.data.worlds.new("Smoke.World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 0.3
scene.world = world
scene.render.resolution_x = scene.render.resolution_y = a.size
scene.render.image_settings.file_format = "PNG"

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "MATCAP"
scene.display.shading.show_cavity = True
scene.render.filepath = out.replace(".png", "_workbench.png")
bpy.ops.render.render(write_still=True)
lap("workbench render")

scene.render.engine = "CYCLES"
dev = env.use_device(scene)
scene.cycles.samples = a.spp
scene.cycles.use_denoising = True
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
lap(f"cycles render ({dev}, {a.spp} spp, {a.size} px)")

report = {"blender": bpy.app.version_string, "device": dev, "human_height_m": round(height, 3),
          "seconds": times, "out": out}
with open(out.replace(".png", ".json"), "w", newline="\n") as f:
    json.dump(report, f, indent=1)
print("[smoke] " + json.dumps(report), flush=True)
