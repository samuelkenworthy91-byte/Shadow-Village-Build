# ninja_assets_v28 - general roster portraits 311–370

Sixtieth-ninja extension of the image-backed general portrait pool, batch v28.

- `direct/ninja_311.webp` … `ninja_370.webp` - 60 lossless WebP portraits,
  240×536 RGBA, transparent background, figure fitted to ≤230×420 and
  bottom-anchored to match the v26/v27 pool profile (full-body height 420,
  bustTop 92).
- `meta.json` - `{ "<id>": <bustTop> }` crop metadata consumed by
  `overrides/apply_ninja_portraits_v28.py` when extending `NINJA_ART_META`.

Art: same cel-shaded modern anime style as batches v26/v27, generated from
style references `ninja_251.png`, `ninja_001.png` and `ninja_120.png`; each
sheet holds 10 full-body figures on a flat white background, flood-fill
background removal, figure segmentation, dust-component cleanup (<0.5% of
figure area), fit and normalize. Kanji-free by construction (no text on the
sheets).

Consumed by `overrides/apply_ninja_portraits_v28.py`, which converts the
webps to `app/public/ninjas/ninja_311..370.png` (ImageMagick, same command
the CI portrait step uses) and wires the ids into the deterministic general
pool. It runs after the v17 technique overhaul and before v18/v19.
