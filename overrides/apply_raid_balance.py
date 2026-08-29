from pathlib import Path

ROOT = Path('.')

def replace_once(path: Path, old: str, new: str, label: str):
    text = path.read_text()
    if new in text:
        print(f'{label}: already applied')
        return
    if old not in text:
        raise SystemExit(f'{label}: expected source block not found in {path}')
    path.write_text(text.replace(old, new, 1))
    print(f'{label}: applied')

# ---------- battle.ts ----------
p = ROOT / 'src/game/battle.ts'
text = p.read_text()
if 'export function makeEnemy' not in text:
    if 'function makeEnemy(i: number, kind: string, power: number): Unit {' not in text:
        raise SystemExit('battle makeEnemy block not found')
    text = text.replace('function makeEnemy(i: number, kind: string, power: number): Unit {', 'export function makeEnemy(i: number, kind: string, power: number): Unit {', 1)
    p.write_text(text)

old = '''export function startBattle(s: GameState, defenders: Ninja[]): Battle {
  const power = 6 + (s.day - 1) * 1.6 + s.raids * 3.2;
  const allies = defenders.slice(0, 4).map(unitFromNinja);
  // Will of Fire style team auras
  let teamAtk = 1;
  for (const n of defenders) teamAtk *= perkFx(n).allyAtk;
  if (teamAtk !== 1) for (const a of allies) a.atk *= teamAtk;

  const count = Math.min(4, 1 + Math.floor(s.day / 4) + (s.raids > 2 ? 1 : 0));
  const kinds: string[] = [];
'''
new = '''/**
 * Raid difficulty curve. v2.1 trims the old curve by roughly 10–15% without
 * flattening progression: raids still grow with days survived and raid wins.
 */
export function raidEnemyPower(s: Pick<GameState, "day" | "raids">): number {
  return 5.5 + (s.day - 1) * 1.4 + s.raids * 2.7;
}

export function raidEnemyCount(s: Pick<GameState, "day" | "raids">): number {
  return Math.min(4, 1 + Math.floor(s.day / 4) + (s.raids > 2 ? 1 : 0));
}

/** A comparable score used only for raid intel and automatic defender choice. */
export function unitCombatPower(u: Unit): number {
  return Math.round(
    u.maxHp +
    u.atk * 8 +
    u.def * 5 +
    u.spd * 2 +
    u.nin * 2 +
    u.gen * 2 +
    u.crit * 100 +
    u.dodge * 100
  );
}

/** Raids now take the four strongest available home defenders, not recruit order. */
export function raidDefenders(defenders: Ninja[]): Ninja[] {
  return [...defenders]
    .sort((a, b) => unitCombatPower(unitFromNinja(b)) - unitCombatPower(unitFromNinja(a)))
    .slice(0, 4);
}

export function raidForecast(s: GameState): {
  enemyPower: number;
  enemyCount: number;
  enemyLevel: number;
  homePower: number;
  dailyThreat: number;
  daysUntil: number;
} {
  const power = raidEnemyPower(s);
  const count = raidEnemyCount(s);
  const boss = s.raids >= 1 && count > 1;
  let enemyPower = 0;
  for (let i = 0; i < count; i++) {
    if (boss && i === count - 1) {
      enemyPower += unitCombatPower(makeEnemy(i, "boss", power));
    } else {
      const avg = ["grunt", "brute", "shadow"]
        .map((kind) => unitCombatPower(makeEnemy(i, kind, power)))
        .reduce((a, b) => a + b, 0) / 3;
      enemyPower += avg;
    }
  }
  const homePower = raidDefenders(s.ninjas.filter((n) => n.status === "ready"))
    .map(unitFromNinja)
    .reduce((sum, u) => sum + unitCombatPower(u), 0);
  const dailyThreat = 19 * (1 + s.raids * 0.05);
  return {
    enemyPower: Math.round(enemyPower),
    enemyCount: count,
    enemyLevel: Math.max(1, Math.round(power / 3)),
    homePower,
    dailyThreat,
    daysUntil: Math.max(0, Math.ceil((100 - s.threat) / dailyThreat)),
  };
}

export function startBattle(s: GameState, defenders: Ninja[]): Battle {
  const power = raidEnemyPower(s);
  const chosenDefenders = raidDefenders(defenders);
  const allies = chosenDefenders.map(unitFromNinja);
  // Will of Fire style team auras only count the shinobi actually defending.
  let teamAtk = 1;
  for (const n of chosenDefenders) teamAtk *= perkFx(n).allyAtk;
  if (teamAtk !== 1) for (const a of allies) a.atk *= teamAtk;

  const count = raidEnemyCount(s);
  const kinds: string[] = [];
'''
replace_once(p, old, new, 'battle difficulty + forecast')

