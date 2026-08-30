from pathlib import Path
import re

ROOT = Path("app")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, value: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding="utf-8")


def replace_once(rel: str, old: str, new: str, label: str) -> None:
    s = read(rel)
    if new in s:
        print(f"{label}: already applied")
        return
    if old not in s:
        raise SystemExit(f"{label}: anchor not found in {rel}")
    write(rel, s.replace(old, new, 1))
    print(f"{label}: applied")


# ---------------------------------------------------------------------------
# 1) More traits, all with explicit mechanical effects.
# ---------------------------------------------------------------------------
p = "src/game/types.ts"
s = read(p)
if '"battleHardened"' not in s:
    m = re.search(r'(export type TraitId\s*=\s*[\s\S]*?)(;)', s)
    if not m:
        raise SystemExit("TraitId union not found")
    additions = '''\n  | "battleHardened" | "quickLearner" | "chakraDense" | "precisionFighter" | "stubborn"\n  | "duelist" | "nightOperative" | "calmUnderFire" | "fieldSurvivor" | "missionVeteran"'''
    s = s[:m.end(1)] + additions + s[m.end(1):]

if "jutsuKnown?: string[];" not in s:
    anchor = "  /** unlocked tech-tree node ids */"
    if anchor not in s:
        raise SystemExit("Ninja perk anchor not found")
    s = s.replace(anchor, '''  /** Elemental jutsu learned in the dedicated jutsu tree. */\n  jutsuKnown?: string[];\n  /** Up to four learned jutsu taken into battle. */\n  jutsuEquipped?: string[];\n  /** Permanent potential increases earned from exceptional special missions. */\n  potentialRaises?: number;\n  /** unlocked tech-tree node ids */''', 1)
write(p, s)

p = "src/game/content.ts"
s = read(p)
if "battleHardened:" not in s:
    trait_insert = '''  battleHardened: { name: "Battle Hardened", desc: "+8% battle ATK and +8% battle DEF.", icon: "戦", rarity: "uncommon" },\n  quickLearner: { name: "Quick Learner", desc: "+15% XP from missions and combat.", icon: "学", rarity: "uncommon" },\n  chakraDense: { name: "Dense Chakra", desc: "+25% maximum chakra and +5% battle DEF.", boost: "nin", icon: "密", rarity: "rare" },\n  precisionFighter: { name: "Precision Fighter", desc: "+8 percentage points crit chance and +10 percentage points critical damage.", boost: "ken", icon: "精", rarity: "uncommon" },\n  stubborn: { name: "Stubborn", desc: "+10% maximum HP and +8% battle DEF, but mission fatigue +8%.", icon: "頑", rarity: "common" },\n  duelist: { name: "Duelist", desc: "Kenjutsu is a specialist skill; +7% battle ATK and +5 percentage points crit chance.", boost: "ken", icon: " duel", rarity: "uncommon" },\n  nightOperative: { name: "Night Operative", desc: "Stealth is a specialist skill; mission success +6 percentage points and dodge +4 percentage points.", boost: "ste", icon: "夜", rarity: "uncommon" },\n  calmUnderFire: { name: "Calm Under Fire", desc: "Battlefield Tactics is a specialist skill; +5% battle DEF and mission success +4 percentage points.", boost: "tac", icon: "静", rarity: "common" },\n  fieldSurvivor: { name: "Field Survivor", desc: "Mission fatigue -18% and battle DEF +5%.", icon: "生", rarity: "common" },\n  missionVeteran: { name: "Mission Veteran", desc: "Mission success +7 percentage points and mission fatigue -10%.", boost: "tac", icon: "歴", rarity: "rare" },\n'''
    marker = "\n};\n\nexport const TRAIT_IDS"
    pos = s.find(marker)
    if pos < 0:
        raise SystemExit("TRAIT_META closing marker not found")
    s = s[:pos] + "\n" + trait_insert + s[pos:]

