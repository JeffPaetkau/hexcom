"""Client for probe18_server.py (spec 18 §3.2): round-trip latency of ping, set_key + measure and render.
Run: python3 -I scripts/research/probe18_client.py <port>
"""
import socket, json, sys, time, statistics

port = int(sys.argv[1])
s = socket.create_connection(("127.0.0.1", port)); f = s.makefile("rwb")
def call(cmd, **args):
    t = time.time(); f.write((json.dumps({"cmd": cmd, "args": args}) + "\n").encode()); f.flush()
    res = json.loads(f.readline()); return res, (time.time() - t) * 1e3
out = {}
lat = [call("ping")[1] for _ in range(50)]
out["ping_ms_median"] = round(statistics.median(lat), 3)
lat = []
for i in range(20):
    call("set_key", key=1, value=0.5 + 0.01 * (i % 3))
    res, ms = call("measure"); lat.append(ms)
out["set_key_measure_ms_median"] = round(statistics.median(lat), 2)
for i in range(4):
    res, ms = call("render", name=f"srv_soldier_{i}", box=[580, 20, 1020, 935], scale=1)
    out[f"render_soldier_x1_fxaa_ms_{i}"] = round(ms, 1)
res, ms = call("render", name="srv_head_x5", box=[715, 30, 885, 200], scale=5)
out["render_head_x5_fxaa_ms"] = round(ms, 1)
call("shutdown")
print("CLIENT", json.dumps(out))
