from pathlib import Path
import re

ROOT = Path('app')

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')

def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

def replace_once(rel: str, old: str, new: str, label: str) -> None:
    s = read(rel)
    if new in s:
        print(f'{label}: already applied')
        return
    if old not in s:
        raise SystemExit(f'{label}: anchor missing in {rel}')
    write(rel, s.replace(old, new, 1))
    print(f'{label}: applied')

# ---------------------------------------------------------------------------
# 1) Twelve more mechanically distinct traits.
# ---------------------------------------------------------------------------
p = 'src/game/types.ts'
s = read(p)
if '"ironGuardian"' not in s:
    anchor = '  | "duelist" | "nightOperative" | "calmUnderFire" | "fieldSurvivor" | "missionVeteran";'
    repl = '''  | "duelist" | "nightOperative" | "calmUnderFire" | "fieldSurvivor" | "missionVeteran"\n  | "ironGuardian" | "chakraConductor" | "hunterInstinct" | "sensorNin" | "battlefieldHealer" | "relentless"\n  | "ghostStep" | "mindGames" | "chakraAnchor" | "inspiringPresence" | "lastStand" | "executioner";'''
    if anchor not in s:
        raise SystemExit('TraitId v3 anchor missing')
    s = s.replace(anchor, repl, 1)
s = s.replace('specialRewardKind?: "potential" | "trait" | "unlock" | "jutsu";', 'specialRewardKind?: "potential" | "trait" | "unlock" | "jutsu" | "gear";')
write(p, s)

p = 'src/game/content.ts'
s = read(p)
if 'ironGuardian:' not in s:
    trait_block = '''  ironGuardian: { name: "Iron Guardian", desc: "+12% maximum HP and +10% battle DEF.", icon: "盾", rarity: "uncommon" },\n  chakraConductor: { name: "Chakra Conductor", desc: "+18% maximum chakra and +8% elemental jutsu damage.", boost: "nin", icon: "導", rarity: "rare" },\n  hunterInstinct: { name: "Hunter Instinct", desc: "+6% battle ATK, +5 percentage points crit chance and +2 percentage points mission success.", icon: "狩", rarity: "uncommon" },\n  sensorNin: { name: "Sensor Ninja", desc: "+6 percentage points mission success and +3 percentage points dodge; Battlefield Tactics becomes a specialist skill.", boost: "tac", icon: "感", rarity: "rare" },\n  battlefieldHealer: { name: "Battlefield Healer", desc: "Regenerates 4 HP each battle round, heals for 4% of damage dealt, and Medical becomes a specialist skill.", boost: "med", icon: "癒", rarity: "rare" },\n  relentless: { name: "Relentless", desc: "+7% battle ATK and regenerates 2 HP each battle round.", icon: "進", rarity: "uncommon" },\n  ghostStep: { name: "Ghost Step", desc: "+8 percentage points dodge and +3 percentage points mission success; Speed becomes a specialist skill.", boost: "spd", icon: "幽", rarity: "rare" },\n  mindGames: { name: "Mind Games", desc: "+6 percentage points dodge and +4 percentage points mission success; Genjutsu becomes a specialist skill.", boost: "gen", icon: "幻", rarity: "uncommon" },\n  chakraAnchor: { name: "Chakra Anchor", desc: "+15% maximum chakra and +7% battle DEF.", boost: "nin", icon: "錨", rarity: "uncommon" },\n  inspiringPresence: { name: "Inspiring Presence", desc: "+4 percentage points mission success and allies deal 6% more battle damage; Battlefield Tactics becomes a specialist skill.", boost: "tac", icon: "鼓", rarity: "rare" },\n  lastStand: { name: "Last Stand", desc: "+15% maximum HP and returns 10% of melee damage taken to the attacker.", icon: "耐", rarity: "rare" },\n  executioner: { name: "Executioner", desc: "+5% battle ATK and +20 percentage points critical damage.", boost: "ken", icon: "断", rarity: "rare" },\n'''
    marker = '\n};\n\nexport const TRAIT_IDS'
    pos = s.find(marker)
    if pos < 0:
        raise SystemExit('TRAIT_META closing marker missing')
    s = s[:pos] + '\n' + trait_block + s[pos:]

