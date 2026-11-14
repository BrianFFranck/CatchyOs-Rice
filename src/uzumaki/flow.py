"""Endless inward flow of the Uzumaki hair spiral, made from the drawing's own ink.

For every pixel p of the spiral dome we know its ring phase Phi(p) (phasefield.py:
Phi grows by 1 per ring going outward, ink lines sit on integer values).
Frame at shift d (0 <= d < 1):
    layer A = the drawing sampled where Phi = Phi(p) + d      (content pulled inward)
    layer B = the drawing sampled where Phi = Phi(p) + d - 1  (the same, one ring further in)
    frame   = variance-preserving blend of A and B with weight d
At d = 0 the frame is exactly the drawing, at d -> 1 it is exactly the drawing again, so the
spiral sinks into itself forever without a seam. A and B always sample the *same* ring phase,
so the ink lines stay sharp; only the strand hatching cross-fades.
"""
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter


def _wrap(x):
    return x - np.round(x)


class SpiralFlow:
    def __init__(self, gray, phase, dome, core=None, offset=(0, 0), step=0.2):
        """gray, phase, dome: float32 arrays of the same (cropped) size.
        core: ((x, y), r0, r1, hand) the drawn spiral's centre, the radius up to which it is
        simply rotated (blending out by r1) and its turning direction; offset: crop origin."""
        self.g = gray.astype(np.float32)
        self.ph = phase.astype(np.float32)
        # Phi jumps by 1 across the spiral's branch cut: interpolate it as a unit vector
        self.pc = np.cos(2 * np.pi * phase).astype(np.float32)
        self.ps = np.sin(2 * np.pi * phase).astype(np.float32)
        self.dome = dome.astype(np.float32)
        H, W = gray.shape
        self.H, self.W = H, W
        # continuous phase gradient (the spiral's branch cut makes Phi jump by 1, so take the
        # gradient of exp(2*pi*i*Phi) instead of Phi itself)
        z = np.exp(2j * np.pi * self.ph.astype(np.float64))
        zy, zx = np.gradient(z)
        gx = (np.conj(z) * zx).imag / (2 * np.pi)
        gy = (np.conj(z) * zy).imag / (2 * np.pi)
        gx = gaussian_filter(gx, 1.5)
        gy = gaussian_filter(gy, 1.5)
        mag = np.hypot(gx, gy) + 1e-6
        self.nx = (gx / mag).astype(np.float32)
        self.ny = (gy / mag).astype(np.float32)
        self.spacing = (1.0 / mag).astype(np.float32)          # px per ring
        # pixels we may sample from: inside the dome, away from its rim and the eyeball
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self.valid = cv2.erode((dome > 0.5).astype(np.uint8), k).astype(np.float32)
        self.step = step
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.px, self.py = xx, yy
        self.core = None
        if core is not None:
            (ccx, ccy), r0, r1, hand = core
            self.core_c = (ccx - offset[0], ccy - offset[1])
            self.core_hand = hand
            r = np.hypot(xx - self.core_c[0], yy - self.core_c[1])
            k = np.clip((r1 - r) / (r1 - r0), 0, 1)
            self.core = (k * k * (3 - 2 * k)).astype(np.float32)

    def _s(self, a, x, y):
        return cv2.remap(a, x, y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    def _err(self, qx, qy, target):
        """Wrapped phase error Phi(q) - target, safe across the branch cut."""
        c = self._s(self.pc, qx, qy); s = self._s(self.ps, qx, qy)
        a = 2 * np.pi * target
        return np.arctan2(s * np.cos(a) - c * np.sin(a), c * np.cos(a) + s * np.sin(a)) / (2 * np.pi)

    def _newton(self, qx, qy, target, iters=2):
        for _ in range(iters):
            e = self._err(qx, qy, target)
            sp = self._s(self.spacing, qx, qy)
            qx = qx - self._s(self.nx, qx, qy) * e * sp
            qy = qy - self._s(self.ny, qx, qy) * e * sp
        return qx, qy

    def _march(self, qx, qy, base, frm, to):
        """Move points from phase base+frm to base+to in small steps along the gradient."""
        n = max(1, int(np.ceil(abs(to - frm) / self.step)))
        for i in range(1, n + 1):
            d = frm + (to - frm) * i / n
            ds = (to - frm) / n
            sp = self._s(self.spacing, qx, qy)
            qx = qx + self._s(self.nx, qx, qy) * ds * sp
            qy = qy + self._s(self.ny, qx, qy) * ds * sp
            qx, qy = self._newton(qx, qy, base + d)
        return qx, qy

    def _ok(self, qx, qy, target):
        inside = (qx >= 1) & (qx < self.W - 2) & (qy >= 1) & (qy < self.H - 2)
        v = self._s(self.valid, qx, qy) > 0.99
        err = np.abs(self._err(qx, qy, target)) < 0.06
        notcore = self._s(self.spacing, qx, qy) > 2.2   # the vanishing point itself
        return inside & v & err & notcore

    def maps(self, d):
        """Sample positions for targets d, d-1, d-2, d-3 plus validity."""
        base = self.ph
        out = []
        qx, qy = self.px.copy(), self.py.copy()
        qx, qy = self._march(qx, qy, base, 0.0, d)
        out.append((qx, qy, self._ok(qx, qy, base + d)))
        prev = d
        for k in (1, 2, 3):
            qx, qy = self._march(qx, qy, base, prev, d - k)
            prev = d - k
            out.append((qx, qy, self._ok(qx, qy, base + d - k)))
        return out

    def frame(self, d):
        m = self.maps(d)
        g = self.g

        def pick(options):
            x = self.px.copy(); y = self.py.copy(); done = np.zeros(g.shape, bool)
            for qx, qy, ok in options:
                take = ok & ~done
                x[take] = qx[take]; y[take] = qy[take]; done |= take
            return x, y, done

        ax, ay, adone = pick(m[0:3])
        bx, by, bdone = pick(m[1:4])
        # near the vanishing point B has nowhere to go: let it follow A
        bx = np.where(bdone, bx, ax); by = np.where(bdone, by, ay)
        A = self._s(g, ax, ay)
        B = self._s(g, bx, by)
        w = d
        mix = (1 - w) * A + w * B
        mu = gaussian_filter(mix, 2.0)
        norm = np.sqrt((1 - w) ** 2 + w ** 2)
        out = mu + (mix - mu) / norm
        # the drawing is nearly pure ink: pull mid-blend greys back towards black/white
        k = 4 * w * (1 - w)
        if k > 0:
            ink = np.clip((out - 0.15) / 0.7, 0, 1); ink = ink * ink * (3 - 2 * ink)
            out = out + 0.55 * k * (ink - out)
        if self.core is not None:
            # the tight curl at the vanishing point: a plain rotation about the drawn centre
            # (one revolution per ring, so d = 1 is the identity again; no cross-fade needed)
            cx0, cy0 = self.core_c
            b = self.core_hand * 2 * np.pi * d
            dx, dy = self.px - cx0, self.py - cy0
            cx = (cx0 + dx * np.cos(b) - dy * np.sin(b)).astype(np.float32)
            cy = (cy0 + dx * np.sin(b) + dy * np.cos(b)).astype(np.float32)
            C = self._s(g, cx, cy)
            out = self.core * C + (1 - self.core) * out
        return np.clip(out, 0, 1)
