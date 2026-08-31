import type { GameState, Ninja, Skill } from "./types";
import { equipmentSlots } from "./equipment";

export const EXILE_MISSING_NIN_CHANCE = 0.03;
export const EXILE_REVEAL_MIN_DAYS = 10;
export const EXILE_REVEAL_MAX_DAYS = 30;
export const HUNT_MIN_EVENT_HP_RATIO = 0.10;
export const BINGO_ACTIVE_PARTY_SIZE = 3;

export type BingoThreat = "B" | "A" | "S" | "S+" | "SS" | "BLACK";
export type BingoTargetStatus =
  | "unknown"
  | "rumoured"
  | "identified"
  | "located"
  | "active_hunt"
  | "escaped"
  | "captured"
  | "killed"
  | "recruited"
  | "resolved";

export type BingoOutcome = "captured" | "killed" | "recruited" | "transferred" | "released" | "executed";

export interface BingoIntelReveal {
  at: number;
  label: string;
  detail: string;
}

export interface BingoTargetDef {
  id: string;
  name: string;
  epithet: string;
  sprite: string;
  threat: BingoThreat;
  level: number;
  potential: 1 | 2 | 3 | 4 | 5;
  elements: string[];
  focus: Skill[];
  organisationId?: string;
  recruitable?: boolean;
  bossMechanics: string[];
  summary: string;
  knownCrimes: string[];
  bountyDead: number;
  bountyAlive: number;
  captureBaseChance: number;
  fleeAtHp?: number;
  intel: BingoIntelReveal[];
}

export interface BingoTargetProgress {
  intel: number;
  status: BingoTargetStatus;
  attempts: number;
  locationKnown: boolean;
  lastKnownRegion?: string;
  outcome?: BingoOutcome;
  rewardsClaimed?: boolean;
}

export interface BingoOrganisationDef {
  id: string;
  name: string;
  description: string;
  members: number;
}

export interface PendingExileMissingNin {
  id: string;
  revealDay: number;
  ninja: Ninja;
}

export interface DynamicMissingNin {
  id: string;
  sourceNinjaId: number;
  name: string;
  epithet: string;
  threat: BingoThreat;
  revealDay: number;
  ninja: Ninja;
  intel: number;
  status: BingoTargetStatus;
  bountyDead: number;
  bountyAlive: number;
  attempts: number;
}

export interface DetentionState {
  level: number;
  prisonerIds: string[];
  securityAlert: number;
}

export interface BingoState {
  unlocked: boolean;
  unlockedDay: number | null;
  targets: Record<string, BingoTargetProgress>;
  pendingExiles: PendingExileMissingNin[];
  dynamicTargets: DynamicMissingNin[];
  organisationsKnown: string[];
  blackBookUnlocked: boolean;
  finalTargetUnlocked: boolean;
  detention: DetentionState;
}

type BingoGameState = GameState & { bingo?: BingoState };

export const BINGO_ORGANISATIONS: BingoOrganisationDef[] = [
  { id: "seven_graves", name: "The Seven Graves", members: 7, description: "Veteran missing-nin who sell battlefield expertise to the highest bidder." },
  { id: "black_lotus", name: "Black Lotus", members: 6, description: "An assassination and intelligence network built around infiltration and poison." },
  { id: "hollow_moon", name: "Hollow Moon", members: 8, description: "Forbidden-technique users bound together by bloodline research and ritual seals." },
  { id: "iron_covenant", name: "Iron Covenant", members: 5, description: "Heavy assault shinobi, former bodyguards and execution specialists." },
  { id: "wandering_court", name: "The Wandering Court", members: 6, description: "Elite rogues who reject the authority of every hidden village." },
];

