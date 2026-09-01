"""Map each final portrait (251-370) back to its raw generation sheet and
classify big white components as sheet-background vs design, using the raw
sheet as ground truth.

Background test: the raw sheet is flood-filled from its borders through
light low-saturation pixels (same as the crop pipeline). A white component
whose raw-sheet counterpart is reached by that flood is sheet background
(either an enclosed pocket the original flood never reached, or a narrow
gap the morphological closing re-swallowed into the mask). Components the
raw flood cannot reach are enclosed by the character's own line art -
those are drawn design (white clothing, weapons, emblems) and are kept,
subject to a background-statistics check for fully-sealed pockets.

Usage: python3 work/white_pocket_audit.py [--min-px 150]
Writes work/white_pocket_report.json and prints a summary.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

STRUCT = np.ones((3, 3), bool)

def background_mask(rgb: np.ndarray) -> np.ndarray:
    """Flood background from the borders through light, low-saturation pixels."""
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = mx - mn
    lum = rgb.sum(axis=2) / 3.0
    cand = (lum > 155) & (sat < 48)
    h, w = cand.shape
    seeds = np.zeros((h, w), dtype=bool)
    seeds[0, :] = cand[0, :]
    seeds[-1, :] = cand[-1, :]
    seeds[:, 0] = cand[:, 0]
    seeds[:, -1] = cand[:, -1]
    bg = seeds.copy()
    while True:
        grown = ndimage.binary_dilation(bg, structure=STRUCT) & cand
        if grown.sum() <= bg.sum():
            break
        bg = grown
    return bg

def sheet_figures(sheet_path: Path):
    """Replicate the crop pipeline's figure detection on a raw sheet."""
    rgb = np.array(Image.open(sheet_path).convert("RGB"))
    bg = background_mask(rgb)
    mask = ~bg
    mask = ndimage.binary_closing(mask, iterations=3)
    mask = ndimage.binary_opening(mask, iterations=2)
    mask = ndimage.binary_closing(mask, iterations=2)
    lab, n = ndimage.label(mask, structure=STRUCT)
    figs = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < mask.size * 0.002:
            continue
        if (xs.max() - xs.min()) <= 30 or (ys.max() - ys.min()) <= 60:
            continue
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
        figs.append({"box": (x0, y0, x1, y1), "mask": (lab == i)[y0:y1+1, x0:x1+1]})
    return rgb, bg, figs

def load_final(path: Path):
    im = np.array(Image.open(path).convert("RGBA")).astype(int)
    return im

def match_sheet_figure(op: np.ndarray, rgb_bg_figs: list):
    """Find the sheet figure whose mask best matches the final silhouette."""
    ys, xs = np.where(op)
    fw, fh = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
    best = None
    for entry in rgb_bg_figs:
        x0, y0, x1, y1 = entry["box"]
        sw, sh = x1 - x0 + 1, y1 - y0 + 1
        # resize final silhouette to the source box size
        fig = Image.fromarray((op[ys.min():ys.max()+1, xs.min():xs.max()+1]).astype(np.uint8) * 255)
        fig = fig.resize((sw, sh), Image.NEAREST)
        fm = np.array(fig) > 127
        inter = (fm & entry["mask"]).sum()
        union = (fm | entry["mask"]).sum()
        iou = inter / max(union, 1)
        if best is None or iou > best[0]:
            best = (iou, entry)
    return best

