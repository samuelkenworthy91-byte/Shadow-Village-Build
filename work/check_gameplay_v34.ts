import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import vm from 'node:vm';
import { createState, makeNinja, scout } from '../app/src/game/engine';
import { NINJA_NAMES, SURNAMES, NATURE_META, KEKKEI_META, TRAIT_META } from '../app/src/game/content';
import { JUTSU, JUTSU_BY_ID, jutsuForNinja, knownJutsuIds, learnJutsu, prerequisiteJutsu, toggleJutsuEquip } from '../app/src/game/jutsu';
import { legendScoutChance, recruitName } from '../app/src/game/recruitment';
import { SUMMONS, SUMMON_BY_ID, ensureSummonState, pullSummons, summonPullCost, bondSummon, releaseSummon, summonAvailableCount } from '../app/src/game/summons';
import { startExamBattle, startBattle, startBingoBattle, doAction, nextTurn, unitFromNinja } from '../app/src/game/battle';
import { statusTickDamage, jutsuStatusPreview } from '../app/src/game/statusDamage';
import { saveSlot, loadSlot } from '../app/src/game/save';
import { ninjaArtId } from '../app/src/game/ninjaArt';
import type { Battle, Ninja, Nature, TraitId, Unit } from '../app/src/game/types';
let seed = 341987;
const originalRandom = Math.random;
Math.random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
const s = createState('playing', 'Gameplay QC');
const template = structuredClone(s.ninjas[0]);
function ninja(traits: TraitId[] = []): Ninja {
  const n = structuredClone(template);
  Object.assign(n, { id: s.nextId++, name: 'Test Shinobi', traits, nature: 'fire', secondaryNature: null, level: 80, rank: 'jonin', perks: [], legend: null, summonId: null, jutsuKnown: [], jutsuGranted: [], jutsuEquipped: [], genjutsuKnown: [], genjutsuEquipped: [], techniqueTree: undefined, dojutsuAwakening: null });
  for (const k of Object.keys(n.s) as (keyof Ninja['s'])[]) n.s[k] = k === 'doj' ? 0 : 60;
  return n;
}
assert.equal(NINJA_NAMES.length, 296); assert.equal(SURNAMES.length, 200);
assert.equal(new Set(NINJA_NAMES).size, 296); assert.equal(new Set(SURNAMES).size, 200);
const names: string[] = [];
for (let i = 0; i < 1200; i++) names.push(recruitName(names));
assert.equal(new Set(names).size, names.length);
assert.equal(new Set(names.slice(0,296).map(n => n.split(' ')[0])).size,296);
const fullFirst = SURNAMES.map(x => `${NINJA_NAMES[0]} ${x}`);
assert(!fullFirst.includes(recruitName(fullFirst, () => 0)));
console.log('PASS names: 59,200 authored combinations, no duplicates across 1,200 recruits');

s.ninjas = []; s.b.hall = 1; s.techs = []; s.day = 5000;
assert.equal(legendScoutChance(s), .02);
let legends = 0, clans = 0, kekkei = 0, nara = 0, jinchuriki = 0;
const trials = 6000;
for (let i = 0; i < trials; i++) {
  s.scout = null; s.ap = 5; s.gold = 1000; s.rice = 1000;
  assert(scout(s, []));
  const recruits = s.scout! as Ninja[];
  assert.equal(new Set(recruits.map(n => n.name)).size,3);
  assert.equal(new Set(recruits.map(n => n.id)).size,3);
  assert.equal(new Set(recruits.map(ninjaArtId)).size,3);
  for (const n of recruits) {
    if (n.legend) legends++;
    if (n.legend === 'jinchuriki') jinchuriki++;
    const unique = n.traits.filter(t => TRAIT_META[t].rarity === 'unique');
    if (!n.legend) assert(unique.length <= 1);
    if (!n.legend && unique.length) clans++;
    if (n.secondaryNature) kekkei++;
    if (n.traits.includes('shadowBinder')) nara++;
  }
}
assert(legends/trials > .012 && legends/trials < .03);
assert(clans/(trials*3) > .19 && clans/(trials*3) < .25);
assert(kekkei/(trials*3) > .08); assert(nara > jinchuriki * 3);
s.b.hall=10; s.techs=['hall_elite_recruitment','tea_black_market']; assert.equal(legendScoutChance(s),.06);
console.log(`PASS scouting: ${legends}/${trials} searches with legends; ${clans}/${trials*3} clan recruits; ${nara} Nara vs ${jinchuriki} Jinchuriki`);

