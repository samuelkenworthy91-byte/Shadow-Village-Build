import type { GameState, Skill } from "./types";
import { HUNT_MIN_EVENT_HP_RATIO } from "./bingo";

export type HuntEventTone = "positive" | "negative" | "mixed";
export type HuntBiome = "forest" | "mountain" | "river" | "urban" | "desert" | "marsh" | "ruins" | "road" | "any";
export type HuntTag = "ambush" | "capture" | "injury" | "chakra" | "intel" | "escape" | "status" | "supplies" | "combat";

export interface HuntMemberState {
  ninjaId: number;
  hpRatio: number;
  chakraRatio: number;
  statuses: string[];
  delayedRounds: number;
}

export interface HuntRunState {
  id: string;
  targetId: string;
  seed: number;
  stage: number;
  intel: number;
  biome: HuntBiome;
  members: HuntMemberState[];
  captureBonus: number;
  targetHpRatio: number;
  targetChakraRatio: number;
  playerAmbushRounds: number;
  enemyAmbushRounds: number;
  targetCannotFleeRounds: number;
  eventIds: string[];
  notes: string[];
}

export interface HuntChoiceEffect {
  label: string;
  result: string;
  hpDelta?: number;
  chakraDelta?: number;
  captureBonus?: number;
  playerAmbushRounds?: number;
  enemyAmbushRounds?: number;
  targetHpDelta?: number;
  targetChakraDelta?: number;
  targetCannotFleeRounds?: number;
  addStatus?: string;
  delayedRounds?: number;
  intelDelta?: number;
}

export interface HuntSkillCheck {
  skill: Skill;
  difficulty: number;
  success: HuntChoiceEffect;
  failure: HuntChoiceEffect;
}

export interface HuntEventDef {
  id: string;
  title: string;
  blurb: string;
  tone: HuntEventTone;
  weight: number;
  biomes: HuntBiome[];
  tags: HuntTag[];
  minIntel?: number;
  maxIntel?: number;
  effect?: HuntChoiceEffect;
  choices?: HuntChoiceEffect[];
  check?: HuntSkillCheck;
}

function event(
  id: string,
  title: string,
  blurb: string,
  tone: HuntEventTone,
  biomes: HuntBiome[],
  tags: HuntTag[],
  extra: Partial<HuntEventDef> = {},
): HuntEventDef {
  return { id, title, blurb, tone, weight: 10, biomes, tags, ...extra };
}

/**
 * Initial authoring batch. The engine is deliberately data-driven so this can grow
 * to ~100 events without touching hunt resolution code.
 */
