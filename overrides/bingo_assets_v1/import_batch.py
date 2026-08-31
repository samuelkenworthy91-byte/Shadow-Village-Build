from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "overrides" / "bingo_assets_v1" / "direct"
OUT = ROOT / "app" / "public" / "bingo"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch-import Bingo Book WebP assets into runtime PNGs")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=80)
    p.add_argument("--workers", type=int, default=min(8, max(1, os.cpu_count() or 1)))
    p.add_argument("--require-complete", action="store_true")
    return p.parse_args()


def convert_one(tool: str, src: Path, dst: Path) -> str:
    subprocess.run([tool, str(src), f"PNG32:{dst}"], check=True, stdout=subprocess.DEVNULL)
    if not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError(f"Failed to create runtime sprite: {dst}")
    return dst.name


def main() -> int:
    opt = args()
    if opt.start < 1 or opt.end < opt.start:
        raise SystemExit("Invalid Bingo asset range")

    tool = shutil.which("magick") or shutil.which("convert")
    if not tool:
        raise SystemExit("ImageMagick is required (magick or convert)")

    OUT.mkdir(parents=True, exist_ok=True)
    wanted = list(range(opt.start, opt.end + 1))
    missing: list[int] = []
    prepared: list[tuple[int, Path]] = []

    with tempfile.TemporaryDirectory(prefix="shadow-village-bingo-") as tmp:
        tmp_dir = Path(tmp)
        for i in wanted:
            stem = f"bingo_{i:03d}"
            direct = SRC / f"{stem}.webp"
            staged = SRC / f"{stem}.webp.b64"
            if direct.exists():
                prepared.append((i, direct))
                continue
            if staged.exists():
                decoded = tmp_dir / f"{stem}.webp"
                payload = "".join(staged.read_text(encoding="utf-8").split())
                decoded.write_bytes(base64.b64decode(payload, validate=True))
                prepared.append((i, decoded))
                continue
            missing.append(i)

        if opt.require_complete and missing:
            ids = ", ".join(f"{i:03d}" for i in missing)
            raise SystemExit(f"Missing Bingo assets: {ids}")
        if not prepared:
            raise SystemExit("No Bingo assets found in requested range")

        failures: list[str] = []
        with ThreadPoolExecutor(max_workers=max(1, opt.workers)) as pool:
            jobs = {
                pool.submit(convert_one, tool, src, OUT / f"bingo_{i:03d}.png"): i
                for i, src in prepared
            }
            for future in as_completed(jobs):
                i = jobs[future]
                try:
                    future.result()
                except Exception as exc:  # report the whole failed set, not one-at-a-time
                    failures.append(f"{i:03d}: {exc}")

        if failures:
            raise SystemExit("Bingo conversion failures:\n" + "\n".join(failures))

    print(f"Imported {len(prepared)} Bingo Book sprites into {OUT}")
    if missing:
        print("Not staged yet: " + ", ".join(f"{i:03d}" for i in missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
