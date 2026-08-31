from pathlib import Path

ROOT = Path('app')


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(rel: str, old: str, new: str, label: str) -> None:
    s = read(rel)
    if new in s:
        print(f'{label}: already applied')
        return
    if old not in s:
        raise SystemExit(f'{label}: anchor not found in {rel}')
    write(rel, s.replace(old, new, 1))
    print(f'{label}: applied')

# ---------------------------------------------------------------------------
# 102-event hunt library: add 64 new skill-driven route events (8 per biome).
# ---------------------------------------------------------------------------
p = 'src/game/huntEvents.ts'
s = read(p)
if 'HUNT_EVENT_EXPANSION_V6' not in s:
    anchor = '\nfunction hashSeed(value: number): number {'
    if anchor not in s:
        raise SystemExit('hunt event expansion anchor not found')
    block = r'''

// HUNT_EVENT_EXPANSION_V6
// Eight new route-specific checks per biome. Together with the original 38,
// this brings the reusable hunt-event library to 102 distinct events.
type HuntExpansionPayoff = "intel" | "ambush" | "capture" | "supplies" | "target" | "escape" | "chakra" | "control";
type HuntExpansionRow = [string, string, string, Skill, number, HuntExpansionPayoff];
type HuntExpansionGroup = { biome: Exclude<HuntBiome, "any">; rows: HuntExpansionRow[] };

function expansionEffects(kind: HuntExpansionPayoff): { tags: HuntTag[]; success: HuntChoiceEffect; failure: HuntChoiceEffect } {
  switch (kind) {
    case "intel": return {
      tags: ["intel"],
      success: { label: "Read the trail", result: "The cell extracts a clean lead and tightens the dossier.", intelDelta: 10 },
      failure: { label: "Trail goes cold", result: "The delay gives the target time to prepare an answer.", enemyAmbushRounds: 1 },
    };
    case "ambush": return {
      tags: ["ambush", "combat"],
      success: { label: "Take the angle", result: "The hunters secure the opening initiative at contact.", playerAmbushRounds: 1, intelDelta: 2 },
      failure: { label: "Position exposed", result: "The target's scouts turn the approach into a painful counter-position.", hpDelta: -0.14, enemyAmbushRounds: 1 },
    };
    case "capture": return {
      tags: ["capture", "escape"],
      success: { label: "Close the net", result: "An escape lane is removed and the restraint plan improves.", captureBonus: 0.12, targetCannotFleeRounds: 1 },
      failure: { label: "Net breaks", result: "The target gains space while the cell burns chakra recovering the route.", chakraDelta: -0.14 },
    };
    case "supplies": return {
      tags: ["supplies", "chakra"],
      success: { label: "Use the opening", result: "A safe pause restores part of the cell's fighting reserves.", hpDelta: 0.08, chakraDelta: 0.10 },
      failure: { label: "Bad stop", result: "The pause costs more strength than it restores.", chakraDelta: -0.16, addStatus: "fatigued" },
    };
    case "target": return {
      tags: ["combat", "intel"],
      success: { label: "Pressure the target", result: "The pursuit forces the missing-nin to spend blood and chakra before contact.", targetHpDelta: -0.12, targetChakraDelta: -0.10, intelDelta: 3 },
      failure: { label: "Pressure reverses", result: "The target slips the pressure and chooses the battlefield instead.", enemyAmbushRounds: 1 },
    };
    case "escape": return {
      tags: ["escape", "capture"],
      success: { label: "Seal the route", result: "The cell blocks the most likely withdrawal corridor.", targetCannotFleeRounds: 2, captureBonus: 0.05 },
      failure: { label: "Route misread", result: "The wrong lane is sealed and the target gains a cleaner retreat.", enemyAmbushRounds: 1 },
    };
    case "chakra": return {
      tags: ["chakra", "combat"],
      success: { label: "Win the chakra exchange", result: "The hunters conserve their reserves while forcing the target to spend theirs.", chakraDelta: 0.10, targetChakraDelta: -0.10 },
      failure: { label: "Lose the exchange", result: "The pursuit burns through one hunter's reserves.", chakraDelta: -0.20 },
    };
    case "control": return {
      tags: ["status", "ambush"],
      success: { label: "Control the approach", result: "The cell enters contact with a restraint advantage.", captureBonus: 0.06, targetChakraDelta: -0.08 },
      failure: { label: "Formation disrupted", result: "One hunter is delayed as the route collapses around the formation.", delayedRounds: 1, hpDelta: -0.08 },
    };
  }
}

const HUNT_EXPANSION_GROUPS: HuntExpansionGroup[] = [
  { biome: "forest", rows: [
    ["canopy_signals", "Signals in the Canopy", "Fresh cord knots high in the branches mark a relay line used by the target's scouts.", "ste", 56, "intel"],
    ["cedar_kill_lane", "Cedar Kill-Lane", "Cut bark and unnatural silence reveal a prepared firing corridor ahead.", "tac", 61, "ambush"],
    ["owl_feather_marker", "The Owl-Feather Marker", "A feather charm repeats on three trees, each pointing toward a concealed withdrawal route.", "doj", 58, "escape"],
    ["herbalist_hut", "Abandoned Herbalist Hut", "A hut stripped in haste still holds field medicines and the target's bloody wrappings.", "med", 54, "supplies"],
    ["sword_marks_pines", "Sword Marks in the Pines", "Deep practice cuts on old trunks reveal where an armed associate waited for the pursuit.", "ken", 60, "target"],
    ["deer_path_sprint", "Deer-Path Sprint", "A narrow game trail can put the cell ahead if they can keep pace without breaking formation.", "spd", 57, "ambush"],
    ["ash_chakra_residue", "Ash-Chakra Residue", "Warm ash carries a faint chakra signature from a recently extinguished technique.", "nin", 62, "chakra"],
    ["whispering_grove", "Whispering Grove", "A low illusion makes every tree sound like a moving shinobi.", "gen", 63, "control"],
  ]},
  { biome: "mountain", rows: [
    ["goat_track", "Goat Track Above the Pass", "A near-vertical trail bypasses the main ridge and the target's obvious sentries.", "ste", 60, "ambush"],
    ["avalanche_marks", "Avalanche Marks", "Fresh scoring on the snowpack suggests the target prepared a controlled collapse.", "tac", 65, "control"],
    ["distant_heat_glint", "Heat Glint on the Ridge", "A tiny distortion far above betrays a lookout using chakra to stay warm.", "doj", 63, "intel"],
    ["thin_air_cramp", "Thin-Air Cramp", "One hunter's breathing turns ragged as the pursuit climbs beyond the tree line.", "med", 58, "supplies"],
    ["ridge_duelist", "Duelist on the Ridge", "A blade specialist bars the only stable ledge and dares the cell to force passage.", "ken", 66, "target"],
    ["scree_race", "Race Across the Scree", "Loose stone makes the shortest descent a contest of speed and balance.", "spd", 61, "escape"],
    ["storm_rod_seal", "Storm-Rod Seal", "Metal rods driven into the ridge are drawing chakra from the weather into a trap.", "nin", 67, "chakra"],
    ["echo_maze", "Echo Maze", "Genjutsu twists the mountain's echoes until footsteps seem to approach from every direction.", "gen", 65, "control"],
  ]},
  { biome: "river", rows: [
    ["reed_channel", "Hidden Reed Channel", "A low channel through the reeds carries a boat wake too small for a merchant craft.", "ste", 55, "intel"],
    ["bridge_crossfire", "Bridge Crossfire", "Two abandoned packs on opposite banks mark a rehearsed crossfire position.", "tac", 61, "ambush"],
    ["water_reflection", "Broken Reflection", "A distant reflection moves against the current, exposing a concealed observer.", "doj", 59, "intel"],
    ["leeched_hunter", "Blood-Leech Crossing", "River leeches carrying chakra-reactive venom cling to one hunter after the crossing.", "med", 57, "supplies"],
    ["ferryman_blade", "The Ferryman's Blade", "A hired swordsman waits on the only intact ferry and refuses passage.", "ken", 62, "target"],
    ["rapid_cutoff", "Rapid Cut-Off", "A sprint along slick stones could reach the next bend before the target's boat.", "spd", 60, "escape"],
    ["chakra_current", "Chakra in the Current", "The water carries enough residual chakra to reveal how hard the target has been travelling.", "nin", 61, "chakra"],
    ["mist_double", "Mist Double", "A false silhouette keeps pace on the opposite bank, trying to drag the hunt downstream.", "gen", 63, "control"],
  ]},
  { biome: "urban", rows: [
    ["roofline_runner", "Runner on the Roofline", "A courier crosses three rooftops without looking down, carrying the target's coded sash.", "ste", 58, "intel"],
    ["market_chokepoint", "Market Chokepoint", "Closed stalls create a perfect funnel, but the target's people have already noticed the crowd shifting.", "tac", 62, "ambush"],
    ["window_reflection", "Watcher in the Window", "A reflection reveals someone observing the squad from behind shuttered glass.", "doj", 60, "intel"],
    ["backstreet_clinic", "Backstreet Clinic", "A frightened doctor treated someone matching the target only minutes earlier.", "med", 55, "target"],
    ["courtyard_enforcer", "Courtyard Enforcer", "A scarred blade-for-hire blocks a narrow courtyard while civilians scatter.", "ken", 64, "target"],
    ["alley_intercept", "Alley Intercept", "Two parallel alleys offer a chance to overtake the target before the district gate.", "spd", 59, "escape"],
    ["seal_lanterns", "Sealed Lantern Row", "Paper lanterns hide linked chakra tags designed to reveal every pursuer who passes.", "nin", 64, "chakra"],
    ["borrowed_faces", "Borrowed Faces", "A layered illusion makes half the street resemble the missing-nin.", "gen", 66, "control"],
  ]},
  { biome: "desert", rows: [
    ["dune_shadow", "Shadow Behind the Dune", "A barely disturbed lee-side slope hides where a scout watched the road.", "ste", 57, "intel"],
    ["salt_flat_trap", "Salt-Flat Trap", "The open ground looks safe precisely because there is nowhere to hide from a prepared attack.", "tac", 63, "ambush"],
    ["heat_haze_tell", "Tell in the Heat Haze", "Enhanced sight catches one distortion moving independently of the mirage.", "doj", 61, "intel"],
    ["sunstroke", "Sunstroke", "One hunter's coordination begins to fail under the relentless heat.", "med", 58, "supplies"],
    ["caravan_champion", "Caravan Champion", "A mercenary swordsman bought by the target waits beside an overturned wagon.", "ken", 64, "target"],
    ["dune_cutoff", "Dune Cut-Off", "A hard sprint over the crest could remove the target's straightest line to open desert.", "spd", 62, "escape"],
    ["glass_chakra", "Chakra-Fused Glass", "A recent fire technique melted sand into glass that still carries the target's signature.", "nin", 63, "chakra"],
    ["mirage_column", "Marching Mirage", "An illusion of a travelling column masks the real target's change of direction.", "gen", 65, "control"],
  ]},
  { biome: "marsh", rows: [
    ["bog_reed_code", "Reed-Cut Code", "Reeds have been clipped at ankle height in a pattern used to guide smugglers through the bog.", "ste", 56, "intel"],
    ["sinking_lane", "Sinking Lane", "The obvious path is deliberately weakened mud designed to break a pursuing formation.", "tac", 61, "control"],
    ["firefly_gap", "Gap in the Fireflies", "A moving patch of darkness among the insects outlines a concealed shinobi.", "doj", 59, "ambush"],
    ["fever_water", "Fever Water", "A hunter swallowed marsh water during the last crossing and is fading fast.", "med", 57, "supplies"],
    ["boardwalk_blade", "Blade on the Boardwalk", "An associate waits on the only dry crossing, using the narrow boards to limit numbers.", "ken", 63, "target"],
    ["bog_skip", "Bog-Skip Route", "A sequence of half-submerged stones could cut the pursuit distance dramatically.", "spd", 60, "escape"],
    ["swamp_gas_seal", "Swamp-Gas Seal", "Chakra tags are using marsh gas as a trigger for a wide-area blast.", "nin", 64, "chakra"],
    ["drowning_voices", "Drowning Voices", "Genjutsu makes cries for help drift from every pool around the squad.", "gen", 64, "control"],
  ]},
  { biome: "ruins", rows: [
    ["dustless_steps", "Dustless Footsteps", "A line of stones with no dust shows exactly where someone crossed the abandoned hall.", "ste", 58, "intel"],
    ["murder_hall", "The Murder Hall", "Arrow holes, cut pillars and fresh wire turn a ceremonial chamber into a designed kill-box.", "tac", 65, "ambush"],
    ["seal_script", "Script Beneath the Dust", "A faint ocular pattern reveals fresh writing hidden beneath centuries of grime.", "doj", 62, "intel"],
    ["old_infirmary", "Old Infirmary", "Ancient cabinets still contain sealed field supplies beside a recent blood trail.", "med", 58, "supplies"],
    ["guardian_statue", "Blade at the Guardian Statue", "A swordsman uses the fallen statuary to make a narrow defensive line.", "ken", 66, "target"],
    ["collapsing_gallery", "Collapsing Gallery", "The upper gallery is failing, but crossing it could put the cell directly above the target.", "spd", 63, "ambush"],
    ["sealed_engine", "Sealed Chakra Engine", "A dead mechanism has been restarted with the target's chakra to power traps deeper inside.", "nin", 67, "chakra"],
    ["memory_corridor", "Memory Corridor", "The hallway projects false memories of previous missions to split the squad's attention.", "gen", 68, "control"],
  ]},
  { biome: "road", rows: [
    ["milestone_cipher", "Milestone Cipher", "Scratches on roadside stones form a moving code used by the target's couriers.", "ste", 56, "intel"],
    ["wagon_barricade", "Wagon Barricade", "Two overturned carts create a choke point too deliberate to be an accident.", "tac", 61, "ambush"],
    ["horizon_silhouette", "Silhouette on the Horizon", "Enhanced sight identifies a stationary figure watching the road from far beyond normal vision.", "doj", 59, "intel"],
    ["traveller_injured", "Injured Traveller", "A traveller caught in the target's wake can identify their direction if stabilised quickly.", "med", 55, "intel"],
    ["bridge_swordsman", "Swordsman at the Toll Bridge", "A paid duelist has closed the bridge and is buying the target time.", "ken", 63, "target"],
    ["relay_horses", "Abandoned Relay Horses", "Fresh relay horses could let the cell leapfrog the target before the next junction.", "spd", 58, "escape"],
    ["burned_waystation", "Burned Waystation", "Residual chakra in a scorched post reveals the technique used to destroy it.", "nin", 62, "chakra"],
    ["endless_road", "The Endless Road", "A subtle loop illusion makes the same crooked tree appear at every bend.", "gen", 64, "control"],
  ]},
];

for (const group of HUNT_EXPANSION_GROUPS) {
  group.rows.forEach(([id, title, blurb, skill, difficulty, payoff], i) => {
    const fx = expansionEffects(payoff);
    HUNT_EVENTS.push(event(`v6_${group.biome}_${id}`, title, blurb, "mixed", [group.biome], fx.tags, {
      weight: 9 + (i % 3),
      check: {
        skill,
        difficulty,
        success: fx.success,
        failure: fx.failure,
      },
    }));
  });
}

export const HUNT_EVENT_TOTAL = HUNT_EVENTS.length;
'''
    s = s.replace(anchor, block + anchor, 1)
    write(p, s)
