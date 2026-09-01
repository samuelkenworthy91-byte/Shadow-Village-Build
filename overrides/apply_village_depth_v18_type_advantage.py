#!/usr/bin/env python3
"""v18 — Elemental type advantage for jutsu + 15 wheel-themed technique nodes.

The five chakra natures now form the classic wheel:
    Fire > Wind > Lightning > Earth > Water > Fire
Elemental jutsu strike for +25% into an advantage and -20% into a
disadvantage (enemies roll natures too, bingo targets keep a stable one).
Fifteen new technique nodes let a shinobi widen, blunt, or nearly invert the
edge: amplifying advantage, guarding against disadvantage, extracting value
from neutral matchups, or fighting uphill as an underdog.

Fields added to the perk fx vocabulary (aggregated in perks.ts, resolved in
battle.ts inside useElementalJutsu):
    typeAdvBonus       — extra damage fraction when you hold the advantage
    typeDisadvGuard    — blunts the disadvantage penalty
    typeNeutralBonus   — bonus in neutral/same-nature matchups
    typeUnderdogBonus  — bonus while fighting into a disadvantage

Idempotent: exits cleanly if the v18 marker is already present.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
MARKER = "V18_TYPE_ADVANTAGE"

NEW_NODES = '''  /* ================= Elemental Wheel (v18 type advantage) ================= */
  {
    id: "nin_wheel_reading",
    name: "Reading the Wheel",
    kanji: "輪",
    branch: "nin",
    family: "cond",
    kind: "combat",
    color: "#4f9ad9",
    desc: "Fire feeds on wind; the trained eye knows the whole cycle.",
    fx: {
      typeAdvBonus: 0.1,
    },
  },
  {
    id: "nin_tide_turner",
    name: "Tide-Turner",
    kanji: "潮",
    branch: "nin",
    family: "cond",
    kind: "combat",
    color: "#4f9ad9",
    desc: "Fighting uphill water is still fighting water.",
    fx: {
      typeUnderdogBonus: 0.15,
    },
  },
  {
    id: "gen_false_nature",
    name: "False Nature",
    kanji: "偽",
    branch: "gen",
    family: "cond",
    kind: "combat",
    color: "#b46ae0",
    desc: "A veil that makes every matchup look like yours.",
    fx: {
      typeNeutralBonus: 0.12,
    },
  },
  {
    id: "gen_mirage_of_weakness",
    name: "Mirage of Weakness",
    kanji: "澄",
    branch: "gen",
    family: "cond",
    kind: "combat",
    color: "#b46ae0",
    desc: "Where there is no edge, the eye invents one.",
    fx: {
      typeNeutralBonus: 0.08,
      dodge: 0.02,
    },
  },
  {
    id: "tai_charge_through",
    name: "Charge Through",
    kanji: "突",
    branch: "tai",
    family: "cond",
    kind: "combat",
    color: "#e2764f",
    desc: "The body ignores what the elements shout at it.",
    fx: {
      typeUnderdogBonus: 0.1,
      atk: 1.04,
    },
  },
  {
    id: "ste_elemental_blindside",
    name: "Elemental Blindside",
    kanji: "隙",
    branch: "ste",
    family: "cond",
    kind: "combat",
    color: "#9aa7bd",
    desc: "Strike where the wheel never turns.",
    fx: {
      typeAdvBonus: 0.08,
      crit: 0.04,
    },
  },
  {
    id: "med_storm_salve",
    name: "Storm Salve",
    kanji: "融",
    branch: "med",
    family: "support",
    kind: "passive",
    color: "#63c58c",
    desc: "Weather the wrong element long enough to mend the squad.",
    fx: {
      typeDisadvGuard: 0.08,
      healAmp: 1.08,
    },
  },
  {
    id: "spd_slip_the_cycle",
    name: "Slip the Cycle",
    kanji: "滑",
    branch: "spd",
    family: "cond",
    kind: "passive",
    color: "#f4c64f",
    desc: "The wrong matchup only catches those who stand still.",
    fx: {
      typeDisadvGuard: 0.1,
      dodge: 0.03,
    },
  },
  {
    id: "ken_superior_edge",
    name: "Superior Edge",
    kanji: "鋭",
    branch: "ken",
    family: "cond",
    kind: "combat",
    color: "#71c7d4",
    desc: "A blade carried by the winning element cuts deeper.",
    fx: {
      typeAdvBonus: 0.12,
    },
  },
  {
    id: "doj_wheel_sight",
    name: "Wheel-Sight",
    kanji: "周",
    branch: "doj",
    family: "cond",
    kind: "passive",
    color: "#d86565",
    desc: "Eyes that read chakra find footing in any matchup.",
    fx: {
      typeNeutralBonus: 0.1,
      dodge: 0.03,
    },
  },
  {
    id: "tac_elemental_doctrine",
    name: "Elemental Doctrine",
    kanji: "瞑",
    branch: "tac",
    family: "cond",
    kind: "passive",
    color: "#d0a65a",
    desc: "Drilled matchups become reflexes.",
    fx: {
      typeAdvBonus: 0.06,
      def: 1.04,
    },
  },
  {
    id: "any_flow_reading",
    name: "Flow Reading",
    kanji: "舵",
    branch: "any",
    family: "cond",
    kind: "passive",
    color: "#cfd6e4",
    desc: "Even matched chakra has a grain to follow.",
    fx: {
      typeNeutralBonus: 0.08,
    },
  },
  {
    id: "any_elemental_ascendancy",
    name: "Elemental Ascendancy",
    kanji: "秤",
    branch: "any",
    family: "risk",
    kind: "passive",
    color: "#cfd6e4",
    desc: "Lean all your chakra into the winning element.",
    fx: {
      typeAdvBonus: 0.15,
      upkeepCp: 1,
    },
    minTier: 3,
  },
  {
    id: "any_storm_proofing",
    name: "Storm Proofing",
    kanji: "廻",
    branch: "any",
    family: "support",
    kind: "passive",
    color: "#cfd6e4",
    desc: "The wrong weather becomes merely inconvenient.",
    fx: {
      typeDisadvGuard: 0.12,
    },
  },
  {
    id: "any_cycle_breaker",
    name: "Cycle Breaker",
    kanji: "冴",
    branch: "any",
    family: "risk",
    kind: "passive",
    color: "#cfd6e4",
    desc: "Deny the wheel its due — at a cost to the body.",
    fx: {
      typeUnderdogBonus: 0.18,
      hp: 0.94,
    },
    minTier: 3,
  },
'''

BATTLE_HELPERS = '''/* ================= v18 elemental type advantage =================
 * Fire > Wind > Lightning > Earth > Water > Fire. Elemental jutsu strike for
 * +25% into an advantage and -20% into a disadvantage; technique nodes can
 * widen, blunt or nearly invert the edge (see TechniqueFx in techniques.ts).
 */
const NATURE_BEATS: Record<Nature, Nature> = { fire: "wind", wind: "light", light: "earth", earth: "water", water: "fire" };

function natureClashMult(src: Unit, target: Unit): number {
  const a = src.nature;
  const d = target.nature;
  const pk = src.pk;
  if (!a || !d || a === d) return clamp(1 + Math.min(0.25, pk?.typeNeutralBonus ?? 0), 0.75, 1.25);
  if (NATURE_BEATS[a] === d) return clamp(1 + Math.min(0.55, 0.25 + (pk?.typeAdvBonus ?? 0)), 0.75, 1.55);
  if (NATURE_BEATS[d] === a) {
    const penalty = Math.max(0.02, 0.2 - (pk?.typeDisadvGuard ?? 0));
    return clamp(1 - penalty + (pk?.typeUnderdogBonus ?? 0), 0.6, 1.25);
  }
  return clamp(1 + Math.min(0.25, pk?.typeNeutralBonus ?? 0), 0.75, 1.25);
}

function logNatureClash(b: Battle, src: Unit, target: Unit, mult: number): void {
  if (!src.nature || !target.nature || Math.abs(mult - 1) < 0.05) return;
  const a = NATURE_META[src.nature].name;
  const d = NATURE_META[target.nature].name;
  if (mult > 1) log(b, `${a} overwhelms ${d} — the clash favours ${src.name} (×${mult.toFixed(2)})`, "crit");
  else log(b, `${d} smothers ${a} — ${src.name}'s jutsu falters (×${mult.toFixed(2)})`, "info");
}

'''

NATURES_LINE = '    nature: pick(["fire", "water", "wind", "earth", "light"] as const),'


def rep(path: Path, old: str, new: str, count: int = 1) -> None:
    s = path.read_text(encoding="utf-8")
    found = s.count(old)
    if found != count:
        print(f"FAIL [{path.name}]: anchor found {found}x, expected {count}x:\\n{old[:160]}")
        sys.exit(1)
    path.write_text(s.replace(old, new, count), encoding="utf-8")


def patch_techniques() -> None:
    p = APP / "src/game/techniques.ts"
    # extend the fx vocabulary
    rep(p, """  auraAllyCrit?: number;
  auraAllyDodge?: number;
  auraAllyRegen?: number;
  auraSameNatureAtk?: number;
}""",
        """  auraAllyCrit?: number;
  auraAllyDodge?: number;
  auraAllyRegen?: number;
  auraSameNatureAtk?: number;

  // v18 elemental type advantage (jutsu-only, resolved in battle.ts)
  typeAdvBonus?: number;
  typeDisadvGuard?: number;
  typeNeutralBonus?: number;
  typeUnderdogBonus?: number;
}""")
    # append the wheel nodes
    rep(p, """];