const INTEL_STANDARD: BingoIntelReveal[] = [
  { at: 0, label: "Rumour", detail: "Alias, approximate danger and a broad region are known." },
  { at: 20, label: "Identity", detail: "Appearance, primary element and approximate level become known." },
  { at: 40, label: "Associates", detail: "Secondary nature, selected traits and known contacts become visible." },
  { at: 60, label: "Combat File", detail: "Signature techniques, likely hideout and escape behaviour are revealed." },
  { at: 80, label: "Full Dossier", detail: "Most combat information, equipment and weaknesses are exposed." },
  { at: 100, label: "Complete Intelligence", detail: "The target file is considered complete. Hunt-event preparation is maximised." },
];

export const BINGO_TARGETS: BingoTargetDef[] = [
  {
    id: "bb_001",
    name: "Kaito",
    epithet: "The Ash Hound",
    sprite: "/bingo/bingo_001.png",
    threat: "A",
    level: 31,
    potential: 4,
    elements: ["Fire", "Wind"],
    focus: ["nin", "spd", "tac"],
    organisationId: "seven_graves",
    bossMechanics: ["Fire techniques leave Burning Ground for two rounds."],
    summary: "A relentless pursuit specialist who burns escape routes behind him and forces opponents through prepared kill-zones.",
    knownCrimes: ["Three convoy attacks", "Murder of two hunter-nin", "Destruction of a border watch post"],
    bountyDead: 32000,
    bountyAlive: 44000,
    captureBaseChance: 0.45,
    intel: INTEL_STANDARD,
  },
  {
    id: "bb_002",
    name: "Mizue",
    epithet: "The White Widow",
    sprite: "/bingo/bingo_002.png",
    threat: "S",
    level: 42,
    potential: 5,
    elements: ["Water", "Ice"],
    focus: ["gen", "ste", "doj"],
    organisationId: "black_lotus",
    recruitable: true,
    bossMechanics: ["Begins with four false bodies; sensory and dōjutsu checks can expose the real target early."],
    summary: "An assassin who weaponises mist, mirrors and false bodies. Most pursuit teams never know which figure struck the killing blow.",
    knownCrimes: ["Assassination of a provincial adviser", "Poisoning of a pursuit cell", "The Frost Road disappearances"],
    bountyDead: 76000,
    bountyAlive: 105000,
    captureBaseChance: 0.32,
    intel: INTEL_STANDARD,
  },
  {
    id: "bb_003",
    name: "Renji",
    epithet: "The Red Cicada",
    sprite: "/bingo/bingo_003.png",
    threat: "S+",
    level: 51,
    potential: 5,
    elements: ["Lightning", "Wind"],
    focus: ["spd", "ken", "ste"],
    organisationId: "wandering_court",
    bossMechanics: ["Attempts to flee below 25% HP unless restrained, sealed or prevented by a hunt modifier."],
    summary: "A famous duelist whose reputation is built as much on impossible escapes as on victories. He never remains where a hunter expects.",
    knownCrimes: ["Killing of an elite swordsman cell", "Theft of restricted lightning scrolls", "Repeated evasion of Kage-sanctioned hunts"],
    bountyDead: 128000,
    bountyAlive: 165000,
    captureBaseChance: 0.24,
    fleeAtHp: 0.25,
    intel: INTEL_STANDARD,
  },
];

export const BINGO_TARGET_BY_ID: Record<string, BingoTargetDef> = Object.fromEntries(BINGO_TARGETS.map((x) => [x.id, x]));

function blankProgress(): BingoTargetProgress {
  return { intel: 0, status: "unknown", attempts: 0, locationKnown: false };
}

