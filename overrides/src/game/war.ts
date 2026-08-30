import type { Ev, GameState, Ninja, WarFactionId, WarOperationType, WarState, WarTerritory } from "./types";

export const WAR_OPERATIONS_PER_DAY = 3;

export const WAR_FACTIONS: Record<WarFactionId, { name: string; short: string }> = {
  shadow: { name: "Shadow Village", short: "SHD" },
  ember: { name: "Ember Coalition", short: "EMB" },
  mist: { name: "Mistwood", short: "MST" },
  stone: { name: "Stone Fang", short: "STN" },
  gold: { name: "Golden Banner", short: "GLD" },
  neutral: { name: "Independent", short: "—" },
};

export const WAR_LINKS: [string, string][] = [
  ["shadow_village", "ash_plain"],
  ["shadow_village", "cedar_road"],
  ["ash_plain", "red_valley"],
  ["ash_plain", "iron_ford"],
  ["cedar_road", "moon_forest"],
  ["cedar_road", "river_gate"],
  ["red_valley", "black_pass"],
  ["iron_ford", "black_pass"],
  ["iron_ford", "sun_fields"],
  ["moon_forest", "mist_marsh"],
  ["river_gate", "mist_marsh"],
  ["river_gate", "sun_fields"],
  ["black_pass", "stone_keep"],
  ["sun_fields", "golden_steppe"],
  ["mist_marsh", "reed_coast"],
  ["stone_keep", "golden_steppe"],
  ["golden_steppe", "reed_coast"],
];

const BASE_TERRITORIES: WarTerritory[] = [
  { id: "shadow_village", name: "Shadow Village", x: 11, y: 50, owner: "shadow", strength: 72, intel: 3, status: "stable" },
  { id: "ash_plain", name: "Ash Plain", x: 27, y: 30, owner: "neutral", strength: 34, intel: 1, status: "stable" },
  { id: "cedar_road", name: "Cedar Road", x: 27, y: 69, owner: "neutral", strength: 30, intel: 1, status: "stable" },
  { id: "red_valley", name: "Red Valley", x: 44, y: 15, owner: "ember", strength: 58, intel: 0, status: "stable" },
  { id: "iron_ford", name: "Iron Ford", x: 45, y: 42, owner: "neutral", strength: 40, intel: 1, status: "stable" },
  { id: "moon_forest", name: "Moon Forest", x: 45, y: 84, owner: "mist", strength: 54, intel: 0, status: "stable" },
  { id: "river_gate", name: "River Gate", x: 60, y: 66, owner: "neutral", strength: 42, intel: 1, status: "stable" },
  { id: "black_pass", name: "Black Pass", x: 62, y: 27, owner: "stone", strength: 62, intel: 0, status: "stable" },
  { id: "sun_fields", name: "Sun Fields", x: 73, y: 48, owner: "gold", strength: 56, intel: 0, status: "stable" },
  { id: "mist_marsh", name: "Mist Marsh", x: 72, y: 83, owner: "mist", strength: 60, intel: 0, status: "stable" },
  { id: "stone_keep", name: "Stone Keep", x: 84, y: 18, owner: "stone", strength: 78, intel: 0, status: "stable" },
  { id: "golden_steppe", name: "Golden Steppe", x: 91, y: 48, owner: "gold", strength: 72, intel: 0, status: "stable" },
  { id: "reed_coast", name: "Reed Coast", x: 91, y: 82, owner: "neutral", strength: 46, intel: 0, status: "stable" },
];

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const pick = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

export function createWarState(): WarState {
  return {
    unlocked: false,
    founderId: null,
    unlockedDay: null,
    turn: 0,
    operationsLeft: WAR_OPERATIONS_PER_DAY,
    territories: BASE_TERRITORIES.map((t) => ({ ...t })),
    history: [],
  };
}

export function normalizeWarState(s: GameState): void {
  if (!s.war || !Array.isArray(s.war.territories)) s.war = createWarState();
  if (!Array.isArray(s.war.history)) s.war.history = [];
  if (typeof s.war.operationsLeft !== "number") s.war.operationsLeft = WAR_OPERATIONS_PER_DAY;
  if (typeof s.war.turn !== "number") s.war.turn = 0;
  const kage = s.ninjas.find((n) => n.rank === "kage");
  if (kage && !s.war.unlocked) {
    s.war.unlocked = true;
    s.war.founderId = kage.id;
    s.war.unlockedDay = s.day;
    s.war.history.unshift(`${kage.name} ushered Shadow Village into the Kage Era.`);
  }
}

