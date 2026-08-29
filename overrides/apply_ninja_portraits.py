from __future__ import annotations

import base64
import glob
import io
import string
import sys
import zipfile
from pathlib import Path

from PIL import Image

SPRITE_W = 240
SPRITE_H = 536
COLS = 10
ROWS = 11
FIRST_ID = 81
LAST_ID = 190
MAX_CONTENT_W = 220
MAX_CONTENT_H = 400
BOTTOM_PAD = 8
BASE64_CHARS = set(string.ascii_letters + string.digits + "+/=")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def read_b64_parts(pattern: str) -> bytes:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise RuntimeError(f"No asset parts matched {pattern}")
    raw = "".join(Path(p).read_text(encoding="utf-8") for p in paths)
    encoded = "".join(raw.split())
    invalid = [(i, ch) for i, ch in enumerate(encoded) if ch not in BASE64_CHARS]
    if invalid:
        raise RuntimeError(f"Invalid base64 transport in {pattern}: {invalid[:12]}")
    if len(encoded) % 4:
        raise RuntimeError(f"Invalid base64 length in {pattern}: {len(encoded)}")
    return base64.b64decode(encoded, validate=True)


def load_atlases(asset_root: Path) -> tuple[Image.Image, Image.Image]:
    bundle = read_b64_parts(str(asset_root / "bundle_parts" / "part_*"))
    if not zipfile.is_zipfile(io.BytesIO(bundle)):
        raise RuntimeError("Portrait bundle is not a valid ZIP archive")

    with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(IMAGE_EXTS)]
        alpha_name = next((n for n in names if "alpha" in Path(n).name.lower()), None)
        color_name = next((n for n in names if n != alpha_name and "color" in Path(n).name.lower()), None)
        if color_name is None:
            color_name = next((n for n in names if n != alpha_name), None)
        if alpha_name is None or color_name is None:
            raise RuntimeError(f"Portrait bundle missing alpha/color images: {names}")
        alpha_bytes = zf.read(alpha_name)
        color_bytes = zf.read(color_name)

    alpha = Image.open(io.BytesIO(alpha_bytes)).convert("L")
    color = Image.open(io.BytesIO(color_bytes)).convert("RGB")
    if color.size != alpha.size:
        raise RuntimeError(f"Atlas sizes differ: color={color.size}, alpha={alpha.size}")
    if color.width % COLS or color.height % ROWS:
        raise RuntimeError(f"Atlas is not divisible into {COLS}x{ROWS} cells: {color.size}")
    print(f"Loaded portrait atlases from bundle: color={color.size}, alpha={alpha.size}")
    return color, alpha


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    game_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    asset_root = repo_root / "overrides" / "ninja_assets_v26"

    color, alpha = load_atlases(asset_root)
    cell_w = color.width // COLS
    cell_h = color.height // ROWS
    atlas = Image.merge("RGBA", (*color.split(), alpha))
    out_dir = game_root / "public" / "ninjas"
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for art_id in range(FIRST_ID, LAST_ID + 1):
        index = art_id - FIRST_ID
        col = index % COLS
        row = index // COLS
        x0 = col * cell_w
        y0 = row * cell_h
        cell = atlas.crop((x0, y0, x0 + cell_w, y0 + cell_h))
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