export const HUNT_EVENTS: HuntEventDef[] = [
  event("shortcut_informant", "An Informant's Shortcut", "A frightened local recognises the target and reveals a concealed approach through their perimeter.", "positive", ["urban", "road", "forest"], ["ambush", "intel"], {
    minIntel: 25,
    effect: { label: "Use the route", result: "Your squad reaches the target from an unexpected angle.", playerAmbushRounds: 1, intelDelta: 4 },
  }),
  event("collapsed_bridge", "Damaged Escape Route", "Heavy weather has destroyed the crossing the target planned to use if cornered.", "positive", ["river", "mountain", "road"], ["capture", "escape"], {
    effect: { label: "Exploit the terrain", result: "The target has fewer ways out.", captureBonus: 0.25, targetCannotFleeRounds: 3 },
  }),
  event("target_resting", "Perfect Opportunity", "A sensory sweep catches the target resting after a long movement cycle.", "positive", ["forest", "mountain", "ruins", "road"], ["chakra", "combat"], {
    minIntel: 55,
    effect: { label: "Strike now", result: "The target starts the confrontation with depleted chakra.", targetChakraDelta: -0.25 },
  }),
  event("wounded_target", "Fresh Blood on the Trail", "The target appears to have recently fought another pursuer. Drops of blood lead directly onward.", "positive", ["forest", "mountain", "marsh", "ruins"], ["combat", "intel"], {
    effect: { label: "Press the advantage", result: "The target enters battle already hurt.", targetHpDelta: -0.18, intelDelta: 3 },
  }),
  event("abandoned_cache", "Abandoned Supply Cache", "A hurried withdrawal left behind sealed water, ration pills and field dressings.", "positive", ["forest", "road", "ruins", "desert"], ["supplies", "chakra"], {
    effect: { label: "Resupply", result: "The team restores some reserves before continuing.", hpDelta: 0.12, chakraDelta: 0.15 },
  }),
  event("friendly_tracker", "Another Hunter's Notes", "A rival hunter abandoned the pursuit but left meticulous route markings behind.", "positive", ["any"], ["intel"], {
    effect: { label: "Study the notes", result: "The dossier becomes more precise.", intelDelta: 12 },
  }),
  event("quiet_camp", "Undisturbed Camp", "For once, the terrain offers a secure place to rest without losing the trail.", "positive", ["forest", "mountain", "desert", "road"], ["supplies"], {
    effect: { label: "Rest briefly", result: "The team recovers before the next stage.", hpDelta: 0.08, chakraDelta: 0.10 },
  }),
  event("captured_scout", "Isolated Scout", "One of the target's scouts strays too far from the main group and can be taken quietly.", "positive", ["forest", "mountain", "urban", "road"], ["capture", "intel"], {
    check: {
      skill: "ste",
      difficulty: 52,
      success: { label: "Silent capture", result: "The scout gives up the safest route into the hideout.", intelDelta: 10, captureBonus: 0.08 },
      failure: { label: "Scout escapes", result: "The scout gets a warning away before disappearing.", enemyAmbushRounds: 1 },
    },
  }),
  event("rockfall", "Rockfall", "Loose stone tears away from the slope and crashes through the formation.", "negative", ["mountain", "ruins"], ["injury"], {
    effect: { label: "Take cover", result: "One hunter takes a severe impact before the squad regroups.", hpDelta: -0.45 },
  }),
  event("poisoned_supplies", "Poisoned Supplies", "Someone reached the team's provisions before the hunt began.", "negative", ["any"], ["status", "supplies"], {
    maxIntel: 75,
    effect: { label: "Discard the supplies", result: "The poison has already taken hold.", addStatus: "poisoned", chakraDelta: -0.08 },
  }),
  event("counter_ambush", "Counter-Ambush", "The target has read the pursuit pattern and prepared a kill-zone around the next bend.", "negative", ["forest", "urban", "road", "ruins"], ["ambush", "combat"], {
    maxIntel: 70,
    effect: { label: "Break through", result: "The enemy gets the opening move.", enemyAmbushRounds: 1 },
  }),
  event("separated", "Separated", "A collapsing route splits one hunter from the formation just before contact.", "negative", ["mountain", "ruins", "marsh"], ["combat"], {
    effect: { label: "Regroup under pressure", result: "One random hunter joins the battle late.", delayedRounds: 1 },
  }),
  event("bad_ford", "Flooded Ford", "A sudden surge forces the squad through freezing water while the trail is still fresh.", "negative", ["river", "marsh"], ["injury", "chakra"], {
    effect: { label: "Cross now", result: "The crossing drains the team's reserves.", hpDelta: -0.12, chakraDelta: -0.18 },
  }),
  event("false_trail", "False Trail", "A deliberate trail of footprints leads the squad into useless ground before doubling back.", "negative", ["forest", "desert", "road"], ["intel", "escape"], {
    maxIntel: 60,
    effect: { label: "Recover the route", result: "The target gains time to prepare.", enemyAmbushRounds: 1 },
  }),
  event("wire_trap", "Hidden Wire Field", "Hair-thin wire is stretched through the approach at shin and throat height.", "negative", ["forest", "ruins", "urban"], ["injury", "ambush"], {
    check: {
      skill: "doj",
      difficulty: 48,
      success: { label: "Spot the glint", result: "The dōjutsu user identifies the trap before anyone enters it.", intelDelta: 2 },
      failure: { label: "Trigger the field", result: "The formation is cut apart and injured.", hpDelta: -0.30, enemyAmbushRounds: 1 },
    },
  }),
  event("snare_pit", "Covered Pit", "The undergrowth hides a deep reinforced snare meant for pursuing shinobi.", "negative", ["forest", "marsh"], ["injury"], {
    effect: { label: "Pull them free", result: "The trapped hunter is badly hurt but alive.", hpDelta: -0.50, delayedRounds: 1 },
  }),
  event("chakra_leech_mist", "Chakra-Leech Mist", "A thin chemical haze clings to the route and reacts violently with active chakra.", "negative", ["marsh", "urban", "ruins"], ["chakra", "status"], {
    effect: { label: "Push through", result: "The squad emerges with badly depleted chakra.", chakraDelta: -0.35 },
  }),
  event("wounded_messenger", "Wounded Messenger", "A courier lies beside the trail clutching papers bearing the target's seal.", "mixed", ["road", "urban", "forest"], ["intel", "supplies"], {
    choices: [
      { label: "Help the courier", result: "The courier survives and explains what they saw.", chakraDelta: -0.10, intelDelta: 18 },
      { label: "Take the documents", result: "The squad gets useful information without losing time.", intelDelta: 10 },
      { label: "Keep moving", result: "The trail matters more than the papers.", intelDelta: 0 },
    ],
  }),
  event("suspicious_shrine", "Suspicious Shrine", "An abandoned sealing shrine sits directly on the target's route. The formulae look recently disturbed.", "mixed", ["ruins", "forest", "mountain"], ["capture", "status"], {
    check: {
      skill: "tac",
      difficulty: 58,
      success: { label: "Read the pattern", result: "The squad adapts the seal into a temporary restraint array.", captureBonus: 0.30 },
      failure: { label: "Misread the seal", result: "The backlash interferes with chakra control.", chakraDelta: -0.22, addStatus: "sealed" },
    },
  }),
  event("burning_village", "Smoke Over the Hamlet", "The target passed through minutes earlier. Civilians are trapped in a burning storehouse while the trail remains hot.", "mixed", ["urban", "road"], ["intel", "escape"], {
    choices: [
      { label: "Rescue civilians", result: "The rescue costs time, but witnesses give a precise description.", intelDelta: 8, targetCannotFleeRounds: -1 },
      { label: "Stay on the target", result: "The squad keeps maximum pressure on the pursuit.", playerAmbushRounds: 1 },
    ],
  }),
  event("mercenary_offer", "Mercenary Offer", "A local tracker claims to know a hidden route and asks for immediate payment.", "mixed", ["urban", "road", "desert"], ["intel", "ambush"], {
    choices: [
      { label: "Trust the tracker", result: "The route is real and bypasses the outer sentries.", playerAmbushRounds: 1, intelDelta: 5 },
      { label: "Refuse", result: "The squad keeps to the verified route.", intelDelta: 0 },
    ],
  }),
  event("injured_enemy", "Wounded Associate", "An injured member of the target's organisation is trying to crawl away from the route.", "mixed", ["any"], ["capture", "intel"], {
    choices: [
      { label: "Interrogate", result: "The associate gives up a rendezvous point.", intelDelta: 14, chakraDelta: -0.05 },
      { label: "Bind and continue", result: "The prisoner cannot warn the target.", targetCannotFleeRounds: 1 },
      { label: "Ignore", result: "No time is lost.", intelDelta: 0 },
    ],
  }),
  event("storm_front", "Storm Front", "A violent storm rolls across the route, hiding movement but making every step hazardous.", "mixed", ["mountain", "river", "road"], ["ambush", "injury"], {
    choices: [
      { label: "Move inside the storm", result: "The weather masks the squad at the cost of injuries and exhaustion.", hpDelta: -0.15, chakraDelta: -0.10, playerAmbushRounds: 1 },
      { label: "Wait it out", result: "The squad stays intact, but the target has more time to prepare.", enemyAmbushRounds: 1 },
    ],
  }),
  event("tracks_split", "Tracks Split Three Ways", "The trail divides into three convincing routes at a dry riverbed.", "mixed", ["forest", "desert", "road"], ["intel", "escape"], {
    check: {
      skill: "tac",
      difficulty: 55,
      success: { label: "Read the deception", result: "The false routes are identified quickly.", intelDelta: 7, targetCannotFleeRounds: 1 },
      failure: { label: "Choose wrong", result: "The squad loses time and walks into prepared ground.", enemyAmbushRounds: 1 },
    },
  }),
  event("medical_emergency", "Old Wound Reopens", "The pace of the hunt tears open an older injury on one squad member.", "mixed", ["any"], ["injury"], {
    check: {
      skill: "med",
      difficulty: 50,
      success: { label: "Field treatment", result: "A medic stabilises the wound before it becomes serious.", hpDelta: -0.05 },
      failure: { label: "Push onward", result: "The wound worsens badly before contact.", hpDelta: -0.35 },
    },
  }),
  event("illusion_road", "Road That Isn't There", "The terrain ahead looks perfectly normal, but tiny inconsistencies suggest a layered illusion.", "mixed", ["forest", "urban", "ruins"], ["ambush", "intel"], {
    check: {
      skill: "gen",
      difficulty: 60,
      success: { label: "Break the illusion", result: "The false route collapses and exposes the real approach.", intelDelta: 8, playerAmbushRounds: 1 },
      failure: { label: "Enter the illusion", result: "The squad emerges disoriented and vulnerable.", chakraDelta: -0.15, enemyAmbushRounds: 1 },
    },
  }),
  event("blade_challenge", "Roadside Challenge", "A skilled subordinate blocks the route and demands single combat to buy their leader time.", "mixed", ["road", "urban", "mountain"], ["combat", "escape"], {
    check: {
      skill: "ken",
      difficulty: 62,
      success: { label: "Accept the duel", result: "A superior swordsman ends the challenge almost immediately.", hpDelta: -0.05, targetCannotFleeRounds: 1 },
      failure: { label: "Hard fight", result: "The duel is won, but the squad pays for it.", hpDelta: -0.25, chakraDelta: -0.12 },
    },
  }),
  event("unstable_cliff", "Unstable Cliff Path", "The shortest route crosses a crumbling ledge above a deep ravine.", "mixed", ["mountain"], ["injury", "ambush"], {
    choices: [
      { label: "Take the shortcut", result: "The squad gains ground but one hunter slips badly.", hpDelta: -0.28, playerAmbushRounds: 1 },
      { label: "Take the safe route", result: "No one is hurt, but the target has time to settle into position.", enemyAmbushRounds: 1 },
    ],
  }),
  event("river_boat", "Abandoned River Boat", "A half-hidden boat could cut hours from the pursuit if it survives the rapids.", "mixed", ["river"], ["ambush", "injury"], {
    choices: [
      { label: "Take the boat", result: "The crossing is brutal but places the squad ahead of the target.", hpDelta: -0.12, playerAmbushRounds: 1 },
      { label: "Follow the bank", result: "The safer route costs the element of surprise.", playerAmbushRounds: 0 },
    ],
  }),
  event("poison_flora", "Toxic Reed Bed", "The trail cuts through reeds that release a numbing powder when disturbed.", "mixed", ["marsh", "river"], ["status", "injury"], {
    check: {
      skill: "med",
      difficulty: 46,
      success: { label: "Prepare antidote", result: "The medic recognises the plant and neutralises the exposure.", intelDelta: 1 },
      failure: { label: "Cross quickly", result: "The powder weakens the team before combat.", hpDelta: -0.12, addStatus: "numbed" },
    },
  }),
  event("watchtower", "Abandoned Watchtower", "A ruined tower overlooks the entire route and could expose the target's movement.", "mixed", ["road", "forest", "desert"], ["intel", "ambush"], {
    check: {
      skill: "doj",
      difficulty: 54,
      success: { label: "Survey from above", result: "Enhanced vision finds the target's next movement before they arrive there.", intelDelta: 12, playerAmbushRounds: 1 },
      failure: { label: "Climb anyway", result: "The squad loses time without seeing anything useful.", intelDelta: 1 },
    },
  }),
  event("enemy_campfire", "Campfire Still Warm", "The squad finds a recently abandoned camp, including discarded wrappings and a rough route sketch.", "positive", ["forest", "mountain", "road", "desert"], ["intel", "capture"], {
    effect: { label: "Search the camp", result: "The discarded material reveals injuries and movement plans.", intelDelta: 9, captureBonus: 0.05 },
  }),
  event("friendly_patrol", "Friendly Border Patrol", "An allied patrol crossed paths with the target earlier in the day and can describe their direction.", "positive", ["road", "forest", "urban"], ["intel"], {
    effect: { label: "Compare notes", result: "The target's route narrows considerably.", intelDelta: 8 },
  }),
  event("broken_weapon", "Damaged Weapon", "A violent climb cracks a weapon fitting just before the next stage.", "negative", ["mountain", "ruins", "road"], ["combat"], {
    effect: { label: "Make a field repair", result: "The repair holds, but the delay leaves the squad poorly positioned.", enemyAmbushRounds: 1 },
  }),
  event("mudslide", "Mudslide", "The saturated hillside gives way beneath the formation.", "negative", ["marsh", "mountain", "forest"], ["injury"], {
    effect: { label: "Dig out", result: "The squad survives, but one hunter is left in terrible condition.", hpDelta: -0.60 },
  }),
  event("explosive_cache", "Concealed Explosive Cache", "A tripwire disappears into a buried cluster of tags beneath the trail.", "negative", ["forest", "urban", "ruins"], ["injury", "ambush"], {
    check: {
      skill: "tac",
      difficulty: 65,
      success: { label: "Disarm the pattern", result: "The squad dismantles the trap and learns how the target lays explosives.", intelDelta: 7 },
      failure: { label: "Detonation", result: "The blast leaves the formation badly injured but alive.", hpDelta: -0.55, enemyAmbushRounds: 1 },
    },
  }),
  event("target_argument", "Voices Through the Trees", "The target is arguing with an associate nearby and neither has noticed the hunters.", "positive", ["forest", "ruins", "road"], ["ambush", "capture"], {
    minIntel: 35,
    effect: { label: "Listen, then strike", result: "The squad learns the escape plan and opens from concealment.", playerAmbushRounds: 1, captureBonus: 0.10, targetCannotFleeRounds: 2 },
  }),
  event("old_battlefield", "Old Battlefield", "The route crosses ground littered with rusted weapons and half-buried explosive tags from an older war.", "mixed", ["road", "forest", "ruins"], ["injury", "capture"], {
    check: {
      skill: "tac",
      difficulty: 57,
      success: { label: "Turn the field against them", result: "The squad maps safe lanes and traps the obvious escape corridor.", captureBonus: 0.12, targetCannotFleeRounds: 1 },
      failure: { label: "Cross carefully", result: "An old tag still has enough charge to injure the squad.", hpDelta: -0.22 },
    },
  }),
];

