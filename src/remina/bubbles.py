"""Mask of the speech bubbles in the Remina panel (pure-white spiky balloons + their text)."""
import cv2, numpy as np, sys
img = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
H, W = img.shape
white = (img > 224).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(white, 8)
zones = [(395, 0, W, 285), (0, 660, 215, 900)]      # x0, y0, x1, y1 of the balloons
mask = np.zeros_like(white)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a < 1500: continue
    cx, cy = x + w / 2, y + h / 2
    if any(z[0] <= cx <= z[2] and z[1] <= cy <= z[3] for z in zones):
        mask[lab == i] = 1
# fill the text holes inside the balloons, then grow over the balloon rim
cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cv2.drawContours(mask, cnts, -1, 1, -1)
mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(sys.argv[4]) if len(sys.argv) > 4 else 13,) * 2))
cv2.imwrite(sys.argv[2], mask * 255)
vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR); vis[mask > 0] = (0.5 * vis[mask > 0] + [0, 0, 120]).astype(np.uint8)
cv2.imwrite(sys.argv[3], vis)