# Replace the mission catalogue with a much wider first-pass pool: 10 per grade.
mission_block = '''export const MISSION_TEMPLATES: Record<Rank, MTemplate[]> = {\n  D: [\n    { name: "Find the Lost Cat Tama", desc: "A merchant's cat vanished into the roof district.", focus: ["spd", "ste"], slots: 1 },\n    { name: "Weed the Elder's Garden", desc: "Simple work, until the hornets arrive.", focus: ["tai"], slots: 1 },\n    { name: "Deliver the Sealed Letter", desc: "Carry a sealed message across the village without delay.", focus: ["spd", "tac"], slots: 1 },\n    { name: "Patch Up the Academy Class", desc: "The academy needs a medic after a training accident.", focus: ["med"], slots: 1 },\n    { name: "Dōjō Blade Drill", desc: "Help the academy run a supervised sword exercise.", focus: ["ken", "spd"], slots: 1 },\n    { name: "Scare Off Mushroom Thieves", desc: "Drive opportunistic thieves from the village stores.", focus: ["tai", "tac"], slots: 2 },\n    { name: "Repair the South Footbridge", desc: "Protect workers while the river crossing is repaired.", focus: ["tai", "tac"], slots: 2 },\n    { name: "Catch the Runaway Messenger Hawk", desc: "A trained hawk has escaped with a coded strip attached.", focus: ["spd", "ste"], slots: 1 },\n    { name: "Guard the Festival Lanterns", desc: "Prevent petty sabotage during the evening festival.", focus: ["ste", "tac"], slots: 2 },\n    { name: "Clear the Training Grounds", desc: "Remove traps and damaged targets before tomorrow's classes.", focus: ["nin", "tai"], slots: 2 },\n  ],\n  C: [\n    { name: "Escort the Tea Merchant", desc: "Bandits have been watching the eastern road.", focus: ["tac", "tai", "spd"], slots: 2 },\n    { name: "Catch the Rice Thief", desc: "Track a thief through the warehouse district.", focus: ["ste", "spd"], slots: 2 },\n    { name: "Break the Illusion Trap", desc: "Travellers report a false road appearing in the bamboo grove.", focus: ["gen", "nin"], slots: 2 },\n    { name: "Field Clinic at the Ford", desc: "Fever has spread through a riverside camp.", focus: ["med", "tac"], slots: 2 },\n    { name: "Map the Northern Pass", desc: "Survey a route before the next merchant convoy leaves.", focus: ["ste", "tac", "spd"], slots: 2 },\n    { name: "Challenge the Roadside Duelist", desc: "A travelling swordsman is harassing local guards.", focus: ["ken", "tac"], slots: 2 },\n    { name: "Guard the Shrine Procession", desc: "Escort priests through a district troubled by thieves.", focus: ["tac", "ste", "tai"], slots: 3 },\n    { name: "Investigate the Empty Village", desc: "A farming settlement stopped sending reports three days ago.", focus: ["ste", "gen", "tac"], slots: 3 },\n    { name: "Drive Off the River Pirates", desc: "Small pirate crews are raiding barges close to home.", focus: ["tai", "nin", "ken"], slots: 3 },\n    { name: "Recover the Stolen Medicine", desc: "A medical shipment disappeared before reaching the clinic.", focus: ["med", "ste", "spd"], slots: 2 },\n  ],\n  B: [\n    { name: "Infiltrate the Bandit Camp", desc: "Enter a fortified camp and identify its command structure.", focus: ["ste", "tac", "gen"], slots: 3 },\n    { name: "Retrieve the Stolen Scroll", desc: "Recover a village scroll before its seal is broken.", focus: ["ste", "nin", "tac"], slots: 3 },\n    { name: "Duel the Rogue Swordsman", desc: "A missing-nin swordsman has defeated three pursuing cells.", focus: ["ken", "spd", "tac"], slots: 3 },\n    { name: "Sabotage the Storehouse", desc: "Destroy enemy supplies without alerting the garrison.", focus: ["nin", "ste", "tac"], slots: 3 },\n    { name: "Rescue the Poisoned Caravan", desc: "Reach a trapped caravan before the poison takes hold.", focus: ["med", "spd", "tac"], slots: 3 },\n    { name: "Intercept the Border Couriers", desc: "Capture enemy dispatches moving between two outposts.", focus: ["spd", "ste", "tac"], slots: 3 },\n    { name: "Destroy the Hidden Bridge", desc: "Cut an enemy reinforcement route through the ravine.", focus: ["nin", "tai", "tac"], slots: 3 },\n    { name: "Expose the False Magistrate", desc: "Prove an infiltrator has replaced a regional official.", focus: ["gen", "ste", "tac"], slots: 3 },\n    { name: "Hunt the Marsh Beast", desc: "Something powerful is attacking patrols in the reed country.", focus: ["nin", "tai", "med"], slots: 4 },\n    { name: "Protect the Defecting Informant", desc: "Keep a valuable source alive until extraction.", focus: ["tac", "med", "ken"], slots: 4 },\n  ],\n  A: [\n    { name: "Silence the War-Horn Tower", desc: "Disable an enemy warning post before the army advances.", focus: ["ste", "nin", "tac"], slots: 3 },\n    { name: "Steal the Fox Lord's Ledger", desc: "Take proof of a hidden military alliance from a guarded estate.", focus: ["gen", "ste", "tac", "nin"], slots: 4 },\n    { name: "Extract the Captured Scout", desc: "Recover a captured operative before interrogation begins.", focus: ["med", "ste", "tac"], slots: 4 },\n    { name: "Hunt the Missing-nin", desc: "A former village operative is selling mission routes to the enemy.", focus: ["tac", "spd", "ken", "gen"], slots: 4 },\n    { name: "Read the Crimson Eye", desc: "An ocular bloodline user is dismantling every ambush sent against them.", focus: ["doj", "gen", "tac"], slots: 3 },\n    { name: "Break the Siege Engineers", desc: "Destroy siege equipment before it reaches allied walls.", focus: ["nin", "tai", "ken", "tac"], slots: 4 },\n    { name: "Escort the Daimyo's Envoy", desc: "Multiple factions want the envoy dead before negotiations begin.", focus: ["tac", "med", "spd", "gen"], slots: 4 },\n    { name: "Capture the Poison Master", desc: "Bring a notorious toxin specialist back alive.", focus: ["med", "ste", "tac", "spd"], slots: 4 },\n    { name: "Raid the Hidden Arsenal", desc: "Strike a weapons depot before its stock can be moved.", focus: ["ken", "nin", "ste", "tac"], slots: 4 },\n    { name: "Hold the Mountain Gate", desc: "Delay a superior enemy force long enough for civilians to escape.", focus: ["tai", "ken", "med", "tac"], slots: 4 },\n  ],\n  S: [\n    { name: "Storm the Obsidian Keep", desc: "Break a fortress believed to be impossible to assault directly.", focus: ["tac", "tai", "nin", "med"], slots: 4 },\n    { name: "Steal the Shogun's Seal", desc: "Enter the inner palace and remove a symbol of state authority.", focus: ["ste", "gen", "tac", "spd"], slots: 4 },\n    { name: "The Nine-Tailed Contract", desc: "Recover a forbidden summoning contract before another village claims it.", focus: ["nin", "gen", "med", "tac"], slots: 4 },\n    { name: "Sever the Serpent's Head", desc: "Eliminate the commander holding three provinces in fear.", focus: ["ken", "spd", "ste", "tac"], slots: 4 },\n    { name: "Mirror-Eye Conspiracy", desc: "Find the source of an ocular network predicting village deployments.", focus: ["doj", "tac", "gen", "ken"], slots: 4 },\n    { name: "Break the Five-Fortress Line", desc: "Open a route through a coordinated defensive network in one operation.", focus: ["tac", "nin", "ken", "med"], slots: 4 },\n    { name: "Recover the Forbidden Archive", desc: "Retrieve an archive of techniques from a collapsing underground complex.", focus: ["nin", "gen", "ste", "med"], slots: 4 },\n    { name: "Defend the Kage Summit", desc: "Protect multiple leaders from an assassination force already inside the venue.", focus: ["tac", "doj", "med", "ken"], slots: 4 },\n    { name: "Hunt the Living Weapon", desc: "Track a shinobi whose body has been altered into a battlefield weapon.", focus: ["nin", "tai", "med", "spd"], slots: 4 },\n    { name: "End the Silent War", desc: "Expose and dismantle a covert network operating inside allied territory.", focus: ["ste", "gen", "tac", "doj"], slots: 4 },\n  ],\n};'''
start = s.find('export const MISSION_TEMPLATES: Record<Rank, MTemplate[]> = {')
end = s.find('\n\nexport const NINJA_NAMES', start)
if start < 0 or end < 0:
    raise SystemExit("MISSION_TEMPLATES block not found")
