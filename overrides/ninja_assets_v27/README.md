# Ninja assets v27 — 60 new recruitable portraits (IDs 251–310)

Sixty new recruitable-ninja portraits matching the existing v26 art style,
extending the deterministic general pool from 250 to 310.

## Layout

- `direct/ninja_251.webp` … `ninja_310.webp` — final 240×536 transparent
  portraits (lossless WebP). This is the directory CI consumes; the pipeline
  mirrors `ninja_assets_v26`.
- `sheets/` — the eight raw generation sheets (opaque white background) that
  the portraits were cropped from. Kept for traceability.
- `sheets_packed/` — the crop-stage deliverable in the standard workflow
  format: six fully transparent 1200×1072 sheets, 10 portraits per sheet
  (5×2 grid of 240×536 cells), IDs in reading order
  (sheet 01 = 251–260, … sheet 06 = 301–310).

## Pipeline

1. Sheets generated against reference portraits from the existing pool
   (style, proportions, palette and figure scale matched statistically:
   luminance ~72 vs refs 60–76, dark-pixel fraction 0.78 vs refs 0.76–0.87,
   figure height 341–420px vs refs 346–420px).
2. Figures located via border flood-fill background removal + connected
   components; merged side-by-side pairs split at the head-gap band.
3. Each figure cropped, fitted to ≤230×420, bottom-anchored on a transparent
   240×536 canvas (same normalization the v26 CI fallback uses).
4. `apply_ninja_portraits_v27.py` (run by CI after
   `apply_ninja_portraits_v26.py`) raises `GENERAL_ART_IDS` and the service
   worker art list from 250 to 310 and appends the measured `bustTop`
   metadata for IDs 251–310.
