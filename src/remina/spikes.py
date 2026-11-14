"""Second-pass mask: the thin spike strokes of the balloons that survive pass 1.
usage: spikes.py pass1.png body-mask.png out-mask.png"""
import cv2, numpy as np, sys
img = cv2.imread(sys.argv[1], 0).astype(np.float32)
body = cv2.imread(sys.argv[2], 0) > 127
ring = cv2.dilate(body.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (81, 81))) > 0
med = cv2.medianBlur(img.astype(np.uint8), 21).astype(np.float32)
dark = (med - img) > 22
light = (img - med) > 30
m = (dark | light) & ring & ~body
m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
m = m | cv2.dilate(body.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
cv2.imwrite(sys.argv[3], m * 255)
