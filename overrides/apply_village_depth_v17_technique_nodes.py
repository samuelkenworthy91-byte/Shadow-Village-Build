#!/usr/bin/env python3
"""v17 — Technique tree overhaul: 350 hand-crafted standard-ninja nodes.

Replaces the retired generic tree pool with a 350-node technique catalogue
(overrides/src/game/techniques.ts) spanning ten skill branches and eleven
mechanic families: flat stats, conditional power, triggered statuses, ramps,
risk/reward, once-per-battle powers, team auras, support, economy, village
effects and signature techniques. Each ninja's personal tree now rolls from
this pool with family-diverse tiers, so every shinobi develops differently.

Uniques, legendaries and identity-gated nodes (trait/nature/kekkei genkai)
are untouched and keep rolling exactly as before.

Mechanics are aggregated in perks.ts (perkFx) and resolved in battle.ts:
  - conditional damage scalars (opening round, vs statuses, low HP, focus, ...)
  - attack/crit status procs (burn/poison/bleed/shred/slow/stun)
  - ramping stacks, upkeep costs, chakra siphon, kill spoils
  - death-defy and unleashed-strike once-per-battle powers
  - team auras at battle start (startBattle / startExamBattle / startBingoBattle)
  - generic signature-technique riders (aoe/weakest/execute/pierce/stun/status/heal)

Idempotent: exits cleanly if the v17 marker is already present.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
MARKER = "V17_TECHNIQUE_OVERHAUL"

RETIRE = """// v17: the original 73 generic tree nodes were retired from new rolls in favour
// of the 350-node technique catalogue. They stay in PERKS as legacy data so
// existing saves keep every learned technique, and frozen rows referencing
// them still resolve (see TREE_TECHNIQUE_REPLACEMENTS above).
const RETIRED_GENERIC_TREE_NODES = new Set([
  "ironbody", "leafwhirl", "gatekeeper", "counterstance", "chakraflow", "shadowclone", "elemental", "sealing",
  "minddagger", "mirrorveil", "nightmare", "ambush", "vanish", "assassinate", "fieldmedic", "regeneration",
  "mysticrevive", "flashstep", "swiftlegs", "thunderfang", "swordform", "precisiondraw", "bladeward", "chakrablade",
  "twinblade", "ocularawakening", "predictiveeye", "chakrasight", "mirrorgaze", "awareness", "formationreading",
  "targetpriority", "counterplan", "commandassault", "veteran", "willoffire", "scholar", "crushingform", "evasiondrill",
  "relentless", "efficientmoulding", "chakraarmor", "greatrelease", "falseopening", "mindshield", "bindingillusion",
  "smokecraft", "vitalstrike", "ghostwalk", "chakraantidote", "surgicalstrike", "chakrarelay", "acceleration",
  "pursuit", "flashbarrage", "duelist", "heavyblade", "perfectedge", "peripheraleye", "intentreading", "crimsonfocus",
  "commandvoice", "killzone", "perfectplan", "impactconditioning", "sensoryfeint", "mindpressure", "illusiondiscipline",
  "blindspotstudy", "chakracompression", "chakraweaving", "ocularprecision", "oculartempo",
]);"""


def rep(path: Path, old: str, new: str, count: int = 1) -> None:
    s = path.read_text(encoding="utf-8")
    found = s.count(old)
    if found != count:
        print(f"FAIL [{path.name}]: anchor found {found}x, expected {count}x:\n{old[:160]}")
        sys.exit(1)
    path.write_text(s.replace(old, new, count), encoding="utf-8")


def patch_types() -> None:
    p = APP / "src/game/types.ts"
    rep(p, """  /** Permanent learned Jutsu mastery modifiers copied into the transient battle unit. */""",
        f"""  /** v17 technique development: aggregated perk combat state (player units). */
  pk?: import("./perks").PerkFx;
  /** v17 ramping technique stacks, ticked at the start of each round. */
  rampAtkStacks?: number;
  rampDefStacks?: number;
  /** v17 focus tracking: consecutive hits on the same target. */
  focusUid?: string | null;
  focusStacks?: number;
  /** v17 once-per-battle power flags. */
  deathDefyUsed?: boolean;
  unleashUsed?: boolean;

  /** Permanent learned Jutsu mastery modifiers copied into the transient battle unit. */""")
    print("  types.ts: unit technique state")


def patch_perks() -> None:
    p = APP / "src/game/perks.ts"

    # import the catalogue
    rep(p, 'import type { Nature, Ninja, Skill, TraitId, VillageTechId } from "./types";',
        'import type { Nature, Ninja, Skill, TraitId, VillageTechId } from "./types";\n'
        'import { TECHNIQUE_NODES, type TechniqueFamily, type TechniqueFx, type TechniqueTech } from "./techniques";')

    # Perk interface: adopt the extended fx/tech vocabulary + family tag
    rep(p, """  /** combat effects */
  fx?: {
    atk?: number;        // multiplier
    def?: number;
    hp?: number;
    cp?: number;
    crit?: number;       // +chance
    critMult?: number;
    dodge?: number;
    lifesteal?: number;
    counter?: number;
    regen?: number;
    firstStrike?: boolean;
    special?: boolean;   // grants the 奥義 command
    jutsu?: number;       // elemental jutsu damage multiplier
  };
  /** signature technique data */
  tech?: { name: string; power: number; stat: Skill; hits: number; note: string };""",
        """  /** combat effects (v17: full technique vocabulary, see techniques.ts) */
  fx?: TechniqueFx;
  /** signature technique data (v17: includes generic riders) */
  tech?: TechniqueTech;""")

    rep(p, """  /** zero-based earliest tree tier (0 = level 2, 4 = level 10) */
  minTier?: number;
}""",
        """  /** zero-based earliest tree tier (0 = level 2, 4 = level 10) */
  minTier?: number;
  /** v17 mechanic family — keeps each tree tier's offers genuinely different */
  family?: TechniqueFamily;
}""")

    # fold the catalogue into the perk registry right after PERKS is declared
    rep(p, """/* ---------------- per-ninja tree generation ---------------- */""",
        """// v17: fold the 350-node technique catalogue into the perk registry.
