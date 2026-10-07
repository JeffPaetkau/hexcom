from PIL import Image, ImageFilter
import numpy as np
from collections import deque
src = Image.open('/home/user/sgt_morgan/ref/reference_full.png').convert('RGB')
im = np.asarray(src).astype(float)
lum = 0.2126*im[...,0]+0.7152*im[...,1]+0.0722*im[...,2]
L = Image.fromarray(lum.astype(np.uint8))
def label(mask):
    H,W = mask.shape; lab = np.zeros((H,W),int); n=0; sizes=[]; boxes=[]
    for y in range(H):
        for x in range(W):
            if mask[y,x] and lab[y,x]==0:
                n+=1; q=deque([(y,x)]); lab[y,x]=n; s=0; x0=x1=x; y0=y1=y
                while q:
                    cy,cx=q.popleft(); s+=1
                    x0=min(x0,cx);x1=max(x1,cx);y0=min(y0,cy);y1=max(y1,cy)
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny,nx=cy+dy,cx+dx
                        if 0<=ny<H and 0<=nx<W and mask[ny,nx] and lab[ny,nx]==0:
                            lab[ny,nx]=n; q.append((ny,nx))
                sizes.append(s); boxes.append((x1-x0+1,y1-y0+1))
    return sizes, boxes
def blotches(x0,y0,x1,y1,lbl,mmpx=2.12):
    sub = lum[y0:y1,x0:x1]
    base = np.asarray(Image.fromarray(sub.astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))).astype(float)
    hp = sub-base
    for name,mask in (('light',hp>np.percentile(hp,70)),('dark',hp<np.percentile(hp,30))):
        sizes,boxes = label(mask)
        keep=[(s,b) for s,b in zip(sizes,boxes) if s>=10]
        if not keep: print(lbl,name,'none'); continue
        eq=np.array([2*np.sqrt(s/np.pi) for s,_ in keep]); w=np.array([b[0] for _,b in keep]); h=np.array([b[1] for _,b in keep])
        print(f"{lbl:<14} {name:<5} n={len(keep):>3} eqdiam px p25/50/75/max={np.percentile(eq,25):.1f}/{np.median(eq):.1f}/{np.percentile(eq,75):.1f}/{eq.max():.1f} -> mm {np.percentile(eq,25)*mmpx:.0f}/{np.median(eq)*mmpx:.0f}/{np.percentile(eq,75)*mmpx:.0f}/{eq.max()*mmpx:.0f}; bbox med w/h {np.median(w):.0f}/{np.median(h):.0f}px; w/h {np.median(w/h):.2f}")
    print(f"   hp p10..p90 = {np.percentile(hp,10):.1f}..{np.percentile(hp,90):.1f}, mean lum {sub.mean():.0f}, contrast {(np.percentile(hp,90)-np.percentile(hp,10))/sub.mean()*100:.0f}%")
blotches(695,580,785,615,'R thigh lit')
blotches(850,580,930,615,'L thigh lit')
blotches(700,705,770,790,'R shin')
blotches(880,705,935,790,'L shin')
# 4-tone k-means on the lit thigh pixels (both)
allp = np.vstack([im[580:615,850:930].reshape(-1,3), im[580:615,695:785].reshape(-1,3), im[705:790,880:935].reshape(-1,3)])
rng=np.random.default_rng(1); C=allp[rng.choice(len(allp),4,replace=False)]
for _ in range(40):
    a=((allp[:,None,:]-C[None])**2).sum(-1).argmin(1)
    C=np.array([allp[a==k].mean(0) if (a==k).any() else C[k] for k in range(4)])
for k in np.argsort(C.sum(1)):
    print('tone','#%02x%02x%02x'%tuple(int(v) for v in C[k]), f'{(a==k).mean()*100:.0f}%')
# silhouette edges of the legs against the bright floor for y>=700
print("== leg silhouette (lum<70 runs) ==")
for y in range(700,812,8):
    row=lum[y,640:1000]; dark=row<70
    runs=[];start=None
    for i,d in enumerate(dark):
        if d and start is None: start=i
        if (not d or i==len(dark)-1) and start is not None:
            if i-start>=20: runs.append((640+start,640+i))
            start=None
    print(y, runs)
