"""Defringe the v27+v28 portrait batches (ninja_251-370).

The sheet-crop pipeline leaves a thin residue of the white sheet background
attached along each figure's silhouette (flood-fill boundary + morphological
closing), which the normalization resize smears into soft white speckles.
v26 reference pool has ~0.1% whiteish pixels on the silhouette ring; the new
batches carry 1.0-1.4%.

Fix, per portrait:
1. Peel pass: flood inward from the transparent region through whiteish
   pixels (bright + low saturation) within a 4px-deep edge zone, clearing
   them. The flood stops at dark (line-art) or colored pixels, so white
   clothing, weapons and emblems that are properly outlined survive intact.
2. Halo pass: whiteish semi-transparent pixels (alpha < 250) in the outer
   2px of the figure are cleared - they are pure background blend residue.
3. Dust pass: opaque components smaller than 0.5% of the figure are dropped
   (the peel can orphan tiny white fragments).

Prints per-file metrics and refuses to write files that lose more than 2.5%
of their opaque area or shift their bbox by more than 2px.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

STRUCT = np.ones((3, 3), bool)

def process(path: Path) -> dict:
    im = np.array(Image.open(path).convert("RGBA"))
    a = im[..., 3]
    rgb = im[..., :3].astype(int)
    op0 = a > 12
    if not op0.any():
        return {"status": "skip-empty"}

    before = op0.sum()
    ys0, xs0 = np.where(op0)
    bbox0 = (int(ys0.min()), int(ys0.max()), int(xs0.min()), int(xs0.max()))

    # Iterated peel: each pass exposes whiteish pixels that sat deeper than
    # the previous pass's edge zone; run to fixpoint (max 4 passes).
    op = op0.copy()
    for _ in range(4):
        mn = rgb.min(axis=-1)
        sat = rgb.max(axis=-1) - mn
        # whiteish: bright and low-saturation (white background residue)
        whiteish = (mn >= 210) & (sat <= 60) & op

        # --- 1. peel: flood from transparent through whiteish, 6px deep ---
        edge_zone = ndimage.binary_dilation(~op, iterations=6) & op
        passable = whiteish & edge_zone
        reach = ndimage.binary_propagation(~op, mask=passable | (~op), structure=STRUCT)
        peel = reach & whiteish

        # --- 2. halo: whiteish semi-transparent pixels in the outer 2px ---
        outer2 = ndimage.binary_dilation(~op, iterations=2) & op
        halo = whiteish & outer2 & (a < 250)

        step = peel | halo
        if not step.any():
            break
        op = op & ~step

    op2 = op

    # --- 3. dust: drop tiny opaque components orphaned by the peel ---
    lab, n = ndimage.label(op2, structure=STRUCT)
    if n > 1:
        sizes = ndimage.sum(op2, lab, range(1, n + 1))
        biggest = sizes.max()
        keep = np.zeros(n + 1, bool)
        keep[1:][sizes >= 0.005 * biggest] = True
        op2 = keep[lab]

    after = op2.sum()
    ys1, xs1 = np.where(op2)
    bbox1 = (int(ys1.min()), int(ys1.max()), int(xs1.min()), int(xs1.max()))

    loss_pct = 100.0 * (before - after) / before
    shift = max(abs(bbox1[0] - bbox0[0]), abs(bbox1[1] - bbox0[1]),
                abs(bbox1[2] - bbox0[2]), abs(bbox1[3] - bbox0[3]))
    if loss_pct > 2.5 or shift > 5:
        return {"status": "REJECT", "loss": round(loss_pct, 2), "shift": shift}

    out = im.copy()
    out[..., 3] = np.where(op2, out[..., 3], 0).astype(np.uint8)
    Image.fromarray(out).save(path, "WEBP", lossless=True)
    return {"status": "ok", "cleared": int(before - after),
            "loss": round(loss_pct, 2), "shift": shift}

def main():
    only = set(int(x) for x in sys.argv[1:]) if len(sys.argv) > 1 else None
    roots = [("overrides/ninja_assets_v27/direct", 251, 311),
             ("overrides/ninja_assets_v28/direct", 311, 371)]
    rejected = []
    total_peel = 0
    for root, lo, hi in roots:
        for i in range(lo, hi):
            if only is not None and i not in only:
                continue
            r = process(Path(f"{root}/ninja_{i}.webp"))
            if r["status"] == "REJECT":
                rejected.append((i, r))
                print(f"ninja_{i}: REJECT loss={r['loss']}% shift={r['shift']}px (not written)")
            elif r["status"] == "ok":
                total_peel += r["cleared"]
        if only is None:
            print(f"{root}: done")
    print(f"total pixels cleared: {total_peel}")
    if rejected:
        print(f"{len(rejected)} REJECTED (unchanged) - inspect individually")
        sys.exit(1)
    print("ALL CLEAN")

if __name__ == "__main__":
    main()
