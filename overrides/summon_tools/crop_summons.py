"""Crop generated summon art into transparent square portrait tiles.

The image model returns a wide painting: a torn-paper border, a flat dark
charcoal field, and the creature somewhere in the middle. The game needs a
small square PNG with the creature filling it and everything else transparent,
so it can sit beside a ninja portrait without a visible box.

Pipeline per image:
  1. Inset past the ragged paper border.
  2. Sample the charcoal background colour from the inset edges.
  3. Build an alpha mask of pixels far enough from that background.
  4. Keep only the largest connected blob, which discards stray paper flecks
     and the model's occasional signature marks.
  5. Crop to that blob, pad to a square, and resize.
"""

from pathlib import Path
import sys
import numpy as np
from PIL import Image

SIZE = 320
INSET = 0.055          # fraction of each side trimmed to clear the paper edge
THRESHOLD = 34         # per-channel distance from background to count as art
FEATHER = 1.1          # alpha blur radius, keeps painted edges soft


def largest_blob(mask: np.ndarray) -> np.ndarray:
    """Iterative flood fill; avoids a scipy dependency."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best: list[tuple[int, int]] = []
    for sy in range(0, h, 4):
        for sx in range(0, w, 4):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            stack = [(sy, sx)]
            seen[sy, sx] = True
            blob = []
            while stack:
                y, x = stack.pop()
                blob.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            if len(blob) > len(best):
                best = blob
    out = np.zeros_like(mask)
    if best:
        ys, xs = zip(*best)
        out[np.array(ys), np.array(xs)] = True
    return out


def crop_one(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    dx, dy = int(w * INSET), int(h * INSET)
    im = im.crop((dx, dy, w - dx, h - dy))
    a = np.asarray(im).astype(np.int16)

    # Background colour: median of a thin frame just inside the crop.
    edge = np.concatenate([
        a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3),
        a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3),
    ])
    bg = np.median(edge, axis=0)

    dist = np.abs(a - bg).max(axis=2)
    mask = dist > THRESHOLD

    # Drop single-pixel speckle before the blob search.
    keep = mask.copy()
    keep[1:-1, 1:-1] &= (
        mask[:-2, 1:-1] | mask[2:, 1:-1] | mask[1:-1, :-2] | mask[1:-1, 2:]
    )
    blob = largest_blob(keep)
    if not blob.any():
        raise SystemExit(f"{src.name}: no subject found")

    ys, xs = np.where(blob)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

    # Soft alpha: ramp over the threshold rather than a hard cut.
    alpha = np.clip((dist - THRESHOLD * 0.45) / (THRESHOLD * 0.9), 0, 1)
    alpha[~blob] = 0

    rgba = np.dstack([np.asarray(im), (alpha * 255).astype(np.uint8)])
    out = Image.fromarray(rgba, "RGBA").crop((x0, y0, x1, y1))

    # Pad to a square so every summon scales identically in the UI.
    side = max(out.size)
    pad = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    pad.paste(out, ((side - out.width) // 2, (side - out.height) // 2))
    pad = pad.resize((SIZE, SIZE), Image.LANCZOS)

    from PIL import ImageFilter
    r, g, b, al = pad.split()
    al = al.filter(ImageFilter.GaussianBlur(FEATHER))
    pad = Image.merge("RGBA", (r, g, b, al))

    dst.parent.mkdir(parents=True, exist_ok=True)
    pad.save(dst, optimize=True)
    print(f"{src.name} -> {dst.name}  subject {x1-x0}x{y1-y0}")


if __name__ == "__main__":
    src_dir, dst_dir = Path(sys.argv[1]), Path(sys.argv[2])
    for p in sorted(src_dir.glob("*.png")):
        crop_one(p, dst_dir / p.name)