s = s[:start] + mission_block + s[end:]
write(p, s)


# ---------------------------------------------------------------------------
# 2) Potential now creates visibly different long-term development curves.
# ---------------------------------------------------------------------------
p = "src/game/engine.ts"
s = read(p)
if "potentialDevelopmentMultiplier" not in s:
    anchor = 'const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));'
    if anchor not in s:
        raise SystemExit("engine clamp anchor not found")
    s = s.replace(anchor, anchor + '''\n\n/** Natural potential is intentionally a major long-term differentiator. */\nexport function potentialDevelopmentMultiplier(pot: number): number {\n  return ({ 1: 0.82, 2: 0.92, 3: 1.0, 4: 1.12, 5: 1.28 } as Record<number, number>)[Math.max(1, Math.min(5, Math.round(pot)))] ?? 1;\n}\n\nexport function potentialTrainingMultiplier(pot: number): number {\n  return ({ 1: 0.90, 2: 0.96, 3: 1.0, 4: 1.08, 5: 1.18 } as Record<number, number>)[Math.max(1, Math.min(5, Math.round(pot)))] ?? 1;\n}\n\nexport function increaseNaturalPotential(n: Ninja): boolean {\n  const raises = n.potentialRaises ?? 0;\n  if (n.pot >= 5 || raises >= 2) return false;\n  n.pot += 1;\n  n.potentialRaises = raises + 1;\n  for (const k of SKILLS) {\n    if (k === "doj" && !dojutsuAwakened(n)) continue;\n    n.growth[k] *= 1.08;\n  }\n  return true;\n}''', 1)

    anchor2 = '  if (legend) for (const k of SKILLS) {'
    if anchor2 not in s:
        raise SystemExit("makeNinja legend anchor not found")
    s = s.replace(anchor2, '''  // Potential affects both the generated growth profile and starting separation.\n  const potDev = potentialDevelopmentMultiplier(pot);\n  const startDelta = ({ 1: -2, 2: -1, 3: 0, 4: 1, 5: 3 } as Record<number, number>)[pot] ?? 0;\n  for (const k of SKILLS) {\n    if (growth[k] <= 0) continue;\n    growth[k] *= potDev;\n    sk[k] = Math.max(1, sk[k] + startDelta);\n  }\n  if (legend) for (const k of SKILLS) {''', 1)

old_gain = 'return Math.max(1, Math.round(1 + n.growth[k] * 1.4));'
new_gain = 'return Math.max(1, Math.round((1 + n.growth[k] * 1.4) * potentialTrainingMultiplier(n.pot)));'
if old_gain in s:
    s = s.replace(old_gain, new_gain, 1)