Object.assign(PERKS, TECHNIQUE_NODES as unknown as Record<string, Perk>);

/* ---------------- per-ninja tree generation ---------------- */""")

    # retire the old generic pool
    rep(p, """// Legacy rows are mapped onto working stat/mission development nodes.""",
        RETIRE + """

// Legacy rows are mapped onto working stat/mission development nodes.""")

    rep(p, """  const eligible = ALL_IDS.filter((id) => {
    if (OBSOLETE_TREE_TECHNIQUES.has(id)) return false;""",
        """  const eligible = ALL_IDS.filter((id) => {
    if (OBSOLETE_TREE_TECHNIQUES.has(id)) return false;
    if (RETIRED_GENERIC_TREE_NODES.has(id)) return false;""")

    # family-diverse tier filling with a fallback pass
    rep(p, """    for (const id of pool) {
      if (row.length >= want) break;
      if (used.has(id)) continue;
      const p = PERKS[id];
      if (p.minTier != null && t < p.minTier) continue;
      if (p.kind === "signature" && t < signatureMinTier) continue;
      pushUnique(row, p, want);
    }
    tiers.push(row);""",
        """    // v17: each tier offers distinct mechanic families so a row never reads as
    // three copies of the same stat stick. The family filter only skips; a
    // second pass fills the row if the diversity pass left it short.
    const famOf = (q: Perk) => q.family ?? (q.kind === "signature" ? "signature" : "stat");
    const tierFams = new Set<string>(row.map(famOf));
    const wantFam = (q: Perk) => {
      if (tierFams.has(famOf(q))) return false;
      tierFams.add(famOf(q));
      return true;
    };
    for (const id of pool) {
      if (row.length >= want) break;
      if (used.has(id)) continue;
      const p = PERKS[id];
      if (p.minTier != null && t < p.minTier) continue;
      if (p.kind === "signature" && t < signatureMinTier) continue;
      if (!wantFam(p)) continue;
      pushUnique(row, p, want);
    }
    for (const id of pool) {
      if (row.length >= want) break;
      if (used.has(id)) continue;
      const p = PERKS[id];
      if (p.minTier != null && t < p.minTier) continue;
      if (p.kind === "signature" && t < signatureMinTier) continue;
      pushUnique(row, p, want);
    }
    tiers.push(row);""")

    # PerkFx gains the aggregated technique mechanics
    rep(p, """export interface PerkFx {
  atk: number; def: number; hp: number; cp: number;
  crit: number; critMult: number; dodge: number;
  lifesteal: number; counter: number; regen: number;
  firstStrike: boolean; special: Perk | null;
  missionBonus: number; fatigue: number; healFast: number; xp: number;
  allyAtk: number; jutsu: number;
}""",
        """export interface PerkFx {
  atk: number; def: number; hp: number; cp: number;
  crit: number; critMult: number; dodge: number;
  lifesteal: number; counter: number; regen: number;
  firstStrike: boolean; special: Perk | null;
  missionBonus: number; fatigue: number; healFast: number; xp: number;
  allyAtk: number; jutsu: number;
  /* v17 technique mechanics — aggregated here, resolved in battle.ts */
  proc: TechniqueProc | null;
  critProc: TechniqueProc | null;
  killHealPct: number; killCpPct: number; cpDrainPct: number;
  healAmp: number; guardAmp: number;
  firstRoundAtk: number; firstBloodAtk: number;
  lowHpAtk: number; lowHpAtkBelow: number;
  lowHpDef: number; lowHpDefBelow: number;
  vsLowHpAtk: number; vsLowHpBelow: number;
  vsBurnAtk: number; vsPoisonAtk: number; vsBleedAtk: number; vsStunnedAtk: number; vsShreddedAtk: number;
  outnumberedAtk: number; outnumberedDef: number; lastStandDef: number; allyHurtAtk: number;
  rampAtkPerRound: number; rampAtkMax: number;
  rampDefPerRound: number; rampDefMax: number;
  rampCritPerRound: number; rampCritMax: number;
  focusAtkPerHit: number; focusAtkMax: number;
  upkeepHpPct: number; upkeepCp: number;
  deathDefyPct: number; unleashMult: number;
  auraSameNatureAtk: number; auraAllyAtk: number; auraAllyDef: number;
  auraAllyCrit: number; auraAllyDodge: number; auraAllyRegen: number;
}""")

    # import the proc type for PerkFx
    rep(p, 'import { TECHNIQUE_NODES, type TechniqueFamily, type TechniqueFx, type TechniqueTech } from "./techniques";',
        'import { TECHNIQUE_NODES, type TechniqueFamily, type TechniqueFx, type TechniqueProc, type TechniqueTech } from "./techniques";')

    # perkFx: extended defaults
    rep(p, """  const out: PerkFx = {
    atk: 1, def: 1, hp: 1, cp: 1, crit: 0, critMult: 0, dodge: 0,
    lifesteal: 0, counter: 0, regen: 0, firstStrike: false, special: null,
    missionBonus: 0, fatigue: 1, healFast: 0, xp: 1, allyAtk: 1, jutsu: 1,
  };""",
        """  const out: PerkFx = {
    atk: 1, def: 1, hp: 1, cp: 1, crit: 0, critMult: 0, dodge: 0,
    lifesteal: 0, counter: 0, regen: 0, firstStrike: false, special: null,
    missionBonus: 0, fatigue: 1, healFast: 0, xp: 1, allyAtk: 1, jutsu: 1,
    proc: null, critProc: null, killHealPct: 0, killCpPct: 0, cpDrainPct: 0,
    healAmp: 1, guardAmp: 1, firstRoundAtk: 1, firstBloodAtk: 1,
    lowHpAtk: 1, lowHpAtkBelow: 0.4, lowHpDef: 1, lowHpDefBelow: 0.4,
    vsLowHpAtk: 1, vsLowHpBelow: 0.3,
    vsBurnAtk: 1, vsPoisonAtk: 1, vsBleedAtk: 1, vsStunnedAtk: 1, vsShreddedAtk: 1,
    outnumberedAtk: 1, outnumberedDef: 1, lastStandDef: 1, allyHurtAtk: 1,
    rampAtkPerRound: 0, rampAtkMax: 0, rampDefPerRound: 0, rampDefMax: 0,
    rampCritPerRound: 0, rampCritMax: 0, focusAtkPerHit: 0, focusAtkMax: 0,
    upkeepHpPct: 0, upkeepCp: 0, deathDefyPct: 0, unleashMult: 1,
    auraSameNatureAtk: 0, auraAllyAtk: 1, auraAllyDef: 1,
    auraAllyCrit: 0, auraAllyDodge: 0, auraAllyRegen: 0,
  };""")

    # perkFx: aggregation rules
    rep(p, """      if (f.firstStrike) out.firstStrike = true;
      if (f.special && p.tech) out.special = p;
      out.jutsu *= f.jutsu ?? 1;
    }""",
        """      if (f.firstStrike) out.firstStrike = true;
      if (f.special && p.tech) out.special = p;
      out.jutsu *= f.jutsu ?? 1;
      // v17 technique mechanics — multipliers multiply, thresholds keep the
      // strongest bonus, procs keep the highest chance, ramps and upkeep sum.
      if (f.proc && (!out.proc || f.proc.chance > out.proc.chance)) out.proc = f.proc;
      if (f.critProc && (!out.critProc || f.critProc.chance > out.critProc.chance)) out.critProc = f.critProc;
      out.killHealPct = Math.max(out.killHealPct, f.killHealPct ?? 0);
      out.killCpPct = Math.max(out.killCpPct, f.killCpPct ?? 0);
      out.cpDrainPct = Math.max(out.cpDrainPct, f.cpDrainPct ?? 0);
      out.healAmp *= f.healAmp ?? 1;
      out.guardAmp *= f.guardAmp ?? 1;
      out.firstRoundAtk *= f.firstRoundAtk ?? 1;
      out.firstBloodAtk *= f.firstBloodAtk ?? 1;
      if (f.lowHpAtk && f.lowHpAtk > out.lowHpAtk) { out.lowHpAtk = f.lowHpAtk; out.lowHpAtkBelow = f.lowHpAtkBelow ?? 0.4; }
      if (f.lowHpDef && f.lowHpDef > out.lowHpDef) { out.lowHpDef = f.lowHpDef; out.lowHpDefBelow = f.lowHpDefBelow ?? 0.4; }
      if (f.vsLowHpAtk && f.vsLowHpAtk > out.vsLowHpAtk) { out.vsLowHpAtk = f.vsLowHpAtk; out.vsLowHpBelow = f.vsLowHpBelow ?? 0.3; }
      out.vsBurnAtk *= f.vsBurnAtk ?? 1;
      out.vsPoisonAtk *= f.vsPoisonAtk ?? 1;
      out.vsBleedAtk *= f.vsBleedAtk ?? 1;
      out.vsStunnedAtk *= f.vsStunnedAtk ?? 1;
      out.vsShreddedAtk *= f.vsShreddedAtk ?? 1;
      out.outnumberedAtk *= f.outnumberedAtk ?? 1;
      out.outnumberedDef *= f.outnumberedDef ?? 1;
      out.lastStandDef *= f.lastStandDef ?? 1;
      out.allyHurtAtk *= f.allyHurtAtk ?? 1;
      out.rampAtkPerRound += f.rampAtkPerRound ?? 0;
      out.rampAtkMax += f.rampAtkMax ?? 0;
      out.rampDefPerRound += f.rampDefPerRound ?? 0;
      out.rampDefMax += f.rampDefMax ?? 0;
      out.rampCritPerRound += f.rampCritPerRound ?? 0;
      out.rampCritMax += f.rampCritMax ?? 0;
      out.focusAtkPerHit += f.focusAtkPerHit ?? 0;
      out.focusAtkMax += f.focusAtkMax ?? 0;
      out.upkeepHpPct += f.upkeepHpPct ?? 0;
      out.upkeepCp += f.upkeepCp ?? 0;
      out.deathDefyPct = Math.max(out.deathDefyPct, f.deathDefyPct ?? 0);
      out.unleashMult = Math.max(out.unleashMult, f.unleashMult ?? 1);
      out.auraSameNatureAtk += f.auraSameNatureAtk ?? 0;
      out.auraAllyAtk *= f.auraAllyAtk ?? 1;
      out.auraAllyDef *= f.auraAllyDef ?? 1;
      out.auraAllyCrit += f.auraAllyCrit ?? 0;
      out.auraAllyDodge += f.auraAllyDodge ?? 0;
      out.auraAllyRegen += f.auraAllyRegen ?? 0;
    }""")

    # proc phrasing table
    rep(p, """const pctDelta = (mult: number) => Math.round((mult - 1) * 100);""",
        """const PROC_TEXT: Record<string, string> = {
  burn: "ignite", poison: "poison", bleed: "open a bleeding wound",
  shred: "shred guard", slow: "slow", stun: "stun",
};

const pctDelta = (mult: number) => Math.round((mult - 1) * 100);""")

    # perkMechanics: render the new vocabulary
    rep(p, """    if (f.firstStrike) out.push("Acts first in the opening round; +12 initiative on later rounds");
    if (f.jutsu != null && f.jutsu !== 1) out.push(`Jutsu damage ${pctDelta(f.jutsu) >= 0 ? "+" : ""}${pctDelta(f.jutsu)}%`);
  }""",
        """    if (f.firstStrike) out.push("Acts first in the opening round; +12 initiative on later rounds");
    if (f.jutsu != null && f.jutsu !== 1) out.push(`Jutsu damage ${pctDelta(f.jutsu) >= 0 ? "+" : ""}${pctDelta(f.jutsu)}%`);
    // v17 technique mechanics
    if (f.proc) out.push(`${points(f.proc.chance)}% chance on strikes to ${PROC_TEXT[f.proc.status] ?? f.proc.status} for ${f.proc.rounds} rounds`);
    if (f.critProc) out.push(`${points(f.critProc.chance)}% chance on criticals to ${PROC_TEXT[f.critProc.status] ?? f.critProc.status} for ${f.critProc.rounds} rounds`);
    if (f.killHealPct) out.push(`Finishing a foe restores ${points(f.killHealPct)}% max HP`);
    if (f.killCpPct) out.push(`Finishing a foe restores ${points(f.killCpPct)}% max chakra`);
    if (f.cpDrainPct) out.push(`Each hit siphons ${points(f.cpDrainPct)}% of the target's max chakra`);
    if (f.healAmp != null && f.healAmp !== 1) out.push(`Healing ${pctDelta(f.healAmp) >= 0 ? "+" : ""}${pctDelta(f.healAmp)}%`);
    if (f.guardAmp != null && f.guardAmp !== 1) out.push(`Guard ${pctDelta(f.guardAmp) >= 0 ? "+" : ""}${pctDelta(f.guardAmp)}% damage reduction`);
    if (f.firstRoundAtk) out.push(`+${pctDelta(f.firstRoundAtk)}% damage in the opening round`);
    if (f.firstBloodAtk) out.push(`+${pctDelta(f.firstBloodAtk)}% damage vs undamaged foes`);
    if (f.lowHpAtk) out.push(`+${pctDelta(f.lowHpAtk)}% damage below ${points(f.lowHpAtkBelow ?? 0.4)}% HP`);
    if (f.lowHpDef) out.push(`${pctDelta(f.lowHpDef) >= 0 ? "+" : ""}${pctDelta(f.lowHpDef)}% defence below ${points(f.lowHpDefBelow ?? 0.4)}% HP`);
    if (f.vsLowHpAtk) out.push(`+${pctDelta(f.vsLowHpAtk)}% damage vs foes below ${points(f.vsLowHpBelow ?? 0.3)}% HP`);
    if (f.vsBurnAtk) out.push(`+${pctDelta(f.vsBurnAtk)}% damage vs burning foes`);
    if (f.vsPoisonAtk) out.push(`+${pctDelta(f.vsPoisonAtk)}% damage vs poisoned foes`);
    if (f.vsBleedAtk) out.push(`+${pctDelta(f.vsBleedAtk)}% damage vs bleeding foes`);
    if (f.vsStunnedAtk) out.push(`+${pctDelta(f.vsStunnedAtk)}% damage vs stunned foes`);
    if (f.vsShreddedAtk) out.push(`+${pctDelta(f.vsShreddedAtk)}% damage vs shredded foes`);
    if (f.outnumberedAtk) out.push(`+${pctDelta(f.outnumberedAtk)}% damage when outnumbered`);
    if (f.outnumberedDef) out.push(`${pctDelta(f.outnumberedDef) >= 0 ? "+" : ""}${pctDelta(f.outnumberedDef)}% defence when outnumbered`);
    if (f.lastStandDef) out.push(`${pctDelta(f.lastStandDef) >= 0 ? "+" : ""}${pctDelta(f.lastStandDef)}% defence as the last one standing`);
    if (f.allyHurtAtk) out.push(`+${pctDelta(f.allyHurtAtk)}% damage while an ally is hurt or down`);
    if (f.rampAtkPerRound) out.push(`+${points(f.rampAtkPerRound)}% damage each round (max +${points(f.rampAtkMax ?? f.rampAtkPerRound * 5)}%)`);
    if (f.rampDefPerRound) out.push(`+${points(f.rampDefPerRound)}% defence each round (max +${points(f.rampDefMax ?? f.rampDefPerRound * 5)}%)`);
    if (f.rampCritPerRound) out.push(`+${points(f.rampCritPerRound)}pp crit each round (max +${points(f.rampCritMax ?? f.rampCritPerRound * 5)}pp)`);
    if (f.focusAtkPerHit) out.push(`+${points(f.focusAtkPerHit)}% damage per repeated hit on one target (max +${points(f.focusAtkMax ?? f.focusAtkPerHit * 5)}%)`);
    if (f.upkeepHpPct) out.push(`Sustains for ${points(f.upkeepHpPct)}% max HP per round (never fatal)`);
    if (f.upkeepCp) out.push(`Sustains for ${f.upkeepCp} chakra per round`);
    if (f.deathDefyPct) out.push(`Once per battle, survive a lethal blow at ${points(f.deathDefyPct)}% HP`);
    if (f.unleashMult) out.push(`First strike of each battle hits for ${Math.round(f.unleashMult * 100)}% damage`);
    if (f.auraAllyAtk) out.push(`Allies +${pctDelta(f.auraAllyAtk)}% ATK while deployed`);
    if (f.auraAllyDef) out.push(`Allies +${pctDelta(f.auraAllyDef)}% DEF while deployed`);
    if (f.auraAllyCrit) out.push(`Allies +${points(f.auraAllyCrit)}pp crit while deployed`);
    if (f.auraAllyDodge) out.push(`Allies +${points(f.auraAllyDodge)}pp dodge while deployed`);
    if (f.auraAllyRegen) out.push(`Allies +${f.auraAllyRegen} regen while deployed`);
    if (f.auraSameNatureAtk) out.push(`+${points(f.auraSameNatureAtk)}% ATK per same-nature ally (incl. self)`);
  }""")

    # perkMechanics: technique target phrasing + generic riders
    rep(p, """      const target = p.id === "shadowclone" || p.id === "lg_summon" ? "all enemies" : p.id === "assassinate" ? "the lowest-HP enemy" : "one enemy";
      out.push(`Combat technique ${t.name}: ${t.hits} hit${t.hits === 1 ? "" : "s"} at ${t.power.toFixed(2)}× ${SKILL_LABEL[t.stat]} scaling; targets ${target}`);""",
        """      const target = p.id === "shadowclone" || p.id === "lg_summon" || t.aoe ? "all enemies"
        : p.id === "assassinate" || t.weakest ? "the lowest-HP enemy"
        : t.heal ? "a wounded ally"
        : "one enemy";
      out.push(`Combat technique ${t.name}: ${t.hits} hit${t.hits === 1 ? "" : "s"} at ${t.power.toFixed(2)}× ${SKILL_LABEL[t.stat]} scaling; targets ${target}`);
      if (t.atk) out.push(`Technique strikes at ${Math.round(t.atk * 100)}% power`);
      if (t.aoe) out.push(t.heal ? "Technique restores every living ally" : "Technique strikes every foe");
      if (t.executeBelow) out.push(`Technique executes foes left below ${points(t.executeBelow)}% HP`);
      if (t.pierceGuard) out.push("Technique ignores Guard");
      if (t.stunRounds) out.push(`Technique stuns for ${t.stunRounds} rounds`);
      if (t.status) out.push(`Technique ${PROC_TEXT[t.status] ?? t.status}s for ${t.statusRounds ?? 2} rounds`);
      if (t.selfHealPct) out.push(`Technique restores ${points(t.selfHealPct)}% max HP after use`);
      if (t.cpDrainPct) out.push(`Technique drains ${points(t.cpDrainPct)}% of the target's max chakra`);""")

    print("  perks.ts: catalogue merge, retirement, family-diverse trees, fx aggregation, mechanics text")


