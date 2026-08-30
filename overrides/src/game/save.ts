import type { GameState } from "./types";

const SAVE_VERSION = 1;
export const SAVE_SLOT_COUNT = 3;

interface StoredSave {
  version: number;
  savedAt: number;
  state: GameState;
}

export interface SaveSlotSummary {
  slot: number;
  exists: boolean;
  savedAt: number | null;
  day: number | null;
  ninjas: number | null;
  gold: number | null;
  clan: string | null;
  raids: number | null;
}

const keyFor = (slot: number) => `shadow-village-save-v${SAVE_VERSION}-slot-${slot}`;
const backupKeyFor = (slot: number) => `${keyFor(slot)}-backup`;

function storageReady(): boolean {
  return typeof localStorage !== "undefined";
}

function validSlot(slot: number): boolean {
  return Number.isInteger(slot) && slot >= 1 && slot <= SAVE_SLOT_COUNT;
}

function parseStored(raw: string | null): StoredSave | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<StoredSave>;
    if (!parsed || typeof parsed !== "object" || !parsed.state || typeof parsed.state !== "object") return null;
    const state = parsed.state as GameState;
    if (!Array.isArray(state.ninjas) || !Array.isArray(state.missions) || typeof state.day !== "number") return null;

    // Lightweight migration/normalisation for saves made before later systems existed.
    for (const ninja of state.ninjas) {
      if (typeof ninja.examFails !== "number") ninja.examFails = 0;
    }
    if (!state.stats) state.stats = { done: 0, failed: 0, raids: 0, earned: 0, levels: 0, promos: 0 };
    if (!state.battle) state.battle = null;
    if (!state.scout) state.scout = null;
    if (!Array.isArray(state.log)) state.log = [];
    if (!Array.isArray(state.reports)) state.reports = [];
    if (state.phase === "menu") state.phase = "playing";

    return {
      version: typeof parsed.version === "number" ? parsed.version : SAVE_VERSION,
      savedAt: typeof parsed.savedAt === "number" ? parsed.savedAt : Date.now(),
      state,
    };
  } catch {
    return null;
  }
}

export function saveSlot(slot: number, state: GameState): void {
  if (!storageReady() || !validSlot(slot)) return;
  try {
    const key = keyFor(slot);
    const current = localStorage.getItem(key);
    if (current) localStorage.setItem(backupKeyFor(slot), current);
    const payload: StoredSave = { version: SAVE_VERSION, savedAt: Date.now(), state };
    localStorage.setItem(key, JSON.stringify(payload));
  } catch {
    // Storage quota/private-mode failures should never break the running game.
  }
}

export function loadSlot(slot: number): GameState | null {
  if (!storageReady() || !validSlot(slot)) return null;
  ensureWarTestSlot();
  const primary = parseStored(localStorage.getItem(keyFor(slot)));
  if (primary) return primary.state;
  const backup = parseStored(localStorage.getItem(backupKeyFor(slot)));
  return backup?.state ?? null;
}

export function deleteSlot(slot: number): void {
  if (!storageReady() || !validSlot(slot)) return;
  localStorage.removeItem(keyFor(slot));
  localStorage.removeItem(backupKeyFor(slot));
}

export function listSaveSlots(): SaveSlotSummary[] {
  ensureWarTestSlot();
  return Array.from({ length: SAVE_SLOT_COUNT }, (_, i) => {
    const slot = i + 1;
    const stored = storageReady()
      ? parseStored(localStorage.getItem(keyFor(slot))) ?? parseStored(localStorage.getItem(backupKeyFor(slot)))
      : null;
    if (!stored) {
      return { slot, exists: false, savedAt: null, day: null, ninjas: null, gold: null, clan: null, raids: null };
    }
    const st = stored.state;
    return {
      slot,
      exists: true,
      savedAt: stored.savedAt,
      day: st.day,
      ninjas: st.ninjas.length,
      gold: st.gold,
      clan: st.clan,
      raids: st.raids,
    };
  });
}

function makeWarTestNinja(id: number, name: string, rank: string, level: number, base: number, tac: number, ken: number, lookShift: number) {
  const s = { nin: base + 4, tai: base, gen: base - 6, ste: base + 2, med: Math.max(18, base - 18), spd: base + 3, ken, doj: 0, tac };
  const growth = { nin: 1.28, tai: 1.24, gen: 1.12, ste: 1.26, med: 1.0, spd: 1.3, ken: 1.3, doj: 0, tac: 1.34 };
  return {
    id, name, seed: id / 1000,
    look: { hair: lookShift % 8, hairColor: (lookShift + 3) % 10, skin: lookShift % 5, eyes: lookShift % 6, mark: lookShift % 5, outfit: lookShift % 7, band: lookShift % 6, acc: lookShift % 4, build: lookShift % 3 },
    nature: lookShift % 2 ? "wind" : "fire", secondaryNature: null, traits: ["tactician"],
    rank, level, xp: 0, sp: 6, pot: rank === "kage" ? 5 : 4, s, growth,
    fatigue: 0, status: "ready", daysLeft: 0, missionId: null, runs: 38, wins: 34,
    dojutsuAwakening: null, perks: [], legend: null, title: rank === "kage" ? "First Shadow" : null, examFails: 0,
  };
}

function makeWarTestState(): GameState {
  return {
    phase: "playing", day: 22, ap: 4, gold: 1600, rice: 900, score: 2850, streak: 3,
    hp: 8, hpMax: 8, threat: 18, hungry: false,
    ninjas: [
      makeWarTestNinja(100, "Ren Kurogane", "kage", 24, 68, 82, 76, 3),
      makeWarTestNinja(101, "Mika Sazanami", "anbu", 19, 55, 64, 48, 6),
      makeWarTestNinja(102, "Daichi Arata", "jonin", 17, 50, 58, 63, 2),
    ],
    missions: [], b: { hall: 3, farm: 3, tea: 2, dojo: 3, tower: 2, shrine: 2 }, techs: [],
    nextId: 200, raids: 4, clan: "Iron Cicada",
    stats: { done: 41, failed: 4, raids: 4, earned: 6200, levels: 67, promos: 17 },
    battle: null, scout: null,
    log: [{ txt: "TEST SAVE — Kage Era ready for War Map testing.", kind: "great", id: 1 }],
    reports: [],
  } as unknown as GameState;
}

function ensureWarTestSlot(): void {
  if (!storageReady()) return;
  try {
    const slot = 3;
    const existing = localStorage.getItem(keyFor(slot)) || localStorage.getItem(backupKeyFor(slot));
    if (!existing) saveSlot(slot, makeWarTestState());
  } catch {
    // QA seed is optional; never block the title screen if storage is unavailable.
  }
}