elif new_gain not in s:
    raise SystemExit("skillPointGain formula not found")
write(p, s)


# Trait mechanics hook into the existing perk/trait effect resolver.
p = "src/game/perks.ts"
s = read(p)
if 'case "battleHardened"' not in s:
    marker = '      case "naturalLeader": out.missionBonus += 0.08; out.allyAtk *= 1.05; break;'
    if marker not in s:
        raise SystemExit("perkFx trait switch marker not found")
    cases = '''      case "battleHardened": out.atk *= 1.08; out.def *= 1.08; break;\n      case "quickLearner": out.xp *= 1.15; break;\n      case "chakraDense": out.cp *= 1.25; out.def *= 1.05; break;\n      case "precisionFighter": out.crit += 0.08; out.critMult += 0.10; break;\n      case "stubborn": out.hp *= 1.10; out.def *= 1.08; out.fatigue *= 1.08; break;\n      case "duelist": out.atk *= 1.07; out.crit += 0.05; break;\n      case "nightOperative": out.missionBonus += 0.06; out.dodge += 0.04; break;\n      case "calmUnderFire": out.def *= 1.05; out.missionBonus += 0.04; break;\n      case "fieldSurvivor": out.fatigue *= 0.82; out.def *= 1.05; break;\n      case "missionVeteran": out.missionBonus += 0.07; out.fatigue *= 0.90; break;\n'''
    s = s.replace(marker, cases + marker, 1)
write(p, s)