print('Bingo hunt event library expanded to 102: applied')

# ---------------------------------------------------------------------------
# Machine-readable boss mechanics that stay aligned with dossier copy.
# ---------------------------------------------------------------------------
p = 'src/game/bingo.ts'
s = read(p)
if 'export type BingoMechanicId' not in s:
    anchor = 'export type BingoThreat = "B" | "A" | "S" | "S+" | "SS" | "BLACK";\n'
    mech_type = '''export type BingoMechanicId =\n  | "burning_ground" | "false_bodies"\n  | "prepared_ambush" | "third_strike_crit" | "half_hp_decoy" | "momentum" | "marked_hunter"\n  | "repeat_hazard" | "chakra_conversion" | "counter_stance" | "low_hp_flee" | "layered_armour"\n  | "heal_punish" | "rotating_resistance" | "delay_hunter" | "hunt_barrier" | "bleed_weapon"\n  | "clone_on_down" | "high_chakra_dodge" | "charged_signature" | "initiative_theft" | "sealing_marks"\n  | "heal_on_miss" | "phase_shift" | "enraged_on_ambush" | "smoke_escape";\n'''
    if anchor not in s:
        raise SystemExit('Bingo mechanic type anchor missing')
    s = s.replace(anchor, anchor + mech_type, 1)

