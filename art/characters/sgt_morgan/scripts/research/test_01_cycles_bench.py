"""Test 1: Cycles benchmark, headless.
Run: blender -b --python test_01_cycles_bench.py -- [samples list e.g. 32,128,512] [repeats]
Scene: subdivided UV sphere, Principled BSDF, 3 area lights, 1920x1080, OIDN denoise.
The device comes from scripts/lib/env.py (SGT_DEVICE, else the setup probe, else CPU); the cloud's
CPU figures are in notes/research_blender_capabilities.md §1.
"""
import bpy, sys, time, json, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import env  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
samples_list = [int(s) for s in (argv[0] if argv else "32,128,512").split(",")]
repeats = int(argv[1]) if len(argv) > 1 else 2
OUT = env.path("renders", "research")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
DEVICE = env.use_device(scene)
print(f"[BENCH] device={DEVICE}", flush=True)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
scene.cycles.use_adaptive_sampling = False  # fixed sample count for fair timing
scene.render.threads_mode = "AUTO"

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.05, 0.05, 0.06, 1)
bg.inputs[1].default_value = 1.0

# Sphere
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(0, 0, 1))
sph = bpy.context.active_object
bpy.ops.object.shade_smooth()
mod = sph.modifiers.new("Subd", "SUBSURF")
mod.levels = 3
mod.render_levels = 3
mat = bpy.data.materials.new("Principled")
mat.use_nodes = True
p = mat.node_tree.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value = (0.6, 0.35, 0.25, 1)
p.inputs["Roughness"].default_value = 0.35
p.inputs["Metallic"].default_value = 0.0
sph.data.materials.append(mat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.3, 0.3, 0.3, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
floor.data.materials.append(fm)

# Three-point area lights
def area(name, loc, rot, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_euler = rot
    scene.collection.objects.link(lo)
    return lo

import math
area("Key", (3, -3, 4), (math.radians(45), 0, math.radians(45)), 800, 2.0, (1, 0.95, 0.9))
area("Fill", (-4, -2, 2.5), (math.radians(65), 0, math.radians(-60)), 250, 3.0, (0.85, 0.9, 1))
area("Rim", (0, 4, 3.5), (math.radians(-50), 0, 0), 500, 1.0)

# Camera
cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 50
cam = bpy.data.objects.new("Cam", cam_d)
cam.location = (0, -5.5, 2.0)
cam.rotation_euler = (math.radians(80), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

results = {}
for s in samples_list:
    scene.cycles.samples = s
    times = []
    for r in range(repeats):
        scene.render.filepath = f"{OUT}/t01_cycles_{s}spp.png"
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        times.append(dt)
        print(f"[BENCH] samples={s} run={r} seconds={dt:.2f}", flush=True)
    results[s] = {"times": [round(t, 2) for t in times], "min": round(min(times), 2)}
results["device"] = DEVICE

print("[BENCH_JSON] " + json.dumps(results))
with open(f"{OUT}/t01_cycles_bench_{DEVICE.lower()}.json", "w") as f:
    json.dump(results, f, indent=1)
