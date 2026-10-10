"""Find the best Cycles GPU back end and print it as `SGT_DEVICE=<kind>` (OPTIX, CUDA, HIP, ... or CPU).

  blender -b --factory-startup --python scripts/setup/gpu_probe.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import env  # noqa: E402

found = {k: env.gpu_devices(k) for k in env.GPU_TYPES}
for k, names in found.items():
    if names:
        print(f"[gpu] {k}: {', '.join(names)}")
print(f"SGT_DEVICE={env.probe_gpu()}", flush=True)