if 'bossMechanicIds?: BingoMechanicId[];' not in s:
    s = s.replace('  bossMechanics: string[];\n', '  bossMechanics: string[];\n  bossMechanicIds?: BingoMechanicId[];\n', 1)

s = s.replace('bossMechanics: ["Fire techniques leave Burning Ground for two rounds."],', 'bossMechanics: ["Fire techniques leave Burning Ground for two rounds."],\n    bossMechanicIds: ["burning_ground"],', 1)
s = s.replace('bossMechanics: ["Begins with four false bodies; sensory and dōjutsu checks can expose the real target early."],', 'bossMechanics: ["Begins with four false bodies; sensory and dōjutsu checks can expose the real target early."],\n    bossMechanicIds: ["false_bodies"],', 1)
s = s.replace('bossMechanics: ["Attempts to flee below 25% HP unless restrained, sealed or prevented by a hunt modifier."],', 'bossMechanics: ["Attempts to flee below 25% HP unless restrained, sealed or prevented by a hunt modifier."],\n    bossMechanicIds: ["low_hp_flee"],', 1)

if 'const BINGO_MECHANIC_IDS' not in s:
    anchor = 'const BINGO_MECHANICS = [\n'
    ids = '''const BINGO_MECHANIC_IDS: BingoMechanicId[] = [\n  "prepared_ambush", "third_strike_crit", "half_hp_decoy", "momentum", "marked_hunter", "repeat_hazard",\n  "chakra_conversion", "counter_stance", "low_hp_flee", "layered_armour", "heal_punish", "rotating_resistance",\n  "delay_hunter", "hunt_barrier", "bleed_weapon", "clone_on_down", "high_chakra_dodge", "charged_signature",\n  "initiative_theft", "sealing_marks", "heal_on_miss", "phase_shift", "enraged_on_ambush", "smoke_escape",\n];\n\n'''
    if anchor not in s:
        raise SystemExit('Bingo mechanics list anchor missing')
    s = s.replace(anchor, ids + anchor, 1)

