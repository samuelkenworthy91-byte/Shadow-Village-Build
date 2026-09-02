# building_assets_v31 - generated village building art

Cel-shaded anime building sprites matching the ninja portrait style,
generated individually on pure white and cut out with the gentle solo
pipeline (work/solo_building.py: adaptive border flood-fill background
removal, NO morphological closing, strict near-canvas-only defringe,
normalized to 200px height, lossless WebP with transparency).

- `bld_hall.webp`    - grand two-story main hall
- `bld_farm.webp`    - rice paddy plot with a farmer hut
- `bld_tea.webp`     - two-story tea house with lanterns
- `bld_dojo.webp`    - training hall with open doors
- `bld_tower.webp`   - wooden watchtower with brazier
- (remaining types - shrine, intel, anbu, hospital, embassy - follow in
  the next batches; those buildings keep the CSS shape fallback until
  their art exists)

Installed by `overrides/apply_building_art_v31.py`, which wires them into
the village scene (Scene.tsx) at 76px height (58px on small screens),
keeps the level pips, falls back to the CSS shapes for types without
art, and adds the sprites to the service-worker precache.
