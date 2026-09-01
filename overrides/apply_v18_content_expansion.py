"""Kage Life v18 content expansion.

Three additions, applied as one reviewed patch plus the summon art payload.

  1. Bingo Book presentation. The endgame screen was styled like every other
     panel — flat dark cards on a flat dark background. It now reads as a
     physical hunter's ledger: aged paper ground, ruled case-file lines,
     threat-tiered dossier edges, rotated verdict stamps (TERMINATED / IN
     CUSTODY / DEFECTED), a sweeping intel bar, a pulsing redaction on
     unidentified targets, a live danger sweep on the active hunt banner, and a
     stage-pip track showing hunt progress.

  2. Animal summons — a separate gacha and a third progression axis. A summon
     that only added stats would be a second equipment slot, and one you spend
     chakra to activate would be a second Jutsu. Summons instead run on
     INTERVENTIONS: a once-per-battle effect that fires automatically when its
     trigger condition is met, costing neither chakra nor the ninja's turn.
     Each also carries an always-on bond so an unspent intervention is never a
     wasted slot. The bonded creature is drawn beside the ninja's portrait.

  3. Tree variety. The elemental Jutsu lanes were built from one small pool of
     effects, so mid-tree choices across elements were often the same decision
     in a different colour. Five new mechanics — drain, mark, echo, siphon and
     momentum — each anchor a new fifth lane per element, and two new Genjutsu
     schools (Famine, Reflection) attack the chakra economy and turn the
     victim's own aggression against them.
"""

from pathlib import Path
import shutil
import subprocess

ROOT = Path("app")
PATCH = Path("overrides/v18_content_expansion.patch")
ART = Path("summon_assets_v18")

if not ROOT.exists():
    raise SystemExit("app/ has not been unpacked yet")
if not PATCH.exists():
    raise SystemExit(f"missing patch payload: {PATCH}")
if not ART.is_dir():
    raise SystemExit(f"missing summon art payload: {ART}")

# The Kage Life branch build reuses the already-patched main artifact, so this
# step must be safe to run twice.
already = (ROOT / "src/game/summons.ts").exists()
if already:
    print("v18 content expansion: already applied, verifying only")
else:
    subprocess.run(
        ["patch", "-p1", "--forward"],
        cwd=ROOT,
        input=PATCH.read_bytes(),
        check=True,
    )

# Summon artwork is binary, so it ships as a payload directory rather than
# inside the text patch.
dest = ROOT / "public/summons"
dest.mkdir(parents=True, exist_ok=True)
copied = 0
for png in sorted(ART.glob("*.png")):
    shutil.copy2(png, dest / png.name)
    copied += 1
if copied != 10:
    raise SystemExit(f"expected 10 summon images, copied {copied}")

CHECKS = {
    "src/game/summons.ts": [
        "export const SUMMONS: SummonDef[]",
        "export function pullSummons",
        "export function bondSummon",
        "export function summonMechanics",
        'export type SummonTrigger',
        "sum_toad", "sum_hawk", "sum_wolf", "sum_serpent", "sum_monkey",
        "sum_turtle", "sum_beetle", "sum_crane", "sum_boar", "sum_fox",
    ],
    "src/game/battle.ts": [
        "function fireSummon",
        "function fireSummonsForSide",
        'fireSummon(b, target, "bonded_fatal")',
        'fireSummonsForSide(b, target.foe, "ally_fallen")',
        'fireSummon(b, u, "chakra_empty")',
        "function doActionInner",
        # new jutsu mechanics
        'case "mark"', 'case "echo"', 'case "siphon"',
        "momentumMult", "reflectFeedUid", "cpBurnRounds",
    ],
    "src/game/jutsu.ts": [
        '| "drain"', '| "mark"', '| "echo"', '| "siphon"', '| "momentum"',
        '...F("consumption"', '...W("erosion"', '...A("delay"',
        '...E("siphon"', '...L("cascade"',
    ],
    "src/game/genjutsu.ts": [
        '...path("famine"', '...path("reflection"',
        "burnCpRounds", "reflectRounds", "feedPct",
    ],
    "src/components/SummonScreen.tsx": [
        "export default function SummonScreen",
        "export function NinjaSummonPanel",
        "export function SummonArt",
    ],
    "src/components/NinjaSprite.tsx": ["/summons/${pact.art}.png"],
    "src/components/GenjutsuTree.tsx": ["PATH_ORDER", "famine:", "reflection:"],
    "src/components/BingoBookScreen.tsx": [
        "bingo-paper", "bingo-card", "bingo-stamp", "intel-fill",
        "bingo-redacted", "hunt-live", "stage-pip",
    ],
    "src/index.css": [
        ".bingo-paper", ".bingo-stamp", ".intel-fill", ".hunt-live",
        ".stage-pip", ".summon-reveal",
    ],
    "src/App.tsx": ['tab === "summons"', "SummonScreen"],
    "src/game/types.ts": ["summonId?: string | null;", "markRounds?: number;", "momentum?: number;"],
    "src/game/save.ts": ["ensureSummonState(state)"],
}

for rel, needles in CHECKS.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v18 check failed: {needle!r} missing from {rel}")

for name in ("toad", "hawk", "wolf", "serpent", "monkey", "turtle", "beetle", "crane", "boar", "fox"):
    if not (dest / f"{name}.png").exists():
        raise SystemExit(f"v18 check failed: missing summon art {name}.png")

print(f"v18 content expansion applied ({copied} summon images)")
