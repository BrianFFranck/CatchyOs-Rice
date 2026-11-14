"""Builds the exact per-pixel ring phase of the hair spiral: the fitted smooth model plus a
locally demodulated correction, so phase lines sit exactly on the drawn rings."""
import cv2, numpy as np, json
from scipy.ndimage import gaussian_filter
from spiralmodel import phase

POLY = np.array([(565,567),(640,560),(700,573),(750,603),(768,660),(770,745),(764,795),
                 (754,833),(733,862),(690,875),(640,905),(590,880),(560,872),(500,842),(450,802),
                 (430,750),(428,685),(445,635),(480,595),(525,572)], np.int32)
EYE = (638, 866, 50)

def dome_mask(H, W):
    m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [POLY], 1.0)
    yy, xx = np.mgrid[0:H, 0:W]
    m[(xx-EYE[0])**2 + (yy-EYE[1])**2 < (EYE[2]+4)**2] = 0
    return m

def build(gray, params, sigma=10.0):
    H, W = gray.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    ph0, rho = phase(params, xx, yy)
    m = dome_mask(H, W)
    I = gaussian_filter(gray, 1.0)
    mu = gaussian_filter(I*m, 6) / np.maximum(gaussian_filter(m, 6), 1e-3)
    z = (I - mu) * m * np.exp(-2j*np.pi*ph0)
    zs = gaussian_filter(z.real, sigma) + 1j*gaussian_filter(z.imag, sigma)
    w = gaussian_filter(m, sigma)
    # where the mask is absent fall back to the dome's mean offset
    zmean = zs[m > 0].mean()
    zz = np.where(w > 0.05, zs / np.maximum(w, 1e-3), zmean)
    e = np.angle(zz) / (2*np.pi)
    ph = ph0 + e   # bright ink line at integer phase
    return ph.astype(np.float32), rho.astype(np.float32), m