mission_additions = {
    'D': ('    { name: "Clear the Training Grounds", desc: "Remove traps and damaged targets before tomorrow\'s classes.", focus: ["nin", "tai"], slots: 2 },', '''\n    { name: "Deliver Fresh Medicine", desc: "Rush a temperature-sensitive medicine pack to the outer farms.", focus: ["spd", "med"], slots: 1 },\n    { name: "Patrol the East Wall", desc: "Walk the village perimeter and investigate any broken warning seals.", focus: ["ste", "tac"], slots: 2 },\n    { name: "Recover the Academy Kunai", desc: "Training weapons have gone missing around the academy grounds.", focus: ["ste", "spd"], slots: 1 },\n    { name: "Rebuild the Market Stall", desc: "Protect and assist workers rebuilding a storm-damaged merchant stall.", focus: ["tai", "tac"], slots: 2 },\n    { name: "Track the Missing Goat", desc: "A prize goat escaped into the terraced woodland above the village.", focus: ["ste", "spd"], slots: 1 },'''),
    'C': ('    { name: "Recover the Stolen Medicine", desc: "A medical shipment disappeared before reaching the clinic.", focus: ["med", "ste", "spd"], slots: 2 },', '''\n    { name: "Escort the Bridge Surveyor", desc: "Protect an engineer measuring a disputed river crossing.", focus: ["tac", "ste", "spd"], slots: 2 },\n    { name: "Stop the Toll-Road Extortion", desc: "Armed thugs are demanding illegal tolls from village merchants.", focus: ["tai", "tac", "ken"], slots: 2 },\n    { name: "Investigate the Smuggler's Tunnel", desc: "A hidden tunnel may be moving contraband beneath the border road.", focus: ["ste", "gen", "tac"], slots: 2 },\n    { name: "Protect the Herbalist Expedition", desc: "Escort medics gathering rare plants in predator territory.", focus: ["med", "ste", "tai"], slots: 3 },\n    { name: "Capture the Masked Burglar", desc: "A rooftop thief has robbed four wealthy compounds without leaving a face behind.", focus: ["spd", "ste", "gen"], slots: 2 },'''),
    'B': ('    { name: "Protect the Defecting Informant", desc: "Keep a valuable source alive until extraction.", focus: ["tac", "med", "ken"], slots: 4 },', '''\n    { name: "Raid the Counterfeit Seal Workshop", desc: "Destroy a workshop producing forged village travel papers.", focus: ["ste", "tac", "nin"], slots: 3 },\n    { name: "Rescue the Border Watch", desc: "A watch post is surrounded and cannot hold until morning.", focus: ["tai", "med", "tac"], slots: 4 },\n    { name: "Shadow the Enemy Diplomat", desc: "Follow a hostile envoy and identify every covert contact they meet.", focus: ["ste", "gen", "tac"], slots: 3 },\n    { name: "Clear the Spider Caverns", desc: "Giant venomous spiders have made a trade tunnel impassable.", focus: ["nin", "med", "tai"], slots: 4 },\n    { name: "Seize the River Fortress", desc: "Take a fortified customs post before reinforcements arrive by boat.", focus: ["tac", "ken", "nin"], slots: 4 },'''),
    'A': ('    { name: "Hold the Mountain Gate", desc: "Delay a superior enemy force long enough for civilians to escape.", focus: ["tai", "ken", "med", "tac"], slots: 4 },', '''\n    { name: "Extract the Double Agent", desc: "Pull a compromised intelligence asset out of an enemy capital before dawn.", focus: ["ste", "gen", "tac", "spd"], slots: 4 },\n    { name: "Break the Blood-Mist Cell", desc: "Dismantle a notorious assassination team operating inside allied territory.", focus: ["ken", "med", "ste", "tac"], slots: 4 },\n    { name: "Defend the Hidden Hospital", desc: "An enemy strike force has discovered a covert field hospital.", focus: ["med", "nin", "tai", "tac"], slots: 4 },\n    { name: "Steal the Siege Plans", desc: "Enter a command pavilion and copy the assault plan before the army moves.", focus: ["ste", "gen", "tac", "spd"], slots: 3 },\n    { name: "Capture the Storm Caller", desc: "Bring back alive a rogue shinobi whose lightning techniques are destroying patrols.", focus: ["nin", "spd", "med", "tac"], slots: 4 },'''),
    'S': ('    { name: "End the Silent War", desc: "Expose and dismantle a covert network operating inside allied territory.", focus: ["ste", "gen", "tac", "doj"], slots: 4 },', '''\n    { name: "The Black Sun Assassination", desc: "Eliminate a warlord during the only six-minute gap in their impossible security screen.", focus: ["ste", "ken", "gen", "tac"], slots: 4 },\n    { name: "Seal the Walking Calamity", desc: "Contain a transformed shinobi whose chakra is devastating everything around them.", focus: ["nin", "med", "doj", "tac"], slots: 4 },\n    { name: "Infiltrate the Kage's Inner Court", desc: "Enter a hostile Kage residence and recover proof of a planned invasion.", focus: ["ste", "gen", "doj", "tac"], slots: 4 },\n    { name: "Shatter the Moonless Fortress", desc: "Destroy a mountain fortress before its hidden army can deploy.", focus: ["nin", "ken", "tai", "tac"], slots: 4 },\n    { name: "Stop the Forbidden Resurrection", desc: "Interrupt a ritual intended to restore a legendary enemy commander to life.", focus: ["nin", "gen", "med", "doj"], slots: 4 },'''),
}
for _, (anchor, addition) in mission_additions.items():
    if addition.strip().splitlines()[0].strip() not in s:
        if anchor not in s:
            raise SystemExit(f'Mission expansion anchor missing: {anchor[:45]}')
        s = s.replace(anchor, anchor + addition, 1)
