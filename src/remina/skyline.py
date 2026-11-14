"""Rebuild the skyline under the 'MORTE A REMINA' balloon from the panel's own buildings.
usage: skyline.py pass2.png seeded.png seam-mask.png"""
import cv2, numpy as np, sys
img = cv2.imread(sys.argv[1], 0)
out = img.copy()
H, W = img.shape
def paste(sx0, sx1, sy0, dx0, flip=False):
    blk = img[sy0:H, sx0:sx1]
    if flip: blk = blk[:, ::-1]
    out[sy0:H, dx0:dx0 + blk.shape[1]] = blk
paste(140, 228, 845, 34)            # two low blocks + the small tower
paste(285, 328, 852, 118, True)     # the windowed block right of the tall tower, mirrored
paste(140, 190, 860, 160, True)
mask = np.zeros_like(img)
mask[690:852, 28:228] = 255                         # sky above the new rooftops
for x in (34, 118, 160, 210):                        # seams between pasted blocks
    mask[845:H, x - 4:x + 4] = 255
# keep the pasted buildings themselves (dark pixels) out of the mask
dark = out < 80
mask[(np.arange(H)[:, None] >= 845) & dark] = 0
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
cv2.imwrite(sys.argv[2], out); cv2.imwrite(sys.argv[3], mask)