# ---------------------------------------------------------------------------
# 3) Dedicated elemental jutsu tree data and UI.
# ---------------------------------------------------------------------------
jutsu_ts = r'''import type { Nature, Ninja } from "./types";

export type JutsuTarget = "foe" | "all_foes" | "ally" | "all_allies" | "self";
export type JutsuEffect = "burn" | "slow" | "guard" | "stun" | "pierce" | "crit" | "cleanse" | "regen" | "none";

export interface JutsuDef {
  id: string;
  name: string;
  nature: Nature;
  tier: number;
  levelReq: number;
  chakra: number;
  power: number;
  target: JutsuTarget;
  effect: JutsuEffect;
  effectValue?: number;
  desc: string;
}

const J = (x: JutsuDef) => x;

export const JUTSU: JutsuDef[] = [
  // FIRE — pressure, AoE and damage over time.
  J({ id: "fire_ember", name: "Ember Shot", nature: "fire", tier: 0, levelReq: 1, chakra: 5, power: 0.82, target: "foe", effect: "burn", effectValue: 2, desc: "Light single-target fire damage; burns for 2 rounds." }),
  J({ id: "fire_ball", name: "Great Fireball", nature: "fire", tier: 1, levelReq: 3, chakra: 9, power: 1.15, target: "foe", effect: "burn", effectValue: 2, desc: "Heavy fire damage with a 2-round burn." }),
  J({ id: "fire_phoenix", name: "Phoenix Flower", nature: "fire", tier: 2, levelReq: 6, chakra: 12, power: 0.72, target: "all_foes", effect: "burn", effectValue: 2, desc: "Hits every enemy and applies a lighter burn." }),
  J({ id: "fire_wall", name: "Flame Wall", nature: "fire", tier: 3, levelReq: 10, chakra: 13, power: 0.45, target: "all_foes", effect: "burn", effectValue: 3, desc: "Low immediate damage; strong 3-round burn across the enemy line." }),
  J({ id: "fire_dragon", name: "Fire Dragon", nature: "fire", tier: 4, levelReq: 15, chakra: 18, power: 1.55, target: "foe", effect: "burn", effectValue: 3, desc: "High single-target damage and a long burn." }),
  J({ id: "fire_inferno", name: "Inferno Field", nature: "fire", tier: 5, levelReq: 22, chakra: 24, power: 1.05, target: "all_foes", effect: "burn", effectValue: 3, desc: "End-game fire technique: strong AoE plus persistent burn." }),

  // WATER — control, protection and cleansing.
  J({ id: "water_bullet", name: "Water Bullet", nature: "water", tier: 0, levelReq: 1, chakra: 5, power: 0.80, target: "foe", effect: "slow", effectValue: 1, desc: "Reliable damage and a small speed reduction." }),
  J({ id: "water_prison", name: "Water Prison", nature: "water", tier: 1, levelReq: 3, chakra: 9, power: 0.72, target: "foe", effect: "slow", effectValue: 2, desc: "Moderate damage with a stronger initiative slow." }),
  J({ id: "water_wall", name: "Water Wall", nature: "water", tier: 2, levelReq: 6, chakra: 11, power: 0, target: "all_allies", effect: "guard", effectValue: 2, desc: "Reduces incoming damage for the whole squad for 2 rounds." }),
  J({ id: "water_cleanse", name: "Cleansing Current", nature: "water", tier: 3, levelReq: 10, chakra: 12, power: 0, target: "ally", effect: "cleanse", desc: "Removes burn, slow and stun effects from one ally." }),
  J({ id: "water_vortex", name: "Crushing Vortex", nature: "water", tier: 4, levelReq: 15, chakra: 17, power: 1.12, target: "all_foes", effect: "slow", effectValue: 2, desc: "AoE damage that drags down enemy initiative." }),
  J({ id: "water_tide", name: "Guardian Tide", nature: "water", tier: 5, levelReq: 22, chakra: 23, power: 0.35, target: "all_allies", effect: "regen", effectValue: 3, desc: "Restores health over 3 rounds and grants brief protection." }),

  // WIND — speed, multi-target pressure and defence penetration.
  J({ id: "wind_cutter", name: "Wind Cutter", nature: "wind", tier: 0, levelReq: 1, chakra: 5, power: 0.86, target: "foe", effect: "pierce", effectValue: 10, desc: "Fast attack that ignores 10% of defence." }),
  J({ id: "wind_scythe", name: "Vacuum Scythe", nature: "wind", tier: 1, levelReq: 3, chakra: 9, power: 1.02, target: "foe", effect: "pierce", effectValue: 18, desc: "Single-target cut ignoring 18% of defence." }),
  J({ id: "wind_fan", name: "Gale Fan", nature: "wind", tier: 2, levelReq: 6, chakra: 11, power: 0.68, target: "all_foes", effect: "pierce", effectValue: 10, desc: "Rapid AoE wind blades with light armour penetration." }),
  J({ id: "wind_step", name: "Gale Step", nature: "wind", tier: 3, levelReq: 10, chakra: 10, power: 0, target: "self", effect: "crit", effectValue: 12, desc: "Boosts initiative and critical chance for the next attacks." }),
  J({ id: "wind_pressure", name: "Pressure Lance", nature: "wind", tier: 4, levelReq: 15, chakra: 17, power: 1.48, target: "foe", effect: "pierce", effectValue: 30, desc: "High damage; ignores 30% of defence." }),
  J({ id: "wind_tempest", name: "Tempest Barrage", nature: "wind", tier: 5, levelReq: 22, chakra: 23, power: 1.08, target: "all_foes", effect: "pierce", effectValue: 22, desc: "End-game AoE that heavily penetrates defence." }),

  // EARTH — barriers, durability and stuns.
  J({ id: "earth_stone", name: "Stone Shot", nature: "earth", tier: 0, levelReq: 1, chakra: 5, power: 0.84, target: "foe", effect: "none", desc: "Efficient direct earth damage." }),
  J({ id: "earth_wall", name: "Earth Wall", nature: "earth", tier: 1, levelReq: 3, chakra: 8, power: 0, target: "all_allies", effect: "guard", effectValue: 2, desc: "Whole-squad damage reduction for 2 rounds." }),
  J({ id: "earth_grasp", name: "Stone Grasp", nature: "earth", tier: 2, levelReq: 6, chakra: 11, power: 0.78, target: "foe", effect: "stun", effectValue: 1, desc: "Moderate damage with a chance to lose the next action." }),
  J({ id: "earth_armour", name: "Stone Armour", nature: "earth", tier: 3, levelReq: 10, chakra: 12, power: 0, target: "ally", effect: "guard", effectValue: 3, desc: "Strong single-ally protection for 3 rounds." }),
  J({ id: "earth_quake", name: "Ground Rupture", nature: "earth", tier: 4, levelReq: 15, chakra: 18, power: 1.02, target: "all_foes", effect: "stun", effectValue: 1, desc: "AoE damage with a lower chance to stun each enemy." }),
  J({ id: "earth_fortress", name: "Living Fortress", nature: "earth", tier: 5, levelReq: 22, chakra: 23, power: 0, target: "all_allies", effect: "guard", effectValue: 4, desc: "End-game defensive field with heavy squad-wide protection." }),

  // LIGHTNING (legacy Nature id "light") — burst, crits and paralysis.
  J({ id: "light_spark", name: "Lightning Spark", nature: "light", tier: 0, levelReq: 1, chakra: 5, power: 0.88, target: "foe", effect: "crit", effectValue: 5, desc: "Quick burst with a small critical bonus." }),
  J({ id: "light_spear", name: "Lightning Spear", nature: "light", tier: 1, levelReq: 3, chakra: 10, power: 1.20, target: "foe", effect: "crit", effectValue: 10, desc: "High burst damage with increased crit chance." }),
  J({ id: "light_net", name: "Static Net", nature: "light", tier: 2, levelReq: 6, chakra: 12, power: 0.62, target: "all_foes", effect: "slow", effectValue: 2, desc: "AoE lightning that sharply reduces initiative." }),
  J({ id: "light_paralyse", name: "Thunder Needle", nature: "light", tier: 3, levelReq: 10, chakra: 13, power: 0.92, target: "foe", effect: "stun", effectValue: 1, desc: "Focused lightning with a strong paralysis chance." }),
  J({ id: "light_flash", name: "Flash Step Strike", nature: "light", tier: 4, levelReq: 15, chakra: 18, power: 1.52, target: "foe", effect: "crit", effectValue: 18, desc: "Very high burst and critical pressure." }),
  J({ id: "light_storm", name: "Heaven's Thunder", nature: "light", tier: 5, levelReq: 22, chakra: 25, power: 1.12, target: "all_foes", effect: "stun", effectValue: 1, desc: "End-game AoE lightning with a chance to paralyse every target." }),
];

export const JUTSU_BY_ID: Record<string, JutsuDef> = Object.fromEntries(JUTSU.map((j) => [j.id, j]));

export function ninjaNatures(n: Ninja): Nature[] {
  const out: Nature[] = [n.nature];
  if (n.secondaryNature && !out.includes(n.secondaryNature)) out.push(n.secondaryNature);
  return out;
}

export function jutsuForNinja(n: Ninja): JutsuDef[] {
  const have = new Set(ninjaNatures(n));
  return JUTSU.filter((j) => have.has(j.nature));
}

export function knownJutsuIds(n: Ninja): string[] {
  const naturalBasics = jutsuForNinja(n).filter((j) => j.tier === 0).map((j) => j.id);
  return Array.from(new Set([...naturalBasics, ...(n.jutsuKnown ?? [])]));
}

export function jutsuPointsTotal(n: Ninja): number {
  return Math.floor(n.level / 3);
}

export function jutsuPointsSpent(n: Ninja): number {
  return (n.jutsuKnown ?? []).filter((id) => (JUTSU_BY_ID[id]?.tier ?? 0) > 0).length;
}

export function jutsuPointsAvailable(n: Ninja): number {
  return Math.max(0, jutsuPointsTotal(n) - jutsuPointsSpent(n));
}

export function canLearnJutsu(n: Ninja, id: string): boolean {
  const j = JUTSU_BY_ID[id];
  if (!j || j.tier === 0 || !ninjaNatures(n).includes(j.nature)) return false;
  if (knownJutsuIds(n).includes(id) || n.level < j.levelReq || jutsuPointsAvailable(n) <= 0) return false;
  if (j.tier <= 1) return true;
  return knownJutsuIds(n).some((known) => JUTSU_BY_ID[known]?.nature === j.nature && JUTSU_BY_ID[known]?.tier === j.tier - 1);
}

export function learnJutsu(n: Ninja, id: string): boolean {
  if (!canLearnJutsu(n, id)) return false;
  n.jutsuKnown = [...(n.jutsuKnown ?? []), id];
  return true;
}

export function toggleJutsuEquip(n: Ninja, id: string): boolean {
  if (!knownJutsuIds(n).includes(id)) return false;
  const eq = [...(n.jutsuEquipped ?? [])].filter((x) => knownJutsuIds(n).includes(x));
  if (eq.includes(id)) {
    n.jutsuEquipped = eq.filter((x) => x !== id);
    return true;
  }
  if (eq.length >= 4) return false;
  n.jutsuEquipped = [...eq, id];
  return true;
}
'''
write("src/game/jutsu.ts", jutsu_ts)

