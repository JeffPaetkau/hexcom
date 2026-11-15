"""Drop-in for torchmcubes.marching_cubes using scikit-image (CPU). torchmcubes returns vertices
in reversed (z,y,x) axis order relative to the array; TripoSR undoes that with [2,1,0], so we
pre-reverse skimage's (i,j,k) index-order vertices to match."""
import numpy as np, torch
from skimage import measure
def marching_cubes(vol, thresh):
    v = vol.detach().cpu().numpy().astype(np.float32)
    verts, faces, _, _ = measure.marching_cubes(v, level=float(thresh))
    verts = verts[:, [2, 1, 0]].copy()
    return torch.from_numpy(verts.astype(np.float32)), torch.from_numpy(faces.astype(np.int64))
