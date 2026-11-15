"""The feet's landmarks as base.py's landmarks() defines them (heel back-bottom, big-toe tip, the 1st and 5th
metatarsal heads' bottoms on the sole plane; each riding foot.<S>), read from the evaluated body. pose_solve.py seats
heel, mt1 and mt5 on the boots' footbeds (heel 36, ball 24 above the floor, each keeping its rest height), so the
boots build their sole plane from the same points (scripts/parts/boots.py FootFrame): what the pose puts on the
footbed is what the boot's footbed is under."""
import numpy as np


def evaluated_co_m(body):
    """World metres of the evaluated body, helpers masked (the Mask modifier as the file has it)."""
    import bpy
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    mw = np.array(body.matrix_world)
    return co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]


def foot_landmarks(body):
    """{"heel_L": {"rest_mm": [x, y, z], "bone": "foot.L"}, "toe_L", "mt5_L", "mt1_L", and _R}: base.py's definition."""
    co = evaluated_co_m(body)
    out = {}
    for s, sign in (("L", 1), ("R", -1)):
        side = co[(co[:, 0] * sign > 0.03) & (co[:, 2] < 0.10)]
        heel = side[side[:, 2] < 0.02]
        heel = heel[np.argmax(heel[:, 1])]
        toe = side[np.argmin(side[:, 1])]
        band = side[(side[:, 2] < 0.012) & (side[:, 1] < heel[1] - 0.15) & (side[:, 1] > toe[1] + 0.03)]
        lat = band[np.argmax(band[:, 0] * sign)]
        med = band[np.argmin(band[:, 0] * sign)]
        for k, p in (("heel", heel), ("toe", toe), ("mt5", lat), ("mt1", med)):
            out[f"{k}_{s}"] = {"rest_mm": [round(float(v) * 1000, 2) for v in p], "bone": f"foot.{s}"}
    return out