BATTLE_HELPERS = '''/* ================= v17 technique development =================
 * Conditional damage scalars, triggered statuses, ramping stacks, team auras
 * and once-per-battle powers, all resolved from the aggregated perk state
 * carried on each player unit as `u.pk` (see perks.ts perkFx).
 */
function aliveAlliesOf(b: Battle, u: Unit): Unit[] {
  return b.units.filter((x) => x.alive && x.foe === u.foe);
}

function aliveFoesOf(b: Battle, u: Unit): Unit[] {
  return b.units.filter((x) => x.alive && x.foe !== u.foe);
}

function outgoingTechniqueMult(b: Battle, src: Unit | null, target: Unit): number {
  if (!src?.pk) return 1;
  const pk = src.pk;
  let m = 1;
  if (pk.firstRoundAtk > 1 && b.round === 1) m *= pk.firstRoundAtk;
  if (pk.firstBloodAtk > 1 && target.hp >= target.maxHp) m *= pk.firstBloodAtk;
  if (pk.vsLowHpAtk > 1 && target.hp / Math.max(1, target.maxHp) <= pk.vsLowHpBelow) m *= pk.vsLowHpAtk;
  if (pk.vsBurnAtk > 1 && (target.burnRounds ?? 0) > 0) m *= pk.vsBurnAtk;
  if (pk.vsPoisonAtk > 1 && (target.poisonRounds ?? 0) > 0) m *= pk.vsPoisonAtk;
  if (pk.vsBleedAtk > 1 && (target.bleedRounds ?? 0) > 0) m *= pk.vsBleedAtk;
  if (pk.vsStunnedAtk > 1 && (target.stun ?? 0) > 0) m *= pk.vsStunnedAtk;
  if (pk.vsShreddedAtk > 1 && (target.defShredRounds ?? 0) > 0) m *= pk.vsShreddedAtk;
  if (pk.lowHpAtk > 1 && src.hp / Math.max(1, src.maxHp) <= pk.lowHpAtkBelow) m *= pk.lowHpAtk;
  if (pk.outnumberedAtk > 1 && aliveFoesOf(b, src).length > aliveAlliesOf(b, src).length) m *= pk.outnumberedAtk;
  if (pk.allyHurtAtk > 1) {
    const friends = b.units.filter((x) => x.foe === src.foe);
    if (friends.some((x) => !x.alive || (x.uid !== src.uid && x.hp / Math.max(1, x.maxHp) < 0.45))) m *= pk.allyHurtAtk;
  }
  if (src.rampAtkStacks) m *= 1 + src.rampAtkStacks;
  if (src.focusUid === target.uid && src.focusStacks && pk.focusAtkPerHit > 0) m *= 1 + pk.focusAtkPerHit * src.focusStacks;
  if (pk.unleashMult > 1 && !src.unleashUsed) {
    src.unleashUsed = true;
    m *= pk.unleashMult;
    log(b, `${src.name} unleashes everything into the opening blow!`, "crit");
  }
  return m;
}

function incomingTechniqueMult(b: Battle, target: Unit): number {
  const pk = target.pk;
  if (!pk) return 1;
  let m = 1;
  if (pk.lowHpDef > 1 && target.hp / Math.max(1, target.maxHp) <= pk.lowHpDefBelow) m *= pk.lowHpDef;
  if (pk.lastStandDef > 1 && aliveAlliesOf(b, target).length === 1) m *= pk.lastStandDef;
  if (pk.outnumberedDef > 1 && aliveFoesOf(b, target).length > aliveAlliesOf(b, target).length) m *= pk.outnumberedDef;
  if (target.rampDefStacks) m *= 1 + target.rampDefStacks;
  return m;
}

function applyStatusProc(b: Battle, u: Unit, t: Unit, proc: { status: string; chance?: number; rounds: number; value?: number }): void {
  if (!t.alive) return;
  if (proc.chance != null && Math.random() >= proc.chance) return;
  const scale = Math.max(u.nin, u.atk * 0.7, u.ken * 0.9);
  const amount = Math.max(1, Math.round(proc.value ?? scale * (proc.status === "poison" ? 0.12 : proc.status === "bleed" ? 0.13 : 0.14)));
  switch (proc.status) {
    case "burn":
      t.burnRounds = Math.max(t.burnRounds ?? 0, proc.rounds);
      t.burnDamage = Math.max(t.burnDamage ?? 0, amount);
      log(b, `${t.name} is set ablaze`, "hit");
      break;
    case "poison":
      t.poisonRounds = Math.max(t.poisonRounds ?? 0, proc.rounds);
      t.poisonDamage = Math.max(t.poisonDamage ?? 0, amount);
      log(b, `${t.name} is poisoned`, "hit");
      break;
    case "bleed":
      t.bleedRounds = Math.max(t.bleedRounds ?? 0, proc.rounds);
      t.bleedDamage = Math.max(t.bleedDamage ?? 0, amount);
      log(b, `${t.name} is bleeding`, "hit");
      break;
    case "shred":
      t.defShredRounds = Math.max(t.defShredRounds ?? 0, proc.rounds);
      t.defShredPct = Math.max(t.defShredPct ?? 0, 0.12);
      log(b, `${t.name}'s guard is shredded`, "info");
      break;
    case "slow":
      t.slowRounds = Math.max(t.slowRounds ?? 0, proc.rounds);
      t.slowPct = Math.max(t.slowPct ?? 0, 0.22);
      log(b, `${t.name} is slowed`, "info");
      break;
    case "stun":
      t.stun = Math.max(t.stun ?? 0, proc.rounds);
      log(b, `${t.name} is stunned`, "info");
      break;
  }
}

function applyAttackProcs(b: Battle, u: Unit, t: Unit, crit: boolean): void {
  const pk = u.pk;
  if (!pk || !t.alive) return;
  if (crit && pk.critProc) applyStatusProc(b, u, t, pk.critProc);
  if (pk.proc && pk.proc.status !== pk.critProc?.status) applyStatusProc(b, u, t, pk.proc);
}

function applyTechRiders(b: Battle, u: Unit, t: Unit, tech: TechniqueTech): void {
  if (t.alive) {
    if (tech.stunRounds) t.stun = Math.max(t.stun ?? 0, tech.stunRounds);
    if (tech.status) applyStatusProc(b, u, t, { status: tech.status, chance: 1, rounds: tech.statusRounds ?? 2 });
    if (tech.executeBelow && t.hp / Math.max(1, t.maxHp) <= tech.executeBelow) {
      const finishing = damage(b, u, t, t.hp * 1.5, "crit", true);
      log(b, `${tech.name} finds the killing angle — ${t.name} is cut down! (${finishing})`, "crit");
    }
  }
  if (tech.selfHealPct) {
    const heal = Math.max(1, Math.round(u.maxHp * tech.selfHealPct));
    u.hp = Math.min(u.maxHp, u.hp + heal);
    log(b, `${u.name} recovers ${heal} HP from ${tech.name}`, "heal");
  }
  if (tech.cpDrainPct && t.cp > 0) {
    const drained = Math.min(t.cp, Math.max(1, Math.round(t.maxCp * tech.cpDrainPct)));
    t.cp -= drained;
    u.cp = Math.min(u.maxCp, u.cp + drained);
  }
}

/** v17: team technique auras, applied once when a battle is created. */
export function applyTechniqueAuras(b: Battle): void {
  const allies = b.units.filter((x) => !x.foe && x.alive);
  for (const src of allies) {
    const pk = src.pk;
    if (!pk) continue;
    if (pk.auraAllyAtk > 1 || pk.auraAllyDef > 1 || pk.auraAllyCrit > 0 || pk.auraAllyDodge > 0 || pk.auraAllyRegen > 0) {
      for (const ally of allies) {
        if (ally.uid === src.uid) continue;
        if (pk.auraAllyAtk > 1) ally.atk *= pk.auraAllyAtk;
        if (pk.auraAllyDef > 1) ally.def *= pk.auraAllyDef;
        if (pk.auraAllyCrit > 0) ally.crit = clamp(ally.crit + pk.auraAllyCrit, 0, 0.85);
        if (pk.auraAllyDodge > 0) ally.dodge = clamp(ally.dodge + pk.auraAllyDodge, 0, 0.6);
        if (pk.auraAllyRegen > 0) ally.regen += pk.auraAllyRegen;
      }
    }
    if (pk.auraSameNatureAtk > 0 && src.nature) {
      const kin = allies.filter((x) => x.nature === src.nature).length;
      if (kin > 0) src.atk *= 1 + pk.auraSameNatureAtk * kin;
    }
  }
}

'''


