import type { GameState, Ninja, Skill } from "./types";

export type EquipmentRarity = "common" | "uncommon" | "rare" | "epic" | "legendary";
export type EquipmentKind = "stat" | "passive" | "technique";

export interface EquipmentAbility {
  id: string;
  name: string;
  kanji: string;
  power: number;
  stat: Skill;
  hits: number;
  note: string;
}

export interface EquipmentItem {
  id: string;
  name: string;
  rarity: EquipmentRarity;
  kind: EquipmentKind;
  icon: string;
  desc: string;
  skill?: Partial<Record<Skill, number>>;
  battle?: {
    hp?: number;
    cp?: number;
    atk?: number;
    def?: number;
    spd?: number;
    crit?: number;
    critMult?: number;
    dodge?: number;
    lifesteal?: number;
    counter?: number;
    regen?: number;
  };
  ability?: EquipmentAbility;
}

export interface EquipmentState {
  inventory: Record<string, number>;
  recent: string[];
  totalPulls: number;
}

type EquipmentCarrier = {
  equipmentSlots?: (string | null)[];
};

type EquipmentGameState = GameState & {
  equipment?: EquipmentState;
};

const SKILLS: Skill[] = ["nin", "tai", "gen", "ste", "med", "spd", "ken", "doj", "tac"];
const SKILL_LABEL: Record<Skill, string> = {
  nin: "NIN", tai: "TAI", gen: "GEN", ste: "STE", med: "MED", spd: "SPD", ken: "KEN", doj: "DŌJ", tac: "TAC",
};

export const RARITY_META: Record<EquipmentRarity, { name: string; color: string; weight: number; rank: number }> = {
  common: { name: "Common", color: "#a8adb8", weight: 55, rank: 1 },
  uncommon: { name: "Uncommon", color: "#63c58c", weight: 25, rank: 2 },
  rare: { name: "Rare", color: "#5aa7e8", weight: 12, rank: 3 },
  epic: { name: "Epic", color: "#b46ae0", weight: 6, rank: 4 },
  legendary: { name: "Legendary", color: "#f4c64f", weight: 2, rank: 5 },
};

export const GACHA_BASE_GOLD = 90;
export const GACHA_BASE_RICE = 45;
export const GACHA_PACKS = [
  { pulls: 1 as const, discount: 0, label: "1 PULL" },
  { pulls: 10 as const, discount: 0.10, label: "10 PULLS" },
  { pulls: 100 as const, discount: 0.20, label: "100 PULLS" },
];

const PREFIXES = [
  "Ash", "Bamboo", "Black", "Blazing", "Blood", "Blue", "Bone", "Bronze", "Cloud", "Crimson",
  "Dawn", "Dusk", "Ember", "Falling", "Fox", "Frost", "Ghost", "Golden", "Hidden", "Hollow",
  "Iron", "Jade", "Lightning", "Mist", "Moon", "Night", "Obsidian", "Pale", "Rain", "Red",
  "River", "Sand", "Scarlet", "Shadow", "Silent", "Silver", "Smoke", "Storm", "Sun", "White",
];
const BASES = ["Headband", "Kunai", "Vest", "Scroll", "Gloves"];
const ICONS = ["鉢", "苦", "衣", "巻", "手"];
const STAT_CYCLE: Skill[] = ["nin", "tai", "gen", "ste", "med", "spd", "ken", "doj", "tac"];

function rarityForIndex(i: number): EquipmentRarity {
  // Exactly 200 pieces: 80 common, 55 uncommon, 35 rare, 20 epic, 10 legendary.
  if (i < 80) return "common";
  if (i < 135) return "uncommon";
  if (i < 170) return "rare";
  if (i < 190) return "epic";
  return "legendary";
}

function strength(rarity: EquipmentRarity): number {
  return ({ common: 1, uncommon: 1.45, rare: 2.05, epic: 2.8, legendary: 3.7 } as const)[rarity];
}

function pct(n: number): string { return `${Math.round(n * 100)}%`; }