const elements = Object.keys(NATURE_META) as Nature[], pairs: string[]=[];
const audit: object[]=[];
for (let i=0;i<elements.length;i++) for(let z=i+1;z<elements.length;z++) {
 const a=elements[i], b=elements[z], key=[a,b].sort().join('+');pairs.push(key);assert(KEKKEI_META[key]);
 const table=JUTSU.filter(j=>j.requiresKekkei===key);assert(table.length>=12);
 const paths=[...new Set(table.map(j=>j.path))];assert.equal(paths.length,4);
 for (const [first,second] of [[a,b],[b,a]]) {
  const n=ninja(['kekkeiTalent']);n.nature=first;n.secondaryNature=second;
  assert.deepEqual(jutsuForNinja(n).map(j=>j.id),table.map(j=>j.id));
  for (const path of paths) {
   const branch=table.filter(j=>j.path===path).sort((a,b)=>a.tier-b.tier);
   assert.equal(branch[0].tier,0);assert(knownJutsuIds(n).includes(branch[0].id));
   for(let tier=1;tier<branch.length;tier++) {assert.equal(branch[tier].tier,tier);assert.equal(prerequisiteJutsu(n,branch[tier].id)?.id,branch[tier-1].id);assert(learnJutsu(n,branch[tier].id));}
  }
  const other=ninja(['shadowBinder','kekkeiTalent']);other.nature=first;other.secondaryNature=second;
  assert(jutsuForNinja(other).some(j=>j.requiresTrait==='shadowBinder'));
  assert.equal(jutsuForNinja(other).filter(j=>j.requiresKekkei===key).length,table.length);
 }
 audit.push({pair:key,name:KEKKEI_META[key].name,techniques:table.length,paths});
}
assert.deepEqual(pairs.sort(),Object.keys(KEKKEI_META).sort());
assert.equal(new Set(JUTSU.map(j=>j.id)).size,JUTSU.length);
for (const trait of ['kamioriClan','hibikiClan','kasumoriClan'] as TraitId[]) {
 const n=ninja([trait]), table=jutsuForNinja(n);assert.equal(table.length,16);assert.equal(table.filter(j=>j.tier===0).length,4);
 for(const j of table.sort((a,b)=>a.tier-b.tier)) {
  if(j.tier>0) assert(learnJutsu(n,j.id),j.id);
  assert(knownJutsuIds(n).includes(j.id));
 }
 assert(table.every(j=>j.requiresTrait===trait));
 for(const j of table.filter(j=>!j.passive).slice(0,4)) assert(toggleJutsuEquip(n,j.id));
 assert.equal(n.jutsuEquipped!.length,4);
 assert(!jutsuForNinja(ninja()).some(j=>j.requiresTrait===trait));
}
console.log('PASS bloodlines: all 10 distinct tables, both nature orders, every prerequisite and clan+pair access');
console.log(JSON.stringify(audit));

s.techs=[];
function fight(id?: string) {
 const n=ninja();n.summonId=id??null;
 const b=startExamBattle(s,n,ninja(),'chunin');
 const u=b.units[0],v=b.units[1];
 for(const x of [u,v]) {x.crit=0;x.dodge=0;x.counter=0;x.regen=0;x.pk=undefined;x.def=0;x.lifesteal=0; x.maxHp=10000;x.hp=10000;x.maxCp=1000;x.cp=1000;}
 b.order=[u.uid,v.uid];b.idx=0;b.state='choose';
 return {b,u,v};
}
function cast(b:Battle,u:Unit,v:Unit,id:string) {b.idx=b.order.indexOf(u.uid);b.state='choose';return doAction(b,'jutsu',v.uid,id);}
function round(b:Battle) {b.idx=b.order.length-1;b.state='choose';nextTurn(b);}
Math.random=()=>.5;
for (const [id,effect] of [['fire_ember','burn'],['swarm_bite','poison'],['bone_camellia','bleed']] as const) {
 for (const stat of [10,60,200]) {
  const {b,u,v}=fight();for (const k of ['nin','gen','ken','med','tac','spd','ste'] as const) u[k]=stat;
  u.jutsuPower=1.3;u.jutsuBurnAmp=1;v.guard=true;
  cast(b,u,v,id);const j=JUTSU_BY_ID[id],tick=v[`${effect}Damage`]!;
  assert.equal(tick,statusTickDamage(effect,stat,1.3));assert(tick>stat*.3);
  assert(jutsuStatusPreview(u,j)?.includes(`${tick} HP/round`));
  const hp=v.hp;round(b);assert.equal(hp-v.hp,tick);
  const strong=v[`${effect}Damage`];u.jutsuPower=.1;cast(b,u,v,id);assert.equal(v[`${effect}Damage`],strong);
 }
}
{
 const {b,u,v}=fight();cast(b,u,v,'fire_ember');cast(b,u,v,'swarm_bite');cast(b,u,v,'bone_camellia');
 b.idx=1;doAction(b,'jutsu',v.uid,'clan_kasumoriClan_antidote_0');
 assert.equal(v.burnRounds,0);assert.equal(v.poisonRounds,0);assert.equal(v.bleedRounds,0);
}
console.log('PASS DoT: live casts, early/mid/late scaling, actual round damage, previews, refresh and cleanse');