function hashSeed(value: number): number {
  let x = value | 0;
  x ^= x << 13;
  x ^= x >>> 17;
  x ^= x << 5;
  return x >>> 0;
}

function seeded01(seed: number): number {
  return hashSeed(seed) / 0xffffffff;
}

function effectiveWeight(ev: HuntEventDef, intel: number): number {
  let w = ev.weight;
  // Better intelligence should meaningfully improve preparation without removing risk.
  if (intel >= 76) w *= ev.tone === "positive" ? 1.45 : ev.tone === "negative" ? 0.72 : 1.10;
  else if (intel >= 51) w *= ev.tone === "positive" ? 1.20 : ev.tone === "negative" ? 0.88 : 1.05;
  else if (intel <= 25) w *= ev.tone === "negative" ? 1.25 : ev.tone === "positive" ? 0.90 : 1;
  return Math.max(0.01, w);
}

export function rollHuntEvent(run: HuntRunState, salt = 0): HuntEventDef {
  const eligible = HUNT_EVENTS.filter((ev) =>
    (ev.biomes.includes("any") || ev.biomes.includes(run.biome)) &&
    (ev.minIntel == null || run.intel >= ev.minIntel) &&
    (ev.maxIntel == null || run.intel <= ev.maxIntel) &&
    !run.eventIds.includes(ev.id)
  );
  const pool = eligible.length ? eligible : HUNT_EVENTS.filter((ev) => ev.biomes.includes("any") || ev.biomes.includes(run.biome));
  const weights = pool.map((ev) => effectiveWeight(ev, run.intel));
  const total = weights.reduce((a, b) => a + b, 0);
  let r = seeded01(run.seed + run.stage * 104729 + salt * 7919) * total;
  for (let i = 0; i < pool.length; i++) {
    if (r < weights[i]) return pool[i];
    r -= weights[i];
  }
  return pool[pool.length - 1];
}