# ---------- Scene.tsx ----------
p = ROOT / 'src/components/Scene.tsx'
replace_once(
    p,
    'import { BUILDINGS } from "../game/content";\n',
    'import { BUILDINGS } from "../game/content";\nimport { raidForecast } from "../game/battle";\n',
    'scene forecast import',
)
replace_once(
    p,
    '  const danger = s.threat >= 80;\n',
    '  const danger = s.threat >= 80;\n  const raid = raidForecast(s);\n  const raidRatio = raid.enemyPower > 0 ? raid.homePower / raid.enemyPower : 0;\n  const raidTone = raid.homePower === 0 ? "text-[#ff6a6f]" : raidRatio >= 1.15 ? "text-jade" : raidRatio >= 0.9 ? "text-gold" : "text-[#ff7a5c]";\n',
    'scene forecast data',
)
old = '''      {/* threat */}
      <div className="absolute right-2.5 top-2.5 flex items-center gap-1.5">
        <span className={cn("font-display text-[11px] font-bold", danger ? "text-[#ff7a5c]" : "text-paper/60")}>襲</span>
        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-black/50 ring-1 ring-white/10 sm:w-28">
          <div
            className={cn("h-full rounded-full transition-[width] duration-500", danger ? "bg-gradient-to-r from-[#e2452f] to-[#ff7a5c]" : "bg-[#7a6a9e]")}
            style={{ width: `${Math.min(100, s.threat)}%` }}
          />
        </div>
        {danger && <span className="animate-pulse text-[9px] font-bold tracking-widest text-[#ff7a5c]">RAID</span>}
      </div>
'''
new = '''      {/* threat + transparent raid intel */}
      <div className="absolute right-2.5 top-2.5 flex flex-col items-end gap-1">
        <div className="flex items-center gap-1.5 rounded-md bg-black/35 px-1.5 py-1 backdrop-blur-sm ring-1 ring-white/10">
          <span className={cn("font-display text-[11px] font-bold", danger ? "text-[#ff7a5c]" : "text-paper/60")}>襲</span>
          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-black/50 ring-1 ring-white/10 sm:w-24">
            <div
              className={cn("h-full rounded-full transition-[width] duration-500", danger ? "bg-gradient-to-r from-[#e2452f] to-[#ff7a5c]" : "bg-[#7a6a9e]")}
              style={{ width: `${Math.min(100, s.threat)}%` }}
            />
          </div>
          <span className={cn("min-w-[30px] text-right text-[9px] font-black tabular-nums", danger ? "text-[#ff7a5c]" : "text-paper/70")}>
            {Math.round(s.threat)}%
          </span>
        </div>
        <div className="rounded-md bg-black/45 px-2 py-1 text-right text-[8px] font-bold leading-[1.25] text-paper/60 backdrop-blur-sm ring-1 ring-white/8">
          <p>+{raid.dailyThreat.toFixed(0)}%/day · {raid.daysUntil === 0 ? "RAID NEXT" : `${raid.daysUntil}d`}</p>
          <p>{raid.enemyCount} raider{raid.enemyCount === 1 ? "" : "s"} · ~Lv {raid.enemyLevel}</p>
          <p className="tabular-nums">HOME <span className={raidTone}>{raid.homePower.toLocaleString()}</span> / RAID ~{raid.enemyPower.toLocaleString()}</p>
        </div>
      </div>
'''
replace_once(p, old, new, 'scene raid intel UI')

# ---------- BattleScreen.tsx ----------
p = ROOT / 'src/components/BattleScreen.tsx'
replace_once(
    p,
    'import { COSTS, actionLabel, aliveAllies, aliveFoes, canUse, currentUnit } from "../game/battle";\n',
    'import { COSTS, actionLabel, aliveAllies, aliveFoes, canUse, currentUnit, unitCombatPower } from "../game/battle";\n',
    'battle screen power import',
)
replace_once(
    p,
    '  const flash = b.flash;\n',
    '  const flash = b.flash;\n  const homePower = allies.filter((u) => u.alive).reduce((sum, u) => sum + unitCombatPower(u), 0);\n  const raidPower = foes.filter((u) => u.alive).reduce((sum, u) => sum + unitCombatPower(u), 0);\n',
    'battle screen live power data',
)
replace_once(
    p,
    '          <span className="rounded-md bg-black/40 px-2 py-1 text-[10px] font-black tabular-nums text-gold">ROUND {b.round}</span>\n',
    '          <div className="hidden items-center gap-1.5 text-[9px] font-black tabular-nums sm:flex">\n            <span className="rounded-md bg-black/40 px-2 py-1 text-jade">HOME {homePower.toLocaleString()}</span>\n            <span className="text-paper/25">VS</span>\n            <span className="rounded-md bg-black/40 px-2 py-1 text-[#ff7a5c]">RAID {raidPower.toLocaleString()}</span>\n          </div>\n          <span className="rounded-md bg-black/40 px-2 py-1 text-[10px] font-black tabular-nums text-gold">ROUND {b.round}</span>\n',
    'battle screen power header',
)
replace_once(
    p,
    '                  <p className="truncate text-center text-[8.5px] font-bold text-paper/70">{u.name}</p>\n                  <Bar v={u.hp} max={u.maxHp} color="#e2452f" />\n',
    '                  <p className="truncate text-center text-[8.5px] font-bold text-paper/70">{u.name} · Lv {u.level}</p>\n                  <Bar v={u.hp} max={u.maxHp} color="#e2452f" />\n                  <p className="mt-[2px] text-center text-[7.5px] font-bold tabular-nums text-paper/45">{Math.max(0, u.hp)}/{u.maxHp} HP</p>\n',
    'battle screen enemy numbers',
)

print('raid balance patch complete')
