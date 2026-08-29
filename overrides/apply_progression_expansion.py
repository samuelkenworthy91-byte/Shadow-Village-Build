from pathlib import Path
import re

ROOT = Path("app")

def text(path):
    return (ROOT / path).read_text()

def save(path, value):
    (ROOT / path).write_text(value)

def replace(path, old, new):
    value = text(path)
    if old not in value:
        raise RuntimeError(f"progression patch pattern missing: {path}: {old[:80]!r}")
    save(path, value.replace(old, new))

# ---------------------------------------------------------------------------
# Core data model: Shadow Village grows from six skills to nine.
# ---------------------------------------------------------------------------
replace("src/game/types.ts",
'''export type Skill = "nin" | "tai" | "gen" | "ste" | "med" | "spd";
export type Nature = "fire" | "water" | "wind" | "earth" | "light";
export type TraitId =
  | "prodigy" | "shadowborn" | "hotblood" | "analyst" | "medicnin"
  | "swift" | "ironwill" | "lucky" | "stoic" | "wildcard";''',
'''export type Skill = "nin" | "tai" | "gen" | "ste" | "med" | "spd" | "ken" | "doj" | "tac";
export type Nature = "fire" | "water" | "wind" | "earth" | "light";
export type TraitId =
  | "prodigy" | "shadowborn" | "hotblood" | "analyst" | "medicnin"
  | "swift" | "ironwill" | "lucky" | "stoic" | "wildcard"
  | "bladeborn" | "tactician" | "dojutsuPotential" | "latebloomer" | "glasscannon"
  | "chakrafrugal" | "protective" | "fearless" | "ambidextrous" | "battletrance"
  | "perfectmemory" | "chakraoverflow" | "elementalsavant" | "scout" | "infiltrator"
  | "naturalLeader";''')
replace("src/game/types.ts", "  trait: TraitId;", "  traits: TraitId[];")
replace("src/game/types.ts",
'''  nin: number;
  gen: number;
  med: number;''',
'''  nin: number;
  gen: number;
  med: number;
  ken: number;
  doj: number;
  tac: number;''')

