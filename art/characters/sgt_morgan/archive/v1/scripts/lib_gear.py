"""Check renders of the shared gear modules on the materials test boot (spec 18 §4.3; CLAUDE.md rule 3).

lib/gn_stitches.py, lib/gear_webbing.py and lib/gear_hardware.py dressed on Lib.Test.Boot (materials.test_boot,
spec 16's stand-in) in spec 17's LookDev, with the boot recipes: a felled vamp/quarter seam on the lateral
side (a 0.8 x 2.5 welt, two rows at 1.5 and 5.5 mm, a bar tack at its top), the toe-cap seam's two rows and
the stays' rows (spec 02 §4.9's table); spec 02 §4.10's ankle strap (the medial strap round the heel folded
round the ladder-lock's rear bar, the lateral strap threaded up through the rear slot, over the middle bar
and down through the front one, doubling back as the tail through the lateral keeper, folded 10 and tacked;
a keeper on each side, box-X stitched); five eyelets and two speed hooks on each stay (spec 02 §4.8). The
stand-in's own stitches, strap, buckle, eyelets, laces and aglets are hidden. Every object is under
Lib.Test.Gear. in the Lib.Test collection, so only spec 16 and 17's LookDev views show it.

  python -I scripts/eval/lib_gear.py [--tier eval] [--views stitches,strap,hardware] [--out renders/lib_gear]
Output: renders/lib_gear/<view>_<tier>.png (+ _ungraded.png, .json, an .exr from eval up) and a RESULT line.
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))  # scripts/
from lib import env  # noqa: E402
from eval import camera  # noqa: E402

import numpy as np  # noqa: E402

PREFIX = "Lib.Test.Gear."
HIDE = ["LookDev.Swatch", "Cal.*", "Lib.Test.Ball", "Lib.Test.Toe", "Lib.Test.Nail", "Lib.Test.Fold"]
REPLACED = ("stitches", "strap", "buckle", "eyelets", "laces", "aglets")


def _view(vid, label, pos, target, lens, res, note):
    return camera._defaults({"id": f"lib_gear.{vid}", "label": label, "owner": "16", "scene": "lookdev",
                             "camera": {"type": "look_at", "frame": "W", "pos_mm": list(pos), "target_mm": list(target),
                                        "up": [0, 0, 1], "lens_mm": lens, "sensor_mm": 36},
                             "render": {"res": list(res), "tier": "eval", "film_transparent": False},
                             "hide": HIDE, "compare": [], "note": note})


VIEWS = {   # boot frame (mm): toes toward -Y, lateral +X; world = boot + (0, 0, 0.5)
    "stitches": _view("stitches", "stitches", (215, -238, 140), (36, -64, 62), 85, (1200, 900),
                      "lateral vamp: the felled seam's ridge and two rows, its bar tack, the toe-cap rows"),
    "stitches_close": _view("stitches_close", "stitches_close", (128, -162, 128), (27, -62, 82), 105, (1200, 900),
                            "the bar tack at the top of the felled seam and the first stitches of both rows"),
    "strap": _view("strap", "strap", (335, 25, 222), (46, 84, 160), 60, (1200, 800),
                   "the lateral side of the ankle strap: ladder-lock at phi 150, keeper at 72, the folded tail"),
    "strap_close": _view("strap_close", "strap_close", (126, 244, 198), (32, 122, 160), 100, (1200, 900),
                         "the ladder-lock: the strap through its slots, the medial strap folded round its rear bar"),
    "hardware": _view("hardware", "hardware", (150, -335, 178), (14, -30, 140), 55, (1000, 1200),
                      "both stays: five rolled eyelets and two speed hooks each, the stay rows"),
    "hardware_close": _view("hardware_close", "hardware_close", (112, -172, 205), (16, 2, 172), 100, (1200, 900),
                            "E5, H1 and H2 on the lateral stay"),
}


def _clear():
    import bpy
    obs = [o for o in bpy.data.objects if o.name.startswith(PREFIX)]
    meshes = {o.data for o in obs if o.data is not None}
    bpy.data.batch_remove(obs)
    bpy.data.batch_remove([m for m in meshes if m.users == 0])


def _outer(upper):
    """A Surface of the upper's outer shell: its Solidify (inward, offset -1) off while sampling."""
    import bpy
    from lib import sweep
    sol = upper.modifiers.get("Solidify")
    prev = sol.show_viewport if sol else None
    if sol:
        sol.show_viewport = False
    bpy.context.evaluated_depsgraph_get().update()
    try:
        return sweep.Surface(upper)
    finally:
        if sol:
            sol.show_viewport = prev
        bpy.context.evaluated_depsgraph_get().update()


