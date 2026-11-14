#!/usr/bin/env python3
"""
Animate Tomie's portrait frame by frame (cut-out / puppet animation).

  * the fake face she holds peels slightly away from her real face along the torn
    seam: the gap opens into shadow and threads of skin stretch across it (some snap),
    then the face snaps back onto her during the glitch twitch at 11.4 s
  * the fake face's two eyes roll on their own (up into the lid, around, darting)
  * the fake face breathes (swells, its mouth gapes) out of step with Tomie, who
    breathes slowly herself (head and shoulders rise)

Everything is periodic over LOOP seconds, so the last frame flows into the first.

usage: animate-tomie.py PORTRAIT.png OUT_DIR [--fps 24] [--loop 16] [--preview DIR]
PORTRAIT is the processed grey portrait from build-assets.sh (467x960, made from the
451x927 original, so every coordinate below is in original-image pixels).
"""
import argparse
import math
import os

import cv2
import numpy as np
from scipy import ndimage

SRC_W, SRC_H = 451, 927          # coordinates below are in this space
SS = 2                           # supersampling factor for all the drawing

# ------------------------------------------------------------------ the fake face
MASK_POLY = [  # outline of the fake face, traced by hand; right side = torn seam
    (104, 345), (108, 325), (118, 312), (132, 296), (141, 289), (152, 295), (156, 316),
    (166, 329), (180, 338), (196, 341), (212, 340), (220, 346), (216, 356), (221, 366),
    (215, 376), (220, 386), (214, 396), (198, 397), (182, 393), (166, 392), (152, 393),
    (140, 393), (128, 392), (112, 388), (102, 375),
]
SEAM = MASK_POLY[9:18]           # (196,341) … (198,397): where it is still attached
HINGE = (124, 402)               # her fingers: the fake face pivots here, so it never slides
LIFT_DIR = np.array([-0.96, -0.28])   # peel direction: off her cheek, out and a bit up
LIFT_MAX = 11.0                  # px (original space) at the seam, at full peel
MASK_CENTER = (168, 352)
MOUTH = (172, 381)               # the dark gaping hole

EYES = [  # centre, flood-fill seed (on the white, not the old pupil), roll radius, pupil r
    dict(c=(193.5, 356.5), seed=(188, 352), roll=7.0, pupil=2.1, name="big"),
    dict(c=(147.0, 302.5), seed=(146, 298), roll=4.2, pupil=1.4, name="upper"),
]

GLITCH = (11.40, 11.53)          # matches the glitch twitch in build-assets.sh


# ------------------------------------------------------------------ timing helpers
def ease(u):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, u)))