def patch_battle() -> None:
    p = APP / "src/game/battle.ts"

    # type import for tech riders
    rep(p, 'import { combatTechniqueIds, lockTechniqueTree, perkById, perkFx } from "./perks";',
        'import { combatTechniqueIds, lockTechniqueTree, perkById, perkFx } from "./perks";\n'
        'import type { TechniqueTech } from "./techniques";')

    # carry the aggregated perk state on every player battle unit
    rep(p, """  return {
    uid: `p${n.id}`,""",
        """  return {
    pk: fx,
    uid: `p${n.id}`,""")

    # helper block before damage()
    rep(p, "function damage(b: Battle, src: Unit | null, target: Unit, raw: number, kind: \"hit\" | \"crit\", pierce = false): number {",
        BATTLE_HELPERS + "function damage(b: Battle, src: Unit | null, target: Unit, raw: number, kind: \"hit\" | \"crit\", pierce = false): number {")

    # conditional damage scalars
    rep(p, """  if (rt && src?.foe && !target.foe && rt.markedUid === target.uid && bingoHas(b, "marked_hunter")) raw *= 1.35;
  let dmg = Math.max(1, Math.round(raw));""",
        """  if (rt && src?.foe && !target.foe && rt.markedUid === target.uid && bingoHas(b, "marked_hunter")) raw *= 1.35;
  // v17 technique development: conditional damage scalars.
  if (src?.pk || target.pk) {
    raw *= outgoingTechniqueMult(b, src, target);
    raw /= incomingTechniqueMult(b, target);
  }
  let dmg = Math.max(1, Math.round(raw));""")

    # guardAmp tunes the Guard reduction itself
    rep(p, "    const guardReduction = target.guard ? 0.58 : 0;",
        "    const guardReduction = target.guard ? clamp(0.58 * (target.pk?.guardAmp ?? 1), 0.3, 0.8) : 0;")

    # chakra siphon + focus tracking after the lifesteal block
    rep(p, """  if (src && src.lifesteal > 0) {
    const heal = Math.round(dmg * src.lifesteal);
    if (heal > 0) {
      src.hp = Math.min(src.maxHp, src.hp + heal);
      log(b, `${src.name} drains ${heal} life`, "heal");
    }
  }""",
        """  if (src && src.lifesteal > 0) {
    const heal = Math.round(dmg * src.lifesteal);
    if (heal > 0) {
      src.hp = Math.min(src.maxHp, src.hp + heal);
      log(b, `${src.name} drains ${heal} life`, "heal");
    }
  }
  // v17: chakra siphon and focus tracking from technique development.
  if (src?.pk && src.uid !== target.uid && dmg > 0) {
    if (src.pk.cpDrainPct > 0 && target.cp > 0) {
      const drained = Math.min(target.cp, Math.max(1, Math.round(target.maxCp * src.pk.cpDrainPct)));
      target.cp -= drained;
      src.cp = Math.min(src.maxCp, src.cp + drained);
      log(b, `${src.name} siphons ${drained} chakra from ${target.name}`, "info");
    }
    if (src.pk.focusAtkPerHit > 0 && src.foe !== target.foe) {
      if (src.focusUid === target.uid) {
        src.focusStacks = Math.min(Math.floor(src.pk.focusAtkMax / src.pk.focusAtkPerHit), (src.focusStacks ?? 0) + 1);
      } else {
        src.focusUid = target.uid;
        src.focusStacks = 0;
      }
    }
  }""")

    # death-defy + kill spoils
    rep(p, """  if (target.hp <= 0) {
    target.alive = false;
    log(b, `${target.name} is down!`, "down");""",
        """  // v17: once-per-battle refusal to fall.
  if (target.hp <= 0 && target.pk?.deathDefyPct && !target.deathDefyUsed) {
    target.deathDefyUsed = true;
    target.hp = Math.max(1, Math.round(target.maxHp * target.pk.deathDefyPct));
    log(b, `${target.name} refuses to fall!`, "crit");
  }
  if (target.hp <= 0) {
    target.alive = false;
    log(b, `${target.name} is down!`, "down");
    // v17: kill spoils from technique development.
    if (src?.pk && src.alive && src.foe !== target.foe) {
      if (src.pk.killHealPct > 0) {
        const spoils = Math.max(1, Math.round(src.maxHp * src.pk.killHealPct));
        src.hp = Math.min(src.maxHp, src.hp + spoils);
        log(b, `${src.name} recovers ${spoils} HP from the finish`, "heal");
      }
      if (src.pk.killCpPct > 0) {
        const steadied = Math.max(1, Math.round(src.maxCp * src.pk.killCpPct));
        src.cp = Math.min(src.maxCp, src.cp + steadied);
        log(b, `${src.name} steadies their chakra (+${steadied})`, "info");
      }
    }""")

    # attack procs after a basic strike
    rep(p, """      const d = damage(b, u, t, raw, crit ? "crit" : "hit");
      log(b, `${u.name} strikes ${t.name} for ${d}${crit ? " — CRITICAL!" : ""}`, crit ? "crit" : "hit");""",
        """      const d = damage(b, u, t, raw, crit ? "crit" : "hit");
      log(b, `${u.name} strikes ${t.name} for ${d}${crit ? " — CRITICAL!" : ""}`, crit ? "crit" : "hit");
      applyAttackProcs(b, u, t, crit);""")

    # healAmp on the heal action
    rep(p, '      const boost = u.perks.includes("fieldmedic") ? 1.4 : 1;',
        '      const boost = (u.perks.includes("fieldmedic") ? 1.4 : 1) * (u.pk?.healAmp ?? 1);')

    # technique case: healing signatures + generic riders
    rep(p, """      // revival / mass heal
      if (p.id === "mysticrevive") {""",
        """      // v17: healing signature techniques restore wounded allies instead of striking.
      if (tech.heal && p.id !== "mysticrevive") {
        const amt = Math.max(1, Math.round(statVal * tech.power * (u.pk?.healAmp ?? 1) * rnd(0.95, 1.1)));
        const wounded = [...alliesSide].sort((a, z) => a.hp / a.maxHp - z.hp / z.maxHp);
        const chosen = tech.aoe
          ? [...alliesSide]
          : target && target.foe === u.foe && target.alive ? [target] : wounded.slice(0, 1);
        if (chosen.length) {
          for (const a of chosen) a.hp = Math.min(a.maxHp, a.hp + amt);
          b.flash = { uid: chosen[0].uid, amount: amt, kind: "heal", n: (b.flash?.n ?? 0) + 1 };
          log(b, `技 ${tech.name}! ${chosen.length > 1 ? `${chosen.length} allies recover` : `${chosen[0].name} recovers`} ${amt}`, "heal");
          return { kind: "heal", targets: chosen.map((a) => a.uid) };
        }
        return { kind: "none", targets: [] };
      }

      // revival / mass heal
      if (p.id === "mysticrevive") {""")

    rep(p, """      // all-target techniques
      if (p.id === "shadowclone" || p.id === "lg_summon") {
        let total = 0;
        for (const t of [...foesSide]) total += damage(b, u, t, statVal * tech.power * rnd(0.92, 1.1), "crit");""",
        """      // all-target techniques
      if (p.id === "shadowclone" || p.id === "lg_summon" || tech.aoe) {
        let total = 0;
        for (const t of [...foesSide]) {
          total += damage(b, u, t, statVal * tech.power * (tech.atk ?? 1) * rnd(0.92, 1.1), "crit");
          applyTechRiders(b, u, t, tech);
        }""")

    rep(p, """      const t = target && target.foe !== u.foe
        ? target
        : p.id === "assassinate"
          ? [...foesSide].sort((a, z) => a.hp - z.hp)[0]
          : foesSide[0];""",
        """      const t = target && target.foe !== u.foe
        ? target
        : p.id === "assassinate" || tech.weakest
          ? [...foesSide].sort((a, z) => a.hp - z.hp)[0]
          : foesSide[0];""")

    rep(p, """      let power = tech.power;
      if (p.id === "lg_beastcloak") power *= 1 + (1 - u.hp / u.maxHp) * 1.1;
      const pierce = p.id === "gatekeeper" || p.id === "lg_silentmist" || p.id === "kekkei_magma";""",
        """      let power = tech.power * (tech.atk ?? 1);
      if (p.id === "lg_beastcloak") power *= 1 + (1 - u.hp / u.maxHp) * 1.1;
      const pierce = p.id === "gatekeeper" || p.id === "lg_silentmist" || p.id === "kekkei_magma" || !!tech.pierceGuard;""")

    rep(p, """      if (p.id === "nightmare") t.stun = 2;
      log(b, `技 ${tech.name}! ${t.name} takes ${total}${tech.hits > 1 ? ` over ${tech.hits} hits` : ""}`, "crit");""",
        """      if (p.id === "nightmare") t.stun = 2;
      applyTechRiders(b, u, t, tech);
      log(b, `技 ${tech.name}! ${t.name} takes ${total}${tech.hits > 1 ? ` over ${tech.hits} hits` : ""}`, "crit");""")

    # ramps + upkeep at the start of each new round
    rep(p, """        u.cp = Math.min(u.maxCp, u.cp + baseCpRegen + u.regen);
        if (u.regen > 0) u.hp = Math.min(u.maxHp, u.hp + u.regen);""",
        """        u.cp = Math.min(u.maxCp, u.cp + baseCpRegen + u.regen);
        if (u.regen > 0) u.hp = Math.min(u.maxHp, u.hp + u.regen);
        // v17 technique development: ramping stacks and upkeep costs.
        const pk = u.pk;
        if (pk) {
          if (pk.rampAtkPerRound > 0) u.rampAtkStacks = Math.min(pk.rampAtkMax, (u.rampAtkStacks ?? 0) + pk.rampAtkPerRound);
          if (pk.rampDefPerRound > 0) u.rampDefStacks = Math.min(pk.rampDefMax, (u.rampDefStacks ?? 0) + pk.rampDefPerRound);
          if (pk.rampCritPerRound > 0) u.crit = clamp(u.crit + pk.rampCritPerRound, 0, 0.85);
          if (pk.upkeepHpPct > 0) {
            const cost = Math.max(1, Math.round(u.maxHp * pk.upkeepHpPct));
            if (u.hp > cost) {
              u.hp -= cost;
              log(b, `${u.name} pays ${cost} HP to sustain their technique`, "hit");
            } else if (u.hp > 1) {
              u.hp = 1;
              log(b, `${u.name}'s technique drains them to their last breath`, "hit");
            }
          }
          if (pk.upkeepCp > 0) u.cp = Math.max(0, u.cp - pk.upkeepCp);
        }""")

    # auras at every battle creation site (story, exam, bingo)
    rep(p, """  rollOrder(b, s.b.tower + (s.techs.includes("tower_rapid_response") ? 1 : 0), true);""",
        """  applyTechniqueAuras(b);
  rollOrder(b, s.b.tower + (s.techs.includes("tower_rapid_response") ? 1 : 0), true);""", count=2)
    rep(p, """  rollOrder(b, s.b.tower, true);""",
        """  applyTechniqueAuras(b);
  rollOrder(b, s.b.tower, true);""")

    print("  battle.ts: technique triggers, auras, riders, ramps")


