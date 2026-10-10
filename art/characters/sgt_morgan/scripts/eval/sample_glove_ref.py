# Spec 11 (gloves) reference sampler: gridded zooms of the glove regions and 5x5 colour / luminance
# samples used in spec/11_gloves.md sections 2.2 and 5.5. Run: python3 -I scripts/eval/sample_glove_ref.py
import sys
from PIL import Image, ImageDraw
import numpy as np
ref = Image.open('/home/user/sgt_morgan/ref/reference_full.png').convert('RGB')
A = np.asarray(ref).astype(float)
out = '/home/user/sgt_morgan/ref/'
def zoom(name, box, k):
    x0,y0,x1,y1 = box
    im = ref.crop(box).resize(((x1-x0)*k,(y1-y0)*k), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for x in range(x0 - x0%5, x1+1, 5):
        X=(x-x0)*k; d.line([(X,0),(X,im.height)], fill=(255,0,0) if x%10==0 else (255,160,160), width=1)
        if x%10==0: d.text((X+2,2), str(x), fill=(255,255,0))
    for y in range(y0 - y0%5, y1+1, 5):
        Y=(y-y0)*k; d.line([(0,Y),(im.width,Y)], fill=(0,255,255) if y%10==0 else (160,255,255), width=1)
        if y%10==0: d.text((2,Y+2), str(y), fill=(255,255,0))
    im.save(out+name); print('wrote', name, im.size)
zoom('zoom_glove_rknuckle_x12.png', (690,330,745,375), 12)
zoom('zoom_glove_rfingers_x10.png', (690,355,755,402), 10)
zoom('zoom_glove_rcuff_x12.png', (685,322,715,355), 12)
zoom('zoom_glove_lthumb_cuff_x10.png', (840,405,890,450), 10)
zoom('zoom_glove_ltips_x10.png', (798,448,840,500), 10)
def s(x,y,r=2):
    p = A[y-r:y+r+1, x-r:x+r+1].reshape(-1,3).mean(0); return '#%02x%02x%02x' % tuple(int(round(v)) for v in p)
pts = {'R knuckle plate index boss':(727,352),'R knuckle plate middle':(718,352),'R knuckle ring':(709,353),'R knuckle little':(701,356),
'R plate upper edge':(715,343),'R dorsum between plate and cuff':(705,340),'R dorsum knit (698,345)':(698,345),'R cuff under guard band':(700,335),
'R index PP dorsal':(735,368),'R index PIP pad':(740,377),'R index MP':(744,386),'R index tip':(749,396),
'R middle PP':(720,378),'R middle PIP pad':(714,388),'R ring PP':(708,385),'R little PP':(700,392),'R thumb web area':(730,362),
'R glove ulnar edge':(694,365),'R glove shadow under fingers':(725,398),
'L thumb stud':(850,445),'L thumb across rail':(860,436),'L thumb MCP area':(868,434),'L dorsum':(850,452),'L dorsum dark':(840,440),
'L cuff neoprene':(872,425),'L cuff upper':(878,415),'L cuff/sleeve edge':(884,420),'L guard band beyond cuff':(890,418),
'L tip index':(806,458),'L tip middle':(812,470),'L tip ring':(820,483),'L tip little':(828,495),'L tip index bright':(804,455),'L finger underside shadow':(815,476)}
for k,(x,y) in pts.items(): print(f'{k:40s} ({x},{y}) {s(x,y)}')
# luminance profiles across the right knuckle plate (column x=712 and x=724, rows 338-372)
L = A.mean(2)
print('col x=712 rows 338..372:', [int(L[y,712]) for y in range(338,373)])
print('col x=724 rows 338..372:', [int(L[y,724]) for y in range(338,373)])
print('row y=352 cols 692..740:', [int(L[352,x]) for x in range(692,741)])
# index finger width at rows 370,378,386,394 along a row
for y in (370,378,386,394):
    print(f'row {y} cols 728..756:', [int(L[y,x]) for x in range(728,757)])
# left tips: profile along column through tips
print('col x=812 rows 448..500:', [int(L[y,812]) for y in range(448,501)])
print('row y=445 cols 840..880 (thumb):', [int(L[445,x]) for x in range(840,881)])
print('row y=425 cols 860..895 (cuff):', [int(L[425,x]) for x in range(860,896)])