function makeItem(i: number): EquipmentItem {
  const rarity = rarityForIndex(i);
  const tier = strength(rarity);
  const prefix = PREFIXES[i % PREFIXES.length];
  const baseIndex = Math.floor(i / PREFIXES.length);
  const base = BASES[baseIndex];
  const icon = ICONS[baseIndex];
  const primary = STAT_CYCLE[i % STAT_CYCLE.length];
  const secondary = STAT_CYCLE[(i * 5 + 3) % STAT_CYCLE.length];
  const mode = i % 5;
  const id = `eq_${String(i + 1).padStart(3, "0")}`;
  const name = `${prefix} ${base}`;

  if (mode <= 1) {
    const primaryGain = Math.max(1, Math.round(1.4 * tier + (i % 3)));
    const secondaryGain = Math.max(1, Math.round(0.8 * tier));
    const skill: Partial<Record<Skill, number>> = { [primary]: primaryGain };
    if (secondary !== primary && rarity !== "common") skill[secondary] = secondaryGain;
    return {
      id, name, rarity, kind: "stat", icon,
      desc: `Equipped: +${primaryGain} ${SKILL_LABEL[primary]}${skill[secondary] ? ` and +${skill[secondary]} ${SKILL_LABEL[secondary]}` : ""}.`,
      skill,
    };
  }

  if (mode <= 3) {
    const shape = i % 8;
    const battle: NonNullable<EquipmentItem["battle"]> = {};
    let text = "";
    if (shape === 0) { battle.hp = 1 + 0.035 * tier; text = `Max HP +${pct(battle.hp - 1)}`; }
    if (shape === 1) { battle.atk = 1 + 0.025 * tier; text = `Battle ATK +${pct(battle.atk - 1)}`; }
    if (shape === 2) { battle.def = 1 + 0.028 * tier; text = `Battle DEF +${pct(battle.def - 1)}`; }
    if (shape === 3) { battle.cp = 1 + 0.04 * tier; text = `Max chakra +${pct(battle.cp - 1)}`; }
    if (shape === 4) { battle.crit = 0.012 * tier; text = `Crit chance +${Math.round(battle.crit * 100)}pp`; }
    if (shape === 5) { battle.dodge = 0.01 * tier; text = `Dodge chance +${Math.round(battle.dodge * 100)}pp`; }
    if (shape === 6) { battle.lifesteal = 0.014 * tier; text = `Heal for ${Math.round(battle.lifesteal * 100)}% of damage dealt`; }
    if (shape === 7) { battle.counter = 0.02 * tier; text = `Counter for ${Math.round(battle.counter * 100)}% of damage received`; }
    return { id, name, rarity, kind: "passive", icon, desc: `Equipped: ${text}.`, battle };
  }

  const abilityStat = STAT_CYCLE[(i * 7 + 2) % STAT_CYCLE.length];
  const hits = rarity === "legendary" && i % 2 === 0 ? 3 : rarity === "epic" || rarity === "legendary" ? 2 : 1;
  const totalPower = 0.92 + tier * 0.18;
  const power = totalPower / hits;
  const ability: EquipmentAbility = {
    id: `geartech_${String(i + 1).padStart(3, "0")}`,
    name: `${prefix} Art`,
    kanji: icon,
    power,
    stat: abilityStat,
    hits,
    note: `${name} releases a stored combat technique`,
  };
  return {
    id, name, rarity, kind: "technique", icon,
    desc: `Equipped: grants 奥義 ${ability.name} (${hits} hit${hits === 1 ? "" : "s"}, ${power.toFixed(2)}× ${SKILL_LABEL[abilityStat]} scaling) when no personal signature technique is equipped.`,
    battle: rarity === "legendary" ? { crit: 0.04, cp: 1.08 } : { cp: 1 + 0.018 * tier },
    ability,
  };
}

export const EQUIPMENT_CATALOG: EquipmentItem[] = Array.from({ length: 200 }, (_, i) => makeItem(i));
export const EQUIPMENT_BY_ID: Record<string, EquipmentItem> = Object.fromEntries(EQUIPMENT_CATALOG.map((x) => [x.id, x]));

export function ensureEquipmentState(s: GameState): EquipmentState {
  const st = s as EquipmentGameState;
  if (!st.equipment) st.equipment = { inventory: {}, recent: [], totalPulls: 0 };
  if (!st.equipment.inventory || typeof st.equipment.inventory !== "object") st.equipment.inventory = {};
  if (!Array.isArray(st.equipment.recent)) st.equipment.recent = [];
  if (typeof st.equipment.totalPulls !== "number") st.equipment.totalPulls = 0;
  return st.equipment;
}