export function ensureBingoState(s: GameState): BingoState {
  const state = s as BingoGameState;
  if (!state.bingo) {
    state.bingo = {
      unlocked: false,
      unlockedDay: null,
      targets: {},
      pendingExiles: [],
      dynamicTargets: [],
      organisationsKnown: [],
      blackBookUnlocked: false,
      finalTargetUnlocked: false,
      detention: { level: 0, prisonerIds: [], securityAlert: 0 },
    };
  }
  const b = state.bingo;
  if (!b.targets || typeof b.targets !== "object") b.targets = {};
  if (!Array.isArray(b.pendingExiles)) b.pendingExiles = [];
  if (!Array.isArray(b.dynamicTargets)) b.dynamicTargets = [];
  if (!Array.isArray(b.organisationsKnown)) b.organisationsKnown = [];
  if (!b.detention) b.detention = { level: 0, prisonerIds: [], securityAlert: 0 };
  for (const target of BINGO_TARGETS) if (!b.targets[target.id]) b.targets[target.id] = blankProgress();

  if (!b.unlocked && s.ninjas.some((n) => n.rank === "kage")) {
    b.unlocked = true;
    b.unlockedDay = s.day;
    b.targets.bb_001 = { ...b.targets.bb_001, intel: Math.max(20, b.targets.bb_001.intel), status: "identified" };
    b.targets.bb_002 = { ...b.targets.bb_002, intel: Math.max(10, b.targets.bb_002.intel), status: "rumoured" };
    b.targets.bb_003 = { ...b.targets.bb_003, intel: Math.max(5, b.targets.bb_003.intel), status: "rumoured" };
    s.log.push({ txt: "The village has produced a Kage-class shinobi. The Bingo Book is now available.", kind: "great", id: Date.now() });
  }
  return b;
}

export function bingoUnlocked(s: GameState): boolean {
  return ensureBingoState(s).unlocked;
}

export function intelBand(intel: number): "rumour" | "identity" | "associates" | "combat" | "dossier" | "complete" {
  if (intel >= 100) return "complete";
  if (intel >= 80) return "dossier";
  if (intel >= 60) return "combat";
  if (intel >= 40) return "associates";
  if (intel >= 20) return "identity";
  return "rumour";
}

export function addBingoIntel(s: GameState, targetId: string, amount: number): BingoTargetProgress | null {
  const b = ensureBingoState(s);
  const progress = b.targets[targetId];
  if (!progress || progress.status === "killed" || progress.status === "captured" || progress.status === "resolved") return null;
  progress.intel = Math.max(0, Math.min(100, progress.intel + Math.max(0, amount)));
  if (progress.intel >= 60 && progress.status !== "located" && progress.status !== "active_hunt" && progress.status !== "escaped") {
    progress.status = "located";
    progress.locationKnown = true;
  } else if (progress.intel >= 20 && (progress.status === "unknown" || progress.status === "rumoured")) {
    progress.status = "identified";
  } else if (progress.intel > 0 && progress.status === "unknown") {
    progress.status = "rumoured";
  }
  return progress;
}

function rankThreat(n: Ninja): BingoThreat {
  if (n.rank === "kage") return "SS";
  if (n.rank === "jonin") return n.pot >= 5 ? "S+" : "S";
  if (n.rank === "chunin") return n.pot >= 4 ? "A" : "B";
  return "B";
}

function cloneForMissingNin(n: Ninja): Ninja {
  const copy = {
    ...n,
    s: { ...n.s },
    growth: { ...n.growth },
    traits: [...n.traits],
    perks: [...n.perks],
    jutsuKnown: [...(n.jutsuKnown ?? [])],
    jutsuEquipped: [...(n.jutsuEquipped ?? [])],
  } as Ninja;
  (copy as Ninja & { equipmentSlots?: (string | null)[] }).equipmentSlots = [null, null, null, null];

  const rankBoost = n.rank === "kage" ? 0.13 : n.rank === "jonin" ? 0.11 : n.rank === "chunin" ? 0.08 : 0.06;
  const potentialBoost = Math.max(0, n.pot - 3) * 0.01;
  const mult = Math.min(1.15, 1 + rankBoost + potentialBoost);
  const skills = Object.keys(copy.s) as Skill[];
  const ordered = [...skills].sort((a, b) => copy.s[b] - copy.s[a]);
  for (const skill of skills) copy.s[skill] = Math.max(1, Math.round(copy.s[skill] * mult));
  for (const skill of ordered.slice(0, 3)) copy.s[skill] += 2;
  copy.level += n.rank === "kage" ? 3 : n.rank === "jonin" ? 2 : 1;
  copy.sp += 2;
  copy.status = "ready";
  copy.fatigue = 0;
  copy.title = "Missing-nin";
  return copy;
}