# ---------------------------------------------------------------------------
# Skill metadata, expanded trait pool, and mission templates.
# ---------------------------------------------------------------------------
p = "src/game/content.ts"
s = text(p)
s = s.replace('export const SKILLS: Skill[] = ["nin", "tai", "gen", "ste", "med", "spd"];',
'''export const SKILLS: Skill[] = ["nin", "tai", "gen", "ste", "med", "spd", "ken", "doj", "tac"];''')
s = re.sub(r'export const SKILL_META: Record<Skill, \{ name: string; short: string; kanji: string; color: string \}> = \{.*?\n\};', '''export const SKILL_META: Record<Skill, { name: string; short: string; kanji: string; color: string }> = {
  nin: { name: "Ninjutsu", short: "NIN", kanji: "忍", color: "#4f9ad9" },
  tai: { name: "Taijutsu", short: "TAI", kanji: "体", color: "#e2764f" },
  gen: { name: "Genjutsu", short: "GEN", kanji: "幻", color: "#b46ae0" },
  ste: { name: "Stealth", short: "STE", kanji: "隠", color: "#9aa7bd" },
  med: { name: "Medical", short: "MED", kanji: "医", color: "#63c58c" },
  spd: { name: "Speed", short: "SPD", kanji: "速", color: "#f4c64f" },
  ken: { name: "Kenjutsu", short: "KEN", kanji: "剣", color: "#71c7d4" },
  doj: { name: "Dōjutsu", short: "DŌJ", kanji: "眼", color: "#d86565" },
  tac: { name: "Battlefield Tactics", short: "TAC", kanji: "策", color: "#d0a65a" },
};''', s, flags=re.S)
traits = '''export type TraitRarity = "common" | "uncommon" | "rare";

export const TRAIT_META: Record<TraitId, { name: string; desc: string; boost?: Skill; icon: string; rarity: TraitRarity }> = {
  prodigy: { name: "Prodigy", desc: "+40% experience gain", icon: "★", rarity: "rare" },
  shadowborn: { name: "Shadow Born", desc: "grows Stealth fast", boost: "ste", icon: "隠", rarity: "common" },
  hotblood: { name: "Hot-Blooded", desc: "grows Taijutsu fast", boost: "tai", icon: "炎", rarity: "common" },
  analyst: { name: "Analyst", desc: "grows Genjutsu fast", boost: "gen", icon: "眼", rarity: "common" },
  medicnin: { name: "Medic-nin", desc: "grows Medical fast · helps reduce squad injury time", boost: "med", icon: "医", rarity: "uncommon" },
  swift: { name: "Swift", desc: "grows Speed fast", boost: "spd", icon: "疾", rarity: "common" },
  ironwill: { name: "Iron Will", desc: "gains 40% less fatigue", icon: "鉄", rarity: "uncommon" },
  lucky: { name: "Lucky", desc: "+8% mission success", icon: "運", rarity: "uncommon" },
  stoic: { name: "Stoic", desc: "recovers from injury fast", icon: "静", rarity: "common" },
  wildcard: { name: "Wild Talent", desc: "grows Ninjutsu fast", boost: "nin", icon: "変", rarity: "uncommon" },
  bladeborn: { name: "Blade Prodigy", desc: "grows Kenjutsu fast and favours sword techniques", boost: "ken", icon: "剣", rarity: "uncommon" },
  tactician: { name: "Tactician", desc: "grows Battlefield Tactics fast", boost: "tac", icon: "策", rarity: "common" },
  dojutsuPotential: { name: "Dōjutsu Potential", desc: "an ocular bloodline can awaken and be trained", boost: "doj", icon: "眼", rarity: "rare" },
  latebloomer: { name: "Late Bloomer", desc: "modest beginnings, unusually strong long-term growth", icon: "芽", rarity: "uncommon" },
  glasscannon: { name: "Glass Cannon", desc: "devastating offence, fragile under pressure", icon: "砕", rarity: "uncommon" },
  chakrafrugal: { name: "Chakra Frugal", desc: "larger usable chakra reserve", icon: "節", rarity: "common" },
  protective: { name: "Protective", desc: "excels when fighting as part of a cell", boost: "tac", icon: "護", rarity: "common" },
  fearless: { name: "Fearless", desc: "tires more slowly on dangerous work", icon: "勇", rarity: "common" },
  ambidextrous: { name: "Ambidextrous", desc: "favours advanced and dual-weapon Kenjutsu", boost: "ken", icon: "双", rarity: "uncommon" },
  battletrance: { name: "Battle Trance", desc: "gains critical pressure and lifesteal in battle", icon: "血", rarity: "rare" },
  perfectmemory: { name: "Perfect Memory", desc: "learns and gains experience unusually quickly", icon: "記", rarity: "rare" },
  chakraoverflow: { name: "Chakra Overflow", desc: "vast chakra reserves at a small defensive cost", boost: "nin", icon: "溢", rarity: "rare" },
  elementalsavant: { name: "Elemental Savant", desc: "exceptional affinity with elemental Ninjutsu", boost: "nin", icon: "性", rarity: "rare" },
  scout: { name: "Natural Scout", desc: "grows Stealth and reads danger early", boost: "ste", icon: "偵", rarity: "common" },
  infiltrator: { name: "Infiltrator", desc: "favours covert missions and Stealth techniques", boost: "ste", icon: "潜", rarity: "uncommon" },
  naturalLeader: { name: "Natural Leader", desc: "grows Battlefield Tactics and improves cell coordination", boost: "tac", icon: "将", rarity: "uncommon" },
};

export const TRAIT_IDS = Object.keys(TRAIT_META) as TraitId[];'''
s = re.sub(r'export const TRAIT_META: Record<TraitId, \{ name: string; desc: string; boost\?: Skill; icon: string \}> = \{.*?export const TRAIT_IDS = Object.keys\(TRAIT_META\) as TraitId\[\];', traits, s, flags=re.S)
start = s.index('export const MISSION_TEMPLATES: Record<Rank, MTemplate[]> = {')
end = s.index('\n\nexport const NINJA_NAMES', start)
missions = '''export const MISSION_TEMPLATES: Record<Rank, MTemplate[]> = {
  D: [
    { name: "Find the Lost Cat Tama", desc: "Fast hands, quiet feet.", focus: ["spd", "ste"], slots: 1 },
    { name: "Weed the Elder's Garden", desc: "Backbreaking. Character building.", focus: ["tai"], slots: 1 },
    { name: "Deliver the Sealed Letter", desc: "Do not open it. Seriously.", focus: ["spd", "tac"], slots: 1 },
    { name: "Patch Up the Academy Class", desc: "Scraped knees everywhere.", focus: ["med"], slots: 1 },
    { name: "Dōjō Blade Drill", desc: "Wooden swords. Real bruises.", focus: ["ken", "spd"], slots: 1 },
    { name: "Scare Off Mushroom Thieves", desc: "Look menacing. That is all.", focus: ["tai", "tac"], slots: 2 },
  ],
  C: [
    { name: "Escort the Tea Merchant", desc: "Bandits love oolong season.", focus: ["tac", "tai", "spd"], slots: 2 },
    { name: "Catch the Rice Thief", desc: "Follow the grains. Literally.", focus: ["ste", "spd"], slots: 2 },
    { name: "Break the Illusion Trap", desc: "The bamboo road lies to travellers.", focus: ["gen", "nin"], slots: 2 },
    { name: "Field Clinic at the Ford", desc: "Fever season on the river.", focus: ["med", "tac"], slots: 2 },
    { name: "Map the Northern Pass", desc: "Ink, rope, and wet sandals.", focus: ["ste", "tac", "spd"], slots: 2 },
    { name: "Challenge the Roadside Duelist", desc: "A travelling swordsman wants a worthy bout.", focus: ["ken", "tac"], slots: 2 },
  ],
  B: [
    { name: "Infiltrate the Bandit Camp", desc: "Walk like them. Smell like them.", focus: ["ste", "tac", "gen"], slots: 3 },
    { name: "Retrieve the Stolen Scroll", desc: "Secrets heavier than steel.", focus: ["ste", "nin", "tac"], slots: 3 },
    { name: "Duel the Rogue Swordsman", desc: "He has beaten three cells.", focus: ["ken", "spd", "tac"], slots: 3 },
    { name: "Sabotage the Storehouse", desc: "Ropes cut themselves, they say.", focus: ["nin", "ste", "tac"], slots: 3 },
    { name: "Rescue the Poisoned Caravan", desc: "Antidote, and fast.", focus: ["med", "spd", "tac"], slots: 3 },
  ],
  A: [
    { name: "Silence the War-Horn Tower", desc: "One horn. One chance.", focus: ["ste", "nin", "tac"], slots: 3 },
    { name: "Steal the Fox Lord's Ledger", desc: "Nine tails, one weakness.", focus: ["gen", "ste", "tac", "nin"], slots: 4 },
    { name: "Extract the Captured Scout", desc: "No one is left in the dark.", focus: ["med", "ste", "tac"], slots: 4 },
    { name: "Hunt the Missing-nin", desc: "He was one of ours, once.", focus: ["tac", "spd", "ken", "gen"], slots: 4 },
    { name: "Read the Crimson Eye", desc: "A bloodline technique is exposing every ambush.", focus: ["doj", "gen", "tac"], slots: 3 },
  ],
  S: [
    { name: "Storm the Obsidian Keep", desc: "Where shadows fear to tread.", focus: ["tac", "tai", "nin", "med"], slots: 4 },
    { name: "Steal the Shogun's Seal", desc: "The realm will never know.", focus: ["ste", "gen", "tac", "spd"], slots: 4 },
    { name: "The Nine-Tailed Contract", desc: "Signed in stolen moonlight.", focus: ["nin", "gen", "med", "tac"], slots: 4 },
    { name: "Sever the Serpent's Head", desc: "One cut for a thousand lives.", focus: ["ken", "spd", "ste", "tac"], slots: 4 },
    { name: "Mirror-Eye Conspiracy", desc: "Every move is being seen before it happens.", focus: ["doj", "tac", "gen", "ken"], slots: 4 },
  ],
};'''
s = s[:start] + missions + s[end:]
save(p, s)