def main():
    min_px = 150
    if "--min-px" in sys.argv:
        min_px = int(sys.argv[sys.argv.index("--min-px") + 1])

    sheets = {}
    for root in ["overrides/ninja_assets_v27/sheets", "work/v28_sheets_proc"]:
        for p in sorted(Path(root).glob("sheet_*.png")):
            rgb, bg, figs = sheet_figures(p)
            sheets[str(p)] = {"rgb": rgb, "bg": bg, "figs": figs,
                              "n_figs": len(figs)}
    for k, v in sheets.items():
        print(f"{k}: {v['n_figs']} figures")

    report = []
    for base, ids in [("overrides/ninja_assets_v27/direct", range(251, 311)),
                      ("overrides/ninja_assets_v28/direct", range(311, 371))]:
        for i in ids:
            im = load_final(Path(f"{base}/ninja_{i}.webp"))
            a = im[..., 3]; op = a > 12
            rgb = im[..., :3]
            mn = rgb.min(axis=-1); sat = rgb.max(axis=-1) - mn
            white = (mn >= 235) & (sat <= 25) & op
            lab, n = ndimage.label(white, structure=STRUCT)
            if n == 0:
                continue
            sizes = ndimage.sum(white, lab, range(1, n + 1))
            comps = []
            for k in range(1, n + 1):
                if sizes[k - 1] < min_px:
                    continue
                comps.append((int(sizes[k - 1]), lab == k))
            if not comps:
                continue
            # locate source figure
            best_iou, best_fig = match_sheet_figure(op, [e for v in sheets.values() for e in v["figs"]])
            # find which sheet it came from
            src_sheet = None
            for sname, v in sheets.items():
                if any(e is best_fig for e in v["figs"]):
                    src_sheet = sname
                    break
            ys, xs = np.where(op)
            fx0, fy0 = int(xs.min()), int(ys.min())
            fw, fh = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
            bx0, by0, bx1, by1 = best_fig["box"]
            sw, sh = bx1 - bx0 + 1, by1 - by0 + 1
            sx = fw / sw
            sy = fh / sh
            entry = {"id": i, "sheet": Path(src_sheet).name, "iou": round(float(best_iou), 3),
                     "components": []}
            for size, comp in comps:
                cys, cxs = np.where(comp)
                # map to raw coords
                rx = bx0 + (cxs - fx0) / sx
                ry = by0 + (cys - fy0) / sy
                rmask = np.zeros(sheets[src_sheet]["bg"].shape, bool)
                rxi = np.clip(np.round(rx).astype(int), 0, rmask.shape[1] - 1)
                ryi = np.clip(np.round(ry).astype(int), 0, rmask.shape[0] - 1)
                rmask[ryi, rxi] = True
                bg = sheets[src_sheet]["bg"]
                frac_bg = float((rmask & bg).sum() / max(rmask.sum(), 1))
                # background statistics of the raw region
                raw_rgb = sheets[src_sheet]["rgb"]
                vals = raw_rgb[rmask]
                entry["components"].append({
                    "px": size, "frac_in_raw_bg": round(frac_bg, 3),
                    "raw_mean": [round(float(v), 1) for v in vals.mean(axis=0)] if len(vals) else None,
                    "raw_std": [round(float(v), 1) for v in vals.std(axis=0)] if len(vals) else None,
                })
            report.append(entry)

    Path("work/white_pocket_report.json").write_text(json.dumps(report, indent=1))
    sure_bg = [(e["id"], c["px"], c["frac_in_raw_bg"]) for e in report for c in e["components"] if c["frac_in_raw_bg"] >= 0.3]
    sealed = [(e["id"], c["px"], c["raw_mean"], c["raw_std"]) for e in report for c in e["components"] if c["frac_in_raw_bg"] < 0.3]
    print(f"\nportraits with components >= {min_px}px: {len(report)}")
    print(f"\nDEFINITE sheet-background (raw flood reaches them): {len(sure_bg)}")
    for s in sorted(sure_bg, key=lambda t: -t[1]):
        print(f"  ninja_{s[0]}: {s[1]}px, {s[2]*100:.0f}% in raw bg")
    print(f"\nSEALED (need judgment): {len(sealed)}")
    for s in sorted(sealed, key=lambda t: -t[1]):
        print(f"  ninja_{s[0]}: {s[1]}px, raw mean {s[2]} std {s[3]}")

if __name__ == "__main__":
    main()
