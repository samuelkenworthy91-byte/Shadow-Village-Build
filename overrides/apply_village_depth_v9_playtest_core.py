from pathlib import Path
import re

ROOT = Path("app")

def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{label}: anchor not found in {path}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: applied")

# 1) Equipment bonuses must be visible on the ninja's main stat sheet, not only in combat.
replace_once(
    "src/components/NinjaDetail.tsx",
    'import { unitFromNinja } from "../game/battle";',
    'import { unitFromNinja } from "../game/battle";\nimport { equipmentSkillBonus } from "../game/equipment";',
    "equipment stat import",
)
replace_once(
    "src/components/NinjaDetail.tsx",
    '  const maxSkill = Math.max(20, ...SKILLS.map((k) => n.s[k]));',
    '  const maxSkill = Math.max(20, ...SKILLS.map((k) => Math.max(n.s[k], effSkill(s, n, k))));',
    "equipment-aware skill scale",
)
replace_once(
    "src/components/NinjaDetail.tsx",
    '''              const raw = n.s[k];
              const eff = effSkill(s, n, k);
              const penalty = raw - eff;
              const gr = n.growth[k];''',
    '''              const raw = n.s[k];
              const gear = equipmentSkillBonus(n, k);
              const eff = effSkill(s, n, k);
              const conditionOnly = eff - gear;
              const penalty = Math.max(0, raw - conditionOnly);
              const shown = Math.max(0, Math.round(eff));
              const gr = n.growth[k];''',
    "equipment-aware stat derivation",
)
replace_once(
    "src/components/NinjaDetail.tsx",
    '''                      <span className="ml-auto text-[11px] font-black tabular-nums text-paper/95">{raw}</span>
                      {penalty > 0.4 && <span className="text-[9px] font-bold tabular-nums text-vermil">−{Math.round(penalty)}</span>}''',
    '''                      <span className="ml-auto text-[11px] font-black tabular-nums text-paper/95">{shown}</span>
                      {gear > 0 && <span className="text-[8.5px] font-black tabular-nums text-jade">+{gear} GEAR</span>}
                      {penalty > 0.4 && <span className="text-[9px] font-bold tabular-nums text-vermil">−{Math.round(penalty)} CONDITION</span>}''',
    "equipment stat labels",
)
replace_once(
    "src/components/NinjaDetail.tsx",
    '''                      <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${(raw / maxSkill) * 100}%`, backgroundColor: meta.color }} />''',
    '''                      <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${(Math.max(0, eff) / maxSkill) * 100}%`, backgroundColor: meta.color }} />''',
    "equipment-aware stat bar",
)

# 2) Raids now scale off the strongest owned ninja. Every attacker is calibrated to
#    a bounded relative band, so day count no longer produces absurd mismatches.
battle = ROOT / "src/game/battle.ts"
text = battle.read_text(encoding="utf-8")
old = '''/**
 * Raid difficulty curve. v2.4 softens v2.1 by another ~14–16% and spaces
 * out extra attackers/elite classes while preserving long-term escalation.
 */
export function raidEnemyPower(s: Pick<GameState, "day" | "raids">): number {
  // Keep the forgiving early v2.4 curve, then add a gentle late-raid catch-up
  // so deeper progression does not trivialise the long game.
  return 4.8 + (s.day - 1) * 1.2 + s.raids * 2.25 + Math.max(0, s.raids - 2) * 0.65;
}

export function raidEnemyCount(s: Pick<GameState, "day" | "raids">): number {
  return Math.min(4, 1 + Math.floor((s.day - 1) / 5));
}
'''
new = '''/**
 * Raid composition still grows from one to four attackers, but raw day count no
 * longer decides whether a raid is trivial or impossible. Each attacker is
 * calibrated against the strongest ninja currently owned by the village.
 */
export const RAID_RELATIVE_MIN = 0.82;
export const RAID_RELATIVE_MAX = 1.18;

export function raidEnemyPower(s: Pick<GameState, "day" | "raids">): number {
  // Kept only as a template level for enemy class stat-shapes and rewards.
  return 4.8 + (s.day - 1) * 0.55 + s.raids * 0.65;
}

export function raidEnemyCount(s: Pick<GameState, "day" | "raids">): number {
  return Math.min(4, 1 + Math.floor((s.day - 1) / 5));
}

function raidHash(s: Pick<GameState, "day" | "raids" | "clan">, salt = 0): number {
  const str = `${s.day}|${s.raids}|${s.clan}|${salt}`;
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h / 4294967295;
}

/** One stable roll per raid, revealed once the attacking clan is known. */
export function raidRelativeMultiplier(s: Pick<GameState, "day" | "raids" | "clan">): number {
  return RAID_RELATIVE_MIN + raidHash(s) * (RAID_RELATIVE_MAX - RAID_RELATIVE_MIN);
}

export function strongestNinjaCombatPower(s: Pick<GameState, "ninjas">): number {
  if (!s.ninjas.length) return 1;
  return Math.max(...s.ninjas.map((n) => unitCombatPower(unitFromNinja(n))));
}

function scaleRaidEnemyToPower(u: Unit, targetPower: number): Unit {
  const scalable = ["maxHp", "atk", "def", "spd", "nin", "gen", "ken", "tac"] as const;
  for (let pass = 0; pass < 3; pass++) {
    const current = Math.max(1, unitCombatPower(u));
    const factor = clamp(targetPower / current, 0.45, 2.2);
    for (const k of scalable) u[k] *= factor;
    u.maxHp = Math.max(1, Math.round(u.maxHp));
    u.hp = u.maxHp;
  }
  u.level = Math.max(1, Math.round((u.atk + u.nin + u.ken) / 7));
  return u;
}
'''
if old not in text:
    raise SystemExit("raid scaling anchor not found")