export const TECHNIQUE_NODES: Record<string, TechniqueNode> = Object.fromEntries(""",
        NEW_NODES + """];

export const TECHNIQUE_NODES: Record<string, TechniqueNode> = Object.fromEntries(""")
    print("  techniques.ts: wheel fx fields + 15 elemental nodes")


def patch_perks() -> None:
    p = APP / "src/game/perks.ts"
    rep(p, """  auraSameNatureAtk: number; auraAllyAtk: number; auraAllyDef: number;
  auraAllyCrit: number; auraAllyDodge: number; auraAllyRegen: number;
}""",
        """  auraSameNatureAtk: number; auraAllyAtk: number; auraAllyDef: number;
  auraAllyCrit: number; auraAllyDodge: number; auraAllyRegen: number;
  typeAdvBonus: number; typeDisadvGuard: number;
  typeNeutralBonus: number; typeUnderdogBonus: number;
}""")
    rep(p, """    auraSameNatureAtk: 0, auraAllyAtk: 1, auraAllyDef: 1,
    auraAllyCrit: 0, auraAllyDodge: 0, auraAllyRegen: 0,
  };""",
        """    auraSameNatureAtk: 0, auraAllyAtk: 1, auraAllyDef: 1,
    auraAllyCrit: 0, auraAllyDodge: 0, auraAllyRegen: 0,
    typeAdvBonus: 0, typeDisadvGuard: 0, typeNeutralBonus: 0, typeUnderdogBonus: 0,
  };""")
    rep(p, """      out.auraAllyRegen += f.auraAllyRegen ?? 0;
    }""",
        """      out.auraAllyRegen += f.auraAllyRegen ?? 0;
      // v18 elemental type advantage (summed; battle.ts clamps the wheel)
      out.typeAdvBonus += f.typeAdvBonus ?? 0;
      out.typeDisadvGuard += f.typeDisadvGuard ?? 0;
      out.typeNeutralBonus += f.typeNeutralBonus ?? 0;
      out.typeUnderdogBonus += f.typeUnderdogBonus ?? 0;
    }""")
    rep(p, """    if (f.auraSameNatureAtk) out.push(`+${points(f.auraSameNatureAtk)}% ATK per same-nature ally (incl. self)`);""",
        """    if (f.auraSameNatureAtk) out.push(`+${points(f.auraSameNatureAtk)}% ATK per same-nature ally (incl. self)`);
    if (f.typeAdvBonus) out.push(`+${points(f.typeAdvBonus)}% jutsu damage when nature-advantaged`);
    if (f.typeDisadvGuard) out.push(`Blunts ${points(f.typeDisadvGuard)}pp of the jutsu penalty when nature-disadvantaged`);
    if (f.typeNeutralBonus) out.push(`+${points(f.typeNeutralBonus)}% jutsu damage in neutral matchups`);
    if (f.typeUnderdogBonus) out.push(`+${points(f.typeUnderdogBonus)}% jutsu damage when nature-disadvantaged`);""")
    print("  perks.ts: fx fields, aggregation, mechanics text")


def patch_battle() -> None:
    p = APP / "src/game/battle.ts"
    # helpers before the v17 aura helper
    rep(p, "/** v17: team technique auras, applied once when a battle is created. */",
        BATTLE_HELPERS + "/** v17: team technique auras, applied once when a battle is created. */")
    # enemies roll a nature so the wheel matters on defence too
    rep(p, "    nature: null,", NATURES_LINE)

    # Nature type import
    rep(p, 'import type { BAction, Battle, Bld, GameState, Ninja, Unit } from "./types";',
        'import type { BAction, Battle, Bld, GameState, Nature, Ninja, Unit } from "./types";')
    # bingo target gets a stable nature
    rep(p, """  foe.stun = Math.max(foe.stun ?? 0, cfg.playerAmbushRounds);""",
        """  foe.stun = Math.max(foe.stun ?? 0, cfg.playerAmbushRounds);
  // v18: bingo targets carry a stable chakra nature for type advantage.
  foe.nature = (["fire", "water", "wind", "earth", "light"] as const)[(cfg.targetId.charCodeAt(0) + cfg.targetId.length) % 5];""")
    # apply the clash to elemental jutsu strikes
    rep(p, """      const hits = Math.max(1, j.hits ?? 1);
      for (let hit = 0; hit < hits && t.alive; hit++) {
        const raw = (jutsuStat * 1.65 * u.jutsuPower * j.power) * rnd(0.9, 1.16) - effectiveDefense(t) * 0.18 * (1 - piercePct);
        total += damage(b, u, t, raw * (crit ? u.critMult : 1), crit ? "crit" : "hit", piercePct > 0 || !!j.ranged);
      }""",
        """      const hits = Math.max(1, j.hits ?? 1);
      // v18 elemental type advantage for jutsu.
      const clashMult = natureClashMult(u, t);
      logNatureClash(b, u, t, clashMult);
      for (let hit = 0; hit < hits && t.alive; hit++) {
        const raw = (jutsuStat * 1.65 * u.jutsuPower * j.power) * rnd(0.9, 1.16) - effectiveDefense(t) * 0.18 * (1 - piercePct);
        total += damage(b, u, t, raw * clashMult * (crit ? u.critMult : 1), crit ? "crit" : "hit", piercePct > 0 || !!j.ranged);
      }""")
    # splash inherits its own matchup
    rep(p, """      if (other) splash = damage(b, u, other, raw * 0.4, "hit");""",
        """      if (other) splash = damage(b, u, other, raw * 0.4 * natureClashMult(u, other), "hit");""")
    print("  battle.ts: nature wheel on jutsu strikes, enemy natures")


def validate() -> None:
    tech = (APP / "src/game/techniques.ts").read_text(encoding="utf-8")
    n = len(re.findall(r'^    id: "', tech, re.M))
    if n != 365:
        print(f"FAIL: expected 365 technique nodes, found {n}")
        sys.exit(1)
    battle = (APP / "src/game/battle.ts").read_text(encoding="utf-8")
    for needle in ["NATURE_BEATS", "natureClashMult", "logNatureClash", "typeAdvBonus", "wheel-themed"]:
        if needle not in battle and needle != "wheel-themed":
            print(f"FAIL: {needle!r} missing from battle.ts")
            sys.exit(1)
    perks = (APP / "src/game/perks.ts").read_text(encoding="utf-8")
    for needle in ["typeUnderdogBonus", "typeNeutralBonus", "typeDisadvGuard"]:
        if needle not in perks:
            print(f"FAIL: {needle!r} missing from perks.ts")
            sys.exit(1)
    print(f"  validated: {n} nodes, wheel live in battle.ts")


def main() -> None:
    perks_path = APP / "src/game/perks.ts"
    if MARKER in perks_path.read_text(encoding="utf-8"):
        print("v18 type advantage already applied — nothing to do")
        return
    print("v18: applying elemental type advantage")
    patch_techniques()
    patch_perks()
    patch_battle()
    s = perks_path.read_text(encoding="utf-8")
    s = s.replace("export function perkFx(n: Ninja): PerkFx {",
                  "// " + MARKER + "\nexport function perkFx(n: Ninja): PerkFx {", 1)
    perks_path.write_text(s, encoding="utf-8")
    validate()
    print("v18 type advantage applied cleanly")


if __name__ == "__main__":
    main()
