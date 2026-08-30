from pathlib import Path

ROOT = Path('app')

def read(rel): return (ROOT / rel).read_text(encoding='utf-8')
def write(rel, s): (ROOT / rel).write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# 1) Rare/unique scout traits.
# ---------------------------------------------------------------------------
p = 'src/game/types.ts'; s = read(p)
old = '  | "ghostStep" | "mindGames" | "chakraAnchor" | "inspiringPresence" | "lastStand" | "executioner";'
new = '''  | "ghostStep" | "mindGames" | "chakraAnchor" | "inspiringPresence" | "lastStand" | "executioner"\n  | "sealingExpert" | "boneBloodline" | "shadowBinder" | "swarmHost" | "crystalRelease" | "mindLinkClan";'''
if '"boneBloodline"' not in s:
    if old not in s: raise SystemExit('TraitId v7 anchor missing')
    s = s.replace(old, new, 1)
write(p, s)

p = 'src/game/content.ts'; s = read(p)
s = s.replace('export type TraitRarity = "common" | "uncommon" | "rare";', 'export type TraitRarity = "common" | "uncommon" | "rare" | "unique";')
if 'boneBloodline:' not in s:
    block = '''\n  sealingExpert: { name: "Sealing Expert", desc: "+12% maximum chakra and +5 percentage points mission success. Unlocks the exclusive Sealing Formula Jutsu branch.", boost: "nin", icon: "封", rarity: "rare" },\n  boneBloodline: { name: "Bone Shaper Bloodline", desc: "+18% maximum HP, +12% battle DEF and +8 percentage points counter. Unlocks the exclusive Bone Arsenal Jutsu branch.", boost: "ken", icon: "骨", rarity: "unique" },\n  shadowBinder: { name: "Shadow Binder Clan", desc: "+6 percentage points mission success and +5 percentage points dodge. Unlocks the exclusive Shadow Binding Jutsu branch.", boost: "gen", icon: "影", rarity: "unique" },\n  swarmHost: { name: "Swarm Host Clan", desc: "+10% maximum chakra, +4 percentage points dodge and +4 percentage points mission success. Unlocks the exclusive Chakra-Insect Jutsu branch.", boost: "ste", icon: "蟲", rarity: "unique" },\n  crystalRelease: { name: "Crystal Release Bloodline", desc: "+15% battle DEF and +10% Jutsu damage. Unlocks the exclusive Crystal Release Jutsu branch.", boost: "nin", icon: "晶", rarity: "unique" },\n  mindLinkClan: { name: "Mind-Link Clan", desc: "+7 percentage points mission success and allies deal 4% more battle damage. Unlocks the exclusive Mind-Link Jutsu branch.", boost: "gen", icon: "心", rarity: "unique" },\n'''
    marker = '\n};\n\nexport const TRAIT_IDS'
    pos = s.find(marker)
    if pos < 0: raise SystemExit('TRAIT_META v7 closing marker missing')
    s = s[:pos] + block + s[pos:]
write(p, s)

p = 'src/game/perks.ts'; s = read(p)
if 'case "boneBloodline"' not in s:
    anchor = '      case "executioner": out.atk *= 1.05; out.critMult += 0.20; break;'
    cases = '''      case "executioner": out.atk *= 1.05; out.critMult += 0.20; break;\n      case "sealingExpert": out.cp *= 1.12; out.missionBonus += 0.05; break;\n      case "boneBloodline": out.hp *= 1.18; out.def *= 1.12; out.counter += 0.08; break;\n      case "shadowBinder": out.missionBonus += 0.06; out.dodge += 0.05; break;\n      case "swarmHost": out.cp *= 1.10; out.dodge += 0.04; out.missionBonus += 0.04; break;\n      case "crystalRelease": out.def *= 1.15; out.jutsu *= 1.10; break;\n      case "mindLinkClan": out.missionBonus += 0.07; out.allyAtk *= 1.04; break;'''
    if anchor not in s: raise SystemExit('perkFx v7 trait anchor missing')
    s = s.replace(anchor, cases, 1)
write(p, s)