text = text.replace(old, new, 1)
battle.write_text(text, encoding="utf-8")
print("relative raid scaling helpers: applied")

text = battle.read_text(encoding="utf-8")
start = text.index('export function raidForecast(s: GameState): {')
end = text.index('/** Start a promotion exam:', start)
replacement = r'''export function raidForecast(s: GameState): {
  enemyPower: number;
  enemyCount: number;
  enemyLevel: number;
  homePower: number;
  dailyThreat: number;
  daysUntil: number;
} {
  const count = raidEnemyCount(s);
  const strongest = strongestNinjaCombatPower(s);
  const relative = raidRelativeMultiplier(s);
  const enemyPower = strongest * relative * count;
  const homePower = raidDefenders(s.ninjas.filter((n) => n.status === "ready"))
    .map(unitFromNinja)
    .reduce((sum, u) => sum + unitCombatPower(u), 0);
  const strongestLevel = s.ninjas.length ? Math.max(...s.ninjas.map((n) => n.level)) : 1;
  const dailyThreat = raidThreatPerDay(s);
  return {
    enemyPower: Math.round(enemyPower),
    enemyCount: count,
    enemyLevel: strongestLevel,
    homePower,
    dailyThreat,
    daysUntil: s.raidGraceDays > 0 ? s.raidGraceDays + Math.max(0, Math.ceil((100 - s.threat) / Math.max(0.01, raidThreatPerDay({ ...s, raidGraceDays: 0 })))) : Math.max(0, Math.ceil((100 - s.threat) / Math.max(0.01, dailyThreat))),
  };
}

export function startBattle(s: GameState, defenders: Ninja[]): Battle {
  const templatePower = raidEnemyPower(s);
  // Preserve the player's selection/order. No automatic strongest-four swap.
  const chosenDefenders = defenders.slice(0, 4);
  const allies = chosenDefenders.map(unitFromNinja);
  // Will of Fire style team auras only count the shinobi actually defending.
  let teamAtk = 1;
  for (const n of chosenDefenders) teamAtk *= perkFx(n).allyAtk;
  if (teamAtk !== 1) for (const a of allies) a.atk *= teamAtk;

  const count = raidEnemyCount(s);
  const pool = raidClassPool(s);
  const kinds: string[] = [];
  for (let i = 0; i < count; i++) {
    if (i === count - 1 && s.raids >= 2 && count > 1) {
      kinds.push(s.raids >= 6 ? "dread_veteran" : "clan_captain");
    } else {
      kinds.push(pick(pool));
    }
  }

  const strongest = strongestNinjaCombatPower(s);
  const raidRoll = raidRelativeMultiplier(s);
  const foes = kinds.map((k, i) => {
    // Small per-attacker variation preserves class texture while the clamp guarantees
    // nobody leaves the user-requested strongest-ninja band.
    const micro = 0.96 + raidHash(s, i + 17) * 0.08;
    const relative = clamp(raidRoll * micro, RAID_RELATIVE_MIN, RAID_RELATIVE_MAX);
    return scaleRaidEnemyToPower(makeEnemy(i, k, templatePower), strongest * relative);
  });
  foes.forEach((f, i) => {
    if (kinds.filter((k) => k === f.kind).length > 1) f.name = `${f.name} ${String.fromCharCode(65 + i)}`;
  });

  const b: Battle = {
    round: 1,
    units: [...allies, ...foes],
    order: [],
    idx: 0,
    state: "choose",
    log: [{ t: `${s.clan} storms the gates! Raid roll: ${Math.round(raidRoll * 100)}% of your strongest ninja per attacker.`, kind: "info" }],
    clan: s.clan,
    gold: Math.round(45 + templatePower * 10 + count * 12),
    score: Math.round(90 + templatePower * 13 + count * 18),
    flash: null,
    acting: null,
    mode: "raid",
    examTargetRank: null,
  };
  rollOrder(b, s.b.tower + (s.techs.includes("tower_rapid_response") ? 1 : 0), true);
  return b;
}

'''
text = text[:start] + replacement + text[end:]
battle.write_text(text, encoding="utf-8")
print("raid forecast/start relative calibration: applied")