export function unlockWar(s: GameState, founder: Ninja): boolean {
  normalizeWarState(s);
  if (s.war.unlocked) return false;
  s.war.unlocked = true;
  s.war.founderId = founder.id;
  s.war.unlockedDay = s.day;
  s.war.operationsLeft = WAR_OPERATIONS_PER_DAY;
  s.war.history.unshift(`${founder.name} became the first Kage-level shinobi. The regional powers have begun to move.`);
  s.war.history = s.war.history.slice(0, 30);
  return true;
}

export function territoryById(s: GameState, id: string): WarTerritory | undefined {
  return s.war.territories.find((t) => t.id === id);
}

export function neighbours(id: string): string[] {
  const out: string[] = [];
  for (const [a, b] of WAR_LINKS) {
    if (a === id) out.push(b);
    if (b === id) out.push(a);
  }
  return out;
}

export function isShadowFrontier(s: GameState, territoryId: string): boolean {
  return neighbours(territoryId).some((id) => territoryById(s, id)?.owner === "shadow");
}

function teamFor(s: GameState, ids: number[]): Ninja[] {
  const unique = [...new Set(ids)].slice(0, 4);
  return unique
    .map((id) => s.ninjas.find((n) => n.id === id))
    .filter((n): n is Ninja => !!n && n.status === "ready");
}

function teamRating(team: Ninja[], op: WarOperationType): number {
  if (team.length === 0) return 0;
  const score = team.reduce((sum, n) => {
    if (op === "scout") return sum + n.s.ste * 1.35 + n.s.tac * 1.1 + n.s.spd * 0.55 + n.level;
    if (op === "raid") return sum + n.s.ste * 1.0 + n.s.nin * 0.85 + n.s.tac * 1.15 + n.s.spd * 0.35 + n.level;
    if (op === "fortify") return sum + n.s.tac * 1.45 + n.s.med * 0.45 + n.s.nin * 0.35 + n.level;
    return sum + n.s.tac * 1.05 + n.s.tai * 0.75 + n.s.ken * 0.65 + n.s.nin * 0.6 + n.level;
  }, 0);
  return score / Math.max(1, Math.sqrt(team.length));
}

export interface WarOperationResult {
  ok: boolean;
  success: boolean;
  message: string;
  captured?: boolean;
}

export function runWarOperation(s: GameState, territoryId: string, op: WarOperationType, ids: number[]): WarOperationResult {
  normalizeWarState(s);
  if (!s.war.unlocked) return { ok: false, success: false, message: "The War Map has not been unlocked." };
  if (s.war.operationsLeft <= 0) return { ok: false, success: false, message: "No strategic operations remain today." };
  const t = territoryById(s, territoryId);
  if (!t) return { ok: false, success: false, message: "Unknown territory." };
  const team = teamFor(s, ids);
  if (team.length === 0) return { ok: false, success: false, message: "Assign at least one ready shinobi." };
  if (op !== "scout" && op !== "fortify" && !isShadowFrontier(s, t.id)) {
    return { ok: false, success: false, message: "Only territories touching Shadow influence can be attacked." };
  }
  if (op === "fortify" && t.owner !== "shadow") return { ok: false, success: false, message: "Only Shadow territory can be fortified." };
  if (op === "assault" && t.owner === "shadow") return { ok: false, success: false, message: "That territory is already under Shadow control." };

  s.war.operationsLeft -= 1;
  const rating = teamRating(team, op);
  for (const n of team) n.fatigue = clamp(n.fatigue + (op === "assault" ? 12 : op === "raid" ? 9 : 6), 0, 100);

  let success = true;
  let captured = false;
  let message = "";

  if (op === "scout") {
    const gain = rating >= t.strength ? 3 : rating >= t.strength * 0.65 ? 2 : 1;
    t.intel = clamp(t.intel + gain, 0, 3);
    message = `${t.name}: intelligence improved to ${t.intel}/3.`;
  } else if (op === "fortify") {
    const gain = Math.max(4, Math.round(rating / 15));
    t.strength = clamp(t.strength + gain, 10, 99);
    t.status = "stable";
    message = `${t.name}: defences strengthened by ${gain}.`;
  } else {
    const chance = clamp(0.18 + rating / (rating + t.strength * (op === "assault" ? 2.4 : 1.8)), 0.18, 0.88);
    success = Math.random() < chance;
    if (op === "raid") {
      const loss = success ? Math.max(7, Math.round(rating / 11)) : Math.max(2, Math.round(rating / 28));
      t.strength = clamp(t.strength - loss, 8, 99);
      if (success) t.status = "contested";
      message = success ? `${t.name}: raid succeeded, enemy strength −${loss}.` : `${t.name}: raid repelled, but strength fell by ${loss}.`;
    } else {
      if (success) {
        const previous = t.owner;
        t.owner = "shadow";
        t.status = "occupied";
        t.intel = 3;
        t.strength = clamp(Math.round(24 + rating / 5), 28, 70);
        captured = true;
        message = `${t.name} captured from ${WAR_FACTIONS[previous].name}.`;
      } else {
        const loss = Math.max(3, Math.round(rating / 24));
        t.strength = clamp(t.strength - loss, 8, 99);
        t.status = "contested";
        message = `${t.name}: assault failed. Enemy strength −${loss}.`;
      }
    }
  }

  s.war.history.unshift(message);
  s.war.history = s.war.history.slice(0, 30);
  return { ok: true, success, message, captured };
}

