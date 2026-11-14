#!/usr/bin/env python3
"""Desktop 3 wallpaper: Hellstar Remina.

The cleaned panel (speech balloons removed with LaMa, skyline rebuilt; see src/remina/) on a
starfield, writes raw rgb24 1920x1080 frames to stdout (pipe into ffmpeg, see build-desktops.sh).
  * the Hellstar breathes, its corona writhes and its star-shaped pupil dilates, turns to look
    down at Remina, and once a loop snaps shut (the panel flashes negative for two frames)
  * a dim blood-red glow pulses off the star and spills out of the panel into space
  * Remina's hair sways in a slow wind
  * ash and a few embers rise from the burning city and drift out of the frame
Every periodic term divides LOOP so the video loops without a seam.
"""
import argparse, os, sys
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

ap = argparse.ArgumentParser()
ap.add_argument('panel', help='cleaned panel (grey PNG)')
ap.add_argument('repaired', help='mask of every inpainted pixel (white = repaired)')
ap.add_argument('--fps', type=int, default=24)
ap.add_argument('--loop', type=float, default=16)
ap.add_argument('--preview', help='write a few PNG frames to this dir instead of streaming')
a = ap.parse_args()

W, H = 1920, 1080
FPS, LOOP = a.fps, a.loop
N = int(round(FPS * LOOP))
TAU = 2 * np.pi
rng = np.random.default_rng(1987)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def bump(t, c, w):
    return np.exp(-((t - c) / w) ** 2)


