"""Minimal persistent Blender server (JSON lines over TCP on 127.0.0.1) for the spec 18 §3.2 latency probe.
Run: blender -b renders/research/mpfb_default.blend --python scripts/research/probe18_server.py -- <port> <out_dir>
then, from another shell: python3 -I scripts/research/probe18_client.py <port>
Commands: ping, measure (evaluated landmark read), set_key, render (Workbench, equivalent crop camera), shutdown.
"""
import bpy, sys, os, json, time, math, socket
import numpy as np

port = int(sys.argv[sys.argv.index("--") + 1]); OUT = sys.argv[sys.argv.index("--") + 2]
base = bpy.data.objects["Human"]; kb = base.data.shape_keys.key_blocks
sc = bpy.context.scene; r = sc.render
cam = bpy.data.cameras.new("Scene.Cam.Hero"); cob = bpy.data.objects.new("Scene.Cam.Hero", cam)
sc.collection.objects.link(cob); sc.camera = cob
cob.location = (0.0, -4.5, 0.6); cob.rotation_euler = (math.radians(93.9), 0.0, 0.0)
cam.sensor_width = 36.0; cam.sensor_fit = "HORIZONTAL"
r.engine = "BLENDER_WORKBENCH"; r.image_settings.file_format = "PNG"
shd = sc.display.shading; shd.light = "MATCAP"; shd.color_type = "SINGLE"; shd.show_cavity = True; shd.cavity_type = "BOTH"
sc.display.render_aa = "FXAA"
LM = np.linspace(0, 8000, 200).astype(int)

def crop_camera(x0, y0, x1, y1, s):
    w, h = x1 - x0, y1 - y0
    cam.lens = 46.0 * 1672 / w; cam.shift_x = ((x0 + x1) / 2 - 836) / w; cam.shift_y = (470.5 - (y0 + y1) / 2) / w
    r.resolution_x, r.resolution_y, r.resolution_percentage = int(w * s), int(h * s), 100

def cmd_ping(a): return {"pong": True}
def cmd_set_key(a):
    kb[a["key"]].value = a["value"]; return {"ok": True}
def cmd_measure(a):
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    ev = base.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)[LM]
    return {"n": int(len(co)), "zmax_mm": float(co[:, 2].max() * 1e3)}
def cmd_render(a):
    crop_camera(*a["box"], a.get("scale", 1))
    r.filepath = os.path.join(OUT, a["name"] + ".png"); bpy.ops.render.render(write_still=True)
    return {"path": r.filepath}
CMDS = {"ping": cmd_ping, "set_key": cmd_set_key, "measure": cmd_measure, "render": cmd_render}

srv = socket.create_server(("127.0.0.1", port)); srv.settimeout(120)
print("LISTENING", port, flush=True)
done = False
while not done:
    conn, _ = srv.accept()
    f = conn.makefile("rwb")
    for line in f:
        req = json.loads(line)
        if req["cmd"] == "shutdown":
            done = True; f.write(b'{"ok": true}\n'); f.flush(); break
        t = time.time()
        try:
            res = {"id": req.get("id"), "ok": True, "result": CMDS[req["cmd"]](req.get("args", {}))}
        except Exception as e:
            res = {"id": req.get("id"), "ok": False, "error": repr(e)}
        res["ms"] = round((time.time() - t) * 1e3, 2)
        f.write((json.dumps(res) + "\n").encode()); f.flush()
    conn.close()
srv.close()
print("SERVER_EXIT", flush=True)