def keys(t, ks):
    """Cosine-interpolated keyframes [(time, value or tuple), …], times ascending."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t0 <= t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return ks[-1][1]


def peel(t, loop):
    p = keys(t, [(0, 0.06), (1.6, 0.06), (7.2, 1.0), (GLITCH[0] - 0.02, 0.9),
                 (GLITCH[0] + 0.06, 0.0), (13.5, 0.03), (loop, 0.06)])
    if 7.2 < t < GLITCH[0]:          # a held breath: the skin trembles under tension
        p += 0.035 * math.sin(2 * math.pi * 6.5 * t) * math.sin(math.pi * (t - 7.2) / (GLITCH[0] - 7.2))
    return p


def big_eye(t, loop):
    """Pupil offset for the big eye, in units of its roll radius (y up is negative)."""
    if 4.6 <= t < 7.0:               # one slow full roll, starting from the top
        a = -math.pi / 2 + 2 * math.pi * ease((t - 4.6) / 2.4)
        r = 0.75
        return (r * math.cos(a), r * math.sin(a))
    ks = [(0, (0.0, 0.0)), (2.4, (0.08, 0.05)), (3.6, (0.0, -1.45)), (4.3, (0.0, -1.45)),
          (4.6, (0.0, -0.75)),
          (7.0, (0.0, -0.75)), (7.25, (-0.7, 0.1)), (7.75, (-0.7, 0.1)), (7.9, (0.65, 0.0)),
          (8.4, (0.65, 0.0)), (8.52, (-0.55, 0.25)), (9.0, (-0.55, 0.25)), (9.1, (0.5, -0.15)),
          (9.5, (0.5, -0.15)), (10.6, (0.0, -1.5)), (GLITCH[0] - 0.01, (0.0, -1.5)),
          (GLITCH[0] + 0.05, (0.0, 0.0)), (loop, (0.0, 0.0))]
    x, y = keys(t, ks)
    if t > GLITCH[1] or t < 2.4:     # staring at you: tiny tremor
        x += 0.05 * math.sin(2 * math.pi * 3 * t)
        y += 0.04 * math.sin(2 * math.pi * 5 * t + 1)
    return (x, y)


def upper_eye(t, loop):
    """Slow ellipse that never lines up with the big eye; rolls up after the glitch."""
    a = 2 * math.pi * t / (loop / 2)
    x, y = 0.55 * math.cos(a), 0.75 * math.sin(a)
    if GLITCH[0] <= t <= 13.6:
        u = ease((t - GLITCH[0]) / 0.4) * (1 - ease((t - 12.6) / 1.0))
        x, y = x * (1 - u), y * (1 - u) - 1.5 * u
    return (x, y)


def mask_breath(t, loop):        # 4 breaths per loop, gasp-like (fast in, slow out)
    ph = (t / (loop / 4)) % 1.0
    return ease(ph / 0.35) if ph < 0.35 else 1 - ease((ph - 0.35) / 0.65)


def body_breath(t, loop):        # 3 slow breaths per loop
    return 0.5 - 0.5 * math.cos(2 * math.pi * t / (loop / 3))


# ------------------------------------------------------------------ rendering
class Animator:
    def __init__(self, portrait_path, loop, fps):
        img = cv2.imread(portrait_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise SystemExit(f"cannot read {portrait_path}")
        self.out_h, self.out_w = img.shape
        self.loop, self.fps = loop, fps
        W, H = self.out_w * SS, self.out_h * SS
        self.W, self.H = W, H
        self.sx, self.sy = W / SRC_W, H / SRC_H
        self.base = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
        self.gx, self.gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        self.rng = np.random.default_rng(1987)

        # fake-face alpha: hard 1px edge at the seam, a little softer elsewhere
        poly = np.array([self.P(p) for p in MASK_POLY], np.int32)
        m = np.zeros((H, W), np.uint8)
        cv2.fillPoly(m, [poly], 255, cv2.LINE_AA)
        self.A0 = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 0.8 * SS)
        # strictly inside the outline: only here can the shadow underneath show
        inner = cv2.erode((m > 127).astype(np.uint8), np.ones((2 * SS + 1, 2 * SS + 1), np.uint8))
        self.H0 = cv2.GaussianBlur(inner.astype(np.float32), (0, 0), 0.5 * SS)

        # how strongly each pixel lifts: 0 at her fingers, 1 at the seam, smooth
        hx, hy = self.P(HINGE)
        seam_pts = np.array([self.P(p) for p in SEAM], np.float32)
        far = np.linalg.norm(seam_pts.mean(0) - (hx, hy))
        d = np.hypot(self.gx - hx, self.gy - hy) / far
        self.lift_w = np.clip(d, 0, 1.15) ** 1.6
        self.lift_w *= cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 6 * SS) * 0.6 + 0.4

        # breathing weight inside the fake face (smooth bump, zero outside)
        self.breath_w = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 9 * SS)
        cx, cy = self.P(MASK_CENTER)
        self.rel = (self.gx - cx, self.gy - cy)
        mx, my = self.P(MOUTH)
        self.mouth_w = np.exp(-(((self.gx - mx) / (15 * self.sx)) ** 2 + ((self.gy - my) / (11 * self.sy)) ** 2))
        self.mouth_rel = (self.gx - mx, self.gy - my)

        # Tomie's breathing: head/shoulders rise, elbows stay put
        y_n = self.gy / H
        self.body_up = np.clip((0.86 - y_n) / 0.36, 0, 1) ** 1.2
        self.body_up = cv2.GaussianBlur(self.body_up, (0, 0), 20 * SS)
        chest = np.exp(-((y_n - 0.62) / 0.12) ** 2)
        self.body_wide = chest * (self.gx - W * 0.52) / W

        self.under = self._underside()
        self._eyes()
        self._strands()

    def P(self, p):
        return (p[0] * self.sx, p[1] * self.sy)

    # what is under the skin: shadow, with raw hatched flesh
    def _underside(self):
        W, H = self.W, self.H
        u = np.full((H, W), 0.015, np.float32)
        hatch = np.zeros((H, W), np.uint8)
        for _ in range(900):
            x = self.rng.uniform(90, 230) * self.sx
            y = self.rng.uniform(285, 400) * self.sy
            ln = self.rng.uniform(3, 9) * self.sy
            a = self.rng.normal(-1.15, 0.25)
            cv2.line(hatch, (int(x), int(y)), (int(x + ln * math.cos(a)), int(y + ln * math.sin(a))),
                     int(self.rng.uniform(40, 120)), 1, cv2.LINE_AA)
        return u + hatch.astype(np.float32) / 255 * 0.2

    def _eyes(self):
        white = (self.base > 0.55).astype(np.uint8)
        for e in EYES:
            sx, sy = self.P(e["seed"])
            lab, _ = ndimage.label(white)
            region = lab == lab[int(sy), int(sx)]
            cx, cy = self.P(e["c"])
            lim = np.hypot((self.gx - cx) / self.sx, (self.gy - cy) / self.sy) < e["roll"] * 1.9
            region &= lim
            region = ndimage.binary_fill_holes(region)          # swallow the old pupil
            region = ndimage.binary_opening(region, iterations=1)
            e["erase"] = cv2.GaussianBlur(region.astype(np.float32), (0, 0), 0.6 * SS)
            clip = ndimage.binary_erosion(region, iterations=SS)  # pupil hides under the lid line
            e["clip"] = cv2.GaussianBlur(clip.astype(np.float32), (0, 0), 0.5 * SS)
            ys, xs = np.nonzero(region)
            e["box"] = (xs.min(), ys.min(), xs.max(), ys.max())

    def _strands(self):
        """Threads of skin across the seam: (anchor on her face, thickness, sag, snap point)."""
        pts = np.array([self.P(p) for p in SEAM], np.float32)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        self.strands = []
        pos = 0.0
        while pos < s[-1]:
            i = min(np.searchsorted(s, pos, side="right") - 1, len(seg) - 1)
            f = (pos - s[i]) / seg[i]
            p = pts[i] * (1 - f) + pts[i + 1] * f
            self.strands.append(dict(
                p=p + self.rng.normal(0, 0.6 * SS, 2),
                w=int(self.rng.choice([2, 2, 3])) * SS // 2,
                sag=self.rng.normal(0, 0.9) * SS,
                snap=self.rng.uniform(0.55, 1.4),       # >1 means it never breaks
                tone=self.rng.uniform(0.7, 0.95),
            ))
            pos += self.rng.uniform(2.2, 5.0) * SS

    def frame(self, t):
        loop = self.loop
        img = self.base.copy()

        # 1. eyes of the fake face: wipe the old pupils, draw rolling ones
        for e, fn in zip(EYES, (big_eye, upper_eye)):
            img = img * (1 - e["erase"]) + e["erase"]
            ox, oy = fn(t, loop)
            cx, cy = self.P(e["c"])
            px, py = cx + ox * e["roll"] * self.sx, cy + oy * e["roll"] * self.sy
            r = e["pupil"] * self.sx
            pupil = np.clip(r + 0.5 - np.hypot(self.gx - px, self.gy - py), 0, 1)
            ring = np.clip(1 - np.abs(np.hypot(self.gx - px, self.gy - py) - r * 1.9) / (0.45 * SS), 0, 1) * 0.55
            ink = np.maximum(pupil, ring) * e["clip"]
            img = img * (1 - ink)

        # 2. the fake face as a warped layer (peel + its own breathing + gaping mouth)
        p = peel(t, loop)
        b = mask_breath(t, loop)
        lift = p * LIFT_MAX * self.lift_w
        dx = LIFT_DIR[0] * lift * self.sx
        dy = LIFT_DIR[1] * lift * self.sy
        k = 0.03 * b * self.breath_w
        dx += self.rel[0] * k
        dy += self.rel[1] * k
        g = 0.6 * b * self.mouth_w
        dx += self.mouth_rel[0] * g * 0.25
        dy += self.mouth_rel[1] * g
        mapx, mapy = (self.gx - dx).astype(np.float32), (self.gy - dy).astype(np.float32)
        img = img.astype(np.float32)
        moved = cv2.remap(img, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        A = cv2.remap(self.A0, mapx, mapy, cv2.INTER_LINEAR)

        # 3. what shows through: shadow under the lifted skin, darkening her cheek too
        under = img * (1 - self.H0) + self.under * self.H0
        gap = self.H0 * (1 - A)
        cheek = cv2.GaussianBlur(gap, (0, 0), 1.2 * SS) * (1 - self.H0)
        under *= 1 - 0.5 * np.clip(cheek * 1.5, 0, 1)

        # 4. threads of skin stretching across the gap (drawn under the lifted edge)
        threads = np.zeros_like(img)
        lift_seam = p * LIFT_MAX
        for st in self.strands:
            x0, y0 = st["p"]
            wv = self.lift_w[int(min(y0, self.H - 1)), int(min(x0, self.W - 1))]
            d = np.array([LIFT_DIR[0] * self.sx, LIFT_DIR[1] * self.sy]) * lift_seam * wv
            length = float(np.hypot(*d))
            if length < 1.2 * SS:
                continue
            frac = 1.0
            if p > st["snap"]:                       # broken: two stubs curl back
                frac = 0.28
            n = 8
            pts_a, pts_b = [], []
            for i in range(n + 1):
                u = i / n
                sag = st["sag"] * math.sin(math.pi * u) * (0.5 + length / (6 * SS))
                nx, ny = -d[1] / length, d[0] / length
                q = (x0 + d[0] * u + nx * sag, y0 + d[1] * u + ny * sag)
                (pts_a if u <= frac else pts_b if u >= 1 - frac else []).append(q)
            for pts in (pts_a, pts_b):
                if len(pts) > 1:
                    cv2.polylines(threads, [np.array(pts, np.float32).round().astype(np.int32)],
                                  False, st["tone"] * min(1.0, length / (3 * SS)), st["w"], cv2.LINE_AA)
        threads = cv2.GaussianBlur(threads, (0, 0), 0.35 * SS)
        under = np.maximum(under, threads)

        comp = under * (1 - A) + moved * A

        # the lifted flap gets an inked edge wherever the gap is next to it
        near_gap = cv2.dilate((gap > 0.3).astype(np.uint8), np.ones((3 * SS, 3 * SS), np.uint8))
        rim = np.clip(A - cv2.erode(A, np.ones((SS + 1, SS + 1), np.uint8)), 0, 1) * near_gap
        comp *= 1 - 0.85 * min(1.0, p * 3) * cv2.GaussianBlur(rim, (0, 0), 0.4 * SS)

        # 5. Tomie breathes: everything above the elbows rises a little
        bb = body_breath(t, loop)
        up = 2.2 * bb * self.sy * self.body_up
        wide = 2.4 * bb * self.sx * self.body_wide
        comp = cv2.remap(comp.astype(np.float32), (self.gx - wide).astype(np.float32),
                         (self.gy + up).astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        out = cv2.resize(comp, (self.out_w, self.out_h), interpolation=cv2.INTER_AREA)
        return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("portrait")
    ap.add_argument("out_dir")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--loop", type=float, default=16)
    ap.add_argument("--only", type=float, nargs="*", help="render just these times (seconds)")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    an = Animator(args.portrait, args.loop, args.fps)
    if args.only:
        for t in args.only:
            cv2.imwrite(os.path.join(args.out_dir, f"t{t:05.2f}.png"), an.frame(t))
        return
    n = int(round(args.loop * args.fps))
    for i in range(n):
        cv2.imwrite(os.path.join(args.out_dir, f"{i:04d}.png"), an.frame(i / args.fps))
        if i % 48 == 0:
            print(f"   frame {i}/{n}", flush=True)


if __name__ == "__main__":
    main()