if 'const mechanicIdA' not in s:
    old = '''  const mechanicA = BINGO_MECHANICS[(index * 5 + 1) % BINGO_MECHANICS.length];\n  const mechanicB = BINGO_MECHANICS[(index * 7 + 9) % BINGO_MECHANICS.length];'''
    new = '''  const mechanicIndexA = (index * 5 + 1) % BINGO_MECHANICS.length;\n  const mechanicIndexB = (index * 7 + 9) % BINGO_MECHANICS.length;\n  const mechanicA = BINGO_MECHANICS[mechanicIndexA];\n  const mechanicB = BINGO_MECHANICS[mechanicIndexB];\n  const mechanicIdA = BINGO_MECHANIC_IDS[mechanicIndexA];\n  const mechanicIdB = BINGO_MECHANIC_IDS[mechanicIndexB];'''
    if old not in s:
        raise SystemExit('generated mechanic index anchor missing')
    s = s.replace(old, new, 1)
    s = s.replace('    bossMechanics: highThreat ? [mechanicA, mechanicB] : [mechanicA],\n', '    bossMechanics: highThreat ? [mechanicA, mechanicB] : [mechanicA],\n    bossMechanicIds: highThreat ? [mechanicIdA, mechanicIdB] : [mechanicIdA],\n', 1)
write(p, s)
print('Bingo mechanic IDs: applied')

# ---------------------------------------------------------------------------
# Battle runtime state for mechanics. One contained optional object prevents the
# generic raid/exam battle schema from becoming a forest of one-off fields.
# ---------------------------------------------------------------------------
p = 'src/game/types.ts'
s = read(p)
if 'export interface BingoBattleRuntimeState' not in s:
    anchor = 'export interface Battle {\n'
    runtime = '''export interface BingoBattleRuntimeState {\n  mechanicIds: string[];\n  targetBaseAtk: number;\n  targetBaseDef: number;\n  targetBaseSpd: number;\n  targetBaseNin: number;\n  targetBaseDodge: number;\n  targetBaseCounter: number;\n  bossActions: number;\n  momentum: number;\n  markedUid: string | null;\n  lastPlayerAction: BAction | null;\n  hazardRounds: number;\n  armourStacks: number;\n  falseBodies: number;\n  halfHpDecoyUsed: boolean;\n  currentAction: BAction | null;\n  currentActorUid: string | null;\n  convertedCharge: number;\n  chargeState: 0 | 1;\n  sealMarks: number;\n  seenAllyDeaths: number;\n  resistNature: Nature | null;\n  escapeAttempted: boolean;\n  huntPrep: number;\n  enemyAmbushAtStart: number;\n}\n\n'''
    if anchor not in s:
        raise SystemExit('Battle runtime type anchor missing')
    s = s.replace(anchor, runtime + anchor, 1)
    s = s.replace('  bingoTargetCannotFleeRounds?: number;\n', '  bingoTargetCannotFleeRounds?: number;\n  bingoRuntime?: BingoBattleRuntimeState;\n', 1)
write(p, s)
print('Bingo battle runtime type: applied')

# ---------------------------------------------------------------------------
# Wire mechanic IDs into contact battle config + runtime initialization.
# ---------------------------------------------------------------------------
p = 'src/game/bingoHunt.ts'
s = read(p)
if 'mechanicIds: target.bossMechanicIds ?? []' not in s:
    old = '    focus: target.focus,\n    members: run.members,\n'
    new = '    focus: target.focus,\n    mechanicIds: target.bossMechanicIds ?? [],\n    members: run.members,\n'
    if old not in s:
        raise SystemExit('Bingo boss config caller anchor missing')
    s = s.replace(old, new, 1)
write(p, s)

p = 'src/game/battle.ts'
s = read(p)
s = s.replace('import { ensureBingoState } from "./bingo";', 'import { BINGO_TARGET_BY_ID, ensureBingoState } from "./bingo";', 1)
if 'mechanicIds: string[];' not in s[s.find('export interface BingoBattleConfig'):s.find('export function startBingoBattle')]:
    s = s.replace('  focus: string[];\n  members:', '  focus: string[];\n  mechanicIds: string[];\n  members:', 1)

