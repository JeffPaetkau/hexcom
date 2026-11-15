"""Run TripoSR on the CPU with (a) a scikit-image marching-cubes shim standing in for the
unbuildable torchmcubes and (b) a state-dict key remap for the transformers>=5 ViT (DINO) module names.

Usage:
  U2NET_HOME=assets/ai/rembg_models venv/bin/python -I scripts/research/ai_triposr_run.py <image.png> \
      --pretrained-model-name-or-path assets/ai/triposr --output-dir <dir> --mc-resolution 128 \
      --chunk-size 8192 --model-save-format obj
SHIM must be a directory holding torchmcubes.py (= ai_triposr_torchmcubes_shim.py) and an empty moderngl.py.
Research-only (see notes/research_ai_helpers.md section 6): TripoSR is NOT part of the build.
"""
import sys, runpy, re, time
REPO = "/home/user/sgt_morgan/assets/ai/triposr/repo"
SHIM = "/tmp/claude-0/-home-user/22b79727-7dd1-5139-b0e5-2c1a1a8c4609/scratchpad/tsr_shim"
sys.path[:0] = [SHIM, REPO]
import torch; torch.set_num_threads(4)
import tsr.system as tsys
# transformers>=5 renamed the ViT (DINO) modules; remap the 2024 checkpoint keys.
_orig = tsys.TSR.load_state_dict
def _remap(k):
    k = k.replace("image_tokenizer.model.encoder.layer.", "image_tokenizer.model.layers.")
    k = k.replace(".attention.attention.query.", ".attention.q_proj.")
    k = k.replace(".attention.attention.key.", ".attention.k_proj.")
    k = k.replace(".attention.attention.value.", ".attention.v_proj.")
    k = k.replace(".attention.output.dense.", ".attention.o_proj.")
    k = k.replace(".intermediate.dense.", ".mlp.fc1.")
    k = re.sub(r"(image_tokenizer\.model\.layers\.\d+)\.output\.dense\.", r"\1.mlp.fc2.", k)
    return k
def load_state_dict(self, sd, strict=True, **kw):
    sd = {_remap(k): v for k, v in sd.items()}
    return _orig(self, sd, strict=strict, **kw)
tsys.TSR.load_state_dict = load_state_dict
sys.argv = [REPO + "/run.py"] + sys.argv[1:]
t0 = time.time()
runpy.run_path(REPO + "/run.py", run_name="__main__")
import resource; print("TOTAL_WALL_S", round(time.time() - t0, 1), "PEAK_RSS_MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