for (const sm of SUMMONS) {
 const {b,u,v}=fight(sm.id);
 const before=v.hp;
 if(sm.trigger==='battle_start') {assert(u.summonUsed);assert(sm.effect==='shield' ? u.summonShieldRounds!>0 : u.summonHasteRounds!>0);}
 if(sm.trigger==='bonded_low_hp') {u.hp=360;u.maxHp=1000;v.nin=40;b.idx=1;doAction(b,'jutsu',u.uid);assert(u.summonUsed,sm.id);}
 if(sm.trigger==='bonded_fatal') {u.hp=1;b.idx=1;doAction(b,'jutsu',u.uid);assert(u.alive);assert.equal(u.hp,Math.round(u.maxHp*sm.power));u.hp=1;doAction(b,'jutsu',u.uid);assert(!u.alive);}
 if(sm.trigger==='chakra_empty') {u.cp=10;u.maxCp=100;doAction(b,'jutsu',v.uid);assert(u.summonUsed);assert(u.cp>=45);}
 if(sm.trigger==='round_three') {b.round=2;round(b);assert(u.summonUsed);assert(v.hp<before);const hp=v.hp;round(b);assert.equal(v.hp,hp);}
 if(sm.trigger==='ally_fallen') {const ally={...unitFromNinja(ninja()),hp:1,maxHp:10000,dodge:0,pk:undefined,uid:'friend'};b.units.push(ally);b.order.push(ally.uid);b.idx=1;doAction(b,'jutsu',ally.uid);assert(!ally.alive);assert(u.summonUsed);assert(v.hp<before);}
 assert.equal(b.log.filter(l=>l.t.includes(`summons ${sm.name}`)).length,1,sm.id);
}
{
 const {b,u}=fight('sum_fox');u.hp=2;u.poisonDamage=10;u.poisonRounds=2;round(b);assert(u.alive&&u.summonUsed);assert(u.hp>2);
}
console.log('PASS summons: all ten actual interventions, once per battle, shields/haste, fatal and DoT rescue');

Math.random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
const owned=createState('playing','Pact save');owned.gold=100000;owned.rice=100000;owned.ap=100;
const st=ensureSummonState(owned);st.sinceEpic=11;
const cost=summonPullCost(5,owned),gold=owned.gold,rice=owned.rice;
const draws=pullSummons(owned,5);assert(draws.ok);assert(['epic','legendary'].includes(draws.items[0].rarity));assert.equal(owned.gold,gold-cost.gold);assert.equal(owned.rice,rice-cost.rice);assert.equal(owned.ap,99);
const a=owned.ninjas[0],z=owned.ninjas[1];st.inventory.sum_fox=1;
assert(bondSummon(owned,a,'sum_fox'));assert(!bondSummon(owned,z,'sum_fox'));assert.equal(summonAvailableCount(owned,'sum_fox'),0);assert(releaseSummon(owned,a));assert(bondSummon(owned,z,'sum_fox'));
z.status='mission';assert(!releaseSummon(owned,z));z.status='ready';
owned.phase='battle';const frozen=JSON.stringify(st);assert(!pullSummons(owned,1).ok);assert(!bondSummon(owned,a,'sum_fox'));assert.equal(JSON.stringify(st),frozen);owned.phase='playing';
owned.gold=0;const total=st.totalPulls,ap=owned.ap;assert(!pullSummons(owned,1).ok);assert.equal(st.totalPulls,total);assert.equal(owned.ap,ap);
const storage=new Map<string,string>();(globalThis as any).window={localStorage:{getItem:(k:string)=>storage.get(k)??null,setItem:(k:string,v:string)=>storage.set(k,v),removeItem:(k:string)=>storage.delete(k)}};(globalThis as any).localStorage=(globalThis as any).window.localStorage;
saveSlot(1,owned);const loaded=loadSlot(1)!;assert(loaded);assert.equal(ensureSummonState(loaded).totalPulls,total);assert.equal(loaded.ninjas[1].summonId,'sum_fox');assert.equal(ensureSummonState(loaded).inventory.sum_fox,1);
const ctx:any={self:{addEventListener(){}}};vm.runInNewContext(readFileSync('app/public/sw.js','utf8')+'\nglobalThis.assets=SUMMON_ART;',ctx);assert.equal(ctx.assets.length,10);for(const path of ctx.assets) assert(existsSync('app/public'+path));
assert.equal(SUMMONS.length,10);assert(SUMMON_BY_ID.sum_fox);
console.log('PASS gacha: pity, charges, copy ownership, deployment locks, failed purchases, save/load and offline art');
Math.random=originalRandom;
