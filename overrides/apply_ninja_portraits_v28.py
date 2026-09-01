"""Extend the image-backed ninja portrait pool from 310 to 370 ids.

Adds batch v28 (general roster portraits 311-370, sourced from
overrides/ninja_assets_v28/direct) to the deterministic general art pool in
src/game/ninjaArt.ts and the service-worker precache list in public/sw.js.
The 60 source webps are already normalized (240x536 RGBA) and are converted
to PNG here with ImageMagick - the same tool the CI portrait step uses.
Runs after the v17 technique overhaul (which validates a 310-portrait tree)
and before the v18/v19 patches.
"""

import subprocess
from pathlib import Path

ROOT = Path("app")
ART = ROOT / "src/game/ninjaArt.ts"
SW = ROOT / "public/sw.js"
SRC = Path("overrides/ninja_assets_v28/direct")
OUT = ROOT / "public/ninjas"

# bustTop crop lines measured from the final 240x536 normalized portraits
# (all 60 figures are full-body height 420 with the standard ~24px headroom,
# matching the established pool profile).
META = {i: 92 for i in range(311, 371)}

s = ART.read_text(encoding="utf-8")

old_pool = """/**
 * Image-backed player ninja art. All 310 portraits share one unrestricted
 * deterministic pool. Legendary status never forces or excludes a portrait.
 */
export const GENERAL_ART_IDS: number[] = Array.from({ length: 310 }, (_, i) => i + 1);"""
new_pool = """/**
 * Image-backed player ninja art. All 370 portraits share one unrestricted
 * deterministic pool. Legendary status never forces or excludes a portrait.
 */
export const GENERAL_ART_IDS: number[] = Array.from({ length: 370 }, (_, i) => i + 1);"""
if new_pool in s:
    print("ninjaArt pool already at 370 portraits")
elif old_pool in s:
    s = s.replace(old_pool, new_pool)
else:
    raise RuntimeError("Expected 310-portrait pool block was not found")

if "  370: { bustTop:" not in s:
    marker = "  310: { bustTop: 92 },\n};"
    if marker not in s:
        raise RuntimeError("Expected NINJA_ART_META tail (id 310) was not found")
    extra = "  310: { bustTop: 92 },\n" + "\n".join(
        f"  {i}: {{ bustTop: {META[i]} }}," for i in range(311, 371)
    ) + "\n};"
    s = s.replace(marker, extra)

ART.write_text(s, encoding="utf-8")

sw = SW.read_text(encoding="utf-8")
old_art = 'const NINJA_ART = Array.from({ length: 310 }, (_, i) => `/ninjas/ninja_${String(i + 1).padStart(3, "0")}.png`);'
new_art = 'const NINJA_ART = Array.from({ length: 370 }, (_, i) => `/ninjas/ninja_${String(i + 1).padStart(3, "0")}.png`);'
if new_art in sw:
    print("service worker art list already at 370 portraits")
elif old_art in sw:
    sw = sw.replace(old_art, new_art)
else:
    raise RuntimeError("Expected 310-portrait service-worker list was not found")
# The service-worker CACHE constant is intentionally left alone here;
# later pipeline stages anchor patches on it. The final stage bumps it.
SW.write_text(sw, encoding="utf-8")

# convert the batch's webp sources to PNG (sources are already 240x536 RGBA)
OUT.mkdir(parents=True, exist_ok=True)
for i in range(311, 371):
    src = SRC / f"ninja_{i}.webp"
    if not src.is_file():
        raise RuntimeError(f"missing portrait source {src}")
    dst = OUT / f"ninja_{i}.png"
    subprocess.run(["convert", str(src), f"PNG32:{dst}"], check=True)

art_check = ART.read_text(encoding="utf-8")
sw_check = SW.read_text(encoding="utf-8")
assert "length: 370" in art_check
assert "370: { bustTop:" in art_check
assert "length: 370" in sw_check
pngs = sorted(OUT.glob("ninja_*.png"))
assert len(pngs) == 370, f"expected 370 portrait PNGs after expansion, found {len(pngs)}"
print("Applied 311-370 ninja portrait library expansion")