if 'bingoRuntime:' not in s[s.find('export function startBingoBattle'):s.find('/* ---------------- turn order ---------------- */')]:
    old = '''    bingoCaptureBonus: cfg.captureBonus,\n    bingoTargetCannotFleeRounds: cfg.targetCannotFleeRounds,\n  };\n  rollOrder(b, s.b.tower, true);'''
    new = '''    bingoCaptureBonus: cfg.captureBonus,\n    bingoTargetCannotFleeRounds: cfg.targetCannotFleeRounds,\n    bingoRuntime: {\n      mechanicIds: [...cfg.mechanicIds],\n      targetBaseAtk: foe.atk,\n      targetBaseDef: foe.def,\n      targetBaseSpd: foe.spd,\n      targetBaseNin: foe.nin,\n      targetBaseDodge: foe.dodge,\n      targetBaseCounter: foe.counter,\n      bossActions: 0,\n      momentum: 0,\n      markedUid: null,\n      lastPlayerAction: null,\n      hazardRounds: cfg.mechanicIds.includes("repeat_hazard") ? 2 : 0,\n      armourStacks: cfg.mechanicIds.includes("layered_armour") ? 4 : 0,\n      falseBodies: cfg.mechanicIds.includes("false_bodies") ? 4 : 0,\n      halfHpDecoyUsed: false,\n      currentAction: null,\n      currentActorUid: null,\n      convertedCharge: 0,\n      chargeState: 0,\n      sealMarks: 0,\n      seenAllyDeaths: 0,\n      resistNature: null,\n      escapeAttempted: false,\n      huntPrep: Math.max(0, cfg.playerAmbushRounds) + Math.max(0, 1 - cfg.targetHpRatio) * 3 + Math.max(0, cfg.captureBonus) * 2,\n      enemyAmbushAtStart: Math.max(0, cfg.enemyAmbushRounds),\n    },\n  };\n  if (cfg.mechanicIds.includes("prepared_ambush") && cfg.playerAmbushRounds <= 0) {\n    for (const ally of allies) ally.stun = Math.max(ally.stun, 1);\n    log(b, `${foe.name} springs a prepared ambush — the hunter cell starts on the back foot.`, "crit");\n  }\n  if (cfg.mechanicIds.includes("counter_stance")) foe.counter = Math.max(foe.counter, 0.28);\n  if (cfg.mechanicIds.includes("hunt_barrier")) {\n    foe.jutsuGuardRounds = 2;\n    foe.jutsuGuardStrength = Math.max(0.16, 0.46 - b.bingoRuntime!.huntPrep * 0.055);\n    log(b, `${foe.name}'s prepared barrier absorbs ${Math.round((foe.jutsuGuardStrength ?? 0) * 100)}% of incoming pressure.`, "info");\n  }\n  applyBingoRoundState(b);\n  rollOrder(b, s.b.tower, true);'''
    if old not in s:
        raise SystemExit('startBingoBattle runtime anchor missing')
    s = s.replace(old, new, 1)

