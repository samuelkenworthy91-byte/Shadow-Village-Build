import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import vm from 'node:vm';
import { createState, makeNinja } from '../app/src/game/engine';
import { GENERAL_ART_IDS, ninjaArtId, ninjaArtSrc } from '../app/src/game/ninjaArt';

const qc = JSON.parse(readFileSync('overrides/portrait_qc_v33.json', 'utf8'));
assert.deepEqual(GENERAL_ART_IDS, qc.approved_ids);
const approved = new Set<number>(GENERAL_ART_IDS);
const state = createState('playing', 'Portrait QC');
const sample = state.ninjas[0];
for (let id = 1; id <= 370; id++) {
  const ninja = { ...sample, portrait: id };
  const resolved = ninjaArtId(ninja);
  assert(approved.has(resolved), `Retired portrait ${id} escaped`);
  if (approved.has(id)) assert.equal(resolved, id, `Approved assignment ${id} changed`);
  assert.equal(ninjaArtId(ninja), resolved);
  assert(existsSync('app/public' + ninjaArtSrc(ninja)));
}
for (const portrait of [-1, 0, 371, 2.5, NaN, Infinity]) {
  assert(approved.has(ninjaArtId({ ...sample, portrait })));
}
function mix(x: number) {
  x = Math.imul(x ^ (x >>> 16), 0x45d9f3b);
  x = Math.imul(x ^ (x >>> 16), 0x45d9f3b);
  return (x ^ (x >>> 16)) >>> 0;
}
for (let id = 1; id <= 10000; id++) {
  const ninja = { ...sample, id, portrait: undefined };
  const L = ninja.look;
  const salt = (id >>> 0) ^ ((L.hair & 15) << 1) ^ ((L.hairColor & 15) << 5)
    ^ ((L.skin & 7) << 9) ^ ((L.outfit & 15) << 12) ^ ((L.acc & 7) << 17) ^ ((L.build & 7) << 20);
  const previous = (mix(salt) % 370) + 1;
  const next = ninjaArtId(ninja);
  assert(approved.has(next));
  if (approved.has(previous)) assert.equal(next, previous, `Legacy ninja ${id} changed unnecessarily`);
}
state.ninjas = [];
for (let i = 0; i < GENERAL_ART_IDS.length; i++) state.ninjas.push(makeNinja(state));
assert.equal(new Set(state.ninjas.map(ninjaArtId)).size, GENERAL_ART_IDS.length, 'Recruitment repeated an available portrait');
assert(approved.has(ninjaArtId(makeNinja(state))), 'Exhausted pool fallback is invalid');
assert.equal(ninjaArtSrc({ ...sample, bingoArt: '/bingo/bingo_001.webp' }), '/bingo/bingo_001.webp');
const ctx: any = { self: { addEventListener() {} } };
vm.runInNewContext(readFileSync('app/public/sw.js', 'utf8') + '\nglobalThis.art = NINJA_ART;', ctx);
assert.equal(ctx.art.length, GENERAL_ART_IDS.length);
assert.deepEqual(Array.from(ctx.art), GENERAL_ART_IDS.map(id => `/ninjas/ninja_${String(id).padStart(3, '0')}.png`));
console.log('PASS: 340 recruits without repeats; all 370 saved IDs; 10,000 legacy identities; invalid-ID fallback; offline asset list; Bingo art');
