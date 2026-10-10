"""Sheen weight vs apparent brightness on a dark textile albedo (Blender 4.5 Principled). Scene-linear read-back."""
import bpy, sys, os, numpy as np, math
out = sys.argv[sys.argv.index("--")+1]
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 48
sc.render.threads_mode = "FIXED"; sc.render.threads = 3
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 720, 260
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Base Contrast"
w = bpy.data.worlds.new("W"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1); sc.world = w
base = (0.040, 0.035, 0.027)
weights = [0.0, 0.04, 0.08, 0.12, 0.20, 0.35]
for row, tint in enumerate(["white", "base130"]):
    for i, sw in enumerate(weights):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=64, ring_count=32, location=(-0.6 + i*0.24, 0, 0.12 - row*0.24))
        ob = bpy.context.active_object; bpy.ops.object.shade_smooth()
        m = bpy.data.materials.new(f"S{row}{i}"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*base, 1); p.inputs["Roughness"].default_value = 0.78
        p.inputs["Specular IOR Level"].default_value = 0.35
        p.inputs["Sheen Weight"].default_value = sw; p.inputs["Sheen Roughness"].default_value = 0.5
        p.inputs["Sheen Tint"].default_value = (1, 1, 1, 1) if tint == "white" else (min(1, base[0]*1.3*10), min(1, base[1]*1.3*10), min(1, base[2]*1.3*10), 1)
        ob.data.materials.append(m)
bpy.ops.object.light_add(type="AREA", location=(-1.2, -1.6, 1.4)); L = bpy.context.active_object
L.data.size = 1.0; L.data.energy = 0.0
d = -L.location.normalized(); L.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add(location=(0, -3.2, 0)); cam = bpy.context.active_object; cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5; sc.camera = cam
sc.render.image_settings.file_format = "OPEN_EXR"; sc.render.filepath = os.path.join(out, "sheen_env.exr")
bpy.ops.render.render(write_still=True)
sc.render.image_settings.file_format = "PNG"; sc.render.filepath = os.path.join(out, "sheen_env.png")
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(os.path.join(out, "sheen_env.exr"))
W, H = img.size; px = np.array(img.pixels[:]).reshape(H, W, 4)[..., :3]
Y = 0.2126*px[...,0] + 0.7152*px[...,1] + 0.0722*px[...,2]
# sphere centres in pixels: ortho 1.5 m across 720 px -> 480 px/m
for row in range(2):
    vals = []
    for i in range(6):
        cx = W/2 + (-0.6 + i*0.24) * 480; cy = H/2 - (0.12 - row*0.24) * 480
        yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx-cx, yy-cy) / (0.1*480)
        core = Y[(r < 0.5)].mean(); rim = Y[(r > 0.8) & (r < 0.95)].mean()
        vals.append((core, rim))
    c0, r0 = vals[0]
    print("ROW", ["white","base130"][row], " ".join(f"sw{weights[i]}: core x{v[0]/c0:.2f} rim x{v[1]/r0:.2f}" for i, v in enumerate(vals)))