p = 'src/game/engine.ts'; s = read(p)
old = '''function rollTraits(s: GameState, pot: number, legendId?: string): import("./types").TraitId[] {\n  const common = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "common");\n  const uncommon = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "uncommon");\n  const rare = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "rare" && (id !== "kekkeiTalent" || pot >= 4));\n  const count = pot >= 5 ? 3 : pot >= 3 ? 2 : 1;\n  const out: import("./types").TraitId[] = [];'''
new = '''function rollTraits(s: GameState, pot: number, legendId?: string): import("./types").TraitId[] {\n  const common = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "common");\n  const uncommon = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "uncommon");\n  const rare = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "rare" && (id !== "kekkeiTalent" || pot >= 4));\n  const unique = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "unique");\n  const count = pot >= 5 ? 3 : pot >= 3 ? 2 : 1;\n  const out: import("./types").TraitId[] = [];'''
if 'const unique = TRAIT_IDS.filter' not in s:
    if old not in s: raise SystemExit('rollTraits v7 pool anchor missing')
    s = s.replace(old, new, 1)
anchor = '  if (legendId === "seal_bearer") add("chakraAnchor");\n  while (out.length < count) {'
replacement = '''  if (legendId === "seal_bearer") add("chakraAnchor");\n  // Clan/bloodline uniques are genuine scouting jackpots. Only ordinary recruits roll them,\n  // and no normal recruit can receive more than one UNIQUE trait.\n  if (!legendId && unique.length) {\n    const uniqueChance = (pot >= 5 ? 0.025 : pot >= 4 ? 0.012 : pot >= 3 ? 0.004 : pot >= 2 ? 0.001 : 0)\n      + (hasTech(s, "hall_elite_recruitment") ? 0.005 : 0);\n    if (Math.random() < uniqueChance) add(pick(unique));\n  }\n  while (out.length < count) {'''
if 'const uniqueChance = (pot >= 5 ? 0.025' not in s:
    if anchor not in s: raise SystemExit('rollTraits v7 unique anchor missing')
    s = s.replace(anchor, replacement, 1)
write(p, s)

# ---------------------------------------------------------------------------
# 2) Trait-exclusive Jutsu branches.
# ---------------------------------------------------------------------------
p = 'src/game/jutsu.ts'; s = read(p)
s = s.replace('import type { Nature, Ninja } from "./types";', 'import type { Nature, Ninja, Skill, TraitId } from "./types";')
old = '''export interface JutsuDef {\n  id: string;\n  name: string;\n  nature: Nature;\n  tier: number;'''
new = '''export interface JutsuDef {\n  id: string;\n  name: string;\n  /** Elemental Jutsu use nature; rare-style Jutsu instead use requiresTrait. */\n  nature?: Nature;\n  requiresTrait?: TraitId;\n  style?: string;\n  stat?: Extract<Skill, "nin" | "gen" | "ken" | "tac">;\n  tier: number;'''
if 'requiresTrait?: TraitId;' not in s:
    if old not in s: raise SystemExit('JutsuDef v7 anchor missing')
    s = s.replace(old, new, 1)