# ---------------------------------------------------------------------------
# Recruitment, progression, training, promotion and mission logic.
# ---------------------------------------------------------------------------
p = "src/game/engine.ts"
s = text(p)
s = s.replace('const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));', '''const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));
const hasTrait = (n: Ninja, id: import("./types").TraitId) => n.traits.includes(id);
const dojutsuAwakened = (n: Ninja) => n.s.doj > 0 || hasTrait(n, "dojutsuPotential") || n.legend === "doujutsu";
function rollTraits(pot: number, legendId?: string): import("./types").TraitId[] {
  const common = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "common");
  const uncommon = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "uncommon");
  const rare = TRAIT_IDS.filter((id) => TRAIT_META[id].rarity === "rare");
  const count = pot >= 5 ? 3 : pot >= 3 ? 2 : 1;
  const out: import("./types").TraitId[] = [];
  const add = (id: import("./types").TraitId) => { if (!out.includes(id)) out.push(id); };
  if (legendId === "doujutsu") add("dojutsuPotential");
  if (legendId === "swordsman") add("bladeborn");
  while (out.length < count) {
    const r = Math.random();
    const rareChance = pot >= 5 ? 0.28 : pot >= 4 ? 0.16 : pot >= 3 ? 0.07 : 0.02;
    const uncommonChance = pot >= 4 ? 0.48 : pot >= 2 ? 0.35 : 0.22;
    add(pick(r < rareChance ? rare : r < rareChance + uncommonChance ? uncommon : common));
  }
  return out;
}''')
s = s.replace('''export function overall(n: Ninja): number {
  let t = 0;
  for (const k of SKILLS) t += n.s[k];
  return t / SKILLS.length;
}

export function topSkills(n: Ninja, count = 2): Skill[] {
  return [...SKILLS].sort((a, b) => n.s[b] - n.s[a]).slice(0, count);
}''', '''export function overall(n: Ninja): number {
  const active = SKILLS.filter((k) => k !== "doj" || dojutsuAwakened(n));
  return active.reduce((sum, k) => sum + n.s[k], 0) / active.length;
}

export function topSkills(n: Ninja, count = 2): Skill[] {
  return [...SKILLS].filter((k) => k !== "doj" || dojutsuAwakened(n)).sort((a, b) => n.s[b] - n.s[a]).slice(0, count);
}''')
s = s.replace('if (squad.some((n) => n.trait === "lucky")) ch += 0.08;', 'if (squad.some((n) => hasTrait(n, "lucky"))) ch += 0.08;')
start = s.index('export function makeNinja(')
end = s.index('\n\nconst MISSION_SPEC', start)
make = '''export function makeNinja(s: GameState, elite = false, legendId?: string): Ninja {
  const used = new Set(s.ninjas.map((n) => n.name.split(" ")[0]));
  const pool = NINJA_NAMES.filter((n) => !used.has(n));
  const first = pool.length ? pick(pool) : pick(NINJA_NAMES);
  const nature = pick(Object.keys(NATURE_META)) as Nature;
  const legend = legendId ? LEGENDS[legendId] : null;
  const pot = legend?.pot ?? ri(1, 5);
  const traits = rollTraits(pot, legendId);
  const growth = {} as Record<Skill, number>;
  const sk = {} as Record<Skill, number>;
  const boosted = new Set<Skill>();
  for (const trait of traits) { const b = TRAIT_META[trait].boost; if (b) boosted.add(b); }
  boosted.add(NATURE_META[nature].boost);
  const spec = new Set<Skill>([...boosted, pick(SKILLS.filter((k) => k !== "doj"))]);
  const canDojutsu = traits.includes("dojutsuPotential") || legendId === "doujutsu";
  for (const k of SKILLS) {
    if (k === "doj" && !canDojutsu) { growth[k] = 0; sk[k] = 0; continue; }
    const isSpec = spec.has(k);
    let g = (isSpec ? 1.25 : 0.8) + Math.random() * 0.35;
    let base = (isSpec ? 7 : 3) + Math.random() * 4 + (elite ? 3 : 0);
    if (traits.includes("latebloomer")) { base -= 2; g += 0.22; }
    if (k === "doj") { base = 4 + Math.random() * 4 + (elite ? 2 : 0); g = Math.max(g, 1.3); }
    growth[k] = g;
    sk[k] = Math.max(1, Math.round(base));
  }
  if (legend) for (const k of SKILLS) { sk[k] += legend.bonus[k] ?? 0; if (legend.bonus[k]) growth[k] = Math.max(growth[k], 1.45); }
  return {
    id: s.nextId++, name: `${first} ${pick(SURNAMES)}`, seed: Math.random(),
    look: { hair: ri(0, 7), hairColor: ri(0, HAIR_COLORS.length - 1), skin: ri(0, SKIN_TONES.length - 1), eyes: ri(0, 5), mark: ri(0, 4), outfit: ri(0, OUTFIT_COLORS.length - 1), band: ri(0, BAND_COLORS.length - 1), acc: ri(0, 3), build: ri(0, 2) },
    nature, traits, rank: "genin", level: 1, xp: 0, sp: 0, pot, s: sk, growth,
    fatigue: 0, status: "ready", daysLeft: 0, missionId: null, runs: 0, wins: 0,
    perks: [], legend: legendId ?? null, title: legend ? legend.title : null,
  };
}'''
s = s[:start] + make + s[end:]
s = s.replace('''  const spec = MISSION_SPEC[rank];
  const t = pick(MISSION_TEMPLATES[rank]);''', '''  const spec = MISSION_SPEC[rank];
  const available = MISSION_TEMPLATES[rank].filter((m) => !m.focus.includes("doj") || s.ninjas.some((n) => dojutsuAwakened(n)));
  const t = pick(available.length ? available : MISSION_TEMPLATES[rank].filter((m) => !m.focus.includes("doj")));''')