write(p, s)

p = 'src/game/perks.ts'
s = read(p)
if 'case "ironGuardian"' not in s:
    anchor = '      case "missionVeteran": out.missionBonus += 0.07; out.fatigue *= 0.90; break;'
    cases = '''      case "missionVeteran": out.missionBonus += 0.07; out.fatigue *= 0.90; break;\n      case "ironGuardian": out.hp *= 1.12; out.def *= 1.10; break;\n      case "chakraConductor": out.cp *= 1.18; out.jutsu *= 1.08; break;\n      case "hunterInstinct": out.atk *= 1.06; out.crit += 0.05; out.missionBonus += 0.02; break;\n      case "sensorNin": out.missionBonus += 0.06; out.dodge += 0.03; break;\n      case "battlefieldHealer": out.regen += 4; out.lifesteal += 0.04; break;\n      case "relentless": out.atk *= 1.07; out.regen += 2; break;\n      case "ghostStep": out.dodge += 0.08; out.missionBonus += 0.03; break;\n      case "mindGames": out.dodge += 0.06; out.missionBonus += 0.04; break;\n      case "chakraAnchor": out.cp *= 1.15; out.def *= 1.07; break;\n      case "inspiringPresence": out.missionBonus += 0.04; out.allyAtk *= 1.06; break;\n      case "lastStand": out.hp *= 1.15; out.counter += 0.10; break;\n      case "executioner": out.atk *= 1.05; out.critMult += 0.20; break;'''
    if anchor not in s:
        raise SystemExit('perkFx trait anchor missing')
    s = s.replace(anchor, cases, 1)
write(p, s)

p = 'src/game/equipment.ts'
s = read(p)
if 'missionOnly?: boolean;' not in s:
    s = s.replace('  ability?: EquipmentAbility;\n}', '  ability?: EquipmentAbility;\n  /** Mission-exclusive gear can be owned/equipped normally but never appears in gacha pulls. */\n  missionOnly?: boolean;\n}', 1)