if 'id: "seal_binding_tag"' not in s:
    marker = '\n];\n\nexport const JUTSU_BY_ID'
    pos = s.find(marker)
    if pos < 0: raise SystemExit('JUTSU v7 list closing marker missing')
    extra = '''\n\n  // SEALING EXPERT — binding, barriers and shutdown.\n  J({ id: "seal_binding_tag", name: "Binding Formula Tag", requiresTrait: "sealingExpert", style: "Sealing Formula", stat: "nin", tier: 0, levelReq: 1, chakra: 6, power: 0.42, target: "foe", effect: "slow", effectValue: 2, desc: "Trait-exclusive. A chakra formula clings to the target, dealing light damage and heavily slowing them." }),\n  J({ id: "seal_barrier_array", name: "Four-Corner Barrier", requiresTrait: "sealingExpert", style: "Sealing Formula", stat: "nin", tier: 1, levelReq: 8, chakra: 12, power: 0, target: "all_allies", effect: "guard", effectValue: 2, desc: "Trait-exclusive. Deploys linked tags that protect the whole squad for 2 rounds." }),\n  J({ id: "seal_fivefold_lock", name: "Fivefold Chakra Lock", requiresTrait: "sealingExpert", style: "Sealing Formula", stat: "nin", tier: 2, levelReq: 16, chakra: 18, power: 0.96, target: "foe", effect: "stun", effectValue: 1, desc: "Trait-exclusive. A high-grade seal crushes chakra flow and can stun the target." }),\n\n  // BONE SHAPER — weaponised skeleton, armour and battlefield spikes.\n  J({ id: "bone_lance", name: "Bone Lance", requiresTrait: "boneBloodline", style: "Bone Arsenal", stat: "ken", tier: 0, levelReq: 1, chakra: 6, power: 0.98, target: "foe", effect: "pierce", effectValue: 20, desc: "UNIQUE bloodline Jutsu. Forms a hardened bone spear that ignores 20% of defence." }),\n  J({ id: "bone_armour", name: "Skeletal Armour", requiresTrait: "boneBloodline", style: "Bone Arsenal", stat: "ken", tier: 1, levelReq: 8, chakra: 10, power: 0, target: "self", effect: "guard", effectValue: 3, desc: "UNIQUE bloodline Jutsu. Grows a defensive bone lattice around the user for 3 rounds." }),\n  J({ id: "bone_forest", name: "White Bone Forest", requiresTrait: "boneBloodline", style: "Bone Arsenal", stat: "ken", tier: 2, levelReq: 16, chakra: 20, power: 0.88, target: "all_foes", effect: "pierce", effectValue: 25, desc: "UNIQUE bloodline Jutsu. Bone pillars erupt beneath every enemy and ignore 25% of defence." }),\n\n  // SHADOW BINDER — immobilisation and control.\n  J({ id: "shadow_snare", name: "Shadow Snare", requiresTrait: "shadowBinder", style: "Shadow Binding", stat: "gen", tier: 0, levelReq: 1, chakra: 7, power: 0.42, target: "foe", effect: "stun", effectValue: 1, desc: "UNIQUE clan Jutsu. Pins one enemy's shadow and can cost them their next action." }),\n  J({ id: "shadow_stitch", name: "Shadow Stitching", requiresTrait: "shadowBinder", style: "Shadow Binding", stat: "gen", tier: 1, levelReq: 8, chakra: 12, power: 0.60, target: "all_foes", effect: "slow", effectValue: 2, desc: "UNIQUE clan Jutsu. Splits the user's shadow across the enemy line, damaging and slowing every target." }),\n  J({ id: "shadow_crush", name: "Shadow Strangle", requiresTrait: "shadowBinder", style: "Shadow Binding", stat: "gen", tier: 2, levelReq: 16, chakra: 19, power: 1.25, target: "foe", effect: "stun", effectValue: 1, desc: "UNIQUE clan Jutsu. Converts a successful bind into a crushing finishing technique with another stun chance." }),\n\n  // SWARM HOST — chakra insects, attrition and protection.\n  J({ id: "swarm_bite", name: "Chakra Beetle Cloud", requiresTrait: "swarmHost", style: "Chakra-Insect Arts", stat: "tac", tier: 0, levelReq: 1, chakra: 5, power: 0.70, target: "foe", effect: "burn", effectValue: 2, desc: "UNIQUE clan Jutsu. A chakra-fed swarm clings to one enemy and deals persistent damage for 2 rounds." }),\n  J({ id: "swarm_screen", name: "Living Insect Screen", requiresTrait: "swarmHost", style: "Chakra-Insect Arts", stat: "tac", tier: 1, levelReq: 8, chakra: 10, power: 0, target: "all_allies", effect: "guard", effectValue: 2, desc: "UNIQUE clan Jutsu. A moving insect veil disrupts incoming attacks against the whole squad." }),\n  J({ id: "swarm_feast", name: "Devouring Swarm", requiresTrait: "swarmHost", style: "Chakra-Insect Arts", stat: "tac", tier: 2, levelReq: 16, chakra: 18, power: 0.72, target: "all_foes", effect: "burn", effectValue: 3, desc: "UNIQUE clan Jutsu. Floods the battlefield with chakra insects, damaging every enemy and leaving a 3-round swarm." }),\n\n  // CRYSTAL RELEASE — piercing constructs and prisons.\n  J({ id: "crystal_shard", name: "Crystal Shard Spear", requiresTrait: "crystalRelease", style: "Crystal Release", stat: "nin", tier: 0, levelReq: 1, chakra: 6, power: 0.95, target: "foe", effect: "pierce", effectValue: 15, desc: "UNIQUE bloodline Jutsu. Fires a dense crystal spear that ignores 15% of defence." }),\n  J({ id: "crystal_prison", name: "Crystal Prison", requiresTrait: "crystalRelease", style: "Crystal Release", stat: "nin", tier: 1, levelReq: 8, chakra: 12, power: 0.72, target: "foe", effect: "stun", effectValue: 1, desc: "UNIQUE bloodline Jutsu. Crystal grows around the target, damaging them with a strong stun chance." }),\n  J({ id: "crystal_dome", name: "Crystal Fortress Dome", requiresTrait: "crystalRelease", style: "Crystal Release", stat: "nin", tier: 2, levelReq: 16, chakra: 18, power: 0, target: "all_allies", effect: "guard", effectValue: 4, desc: "UNIQUE bloodline Jutsu. Raises a fortified crystal dome around the squad for 4 rounds." }),\n\n  // MIND-LINK CLAN — mental suppression and squad coordination.\n  J({ id: "mind_probe", name: "Mind Probe", requiresTrait: "mindLinkClan", style: "Mind-Link Arts", stat: "gen", tier: 0, levelReq: 1, chakra: 6, power: 0.35, target: "foe", effect: "slow", effectValue: 2, desc: "UNIQUE clan Jutsu. Disrupts the target's thought process and sharply slows their initiative." }),\n  J({ id: "mind_lock", name: "Mind Lock", requiresTrait: "mindLinkClan", style: "Mind-Link Arts", stat: "gen", tier: 1, levelReq: 8, chakra: 12, power: 0.50, target: "foe", effect: "stun", effectValue: 1, desc: "UNIQUE clan Jutsu. Forces a brief mental seizure that can remove the target's next action." }),\n  J({ id: "mind_network", name: "Shared Intent Network", requiresTrait: "mindLinkClan", style: "Mind-Link Arts", stat: "gen", tier: 2, levelReq: 16, chakra: 16, power: 0, target: "all_allies", effect: "crit", effectValue: 15, desc: "UNIQUE clan Jutsu. Links the squad's intent for 2 rounds, improving initiative and crit chance by 15 percentage points." }),'''
    s = s[:pos] + extra + s[pos:]