jutsu_tree = r'''import type { Ninja } from "../game/types";
import { JUTSU, canLearnJutsu, jutsuPointsAvailable, knownJutsuIds, learnJutsu, ninjaNatures, toggleJutsuEquip } from "../game/jutsu";
import { NATURE_META } from "../game/content";
import { cn } from "../utils/cn";

export default function JutsuTree({ n, onChanged }: { n: Ninja; onChanged: () => void }) {
  const known = new Set(knownJutsuIds(n));
  const equipped = new Set(n.jutsuEquipped ?? []);
  const natures = ninjaNatures(n);
  const points = jutsuPointsAvailable(n);

  const learn = (id: string) => {
    if (learnJutsu(n, id)) onChanged();
  };
  const equip = (id: string) => {
    if (toggleJutsuEquip(n, id)) onChanged();
  };

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-2">
        <div>
          <p className="text-[9px] font-black tracking-[0.18em] text-gold/75">ELEMENTAL JUTSU TREE</p>
          <p className="mt-0.5 text-[9px] leading-relaxed text-paper/45">One Jutsu Point every 3 levels. Learn only your natural element(s); equip up to 4 for battle.</p>
        </div>
        <div className="shrink-0 rounded-lg bg-black/30 px-2 py-1 text-center ring-1 ring-white/8">
          <p className="text-[8px] font-black tracking-wider text-paper/40">JUTSU PTS</p>
          <p className="text-sm font-black tabular-nums text-gold">{points}</p>
        </div>
      </div>

      <div className="space-y-3">
        {natures.map((nature) => {
          const meta = NATURE_META[nature];
          const rows = JUTSU.filter((j) => j.nature === nature).sort((a, b) => a.tier - b.tier);
          return (
            <div key={nature} className="rounded-xl bg-black/20 p-2 ring-1 ring-white/7">
              <div className="mb-2 flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-lg text-sm font-black" style={{ backgroundColor: `${meta.color}22`, color: meta.color }}>{meta.kanji}</span>
                <div>
                  <p className="text-[10px] font-black text-paper">{nature === "light" ? "Lightning" : meta.name} Jutsu</p>
                  <p className="text-[8px] font-bold text-paper/40">{nature === "fire" ? "DoT + AoE" : nature === "water" ? "Control + protection" : nature === "wind" ? "Speed + armour pierce" : nature === "earth" ? "Barriers + stuns" : "Burst + paralysis"}</p>
                </div>
              </div>
              <div className="space-y-1.5">
                {rows.map((j) => {
                  const has = known.has(j.id);
                  const eq = equipped.has(j.id);
                  const learnable = canLearnJutsu(n, j.id);
                  const locked = !has && !learnable;
                  return (
                    <div key={j.id} className={cn("rounded-lg p-2 ring-1 ring-inset", has ? "bg-jade/8 ring-jade/20" : "bg-black/20 ring-white/6", locked && "opacity-55") }>
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <p className="text-[10px] font-black text-paper">T{j.tier} · {j.name}</p>
                            <span className="rounded bg-black/35 px-1 py-[1px] text-[7.5px] font-bold text-paper/45">Lv {j.levelReq}</span>
                            <span className="rounded bg-black/35 px-1 py-[1px] text-[7.5px] font-bold text-[#75bfff]">{j.chakra} CP</span>
                            {eq && <span className="rounded bg-gold/15 px-1 py-[1px] text-[7.5px] font-black text-gold">EQUIPPED</span>}
                          </div>
                          <p className="mt-1 text-[9px] leading-relaxed text-paper/58">{j.desc}</p>
                          <p className="mt-0.5 text-[8px] font-bold text-paper/35">Power {j.power.toFixed(2)}× · {j.target.replaceAll("_", " ")} · effect: {j.effect}{j.effectValue ? ` ${j.effectValue}` : ""}</p>
                        </div>
                        <div className="flex shrink-0 flex-col gap-1">
                          {!has && j.tier > 0 && <button disabled={!learnable} onClick={() => learn(j.id)} className="rounded-lg bg-gold px-2 py-1.5 text-[8px] font-black text-[#2b2118] disabled:cursor-not-allowed disabled:bg-white/8 disabled:text-paper/25">LEARN</button>}
                          {has && <button onClick={() => equip(j.id)} className={cn("rounded-lg px-2 py-1.5 text-[8px] font-black ring-1", eq ? "bg-vermil/15 text-vermil ring-vermil/25" : "bg-black/30 text-paper/60 ring-white/10")}>{eq ? "REMOVE" : equipped.size >= 4 ? "4/4" : "EQUIP"}</button>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
'''
write("src/components/JutsuTree.tsx", jutsu_tree)