if 'MISSION_UNIQUE_GEAR' not in s:
    unique = r'''
export const MISSION_UNIQUE_GEAR: EquipmentItem[] = [
  { id: "uniq_smokeveil_mask", name: "Smokeveil Mask", rarity: "rare", kind: "passive", icon: "煙", missionOnly: true, appearance: "A charcoal half-mask woven with silver-grey chakra thread; its edges seem to blur whenever the wearer moves.", desc: "Mission exclusive. +4 STE, +2 SPD and +5 percentage points dodge.", skill: { ste: 4, spd: 2 }, battle: { dodge: 0.05 } },
  { id: "uniq_iron_leaf_bracers", name: "Iron Leaf Bracers", rarity: "rare", kind: "stat", icon: "鉄", missionOnly: true, appearance: "Heavy forearm guards of layered dark steel, each plate stamped with an old leaf-shaped maker's seal.", desc: "Mission exclusive. +4 TAI, +2 KEN and +8% battle ATK.", skill: { tai: 4, ken: 2 }, battle: { atk: 1.08 } },
  { id: "uniq_stormglass_ring", name: "Stormglass Ring", rarity: "epic", kind: "technique", icon: "雷", missionOnly: true, appearance: "A translucent blue-black ring with a lightning-shaped flaw trapped inside the stone; static crawls across it when chakra is fed through the band.", desc: "Mission exclusive. +5 NIN, +3 SPD, +15% chakra, +4pp crit and grants Thunderclap Seal.", skill: { nin: 5, spd: 3 }, battle: { cp: 1.15, crit: 0.04 }, ability: { id: "geartech_stormglass", name: "Thunderclap Seal", kanji: "雷", power: 0.82, stat: "nin", hits: 2, note: "The Stormglass Ring discharges a stored two-hit lightning seal" } },
  { id: "uniq_white_heron_cloak", name: "White Heron Cloak", rarity: "epic", kind: "passive", icon: "鷺", missionOnly: true, appearance: "A pale travel cloak with feather-like layered panels, dark inner lining and tiny weighted hems that never seem to catch the wind.", desc: "Mission exclusive. +5 STE, +3 TAC and +7 percentage points dodge.", skill: { ste: 5, tac: 3 }, battle: { dodge: 0.07 } },
  { id: "uniq_kagebreaker_blade", name: "Kagebreaker Blade", rarity: "legendary", kind: "technique", icon: "影", missionOnly: true, appearance: "A short blackened blade with a broken gold line running through the steel and a guard made from two opposing crescent shapes.", desc: "Mission exclusive. +7 KEN, +3 TAC, +12% ATK, +6pp crit and grants Kagebreaker Draw.", skill: { ken: 7, tac: 3 }, battle: { atk: 1.12, crit: 0.06 }, ability: { id: "geartech_kagebreaker", name: "Kagebreaker Draw", kanji: "断", power: 1.18, stat: "ken", hits: 2, note: "A two-part draw cut released from the Kagebreaker Blade" } },
  { id: "uniq_nine_seal_talisman", name: "Nine-Seal Talisman", rarity: "legendary", kind: "passive", icon: "封", missionOnly: true, appearance: "Nine tiny lacquered seal plates hang from braided crimson cord around a central jade token covered in microscopic script.", desc: "Mission exclusive. +7 NIN, +4 MED, +25% chakra, +8% DEF and regenerates 3 HP each round.", skill: { nin: 7, med: 4 }, battle: { cp: 1.25, def: 1.08, regen: 3 } },
];
'''
    marker = 'export const EQUIPMENT_CATALOG: EquipmentItem[] = Array.from({ length: 400 }, (_, i) => makeItem(i));'
    if marker not in s:
        raise SystemExit('equipment catalogue anchor missing')
    s = s.replace(marker, unique + '\nexport const EQUIPMENT_CATALOG: EquipmentItem[] = [...Array.from({ length: 400 }, (_, i) => makeItem(i)), ...MISSION_UNIQUE_GEAR];', 1)
s = s.replace('const pool = EQUIPMENT_CATALOG.filter((x) => x.rarity === rarity);', 'const pool = EQUIPMENT_CATALOG.filter((x) => x.rarity === rarity && !x.missionOnly);')
write(p, s)

