#!/usr/bin/env python3
"""Desktop 2 wallpaper: the Uzumaki girl whose hair spiral sinks into itself forever.

Writes raw 8-bit grey 1920x1080 frames to stdout (pipe into ffmpeg, see build-desktops.sh).
  * the hair spiral flows endlessly inward, built from the drawing's own ink (src/uzumaki/flow.py)
  * the eyeball in her hair rolls twice per loop
  * faint inked rings in the dark drift in towards her head
Every periodic term divides LOOP, so the last frame runs straight into the first.
"""
import argparse, json, os, sys
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src', 'uzumaki'))
from phasefield import build          # noqa: E402
from flow import SpiralFlow           # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('src')
ap.add_argument('--fps', type=int, default=24)
ap.add_argument('--loop', type=float, default=16)
ap.add_argument('--rings', type=int, default=3, help='rings that sink per loop')
ap.add_argument('--preview', help='write a few PNG frames to this dir instead of streaming')
a = ap.parse_args()

W, H = 1920, 1080
FPS, LOOP = a.fps, a.loop
N = int(round(FPS * LOOP))

src = cv2.imread(a.src, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
params = json.load(open(os.path.join(HERE, '..', 'src', 'uzumaki', 'phase-params.json')))
ph, rho, dome = build(src, params)

# ---------------------------------------------------------------- the spiral (source pixels)
X0, Y0, X1, Y1 = 400, 530, 800, 930
crop = lambda img: img[Y0:Y1, X0:X1]
flow = SpiralFlow(crop(src), crop(ph), crop(dome), core=((709, 822), 22, 34, 1), offset=(X0, Y0))
feather = gaussian_filter(cv2.erode(crop(dome), np.ones((3, 3), np.uint8)), 2.0)

# ---------------------------------------------------------------- the eyeball in her hair
EX, EY, ER = 638, 865, 43
gy, gx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
er = np.hypot(gx - EX, gy - EY)
eye_w = np.clip((ER - er) / 4.0, 0, 1).astype(np.float32)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def eye_angle(t):
    """Degrees. A slow glance at 4.6 s, a nervous twitch around 12.2 s."""
    g = smooth((t - 4.6) / 0.5) - smooth((t - 6.9) / 0.7)              # look aside and back
    tw = np.exp(-((t - 12.2) / 0.12) ** 2) - 0.7 * np.exp(-((t - 12.55) / 0.1) ** 2)
    return 14 * g + 9 * tw


def eye_roll(img, t):
    ang = np.deg2rad(eye_angle(t))
    if abs(ang) < 1e-4:
        return img
    c, s = np.cos(ang), np.sin(ang)
    dx, dy = gx - EX, gy - EY
    sx = (EX + c * dx + s * dy - X0).astype(np.float32)
    sy = (EY - s * dx + c * dy - Y0).astype(np.float32)
    rolled = cv2.remap(img, sx, sy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return eye_w * rolled + (1 - eye_w) * img


# ---------------------------------------------------------------- layout (same as Tomie's)
TX, TY, TW, TH = 147, 413, 847, 1210            # framed art inside the phone-sized source
PH = 960
PW = int(round(TW * PH / TH))
PX, PY = (W - PW) // 2, (H - PH) // 2
S = PH / TH
CX, CY = PX + (709 - TX) * S, PY + (822 - TY) * S   # spiral centre on screen

# background: hand-inked rings converging on her head (log-spaced, a tunnel into the spiral)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx - CX, yy - CY) + 1e-3
th = np.arctan2(yy - CY, xx - CX)
rr = r + 4.0 * np.sin(9 * th + r / 37) + 2.2 * np.sin(23 * th + r / 61)
g_bg = (np.log(np.maximum(rr, 1.0) / 60.0) / np.log(1.32)).astype(np.float32)
panel = np.zeros((H, W), np.float32)
cv2.rectangle(panel, (PX - 20, PY - 20), (PX + PW + 20, PY + PH + 20), 1.0, -1)
bg_mask = (1 - gaussian_filter(panel, 55)) * np.clip(1.15 - r / 1400, 0.35, 1) * np.clip((r - 40) / 200, 0, 1)
bg_mask = bg_mask.astype(np.float32)


def frame(i):
    t = i / FPS
    d = (a.rings * i / N) % 1.0
    art = src.copy()
    sp = flow.frame(d)
    region = feather * sp + (1 - feather) * crop(src)
    region = eye_roll(region, t)
    art[Y0:Y1, X0:X1] = region
    panel_img = cv2.resize(art[TY:TY + TH, TX:TX + TW], (PW, PH), interpolation=cv2.INTER_AREA)
    panel_img = cv2.filter2D(panel_img, -1, np.array([[0, -0.12, 0], [-0.12, 1.48, -0.12], [0, -0.12, 0]], np.float32))
    # rings: two ring-periods per loop, drifting inwards
    ph_bg = g_bg + 2.0 * i / N
    bg = np.power(0.5 + 0.5 * np.cos(2 * np.pi * ph_bg), 9) * bg_mask * 0.20
    out = bg
    out[PY:PY + PH, PX:PX + PW] = np.maximum(out[PY:PY + PH, PX:PX + PW], np.clip(panel_img, 0, 1))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


if a.preview:
    os.makedirs(a.preview, exist_ok=True)
    for i in (0, N // 8, N // 6, N // 4, int(4.6 * FPS + 14), int(12.2 * FPS)):
        cv2.imwrite(os.path.join(a.preview, f'{i:04d}.png'), frame(i))
    sys.exit(0)

out = sys.stdout.buffer
for i in range(N):
    out.write(frame(i).tobytes())
    if i % 48 == 0:
        print(f'  uzumaki frame {i}/{N}', file=sys.stderr)