s = s.replace('''  if (!n || n.sp <= 0) return false;
  n.sp--;''', '''  if (!n || n.sp <= 0) return false;
  if (k === "doj" && !dojutsuAwakened(n)) return false;
  n.sp--;''', 1)
s = s.replace('''  for (const k of SKILLS) {
    rival.s[k] = Math.max(1, Math.round(candidate.s[k] * (0.90 + Math.random() * 0.18) + ri(-1, 1)));
  }''', '''  for (const k of SKILLS) {
    if (k === "doj" && candidate.s.doj <= 0) { rival.s.doj = 0; rival.growth.doj = 0; continue; }
    rival.s[k] = Math.max(1, Math.round(candidate.s[k] * (0.90 + Math.random() * 0.18) + ri(-1, 1)));
  }''')
s = s.replace('const mult = n.trait === "prodigy" ? 1.4 : 1;', 'const mult = hasTrait(n, "prodigy") ? 1.4 : hasTrait(n, "perfectmemory") ? 1.25 : 1;')
s = s.replace('''  spd: ["was over the wall before the alarm finished its first note", "outran the pursuit for six li without slowing", "struck and was gone between two heartbeats"],
};''', '''  spd: ["was over the wall before the alarm finished its first note", "outran the pursuit for six li without slowing", "struck and was gone between two heartbeats"],
  ken: ["drew steel once and ended the duel cleanly", "caught the enemy blade and turned it aside", "cut a path through the chokepoint without breaking stride"],
  doj: ["read the enemy chakra flow before the trap was sprung", "saw the feint and called the cell clear", "tracked a hidden target by a flicker no ordinary eye could catch"],
  tac: ["read the battlefield three moves ahead", "shifted the formation before the ambush closed", "called the target order and broke the enemy line apart"],
};''')
s = s.replace('n.trait === "medicnin"', 'hasTrait(n, "medicnin")').replace('o.trait === "medicnin"', 'hasTrait(o, "medicnin")').replace('n.trait === "stoic"', 'hasTrait(n, "stoic")').replace('n.trait === "ironwill"', 'hasTrait(n, "ironwill")')
s = s.replace('''        for (const k of SKILLS) {
          n.s[k] += Math.max(1, Math.round(req.boost * 1.35 * (n.growth[k] / 1.4)));
        }''', '''        for (const k of SKILLS) {
          if (k === "doj" && !dojutsuAwakened(n)) continue;
          n.s[k] += Math.max(1, Math.round(req.boost * 1.35 * (n.growth[k] / 1.4)));
        }''')