# Ninja detail: separate Skill/Technique and Jutsu submenus, plus stronger preview.
p = "src/components/NinjaDetail.tsx"
s = read(p)
if 'import JutsuTree from "./JutsuTree";' not in s:
    anchor = 'import NinjaEquipment from "./NinjaEquipment";'
    if anchor not in s:
        raise SystemExit("NinjaEquipment import not found")
    s = s.replace(anchor, anchor + '\nimport JutsuTree from "./JutsuTree";', 1)

if "potentialDevelopmentMultiplier" not in s:
    s = s.replace('skillPointGain, xpNext', 'skillPointGain, potentialDevelopmentMultiplier, xpNext', 1)

if 'const [progressionView, setProgressionView]' not in s:
    anchor = '  const [showEquipment, setShowEquipment] = useState(false);'
    if anchor not in s:
        raise SystemExit("NinjaDetail equipment state anchor not found")
    s = s.replace(anchor, anchor + '\n  const [progressionView, setProgressionView] = useState<"skills" | "jutsu">("skills");', 1)

old_tree = '<PerkTree n={n} techs={s.techs} onPick={(perkId, rect) => setConfirmSpend({ kind: "perk", perkId, rect })} />'
if old_tree in s:
    new_tree = '''<div className="mb-3 grid grid-cols-2 gap-2">\n              <button onClick={() => setProgressionView("skills")} className={cn("rounded-xl px-3 py-2 text-[9px] font-black tracking-wider ring-1", progressionView === "skills" ? "bg-gold text-[#2b2118] ring-gold" : "bg-black/25 text-paper/55 ring-white/8")}>SKILLS + TECHNIQUES</button>\n              <button onClick={() => setProgressionView("jutsu")} className={cn("rounded-xl px-3 py-2 text-[9px] font-black tracking-wider ring-1", progressionView === "jutsu" ? "bg-[#4f9ad9] text-white ring-[#4f9ad9]" : "bg-black/25 text-paper/55 ring-white/8")}>ELEMENTAL JUTSU</button>\n            </div>\n            {progressionView === "skills" ? (\n              <PerkTree n={n} techs={s.techs} onPick={(perkId, rect) => setConfirmSpend({ kind: "perk", perkId, rect })} />\n            ) : (\n              <JutsuTree n={n} onChanged={onEquipmentChanged} />\n            )}'''
    s = s.replace(old_tree, new_tree, 1)
elif "ELEMENTAL JUTSU" not in s:
    raise SystemExit("PerkTree render anchor not found")

# Add actual potential multiplier to the explanatory panel.
old_pot = 'Higher potential means more skill points each level.'
if old_pot in s:
    s = s.replace(old_pot, 'Potential now directly changes long-term growth and point value. Current development multiplier: ×{potentialDevelopmentMultiplier(n.pot).toFixed(2)}.', 1)