if 'function bingoHas(b: Battle' not in s:
    anchor = '''function log(b: Battle, t: string, kind: Battle["log"][number]["kind"] = "info"): void {\n  b.log.push({ t, kind });\n  if (b.log.length > 40) b.log.shift();\n}\n'''
    helpers = r'''

function bingoHas(b: Battle, id: string): boolean {
  return b.mode === "bingo" && !!b.bingoRuntime?.mechanicIds.includes(id);
}

function bingoBoss(b: Battle): Unit | null {
  return b.mode === "bingo" ? b.units.find((u) => u.foe) ?? null : null;
}

function bingoInterruptCharge(b: Battle, reason: string): void {
  const rt = b.bingoRuntime;
  if (!rt || rt.chargeState !== 1) return;
  rt.chargeState = 0;
  log(b, `The charged signature technique collapses under ${reason}.`, "miss");
}

function bingoHealBossOnMiss(b: Battle): void {
  if (!bingoHas(b, "heal_on_miss")) return;
  const boss = bingoBoss(b);
  if (!boss?.alive) return;
  const heal = Math.max(1, Math.round(boss.maxHp * 0.045));
  boss.hp = Math.min(boss.maxHp, boss.hp + heal);
  log(b, `${boss.name} turns the missed attack into breathing room and recovers ${heal} HP.`, "heal");
}

function bingoCheckEscape(b: Battle): boolean {
  const boss = bingoBoss(b);
  const rt = b.bingoRuntime;
  if (!boss?.alive || !rt || b.state === "won" || b.state === "lost") return false;
  if ((b.bingoTargetCannotFleeRounds ?? 0) > 0 || boss.stun > 0 || (boss.chakraLockRounds ?? 0) > 0) return false;
  const targetDef = b.bingoTargetId ? BINGO_TARGET_BY_ID[b.bingoTargetId] : undefined;
  const ratio = boss.hp / Math.max(1, boss.maxHp);
  const fleeAt = targetDef?.fleeAtHp ?? 0.25;
  if (bingoHas(b, "low_hp_flee") && ratio <= fleeAt) {
    log(b, `${boss.name} breaks contact at ${Math.round(ratio * 100)}% HP and disappears from the battlefield!`, "miss");
    b.state = "lost";
    return true;
  }
  if (bingoHas(b, "smoke_escape") && !rt.escapeAttempted && ratio <= 0.20) {
    rt.escapeAttempted = true;
    log(b, `${boss.name}'s emergency smoke seal detonates — the target escapes the kill-zone!`, "miss");
    b.state = "lost";
    return true;
  }
  return false;
}

function applyBingoRoundState(b: Battle): void {
  const rt = b.bingoRuntime;
  const boss = bingoBoss(b);
  if (!rt || !boss?.alive) return;

  let atk = rt.targetBaseAtk;
  let def = rt.targetBaseDef;
  let spd = rt.targetBaseSpd;
  let nin = rt.targetBaseNin;
  let dodge = rt.targetBaseDodge;

  if (bingoHas(b, "phase_shift")) {
    if (b.round % 2 === 1) { atk *= 1.22; nin *= 1.18; def *= 0.86; }
    else { atk *= 0.88; nin *= 0.90; def *= 1.28; }
    log(b, `${boss.name} shifts into ${b.round % 2 === 1 ? "OFFENSIVE" : "DEFENSIVE"} phase.`, "info");
  }
  if (bingoHas(b, "momentum")) spd *= 1 + Math.min(4, rt.momentum) * 0.08;
  if (bingoHas(b, "high_chakra_dodge")) dodge += boss.cp / Math.max(1, boss.maxCp) > 0.50 ? 0.16 : -0.04;
  if (bingoHas(b, "enraged_on_ambush") && rt.enemyAmbushAtStart > 0 && b.round <= 2) {
    atk *= 1.25; nin *= 1.18; def *= 0.84;
    if (b.round === 1) log(b, `${boss.name} is enraged by the violent pursuit — offence surges while defence opens up.`, "crit");
  }

  boss.atk = atk;
  boss.def = def;
  boss.spd = spd;
  boss.nin = nin;
  boss.dodge = clamp(dodge, 0, 0.55);
  boss.counter = bingoHas(b, "counter_stance") ? Math.max(rt.targetBaseCounter, 0.28) : rt.targetBaseCounter;

  if (bingoHas(b, "rotating_resistance")) {
    const cycle = ["fire", "water", "wind", "earth", "light"] as const;
    rt.resistNature = cycle[(b.round - 1) % cycle.length];
    log(b, `${boss.name} rotates resistance to ${rt.resistNature.toUpperCase()} chakra.`, "info");
  }

  if (bingoHas(b, "marked_hunter")) {
    const live = aliveAllies(b);
    rt.markedUid = live.length ? live[(b.round - 1) % live.length].uid : null;
    const marked = rt.markedUid ? unitById(b, rt.markedUid) : null;
    if (marked) log(b, `${boss.name} marks ${marked.name} as this round's priority target.`, "crit");
  }

  if (bingoHas(b, "delay_hunter") && b.round > 1 && b.round % 2 === 0) {
    const live = aliveAllies(b);
    if (live.length) {
      const victim = live[(b.round + rt.bossActions) % live.length];
      victim.stun = Math.max(victim.stun, 1);
      log(b, `${boss.name} collapses the battlefield around ${victim.name}, delaying their action.`, "miss");
    }
  }

  const deadAllies = b.units.filter((u) => !u.foe && !u.alive).length;
  if (bingoHas(b, "clone_on_down") && deadAllies > rt.seenAllyDeaths) {
    boss.extraTurnPending = true;
    log(b, `${boss.name} creates a battlefield clone from the opening left by the fallen hunter.`, "crit");
  }
  rt.seenAllyDeaths = deadAllies;

  if (bingoHas(b, "charged_signature")) {
    if (rt.chargeState === 1) {
      let total = 0;
      for (const ally of aliveAllies(b)) total += damage(b, boss, ally, boss.nin * 1.15 + boss.atk * 0.55, "crit", true);
      log(b, `${boss.name} releases the charged signature technique for ${total} total damage!`, "crit");
      rt.chargeState = 0;
    } else if (b.round >= 3 && b.round % 3 === 0) {
      rt.chargeState = 1;
      log(b, `${boss.name} begins charging a catastrophic signature technique — interrupt it before next round.`, "crit");
    }
  }
}

function bingoBeforeAction(b: Battle, u: Unit, action: BAction): void {
  const rt = b.bingoRuntime;
  if (!rt) return;
  rt.currentAction = action;
  rt.currentActorUid = u.uid;

  if (u.foe) {
    if (action !== "guard" && action !== "heal") {
      rt.bossActions += 1;
      if (bingoHas(b, "momentum")) rt.momentum = Math.min(4, rt.momentum + 1);
      if (bingoHas(b, "third_strike_crit") && rt.bossActions % 3 === 0) {
        u.jutsuCritRounds = Math.max(u.jutsuCritRounds ?? 0, 1);
        u.jutsuCritBonus = Math.max(u.jutsuCritBonus ?? 0, 0.38);
        log(b, `${u.name}'s third strike is primed for a lethal critical window.`, "crit");
      }
      if (bingoHas(b, "sealing_marks")) {
        rt.sealMarks = Math.min(3, rt.sealMarks + 1);
        if (rt.sealMarks === 3) log(b, `Three sealing marks lock over the battlefield — hunter chakra recovery is suppressed.`, "miss");
      }
    }
  } else if (bingoHas(b, "repeat_hazard") && rt.hazardRounds > 0 && action !== "guard") {
    if (rt.lastPlayerAction === action) {
      const tick = Math.max(1, Math.round(u.maxHp * 0.07));
      u.hp = Math.max(0, u.hp - tick);
      log(b, `${u.name} repeats ${actionLabel(u, action)} and the elemental hazard lashes back for ${tick}.`, "hit");
      if (u.hp <= 0) { u.alive = false; log(b, `${u.name} is down!`, "down"); }
    }
    rt.lastPlayerAction = action;
  }
}
'''
    if anchor not in s:
        raise SystemExit('battle log helper anchor missing')
    s = s.replace(anchor, anchor + helpers, 1)

if 'bingoBeforeAction(b, u, action);' not in s:
    old = '''  const u = currentUnit(b);\n  if (!u) return { kind: "none", targets: [] };\n  u.guard = false;'''
    new = '''  const u = currentUnit(b);\n  if (!u) return { kind: "none", targets: [] };\n  bingoBeforeAction(b, u, action);\n  if (!u.alive) return { kind: "hit", targets: [u.uid] };\n  u.guard = false;'''
    if old not in s:
        raise SystemExit('doAction prehook anchor missing')
    s = s.replace(old, new, 1)