# ------------------------------------------------------------------ the panel, graded
src = cv2.imread(a.panel, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
ph_, pw_ = src.shape
rep = gaussian_filter((cv2.imread(a.repaired, cv2.IMREAD_GRAYSCALE) > 127).astype(np.float32), 3)

# LaMa leaves the repaired sky smoother than Ito's sponge stipple: put the grain back
hf = src - gaussian_filter(src, 2.0)
sky = (gaussian_filter(src, 4) > 0.45) & (rep < 0.05)
amp = hf[sky].std()
n = sum(gaussian_filter(rng.standard_normal(src.shape).astype(np.float32), s) * w
        for s, w in ((0.6, 1.0), (1.2, 0.8), (2.5, 0.5)))
n = n - gaussian_filter(n, 2.0)
n *= amp / (n.std() + 1e-6)
skyish = smooth((gaussian_filter(src, 4) - 0.38) / 0.15)
src = np.clip(src + n * rep * skyish * 1.1, 0, 1)

SCX, SCY = 167.0, 134.0            # Hellstar centre in panel pixels
yy, xx = np.mgrid[0:ph_, 0:pw_].astype(np.float32)
dsx, dsy = xx - SCX, yy - SCY
rs = np.hypot(dsx, dsy)
ths = np.arctan2(dsy, dsx)

# lit by the star: everything falls into night away from it
light = 0.64 + 0.36 * np.exp(-(rs / 430.0) ** 2)
src = np.clip((src - 0.04) / 0.96, 0, 1) ** 1.12 * light
# deepen the bottom (the city is in shadow)
src *= 1 - 0.35 * smooth((yy - 700) / 229)

# ------------------------------------------------------------------ masks for the motion
hair_poly = np.array([(300, 280), (345, 300), (380, 330), (395, 380), (400, 440), (395, 520),
                      (380, 600), (340, 610), (330, 520), (345, 470), (345, 400), (330, 360),
                      (285, 352), (250, 370), (232, 410), (232, 450), (245, 480), (230, 520),
                      (200, 560), (160, 600), (90, 600), (60, 560), (30, 520), (0, 500), (0, 430),
                      (60, 400), (150, 350), (200, 310)], np.int32)
hair = np.zeros_like(src); cv2.fillPoly(hair, [hair_poly], 1.0)
hair = gaussian_filter(hair, 6)
hair_ramp = smooth((np.hypot(xx - 290, yy - 285) - 40) / 230)
hair_w = hair * hair_ramp
star_w = (1 - smooth((rs - 235) / 70)) * (1 - hair)          # star motion never touches her hair
corona_w = smooth((rs - 120) / 45) * (1 - smooth((rs - 225) / 60)) * (1 - hair)
pupil_r = 60.0
pupil_w = np.clip(1 - rs / pupil_r, 0, 1)
look_w = smooth(1 - rs / 78.0)


def warp(t):
    breath = 1 + 0.016 * np.sin(TAU * 2 * t / LOOP)
    dil = 0.16 * np.sin(TAU * t / LOOP) - 0.42 * bump(t, 10.42, 0.10) + 0.10 * bump(t, 10.9, 0.35)
    look = smooth((t - 5.2) / 0.9) - smooth((t - 8.6) / 1.1)
    lx, ly = 5.5 * look, 6.0 * look
    rock = 0.022 * np.sin(TAU * t / LOOP)
    dr = (rs * (1 / breath - 1) - dil * rs * pupil_w ** 2) * star_w
    dth = rock * star_w + 0.032 * np.sin(6 * ths + rs / 22 - TAU * 3 * t / LOOP) * corona_w \
        + 0.018 * np.sin(11 * ths - rs / 15 + TAU * 2 * t / LOOP) * corona_w
    r2, t2 = rs + dr, ths + dth
    sx = SCX + r2 * np.cos(t2) - lx * look_w
    sy = SCY + r2 * np.sin(t2) - ly * look_w
    # wind in her hair: longer strands move more, a gust travels down them
    sway = 2.7 * (0.62 * np.sin(TAU * 2 * t / LOOP + yy / 60) +
                  0.38 * np.sin(TAU * 3 * t / LOOP + yy / 37 + 1.3)) * hair_w
    sx = sx + sway
    sy = sy + 0.25 * sway
    return sx.astype(np.float32), sy.astype(np.float32)


# ------------------------------------------------------------------ layout
PH = 960
PW = int(round(pw_ * PH / ph_))
PX, PY = (W - PW) // 2, (H - PH) // 2
S = PH / ph_
SX, SY = PX + SCX * S, PY + SCY * S           # star on screen

Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.hypot(X - SX, Y - SY)
RED = np.array([0.62, 0.05, 0.04], np.float32)
glow_ring = np.exp(-((rr - 136 * S) / (40 * S)) ** 2) * 0.85 + np.exp(-(rr / (300 * S)) ** 2) * 0.45
glow_out = np.exp(-(rr / 520.0) ** 1.6) * 0.55                  # spill into space

inpanel = np.zeros((H, W), np.float32)
inpanel[PY:PY + PH, PX:PX + PW] = 1

# starfield (stays out of the panel)
NS = 230
st_x = rng.uniform(0, W, NS); st_y = rng.uniform(0, H, NS)
keep = ~((st_x > PX - 30) & (st_x < PX + PW + 30) & (st_y > PY - 30) & (st_y < PY + PH + 30))
st_x, st_y = st_x[keep], st_y[keep]
st_b = rng.uniform(0.10, 0.42, len(st_x)) * np.clip(1.1 - np.hypot(st_x - W / 2, st_y - H / 2) / 1300, 0.4, 1)
st_k = rng.integers(1, 4, len(st_x)); st_p = rng.uniform(0, TAU, len(st_x))
st_big = rng.random(len(st_x)) < 0.12


def draw_stars(t):
    img = np.zeros((H, W), np.float32)
    b = st_b * (0.55 + 0.45 * np.sin(TAU * st_k * t / LOOP + st_p))
    xi, yi = st_x.astype(int), st_y.astype(int)
    np.add.at(img, (yi, xi), b)
    big = st_big
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        np.add.at(img, (np.clip(yi[big] + dy, 0, H - 1), np.clip(xi[big] + dx, 0, W - 1)), b[big] * 0.4)
    return img


# frames (two thin manga-panel outlines, one tilted, as on the other desktops)
frames = np.zeros((H, W), np.float32)
cv2.rectangle(frames, (PX - 14, PY - 14), (PX + PW + 13, PY + PH + 13), 0.9, 1, cv2.LINE_AA)
box = cv2.boxPoints(((PX + PW / 2 + 12, PY + PH / 2 + 4), (PW + 70, PH + 40), -2.4))
cv2.polylines(frames, [box.astype(np.int32)], True, 0.75, 1, cv2.LINE_AA)
frames[PY:PY + PH, PX:PX + PW] = 0       # never draw over the art

# ash and embers rising from the city
NP = 110
p_x0 = rng.uniform(PX - 260, PX + PW + 260, NP)
p_y0 = rng.uniform(PY + PH - 160, H + 30, NP)
p_rise = rng.uniform(380, 820, NP)
p_k = rng.integers(1, 3, NP)
p_ph = rng.uniform(0, 1, NP)
p_wob = rng.uniform(6, 26, NP); p_wk = rng.integers(1, 4, NP); p_wp = rng.uniform(0, TAU, NP)
p_size = rng.uniform(0.7, 2.0, NP)
p_ember = rng.random(NP) < 0.16
p_b = np.where(p_ember, rng.uniform(0.55, 0.95, NP), rng.uniform(0.25, 0.6, NP))
EMBER = np.array([1.0, 0.38, 0.16], np.float32)
ASH = np.array([0.85, 0.83, 0.80], np.float32)
KS = 7
kk = np.arange(-KS, KS + 1, dtype=np.float32)


def draw_particles(img, t):
    for i in range(NP):
        u = (p_k[i] * t / LOOP + p_ph[i]) % 1.0
        x = p_x0[i] + p_wob[i] * np.sin(TAU * p_wk[i] * t / LOOP + p_wp[i]) + 40 * u
        y = p_y0[i] - p_rise[i] * u
        f = smooth(u / 0.15) * (1 - smooth((u - 0.6) / 0.4))
        if f <= 0.01:
            continue
        flick = 0.75 + 0.25 * np.sin(TAU * 7 * p_k[i] * t / LOOP + p_wp[i] * 3) if p_ember[i] else 1.0
        xi, yi = int(x), int(y)
        if xi < KS or yi < KS or xi >= W - KS or yi >= H - KS:
            continue
        gx = np.exp(-((kk - (x - xi)) / p_size[i]) ** 2)
        gy = np.exp(-((kk - (y - yi)) / p_size[i]) ** 2)
        spot = np.outer(gy, gx) * p_b[i] * f * flick
        col = EMBER if p_ember[i] else ASH
        img[yi - KS:yi + KS + 1, xi - KS:xi + KS + 1] += spot[..., None] * col


def frame(i):
    t = i / FPS
    sx, sy = warp(t)
    pan = cv2.remap(src, sx, sy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    pan = cv2.resize(pan, (PW, PH), interpolation=cv2.INTER_AREA)
    shock = bump(t, 10.42, 0.045)                       # two frames of negative
    if shock > 0.2:
        pan = pan + (1 - 2 * pan) * 0.9 * shock
    g = np.zeros((H, W), np.float32)
    g[PY:PY + PH, PX:PX + PW] = np.clip(pan, 0, 1)
    g += frames + draw_stars(t) * (1 - inpanel)
    img = np.repeat(g[..., None], 3, axis=2)
    pulse = 0.55 + 0.22 * np.sin(TAU * 2 * t / LOOP + 0.6) + 0.55 * bump(t, 10.5, 0.35)
    glow = (glow_ring * inpanel * 0.30 + glow_out * (1 - inpanel)) * pulse
    img = 1 - (1 - img) * (1 - glow[..., None] * RED)          # screen blend
    draw_particles(img, t)
    if 0.2 < bump(t, 10.42, 0.09):                            # the panel jolts
        img = np.roll(img, (int(3 * np.sin(i * 2.1)), int(2 * np.cos(i * 1.7))), axis=(0, 1))
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


if a.preview:
    os.makedirs(a.preview, exist_ok=True)
    for i in (0, int(3 * FPS), int(7 * FPS), int(10.42 * FPS), int(13 * FPS)):
        cv2.imwrite(os.path.join(a.preview, f'{i:04d}.png'), cv2.cvtColor(frame(i), cv2.COLOR_RGB2BGR))
    sys.exit(0)

out = sys.stdout.buffer
for i in range(N):
    out.write(frame(i).tobytes())
    if i % 48 == 0:
        print(f'  remina frame {i}/{N}', file=sys.stderr)
