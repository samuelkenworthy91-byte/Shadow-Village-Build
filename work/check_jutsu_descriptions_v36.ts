import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createState } from '../app/src/game/engine';
import { JUTSU, JUTSU_BY_ID, jutsuCostForNinja } from '../app/src/game/jutsu';
import { jutsuFlavour } from '../app/src/game/jutsuFlavour';
import { describeJutsu } from '../app/src/game/jutsuDescription';
import { startExamBattle, doAction, unitFromNinja } from '../app/src/game/battle';
import { loadSlot, saveSlot } from '../app/src/game/save';

const state = createState('playing', 'Upgrade compatibility');
const n = state.ninjas[0];
Object.assign(n, { traits: ['akimichiClan'], legend: null, level: 80, rank: 'jonin', perks: [], jutsuKnown: ['clan_akimichiClan_roll_1', 'clan_akimichiClan_expand_1'], jutsuEquipped: ['clan_akimichiClan_roll_0'], summonId: 'sum_toad' });
Object.assign(n.s, { tai: 60, nin: 12, ken: 24, doj: 0, gen: 20, med: 35 });
for (const ninja of state.ninjas) ninja.examFails = 0;
n.dojutsuAwakening = null; n.growth.doj = 0;
Object.assign(state, { gold: 45678, rice: 23456, day: 81 });
state.summons = { inventory: { sum_toad: 2, sum_fox: 1 }, recent: [], totalPulls: 23, sinceEpic: 7 };
const unit = unitFromNinja(n);
const before = JSON.stringify(n);
for (const j of JUTSU) {
  const flavour = jutsuFlavour(j);
  assert(flavour && flavour.length > 25, j.id + ' flavour');
  assert(!/clan specialisation|permanently alters|Personal .* technique/.test(flavour), j.id + ' placeholder flavour');
  const text = describeJutsu(unit, j, jutsuCostForNinja(n, j));
  assert(text.scaling.length > 10 && text.lines.length > 0, j.id);
  assert(!/undefined|NaN|clan specialisation|permanently alters/.test(JSON.stringify(text)), j.id);
  if (!j.passive) assert.match(text.lines[0], /Target: .* Cost: \d+ chakra\./);
}
assert.equal(JSON.stringify(n), before, 'rendering descriptions never mutates ninja progression');
const roll = JUTSU_BY_ID.clan_akimichiClan_roll_0;
assert.match(describeJutsu(unit, roll).scaling, /ATK .*Taijutsu/);
assert.match(describeJutsu(unit, JUTSU_BY_ID.clan_akimichiClan_expand_0).lines.join(' '), /Max HP: \+10\.4%/);
assert.match(describeJutsu(unit, JUTSU_BY_ID.clan_akimichiClan_expand_1).lines.join(' '), /Barrier: 30%.*2 rounds/);
assert.match(describeJutsu(unit, JUTSU_BY_ID.clan_akimichiClan_calorie_1).lines.join(' '), /Heals you for 18\.84%/);
assert.match(describeJutsu(unit, JUTSU_BY_ID.clan_akimichiClan_roll_1).lines.join(' '), /3 hits per target/);

// Independent live-cast check: ATK affects Akimichi direct damage, not its declared NIN.
const random = Math.random; Math.random = () => .5;
function cast(atk: number, nin: number, id: string) {
  const b = startExamBattle(state, n, state.ninjas[1], 'chunin');
  const [u, v] = b.units;
  for (const x of [u, v]) Object.assign(x, { pk: undefined, special: null, summonId: null, crit: 0, dodge: 0, def: 0, counter: 0, lifesteal: 0, maxHp: 10000, hp: 10000, maxCp: 1000, cp: 1000, nature: null });
  Object.assign(u, { atk, nin, jutsuPower: 1, jutsuStunBonus: 0, jutsuGuardAmp: 1 });
  b.order = [u.uid, v.uid]; b.idx = 0; b.state = 'choose';
  const desc = describeJutsu(u, JUTSU_BY_ID[id]);
  doAction(b, 'jutsu', id.includes('expand_1') ? u.uid : v.uid, id);
  return { damage: 10000-v.hp, u, v, desc };
}
assert.equal(cast(50, 1, roll.id).damage, cast(50, 200, roll.id).damage);
assert(cast(100, 1, roll.id).damage > cast(50, 1, roll.id).damage * 1.9);
const guard = cast(50, 1, 'clan_akimichiClan_expand_1');
assert.equal(guard.u.jutsuGuardStrength, .3); assert.equal(guard.u.jutsuGuardRounds, 2);
Math.random = random;

// Load a v35-format save in all three slots and round-trip the full state.
const storage = new Map<string, string>();
(globalThis as any).window = { localStorage: { getItem: (k: string) => storage.get(k) ?? null, setItem: (k: string, v: string) => storage.set(k, v), removeItem: (k: string) => storage.delete(k) } };
(globalThis as any).localStorage = (globalThis as any).window.localStorage;
for (let slot = 1; slot <= 3; slot++) {
  const snapshot = structuredClone(state); snapshot.day = 50 + slot;
  storage.set(`shadow-village-save-v3-slot-${slot}`, JSON.stringify({ version: 3, savedAt: 1788350400000, state: snapshot }));
  const loaded = loadSlot(slot)!; assert(loaded);
  assert.equal(loaded.day, snapshot.day); assert.deepEqual(loaded.ninjas, snapshot.ninjas);
  const original = structuredClone(loaded); saveSlot(slot, loaded); assert.deepEqual(loadSlot(slot), original);
}
assert.match(readFileSync('app/capacitor.config.ts','utf8'), /com\.shadowvillage\.game\.progression/);
console.log(`PASS descriptions: all ${JUTSU.length} jutsu; Akimichi scaling, barriers, healing, multi-hit; no state mutation; three existing save slots retained`);
