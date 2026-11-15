"""Round 0, stage 3: evaluate the posed body against the reference (PLAN.md, round 0 step 3).

Renders cache/stages/pose.blend through take 1's matched hero camera (scripts/eval/camera.py; lights,
floor and world from scripts/eval/scene.py, the lights at 0.3 of spec 17's energy, which take 1 found
3-5x too bright), then composes comparison sheets with PIL. Everything goes to renders/round_00/:

  hero_full_clay.png, hero_full_cycles.png    the full 1672 x 941 frame, Workbench clay / quick Cycles
  soldier_clay.png, soldier_cycles.png        ref.soldier_full: box (580, 20, 1020, 935) at scale 2
  compare_soldier.png                         reference crop | clay | Cycles, side by side
  overlay_soldier.png                         the reference at 50 % with the render's silhouette edge
                                              (cyan), the fitted joints (green dots), the targets they
                                              were fitted to (red crosses, lines = residual), MediaPipe's
                                              raw keypoints (yellow rings) and the carbine stand-in pins
  views_posed.png, posed_{front,side_R,side_L,threeq_R,threeq_L,top}.png    the posed body from around
  views_rest.png, rest_{front,side_R}.png    the rest pose
  joints_px.json                              per-joint projected positions, targets and residuals

  "$SGT_PYIMG" -I scripts/stages/eval_round0.py [--no-cycles] [--samples 32]
  (launches "$SGT_BLENDER" -b cache/stages/pose.blend --python scripts/stages/eval_round0.py -- --blender)
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))
sys.path.insert(0, HERE)
OUT = os.path.join(PROJECT, "renders", "round_00")
POSE_BLEND = os.path.join(PROJECT, "cache", "stages", "pose.blend")
BOX, SCALE = (580, 20, 1020, 935), 2
LIGHT_SCALE = 0.3
# (name, camera position, target), metres; perspective 150 mm on 36 mm at about 6 m
VIEWS = {
    "front": ((0.0, -6.0, 1.0), (0.0, 0.0, 0.95)),
    "side_R": ((-6.0, 0.0, 1.0), (0.0, 0.0, 0.95)),
    "side_L": ((6.0, 0.0, 1.0), (0.0, 0.0, 0.95)),
    "threeq_R": ((-4.24, -4.24, 1.4), (0.0, 0.0, 0.95)),
    "threeq_L": ((4.24, -4.24, 1.4), (0.0, 0.0, 0.95)),
    "top": ((0.0, -0.6, 7.0), (0.0, 0.0, 0.9)),
}
REST_VIEWS = ("front", "side_R")


# --------------------------------------------------------------------------- inside Blender

def blender_main(argv):
    import bpy
    import numpy as np
    from mathutils import Matrix
    from eval import camera, camproj, render, scene as escene
    import pose as P
    a = argparse.ArgumentParser()
    a.add_argument("--no-cycles", action="store_true")
    a.add_argument("--samples", type=int, default=32)
    args = a.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    t0 = time.perf_counter()
    sc = bpy.context.scene
    rig = bpy.data.objects["Morgan.Rig"]
    data = P.apply_hero_pose(rig)
    if bpy.data.objects.get(P.PROXY) is None:
        P.add_carbine_proxy(rig, data)
    # the evaluation scene (spec 17 scope note) around the character
    for ob in list(bpy.data.objects):
        if ob.name.startswith("Scene."):
            bpy.data.objects.remove(ob, do_unlink=True)
    camera.hero_camera(sc)
    floor = escene.build_floor(sc)
    lights = escene.build_lights(sc)
    for L in lights:
        L.data.energy *= LIGHT_SCALE
    escene.build_world(sc, "hdri")
    escene.colour_management(sc)
    rig.hide_render = True
    times = {}

    def wb(path, film=True, floor_on=False):
        render._set_tier(sc, "form")
        sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
        sc.render.film_transparent = film
        floor.hide_render = not floor_on
        t = time.perf_counter()
        bpy.ops.render.render()
        render._save(sc, path, "PNG", "8", "RGBA")
        times[os.path.basename(path)] = round(time.perf_counter() - t, 2)

    def cy(path):
        render._set_tier(sc, "look", samples=args.samples)
        sc.render.resolution_percentage = 100
        escene.colour_management(sc)
        sc.render.film_transparent = True
        floor.hide_render = False
        t = time.perf_counter()
        bpy.ops.render.render()
        render._save(sc, path, "PNG", "8", "RGBA")
        times[os.path.basename(path)] = round(time.perf_counter() - t, 2)

    reg = camera.load_registry()
    # hero full frame and the soldier crop
    camera.apply(reg.get("ref.full"), sc, percent=100)
    wb(os.path.join(OUT, "hero_full_clay.png"))
    if not args.no_cycles:
        camera.apply(reg.get("ref.full"), sc, percent=100)
        cy(os.path.join(OUT, "hero_full_cycles.png"))
    camera.apply(reg.get("ref.soldier_full"), sc, percent=100)
    wb(os.path.join(OUT, "soldier_clay.png"))
    if not args.no_cycles:
        camera.apply(reg.get("ref.soldier_full"), sc, percent=100)
        cy(os.path.join(OUT, "soldier_cycles.png"))
    # projected joints and landmarks, measured on Blender's posed rig and mesh
    joints = {}
    for n, j in data["joints_px"].items():
        if n in rig.pose.bones:
            w = np.array(rig.matrix_world @ rig.pose.bones[n].head)
        else:
            w = None
        if w is not None:
            p = camproj.HERO.project([w])[0]
            j = dict(j, blender_px=[round(float(p[0]), 1), round(float(p[1]), 1)])
        joints[n] = j
    # floor contact and head top of the posed mesh (the evaluated body, through the camera)
    body = bpy.data.objects["Body.Mesh"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3) @ np.array(body.matrix_world)[:3, :3].T + np.array(body.matrix_world)[:3, 3]
    px = camproj.HERO.project(co)
    top = int(np.argmax(co[:, 2]))
    feet = {}
    for s, sign in (("L", 1), ("R", -1)):
        m = (co[:, 0] * sign > 0.02) & (co[:, 2] < 0.15)
        i = np.where(m)[0][np.argmax(px[m, 1])]
        feet[s] = {"lowest_px_y": round(float(px[i, 1]), 1), "z_mm": round(float(co[i, 2]) * 1000, 1),
                   "sole_min_z_mm": round(float(co[m, 2].min()) * 1000, 1)}
    checks = {"head_top": {"z_mm": round(float(co[top, 2]) * 1000, 1), "px": [round(float(v), 1) for v in px[top]],
                           "drawn_px_y": 20, "note": "drawn y 20 is the hair mass; the scalp sits ~15 mm (3 px) under it"},
              "feet_lowest": feet, "drawn_sole_px_y": {"R": 895, "L": 907},
              "silhouette_px": {"x": [round(float(px[:, 0].min()), 1), round(float(px[:, 0].max()), 1)],
                                "y": [round(float(px[:, 1].min()), 1), round(float(px[:, 1].max()), 1)]}}
    # carbine pins through Blender
    fr = bpy.data.objects[P.FRAME]
    M = np.array(fr.matrix_world)
    pins = {}
    for k in ("butt_pad_centre", "muzzle", "pistol_grip", "handguard", "receiver_face"):
        v = np.array(data["carbine_frame"]["points_mm"][k]) / 1000.0
        w = M[:3, :3] @ v + M[:3, 3]
        pins[k] = [round(float(c), 1) for c in camproj.HERO.project([w])[0]]
    # around views, posed then rest
    pc = camera.preset_camera(sc)
    sc.camera = pc

    def view(name, pos, tgt, path, lens=150.0, res=(560, 1000)):
        R = camproj.look_at_matrix(pos, tgt)
        Mv = np.eye(4)
        Mv[:3, :3], Mv[:3, 3] = R, pos
        pc.matrix_world = Matrix(Mv.tolist())
        pc.data.type, pc.data.lens, pc.data.sensor_width, pc.data.sensor_fit = "PERSP", lens, 36.0, "HORIZONTAL"
        pc.data.shift_x = pc.data.shift_y = 0.0
        pc.data.clip_start, pc.data.clip_end = 0.05, 100.0
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res[0], res[1], 100
        wb(path, film=True)
    for n, (pos, tgt) in VIEWS.items():
        view(n, pos, tgt, os.path.join(OUT, f"posed_{n}.png"))
    # the hands on the carbine, close: along the hero camera's line and from his side
    cam = np.asarray(camproj.HERO_LOC)
    for s in ("R", "L"):
        hb = rig.pose.bones
        tgt = np.array(rig.matrix_world @ ((hb[f"wrist.{s}"].head + hb[f"finger3-1.{s}"].head) / 2))
        d = (cam - tgt) / np.linalg.norm(cam - tgt)
        view(f"hand_{s}", tgt + d * 1.2, tgt, os.path.join(OUT, f"posed_hand_{s}.png"), lens=100.0, res=(700, 700))
        side = np.array([-1.0 if s == "R" else 1.0, -0.6, 0.3])
        side /= np.linalg.norm(side)
        view(f"hand_{s}_side", tgt + side * 1.2, tgt, os.path.join(OUT, f"posed_hand_{s}_side.png"), lens=100.0, res=(700, 700))
    for pb in rig.pose.bones:
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.location = (0.0, 0.0, 0.0)
    bpy.data.objects[P.PROXY].hide_render = True
    bpy.context.view_layer.update()
    for n in REST_VIEWS:
        pos, tgt = VIEWS[n]
        view(n, pos, tgt, os.path.join(OUT, f"rest_{n}.png"))
    out = {"joints": joints, "checks": checks, "carbine_pins_px": pins, "pose_solve": data.get("solve"),
           "readback": data.get("readback"), "render_seconds": times,
           "total_seconds": round(time.perf_counter() - t0, 1)}
    with open(os.path.join(OUT, "joints_px.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    print("[eval] renders:", json.dumps(times), flush=True)
    return 0


# --------------------------------------------------------------------------- outside Blender: the sheets

def compose():
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from eval import camproj
    with open(os.path.join(OUT, "joints_px.json"), encoding="utf-8") as f:
        J = json.load(f)
    with open(os.path.join(HERE, "ref_keypoints.json"), encoding="utf-8") as f:
        KP = json.load(f)
    try:
        font = ImageFont.load_default(size=18)
        small = ImageFont.load_default(size=13)
    except TypeError:
        font = small = ImageFont.load_default()
    BG = (40, 40, 44)

    def flat(path):
        im = Image.open(path).convert("RGBA")
        base = Image.new("RGBA", im.size, BG + (255,))
        return Image.alpha_composite(base, im).convert("RGB")

    full = Image.open(os.path.join(PROJECT, "ref", "reference_full.png")).convert("RGB")
    W, H = (BOX[2] - BOX[0]) * SCALE, (BOX[3] - BOX[1]) * SCALE
    ref = full.crop(BOX).resize((W, H), Image.LANCZOS)

    def label(im, text):
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, im.width, 30), fill=(0, 0, 0))
        d.text((8, 5), text, fill=(255, 255, 255), font=font)
        return im
    panels = [label(ref.copy(), "reference (ref.soldier_full x2)"), label(flat(os.path.join(OUT, "soldier_clay.png")), "round 0: Workbench clay")]
    cyc = os.path.join(OUT, "soldier_cycles.png")
    if os.path.exists(cyc):
        panels.append(label(flat(cyc), "round 0: Cycles (quick)"))
    sheet = Image.new("RGB", (W * len(panels) + 10 * (len(panels) - 1), H), (0, 0, 0))
    for i, p in enumerate(panels):
        sheet.paste(p, (i * (W + 10), 0))
    sheet.save(os.path.join(OUT, "compare_soldier.png"))

    # overlay
    clay = Image.open(os.path.join(OUT, "soldier_clay.png")).convert("RGBA")
    alpha = np.asarray(clay)[:, :, 3] > 127
    e = alpha.copy()
    inner = alpha.copy()
    inner[1:] &= alpha[:-1]
    inner[:-1] &= alpha[1:]
    inner[:, 1:] &= alpha[:, :-1]
    inner[:, :-1] &= alpha[:, 1:]
    e = alpha & ~inner
    from scipy.ndimage import binary_dilation
    e = binary_dilation(e, iterations=1)
    base = (np.asarray(ref).astype(float) * 0.5 + 0.5 * 30).astype(np.uint8)
    base[e] = (0, 230, 255)
    ov = Image.fromarray(base)
    d = ImageDraw.Draw(ov)

    def P(xy):
        return ((xy[0] - BOX[0]) * SCALE, (xy[1] - BOX[1]) * SCALE)
    for n, v in KP["mediapipe"].items():
        x, y = P(v["xy"])
        d.ellipse((x - 7, y - 7, x + 7, y + 7), outline=(255, 220, 0), width=2)
    for n, j in J["joints"].items():
        t, f = P(j["target_px"]), P(j.get("blender_px", j["fit_px"]))
        d.line((t, f), fill=(255, 80, 80), width=2)
        d.line((t[0] - 9, t[1], t[0] + 9, t[1]), fill=(255, 60, 60), width=3)
        d.line((t[0], t[1] - 9, t[0], t[1] + 9), fill=(255, 60, 60), width=3)
        d.ellipse((f[0] - 6, f[1] - 6, f[0] + 6, f[1] + 6), fill=(60, 255, 90))
        d.text((f[0] + 9, f[1] - 7), f"{n} {j['residual_px']:.0f}", fill=(220, 255, 220), font=small)
    for k, v in J["carbine_pins_px"].items():
        x, y = P(v)
        d.rectangle((x - 6, y - 6, x + 6, y + 6), outline=(255, 120, 255), width=3)
    d.rectangle((0, 0, W, 64), fill=(0, 0, 0))
    d.text((8, 4), "overlay: ref 50 % | cyan = render silhouette | green = fitted joints | red = targets (line = residual)",
           fill=(255, 255, 255), font=small)
    d.text((8, 22), "yellow rings = MediaPipe raw | magenta = carbine stand-in points (butt, muzzle, grip, handguard, receiver)",
           fill=(255, 255, 255), font=small)
    d.text((8, 40), "head top z %.0f mm -> y %.1f (drawn hair top 20); lowest foot px y R %.1f L %.1f (drawn soles 895 / 907)" % (
        J["checks"]["head_top"]["z_mm"], J["checks"]["head_top"]["px"][1], J["checks"]["feet_lowest"]["R"]["lowest_px_y"],
        J["checks"]["feet_lowest"]["L"]["lowest_px_y"]), fill=(255, 255, 255), font=small)
    ov.save(os.path.join(OUT, "overlay_soldier.png"))

    def strip(names, prefix, out, title):
        ims = [label(flat(os.path.join(OUT, f"{prefix}_{n}.png")), f"{prefix} {n}") for n in names]
        w = sum(i.width for i in ims) + 8 * (len(ims) - 1)
        s = Image.new("RGB", (w, ims[0].height), (0, 0, 0))
        x = 0
        for i in ims:
            s.paste(i, (x, 0))
            x += i.width + 8
        s.save(os.path.join(OUT, out))
    strip(list(VIEWS), "posed", "views_posed.png", "posed")
    strip(["hand_R", "hand_R_side", "hand_L", "hand_L_side"], "posed", "views_hands.png", "hands")
    strip(list(REST_VIEWS), "rest", "views_rest.png", "rest")
    print("[eval] sheets written to", os.path.relpath(OUT, PROJECT))


def main(argv):
    if "--blender" in argv:
        rest = [a for a in argv if a != "--blender"]
        return blender_main(rest)
    from lib import env
    a = argparse.ArgumentParser()
    a.add_argument("--no-cycles", action="store_true")
    a.add_argument("--samples", type=int, default=32)
    a.add_argument("--sheets-only", action="store_true")
    args = a.parse_args(argv)
    if not args.sheets_only:
        cmd, environ = env.blender_cmd(["-b", POSE_BLEND, "--python", os.path.abspath(__file__), "--", "--blender"]
                                       + (["--no-cycles"] if args.no_cycles else []) + ["--samples", str(args.samples)])
        t = time.perf_counter()
        r = subprocess.run(cmd, env=environ, cwd=PROJECT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        lines = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith(("[eval]", "Traceback", "  File", "Error")) or "Error" in l]
        print("\n".join(lines[-40:]))
        print(f"[eval] Blender {time.perf_counter() - t:.1f} s, exit {r.returncode}")
        if r.returncode:
            return r.returncode
    compose()
    return 0


if __name__ == "__main__":
    in_blender = "bpy" in sys.modules
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ([] if in_blender else sys.argv[1:])
    if in_blender:
        try:
            rc = blender_main([a for a in argv if a != "--blender"])
        except Exception:
            import traceback
            traceback.print_exc()
            rc = 1
        sys.stdout.flush()
        if rc:
            os._exit(rc)
    else:
        sys.exit(main(argv))