old = '''export function jutsuForNinja(n: Ninja): JutsuDef[] {\n  const have = new Set(ninjaNatures(n));\n  return JUTSU.filter((j) => have.has(j.nature));\n}'''
new = '''export function jutsuForNinja(n: Ninja): JutsuDef[] {\n  const have = new Set(ninjaNatures(n));\n  return JUTSU.filter((j) => (j.nature != null && have.has(j.nature)) || (j.requiresTrait != null && n.traits.includes(j.requiresTrait)));\n}'''
if old in s: s = s.replace(old, new, 1)
old = '''export function canLearnJutsu(n: Ninja, id: string): boolean {\n  const j = JUTSU_BY_ID[id];\n  if (!j || j.tier === 0 || !ninjaNatures(n).includes(j.nature)) return false;\n  if (knownJutsuIds(n).includes(id) || n.level < j.levelReq || jutsuPointsAvailable(n) <= 0) return false;\n  if (j.tier <= 1) return true;\n  return knownJutsuIds(n).some((known) => JUTSU_BY_ID[known]?.nature === j.nature && JUTSU_BY_ID[known]?.tier === j.tier - 1);\n}'''
new = '''export function canLearnJutsu(n: Ninja, id: string): boolean {\n  const j = JUTSU_BY_ID[id];\n  if (!j || j.tier === 0) return false;\n  const eligible = (j.nature != null && ninjaNatures(n).includes(j.nature)) || (j.requiresTrait != null && n.traits.includes(j.requiresTrait));\n  if (!eligible || knownJutsuIds(n).includes(id) || n.level < j.levelReq || jutsuPointsAvailable(n) <= 0) return false;\n  if (j.tier <= 1) return true;\n  return knownJutsuIds(n).some((known) => {\n    const prev = JUTSU_BY_ID[known];\n    if (!prev || prev.tier !== j.tier - 1) return false;\n    return j.requiresTrait ? prev.requiresTrait === j.requiresTrait : prev.nature === j.nature;\n  });\n}'''
if old in s: s = s.replace(old, new, 1)
write(p, s)

p = 'src/game/battle.ts'; s = read(p)
old = '      const raw = (u.nin * 1.65 * u.jutsuPower * j.power) * rnd(0.9, 1.16) - t.def * 0.18 * (1 - piercePct);'
new = '''      const jutsuStat = j.stat === "gen" ? u.gen : j.stat === "ken" ? u.ken : j.stat === "tac" ? u.tac : u.nin;\n      const raw = (jutsuStat * 1.65 * u.jutsuPower * j.power) * rnd(0.9, 1.16) - t.def * 0.18 * (1 - piercePct);'''
if 'const jutsuStat = j.stat === "gen"' not in s:
    if old not in s: raise SystemExit('battle rare-jutsu scaling anchor missing')
    s = s.replace(old, new, 1)