special_rel = 'src/game/specialMissionsV2.ts' if (ROOT / 'src/game/specialMissionsV2.ts').exists() else 'src/game/specialMissions.ts'
s = read(special_rel)
if '{ kind: "gear";' not in s:
    s = s.replace('  | { kind: "jutsu"; jutsuId: string };', '  | { kind: "jutsu"; jutsuId: string }\n  | { kind: "gear"; gearId: string; name: string };', 1)
if 'smokeveil_cache' not in s:
    specials = r'''  { id: "smokeveil_cache", name: "The Smokeveil Cache", grade: "C", desc: "A retired courier left directions to a hidden cache that can only be reached without alerting the local smugglers.", warning: "CONTESTED CACHE: the route crosses active smuggler territory. Success awards the unique Smokeveil Mask; it cannot be pulled from equipment gacha.", focus: ["ste", "spd", "tac"], slots: 2, reward: { kind: "gear", gearId: "uniq_smokeveil_mask", name: "Smokeveil Mask" } },
  { id: "iron_leaf_relic", name: "Relic of the Iron Leaf", grade: "B", desc: "An abandoned battlefield shrine contains the bracers of a famous close-combat instructor.", warning: "RELIC RECOVERY: rival scavengers are already searching the site. Success awards the unique Iron Leaf Bracers.", focus: ["tai", "ken", "tac"], slots: 3, reward: { kind: "gear", gearId: "uniq_iron_leaf_bracers", name: "Iron Leaf Bracers" } },
  { id: "stormglass_vault", name: "The Stormglass Vault", grade: "A", desc: "A lightning-scarred vault opens only during the centre of a mountain storm.", warning: "LETHAL WEATHER: lightning strikes and collapsing stone make failure dangerous. Success awards the unique Stormglass Ring and its Thunderclap Seal technique.", focus: ["nin", "spd", "med", "tac"], slots: 3, reward: { kind: "gear", gearId: "uniq_stormglass_ring", name: "Stormglass Ring" } },
  { id: "white_heron_route", name: "The White Heron's Last Route", grade: "A", desc: "Follow the final coded route of an elite courier who vanished while carrying a legendary infiltration cloak.", warning: "DEEP INFILTRATION: enemy sensor teams still patrol the route. Success awards the unique White Heron Cloak.", focus: ["ste", "gen", "spd", "tac"], slots: 3, reward: { kind: "gear", gearId: "uniq_white_heron_cloak", name: "White Heron Cloak" } },
  { id: "kagebreakers_grave", name: "Kagebreaker's Grave", grade: "S", desc: "A sealed duelling ground is said to contain the blade of a shinobi who once defeated a Kage in single combat.", warning: "S-RANK RELIC: multiple missing-nin cells are converging on the grave. Success awards the legendary Kagebreaker Blade and its signature draw technique.", focus: ["ken", "ste", "tac", "spd"], slots: 4, reward: { kind: "gear", gearId: "uniq_kagebreaker_blade", name: "Kagebreaker Blade" } },
  { id: "nine_seal_treasury", name: "The Nine-Seal Treasury", grade: "S", desc: "Nine interlocking barrier rooms protect a talisman built by generations of sealing masters.", warning: "FORBIDDEN SEALS: a failed breach may injure the entire cell. Success awards the legendary Nine-Seal Talisman.", focus: ["nin", "gen", "med", "doj"], slots: 4, reward: { kind: "gear", gearId: "uniq_nine_seal_talisman", name: "Nine-Seal Talisman" } },
'''
    marker = '];\n\nexport const SPECIAL_BY_ID'
    if marker not in s:
        raise SystemExit(f'special mission list marker missing in {special_rel}')
    s = s.replace(marker, specials + '];\n\nexport const SPECIAL_BY_ID', 1)
