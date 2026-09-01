"""Process a single-figure portrait image into the standard 240x536 asset.

Gentle pipeline for individually generated portraits:
1. Adaptive border flood-fill background removal (thresholds derived from the
   image's own border color, so white or off-white backdrops both work).
   NO morphological closing - under-arm and between-leg gaps that are open
   in the source stay transparent instead of being sealed into the figure.
2. Dust pass: opaque fragments under 0.5% of the figure are dropped.
3. Strict defringe: only near-canvas pixels (min channel >= 240, saturation
   <= 12) are peeled, max 3px deep, single pass - pale skin and light
   clothing are never touched.
4. Normalize: fit to <=230x420, bottom-anchored and centered on a
   transparent 240x536 canvas; saved as lossless WebP.

Usage: python3 work/solo_portrait.py <input.png> <output.webp> [--report]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

STRUCT = np.ones((3, 3), bool)
SPRITE_W, SPRITE_H = 240, 536
FIT_W, FIT_H = 230, 420

def cutout(rgb: np.ndarray):
    """Adaptive flood-fill background removal from the borders."""
    h, w = rgb.shape[:2]
    border = np.concatenate([rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]])
    bmean = border.mean(axis=0)
    dist = np.abs(rgb.astype(int) - bmean).sum(axis=2)
    lum = rgb.mean(axis=2)
    sat = rgb.max(axis=2).astype(int) - rgb.min(axis=2)
    # passable: close to the border color, or bright and low-saturation
    near_border = dist <= 90
    light_low_sat = (lum > 205) & (sat < 30)
    cand = near_border | light_low_sat
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

def strict_defringe(arr: np.ndarray) -> np.ndarray:
    """Peel only near-canvas pixels from the silhouette, max 3px deep."""
    a = arr[..., 3]
    rgb = arr[..., :3].astype(int)
    op = a > 12
    mn = rgb.min(axis=-1)
    sat = rgb.max(axis=-1) - mn
    canvasish = (mn >= 240) & (sat <= 12) & op
    edge_zone = ndimage.binary_dilation(~op, iterations=3) & op
    passable = canvasish & edge_zone
    reach = ndimage.binary_propagation(~op, mask=passable | (~op), structure=STRUCT)
    peel = reach & canvasish
    op2 = op & ~peel
    # drop fragments orphaned by the peel
    lab, n = ndimage.label(op2, structure=STRUCT)
    if n > 1:
        sizes = ndimage.sum(op2, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:][sizes >= 0.005 * sizes.max()] = True
        op2 = keep[lab]
    return op2

def normalize(fig_rgb: np.ndarray, mask: np.ndarray) -> Image.Image:
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sub = fig_rgb[y0:y1 + 1, x0:x1 + 1]
    msub = mask[y0:y1 + 1, x0:x1 + 1]
    rgba = np.dstack([sub.astype(np.uint8), (msub * 255).astype(np.uint8)])
    img = Image.fromarray(rgba, "RGBA")
    w, h = img.size
    scale = min(FIT_W / w, FIT_H / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (SPRITE_W, SPRITE_H), (0, 0, 0, 0))
    canvas.paste(img, ((SPRITE_W - nw) // 2, SPRITE_H - nh), img)
    return canvas

def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    report = "--report" in sys.argv
    rgb = np.array(Image.open(src).convert("RGB"))
    mask = cutout(rgb)
    # figure-level dust: keep only substantial components before normalize
    lab, n = ndimage.label(mask, structure=STRUCT)
    if n == 0:
        raise SystemExit("no figure detected")
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    order = np.argsort(sizes)[::-1]
    keep = np.zeros_like(mask)
    for k in order:
        if sizes[k] >= 0.05 * sizes[order[0]]:
            keep |= (lab == (k + 1))
    mask = keep

    fig_rgb = rgb.copy()
    arr = np.dstack([fig_rgb, (mask * 255).astype(np.uint8)])
    op2 = strict_defringe(arr)
    out = arr.copy()
    out[..., 3] = np.where(op2, out[..., 3], 0).astype(np.uint8)

    canvas = normalize(out[..., :3].astype(np.uint8), op2)
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst, "WEBP", lossless=True)

    if report:
        a = np.array(canvas)[..., 3]
        op = a > 12
        ys, xs = np.where(op)
        h = int(ys.max() - ys.min() + 1); w = int(xs.max() - xs.min() + 1)
        # enclosed holes = open gaps kept transparent inside the figure bbox
        inner = np.zeros_like(op)
        inner[ys.min():ys.max()+1, xs.min():xs.max()+1] = True
        lab2, n2 = ndimage.label(inner & ~op, structure=STRUCT)
        hole_px = int((inner & ~op).sum())
        mn = np.array(canvas)[..., :3].astype(int).min(axis=-1)
        sat = np.array(canvas)[..., :3].astype(int).max(axis=-1) - mn
        d = ndimage.distance_transform_edt(op)
        edge_white = int((((mn >= 225) & (sat <= 45))[d == 1]).sum())
        print(f"{dst.name}: figure {w}x{h}, ar {w/h:.2f}, holes {hole_px}px/{n2}, "
              f"depth1-white {edge_white}, opaque {int(op.sum())}")

if __name__ == "__main__":
    main()
