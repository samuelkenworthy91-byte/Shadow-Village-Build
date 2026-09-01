"""v29: regenerate ninja portraits individually + fair no-repeat art selection.

Part 1 - Portrait replacement: overrides/ninja_assets_v29/direct holds
individually generated portraits (ids 251-370, filling up over time) that
replace the sheet-cropped versions in app/public/ninjas. Each is generated
solo on a pure white background and cut with a gentle pipeline (flood-fill
background removal with NO morphological closing, so under-arm and
between-leg gaps stay transparent; strict near-canvas-only defringe, so
pale faces are never eaten).

Part 2 - Fair art selection: the old assignment hashed the ninja into the
pool (uniform WITH replacement), so two recruits could land on the same
portrait. New recruits now draw uniformly from the portraits not yet used
by the roster (sampled without replacement, no duplicates until the pool
is exhausted; falls back to the legacy hash afterwards). Existing saves
keep their portraits exactly as they were.

Runs after apply_ninja_portraits_v28.py and before the v18/v19 patches.
"""

import subprocess
from pathlib import Path

ROOT = Path("app")
SRC = Path("overrides/ninja_assets_v29/direct")
OUT = ROOT / "public/ninjas"
TYPES = ROOT / "src/game/types.ts"
ENGINE = ROOT / "src/game/engine.ts"
ART = ROOT / "src/game/ninjaArt.ts"

# ---------------------------------------------------------------- Part 1
OUT.mkdir(parents=True, exist_ok=True)
replaced = []
for webp in sorted(SRC.glob("ninja_*.webp")):
    dst = OUT / (webp.stem + ".png")
    subprocess.run(["convert", str(webp), f"PNG32:{dst}"], check=True)
    replaced.append(webp.stem)
print(f"regenerated portraits installed: {len(replaced)}"
      + (f" ({replaced[0]}..{replaced[-1]})" if replaced else ""))

# ---------------------------------------------------------------- Part 2
# 2a. Ninja type gains an optional assigned portrait
t = TYPES.read_text(encoding="utf-8")
type_old = """export interface Ninja {
  id: number;
  name: string;
  seed: number;
  look: Look;"""
type_new = """export interface Ninja {
  id: number;
  name: string;
  seed: number;
  look: Look;
  /** Uniform no-repeat portrait assignment; unset = legacy hash art. */
  portrait?: number;"""
if type_new in t:
    print("types.ts: portrait field already present")
elif type_old in t:
    t = t.replace(type_old, type_new, 1)
    TYPES.write_text(t, encoding="utf-8")
else:
    raise RuntimeError("expected Ninja interface head not found in types.ts")

# 2b. ninjaArtId honours the assigned portrait (legacy ninjas keep hash art)
a = ART.read_text(encoding="utf-8")
art_old = """export function ninjaArtId(n: { id: number; look: Look; legend?: string | null }): number {
  // Legendary ninjas deliberately use the same unrestricted pool.
  // Include immutable appearance rolls as salt so sequential IDs distribute well."""
art_new = """export function ninjaArtId(n: { id: number; look: Look; legend?: string | null; portrait?: number }): number {
  // Assigned portraits (uniform no-repeat draw) win; legacy saves fall through
  // to the hash so existing ninjas never change appearance.
  if (typeof n.portrait === "number" && n.portrait >= 1 && n.portrait <= GENERAL_ART_IDS.length) {
    return n.portrait;
  }
  // Legendary ninjas deliberately use the same unrestricted pool.
  // Include immutable appearance rolls as salt so sequential IDs distribute well."""
if art_new in a:
    print("ninjaArt.ts: portrait fast path already present")
elif art_old in a:
    a = a.replace(art_old, art_new, 1)
    ART.write_text(a, encoding="utf-8")
else:
    raise RuntimeError("expected ninjaArtId head not found in ninjaArt.ts")

# 2c. makeNinja draws uniformly from the unused portraits
e = ENGINE.read_text(encoding="utf-8")
imp_old = 'import { startBattle, startExamBattle } from "./battle";'
imp_new = 'import { startBattle, startExamBattle } from "./battle";\nimport { GENERAL_ART_IDS, ninjaArtId } from "./ninjaArt";'
if imp_new in e:
    pass
elif imp_old in e:
    e = e.replace(imp_old, imp_new, 1)
else:
    raise RuntimeError("expected engine import line not found")

mk_old = """  };
  return n;
}


export function bingoRecruitChance(s: GameState, targetId: string): number {"""
mk_new = """  };
  // Uniform draw WITHOUT replacement: every unused portrait is equally likely
  // and no two recruits share art until the pool is exhausted.
  const usedArt = new Set<number>();
  for (const m of s.ninjas) usedArt.add(ninjaArtId(m));
  const freeArt = GENERAL_ART_IDS.filter((artId) => !usedArt.has(artId));
  if (freeArt.length) n.portrait = freeArt[Math.floor(Math.random() * freeArt.length)];
  return n;
}


export function bingoRecruitChance(s: GameState, targetId: string): number {"""
if "const freeArt = GENERAL_ART_IDS.filter" in e:
    print("engine.ts: no-repeat portrait draw already present")
elif mk_old in e:
    e = e.replace(mk_old, mk_new, 1)
    ENGINE.write_text(e, encoding="utf-8")
else:
    raise RuntimeError("expected makeNinja tail not found in engine.ts")

# ---------------------------------------------------------------- checks
t_chk = TYPES.read_text(encoding="utf-8")
a_chk = ART.read_text(encoding="utf-8")
e_chk = ENGINE.read_text(encoding="utf-8")
assert "portrait?: number" in t_chk
assert "n.portrait" in a_chk
assert "freeArt[Math.floor(Math.random() * freeArt.length)]" in e_chk
assert "import { GENERAL_ART_IDS, ninjaArtId }" in e_chk
pngs = sorted(OUT.glob("ninja_*.png"))
assert len(pngs) == 370, f"expected 370 portraits, found {len(pngs)}"
for stem in replaced:
    assert (OUT / f"{stem}.png").is_file()
print("Applied v29: individual portrait regeneration + fair no-repeat art selection")