if 'r.kind === "gear"' not in s:
    s = s.replace('  if (r.kind === "jutsu") return `UNIQUE JUTSU: ${r.jutsuId}`;\n  return `VILLAGE UNLOCK: ${r.key}`;', '  if (r.kind === "jutsu") return `UNIQUE JUTSU: ${r.jutsuId}`;\n  if (r.kind === "gear") return `UNIQUE GEAR: ${r.name}`;\n  return `VILLAGE UNLOCK: ${r.key}`;', 1)
write(special_rel, s)

p = 'src/components/MissionBoard.tsx'
s = read(p)
s = s.replace('Rare contracts with permanent rewards, unique traits, techniques or unlocks.', 'Rare contracts with permanent rewards: traits, jutsu, unique gear, Potential breakthroughs or village unlocks.')
write(p, s)

p = 'src/components/SquadModal.tsx'
s = read(p)
s = s.replace('specialDef.reward.kind === "unlock" || squad.some((n) => specialRecipientEligible(specialDef, n))', '(specialDef.reward.kind === "unlock" || specialDef.reward.kind === "gear") || squad.some((n) => specialRecipientEligible(specialDef, n))')
write(p, s)

p = 'src/game/engine.ts'
s = read(p)
if 'ensureEquipmentState' not in '\n'.join(s.splitlines()[:30]):
    s = s.replace('import { equipmentSkillBonus } from "./equipment";', 'import { equipmentSkillBonus, ensureEquipmentState } from "./equipment";', 1)
if 'def.reward.kind === "gear"' not in s:
    anchor = '  if (def.reward.kind === "unlock") { const list = s.specialUnlocks ?? (s.specialUnlocks = []); if (!list.includes(def.reward.key)) list.push(def.reward.key); return `Village discovery unlocked: ${m.specialRewardLabel}.`; }'
    gear = anchor + '\n  if (def.reward.kind === "gear") { const inv = ensureEquipmentState(s).inventory; inv[def.reward.gearId] = (inv[def.reward.gearId] ?? 0) + 1; return `Unique gear acquired: ${def.reward.name}. It has been added to the Equipment inventory.`; }'
    if anchor not in s:
        raise SystemExit('special reward engine anchor missing')
    s = s.replace(anchor, gear, 1)
s = s.replace('reward.kind === "unlock" ? reward.key : undefined', 'reward.kind === "unlock" ? reward.key : reward.kind === "gear" ? reward.gearId : undefined')
write(p, s)

