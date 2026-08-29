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