function pickMember(run: HuntRunState, salt: number): HuntMemberState | null {
  if (!run.members.length) return null;
  const index = Math.floor(seeded01(run.seed + run.stage * 31 + salt * 997) * run.members.length) % run.members.length;
  return run.members[index];
}

function clampMember(member: HuntMemberState): void {
  member.hpRatio = Math.max(HUNT_MIN_EVENT_HP_RATIO, Math.min(1, member.hpRatio));
  member.chakraRatio = Math.max(0, Math.min(1, member.chakraRatio));
  member.delayedRounds = Math.max(0, Math.round(member.delayedRounds));
}

export function applyHuntEffect(run: HuntRunState, effect: HuntChoiceEffect, salt = 0): void {
  if (effect.hpDelta) {
    const member = pickMember(run, salt + 1);
    if (member) member.hpRatio += effect.hpDelta;
  }
  if (effect.chakraDelta) {
    if (effect.chakraDelta > 0) {
      for (const member of run.members) member.chakraRatio += effect.chakraDelta;
    } else {
      const member = pickMember(run, salt + 2);
      if (member) member.chakraRatio += effect.chakraDelta;
    }
  }
  if (effect.addStatus) {
    const member = pickMember(run, salt + 3);
    if (member && !member.statuses.includes(effect.addStatus)) member.statuses.push(effect.addStatus);
  }
  if (effect.delayedRounds) {
    const member = pickMember(run, salt + 4);
    if (member) member.delayedRounds = Math.max(member.delayedRounds, effect.delayedRounds);
  }
  run.captureBonus += effect.captureBonus ?? 0;
  run.playerAmbushRounds += effect.playerAmbushRounds ?? 0;
  run.enemyAmbushRounds += effect.enemyAmbushRounds ?? 0;
  run.targetCannotFleeRounds += effect.targetCannotFleeRounds ?? 0;
  run.targetHpRatio = Math.max(0.10, Math.min(1, run.targetHpRatio + (effect.targetHpDelta ?? 0)));
  run.targetChakraRatio = Math.max(0.05, Math.min(1, run.targetChakraRatio + (effect.targetChakraDelta ?? 0)));
  run.intel = Math.max(0, Math.min(100, run.intel + (effect.intelDelta ?? 0)));
  for (const member of run.members) clampMember(member);
}