# 3) Make the newly-added rare orders and unique bloodlines realistically discoverable.
replace_once(
    "src/game/perks.ts",
    'id: "beast_sage", title: "Beast Sage", epithet: "of the Five Paths", color: "#79cf69", scoutable: true, scoutWeight: 0.07,',
    'id: "beast_sage", title: "Beast Sage", epithet: "of the Five Paths", color: "#79cf69", scoutable: true, scoutWeight: 0.55,',
    "Beast Sage scout visibility",
)
replace_once(
    "src/game/perks.ts",
    'id: "storm_caller", title: "Storm Caller", epithet: "of the Four Tempests", color: "#8bc8ff", scoutable: true, scoutWeight: 0.12,',
    'id: "storm_caller", title: "Storm Caller", epithet: "of the Four Tempests", color: "#8bc8ff", scoutable: true, scoutWeight: 0.65,',
    "Storm Caller scout visibility",
)
replace_once(
    "src/game/perks.ts",
    'id: "masked_assassin", title: "Masked Assassin", epithet: "of the Nine Faces", color: "#c9b2ff", scoutable: true, scoutWeight: 0.18,',
    'id: "masked_assassin", title: "Masked Assassin", epithet: "of the Nine Faces", color: "#c9b2ff", scoutable: true, scoutWeight: 0.75,',
    "Masked Assassin scout visibility",
)
replace_once(
    "src/game/engine.ts",
    '''    const uniqueChance = (pot >= 5 ? 0.025 : pot >= 4 ? 0.012 : pot >= 3 ? 0.004 : pot >= 2 ? 0.001 : 0)
      + (hasTech(s, "hall_elite_recruitment") ? 0.005 : 0);''',
    '''    const uniqueChance = (pot >= 5 ? 0.060 : pot >= 4 ? 0.035 : pot >= 3 ? 0.012 : pot >= 2 ? 0.003 : 0)
      + (hasTech(s, "hall_elite_recruitment") ? 0.010 : 0);''',
    "UNIQUE clan trait visibility",
)
replace_once(
    "src/game/engine.ts",
    '  if (Math.random() >= 0.14) return;',
    '  if (Math.random() >= 0.18) return;',
    "special mission visibility",
)
replace_once(
    "src/game/engine.ts",
    '  const d = pick(eligible); const spec = MISSION_SPEC[d.grade]; const scale = 1 + (s.day - 1) * 0.03; const req: Partial<Record<Skill, number>> = {};',
    '  const rareOrderIds = new Set(["beast_sage", "storm_caller", "masked_assassin", "gate_master", "seal_bearer"]);\n  const rareOrderDefs = eligible.filter((x) => x.reward.kind === "recruit" && rareOrderIds.has(x.reward.legendId));\n  const hasRareOrderMember = s.ninjas.some((n) => n.legend != null && rareOrderIds.has(n.legend));\n  // New rare-order characters were effectively invisible when all Special Missions shared one flat roll.\n  const weightedEligible = hasRareOrderMember ? [...eligible, ...rareOrderDefs] : [...eligible, ...rareOrderDefs, ...rareOrderDefs];\n  const d = pick(weightedEligible); const spec = MISSION_SPEC[d.grade]; const scale = 1 + (s.day - 1) * 0.03; const req: Partial<Record<Skill, number>> = {};',
    "rare-order special mission weighting",
)

# Cache marker used for field testing.
sw = ROOT / "public/sw.js"
sw_text = sw.read_text(encoding="utf-8")
sw_text, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-depth-v9-playtest-core";', sw_text, count=1)
if n != 1:
    raise SystemExit("service worker cache marker not found")
sw.write_text(sw_text, encoding="utf-8")

print("Village depth v9 core playtest pass applied")