write(p, s)

p = 'src/components/JutsuTree.tsx'; s = read(p)
s = s.replace('import { NATURE_META } from "../game/content";', 'import { NATURE_META, TRAIT_META } from "../game/content";')
old = '''  const natures = ninjaNatures(n);\n  const points = jutsuPointsAvailable(n);'''
new = '''  const natures = ninjaNatures(n);\n  const exclusiveTraits = Array.from(new Set(JUTSU.filter((j) => j.requiresTrait ? n.traits.includes(j.requiresTrait) : false).map((j) => j.requiresTrait!)));\n  const points = jutsuPointsAvailable(n);'''
if 'const exclusiveTraits = Array.from' not in s:
    if old not in s: raise SystemExit('JutsuTree v7 state anchor missing')
    s = s.replace(old, new, 1)
s = s.replace('One Jutsu Point every 3 levels. Learn only your natural element(s); equip up to 4 for battle.', 'One Jutsu Point every 3 levels. Learn your natural element(s) plus any rare trait-exclusive styles; equip up to 4 for battle.')
needle = '''        })}\n      </div>\n    </div>\n  );'''
if 'RARE / UNIQUE STYLE JUTSU' not in s:
    extra = '''        })}\n\n        {exclusiveTraits.length > 0 && <div className="pt-1">\n          <p className="mb-1 text-[8px] font-black tracking-[0.16em] text-gold/65">RARE / UNIQUE STYLE JUTSU</p>\n        </div>}\n        {exclusiveTraits.map((traitId) => {\n          const meta = TRAIT_META[traitId];\n          const rows = JUTSU.filter((j) => j.requiresTrait === traitId).sort((a, b) => a.tier - b.tier);\n          const style = rows[0]?.style ?? meta.name;\n          return (\n            <div key={traitId} className="rounded-xl bg-gold/[0.04] p-2 ring-1 ring-gold/15">\n              <div className="mb-2 flex items-center gap-2">\n                <span className="grid h-7 w-7 place-items-center rounded-lg bg-gold/10 text-sm font-black text-gold">{meta.icon}</span>\n                <div>\n                  <p className="text-[10px] font-black text-gold">{style}</p>\n                  <p className="text-[8px] font-bold text-paper/40">{meta.rarity.toUpperCase()} trait-exclusive techniques · cannot be learned without {meta.name}</p>\n                </div>\n              </div>\n              <div className="space-y-1.5">\n                {rows.map((j) => {\n                  const has = known.has(j.id);\n                  const eq = equipped.has(j.id);\n                  const learnable = canLearnJutsu(n, j.id);\n                  const locked = !has && !learnable;\n                  return (\n                    <div key={j.id} className={cn("rounded-lg p-2 ring-1 ring-inset", has ? "bg-jade/8 ring-jade/20" : "bg-black/20 ring-white/6", locked && "opacity-55")}>\n                      <div className="flex items-start justify-between gap-2">\n                        <div className="min-w-0">\n                          <div className="flex flex-wrap items-center gap-1.5">\n                            <p className="text-[10px] font-black text-paper">T{j.tier} · {j.name}</p>\n                            <span className="rounded bg-black/35 px-1 py-[1px] text-[7.5px] font-bold text-paper/45">Lv {j.levelReq}</span>\n                            <span className="rounded bg-black/35 px-1 py-[1px] text-[7.5px] font-bold text-[#75bfff]">{j.chakra} CP</span>\n                            {eq && <span className="rounded bg-gold/15 px-1 py-[1px] text-[7.5px] font-black text-gold">EQUIPPED</span>}\n                          </div>\n                          <p className="mt-1 text-[9px] leading-relaxed text-paper/58">{j.desc}</p>\n                          <p className="mt-0.5 text-[8px] font-bold text-paper/35">Power {j.power.toFixed(2)}× · {j.target.replaceAll("_", " ")} · effect: {j.effect}{j.effectValue ? ` ${j.effectValue}` : ""}</p>\n                        </div>\n                        <div className="flex shrink-0 flex-col gap-1">\n                          {!has && j.tier > 0 && <button disabled={!learnable} onClick={() => learn(j.id)} className="rounded-lg bg-gold px-2 py-1.5 text-[8px] font-black text-[#2b2118] disabled:cursor-not-allowed disabled:bg-white/8 disabled:text-paper/25">LEARN</button>}\n                          {has && <button onClick={() => equip(j.id)} className={cn("rounded-lg px-2 py-1.5 text-[8px] font-black ring-1", eq ? "bg-vermil/15 text-vermil ring-vermil/25" : "bg-black/30 text-paper/60 ring-white/10")}>{eq ? "REMOVE" : equipped.size >= 4 ? "4/4" : "EQUIP"}</button>}\n                        </div>\n                      </div>\n                    </div>\n                  );\n                })}\n              </div>\n            </div>\n          );\n        })}\n      </div>\n    </div>\n  );'''
    if needle not in s: raise SystemExit('JutsuTree v7 render anchor missing')
    s = s.replace(needle, extra, 1)
