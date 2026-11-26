#!/usr/bin/env python3
"""Cut a round knob (pointer up, on a flat magenta or transparent background) into
rotated Stream Deck images. Canvas 144x144, axis in the centre.
Usage: python3 tools/cut_knob.py knob.png <outdir> <prefix> name:angle [name:angle ...]
       e.g. ... c750_xfeed l:-60 off:0 r:60   (angle in degrees, clockwise)
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, __import__('os').path.dirname(__file__))
from cut_toggles import load_alpha

SIZE, DIAM = 144, 136

def main():
    src, outdir, prefix, *specs = sys.argv[1:]
    a = load_alpha(src)
    m = a[..., 3] > 128
    lab, n = nd.label(m)
    k = np.argmax(nd.sum(m, lab, range(1, n + 1))) + 1
    mask = nd.binary_fill_holes(lab == k)
    a[..., 3] = np.where(mask, np.clip((a[..., 3] - 100) * 255 / 140, 0, 255), 0)
    ys, xs = np.nonzero(mask)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    r = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 + 2
    crop = a[int(cy - r):int(cy + r), int(cx - r):int(cx + r)].copy()
    crop[..., :3] *= crop[..., 3:4] / 255.0                      # premultiply
    big = Image.fromarray(crop.clip(0, 255).astype(np.uint8), 'RGBA')
    for spec in specs:
        name, ang = spec.split(':')
        rot = big.rotate(-float(ang), resample=Image.BICUBIC)     # PIL rotates counter-clockwise
        small = np.array(rot.resize((DIAM, DIAM), Image.LANCZOS)).astype(np.float64)
        out = np.zeros((SIZE, SIZE, 4)); o = (SIZE - DIAM) // 2
        out[o:o + DIAM, o:o + DIAM] = small
        al = out[..., 3:4]
        out[..., :3] = np.where(al > 0, out[..., :3] * 255.0 / np.maximum(al, 1), 0)
        out[..., 3] = np.where(out[..., 3] < 8, 0, out[..., 3])
        p = f'{outdir}/{prefix}_{name}.png'
        Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA').save(p)
        print(p)

if __name__ == '__main__':
    main()
