from __future__ import annotations

import base64
import glob
import io
import string
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

SPRITE_W = 240
SPRITE_H = 536
CELL_W = 80
CELL_H = 179
COLS = 10
FIRST_ID = 81
LAST_ID = 190
MAX_CONTENT_W = 220
MAX_CONTENT_H = 400
BOTTOM_PAD = 8
BASE64_CHARS = set(string.ascii_letters + string.digits + "+/=")


def read_b64_parts(pattern: str) -> bytes:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise RuntimeError(f"No asset parts matched {pattern}")
    raw = "".join(Path(p).read_text(encoding="utf-8") for p in paths)
    encoded = "".join(raw.split())
    invalid = [(i, ch, ord(ch)) for i, ch in enumerate(encoded) if ch not in BASE64_CHARS]
    if invalid:
        counts = Counter(ch for _, ch, _ in invalid)
        sample = invalid[:12]
        raise RuntimeError(
            f"Invalid base64 transport characters in {pattern}: count={len(invalid)}, "
            f"types={dict(counts)}, sample={sample}, compact_len={len(encoded)}"
        )
    if len(encoded) % 4:
        raise RuntimeError(f"Invalid base64 length in {pattern}: {len(encoded)} (mod 4 = {len(encoded) % 4})")
    return base64.b64decode(encoded, validate=True)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    game_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    asset_root = repo_root / "overrides" / "ninja_assets_v26"

    color_bytes = read_b64_parts(str(asset_root / "color32_parts" / "part_*"))
    alpha_bytes = read_b64_parts(str(asset_root / "alpha80_parts" / "part_*"))

    color = Image.open(io.BytesIO(color_bytes)).convert("RGB")
    alpha = Image.open(io.BytesIO(alpha_bytes)).convert("L")
    expected_size = (CELL_W * COLS, CELL_H * 11)
    if color.size != expected_size or alpha.size != expected_size:
        raise RuntimeError(
            f"Unexpected portrait atlas size: color={color.size}, alpha={alpha.size}, expected={expected_size}"
        )

    atlas = Image.merge("RGBA", (*color.split(), alpha))
    out_dir = game_root / "public" / "ninjas"
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for art_id in range(FIRST_ID, LAST_ID + 1):
        index = art_id - FIRST_ID
        col = index % COLS
        row = index // COLS
        x0 = col * CELL_W
        y0 = row * CELL_H
        cell = atlas.crop((x0, y0, x0 + CELL_W, y0 + CELL_H))
        bbox = cell.getbbox()
        if bbox is None:
            raise RuntimeError(f"Portrait {art_id} has no visible pixels")

        figure = cell.crop(bbox)
        scale = min(MAX_CONTENT_W / figure.width, MAX_CONTENT_H / figure.height)
        new_w = max(1, round(figure.width * scale))
        new_h = max(1, round(figure.height * scale))
        figure = figure.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (SPRITE_W, SPRITE_H), (0, 0, 0, 0))
        px = (SPRITE_W - new_w) // 2
        py = SPRITE_H - BOTTOM_PAD - new_h
        canvas.alpha_composite(figure, (px, py))
        canvas.save(out_dir / f"ninja_{art_id:03d}.png", optimize=True)
        written += 1

    if written != 110:
        raise RuntimeError(f"Expected 110 portraits, wrote {written}")

    for art_id in (81, 100, 125, 150, 175, 190):
        path = out_dir / f"ninja_{art_id:03d}.png"
        with Image.open(path) as check:
            if check.size != (SPRITE_W, SPRITE_H) or check.mode != "RGBA":
                raise RuntimeError(f"Bad output portrait {path}: {check.size} {check.mode}")
            if check.getbbox() is None:
                raise RuntimeError(f"Portrait {path} is fully transparent")

    print(f"Reconstructed {written} transparent portraits ({FIRST_ID}-{LAST_ID}) into {out_dir}")


if __name__ == "__main__":
    main()
