"""Prototype of the procedural 4-tone dark blotch camo (numpy only, tileable).
Tile = 1.0 m x 1.0 m at N px. Recipe:
  macro field  : fBm periodic noise, base wavelength ~180 mm (2 octaves)  -> splits background into two zones
  blotch field : fBm, base wavelength ~70 mm, 3 octaves, warped by a 25 mm noise (organic edges)
  speckle field: wavelength ~14 mm, 2 octaves (small islands)
  tone id      : thresholds on (0.55*blotch + 0.30*macro + 0.15*speckle) at quantiles giving 30/35/25/10 %
  soft edges   : tone-id image blurred with sigma = 2 mm then re-quantised softly (mix) -> 3-5 mm feathering
"""
import numpy as np, sys
from PIL import Image, ImageFilter
N = int(sys.argv[1]) if len(sys.argv)>1 else 2048
rng = np.random.default_rng(7)
def periodic_noise(n, wavelength_px, octaves, persistence=0.5, lacunarity=2.0):
    """Tileable fractal noise via spectral synthesis (band-limited white noise)."""
    fy = np.fft.fftfreq(n)[:,None]; fx = np.fft.fftfreq(n)[None,:]
    f = np.sqrt(fx**2+fy**2)+1e-9
    out = np.zeros((n,n)); amp=1.0; wl=wavelength_px
    for o in range(octaves):
        f0 = 1.0/wl
        # gaussian band around f0 (one octave wide)
        band = np.exp(-((np.log(f/f0))**2)/(2*0.45**2))
        phase = np.exp(2j*np.pi*rng.random((n,n)))
        spec = band*phase
        field = np.real(np.fft.ifft2(spec))
        field /= field.std()
        out += amp*field; amp*=persistence; wl/=lacunarity
    out -= out.mean(); out /= out.std()
    return out
mm = N/1000.0  # px per mm
macro  = periodic_noise(N, 220*mm, 2)
blotch = periodic_noise(N, 95*mm, 3, persistence=0.45)
warp   = periodic_noise(N, 25*mm, 2)
# domain-warp the blotch field by ~6 mm
yy,xx = np.mgrid[0:N,0:N]
sx = (xx + warp*6*mm).astype(int) % N; sy = (yy + np.roll(warp,N//3,axis=0)*6*mm).astype(int) % N
blotch_w = blotch[sy,sx]
speck  = periodic_noise(N, 14*mm, 2)
field = 0.55*blotch_w + 0.35*macro + 0.10*speck
field = np.asarray(Image.fromarray(((field-field.min())/(field.max()-field.min())*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.0*mm))).astype(float)
# quantile thresholds for tone fractions near-black 30 / charcoal 35 / olive 25 / tan 10
q = np.quantile(field, [0.30, 0.65, 0.90])
tone = np.digitize(field, q)  # 0..3
tones = np.array([[0x0c,0x0c,0x0a],[0x1c,0x1a,0x17],[0x36,0x32,0x2c],[0x5e,0x52,0x46]],float)
# soft edges: blur one-hot tone masks by sigma 2 mm then renormalise
rgb = np.zeros((N,N,3))
wsum = np.zeros((N,N))
for k in range(4):
    m = Image.fromarray(((tone==k)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5*mm))
    m = np.asarray(m).astype(float)/255.0
    rgb += m[...,None]*tones[k]; wsum += m
rgb /= np.maximum(wsum,1e-6)[...,None]
img = Image.fromarray(np.clip(rgb,0,255).astype(np.uint8))
img.save('/home/user/sgt_morgan/ref/zoom_camo_generated_tile_1m_v2.png')
print('tone fractions', [round((tone==k).mean()*100) for k in range(4)])
# verification at reference scale: 1 m -> 472 px (4.72 px/cm); analyse 90x35 px windows like the reference
small = img.resize((472,472), Image.LANCZOS)
small.save('/home/user/sgt_morgan/ref/zoom_camo_generated_at_refscale_v2.png')
lum = np.asarray(small.convert('L')).astype(float)
from collections import deque
def label(mask):
    H,W=mask.shape; lab=np.zeros((H,W),int); n=0; sizes=[]
    for y in range(H):
        for x in range(W):
            if mask[y,x] and lab[y,x]==0:
                n+=1; q=deque([(y,x)]); lab[y,x]=n; s=0
                while q:
                    cy,cx=q.popleft(); s+=1
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny,nx=cy+dy,cx+dx
                        if 0<=ny<H and 0<=nx<W and mask[ny,nx] and lab[ny,nx]==0: lab[ny,nx]=n; q.append((ny,nx))
                sizes.append(s)
    return sizes
for (x0,y0) in ((20,20),(200,60),(300,300),(100,380)):
    sub = lum[y0:y0+35, x0:x0+90]
    base = np.asarray(Image.fromarray(sub.astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))).astype(float)
    hp = sub-base
    for name,mask in (('light',hp>np.percentile(hp,70)),('dark',hp<np.percentile(hp,30))):
        sizes=[s for s in label(mask) if s>=10]
        eq=np.array([2*np.sqrt(s/np.pi) for s in sizes])*2.12
        print(f"win({x0},{y0}) {name:<5} n={len(eq):>2} eqdiam mm p25/50/75/max={np.percentile(eq,25):.0f}/{np.median(eq):.0f}/{np.percentile(eq,75):.0f}/{eq.max():.0f}")
    print(f"   contrast {(np.percentile(hp,90)-np.percentile(hp,10))/sub.mean()*100:.0f}% (mean lum {sub.mean():.0f})")
