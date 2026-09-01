"""Remove sealed sheet-background pockets from the v27+v28 portraits.

The crop pipeline's morphological closing seals narrow background gaps
(between limbs, body and weapons) into the figure mask, leaving opaque
patches of untouched sheet canvas inside portraits. Detection uses the raw
generation sheets as ground truth: a white component whose raw-sheet
interior is statistically indistinguishable from the sheet's deep
background (mean >= 253.5, std <= 1.5 against 254.9 +/- 0.3) is untouched
canvas, not drawn art, and becomes transparent. Drawn white garments
deviate clearly (painted fills land at 248-253 with visible texture).

After clearing a pocket the portrait is re-defringed so the newly exposed
edges are cleaned.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from white_pocket_audit import background_mask, sheet_figures, match_sheet_figure, load_final, STRUCT

MIN_PX = 250          # only remove visibly-large pockets
PRISTINE_MEAN = 253.5  # raw interior must match the untouched canvas
PRISTINE_STD = 1.5

def build_sheets():
    sheets = {}
    for root in ["overrides/ninja_assets_v27/sheets", "work/v28_sheets_proc"]:
        for p in sorted(Path(root).glob("sheet_*.png")):
            rgb, bg, figs = sheet_figures(p)
            deep = ndimage.binary_erosion(bg, iterations=15)
            vals = rgb[deep].astype(float)
            sheets[str(p)] = {"rgb": rgb, "figs": figs,
                              "bg_mean": float(vals.mean()), "bg_std": float(vals.std())}
    return sheets

def defringe_pass(arr: np.ndarray) -> np.ndarray:
    """One full iterated defringe (same rules as work/defringe_portraits.py)."""
    a = arr[..., 3]
    rgb = arr[..., :3].astype(int)
    op = a > 12
    for _ in range(4):
        mn = rgb.min(axis=-1)
        sat = rgb.max(axis=-1) - mn
        whiteish = (mn >= 210) & (sat <= 60) & op
        edge_zone = ndimage.binary_dilation(~op, iterations=6) & op
        passable = whiteish & edge_zone
        reach = ndimage.binary_propagation(~op, mask=passable | (~op), structure=STRUCT)
        peel = reach & whiteish
        outer2 = ndimage.binary_dilation(~op, iterations=2) & op
        halo = whiteish & outer2 & (a < 250)
        step = peel | halo
        if not step.any():
            break
        op = op & ~step
    return op

def main():
    sheets = build_sheets()
    all_figs = [e for v in sheets.values() for e in v["figs"]]
    removed_report = []
    for base, ids in [("overrides/ninja_assets_v27/direct", range(251, 311)),
                      ("overrides/ninja_assets_v28/direct", range(311, 371))]:
        for i in ids:
            path = Path(f"{base}/ninja_{i}.webp")
            im = load_final(path)
            a = im[..., 3]; op = a > 12
            if not op.any():
                continue
            rgb = im[..., :3]
            mn = rgb.min(axis=-1); sat = rgb.max(axis=-1) - mn
            white = (mn >= 235) & (sat <= 25) & op
            lab, n = ndimage.label(white, structure=STRUCT)
            if n == 0:
                continue
            sizes = ndimage.sum(white, lab, range(1, n + 1))
            comps = [(int(sizes[k - 1]), lab == k) for k in range(1, n + 1) if sizes[k - 1] >= MIN_PX]
            if not comps:
                continue
            iou, fig = match_sheet_figure(op, all_figs)
            if iou < 0.85:
                print(f"ninja_{i}: mapping IoU {iou:.2f} too low, skipping")
                continue
            src = next(s for s, v in sheets.items() if any(e is fig for e in v["figs"]))
            ys, xs = np.where(op)
            fx0, fy0 = int(xs.min()), int(ys.min())
            fw, fh = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
            bx0, by0, bx1, by1 = fig["box"]
            sx = fw / (bx1 - bx0 + 1); sy = fh / (by1 - by0 + 1)
            raw = sheets[src]["rgb"]
            to_remove = []
            for size, comp in comps:
                interior = ndimage.binary_erosion(comp, iterations=2)
                if interior.sum() < 60:
                    interior = comp
                cys, cxs = np.where(interior)
                rx = np.clip(np.round(bx0 + (cxs - fx0) / sx).astype(int), 0, raw.shape[1] - 1)
                ry = np.clip(np.round(by0 + (cys - fy0) / sy).astype(int), 0, raw.shape[0] - 1)
                vals = raw[ry, rx].astype(float)
                if vals.mean() >= PRISTINE_MEAN and vals.std() <= PRISTINE_STD:
                    to_remove.append((size, comp, float(vals.mean()), float(vals.std())))
            if not to_remove:
                continue
            out = im.copy()
            for size, comp, m, s in to_remove:
                # clear the component plus its 1px anti-alias blend ring
                clear = ndimage.binary_dilation(comp, iterations=1)
                out[..., 3] = np.where(clear, 0, out[..., 3]).astype(np.uint8)
            # re-defringe the newly exposed edges
            op2 = defringe_pass(out)
            # safety: the main figure must survive mostly intact
            lab1, n1 = ndimage.label(op, structure=STRUCT)
            lab2, n2 = ndimage.label(op2, structure=STRUCT)
            if n1 and n2:
                sizes1 = ndimage.sum(op, lab1, range(1, n1 + 1))
                sizes2 = ndimage.sum(op2, lab2, range(1, n2 + 1))
                if sizes2.max() < 0.75 * sizes1.max():
                    print(f"ninja_{i}: main figure would drop below 75%, skipping")
                    continue
            out[..., 3] = np.where(op2, out[..., 3], 0).astype(np.uint8)
            Image.fromarray(out.astype(np.uint8)).save(path, "WEBP", lossless=True)
            removed_report.append((i, [(s, round(m, 1)) for s, _, m, _ in to_remove]))
            print(f"ninja_{i}: removed {len(to_remove)} pocket(s), {sum(s for s, _, _, _ in to_remove)}px")

    print(f"\n{len(removed_report)} portraits cleaned")
    for i, lst in removed_report:
        print(f"  ninja_{i}: {lst}")

if __name__ == "__main__":
    main()
