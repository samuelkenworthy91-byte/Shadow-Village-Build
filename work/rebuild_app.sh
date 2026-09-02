#!/usr/bin/env bash
# Rebuild the patched game source exactly as .github/workflows/build-apk.yml does
# on the main branch (patch phase only — no npm/APK build).
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf app
mkdir -p app
unzip -q ninja-settlement-management-game-art-swap.zip -d app

cp overrides/src/components/NinjaSprite.tsx app/src/components/NinjaSprite.tsx
cp overrides/src/components/HUD.tsx app/src/components/HUD.tsx
cp overrides/src/game/ninjaArt.ts app/src/game/ninjaArt.ts
cp overrides/public/sw.js app/public/sw.js
cp overrides/public/manifest.webmanifest app/public/manifest.webmanifest

(cd app && python ../overrides/apply_raid_balance.py) >/dev/null

cat overrides/raid_patch_b64_v22/part_* | tr -d '\n\r' | base64 --decode > /tmp/raid-v22.patch
(cd app && patch -p1 --forward < /tmp/raid-v22.patch >/dev/null 2>&1 || true)
rm -f app/public/sw.js.rej
cp overrides/raid_sw_v22.js app/public/sw.js
mkdir -p app/public/raiders
cp overrides/raid_assets_direct_v22/raiders/*.webp app/public/raiders/
cp overrides/raid_assets_direct_v22/bg-raid-field.jpg app/public/bg-raid-field.jpg

(cd app && python ../overrides/apply_rank_exam.py) >/dev/null
cat overrides/rank_exam_assets_b64_v23/part_* | tr -d '\n\r' | base64 --decode > app/public/bg-exam-arena.jpg

cat overrides/v24_patch_parts/part_* > /tmp/v24.patch
(cd app && patch -p1 --forward < /tmp/v24.patch >/dev/null)
cp overrides/src/game/save.ts app/src/game/save.ts
sed -i 's/shadow-village-v6-rank-exams/shadow-village-v7-save-slots/' app/public/sw.js

(cd app && python ../overrides/apply_target_selection.py) >/dev/null
sed -i 's/shadow-village-v7-save-slots/shadow-village-v8-target-selection/' app/public/sw.js

python overrides/apply_progression_expansion.py >/dev/null

cat overrides/progression_v02.patch.gz.b64 | tr -d '\n\r' | base64 --decode | gzip -d > /tmp/progression-v02.patch
(cd app && patch -p1 --forward < /tmp/progression-v02.patch >/dev/null)
(cd app && patch -p1 --forward < ../overrides/progression_v021.patch >/dev/null)
cat overrides/progression_v03.patch.gz.b64 | tr -d '\n\r' | base64 --decode | gzip -d > /tmp/progression-v03.patch
(cd app && patch -p1 --forward < /tmp/progression-v03.patch >/dev/null)
(cd app && patch -p1 --forward < ../overrides/progression_v032.patch >/dev/null)
(cd app && patch -p1 --forward < ../overrides/progression_v033.patch >/dev/null)

mkdir -p app/public/ninjas
asset_dirs=(overrides/ninja_assets_v26/direct)
if [ -d overrides/ninja_assets_v27/direct ]; then
  asset_dirs+=(overrides/ninja_assets_v27/direct)
fi
test "$(find "${asset_dirs[@]}" -maxdepth 1 -name 'ninja_*.webp' | wc -l)" -eq 230
for n in $(seq -w 81 310); do
  src=""
  for dir in "${asset_dirs[@]}"; do
    candidate="$dir/ninja_${n}.webp"
    if [ -f "$candidate" ]; then src="$candidate"; break; fi
  done
  test -n "$src"
  dims="$(identify -format '%wx%h' "$src")"
  if [ "$dims" = "240x536" ]; then
    convert "$src" "PNG32:app/public/ninjas/ninja_${n}.png"
  else
    convert "$src" -trim +repage -resize '230x520>' -gravity south -background none -extent 240x536 "PNG32:app/public/ninjas/ninja_${n}.png"
  fi
done
python overrides/apply_ninja_portraits_v26.py >/dev/null
test "$(find app/public/ninjas -maxdepth 1 -name 'ninja_*.png' | wc -l)" -eq 310

python overrides/apply_equipment_gacha.py >/dev/null
python overrides/apply_equipment_gacha_v2.py >/dev/null
python overrides/apply_village_depth_v2_shim.py >/dev/null
python overrides/apply_village_depth_v1.py >/dev/null

# Bingo Book stack — exactly the steps that run on main
python overrides/apply_bingo_book_v1.py >/dev/null
python overrides/bingo_assets_v1/import_batch.py --start 1 --end 80 --require-complete >/dev/null
python overrides/apply_bingo_book_v3.py >/dev/null
python overrides/apply_bingo_book_v4.py >/dev/null
python overrides/apply_bingo_book_v5.py >/dev/null
python overrides/apply_bingo_book_v6.py >/dev/null
python overrides/apply_bingo_book_v7.py >/dev/null
python overrides/apply_bingo_book_v7_1.py >/dev/null

# Final stage: portrait pool expansions and the technique overhaul stack.
# v27 (251-310) runs before v17 (which validates a 310-portrait tree);
# v28 (311-370) runs after v17 and converts its own webps; v29 replaces
# regenerated portraits on top; v18/v19 last.
python overrides/apply_ninja_portraits_v27.py >/dev/null
python overrides/apply_village_depth_v17_technique_nodes.py >/dev/null
python overrides/apply_ninja_portraits_v28.py >/dev/null
if [ -f overrides/apply_ninja_portraits_v29.py ]; then
  python overrides/apply_ninja_portraits_v29.py >/dev/null
fi
if [ -f overrides/apply_ui_daily_panel_v30.py ]; then
  python overrides/apply_ui_daily_panel_v30.py >/dev/null
fi
if [ -f overrides/apply_building_art_v31.py ]; then
  python overrides/apply_building_art_v31.py >/dev/null
fi
python overrides/apply_village_depth_v18_type_advantage.py >/dev/null
python overrides/apply_village_depth_v19_dekanji.py

echo "App rebuilt (main-branch patch phase)."
