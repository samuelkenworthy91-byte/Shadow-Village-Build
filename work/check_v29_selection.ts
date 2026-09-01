/* Verify v29: regenerated portraits present + no-repeat uniform art draw. */
import { createState, makeNinja } from "../app/src/game/engine";
import { ninjaArtId } from "../app/src/game/ninjaArt";
import { existsSync } from "fs";
import { join, resolve } from "path";

const s = createState("playing", "Check Village");
const recruits = [];
for (let i = 0; i < 150; i++) {
  const n = makeNinja(s);
  recruits.push(n);
  s.ninjas.push(n); // the game adds each recruit before the next one rolls
}

const arts = recruits.map((n) => ninjaArtId(n));
const dupes = arts.filter((a, i) => arts.indexOf(a) !== i);
console.log(`[1] 150 recruits -> ${new Set(arts).size} distinct portraits, ${dupes.length} duplicates`);
if (dupes.length) console.log("  FAIL duplicate art ids:", dupes);

const bad = arts.filter((a) => a < 1 || a > 370 || !Number.isInteger(a));
console.log(`[2] all ids in 1..370: ${bad.length === 0}`);

const pubDir = resolve(process.cwd(), "app/public/ninjas");
let missing = 0;
for (const a of new Set(arts)) {
  if (!existsSync(join(pubDir, `ninja_${String(a).padStart(3, "0")}.png`))) missing++;
}
console.log(`[3] all ${new Set(arts).size} used portraits resolve to files: ${missing === 0}`);

// legacy path: ninjas without portrait field must keep hash art
const legacy = { ...recruits[0] } as any;
delete legacy.portrait;
const legacyArts = new Set<number>();
for (let i = 0; i < 3; i++) legacyArts.add(ninjaArtId(legacy));
console.log(`[4] legacy ninja keeps stable hash art (${[...legacyArts].join(",")}): ${legacyArts.size === 1}`);
console.log(arts.length && new Set(arts).size === arts.length ? "\nSELECTION VERIFIED" : "\nSELECTION FAILURES");