function bountyFor(n: Ninja): { dead: number; alive: number } {
  const rankBase = n.rank === "kage" ? 180000 : n.rank === "jonin" ? 90000 : n.rank === "chunin" ? 42000 : 18000;
  const skillPower = Object.values(n.s).reduce((a, b) => a + b, 0);
  const dead = Math.round((rankBase + skillPower * 160 + n.level * 500) / 1000) * 1000;
  return { dead, alive: Math.round(dead * 1.3 / 1000) * 1000 };
}

export function exileNinja(s: GameState, ninjaId: number): { ok: boolean; error?: string } {
  const n = s.ninjas.find((x) => x.id === ninjaId);
  if (!n) return { ok: false, error: "Ninja not found." };
  if (n.status !== "ready") return { ok: false, error: "Only a ready ninja can be exiled." };
  if (s.battle?.units?.some((u) => u.ninjaId === ninjaId)) return { ok: false, error: "That ninja is currently in battle." };

  const b = ensureBingoState(s);
  const missingRoll = Math.random() < EXILE_MISSING_NIN_CHANCE;
  if (missingRoll) {
    const revealDay = s.day + EXILE_REVEAL_MIN_DAYS + Math.floor(Math.random() * (EXILE_REVEAL_MAX_DAYS - EXILE_REVEAL_MIN_DAYS + 1));
    b.pendingExiles.push({ id: `exile_${n.id}_${Date.now()}`, revealDay, ninja: cloneForMissingNin(n) });
  }

  // Inventory stores ownership totals. Clearing slots immediately returns all four pieces to availability.
  const slots = equipmentSlots(n);
  for (let i = 0; i < slots.length; i++) slots[i] = null;
  s.ninjas = s.ninjas.filter((x) => x.id !== ninjaId);
  s.log.push({ txt: `${n.name} was exiled from Shadow Village.`, kind: "info", id: Date.now() });
  return { ok: true };
}

export function refreshPendingMissingNin(s: GameState): string[] {
  const b = ensureBingoState(s);
  const ready = b.pendingExiles.filter((x) => x.revealDay <= s.day);
  if (!ready.length) return [];
  const revealed: string[] = [];
  for (const pending of ready) {
    if (b.dynamicTargets.some((x) => x.id === pending.id)) continue;
    const threat = rankThreat(pending.ninja);
    const bounty = bountyFor(pending.ninja);
    const epithetPool = ["The Turncoat", "Village Ghost", "Broken Oath", "The Stray Blade", "The Unbound"];
    const epithet = epithetPool[Math.abs(pending.ninja.id) % epithetPool.length];
    b.dynamicTargets.push({
      id: pending.id,
      sourceNinjaId: pending.ninja.id,
      name: pending.ninja.name,
      epithet,
      threat,
      revealDay: pending.revealDay,
      ninja: pending.ninja,
      intel: 20,
      status: "identified",
      bountyDead: bounty.dead,
      bountyAlive: bounty.alive,
      attempts: 0,
    });
    revealed.push(pending.ninja.name);
    s.log.push({ txt: `Bingo Book update: reports identify former Shadow Village shinobi ${pending.ninja.name} as a missing-nin.`, kind: "bad", id: Date.now() + revealed.length });
  }
  const readyIds = new Set(ready.map((x) => x.id));
  b.pendingExiles = b.pendingExiles.filter((x) => !readyIds.has(x.id));
  return revealed;
}

export function captureChance(target: BingoTargetDef, intel: number, sealingBonus = 0, huntBonus = 0): number {
  const intelBonus = Math.max(0, Math.min(0.20, intel / 500));
  return Math.max(0.05, Math.min(0.95, target.captureBaseChance + intelBonus + sealingBonus + huntBonus));
}