function aiCandidates(s: GameState): WarTerritory[] {
  return s.war.territories.filter((t) => t.owner !== "shadow" && t.owner !== "neutral" && neighbours(t.id).some((id) => {
    const n = territoryById(s, id);
    return n && (n.owner === "shadow" || n.owner === "neutral");
  }));
}

export function advanceWarDay(s: GameState, ev: Ev[]): void {
  normalizeWarState(s);
  if (!s.war.unlocked) return;
  s.war.turn += 1;
  s.war.operationsLeft = WAR_OPERATIONS_PER_DAY;

  const candidates = aiCandidates(s);
  if (candidates.length === 0) return;
  const attacker = pick(candidates);
  const targets = neighbours(attacker.id)
    .map((id) => territoryById(s, id))
    .filter((t): t is WarTerritory => !!t && (t.owner === "shadow" || t.owner === "neutral"));
  if (targets.length === 0) return;
  const target = pick(targets);
  const pressure = attacker.strength + Math.random() * 28;

  if (target.owner === "neutral") {
    if (pressure > target.strength + 18) {
      target.owner = attacker.owner;
      target.status = "occupied";
      target.intel = 0;
      target.strength = clamp(Math.round((target.strength + attacker.strength) / 2), 30, 78);
      const msg = `${WAR_FACTIONS[attacker.owner].name} seized ${target.name}.`;
      s.war.history.unshift(msg);
      ev.push({ type: "war_alert", message: msg });
    }
  } else if (target.owner === "shadow") {
    const defence = target.strength + Math.random() * 34;
    if (pressure > defence) {
      if (target.id === "shadow_village") {
        target.status = "contested";
        target.strength = clamp(target.strength - 10, 30, 99);
        const msg = `${WAR_FACTIONS[attacker.owner].name} reached Shadow Village's outer defences. The capital held.`;
        s.war.history.unshift(msg);
        ev.push({ type: "war_alert", message: msg });
      } else {
        target.owner = attacker.owner;
        target.status = "occupied";
        target.intel = 1;
        target.strength = clamp(Math.round(attacker.strength * 0.72), 30, 78);
        const msg = `${WAR_FACTIONS[attacker.owner].name} broke through and took ${target.name}.`;
        s.war.history.unshift(msg);
        ev.push({ type: "war_alert", message: msg });
      }
    } else {
      target.strength = clamp(target.strength - 5, 10, 99);
      target.status = "contested";
      const msg = `${target.name} held against pressure from ${WAR_FACTIONS[attacker.owner].name}.`;
      s.war.history.unshift(msg);
      ev.push({ type: "war_alert", message: msg });
    }
  }
  s.war.history = s.war.history.slice(0, 30);
}