export function bestSquadSkill(s: GameState, run: HuntRunState, skill: Skill): number {
  const ids = new Set(run.members.map((m) => m.ninjaId));
  return s.ninjas.filter((n) => ids.has(n.id)).reduce((best, n) => Math.max(best, n.s[skill] ?? 0), 0);
}

export function resolveSkillCheck(s: GameState, run: HuntRunState, ev: HuntEventDef, salt = 0): { success: boolean; effect: HuntChoiceEffect } | null {
  if (!ev.check) return null;
  const skill = bestSquadSkill(s, run, ev.check.skill);
  // A high specialist stat is meaningful, but there is always some uncertainty.
  const chance = Math.max(0.08, Math.min(0.92, 0.50 + (skill - ev.check.difficulty) * 0.025 + (run.intel - 50) * 0.002));
  const success = seeded01(run.seed + run.stage * 1543 + salt * 3571) < chance;
  return { success, effect: success ? ev.check.success : ev.check.failure };
}

export function createHuntRun(targetId: string, ninjaIds: number[], intel: number, biome: HuntBiome, seed = Date.now()): HuntRunState {
  return {
    id: `hunt_${targetId}_${seed}`,
    targetId,
    seed,
    stage: 0,
    intel: Math.max(0, Math.min(100, intel)),
    biome,
    members: ninjaIds.slice(0, 3).map((ninjaId) => ({ ninjaId, hpRatio: 1, chakraRatio: 1, statuses: [], delayedRounds: 0 })),
    captureBonus: 0,
    targetHpRatio: 1,
    targetChakraRatio: 1,
    playerAmbushRounds: 0,
    enemyAmbushRounds: 0,
    targetCannotFleeRounds: 0,
    eventIds: [],
    notes: [],
  };
}
