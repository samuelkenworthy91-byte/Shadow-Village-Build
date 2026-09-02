# Portrait quality control — v33

Reviewed the 370 final runtime portraits from playtest commit
`3ffc22ae2f93f48a44bc94f8a07b109f7175a4b8`.

- Removed 30 portraits with clipped figures, undersized framing, or a second
  humanoid figure. The playable pool now contains **340** portraits.
- Cleaned 82 newer portraits using individually reviewed background pockets.
  White garments, skin, bandages, weapon highlights and props remain intact.
  The repair changes alpha only; original RGB artwork and canvas placement
  are preserved. No generated replacement artwork is used.
- Corrected stale bust crops left over from the pre-v29 images.
- Preserved approved saved assignments, including IDs above 340. The IDs are
  deliberately sparse, and are never interpreted as a contiguous 1–340 range.
- Kept approved legacy hash assignments unchanged. Retired or invalid saved
  assignments resolve deterministically to an approved portrait in roster
  and battle views. Bingo Book artwork continues using its separate path.
- Recruitment draws only from approved IDs. Offline caching uses the same
  list and a new cache version.

`overrides/portrait_qc_v33.json` is the reviewed inventory: removal reasons,
approved IDs, original/cleaned hashes, and exact background repair seeds.
The 33 retired direct WebP source files were deleted across their generations.
The original game archive is a historical build input; retired PNGs from it
are removed by the shared installer and never ship in the final build.

Repository sources remain individual compact WebPs; runtime files remain
individual PNGs under `public/ninjas`.

## Build integration

The playtest workflow applies `apply_portrait_qc_v33.py` **last**, after v19.
Earlier patch stages still use their historical 250/310/370 code anchors, but
asset checks compare actual approved IDs for that stage instead of assuming
contiguous filenames. The finalizer installs the reviewed sources again,
prunes retired runtime files, and writes the approved selection/cache lists.

The checked baseline for local validation is the successful playtest workflow's
patched-source artifact. The older archive-based `work/rebuild_app.sh` has an
existing MissionBoard/v19 anchor mismatch; the playtest workflow is authoritative.

## Verification

After the finalizer:

```sh
python work/check_portrait_qc_v33.py
app/node_modules/.bin/esbuild work/check_portrait_selection_v33.ts --bundle --platform=node --outfile=/tmp/check-portrait-selection.cjs
node /tmp/check-portrait-selection.cjs
npm --prefix app run build
```

Checks cover all 340 asset paths; hashes and transparency seeds in all 82
repaired portraits; all 370 possible old saved assignments; 10,000 legacy
identities; invalid saved values; a full 340-recruit no-repeat draw; pool
exhaustion; Bingo Book paths; and exact agreement with the offline cache.
