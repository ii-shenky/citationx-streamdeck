#!/usr/bin/env python3
"""Cut a toggle sheet (3 toggles on a transparent/keyed background: up, mid, down,
left to right) into Stream Deck images c750_toggle_<type>_{up,mid,down,on,off}.png.

Canvas 127x257, nut centre at (63,125); all types share one nut size so they match.
Usage: python3 tools/cut_toggles.py sheet.png <type> <outdir> [--nut 92]
"""
import sys, argparse
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

W, H, PX, PY = 127, 257, 63, 125

def load_alpha(path):
    im = Image.open(path).convert('RGBA')
    a = np.array(im).astype(np.float64)
    if a[..., 3].min() == 255:            # no alpha: key out a flat magenta background
        rgb = a[..., :3]
        k = np.median(np.concatenate([rgb[:20, :20].reshape(-1, 3), rgb[-20:, -20:].reshape(-1, 3)]), 0)
        mag = np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]          # "magenta-ness"
        km = min(k[0], k[2]) - k[1]
        alpha = np.clip((km - 12 - mag) / (km - 70), 0, 1)                # bg -> 0, object -> 1
        safe = np.maximum(alpha, 1e-3)[..., None]
        a[..., :3] = np.clip((rgb - (1 - alpha[..., None]) * k) / safe, 0, 255)   # remove magenta spill
        a[..., 3] = alpha * 255
    return a

def components(a):
    m = a[..., 3] > 128
    lab, n = nd.label(m)
    sizes = nd.sum(m, lab, range(1, n + 1))
    keep = sorted(np.argsort(sizes)[::-1][:3] + 1)
    objs = nd.find_objects(lab)
    comps = [(objs[k - 1], lab == k) for k in keep]
    return sorted(comps, key=lambda c: c[0][1].start)   # left to right

def render(a, comp, sl, pivot, scale):
    mask = nd.binary_fill_holes(comp)
    rgba = a.copy()
    al = np.where(mask, np.clip((rgba[..., 3] - 100) * 255 / 140, 0, 255), 0)   # solid inside, crisp edge
    rgba[..., 3] = al
    pre = rgba.copy(); pre[..., :3] *= al[..., None] / 255.0            # premultiply for clean resize
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    crop = Image.fromarray(pre[y0:y1, x0:x1].clip(0, 255).astype(np.uint8), 'RGBA')
    w, h = max(1, round((x1 - x0) * scale)), max(1, round((y1 - y0) * scale))
    small = np.array(crop.resize((w, h), Image.LANCZOS)).astype(np.float64)
    out = np.zeros((H, W, 4))
    ox, oy = round(PX - (pivot[0] - x0) * scale), round(PY - (pivot[1] - y0) * scale)
    ys, xs = slice(max(0, oy), min(H, oy + h)), slice(max(0, ox), min(W, ox + w))
    out[ys, xs] = small[ys.start - oy:ys.stop - oy, xs.start - ox:xs.stop - ox]
    clipped = (oy < 0) or (ox < 0) or (oy + h > H) or (ox + w > W)
    alpha = out[..., 3:4]
    out[..., :3] = np.where(alpha > 0, out[..., :3] * 255.0 / np.maximum(alpha, 1), 0)
    out[..., 3] = np.where(out[..., 3] < 8, 0, out[..., 3])
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA'), clipped

def indicator(img, lit):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([96, 6, 123, 33], radius=4, fill=(20, 20, 20, 255))
    d.rounded_rectangle([99, 9, 120, 30], radius=2,
                        fill=(236, 226, 196, 255) if lit else (62, 66, 70, 255))
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet'); ap.add_argument('type'); ap.add_argument('outdir')
    ap.add_argument('--nut', type=float, default=92, help='nut height in px on the canvas')
    o = ap.parse_args()
    a = load_alpha(o.sheet)
    (s_up, c_up), (s_mid, c_mid), (s_dn, c_dn) = components(a)
    nut_h = s_mid[0].stop - s_mid[0].start
    r = nut_h / 2
    piv_mid = ((s_mid[1].start + s_mid[1].stop) / 2, (s_mid[0].start + s_mid[0].stop) / 2)
    piv_up = ((s_up[1].start + s_up[1].stop) / 2, s_up[0].stop - r)       # nut is the bottom of "up"
    piv_dn = ((s_dn[1].start + s_dn[1].stop) / 2, s_dn[0].start + r)      # nut is the top of "down"
    scale = o.nut / nut_h
    res = {}
    for name, sl, comp, piv in [('up', s_up, c_up, piv_up), ('mid', s_mid, c_mid, piv_mid), ('down', s_dn, c_dn, piv_dn)]:
        img, clipped = render(a, comp, sl, piv, scale)
        if clipped:
            print(f'WARNING: {name} does not fit the canvas at --nut {o.nut}; use a smaller value')
        res[name] = img
    res['on'] = indicator(res['up'].copy(), True)
    res['off'] = indicator(res['down'].copy(), False)
    for k, img in res.items():
        p = f'{o.outdir}/c750_toggle_{o.type}_{k}.png'
        img.save(p)
        al = np.array(img)[..., 3]
        print(p, img.size, 'semi-transparent px:', int(((al > 0) & (al < 255)).sum()))

if __name__ == '__main__':
    main()