def _shaft_point(surf, phi_deg, z, out=0.0):
    """The shaft's surface point at spec 02's phi (0 the front, + lateral, 180 the back) and height z: a ray
    from the shaft's axis (0, 70) outward."""
    a = math.radians(phi_deg)
    d = np.array([math.sin(a), -math.cos(a), 0.0])
    hit = surf.ray(np.array([0.0, 70.0, z]), d, 200.0)
    p, n = hit[0], hit[1]
    return p + n * out, n


def _stay_point(surf, x, y, z):
    """A point on the stand-in's lace stays (as materials._throat finds its eyelet anchors): above h 120 a
    ray from behind toward -Y, below it a ray from the upper's centre (0, 45, 70) through (x, y, z)."""
    if z > 120.0:
        return surf.ray(np.array([x, 70.0, z]), np.array([0.0, -1.0, 0.0]), 200.0)[0]
    o = np.array([0.0, 45.0, 70.0])
    d = np.array([x, y, z]) - o
    return surf.ray(o, d / np.linalg.norm(d), 300.0)[0]


def build_stitches(upper, coll, rep):
    from lib import gn_stitches as GS, sweep
    t0 = time.time()
    S0 = _outer(upper)
    seam = GS.seam_path(S0, [(23.0, -63.0, 86.0), (36.0, -55.0, 70.0), (47.0, -44.0, 55.0), (53.0, -30.0, 42.0)],
                        step=0.5)
    # the felled ridge as a welt of its own (lib ridge() needs a finer panel than this stand-in's 0.6 mm)
    w = GS.welt(seam.sub(int(np.searchsorted(seam.s, 3.0)), len(seam)), 2.5, 0.8, sink=0.3, taper=4.0,
                offset=0.4, seed=2)   # it starts under the tack
    wob = w.to_object(PREFIX + "Welt", coll)
    from lib import materials as M
    M.assign(wob, "Leather.Boot.FullGrain", part="Lib")
    S1 = S0
    T, N, B = sweep.rmf_frames(seam)
    i = int(np.searchsorted(seam.s, 4.0))
    tack_c = seam.co[i] + B[i] * 2.6
    tack = GS.bartack(S1, tack_c, B[i], 10.0, 3.0, 0.6, seed=3)
    felled = GS.rows(seam, (1.5, 5.5), 3.4, 0.8, target=S1, seed=11).clear_of(tack_c, 5.2)
    # the toe cap's edge: the upper's section by the plane y -86 (rays from inside), rows on the cap
    pts = []
    for al in np.radians(np.linspace(-78.0, 78.0, 27)):
        h = S1.ray(np.array([0.0, -86.0, 36.0]), np.array([math.sin(al), 0.0, math.cos(al)]), 200.0)
        pts.append(h[0])
    toe = GS.seam_path(S1, pts, step=0.5)
    toecap = GS.rows(toe, (1.5, 5.5), 3.4, 0.8, target=S1, seed=21)
    stays = []
    for sx in (-1.0, 1.0):
        for k, xo in enumerate((28.5, 25.5)):
            line = []
            for z in np.linspace(97.0, 206.0, 12):
                h = S1.ray(np.array([sx * xo, 70.0, z]), np.array([0.0, -1.0, 0.0]), 200.0)
                line.append(h[0])
            stays.append(GS.running(GS.seam_path(S1, line, step=0.5), 3.4, 0.8, seed=31 + k + (5 if sx > 0 else 0)))
    allst = GS.Stitches.join([felled, toecap] + stays)
    ob = GS.stitch_object(PREFIX + "Stitches", allst, part="Lib", radius=0.2, sink=0.1, bow=0.15, coll=coll)
    tk = GS.tack_object(PREFIX + "Bartacks", tack, part="Lib", coll=coll)
    rep["stitches"] = {"welt_faces": len(w.faces), "welt_manifold": w.manifold(), "stitches": len(allst), "bartack_legs": len(tack), "thread_mm": round(allst.thread_mm(), 1),
                       "felled": len(felled), "toecap": len(toecap), "stays": int(sum(len(s) for s in stays)),
                       "seconds": round(time.time() - t0, 2)}
    return [ob, tk, wob], S1