save(p, s)

# ---------------------------------------------------------------------------
# Existing procedural technique tree: 10 tiers, new branches, Dōjutsu gating.
# ---------------------------------------------------------------------------
p = "src/game/perks.ts"
s = text(p)
new_perks = '''  /* ---- kenjutsu branch ---- */
  swordform: { id: "swordform", name: "Sword Fundamentals", kanji: "剣", branch: "ken", kind: "passive", color: "#71c7d4", desc: "Clean blade form adds striking power and defence.", fx: { atk: 1.10, def: 1.05 } },
  precisiondraw: { id: "precisiondraw", name: "Precision Draw", kanji: "抜", branch: "ken", kind: "combat", color: "#71c7d4", desc: "A disciplined draw adds critical chance and critical damage.", fx: { crit: 0.10, critMult: 0.22 } },
  bladeward: { id: "bladeward", name: "Blade Ward", kanji: "受", branch: "ken", kind: "passive", color: "#71c7d4", desc: "Turns incoming force away with the flat of the blade.", fx: { def: 1.13, counter: 0.16 } },
  chakrablade: { id: "chakrablade", name: "Chakra Blade", kanji: "刃", branch: "ken", kind: "signature", color: "#71c7d4", desc: "Unlocks 奥義 Chakra Edge — a focused blade strike powered by Kenjutsu.", fx: { special: true, atk: 1.06 }, tech: { name: "Chakra Edge", power: 1.25, stat: "ken", hits: 1, note: "a precise chakra-fed sword strike" } },
  twinblade: { id: "twinblade", name: "Twin Blade Flow", kanji: "双", branch: "ken", kind: "signature", color: "#71c7d4", desc: "Unlocks 奥義 Twin Fang — two rapid blade strikes.", fx: { special: true, crit: 0.08 }, tech: { name: "Twin Fang", power: 0.72, stat: "ken", hits: 2, note: "two linked sword cuts" } },
  /* ---- dōjutsu branch ---- */
  ocularawakening: { id: "ocularawakening", name: "Ocular Awakening", kanji: "眼", branch: "doj", kind: "passive", color: "#d86565", desc: "The awakened eye reads motion a fraction before it happens.", fx: { dodge: 0.08, crit: 0.05 } },
  predictiveeye: { id: "predictiveeye", name: "Predictive Eye", kanji: "読", branch: "doj", kind: "combat", color: "#d86565", desc: "Tracks intent through tiny shifts in movement.", fx: { dodge: 0.12, counter: 0.15 } },
  chakrasight: { id: "chakrasight", name: "Chakra Sight", kanji: "脈", branch: "doj", kind: "passive", color: "#d86565", desc: "Sees hidden chakra signatures and improves difficult mission reads.", village: { missionBonus: 0.10 } },
  mirrorgaze: { id: "mirrorgaze", name: "Mirror Gaze", kanji: "鏡", branch: "doj", kind: "signature", color: "#d86565", desc: "Unlocks 奥義 Mirror Gaze — an ocular counter-technique.", fx: { special: true, dodge: 0.08 }, tech: { name: "Mirror Gaze", power: 1.22, stat: "doj", hits: 1, note: "an ocular counter that pierces hesitation" } },
  /* ---- battlefield tactics branch ---- */
  awareness: { id: "awareness", name: "Situational Awareness", kanji: "察", branch: "tac", kind: "passive", color: "#d0a65a", desc: "Reads threats early, improving defence and mission execution.", fx: { def: 1.07, dodge: 0.04 }, village: { missionBonus: 0.05 } },
  formationreading: { id: "formationreading", name: "Formation Reading", kanji: "陣", branch: "tac", kind: "passive", color: "#d0a65a", desc: "Finds weak points and keeps the cell organised.", fx: { atk: 1.05, def: 1.08 }, village: { missionBonus: 0.06 } },
  targetpriority: { id: "targetpriority", name: "Target Priority", kanji: "標", branch: "tac", kind: "combat", color: "#d0a65a", desc: "Identifies the decisive target before battle turns chaotic.", fx: { crit: 0.11, critMult: 0.15 } },
  counterplan: { id: "counterplan", name: "Counterplan", kanji: "逆", branch: "tac", kind: "passive", color: "#d0a65a", desc: "Adapts after first contact and turns pressure back on the enemy.", fx: { counter: 0.22, def: 1.06 } },
  commandassault: { id: "commandassault", name: "Commander's Gambit", kanji: "将", branch: "tac", kind: "signature", color: "#d0a65a", desc: "Unlocks 奥義 Coordinated Assault.", fx: { special: true, atk: 1.05 }, tech: { name: "Coordinated Assault", power: 0.68, stat: "tac", hits: 2, note: "two attacks timed to the enemy opening" } },

'''
s = s.replace('  /* ---- universal ---- */', new_perks + '  /* ---- universal ---- */')
s = s.replace('''const TRAIT_BRANCH: Partial<Record<TraitId, Skill>> = {
  shadowborn: "ste", hotblood: "tai", analyst: "gen", medicnin: "med", swift: "spd", wildcard: "nin",
};''', '''const TRAIT_BRANCH: Partial<Record<TraitId, Skill>> = {
  shadowborn: "ste", hotblood: "tai", analyst: "gen", medicnin: "med", swift: "spd", wildcard: "nin",
  bladeborn: "ken", ambidextrous: "ken", tactician: "tac", naturalLeader: "tac", protective: "tac",
  dojutsuPotential: "doj", scout: "ste", infiltrator: "ste", elementalsavant: "nin",
};''')
s = s.replace('return Math.max(0, Math.floor(level / 2));', 'return Math.min(10, Math.max(0, Math.floor(level / 2)));')
s = s.replace('''  const tb = TRAIT_BRANCH[n.trait];
  if (tb) favour.push(tb);''', '''  for (const trait of n.traits) { const tb = TRAIT_BRANCH[trait]; if (tb) favour.push(tb); }''')