if 'BINGO FALSE BODY' not in s:
    old = '''function damage(b: Battle, src: Unit | null, target: Unit, raw: number, kind: "hit" | "crit", pierce = false): number {\n  let dmg = Math.max(1, Math.round(raw));'''
    new = '''function damage(b: Battle, src: Unit | null, target: Unit, raw: number, kind: "hit" | "crit", pierce = false): number {\n  const rt = b.bingoRuntime;\n  const bossTarget = !!rt && target.foe && target.uid === bingoBoss(b)?.uid;\n  if (bossTarget && src && !src.foe) {\n    if (rt.falseBodies > 0) {\n      if (src.doj >= Math.max(12, target.level * 0.70)) {\n        rt.falseBodies = 0;\n        log(b, `${src.name}'s dōjutsu exposes the real body — the remaining false bodies collapse.`, "info");\n      } else {\n        rt.falseBodies -= 1;\n        log(b, `BINGO FALSE BODY — ${src.name}'s attack destroys a decoy instead of the real target (${rt.falseBodies} remain).`, "miss");\n        return 0;\n      }\n    }\n    if (bingoHas(b, "half_hp_decoy") && !rt.halfHpDecoyUsed && target.hp / Math.max(1, target.maxHp) <= 0.50) {\n      rt.halfHpDecoyUsed = true;\n      target.extraTurnPending = true;\n      log(b, `${target.name} drops a half-health decoy; the hit is wasted and the target steals a free action.`, "miss");\n      return 0;\n    }\n    if (bingoHas(b, "rotating_resistance") && rt.currentAction === "jutsu" && src.nature && src.nature === rt.resistNature) {\n      raw *= 0.55;\n      log(b, `${target.name}'s rotating ${src.nature.toUpperCase()} resistance cuts the jutsu's force.`, "info");\n    }\n    if (bingoHas(b, "layered_armour") && rt.armourStacks > 0) {\n      raw *= 0.62;\n      rt.armourStacks -= 1;\n      log(b, `${target.name}'s layered armour absorbs the blow (${rt.armourStacks} layers remain).`, "info");\n    }\n  }\n  if (rt && src?.foe && !target.foe && rt.markedUid === target.uid && bingoHas(b, "marked_hunter")) raw *= 1.35;\n  let dmg = Math.max(1, Math.round(raw));'''
    if old not in s:
        raise SystemExit('damage mechanic anchor missing')
    s = s.replace(old, new, 1)

    old2 = '''  if (target.hp <= 0) {\n    target.alive = false;\n    log(b, `${target.name} is down!`, "down");\n  } else if (src && src.alive && src.uid !== target.uid && (target.retaliationRounds ?? 0) > 0 && (target.retaliationPct ?? 0) > 0) {'''
    new2 = '''  if (bossTarget && src && !src.foe) {\n    if (bingoHas(b, "chakra_conversion") && rt?.currentAction === "jutsu") {\n      const gain = Math.max(1, Math.round(dmg * 0.14));\n      target.cp = Math.min(target.maxCp, target.cp + gain);\n      if (rt) rt.convertedCharge += gain;\n      log(b, `${target.name} converts ${gain} points of the jutsu's force into chakra.`, "info");\n    }\n    if (kind === "crit") {\n      bingoInterruptCharge(b, "a heavy critical hit");\n      if (bingoHas(b, "initiative_theft") && target.alive) { target.extraTurnPending = true; log(b, `${target.name} steals initiative from the critical impact.`, "crit"); }\n    }\n    if (bingoHas(b, "counter_stance") && target.alive && src.alive && (rt?.currentAction === "attack" || rt?.currentAction === "technique" || rt?.currentAction === "gear")) {\n      target.counter = Math.max(target.counter, 0.28);\n      if (rt?.currentAction !== "attack" && dmg >= target.maxHp * 0.06) {\n        const back = Math.max(1, Math.round(dmg * 0.22));\n        src.hp = Math.max(0, src.hp - back);\n        log(b, `${target.name}'s counter stance punishes the close-range technique for ${back}.`, "crit");\n        if (src.hp <= 0) { src.alive = false; log(b, `${src.name} is down!`, "down"); }\n      }\n    }\n  }\n  if (target.hp <= 0) {\n    target.alive = false;\n    log(b, `${target.name} is down!`, "down");\n    if (!target.foe && bingoHas(b, "clone_on_down")) {\n      const boss = bingoBoss(b);\n      if (boss?.alive) { boss.extraTurnPending = true; log(b, `${boss.name} exploits the fallen hunter and creates a battlefield clone.`, "crit"); }\n    }\n  } else if (src && src.alive && src.uid !== target.uid && (target.retaliationRounds ?? 0) > 0 && (target.retaliationPct ?? 0) > 0) {'''
    if old2 not in s:
        raise SystemExit('damage reaction anchor missing')
    s = s.replace(old2, new2, 1)

if 'bingoHealBossOnMiss(b);' not in s:
    s = s.replace('''      if (tryDodge(t)) {\n        log(b, `${t.name} slips past ${u.name}'s strike`, "miss");\n        return { kind: "miss", targets: [t.uid] };\n      }''', '''      if (tryDodge(t)) {\n        log(b, `${t.name} slips past ${u.name}'s strike`, "miss");\n        if (t.foe) bingoHealBossOnMiss(b);\n        return { kind: "miss", targets: [t.uid] };\n      }''', 1)
    s = s.replace('''      log(b, `${t.name} shatters ${u.name}'s illusion`, "miss");\n      return { kind: "miss", targets: [t.uid] };''', '''      log(b, `${t.name} shatters ${u.name}'s illusion`, "miss");\n      if (t.foe) bingoHealBossOnMiss(b);\n      return { kind: "miss", targets: [t.uid] };''', 1)

if 'Bingo bleed weapon' not in s:
    old = '''      const d = damage(b, u, t, raw, crit ? "crit" : "hit");\n      log(b, `${u.name} strikes ${t.name} for ${d}${crit ? " — CRITICAL!" : ""}`, crit ? "crit" : "hit");\n      counterHit(b, u, t, d);'''
    new = '''      const d = damage(b, u, t, raw, crit ? "crit" : "hit");\n      log(b, `${u.name} strikes ${t.name} for ${d}${crit ? " — CRITICAL!" : ""}`, crit ? "crit" : "hit");\n      // Bingo bleed weapon\n      if (u.foe && bingoHas(b, "bleed_weapon") && t.alive) {\n        t.bleedRounds = Math.max(t.bleedRounds ?? 0, 3);\n        t.bleedDamage = Math.max(t.bleedDamage ?? 0, Math.max(1, Math.round(u.atk * 0.10)));\n        log(b, `${t.name} is left bleeding by ${u.name}'s weapon.`, "hit");\n      }\n      counterHit(b, u, t, d);'''
    if old not in s:
        raise SystemExit('attack bleed anchor missing')
    s = s.replace(old, new, 1)

