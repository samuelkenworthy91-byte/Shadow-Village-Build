from pathlib import Path
import base64
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "overrides" / "bingo_assets_v1" / "direct"
OUT = ROOT / "app" / "public" / "bingo"
OUT.mkdir(parents=True, exist_ok=True)

expected = [f"bingo_{i:03d}" for i in range(1, 21)]

for stem in expected:
    webp = SRC / f"{stem}.webp"
    staged = SRC / f"{stem}.webp.b64"
    if not webp.exists() and staged.exists():
        webp.write_bytes(base64.b64decode("".join(staged.read_text(encoding="utf-8").split())))
    if not webp.exists():
        raise SystemExit(f"Missing Bingo asset: {webp}")
    out = OUT / f"{stem}.png"
    subprocess.run(["convert", str(webp), f"PNG32:{out}"], check=True)
    if not out.exists() or out.stat().st_size == 0:
        raise SystemExit(f"Failed to create runtime sprite: {out}")

print(f"Imported {len(expected)} Bingo Book sprites into {OUT}")
