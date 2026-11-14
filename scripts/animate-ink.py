#!/usr/bin/env python3
"""Desktop 4 wallpaper: 墨 Ink. A brush writes one spiral, it dries, then blows away as ash.

Raw 8-bit grey 1920x1080 frames go to stdout (pipe into ffmpeg, see build-desktops.sh).
  0 - 9 s    a dry brush winds the spiral in from the outside; the bristles run out of ink
             towards the centre and the stroke lifts to a hair-fine point
  9 - 12 s   the ink sinks into the paper
  12 - 15.5  wind takes it: the spiral crumbles from the left into drifting ash
  15.5 - 16  dark, and the brush comes down again (the loop is seamless)
"""
import argparse, os, sys
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

ap = argparse.ArgumentParser()
ap.add_argument('--fps', type=int, default=24)
ap.add_argument('--loop', type=float, default=16)
ap.add_argument('--preview')
a = ap.parse_args()
W, H = 1920, 1080
FPS, LOOP = a.fps, a.loop
N = int(round(FPS * LOOP))
TAU = 2 * np.pi
rng = np.random.default_rng(4)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def fbm(shape, scales, seed):
    r = np.random.default_rng(seed)
    out = np.zeros(shape, np.float32)
    for s, w in scales:
        out += gaussian_filter(r.standard_normal(shape).astype(np.float32), s) * w * s
    out -= out.min(); out /= out.max() + 1e-6
    return out


# ------------------------------------------------------------------ the stroke (static)
CX, CY = 905.0, 528.0
R0, TURNS, PHI0 = 410.0, 5.4, -2.25
THETA = TAU * TURNS
B = R0 / THETA                                   # px of radius lost per radian
L = R0 * THETA - B * THETA ** 2 / 2              # stroke length in px

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dx, dy = xx - CX, yy - CY
r = np.hypot(dx, dy)
phi = np.arctan2(dy, dx)
tb = np.mod(phi - PHI0, TAU)
k = np.round((R0 - r) / (TAU * B) - tb / TAU)
th = np.clip(tb + TAU * k, 0, THETA)
d = r - (R0 - B * th)                            # across the stroke
s = R0 * th - B * th ** 2 / 2                    # along the stroke (arc length)
u = s / L

# pressure: touch down, a slow swell, thinner as it winds in, lift to a point
noise_s = np.interp(s, np.linspace(0, L, 900), gaussian_filter(rng.standard_normal(900), 6) * 4)
w = 30 * smooth(u / 0.02) * (1 - 0.5 * u) * (1 + 0.10 * np.sin(u * 37) + 0.05 * noise_s) * \
    (1 - smooth((u - 0.93) / 0.07) * 0.92)
w = np.maximum(w, 0.6)
acr = d / w                                     # -0.5..0.5 inside the stroke
fibre = fbm((H, W), ((0.6, 1.0), (1.5, 0.7), (4.0, 0.4)), 3) - 0.5
inside = smooth(((0.5 - np.abs(acr)) * w + 3.2 * fibre) / 1.4)   # ragged, paper-bitten edge

# dry brush: 30 bristles, each with its own ink reserve
NB = 30
bj = np.clip(((acr + 0.5) * NB).astype(int), 0, NB - 1)
reserve = rng.uniform(0.25, 1.0, NB).astype(np.float32)
reserve[[0, 1, NB - 2, NB - 1]] *= 0.55          # the edge hairs dry first
drift = np.interp(s, np.linspace(0, L, 400), gaussian_filter(rng.standard_normal(400), 3))
dry = 0.12 + 0.85 * u ** 1.3 + 0.12 * drift
streak = (reserve[bj] - dry * (0.85 + 0.3 * np.sin(s / 23 + bj * 1.7)))
ink = smooth(streak / 0.08) * inside
paper = fbm((H, W), ((0.7, 1.0), (2.0, 0.6)), 7)
tone = np.interp(s, np.linspace(0, L, 300), 0.5 + 0.5 * np.tanh(gaussian_filter(rng.standard_normal(300), 4) * 3))
ink *= (0.70 + 0.22 * paper) * (0.82 + 0.18 * tone) * (1 - 0.18 * np.abs(acr * 2) ** 3)   # tooth, load, belly
ink = gaussian_filter(ink, 0.6)
wick = gaussian_filter(ink, 3.5) * 0.10          # ink soaking into the fibres
full = np.clip(ink * 0.93 + wick, 0, 1).astype(np.float32)
smap = s.astype(np.float32)

# ------------------------------------------------------------------ crumble + ash
field = (0.62 * fbm((H, W), ((3, 1.0), (10, 0.8), (30, 0.5)), 11) + 0.38 * xx / W).astype(np.float32)
ys, xs = np.nonzero(full > 0.25)
pick = rng.choice(len(xs), 2600, replace=False)
px, py = xs[pick].astype(np.float32), ys[pick].astype(np.float32)
pf = field[ys[pick], xs[pick]]
pv = rng.uniform(70, 190, len(px)); pup = rng.uniform(15, 70, len(px))
pw_ = rng.uniform(0, TAU, len(px)); pb = rng.uniform(0.35, 0.9, len(px))
fmin, fmax = field[full > 0.25].min(), field[full > 0.25].max()


def head_pos(t):
    return L * smooth(np.clip(t / 9.0, 0, 1)) ** 0.9


def frame(i):
    t = i / FPS
    sh = head_pos(t)
    reveal = smooth((sh - smap) / 6.0)
    img = full * reveal
    # wet gloss just behind the moving brush
    if t < 9.2:
        img = img + 0.10 * smooth(1 - (sh - smap) / 60.0) * reveal * (full > 0.1)
    # the ink sinks in
    sink = smooth((t - 9.0) / 3.0)
    img = img * (1 - 0.18 * sink) + gaussian_filter(img, 1.2) * 0.18 * sink if sink > 0 else img
    # wind
    q = np.clip((t - 12.0) / 3.3, 0, 1) ** 1.25
    out = img
    if q > 0:
        thr = fmin + (fmax - fmin + 0.05) * q
        alive = smooth((field - thr) / 0.012)
        ember = np.exp(-((field - thr) / 0.008) ** 2) * (full > 0.2)
        out = img * alive + 0.35 * ember * img
        tt = np.clip((thr - pf) / (fmax - fmin + 0.05) * 3.5, 0, None)    # seconds since freed
        live = (thr > pf) & (tt < 2.6)
        if live.any():
            ax = px[live] + pv[live] * tt[live] + 12 * np.sin(pw_[live] + tt[live] * 3)
            ay = py[live] - pup[live] * tt[live] - 6 * tt[live] ** 2
            ab = pb[live] * (1 - smooth(tt[live] / 2.6))
            ok = (ax >= 1) & (ax < W - 1) & (ay >= 1) & (ay < H - 1)
            ax, ay, ab = ax[ok].astype(int), ay[ok].astype(int), ab[ok]
            ash = np.zeros((H, W), np.float32)
            np.add.at(ash, (ay, ax), ab)
            out = out + gaussian_filter(ash, 0.7) * 2.2
    out = out * (1 - smooth((t - 15.5) / 0.4))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


if a.preview:
    os.makedirs(a.preview, exist_ok=True)
    for t in (3.0, 8.9, 11.0, 13.2, 14.6):
        cv2.imwrite(os.path.join(a.preview, f'ink-{t:04.1f}.png'), frame(int(t * FPS)))
    sys.exit(0)

o = sys.stdout.buffer
for i in range(N):
    o.write(frame(i).tobytes())
    if i % 48 == 0:
        print(f'  ink frame {i}/{N}', file=sys.stderr)