s = s.replace('  const pool = [...ALL_IDS];', '  const canDojutsu = n.s.doj > 0 || n.traits.includes("dojutsuPotential") || n.legend === "doujutsu";\n  const pool = ALL_IDS.filter((id) => PERKS[id].branch !== "doj" || canDojutsu);')
s = s.replace("Build this ninja's personal tree: 6 tiers", "Build this ninja's personal tree: 10 tiers").replace('for (let t = 0; t < 6; t++) {', 'for (let t = 0; t < 10; t++) {')
s = s.replace('bonus: { gen: 9, spd: 6 }, pot: 5,', 'bonus: { gen: 5, spd: 4, doj: 10 }, pot: 5,').replace('stat: "gen", hits: 1, note: "turns their power back on them"', 'stat: "doj", hits: 1, note: "turns their power back on them"')
s = s.replace('bonus: { tai: 9, ste: 6 }, pot: 4,', 'bonus: { ken: 9, ste: 6, tac: 3 }, pot: 4,').replace('stat: "tai", hits: 1, note: "cannot be dodged or guarded"', 'stat: "ken", hits: 1, note: "cannot be dodged or guarded"')
s = s.replace('''    if (p.id === "willoffire") out.allyAtk *= 1.12;
  }
  return out;''', '''    if (p.id === "willoffire") out.allyAtk *= 1.12;
  }
  for (const trait of n.traits) {
    switch (trait) {
      case "glasscannon": out.atk *= 1.18; out.hp *= 0.86; break;
      case "chakrafrugal": out.cp *= 1.2; break;
      case "protective": out.def *= 1.08; out.missionBonus += 0.03; break;
      case "fearless": out.fatigue *= 0.85; break;
      case "ambidextrous": out.crit += 0.05; out.critMult += 0.12; break;
      case "battletrance": out.crit += 0.07; out.lifesteal += 0.08; break;
      case "chakraoverflow": out.cp *= 1.45; out.def *= 0.95; break;
      case "elementalsavant": out.atk *= 1.06; out.cp *= 1.08; break;
      case "scout": out.missionBonus += 0.03; out.dodge += 0.03; break;
      case "infiltrator": out.missionBonus += 0.05; break;
      case "naturalLeader": out.missionBonus += 0.08; out.allyAtk *= 1.05; break;
    }
  }
  return out;''')