def build_strap(upper, S1, coll, rep):
    """Spec 02 §4.10 on the stand-in's shaft at h 158 (see the module docstring)."""
    from lib import gear_hardware as GH, gear_webbing as GW, gn_stitches as GS, sweep
    t0 = time.time()
    z, w, t, so = 158.0, 15.0, 1.5, 1.0
    # the ladder-lock at phi 150: lying on the shaft, +Y forward (toward phi 72), its mid-plane 6.3 off
    pb, nb = _shaft_point(S1, 150.0, z)
    fwd = _shaft_point(S1, 140.0, z)[0] - _shaft_point(S1, 160.0, z)[0]
    lock = GH.ladder_lock(24.0, 18.0, 3.0, 3.0, 2, arch=1.2, edge_r=1.1)
    M = GH.frame_on(S1, pb, (0.0, 0.0, 1.0), lift=6.3)
    # frame_on puts +X along the hint; the lock's +X is across the strap (the shaft's axis, up) and +Y forward
    y = sweep._unit(fwd - (fwd @ M[:3, 2]) * M[:3, 2])
    x = np.cross(y, M[:3, 2])
    M[:3, 0], M[:3, 1] = x, y
    lock_ob = GH.to_object(PREFIX + "Lock", lock, matrix=M, material="Metal.Gunmetal", part="Lib", coll=coll)
    rear_bar = M[:3, :3] @ np.array([0.0, -7.5, 1.2 * (1 - (15.0 / 18.0) ** 2)]) + M[:3, 3]
    # the medial strap: from the medial stay (phi -32) round the heel to the lock, folded round its rear bar
    gap = 3.4
    s_end = float(nb @ (rear_bar - pb)) - (t + gap / 2.0)   # its standoff where it turns round the bar
    phis = [-32.0, -55.0, -90.0, -125.0, -160.0, 180.0, 165.0]
    ctrl = [_shaft_point(S1, p, z)[0] for p in phis]
    stand = [so] * len(phis)
    end = rear_bar - nb * (t + gap / 2.0)
    path_m = sweep.surface_path(S1, ctrl + [end - nb * s_end], standoff=stand + [s_end], step=1.0)
    strap_m = GW.strap(path_m, w, t, roll_deg=0.4, z_jitter=0.3, seed=5)
    sweep.fold_end(strap_m, 12.0, gap=gap)
    # the lateral strap: from the lateral stay (phi 32) back under the lock, up through the rear slot, over
    # the middle bar, down through the front slot, and forward on itself through the keeper as the tail
    # A strap wrapped round a bar keeps the same face inside the bend: coming back under the lock, up the
    # rear slot, over the middle bar and down the front one, its outer face on the boot turns to face the
    # boot as the tail. So the incoming layer's path (sweep's underside, thickness along N) is its outer
    # face with N into the boot, and the tail's path its inner face with N out: no roll anywhere.
    tail_so = so + t + 0.3
    p_in = sweep.surface_path(S1, [_shaft_point(S1, p, z)[0] for p in (32.0, 60.0, 90.0, 120.0, 140.0, 152.0)],
                              standoff=so + t, step=1.0)
    path_in = sweep.Path(p_in.co, -p_in.normal, True, p_in.on, False, p_in.surface, p_in.standoff)
    path_out = sweep.surface_path(S1, [_shaft_point(S1, p, z)[0] for p in (146.0, 130.0, 100.0, 72.0, 52.0, 42.0)],
                                  standoff=tail_so, step=1.0)
    joined = sweep.Path.join([path_in, path_out])
    slots = [GH.through(lock, 0, thickness=t, direction=1, wrap=-1, snug=True), GH.over(lock, 1, direction=1),
             GH.through(lock, 1, thickness=t, direction=-1, wrap=1, snug=True)]   # up, across the middle bar, down
    threaded = sweep.thread(joined, lock_ob, slots, lead=5.0, clear=0.3)   # short leads: ~5 mm of room under the lock
    strap_l = GW.strap(threaded, w, t, roll_deg=0.4, z_jitter=0.25, seed=6)
    sweep.fold_end(strap_l, 10.0)
    straps = GW.webbing(PREFIX + "Strap", [strap_m, strap_l], part="Lib", coll=coll)
    # keepers: leather loops over the two layers (lateral, phi 72) and over the medial strap (phi -72)
    keepers, kst = [], []
    for phi, standoff in ((72.0, 5.2), (-72.0, 3.4)):
        c, n = _shaft_point(S1, phi, z)
        along = _shaft_point(S1, phi + 3.0, z)[0] - _shaft_point(S1, phi - 3.0, z)[0]
        keepers.append(GW.keeper(S1, c, along, span=19.5, width=12.0, thickness=2.0, standoff=standoff, tab=8.0,
                                 seed=int(phi)))
    kob = GW.webbing(PREFIX + "Keepers", [k.strip for k in keepers], part="Lib", coll=coll, bevel=0.5,
                     material="Leather.Boot.FullGrain")
    for k, kp in enumerate(keepers):
        kst.append(kp.box_x(kob, size=(6.0, 9.0), pitch=2.4, seed=7 + k))
    # tacks: the tail's fold, the medial strap's fold behind the bar, both anchors at the stays
    tacks = [GW.fold_tack(straps, strap_l, length=12.0, width=4.0, seed=1),
             GW.fold_tack(straps, strap_m, length=12.0, width=4.0, from_end=7.5, seed=2)]
    for P, seed, top in ((path_m, 3, t + 1.0), (path_in, 4, -1.0)):   # path_in's N points into the boot
        Tm, Nm, Bm = sweep.rmf_frames(P)
        tacks.append(GS.bartack(straps, P.co[6] + Nm[6] * top, Bm[6], 12.0, 4.0, 0.6, seed=seed))
    st = GS.stitch_object(PREFIX + "StrapStitches", GS.Stitches.join(kst), part="Lib", coll=coll)
    tk = GS.tack_object(PREFIX + "StrapTacks", GS.Stitches.join(tacks), part="Lib", coll=coll)
    pen = {}
    for nm, sw in (("medial", strap_m), ("lateral", strap_l)):
        pen[nm] = sweep.penetration(sw, S1)
    lock_pen = sweep.penetration(strap_l, lock_ob)
    rep["strap"] = {"faces": len(strap_m.faces) + len(strap_l.faces), "manifold": [strap_m.manifold(), strap_l.manifold()],
                    "into_boot": {k: round(v["max_mm"], 3) for k, v in pen.items()},
                    "into_lock_mm": round(lock_pen["max_mm"], 3), "lock_inside_vertices": lock_pen["inside"],
                    "leads": getattr(threaded, "leads", None), "tightest_bend_mm": round(threaded.min_bend_radius(), 2),
                    "keeper_stitches": int(sum(len(s) for s in kst)), "tack_legs": int(sum(len(s) for s in tacks)),
                    "seconds": round(time.time() - t0, 2)}
    return [straps, kob, lock_ob, st, tk]


