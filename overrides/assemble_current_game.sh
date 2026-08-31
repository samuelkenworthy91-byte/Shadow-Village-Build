#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(pwd)"
APP_DIR="$ROOT_DIR/app"

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
unzip -q ninja-settlement-management-game-art-swap.zip -d "$APP_DIR"
test -f "$APP_DIR/package.json"

# Core art, branding and PWA files used by every target.
cp overrides/src/components/NinjaSprite.tsx app/src/components/NinjaSprite.tsx
cp overrides/src/components/HUD.tsx app/src/components/HUD.tsx
cp overrides/src/game/ninjaArt.ts app/src/game/ninjaArt.ts
cp overrides/public/sw.js app/public/sw.js
cp overrides/public/manifest.webmanifest app/public/manifest.webmanifest
cat overrides/icon_parts/*.txt | tr -d '\n\r' | base64 --decode > /tmp/shadow-village-logo.png
convert /tmp/shadow-village-logo.png -resize 512x512 app/public/icon.png
mkdir -p app/assets
convert /tmp/shadow-village-logo.png -resize 1024x1024 app/assets/logo.png

# Raid balance and transparency.
(
  cd app
  python ../overrides/apply_raid_balance.py
)

# Raid classes and defender selection.
cat overrides/raid_patch_b64_v22/part_* | tr -d '\n\r' | base64 --decode > /tmp/raid-v22.patch
(
  cd app
  set +e
  patch -p1 --forward < /tmp/raid-v22.patch
  PATCH_RC=$?
  set -e
  test -f src/components/RaidDefenseModal.tsx
  grep -q 'raid_select' src/game/types.ts
  grep -q 'beginRaidBattle' src/game/engine.ts
  echo "Raid patch return code: $PATCH_RC"
)
cp overrides/raid_sw_v22.js app/public/sw.js
mkdir -p app/public/raiders
cp overrides/raid_assets_direct_v22/raiders/*.webp app/public/raiders/
cp overrides/raid_assets_direct_v22/bg-raid-field.jpg app/public/bg-raid-field.jpg

# Rank-up exams.
(
  cd app
  python ../overrides/apply_rank_exam.py
)
cat overrides/rank_exam_assets_b64_v23/part_* | tr -d '\n\r' | base64 --decode > app/public/bg-exam-arena.jpg
test -s app/public/bg-exam-arena.jpg

# Raid rebalance and local save slots.
cat overrides/v24_patch_parts/part_* > /tmp/v24.patch
(
  cd app
  patch -p1 < /tmp/v24.patch
)
cp overrides/src/game/save.ts app/src/game/save.ts
sed -i 's/shadow-village-v6-rank-exams/shadow-village-v7-save-slots/' app/public/sw.js

# Universal battle target selection.
(
  cd app
  python ../overrides/apply_target_selection.py
)
sed -i 's/shadow-village-v7-save-slots/shadow-village-v8-target-selection/' app/public/sw.js

# Expanded ninja progression.
python overrides/apply_progression_expansion.py
grep -q '"ken" | "doj" | "tac"' app/src/game/types.ts
grep -q 'SAVE_VERSION = 2' app/src/game/save.ts

# Progression and bloodline update stack.
cat overrides/progression_v02.patch.gz.b64 | tr -d '\n\r' | base64 --decode | gzip -d > /tmp/progression-v02.patch
(
  cd app
  patch -p1 < /tmp/progression-v02.patch
  patch -p1 < ../overrides/progression_v021.patch
)
cat overrides/progression_v03.patch.gz.b64 | tr -d '\n\r' | base64 --decode | gzip -d > /tmp/progression-v03.patch
(
  cd app
  patch -p1 < /tmp/progression-v03.patch
  patch -p1 < ../overrides/progression_v032.patch
  patch -p1 < ../overrides/progression_v033.patch
)

# Complete 250-portrait library.
mkdir -p app/public/ninjas
asset_dirs=(overrides/ninja_assets_v26/direct)
if [ -d overrides/ninja_assets_v27/direct ]; then
  asset_dirs+=(overrides/ninja_assets_v27/direct)
fi
test "$(find "${asset_dirs[@]}" -maxdepth 1 -name 'ninja_*.webp' | wc -l)" -eq 170
for n in $(seq -w 81 250); do
  src=""
  for dir in "${asset_dirs[@]}"; do
    candidate="$dir/ninja_${n}.webp"
    if [ -f "$candidate" ]; then
      src="$candidate"
      break
    fi
  done
  test -n "$src"
  dims="$(identify -format '%wx%h' "$src")"
  if [ "$dims" = "240x536" ]; then
    convert "$src" "PNG32:app/public/ninjas/ninja_${n}.png"
  else
    convert "$src" -trim +repage -resize '230x520>' -gravity south -background none -extent 240x536 "PNG32:app/public/ninjas/ninja_${n}.png"
  fi
done
python overrides/apply_ninja_portraits_v26.py
test "$(find app/public/ninjas -maxdepth 1 -name 'ninja_*.png' | wc -l)" -eq 250

# Equipment gacha system.
python overrides/apply_equipment_gacha.py
python overrides/apply_equipment_gacha_v2.py
grep -q 'Array.from({ length: 400 }' app/src/game/equipment.ts
grep -q 'applyEquipmentToBattleUnit' app/src/game/battle.ts

# Village depth stack through v16.
python overrides/apply_village_depth_v2_shim.py
test -f app/src/game/specialMissionsV2.ts
grep -q 'apply_village_depth_v16_specialist_combat.py' overrides/apply_village_depth_v1.py
grep -q 'apply_village_depth_v16_typefix.py' overrides/apply_village_depth_v1.py
python overrides/apply_village_depth_v1.py

# Final integration checks.
grep -q 'export function specialistJutsuTraits' app/src/game/jutsu.ts
grep -q 'export function combatTechniqueIds' app/src/game/perks.ts
grep -q '"technique"' app/src/game/types.ts
grep -q 'COMBAT TECHNIQUES' app/src/components/BattleScreen.tsx
grep -q 'EQUIPPED GEAR TECHNIQUES' app/src/components/BattleScreen.tsx
grep -q 'ONE DEFINING JUTSU STYLE' app/src/components/JutsuTree.tsx
grep -q 'shadow-village-depth-v1-jutsu-potential-v16-specialist-combat-rework' app/public/sw.js
! grep -q 'case "special":' app/src/game/battle.ts
! grep -q '{ id: "special"' app/src/components/BattleScreen.tsx

echo "Shadow Village current source assembled successfully."