save(p, s)

# ---------------------------------------------------------------------------
# Battle derivation. New stats actively matter rather than merely display.
# ---------------------------------------------------------------------------
p = "src/game/battle.ts"
s = text(p)
s = s.replace(' *   SPD → turn order + crit chance + dodge', ' *   SPD → turn order + dodge\n *   KEN → blade attack power + critical precision\n *   DŌJ → ocular perception + genjutsu reading + evasion\n *   TAC → defence + initiative + target selection')
s = s.replace('''    atk: (n.s.tai * 1.45 + n.s.nin * 0.3 + rb * 2) * fx.atk,
    def: (5 + n.s.tai * 0.55 + rb * 2.5) * fx.def,
    spd: n.s.spd * 1.4 + n.level,
    nin: n.s.nin,
    gen: n.s.gen,
    med: n.s.med,''', '''    atk: (n.s.tai * 1.22 + n.s.ken * 0.52 + n.s.nin * 0.28 + rb * 2) * fx.atk,
    def: (5 + n.s.tai * 0.46 + n.s.tac * 0.34 + rb * 2.5) * fx.def,
    spd: n.s.spd * 1.28 + n.s.tac * 0.16 + n.level,
    nin: n.s.nin,
    gen: n.s.gen + n.s.doj * 0.22,
    med: n.s.med,
    ken: n.s.ken,
    doj: n.s.doj,
    tac: n.s.tac,''')
s = s.replace('''    crit: clamp(0.05 + n.s.spd * 0.006 + fx.crit, 0, 0.7),
    critMult: 1.8 + n.s.ste * 0.022 + fx.critMult,
    dodge: clamp(n.s.spd * 0.0035 + fx.dodge, 0, 0.45),''', '''    crit: clamp(0.05 + n.s.spd * 0.0045 + n.s.ken * 0.004 + n.s.doj * 0.0025 + fx.crit, 0, 0.7),
    critMult: 1.8 + n.s.ste * 0.018 + n.s.ken * 0.008 + fx.critMult,
    dodge: clamp(n.s.spd * 0.003 + n.s.doj * 0.0035 + n.s.tac * 0.0012 + fx.dodge, 0, 0.45),''')