# Upgrade point confirmation from a single skill-number preview to derived combat stats.
old_calc = '          const mechanics = skill ? skillPointMechanics(skill) : perk ? perkMechanics(perk) : "";\n          return ('
if old_calc in s:
    new_calc = '''          const mechanics = skill ? skillPointMechanics(skill) : perk ? perkMechanics(perk) : "";\n          const beforeUnit = unitFromNinja(n);\n          const previewNinja = skill\n            ? { ...n, s: { ...n.s, [skill]: n.s[skill] + gain } }\n            : perk\n              ? { ...n, perks: [...n.perks, perk.id] }\n              : n;\n          const afterUnit = unitFromNinja(previewNinja);\n          const previewStats = [\n            ["HP", beforeUnit.maxHp, afterUnit.maxHp],\n            ["ATK", beforeUnit.atk, afterUnit.atk],\n            ["DEF", beforeUnit.def, afterUnit.def],\n            ["CHAKRA", beforeUnit.maxCp, afterUnit.maxCp],\n          ] as const;\n          return ('''
    s = s.replace(old_calc, new_calc, 1)
elif "previewStats" not in s:
    raise SystemExit("point confirmation calculation anchor not found")

old_mech_close = '                  {skill && <p className="mt-1.5 text-[9px] leading-relaxed text-paper/45">Also improves mission checks that require {meta?.name}. Values shown are the direct contribution before perk multipliers and caps.</p>}\n                </div>'
if old_mech_close in s:
    new_mech_close = '''                  {skill && <p className="mt-1.5 text-[9px] leading-relaxed text-paper/45">Also improves mission checks that require {meta?.name}. Values shown are the direct contribution before perk multipliers and caps.</p>}\n                  <div className="mt-2 grid grid-cols-4 gap-1.5">\n                    {previewStats.map(([label, before, after]) => (\n                      <div key={label} className="rounded-lg bg-black/25 p-1.5 text-center ring-1 ring-white/6">\n                        <p className="text-[7px] font-black tracking-wider text-paper/35">{label}</p>\n                        <p className="mt-0.5 text-[8.5px] font-black tabular-nums text-paper/70">{Math.round(before)} → <span className={after > before ? "text-jade" : after < before ? "text-vermil" : "text-paper/55"}>{Math.round(after)}</span></p>\n                      </div>\n                    ))}\n                  </div>\n                </div>'''
    s = s.replace(old_mech_close, new_mech_close, 1)
elif "previewStats.map" not in s:
    raise SystemExit("point confirmation mechanics anchor not found")
write(p, s)


# ---------------------------------------------------------------------------
# 4) Special mission definitions ready for the mission-board pass.
# ---------------------------------------------------------------------------
special_ts = r'''import type { Rank, Skill, TraitId } from "./types";

export type SpecialReward =
  | { kind: "potential"; amount: 1; maxPerNinja: 2 }
  | { kind: "trait"; trait: TraitId }
  | { kind: "unlock"; key: string }
  | { kind: "jutsu"; jutsuId: string };

export interface SpecialMissionDef {
  id: string;
  name: string;
  warning: string;
  minRank: Rank;
  focus: Skill[];
  slots: number;
  reward: SpecialReward;
}

export const SPECIAL_MISSIONS: SpecialMissionDef[] = [
  { id: "breakthrough_trial", name: "The Breakthrough Trial", warning: "EXTREME TRAINING: failure can cause a long injury. Success may permanently raise one ninja's natural Potential.", minRank: "B", focus: ["tai", "nin", "tac"], slots: 1, reward: { kind: "potential", amount: 1, maxPerNinja: 2 } },
  { id: "ancient_chakra_path", name: "Ancient Chakra Path", warning: "FORBIDDEN SITE: unstable chakra conditions may permanently alter participants.", minRank: "A", focus: ["nin", "med", "tac"], slots: 2, reward: { kind: "trait", trait: "chakraDense" } },
  { id: "night_hunter_oath", name: "Night Hunter's Oath", warning: "COVERT TRIAL: discovery will trigger an elite pursuit force.", minRank: "B", focus: ["ste", "spd", "tac"], slots: 1, reward: { kind: "trait", trait: "nightOperative" } },
  { id: "thunder_master", name: "Audience with the Thunder Master", warning: "MASTER'S TEST: only lightning-nature shinobi can claim the technique.", minRank: "A", focus: ["nin", "spd", "tac"], slots: 1, reward: { kind: "jutsu", jutsuId: "light_flash" } },
  { id: "village_barrier_secret", name: "The Buried Barrier Formula", warning: "ANCIENT RUINS: success permanently unlocks a new village defence project.", minRank: "A", focus: ["nin", "gen", "tac"], slots: 3, reward: { kind: "unlock", key: "barrier_research" } },
];
'''
write("src/game/specialMissions.ts", special_ts)

# Cache bump makes installed APK/PWA clients pick up the new UI immediately.
p = "public/sw.js"
s = read(p)
s, count = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-depth-v1-jutsu-potential";', s, count=1)
if count != 1:
    raise SystemExit("service worker CACHE constant not found")
write(p, s)

print("Village depth v1 implementation applied")