p = 'src/game/missionReports.ts'
s = read(p)
if '"Deliver Fresh Medicine"' not in s:
    beats = r'''  "Deliver Fresh Medicine": { open: "The medicine pack was sealed into an insulated satchel and handed over with strict timing instructions.", win: "The dose reached the outer farms cold, intact and early enough for treatment to begin immediately.", fail: "A delay on the ridge road spoiled the medicine before it reached the patient." },
  "Patrol the East Wall": { open: "Two warning seals on the east wall had stopped reporting before sunrise.", win: "A damaged wire and a prowling thief were both found; the perimeter was secure again before nightfall.", fail: "The patrol found signs of tampering but could not identify who crossed the perimeter." },
  "Recover the Academy Kunai": { open: "The academy quartermaster counted the training racks twice before admitting twelve kunai were missing.", win: "The missing weapons were found beneath the old practice shed where students had hidden them after an unsanctioned game.", fail: "The search turned up footprints but none of the missing academy weapons." },
  "Rebuild the Market Stall": { open: "Storm winds had folded the spice merchant's stall into the lane overnight.", win: "The stall was rebuilt, reinforced and reopened before the afternoon market crowd arrived.", fail: "A second structural collapse forced the workers to abandon the job for the day." },
  "Track the Missing Goat": { open: "The prize goat's bell could occasionally be heard somewhere above the terraced woodland.", win: "The goat was cornered on a narrow ledge and carried home loudly objecting to the entire operation.", fail: "The bell vanished deeper into the woods and the team returned goatless." },
  "Escort the Bridge Surveyor": { open: "The surveyor needed measurements from both banks of a crossing claimed by two rival villages.", win: "Every marker was placed and the survey completed without either side disrupting the work.", fail: "Armed locals forced the survey team away before the final measurements could be taken." },
  "Stop the Toll-Road Extortion": { open: "Merchants had begun travelling in groups after armed men erected an illegal barrier across the road.", win: "The extortion crew surrendered their toll chest and the road reopened before midday.", fail: "The gang scattered into the hills and returned to the road after the cell withdrew." },
  "Investigate the Smuggler's Tunnel": { open: "Fresh earth beneath a roadside shrine suggested the smugglers had opened a route below the border patrols.", win: "The tunnel was mapped from end to end and its hidden exits marked for closure.", fail: "A concealed collapse sealed the route before the team could discover where it emerged." },
  "Protect the Herbalist Expedition": { open: "The herbalists needed moonleaf from a valley where recent predator tracks were unusually large.", win: "The expedition gathered a full season's supply and returned without losing a single basket.", fail: "Repeated attacks forced the herbalists to abandon the valley with almost nothing collected." },
  "Capture the Masked Burglar": { open: "The burglar struck only tiled compounds and always vanished before the alarm bells finished ringing.", win: "A rooftop feint drove the masked thief into a waiting net team and ended the string of robberies.", fail: "The burglar slipped through a decoy cordon and disappeared across the roofline again." },
  "Raid the Counterfeit Seal Workshop": { open: "Forged travel seals were being dried in a guarded riverside workshop before shipment.", win: "The presses, seal dies and finished documents were seized before the forgers could burn them.", fail: "The workshop was torched by its own guards and the evidence was lost in the fire." },
  "Rescue the Border Watch": { open: "A single flare from the watch post confirmed the defenders were still alive but nearly surrounded.", win: "The encirclement was broken and every surviving sentry extracted before the post fell.", fail: "The attackers overran the position before the relief cell could force a corridor through." },
  "Shadow the Enemy Diplomat": { open: "The envoy changed clothes twice before leaving the guest compound through a servants' gate.", win: "Four covert contacts were identified without the diplomat ever realising they were followed.", fail: "A counter-surveillance turn exposed the tail and the diplomat cancelled the remaining meetings." },
  "Clear the Spider Caverns": { open: "Silk thick as rope blocked the trade tunnel and venom stains marked the abandoned carts inside.", win: "The breeding chamber was destroyed and the tunnel burned clear enough for engineers to reopen it.", fail: "The swarm forced a retreat before the largest nest could be reached." },
  "Seize the River Fortress": { open: "The customs fort controlled the river bend and could signal reinforcements with a single fire arrow.", win: "The signal tower fell first and the garrison surrendered before relief boats came into sight.", fail: "A warning arrow escaped the fort and incoming reinforcements forced the assault to break off." },
  "Extract the Double Agent": { open: "The asset's final coded message contained only a street, a bell time and the word compromised.", win: "The double agent crossed the extraction line minutes before enemy hunters sealed the district.", fail: "The rendezvous was empty except for a burned cipher strip and signs of a hurried arrest." },
  "Break the Blood-Mist Cell": { open: "Three assassinations in one week carried the same fine red mist residue around the wounds.", win: "The assassination cell was cornered in its safehouse and dismantled before another target could be named.", fail: "The killers abandoned the safehouse moments before the raid and vanished into allied territory." },
  "Defend the Hidden Hospital": { open: "The field hospital began evacuating patients as soon as enemy scouts appeared on the ridge.", win: "The attackers were held outside the treatment caves until every patient had been moved to safety.", fail: "The strike force breached the outer wards and the hospital had to be abandoned under fire." },
  "Steal the Siege Plans": { open: "The command pavilion kept the siege maps chained to a table whenever the general was absent.", win: "A complete copy of the assault plan reached the village before the enemy noticed the pavilion had been entered.", fail: "A guard rotation changed unexpectedly and forced the infiltrators out before the plans were copied." },
  "Capture the Storm Caller": { open: "Burned trees and fused stones marked the rogue lightning user's path through the uplands.", win: "The Storm Caller was exhausted, bound and brought back alive despite a final lightning barrage.", fail: "The target broke the containment line with a wide-area strike and escaped into the storm." },
  "The Black Sun Assassination": { open: "For six minutes at dusk, the warlord's overlapping guard rotations left one route imperfectly covered.", win: "The target fell inside that six-minute window and the cell was beyond the inner wall before the alarm spread.", fail: "The security gap closed early and the assassination team withdrew under pursuit." },
  "Seal the Walking Calamity": { open: "The transformed shinobi's chakra could be felt through the ground long before the team saw the devastation.", win: "Layered seals contained the unstable chakra and the calamity collapsed without another district being destroyed.", fail: "The first containment lattice shattered and the team had to evacuate before the chakra surge consumed them." },
  "Infiltrate the Kage's Inner Court": { open: "The inner residence admitted only sworn retainers whose identities were checked at three separate gates.", win: "Proof of the invasion order was removed from the private archive and replaced before dawn.", fail: "The final identity check exposed the infiltration and the cell escaped without reaching the archive." },
  "Shatter the Moonless Fortress": { open: "The fortress lights were deliberately extinguished on moonless nights to hide troop movements in the valley.", win: "Demolition teams broke the inner supports and the fortress became unusable before its army could deploy.", fail: "The defenders isolated the demolition team and forced the assault back from the inner wall." },
  "Stop the Forbidden Resurrection": { open: "The ritual chamber was already drawing chakra from nine outer pylons when the strike cell arrived.", win: "The central seal was destroyed seconds before the resurrection completed and the ritual collapsed harmlessly.", fail: "The cell broke several pylons but could not reach the central seal before being driven out." },
  "The Smokeveil Cache": { open: "The courier's map ended at a cliff path watched by smugglers who did not know what was hidden beneath them.", win: "The cache was opened without raising an alarm; the Smokeveil Mask was wrapped inside an oilskin packet.", fail: "Smuggler patrols closed on the route and forced the team away before the cache could be reached." },
  "Relic of the Iron Leaf": { open: "Rusting prayer tags marked a battlefield shrine that rival scavengers had already begun to search.", win: "The Iron Leaf Bracers were recovered from beneath the shrine stone before the rival cell reached the chamber.", fail: "The scavengers collapsed the relic chamber and escaped with whatever had been stored inside." },
  "The Stormglass Vault": { open: "The vault door only reacted when lightning struck the metal spine running down the mountain.", win: "The team crossed the charged chambers and recovered the Stormglass Ring as the storm reached its peak.", fail: "Repeated lightning strikes made the vault approach untenable and the cell withdrew injured." },
  "The White Heron's Last Route": { open: "The vanished courier's code led through three sensor screens and a route no ordinary messenger would choose.", win: "The final dead drop contained the White Heron Cloak, still folded around the courier's last report.", fail: "Enemy sensors caught the team near the final marker and the route had to be abandoned." },
  "Kagebreaker's Grave": { open: "Five missing-nin groups were already climbing toward the sealed duelling ground when the village cell arrived.", win: "The competitors were beaten to the inner grave and the Kagebreaker Blade claimed from its stone stand.", fail: "A rival elite cell reached the grave first and forced the village team from the summit." },
  "The Nine-Seal Treasury": { open: "Each chamber in the treasury carried a different sealing rule and punished the wrong answer immediately.", win: "All nine rooms were opened in sequence and the Nine-Seal Talisman removed without collapsing the barrier complex.", fail: "The sixth seal reflected the breach attempt and injured the cell badly enough to force retreat." },
'''
    marker = '\n};\n\nexport function missionReportBeat'
    if marker not in s:
        raise SystemExit('missionReports table marker missing')
    s = s.replace(marker, '\n' + beats + marker, 1)
write(p, s)

p = 'public/sw.js'
s = read(p)
s, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-depth-v1-jutsu-potential-v3-missions-traits-unique-gear";', s, count=1)
if n != 1:
    raise SystemExit('service worker cache constant missing')
write(p, s)

print('Village depth v3: +25 missions, +12 traits, +6 mission-exclusive gear rewards applied')