def build_hardware(S1, coll, rep):
    from lib import gear_hardware as GH
    t0 = time.time()
    yz_e = [(-66.0, 80.0), (-46.0, 94.0), (-26.0, 108.0), (-10.0, 126.0), (-2.0, 150.0)]
    yz_h = [(0.0, 175.0), (0.0, 199.0)]
    ey = GH.eyelet()
    hook = GH.speed_hook()
    obs = []
    for sx, side in ((1.0, "L"), (-1.0, "M")):
        frames = []
        for k, (y, z) in enumerate(yz_e):
            xo = 15.0 + 3.0 * k / 4.0
            frames.append(GH.frame_on(S1, _stay_point(S1, sx * xo, y, z), (0.0, 0.0, 1.0), seed=k + (0 if sx > 0 else 9),
                                      seat_mm=0.3, tilt_deg=3.0))
        obs += GH.row(PREFIX + f"Eyelet.{side}", ey, frames, material="Metal.Gunmetal", part="Lib", coll=coll,
                      surface=S1)
        piece = hook if sx > 0 else hook.mirrored("Y")
        for k, (y, z) in enumerate(yz_h):
            Mh = GH.frame_on(S1, _stay_point(S1, sx * 19.0, y, z), (0.0, 0.0, 1.0), seed=20 + k, seat_mm=0.2,
                             tilt_deg=2.0)
            obs.append(GH.to_object(PREFIX + f"Hook.{side}.{k + 1}", GH.conform(piece, S1, Mh), matrix=Mh,
                                    material="Metal.Gunmetal", part="Lib", coll=coll))
    rep["hardware"] = {"eyelets": 10, "hooks": 4, "eyelet_faces": len(ey.faces), "hook_faces": len(hook.faces),
                       "hook_dims": hook.dims, "seconds": round(time.time() - t0, 2)}
    return obs


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tier", default="eval")
    ap.add_argument("--views", default=",".join(VIEWS))
    ap.add_argument("--out", default="renders/lib_gear")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--save", help="save the scene to this .blend (for inspection)")
    a = ap.parse_args(argv)
    if not camera.in_blender():
        return camera.run_in_blender(__file__, argv, env.path("cache", "scene_eval.blend"))
    import bpy
    from lib import materials as M
    from eval import lookdev, render
    t0 = time.time()
    scene = lookdev.ensure()
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    _clear()
    objs = M.test_boot(scene)
    coll = bpy.data.collections[M.TEST_COLL]
    for k in REPLACED:
        objs[k].hide_render = True
        objs[k].hide_viewport = True
    rep = {"boot_s": round(time.time() - t0, 2)}
    made, S1 = build_stitches(objs["upper"], coll, rep)
    made += build_strap(objs["upper"], S1, coll, rep)
    made += build_hardware(S1, coll, rep)
    rep["build_s"] = round(time.time() - t0, 2)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    faces = {}
    for ob in made:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        faces[ob.name] = len(me.polygons)
        ev.to_mesh_clear()
    rep["faces_evaluated"] = faces
    rep["faces_total"] = int(sum(faces.values()))
    print("[lib_gear] " + json.dumps(rep, default=str), flush=True)   # before rendering (research F §0)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=env.path(a.save), copy=True)
    out_dir = env.path(a.out)
    os.makedirs(out_dir, exist_ok=True)
    renders = []
    scene.render.use_persistent_data = True
    for vid in [v for v in a.views.split(",") if v]:
        side = render.render_preset(VIEWS[vid], tier=a.tier, out_dir=out_dir, stem=f"{vid}_{a.tier}",
                                    samples=a.samples, scene_name="lookdev")
        renders.append({"view": vid, "seconds": side["seconds"], "seconds_total": side["seconds_total"],
                        "png": side["outputs"]["png"]})
        print(f"[lib_gear] {vid} {a.tier}: {side['seconds']:.1f} s render -> {side['outputs']['png']}", flush=True)
    rep["renders"] = renders
    rep["seconds"] = round(time.time() - t0, 2)
    print("RESULT " + json.dumps(rep, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(camera.script_args()))
