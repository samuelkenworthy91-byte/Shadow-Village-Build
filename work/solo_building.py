"""Process a single generated building sprite into a transparent WebP asset.

Same gentle cutout as the portraits (adaptive border flood-fill, no
morphological closing, strict near-canvas-only defringe), then normalize to
a fixed height (default 200px, ~2x the on-screen size) keeping aspect
ratio, and save as lossless WebP.

Usage: python3 work/solo_building.py <input.png> <output.webp> [height]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

STRUCT = np.ones((3, 3), bool)

def cutout(rgb: np.ndarray):
    h, w = rgb.shape[:2]
    border = np.concatenate([rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]])
    bmean = border.mean(axis=0)
    dist = np.abs(rgb.astype(int) - bmean).sum(axis=2)
    lum = rgb.mean(axis=2)
    sat = rgb.max(axis=2).astype(int) - rgb.min(axis=2)
    cand = (dist <= 90) | ((lum > 205) & (sat < 30))
    seeds = np.zeros((h, w), bool)
    seeds[0, :] = cand[0, :]; seeds[-1, :] = cand[-1, :]
    seeds[:, 0] = cand[:, 0]; seeds[:, -1] = cand[:, -1]
    bg = seeds.copy()
    while True:
        grown = ndimage.binary_dilation(bg, structure=STRUCT) & cand
        if grown.sum() <= bg.sum():
            break
        bg = grown
    return ~bg

def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    height = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    rgb = np.array(Image.open(src).convert("RGB"))
    mask = cutout(rgb)
    lab, n = ndimage.label(mask, structure=STRUCT)
    if n == 0:
        raise SystemExit("no building detected")
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    order = np.argsort(sizes)[::-1]
    keep = np.zeros_like(mask)
    for k in order:
        if sizes[k] >= 0.05 * sizes[order[0]]:
            keep |= (lab == (k + 1))
    mask = keep

    # strict near-canvas defringe (single pass, 3px)
    arr = np.dstack([rgb, (mask * 255).astype(np.uint8)])
    a = arr[..., 3]
    op = a > 12
    rgb_i = arr[..., :3].astype(int)
    mn = rgb_i.min(axis=-1)
    sat = rgb_i.max(axis=-1) - mn
    canvasish = (mn >= 240) & (sat <= 12) & op
    edge_zone = ndimage.binary_dilation(~op, iterations=3) & op
    passable = canvasish & edge_zone
    reach = ndimage.binary_propagation(~op, mask=passable | (~op), structure=STRUCT)
    op2 = op & ~(reach & canvasish)
    lab2, n2 = ndimage.label(op2, structure=STRUCT)
    if n2 > 1:
        sizes2 = ndimage.sum(op2, lab2, range(1, n2 + 1))
        keep2 = np.zeros(n2 + 1, bool)
        keep2[1:][sizes2 >= 0.005 * sizes2.max()] = True
        op2 = keep2[lab2]

    ys, xs = np.where(op2)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sub = arr[y0:y1 + 1, x0:x1 + 1].astype(np.uint8).copy()
    sub[..., 3] = np.where(op2[y0:y1 + 1, x0:x1 + 1], sub[..., 3], 0)
    img = Image.fromarray(sub, "RGBA")
    w, h = img.size
    nw = max(1, round(w * height / h))
    img = img.resize((nw, height), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "WEBP", lossless=True)
    print(f"{dst.name}: {img.size[0]}x{img.size[1]}")

if __name__ == "__main__":
    main()
