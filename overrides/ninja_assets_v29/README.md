# ninja_assets_v29 - individually regenerated ninja portraits (251-370)

Rebuild of the v27/v28 portrait batches. The sheet-crop pipeline sealed
background gaps into figures and its defringe pass damaged pale faces, so
these portraits are generated ONE PER IMAGE on a pure white background and
cut with a gentle single-figure pipeline (work/solo_portrait.py):

- adaptive border flood-fill background removal with NO morphological
  closing, so under-arm and between-leg gaps stay transparent
- strict near-canvas-only defringe (min channel >= 240, saturation <= 12,
  max 3px deep) - pale faces and light clothing are never touched
- normalized like the rest of the pool: fit to <=230x420, bottom-anchored
  on a transparent 240x536 canvas, lossless WebP, bustTop 92

- `direct/ninja_251.webp` ... - the regenerated portraits. The batch fills
  up over time (10 per generation session); ids not yet present keep their
  v27/v28 art until replaced.
- `meta.json` - bustTop crop metadata per id.

Installed by `overrides/apply_ninja_portraits_v29.py`, which also lands the
fair art-selection change: recruits draw uniformly WITHOUT replacement from
the 370-portrait pool, so no two ninjas share a portrait until the pool is
exhausted (existing saves keep their current art).
