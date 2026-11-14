"""Fit a smooth ring-phase model Phi(x,y) to the hair spiral of the Uzumaki art.
Phi increases by 1 per ring going outward. Used by animate-uzumaki.py."""
import cv2, numpy as np, sys, json
from scipy.optimize import minimize
from scipy.ndimage import gaussian_filter

SRC = sys.argv[1]; OUT = sys.argv[2]
img = cv2.imread(SRC, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
H, W = img.shape
# hand-traced outline of the spiral dome (original 1125x2003 coordinates)
POLY = np.array([(565,567),(640,560),(700,573),(750,603),(772,660),(776,745),(776,800),
                 (772,842),(735,866),(690,875),(640,905),(590,880),(560,872),(500,842),(450,802),
                 (430,750),(428,685),(445,635),(480,595),(525,572)], np.int32)
mask = np.zeros((H, W), np.uint8); cv2.fillPoly(mask, [POLY], 1)
EYE = (638, 866, 50)  # eyeball centre + radius: stays still
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
mask[(xx-EYE[0])**2 + (yy-EYE[1])**2 < (EYE[2]+6)**2] = 0
cv2.imwrite(OUT + '/mask-raw.png', mask*255)

ys, xs = np.nonzero(mask)
Iv = gaussian_filter(img, 1.0)[ys, xs]; Iv = Iv - Iv.mean()

def spacing_int(rho, s0, s1, L):
    # F(rho) = integral dr / s(r), s(r) = s1 - (s1-s0) exp(-r/L)   (closed form)
    # 1/s = 1/(s1 - (s1-s0)e^{-r/L});  integral = r/s1 + (L/s1) ln((s1 - (s1-s0)e^{-r/L})/s0)
    return rho/s1 + (L/s1)*np.log((s1 - (s1-s0)*np.exp(-rho/L))/s0)

def phase(params, x, y):
    cx, cy, dx, dy, s0, s1, L, hand = params
    qx, qy = x-cx, y-cy
    dd = dx*dx + dy*dy
    qd = qx*dx + qy*dy
    rho = (-qd + np.sqrt(qd*qd + (1-dd)*(qx*qx+qy*qy))) / (1-dd)
    ang = np.arctan2(qy - rho*dy, qx - rho*dx)
    return spacing_int(rho, s0, s1, L) + hand*ang/(2*np.pi), rho

def score(p, hand):
    cx, cy, dx, dy, s0, s1, L = p
    if not (0.5 < s0 < 40 and 5 < s1 < 80 and 5 < L < 600 and dx*dx+dy*dy < 0.8): return 1e9
    ph, _ = phase((*p, hand), xs, ys)
    z = np.sum(Iv * np.exp(-2j*np.pi*ph))
    return -abs(z) / len(xs)

best = None
for hand in (1, -1):
    for dx0, dy0 in ((-0.2,-0.2), (-0.35,-0.25), (-0.1,-0.3), (0,0)):
        x0 = [709, 822, dx0, dy0, 8, 24, 60]
        r = minimize(score, x0, args=(hand,), method='Nelder-Mead',
                     options=dict(maxiter=4000, xatol=1e-3, fatol=1e-7))
        print(hand, dx0, dy0, r.fun, np.round(r.x, 3))
        if best is None or r.fun < best[0]: best = (r.fun, hand, r.x)
fun, hand, p = best
params = [*map(float, p), float(hand)]
json.dump(params, open(OUT + '/phase-params.json', 'w'))
print('BEST', fun, params)
