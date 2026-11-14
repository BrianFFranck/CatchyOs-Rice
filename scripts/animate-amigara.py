#!/usr/bin/env python3
"""Desktop 5 wallpaper: 穴 The Enigma of Amigara Fault.

A torch searches a dark rock face covered in human-shaped holes; dust hangs in the beam and
for a few seconds the light stops on one hole: yours. Raw 8-bit grey 1920x1080 frames go to
stdout (pipe into ffmpeg, see build-desktops.sh). Seamless 16 s loop.
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
rng = np.random.default_rng(1990)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def noise(shape, sigma, seed):
    g = gaussian_filter(np.random.default_rng(seed).standard_normal(shape).astype(np.float32), sigma)
    return g / (g.std() + 1e-6)


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# ------------------------------------------------------------------ the rock face
warp = noise((H, W), 60, 1) * 18
strata = np.sin((yy + 0.18 * xx + warp) * 0.052) * 0.5 + np.sin((yy + 0.21 * xx + warp * 1.6) * 0.017) * 0.5
grain = noise((H, W), 1.2, 2) * 0.5 + noise((H, W), 3.0, 3) * 0.6 + noise((H, W), 9, 4) * 0.8
ridge = 1 - np.abs(noise((H, W), 5, 5))                     # cracks: ridged noise
cracks = smooth((ridge - 0.93) / 0.06)
# sedimentary layers: each band its own tone, thin dark seams between them
lay = (yy + 0.17 * xx + warp) / 34.0
band = np.floor(lay)
tones = np.random.default_rng(9).uniform(-1, 1, 400).astype(np.float32)
btone = tones[(band.astype(int) % 400)]
seam = smooth(1 - np.abs(lay - np.round(lay)) / 0.06)
rock = 0.47 + 0.075 * btone + 0.03 * strata + 0.035 * grain - 0.22 * seam * smooth(noise((H, W), 14, 8) + 0.3) - 0.30 * cracks
# chisel marks: short diagonal tool strokes
tool = smooth((np.sin((xx * 0.8 + yy * 0.6) * 0.9 + noise((H, W), 2, 6) * 2) - 0.86) / 0.1) * smooth(noise((H, W), 25, 7))
rock -= 0.08 * tool
rock = np.clip(rock, 0.05, 0.9).astype(np.float32)

# ------------------------------------------------------------------ the holes
# joints: head(cx,cy,r), neck, hips, l/r shoulder->elbow->hand, l/r hip->knee->foot
POSES = {
    'still':  dict(arms=[((-.13, .25), (-.17, .48), (-.16, .70)), ((.13, .25), (.17, .48), (.16, .70))],
                   legs=[((-.06, .62), (-.07, .85), (-.07, 1.08)), ((.06, .62), (.07, .85), (.07, 1.08))]),
    'raised': dict(arms=[((-.12, .24), (-.20, .05), (-.24, -.17)), ((.12, .24), (.20, .05), (.24, -.17))],
                   legs=[((-.06, .62), (-.09, .85), (-.10, 1.08)), ((.06, .62), (.08, .86), (.09, 1.08))]),
    'reach':  dict(arms=[((-.12, .24), (-.20, .05), (-.22, -.18)), ((.13, .25), (.20, .47), (.27, .66))],
                   legs=[((-.06, .62), (-.15, .83), (-.20, 1.05)), ((.06, .62), (.12, .85), (.15, 1.07))]),
    'broken': dict(arms=[((-.12, .25), (-.32, .30), (-.28, .55)), ((.13, .25), (.30, .18), (.42, .30))],
                   legs=[((-.06, .62), (-.17, .78), (-.05, .98)), ((.06, .62), (.20, .80), (.30, 1.02))]),
    'long':   dict(arms=[((-.11, .24), (-.13, .55), (-.12, .88)), ((.11, .24), (.13, .55), (.12, .88))],
                   legs=[((-.05, .66), (-.05, 1.0), (-.05, 1.32)), ((.05, .66), (.05, 1.0), (.05, 1.32))]),
}
# x, y (head top), height px, rotation deg, pose, stretch
HOLES = [
    (300, 140, 300, -6, 'still', 1.25), (560, 330, 250, 5, 'raised', 1.1), (1110, 120, 270, 9, 'broken', 1.15),
    (1350, 420, 320, -4, 'reach', 1.2), (1640, 120, 260, 3, 'long', 1.0), (170, 610, 260, 8, 'broken', 1.1),
    (1560, 650, 300, -9, 'raised', 1.2), (1810, 380, 230, 6, 'still', 1.3), (470, 760, 230, -3, 'long', 1.0),
    (1220, 790, 220, 11, 'still', 1.15), (40, 200, 240, 0, 'reach', 1.2),
    (845, 330, 400, -2, 'still', 1.35),           # yours
]
MINE = HOLES[-1]
SS = 2                                             # draw at 2x for smooth edges
hole_hi = np.zeros((H * SS, W * SS), np.uint8)


def P(x, y, h, rot, st, pt):
    c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
    px, py = pt[0] * h, pt[1] * h * st
    return (int((x + c * px - s * py) * SS), int((y + s * px + c * py) * SS))


for (x, y, h, rot, pose, st) in HOLES:
    p = POSES[pose]
    f = lambda pt: P(x, y, h, rot, st, pt)
    th = h * SS
    cv2.ellipse(hole_hi, f((0, .085)), (int(h * .066 * SS), int(h * .082 * st * SS)), rot, 0, 360, 255, -1)
    torso = np.array([f((-.15, .215)), f((-.07, .19)), f((.07, .19)), f((.15, .215)), f((.125, .33)),
                      f((.10, .46)), f((.115, .60)), f((.09, .67)), f((-.09, .67)), f((-.115, .60)),
                      f((-.10, .46)), f((-.125, .33))])
    cv2.fillPoly(hole_hi, [torso], 255)
    cv2.line(hole_hi, f((0, .13)), f((0, .22)), 255, int(th * 0.06))
    for limb in p['arms']:
        cv2.line(hole_hi, f(limb[0]), f(limb[1]), 255, int(th * 0.072))
        cv2.line(hole_hi, f(limb[1]), f(limb[2]), 255, int(th * 0.056))
        cv2.ellipse(hole_hi, f(limb[2]), (int(th * .032), int(th * .045)), rot, 0, 360, 255, -1)
    for limb in p['legs']:
        cv2.line(hole_hi, f(limb[0]), f(limb[1]), 255, int(th * 0.10))
        cv2.line(hole_hi, f(limb[1]), f(limb[2]), 255, int(th * 0.072))
        cv2.ellipse(hole_hi, f(limb[2]), (int(th * .04), int(th * .025)), rot, 0, 360, 255, -1)
# soften every joint into one carved outline
hole_hi = ((cv2.GaussianBlur(hole_hi, (0, 0), 7) > 120) * 255).astype(np.uint8)
hole = cv2.resize(hole_hi, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
inner = cv2.distanceTransform((hole > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
outer = cv2.distanceTransform((hole <= 0.5).astype(np.uint8), cv2.DIST_L2, 5)
# deep inside: black; a lit inner wall a few px wide; a shadowed lip just outside
depth = np.exp(-inner / 2.6) * 0.5
lip = 0.55 + 0.45 * smooth(outer / 7.0)
wall = rock * lip * (1 - hole) + rock * depth * hole
# the inner wall catches light from the lower right more than the upper left
gy, gx = np.gradient(gaussian_filter(hole, 2.0))
wall += hole * np.clip(-(gx * 0.6 + gy * 0.8) * 9, 0, 0.22) * np.exp(-inner / 2.5)
wall = np.clip(wall, 0, 1).astype(np.float32)

# ------------------------------------------------------------------ the torch
MX, MY = MINE[0], MINE[1] + MINE[2] * 0.45 * MINE[5]


def torch(t):
    ph = TAU * t / LOOP
    x = 960 + 600 * np.sin(ph + 0.4) + 90 * np.sin(3 * ph)
    y = 520 + 250 * np.sin(2 * ph + 1.2) + 60 * np.cos(5 * ph)
    stay = smooth((t - 8.6) / 1.2) * (1 - smooth((t - 12.4) / 1.4))   # it stops on your hole
    x = x + (MX - x) * stay
    y = y + (MY - y) * stay
    rad = 300 + 40 * stay
    shake = np.array([np.sin(t * 13.1) + np.sin(t * 7.3), np.cos(t * 11.7) + np.sin(t * 5.9)]) * 2.0
    return x + shake[0], y + shake[1], rad, stay


# dust in the air
ND = 520
dx0 = rng.uniform(0, W, ND); dy0 = rng.uniform(0, H, ND)
dax = rng.uniform(10, 60, ND); day = rng.uniform(10, 50, ND)
dk = rng.integers(1, 3, ND); dp = rng.uniform(0, TAU, ND); db = rng.uniform(0.2, 0.7, ND)
hatch = (smooth((np.sin((xx - yy) * 0.62) - 0.55) / 0.3)).astype(np.float32)


def frame(i):
    t = i / FPS
    tx, ty, rad, stay = torch(t)
    d = np.hypot((xx - tx) / 1.08, yy - ty)
    beam = np.exp(-(d / rad) ** 2.4) * (1.05 + 0.04 * np.sin(t * 31) * np.sin(t * 17))
    halo = np.exp(-(d / (rad * 2.6)) ** 2) * 0.10
    light = 0.035 + beam * 0.95 + halo
    img = wall * light
    # manga screen: diagonal hatching in the half-lit falloff of the beam
    mid = smooth((light - 0.12) / 0.2) * (1 - smooth((light - 0.6) / 0.25))
    img = img * (1 - 0.35 * hatch * mid)
    # dust
    xs = (dx0 + dax * np.sin(TAU * dk * t / LOOP + dp)) % W
    ys = (dy0 + day * np.sin(TAU * dk * t / LOOP + dp * 1.7) - 30 * np.sin(TAU * t / LOOP)) % H
    dl = np.exp(-(np.hypot((xs - tx) / 1.08, ys - ty) / rad) ** 2.4)
    dust = np.zeros((H, W), np.float32)
    np.add.at(dust, (ys.astype(int), xs.astype(int)), db * dl)
    img = img + gaussian_filter(dust, 0.8) * 2.5
    # a breath of cold air from your hole while the light rests on it
    img = img * (1 - 0.06 * stay * np.exp(-((xx - MX) ** 2 + (yy - MY) ** 2) / (2 * 260 ** 2)) * np.sin(TAU * 3 * t / LOOP) ** 2)
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


if a.preview:
    os.makedirs(a.preview, exist_ok=True)
    for t in (2.0, 6.0, 10.5, 14.0):
        cv2.imwrite(os.path.join(a.preview, f'ami-{t:04.1f}.png'), frame(int(t * FPS)))
    cv2.imwrite(os.path.join(a.preview, 'ami-wall.png'), (wall * 255).astype(np.uint8))
    sys.exit(0)

o = sys.stdout.buffer
for i in range(N):
    o.write(frame(i).tobytes())
    if i % 48 == 0:
        print(f'  amigara frame {i}/{N}', file=sys.stderr)
