"""Kage Life v17 gameplay polish.

Applies one reviewed patch covering six player-reported problems:

  1. Potential audit — natural potential was a flat 1-5 roll (20% five-star,
     ~36% with Talent Scouts) and the uncertainty band displayed five stars for
     anyone who *might* be a 5, so effectively every recruit looked maxed.
     Potential is now a weighted roll (5★ ≈ 6%) and the star readout states
     whether the value is an estimate or confirmed.
  2. Every Jutsu, Genjutsu, gear technique and skill-tree technique now shows
     both a flavour line and a generated mechanical line. The mechanical text is
     derived from the same structured numbers combat resolves with, so the two
     can never drift apart.
  3. Equipment is fully unrestricted: any four owned pieces on any ninja, in any
     slot, including repeated rarities. Every numeric bonus is always displayed.
  4. Gold and rice predictions are shown on the home screen underneath the
     running totals, including the net rice figure.
  5. Items carry a drawn picture matching their written appearance, replacing
     the kanji tile on their card.
  6. Four new buildings (Ninja Academy, Armourer's Forge, Merchant Quarter,
     Scroll Archive) and sixteen new technologies feed the core loop: XP,
     recruitment quality, equipment economy, chakra costs, JP income, gold and
     an extra daily action.
"""

from pathlib import Path
import subprocess

ROOT = Path("app")
PATCH = Path("overrides/v17_gameplay_polish.patch")

if not ROOT.exists():
    raise SystemExit("app/ has not been unpacked yet")
if not PATCH.exists():
    raise SystemExit(f"missing patch payload: {PATCH}")

# The Kage Life branch build reuses the already-patched main artifact, so this
# step must be safe to run twice.
already = (ROOT / "src/components/EquipmentArtwork.tsx").exists()
if already:
    print("v17 gameplay polish: already applied, verifying only")
else:
    subprocess.run(
        ["patch", "-p1", "--forward"],
        cwd=ROOT,
        input=PATCH.read_bytes(),
        check=True,
    )

CHECKS = {
    "src/game/engine.ts": [
        "export const POTENTIAL_WEIGHTS",
        "export function rollPotential",
        "export function dailyGoldIncome",
        "export function dailyRiceConsumption",
        "export function villageXpMultiplier",
        "export function repairCost",
        "export function syncBonusJp",
    ],
    "src/game/jutsu.ts": [
        "export function jutsuFlavour",
        "export function jutsuMechanics",
        "Math.max(0, n.bonusJp ?? 0)",
    ],
    "src/game/genjutsu.ts": [
        "export function genjutsuFlavour",
        "export function genjutsuMechanics",
    ],
    "src/game/equipment.ts": [
        "export type EquipmentArt",
        "export function itemBonusTags",
        "export function forgeDiscount",
        "Equipment is completely unrestricted",
    ],
    "src/game/content.ts": [
        '"academy", "forge", "market", "archive"',
        "academy_chakra_theory",
        "forge_masterwork_bench",
        "archive_forbidden_vault",
        "market_war_chest",
    ],
    "src/game/types.ts": [
        '| "academy" | "forge" | "archive" | "market"',
        "bonusJp?: number;",
    ],
    "src/components/EquipmentArtwork.tsx": ["export default function EquipmentArtwork"],
    "src/components/Scene.tsx": ["function ResourceForecast"],
    "src/components/NinjaEquipment.tsx": ["ANY FOUR PIECES · NO RESTRICTIONS"],
    "src/components/JutsuTree.tsx": ["jutsuMechanics(j)"],
    "src/components/GenjutsuTree.tsx": ["genjutsuMechanics(g)"],
}

for rel, needles in CHECKS.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v17 check failed: {needle!r} missing from {rel}")

sw = ROOT / "public/sw.js"
sw_text = sw.read_text(encoding="utf-8")
if "kage-life-v17-gameplay-polish" not in sw_text:
    sw.write_text(
        sw_text.replace("shadow-village-main-polish-v1", "kage-life-v17-gameplay-polish", 1),
        encoding="utf-8",
    )

print("v17 gameplay polish applied")
