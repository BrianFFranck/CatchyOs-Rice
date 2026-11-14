"""Inpaint with big-lama (TorchScript).  usage: lama.py image mask out [model]
Runs in ~/.local/share/junji-ito-rice/venv-lama (torch CPU + numpy + pillow)."""
import os
import sys

import numpy as np
import torch
from PIL import Image

img_p, mask_p, out_p = sys.argv[1:4]
model_p = sys.argv[4] if len(sys.argv) > 4 else os.path.expanduser('~/.cache/junji-ito-rice/big-lama.pt')
torch.set_num_threads(os.cpu_count() or 4)
model = torch.jit.load(model_p, map_location='cpu').eval()

img = np.asarray(Image.open(img_p).convert('RGB')).astype(np.float32) / 255
mask = (np.asarray(Image.open(mask_p).convert('L')) > 127).astype(np.float32)
H, W = mask.shape
ph, pw = (8 - H % 8) % 8, (8 - W % 8) % 8
it = torch.from_numpy(np.pad(img, ((0, ph), (0, pw), (0, 0)), mode='reflect')).permute(2, 0, 1)[None]
mt = torch.from_numpy(np.pad(mask, ((0, ph), (0, pw)), mode='reflect'))[None, None]
with torch.inference_mode():
    out = model(it, mt)[0].permute(1, 2, 0).numpy()[:H, :W]
out = np.clip(out * 255, 0, 255).astype(np.uint8)
keep = mask[..., None] < 0.5                       # untouched pixels stay bit-exact
out = np.where(keep, (img * 255 + 0.5).astype(np.uint8), out)
Image.fromarray(out).convert('L').save(out_p)
print('ok', out_p)