export function equipmentSlots(n: Ninja): (string | null)[] {
  const carrier = n as Ninja & EquipmentCarrier;
  if (!Array.isArray(carrier.equipmentSlots)) carrier.equipmentSlots = [null, null, null, null];
  while (carrier.equipmentSlots.length < 4) carrier.equipmentSlots.push(null);
  if (carrier.equipmentSlots.length > 4) carrier.equipmentSlots = carrier.equipmentSlots.slice(0, 4);
  return carrier.equipmentSlots;
}

export function equippedCount(s: GameState, itemId: string): number {
  return s.ninjas.reduce((sum, n) => sum + equipmentSlots(n).filter((id) => id === itemId).length, 0);
}

export function availableCount(s: GameState, itemId: string): number {
  const inv = ensureEquipmentState(s).inventory[itemId] ?? 0;
  return Math.max(0, inv - equippedCount(s, itemId));
}

export function equipItem(s: GameState, n: Ninja, slot: number, itemId: string): boolean {
  if (slot < 0 || slot > 3 || !EQUIPMENT_BY_ID[itemId]) return false;
  const slots = equipmentSlots(n);
  if (slots[slot] === itemId) return true;
  if (availableCount(s, itemId) <= 0) return false;
  slots[slot] = itemId;
  return true;
}

export function unequipItem(n: Ninja, slot: number): void {
  if (slot < 0 || slot > 3) return;
  equipmentSlots(n)[slot] = null;
}

function rollRarity(): EquipmentRarity {
  let r = Math.random() * 100;
  for (const rarity of ["legendary", "epic", "rare", "uncommon", "common"] as EquipmentRarity[]) {
    const w = RARITY_META[rarity].weight;
    if (r < w) return rarity;
    r -= w;
  }
  return "common";
}

function randomOfRarity(rarity: EquipmentRarity): EquipmentItem {
  const pool = EQUIPMENT_CATALOG.filter((x) => x.rarity === rarity);
  return pool[Math.floor(Math.random() * pool.length)];
}

export function gachaCost(pulls: 1 | 10 | 100): { gold: number; rice: number; discount: number } {
  const pack = GACHA_PACKS.find((x) => x.pulls === pulls)!;
  const mult = 1 - pack.discount;
  return {
    gold: Math.round(GACHA_BASE_GOLD * pulls * mult),
    rice: Math.round(GACHA_BASE_RICE * pulls * mult),
    discount: pack.discount,
  };
}

export function pullEquipment(s: GameState, pulls: 1 | 10 | 100): { ok: boolean; error?: string; items: EquipmentItem[]; newIds: string[] } {
  const cost = gachaCost(pulls);
  if (s.ap < 1) return { ok: false, error: "No actions remaining today.", items: [], newIds: [] };
  if (s.gold < cost.gold) return { ok: false, error: `Need ${cost.gold.toLocaleString()} gold.`, items: [], newIds: [] };
  if (s.rice < cost.rice) return { ok: false, error: `Need ${cost.rice.toLocaleString()} rice.`, items: [], newIds: [] };

  const st = ensureEquipmentState(s);
  s.ap -= 1;
  s.gold -= cost.gold;
  s.rice -= cost.rice;
  const items: EquipmentItem[] = [];
  const newIds: string[] = [];
  for (let i = 0; i < pulls; i++) {
    const item = randomOfRarity(rollRarity());
    if (!st.inventory[item.id]) newIds.push(item.id);
    st.inventory[item.id] = (st.inventory[item.id] ?? 0) + 1;
    items.push(item);
  }
  st.totalPulls += pulls;
  st.recent = [...items.map((x) => x.id).reverse(), ...st.recent].slice(0, 100);
  return { ok: true, items, newIds };
}

export function ownedUniqueCount(s: GameState): number {
  const inv = ensureEquipmentState(s).inventory;
  return Object.keys(inv).filter((id) => (inv[id] ?? 0) > 0).length;
}

export function equipmentSkillBonus(n: Ninja, k: Skill): number {
  return equipmentSlots(n).reduce((sum, id) => sum + (id ? (EQUIPMENT_BY_ID[id]?.skill?.[k] ?? 0) : 0), 0);
}

export function equippedItems(n: Ninja): EquipmentItem[] {
  return equipmentSlots(n).map((id) => id ? EQUIPMENT_BY_ID[id] : null).filter((x): x is EquipmentItem => !!x);
}