s = s.replace('''    nin: (6 + power * 0.7) * k.nin,
    gen: (5 + power * 0.6) * k.gen,
    med: 0,''', '''    nin: (6 + power * 0.7) * k.nin,
    gen: (5 + power * 0.6) * k.gen,
    med: 0,
    ken: 4 + power * 0.55,
    doj: 0,
    tac: 4 + power * 0.5,''')
s = s.replace('''    u.gen * 2 +
    u.crit * 100 +''', '''    u.gen * 2 +
    u.ken * 1.8 + u.doj * 1.5 + u.tac * 1.7 +
    u.crit * 100 +''')
s = s.replace('''      const statVal = tech.stat === "tai" ? u.atk / 1.45 : tech.stat === "nin" ? u.nin : tech.stat === "gen" ? u.gen : tech.stat === "med" ? u.med : tech.stat === "spd" ? u.spd / 1.4 : u.atk / 1.6;''', '''      const statVal = tech.stat === "tai" ? u.atk / 1.45 : tech.stat === "nin" ? u.nin : tech.stat === "gen" ? u.gen : tech.stat === "med" ? u.med : tech.stat === "spd" ? u.spd / 1.4 : tech.stat === "ken" ? u.ken : tech.stat === "doj" ? u.doj : tech.stat === "tac" ? u.tac : u.atk / 1.6;''')
s = s.replace('n.trait === "prodigy"', 'n.traits.includes("prodigy")').replace('n.trait === "stoic"', 'n.traits.includes("stoic")')
save(p, s)

# ---------------------------------------------------------------------------
# UI: multiple traits + dormant Dōjutsu lock.
# ---------------------------------------------------------------------------
p = "src/components/NinjaDetail.tsx"
s = text(p).replace('const trait = TRAIT_META[n.trait];', 'const traits = n.traits.map((id) => TRAIT_META[id]);')
s = s.replace('''              <span className="rounded bg-gold/15 px-1.5 py-[2px] text-gold" title={trait.desc}>
                {trait.icon} {trait.name}
              </span>''', '''              {traits.map((trait) => <span key={trait.name} className="rounded bg-gold/15 px-1.5 py-[2px] text-gold" title={trait.desc}>{trait.icon} {trait.name}</span>)}''')
s = s.replace('disabled={n.sp <= 0}', 'disabled={n.sp <= 0 || (k === "doj" && n.s.doj <= 0 && !n.traits.includes("dojutsuPotential") && n.legend !== "doujutsu")}')
s = s.replace('''            <b className="text-paper/75">{trait.name}:</b> {trait.desc}. <b className="text-paper/75">{nat.name}</b> accelerates {SKILL_META[nat.boost].name}.
            Higher potential means more skill points each level — the estimate sharpens as {n.name.split(" ")[0]} gains experience.''', '''            <b className="text-paper/75">Traits:</b> {traits.map((t) => `${t.name} — ${t.desc}`).join(" · ")}. <b className="text-paper/75">{nat.name}</b> accelerates {SKILL_META[nat.boost].name}.
            Dōjutsu remains dormant at 0 unless an ocular bloodline awakens it. Higher potential means more skill points each level.''')
save(p, s)

p = "src/components/ScoutModal.tsx"
s = text(p).replace('const trait = TRAIT_META[n.trait];', 'const traits = n.traits.map((id) => TRAIT_META[id]);')
s = s.replace('<span className="rounded bg-gold/15 px-1.5 py-[2px] text-gold">{trait.icon} {trait.name}</span>', '{traits.map((trait) => <span key={trait.name} className="rounded bg-gold/15 px-1.5 py-[2px] text-gold">{trait.icon} {trait.name}</span>)}').replace('{trait.desc}.', '{traits.map((t) => t.desc).join(" · ")}.')
save(p, s)
for p in ["src/components/SquadModal.tsx", "src/components/RaidDefenseModal.tsx"]:
    s = text(p).replace('TRAIT_META[n.trait].name', 'n.traits.map((id) => TRAIT_META[id].name).join(" · ")')
    save(p, s)

# Fresh development saves and a separate Android app identity.
replace("src/game/save.ts", "const SAVE_VERSION = 1;", "const SAVE_VERSION = 2;")
p = "capacitor.config.ts"
s = text(p).replace('appId: "com.shadowvillage.game",', 'appId: "com.shadowvillage.game.progression",').replace('appName: "Shadow Village",', 'appName: "Shadow Village — Progression Dev",')
save(p, s)
p = "public/sw.js"
s = text(p).replace('shadow-village-v8-target-selection', 'shadow-village-progression-dev-v1')
save(p, s)

print("Shadow Village progression expansion applied")