write(p, s)

# ---------------------------------------------------------------------------
# 3) A few order members can appear through scouting, but at tiny weights.
# ---------------------------------------------------------------------------
p = 'src/game/perks.ts'; s = read(p)
s = s.replace('  scoutable?: boolean;\n}', '  scoutable?: boolean;\n  /** Relative weight inside the already-rare legendary scout roll. */\n  scoutWeight?: number;\n}')
s = s.replace('id: "beast_sage", title: "Beast Sage", epithet: "of the Five Paths", color: "#79cf69", scoutable: false,', 'id: "beast_sage", title: "Beast Sage", epithet: "of the Five Paths", color: "#79cf69", scoutable: true, scoutWeight: 0.07,')
s = s.replace('id: "storm_caller", title: "Storm Caller", epithet: "of the Four Tempests", color: "#8bc8ff", scoutable: false,', 'id: "storm_caller", title: "Storm Caller", epithet: "of the Four Tempests", color: "#8bc8ff", scoutable: true, scoutWeight: 0.12,')
s = s.replace('id: "masked_assassin", title: "Masked Assassin", epithet: "of the Nine Faces", color: "#c9b2ff", scoutable: false,', 'id: "masked_assassin", title: "Masked Assassin", epithet: "of the Nine Faces", color: "#c9b2ff", scoutable: true, scoutWeight: 0.18,')
write(p, s)

p = 'src/game/engine.ts'; s = read(p)
if 'function pickScoutLegend' not in s:
    anchor = 'export function scout(s: GameState, ev: Ev[]): boolean {'
    helper = '''function pickScoutLegend(ids: string[]): string | null {\n  if (!ids.length) return null;\n  const weighted = ids.map((id) => ({ id, w: Math.max(0.01, LEGENDS[id]?.scoutWeight ?? 1) }));\n  const total = weighted.reduce((sum, x) => sum + x.w, 0);\n  let roll = Math.random() * total;\n  for (const x of weighted) { roll -= x.w; if (roll <= 0) return x.id; }\n  return weighted[weighted.length - 1]?.id ?? null;\n}\n\n'''
    if anchor not in s: raise SystemExit('scout v7 helper anchor missing')
    s = s.replace(anchor, helper + anchor, 1)
s = s.replace('const legendId = available.length && Math.random() < chance ? pick(available) : null;', 'const legendId = available.length && Math.random() < chance ? pickScoutLegend(available) : null;')
write(p, s)

p = 'src/game/specialMissionsV2.ts'; s = read(p)
s = s.replace('The order will never exceed nine members and cannot appear in normal scouting.', 'The order will never exceed nine members; a lone member can also appear exceptionally rarely through scouting.')
s = s.replace('They cannot be scouted normally and arrive with Storm Crown mastered. Maximum four.', 'A lone member can also appear exceptionally rarely through scouting. Mission recruits arrive with Storm Crown mastered. Maximum four.')
s = s.replace('They arrive with Primal Covenant already mastered. Maximum five in the village.', 'A lone Beast Sage can also appear exceptionally rarely through scouting; mission recruits arrive with Primal Covenant already mastered. Maximum five in the village.')
write(p, s)

p = 'public/sw.js'; s = read(p)
s = s.replace('shadow-village-depth-v1-jutsu-potential-v5-infrastructure-threat', 'shadow-village-depth-v1-jutsu-potential-v7-scout-uniques')
write(p, s)

print('Applied village depth v7: scoutable order outliers, UNIQUE clan/bloodline traits, and trait-exclusive Jutsu branches.')