export function equipmentSummary(n: Ninja): string[] {
  const items = equippedItems(n);
  if (!items.length) return ["No equipment bonuses active."];
  const out: string[] = [];
  for (const k of SKILLS) {
    const gain = items.reduce((sum, item) => sum + (item.skill?.[k] ?? 0), 0);
    if (gain) out.push(`+${gain} ${SKILL_LABEL[k]}`);
  }
  const hp = items.reduce((m, x) => m * (x.battle?.hp ?? 1), 1);
  const cp = items.reduce((m, x) => m * (x.battle?.cp ?? 1), 1);
  const atk = items.reduce((m, x) => m * (x.battle?.atk ?? 1), 1);
  const def = items.reduce((m, x) => m * (x.battle?.def ?? 1), 1);
  const crit = items.reduce((v, x) => v + (x.battle?.crit ?? 0), 0);
  const dodge = items.reduce((v, x) => v + (x.battle?.dodge ?? 0), 0);
  if (hp !== 1) out.push(`HP +${pct(hp - 1)}`);
  if (cp !== 1) out.push(`Chakra +${pct(cp - 1)}`);
  if (atk !== 1) out.push(`ATK +${pct(atk - 1)}`);
  if (def !== 1) out.push(`DEF +${pct(def - 1)}`);
  if (crit) out.push(`Crit +${Math.round(crit * 100)}pp`);
  if (dodge) out.push(`Dodge +${Math.round(dodge * 100)}pp`);
  const ability = items.find((x) => x.ability)?.ability;
  if (ability) out.push(`Gear technique: ${ability.name}`);
  return out.length ? out : ["Equipment passives active."];
}

export function applyEquipmentToBattleUnit(n: Ninja, u: any): any {
  const items = equippedItems(n);
  if (!items.length) return u;

  let hp = 1, cp = 1, atk = 1, def = 1, spd = 1;
  let crit = 0, critMult = 0, dodge = 0, lifesteal = 0, counter = 0, regen = 0;
  for (const item of items) {
    const b = item.battle;
    if (!b) continue;
    hp *= b.hp ?? 1; cp *= b.cp ?? 1; atk *= b.atk ?? 1; def *= b.def ?? 1; spd *= b.spd ?? 1;
    crit += b.crit ?? 0; critMult += b.critMult ?? 0; dodge += b.dodge ?? 0;
    lifesteal += b.lifesteal ?? 0; counter += b.counter ?? 0; regen += b.regen ?? 0;
  }

  if (typeof u.maxHp === "number") { u.maxHp = Math.max(1, Math.round(u.maxHp * hp)); u.hp = u.maxHp; }
  if (typeof u.maxCp === "number") { u.maxCp = Math.max(0, Math.round(u.maxCp * cp)); u.cp = u.maxCp; }
  if (typeof u.atk === "number") u.atk *= atk;
  if (typeof u.def === "number") u.def *= def;
  if (typeof u.spd === "number") u.spd *= spd;
  if (typeof u.crit === "number") u.crit = Math.min(0.85, u.crit + crit);
  if (typeof u.critMult === "number") u.critMult += critMult;
  if (typeof u.dodge === "number") u.dodge = Math.min(0.60, u.dodge + dodge);
  if (typeof u.lifesteal === "number") u.lifesteal += lifesteal;
  if (typeof u.counter === "number") u.counter += counter;
  if (typeof u.regen === "number") u.regen += regen;

  // Technique equipment plugs into the existing 奥義 action without replacing a ninja's personal signature technique.
  if (!u.special) {
    const ability = items.map((x) => x.ability).find((x): x is EquipmentAbility => !!x);
    if (ability) u.special = ability.id;
  }
  return u;
}

export function equipmentAbilityPerk(id: string): any | null {
  const item = EQUIPMENT_CATALOG.find((x) => x.ability?.id === id);
  const a = item?.ability;
  if (!item || !a) return null;
  return {
    id: a.id,
    name: a.name,
    kanji: a.kanji,
    branch: a.stat,
    kind: "signature",
    color: RARITY_META[item.rarity].color,
    desc: item.desc,
    fx: { special: true },
    tech: { name: a.name, power: a.power, stat: a.stat, hits: a.hits, note: a.note },
  };
}