def patch_perk_tree() -> None:
    p = APP / "src/components/PerkTree.tsx"
    rep(p, "This tree now prioritises passive combat, mission and stat development. A smaller number of non-Jutsu active combat techniques unlock into the Techniques submenu. Rows lock when their level is reached; future rows can still evolve with this ninja's skills, and no node can repeat.",
        "A personal path drawn from 350 hand-crafted techniques, keyed to this ninja's nature, traits and strongest skills — conditional powers, triggered statuses, ramping arts, once-per-battle trump cards, team auras and active signature techniques in the Techniques submenu. Rows lock as their level is reached; no node can repeat.")
    rep(p, "mt-0.5 line-clamp-4 text-[9px]", "mt-0.5 line-clamp-5 text-[9px]")
    print("  PerkTree.tsx: explainer + mechanics space")


def patch_sw() -> None:
    p = APP / "public/sw.js"
    rep(p, 'const CACHE = "kage-life-v1-village-identity"; // previous: shadow-village-main-polish-v1',
        'const CACHE = "kage-life-v2-technique-depth"; // previous: shadow-village-main-polish-v1, kage-life-v1-village-identity')
    print("  sw.js: cache bumped (v17 ships the technique catalogue)")


def validate() -> None:
    checks = [
        ("src/game/techniques.ts", "TECHNIQUE_NODE_COUNT"),
        ("src/game/perks.ts", "TECHNIQUE_NODES"),
        ("src/game/perks.ts", "RETIRED_GENERIC_TREE_NODES"),
        ("src/game/perks.ts", MARKER),
        ("src/game/battle.ts", "outgoingTechniqueMult"),
        ("src/game/battle.ts", "incomingTechniqueMult"),
        ("src/game/battle.ts", "deathDefyPct"),
        ("src/game/battle.ts", "applyTechniqueAuras"),
        ("src/game/battle.ts", "unleashMult"),
        ("src/components/PerkTree.tsx", "350 hand-crafted techniques"),
        ("public/sw.js", "kage-life-v2-technique-depth"),
    ]
    for rel, needle in checks:
        f = APP / rel
        if needle not in f.read_text(encoding="utf-8"):
            print(f"FAIL validation: {needle!r} missing from {rel}")
            sys.exit(1)

    battle = (APP / "src/game/battle.ts").read_text(encoding="utf-8")
    calls = battle.count("applyTechniqueAuras(b);")
    if calls != 3:
        print(f"FAIL validation: expected 3 applyTechniqueAuras call sites, found {calls}")
        sys.exit(1)

    from portrait_library import validate_assets
    validate_assets(max_id=310)

    # family diversity sanity: the catalogue itself
    tech = (APP / "src/game/techniques.ts").read_text(encoding="utf-8")
    n = tech.count('    id: "')
    if n != 350:
        print(f"FAIL validation: expected 350 technique nodes in techniques.ts, found {n}")
        sys.exit(1)
    print(f"  validated: 350 nodes, {calls} aura sites, approved portraits validated, cache bumped")


def main() -> None:
    perks = APP / "src/game/perks.ts"
    if MARKER in perks.read_text(encoding="utf-8"):
        print("v17 technique overhaul already applied — nothing to do")
        return

    print("v17: applying technique-node overhaul")
    src = ROOT / "overrides/src/game/techniques.ts"
    dest = APP / "src/game/techniques.ts"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    print(f"  techniques.ts: copied catalogue ({dest.stat().st_size // 1024} KB)")

    patch_types()
    patch_perks()
    patch_battle()
    patch_perk_tree()
    patch_sw()

    # drop the idempotency marker
    s = perks.read_text(encoding="utf-8")
    s = s.replace("const RETIRED_GENERIC_TREE_NODES = new Set([",
                  f"// {MARKER}\nconst RETIRED_GENERIC_TREE_NODES = new Set([", 1)
    perks.write_text(s, encoding="utf-8")

    validate()
    print("v17 technique overhaul applied cleanly")


if __name__ == "__main__":
    main()
