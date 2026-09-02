"""Split a multi-figure row image (N characters spaced on pure white) into
individual normalized portraits.

Uses the same gentle cutout as the solo pipeline (adaptive border
flood-fill, NO morphological closing, strict near-canvas-only defringe),
then clusters the opaque components into figures: components whose
horizontal extents overlap or sit within a small gap belong to the same
figure (body + detached weapon). Each figure is normalized like the rest
of the pool (fit <=230x420, bottom-anchored, 240x536, lossless WebP).

Usage: python3 work/row_portraits.py <input.png> <out_prefix> <start_id> [--report]
Writes <out_prefix>_<id>.webp for each detected figure; prints ids.
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

def strict_defringe(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    op = mask
    rgb = arr[..., :3].astype(int)
    mn = rgb.min(axis=-1)
    sat = rgb.max(axis=-1) - mn
    canvasish = (mn >= 240) & (sat <= 12) & op
    edge_zone = ndimage.binary_dilation(~op, iterations=3) & op
    passable = canvasish & edge_zone
    reach = ndimage.binary_propagation(~op, mask=passable | (~op), structure=STRUCT)
    op2 = op & ~(reach & canvasish)
    lab, n = ndimage.label(op2, structure=STRUCT)
    if n > 1:
        sizes = ndimage.sum(op2, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:][sizes >= 0.005 * sizes.max()] = True
        op2 = keep[lab]
    return op2

def normalize(rgb: np.ndarray, mask: np.ndarray) -> Image.Image:
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    rgba = np.dstack([rgb[y0:y1 + 1, x0:x1 + 1].astype(np.uint8),
                      (mask[y0:y1 + 1, x0:x1 + 1] * 255).astype(np.uint8)])
    img = Image.fromarray(rgba, "RGBA")
    w, h = img.size
    scale = min(FIT_W / w, FIT_H / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (SPRITE_W, SPRITE_H), (0, 0, 0, 0))
    canvas.paste(img, ((SPRITE_W - nw) // 2, SPRITE_H - nh), img)
    return canvas

def main():
    src = Path(sys.argv[1])
    prefix = Path(sys.argv[2])
    start_id = int(sys.argv[3])
    report = "--report" in sys.argv

    rgb = np.array(Image.open(src).convert("RGB"))
    mask = cutout(rgb)

    # cluster components into figures by horizontal proximity
    lab, n = ndimage.label(mask, structure=STRUCT)
    if n == 0:
        print("no figures detected")
        return
    boxes = []
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        boxes.append({"k": k, "x0": int(xs.min()), "x1": int(xs.max()),
                      "y0": int(ys.min()), "y1": int(ys.max()), "px": len(ys)})
    # drop specks (<0.3% of the largest component)
    big = max(b["px"] for b in boxes)
    boxes = [b for b in boxes if b["px"] >= 0.003 * big]
    for b in boxes:
        b.setdefault("ks", [b["k"]])
        b["h"] = b["y1"] - b["y0"]
        b["w"] = b["x1"] - b["x0"]
        b["cx"] = (b["x0"] + b["x1"]) / 2

    # persons: tall components; anything shorter is a fragment/weapon that
    # gets attached to the nearest person afterwards
    max_h = max(b["h"] for b in boxes)
    persons = [dict(b) for b in boxes if b["h"] >= 0.70 * max_h]
    frags = [b for b in boxes if b["h"] < 0.70 * max_h]
    if not persons:
        persons = [dict(b) for b in boxes]
        frags = []

    # neck-split suspiciously wide persons (two people touching): cut at the
    # sparsest column in the middle 60% when it is clearly thinner than average
    ws = sorted(pp["w"] for pp in persons)
    med_w = ws[len(ws) // 2] if ws else 0
    split_persons = []
    for pp in persons:
        region = np.isin(lab, pp["ks"]) & mask
        if med_w and pp["w"] > 1.3 * med_w:
            cols = region[:, pp["x0"]:pp["x1"] + 1].sum(axis=0).astype(float)
            lo, hi = int(pp["w"] * 0.2), int(pp["w"] * 0.8)
            window = cols[lo:hi]
            cut = lo + int(np.argmin(window))
            avg = cols.mean() if cols.mean() else 1.0
            if window.min() < 0.35 * avg:
                for half in ({"ks": pp["ks"], "x0": pp["x0"], "x1": pp["x0"] + cut},
                             {"ks": pp["ks"], "x0": pp["x0"] + cut + 1, "x1": pp["x1"]}):
                    sub = region[:, half["x0"]:half["x1"] + 1]
                    ys2 = np.where(sub.any(axis=1))[0]
                    if len(ys2) and sub.sum() >= 0.003 * big:
                        half["y0"] = pp["y0"] + int(ys2.min())
                        half["y1"] = pp["y0"] + int(ys2.max())
                        half["w"] = half["x1"] - half["x0"]
                        half["h"] = half["y1"] - half["y0"]
                        half["px"] = int(sub.sum())
                        half["ks"] = list(pp["ks"])
                        half["frags"] = []
                        split_persons.append(half)
                continue
        pp["frags"] = []
        split_persons.append(pp)
    persons = split_persons

    # attach fragments (weapons, banner poles) to the nearest person by
    # x-center distance
    for f in frags:
        if not persons:
            break
        nearest = min(persons, key=lambda pp: abs(pp["x0"] + pp["x1"] - 2 * f["cx"]))
        nearest["x0"] = min(nearest["x0"], f["x0"])
        nearest["x1"] = max(nearest["x1"], f["x1"])
        nearest["ks"] = nearest["ks"] + f["ks"]

    # figures must be tall enough (a person) relative to the tallest
    tallest = max(pp["y1"] - pp["y0"] for pp in persons)
    figures = [pp for pp in persons if (pp["y1"] - pp["y0"]) >= 0.62 * tallest]
    figures.sort(key=lambda m: (m["x0"] + m["x1"]) / 2)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    ids = []
    for i, f in enumerate(figures):
        fmask = np.isin(lab, f["ks"]) & mask
        # slice to the figure's box so normalization is per-figure
        sub = np.zeros_like(fmask)
        sub[f["y0"]:f["y1"] + 1, f["x0"]:f["x1"] + 1] = fmask[f["y0"]:f["y1"] + 1, f["x0"]:f["x1"] + 1]
        if not sub.any():
            continue
        sub_rgb = rgb
        arr = np.dstack([sub_rgb, (sub * 255).astype(np.uint8)])
        op2 = strict_defringe(arr, sub)
        canvas = normalize(sub_rgb, op2)
        cid = start_id + i
        out = Path(f"{prefix}_{cid}.webp")
        canvas.save(out, "WEBP", lossless=True)
        ids.append(cid)
        if report:
            a = np.array(canvas)[..., 3]
            op = a > 12
            ys, xs = np.where(op)
            d = ndimage.distance_transform_edt(op)
            mn2 = np.array(canvas)[..., :3].astype(int).min(axis=-1)
            sat2 = np.array(canvas)[..., :3].astype(int).max(axis=-1) - mn2
            ew = int((((mn2 >= 225) & (sat2 <= 45))[d == 1]).sum())
            print(f"  {out.name}: {xs.max()-xs.min()+1}x{ys.max()-ys.min()+1} edge-white {ew}")
    print(f"figures: {len(figures)} -> ids {ids}")

if __name__ == "__main__":
    main()