if 'Bingo converted chakra release' not in s:
    old = '''      const d = damage(b, u, t, raw, "hit");\n      const other = foesSide.find((x) => x.uid !== t.uid);'''
    new = '''      let d = damage(b, u, t, raw, "hit");\n      // Bingo converted chakra release\n      if (u.foe && bingoHas(b, "chakra_conversion") && b.bingoRuntime && b.bingoRuntime.convertedCharge > 0 && t.alive) {\n        const extra = Math.min(Math.round(u.nin * 1.45), b.bingoRuntime.convertedCharge * 3);\n        if (extra > 0) { d += damage(b, u, t, extra, "crit", true); log(b, `${u.name} releases stored chakra through the jutsu.`, "crit"); }\n        b.bingoRuntime.convertedCharge = 0;\n      }\n      if (u.foe && bingoHas(b, "burning_ground")) {\n        for (const ally of aliveAllies(b)) {\n          ally.burnRounds = Math.max(ally.burnRounds ?? 0, 2);\n          ally.burnDamage = Math.max(ally.burnDamage ?? 0, Math.max(1, Math.round(u.nin * 0.10)));\n        }\n        log(b, `${u.name}'s fire leaves Burning Ground under the hunter cell for two rounds.`, "hit");\n      }\n      const other = foesSide.find((x) => x.uid !== t.uid);'''
    if old not in s:
        raise SystemExit('generic jutsu mechanic anchor missing')
    s = s.replace(old, new, 1)

if 'punishes the healing window' not in s:
    old = '''      t.hp = Math.min(t.maxHp, t.hp + amt);\n      b.flash = { uid: t.uid, amount: amt, kind: "heal", n: (b.flash?.n ?? 0) + 1 };\n      log(b, `${u.name} mends ${t.name} for ${amt}`, "heal");'''
    new = '''      t.hp = Math.min(t.maxHp, t.hp + amt);\n      b.flash = { uid: t.uid, amount: amt, kind: "heal", n: (b.flash?.n ?? 0) + 1 };\n      log(b, `${u.name} mends ${t.name} for ${amt}`, "heal");\n      if (!u.foe && bingoHas(b, "heal_punish") && (u.braceRounds ?? 0) <= 0 && (u.jutsuGuardRounds ?? 0) <= 0) {\n        const boss = bingoBoss(b);\n        if (boss?.alive) {\n          const pressure = damage(b, boss, u, boss.atk * 0.55 + boss.nin * 0.22, "crit", true);\n          log(b, `${boss.name} punishes the healing window with an immediate pressure attack for ${pressure}.`, "crit");\n        }\n      }'''
    if old not in s:
        raise SystemExit('heal punish anchor missing')
    s = s.replace(old, new, 1)

if 'bingoInterruptCharge(b, "genjutsu control")' not in s:
    old = '''        t.stun = sure ? 2 : 1;\n        const d = damage(b, u, t, u.gen * 0.55, "hit");'''
    new = '''        t.stun = sure ? 2 : 1;\n        if (t.foe) bingoInterruptCharge(b, "genjutsu control");\n        const d = damage(b, u, t, u.gen * 0.55, "hit");'''
    if old not in s:
        raise SystemExit('genjutsu interrupt anchor missing')
    s = s.replace(old, new, 1)

if 'if (bingoCheckEscape(b)) return;' not in s:
    old = '''export function nextTurn(b: Battle, towerLvl = 0): void {\n  if (aliveFoes(b).length === 0) {'''
    new = '''export function nextTurn(b: Battle, towerLvl = 0): void {\n  if (bingoCheckEscape(b)) return;\n  if (aliveFoes(b).length === 0) {'''
    if old not in s:
        raise SystemExit('nextTurn escape anchor missing')
    s = s.replace(old, new, 1)

if 'bingoRuntime?.sealMarks' not in s:
    old = '        u.cp = Math.min(u.maxCp, u.cp + 3 + u.regen);'
    new = '        const baseCpRegen = b.mode === "bingo" && !u.foe && (b.bingoRuntime?.sealMarks ?? 0) >= 3 ? 1 : 3;\n        u.cp = Math.min(u.maxCp, u.cp + baseCpRegen + u.regen);'
    if old not in s:
        raise SystemExit('chakra regen anchor missing')
    s = s.replace(old, new, 1)

if 'applyBingoRoundState(b);\n      rollOrder' not in s:
    old = '''      rollOrder(b, towerLvl);\n      log(b, `— Round ${b.round} —`, "info");'''
    new = '''      if ((b.bingoTargetCannotFleeRounds ?? 0) > 0) b.bingoTargetCannotFleeRounds = Math.max(0, (b.bingoTargetCannotFleeRounds ?? 0) - 1);\n      if (b.bingoRuntime && b.bingoRuntime.hazardRounds > 0) b.bingoRuntime.hazardRounds -= 1;\n      applyBingoRoundState(b);\n      if (bingoCheckEscape(b)) return;\n      rollOrder(b, towerLvl);\n      log(b, `— Round ${b.round} —`, "info");'''
    if old not in s:
        raise SystemExit('new round mechanics anchor missing')
    s = s.replace(old, new, 1)

write(p, s)
print('Bingo operational boss mechanics: applied')

p = 'src/components/BattleScreen.tsx'
s = read(p)
if 'BOSS MECHANICS ACTIVE' not in s:
    anchor = '<p className="text-[9.5px] font-bold tracking-[0.2em] text-paper/45">{isExam ? "PROMOTION DUEL" : "RAID ON THE VILLAGE"}</p>'
    if anchor in s:
        s = s.replace(anchor, '<p className="text-[9.5px] font-bold tracking-[0.2em] text-paper/45">{isExam ? "PROMOTION DUEL" : b.mode === "bingo" ? "BINGO TARGET CONTACT" : "RAID ON THE VILLAGE"}</p>{b.mode === "bingo" && <p className="mt-0.5 text-[7.5px] font-black tracking-wider text-gold">BOSS MECHANICS ACTIVE · {b.bingoRuntime?.mechanicIds.length ?? 0}</p>}', 1)
write(p, s)

p = 'public/sw.js'
s = read(p)
s = s.replace('const CACHE = "shadow-village-bingo-book-v5-detention-recruitment";', 'const CACHE = "shadow-village-bingo-book-v6-events-mechanics";')
write(p, s)
print('Bingo Book v6: 102 hunt events + operational boss mechanics complete')
