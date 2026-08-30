from pathlib import Path
import re

ROOT = Path('app')

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')

def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'{label} anchor missing')
    return text.replace(old, new, 1)

# ---------------------------------------------------------------------------
# Types: four advanced facilities + post-raid grace state.
# ---------------------------------------------------------------------------
p = 'src/game/types.ts'
s = read(p)
s = s.replace(
    'export type Bld = "hall" | "farm" | "tea" | "dojo" | "tower" | "shrine";',
    'export type Bld = "hall" | "farm" | "tea" | "dojo" | "tower" | "shrine" | "intel" | "anbu" | "hospital" | "embassy";'
)
if 'raidGraceDays: number;' not in s:
    s = replace_once(s, '  threat: number;\n', '  threat: number;\n  /** Days after a raid during which hostility cannot rise. */\n  raidGraceDays: number;\n', 'GameState threat')
write(p, s)

# ---------------------------------------------------------------------------
# Building catalogue: advanced facilities are expensive, prerequisite-gated.
# ---------------------------------------------------------------------------
p = 'src/game/content.ts'
s = read(p)
if 'requires?: { bld: Bld; level: number };' not in s:
    s = replace_once(
        s,
        '  color: string;\n}',
        '  color: string;\n  /** Optional prerequisite building for advanced facilities. */\n  requires?: { bld: Bld; level: number };\n}',
        'BldMeta'
    )
s = s.replace(
    'export const BUILD_ORDER: Bld[] = ["farm", "tea", "dojo", "tower", "shrine", "hall"];',
    'export const BUILD_ORDER: Bld[] = ["farm", "tea", "dojo", "tower", "shrine", "hall", "intel", "hospital", "embassy", "anbu"];'
)
if 'intel: {' not in s:
    anchor = '''  hall: {\n    name: "Main Hall", kanji: "影", color: "#e2452f",\n    desc: "+2 ninja cap · +1 action each day",\n    costs: [{ gold: 0, rice: 0 }, { gold: 120, rice: 10 }, { gold: 220, rice: 50 }],\n    max: 3, hotkey: "H",\n  },\n};'''
    replacement = '''  hall: {\n    name: "Main Hall", kanji: "影", color: "#e2452f",\n    desc: "+2 ninja cap · +1 action each day",\n    costs: [{ gold: 0, rice: 0 }, { gold: 120, rice: 10 }, { gold: 220, rice: 50 }],\n    max: 3, hotkey: "H",\n  },\n  intel: {\n    name: "Intelligence Bureau", kanji: "情", color: "#8fa7d8",\n    desc: "raid threat -8%/day per level · stronger security operations",\n    costs: [{ gold: 190, rice: 55 }, { gold: 330, rice: 95 }],\n    max: 2, hotkey: "I", requires: { bld: "tower", level: 2 },\n  },\n  hospital: {\n    name: "Advanced Hospital", kanji: "療", color: "#d99ab5",\n    desc: "injuries recover 1 day faster per level",\n    costs: [{ gold: 210, rice: 65 }, { gold: 370, rice: 120 }],\n    max: 2, hotkey: "M", requires: { bld: "shrine", level: 2 },\n  },\n  embassy: {\n    name: "Diplomacy Office", kanji: "盟", color: "#d3b46d",\n    desc: "raid threat -7%/day per level · +5% mission pay per level",\n    costs: [{ gold: 220, rice: 50 }, { gold: 395, rice: 100 }],\n    max: 2, hotkey: "E", requires: { bld: "tea", level: 2 },\n  },\n  anbu: {\n    name: "ANBU Headquarters", kanji: "暗", color: "#9c8bc2",\n    desc: "raid threat -10%/day per level · may intercept incoming raids",\n    costs: [{ gold: 280, rice: 85 }, { gold: 470, rice: 145 }],\n    max: 2, hotkey: "A", requires: { bld: "hall", level: 3 },\n  },\n};'''
    s = replace_once(s, anchor, replacement, 'BUILDINGS hall')
write(p, s)

# ---------------------------------------------------------------------------
# Shared security math used by engine and the visible raid forecast.
# ---------------------------------------------------------------------------
security_ts = '''import type { GameState } from "./types";\nimport { THREAT_PER_DAY } from "./content";\n\nconst clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));\n\n/** Multiplicative hostility growth after village defences and diplomacy. */\nexport function raidThreatMultiplier(s: Pick<GameState, "b" | "techs">): number {\n  let mult = s.techs.includes("tower_raid_forecast") ? 0.80 : 1;\n  mult *= 1 - s.b.tower * 0.03;\n  mult *= 1 - s.b.intel * 0.08;\n  mult *= 1 - s.b.anbu * 0.10;\n  mult *= 1 - s.b.embassy * 0.07;\n  return clamp(mult, 0.30, 1);\n}\n\nexport function raidThreatPerDay(s: Pick<GameState, "b" | "techs" | "raids" | "raidGraceDays">): number {\n  if (s.raidGraceDays > 0) return 0;\n  return THREAT_PER_DAY * (1 + s.raids * 0.05) * raidThreatMultiplier(s);\n}\n\n/** Active player action: border patrols, informants and ANBU sweeps. */\nexport function securityOperationReduction(s: Pick<GameState, "b">): number {\n  return 14 + s.b.tower * 5 + s.b.intel * 9 + s.b.anbu * 11 + s.b.embassy * 4;\n}\n\n/** Chance that village intelligence stops a raid before a full battle begins. */\nexport function raidInterceptChance(s: Pick<GameState, "b" | "techs">): number {\n  const sensorBonus = s.techs.includes("tower_sensor_corps") ? 0.08 : 0;\n  return clamp(s.b.anbu * 0.18 + s.b.intel * 0.06 + sensorBonus, 0, 0.52);\n}\n\nexport const SECURITY_OPERATION_COST = { gold: 30, rice: 12 };\n'''
write('src/game/villageSecurity.ts', security_ts)

# ---------------------------------------------------------------------------
# Engine: state migration shape, prerequisite buildings, mission pay,
# hospital recovery, active security operation, threat grace/interception.
# ---------------------------------------------------------------------------
p = 'src/game/engine.ts'
s = read(p)
if 'villageSecurity' not in '\n'.join(s.splitlines()[:20]):
    s = s.replace(
        'import { SPECIAL_BY_ID, SPECIAL_MISSIONS, specialRecipientEligible, specialRewardLabel } from "./specialMissionsV2";',
        'import { SPECIAL_BY_ID, SPECIAL_MISSIONS, specialRecipientEligible, specialRewardLabel } from "./specialMissionsV2";\nimport { raidInterceptChance, raidThreatPerDay, securityOperationReduction, SECURITY_OPERATION_COST } from "./villageSecurity";',
        1,
    )
# Threat math moved to villageSecurity.ts; keep strict noUnusedLocals clean.
s = s.replace('  THREAT_PER_DAY, TRAIT_IDS, TRAIT_META, TECH_BY_ID, nextRank, rankIndex,\n', '  TRAIT_IDS, TRAIT_META, TECH_BY_ID, nextRank, rankIndex,\n')
# Mission reward scaling at generation time.
s = s.replace(
    'gold: Math.round(ri(spec.gold[0], spec.gold[1]) * scale * 1.15), rice: Math.round(ri(spec.rice[0], spec.rice[1]) * scale * 1.15),',
    'gold: Math.round(ri(spec.gold[0], spec.gold[1]) * scale * 1.15 * (1 + s.b.embassy * 0.05)), rice: Math.round(ri(spec.rice[0], spec.rice[1]) * scale * 1.15 * (1 + s.b.embassy * 0.05)),'
)
s = s.replace(
    'gold: Math.round(ri(spec.gold[0], spec.gold[1]) * scale),\n    rice: Math.round(ri(spec.rice[0], spec.rice[1]) * scale),',
    'gold: Math.round(ri(spec.gold[0], spec.gold[1]) * scale * (1 + s.b.embassy * 0.05)),\n    rice: Math.round(ri(spec.rice[0], spec.rice[1]) * scale * (1 + s.b.embassy * 0.05)),'
)
# New state fields/building keys.
s = s.replace('    threat: 10,\n', '    threat: 10,\n    raidGraceDays: 0,\n', 1)
s = s.replace(
    '    b: { hall: 1, farm: 1, tea: 0, dojo: 0, tower: 0, shrine: 0 },',
    '    b: { hall: 1, farm: 1, tea: 0, dojo: 0, tower: 0, shrine: 0, intel: 0, anbu: 0, hospital: 0, embassy: 0 },'
)
# Advanced building prerequisites.
old = '''export function build(s: GameState, type: Bld, ev: Ev[]): boolean {\n  const meta = BUILDINGS[type];\n  const lvl = s.b[type];\n  if (lvl >= meta.max || s.ap < 1) return false;'''
new = '''export function build(s: GameState, type: Bld, ev: Ev[]): boolean {\n  const meta = BUILDINGS[type];\n  const lvl = s.b[type];\n  if (lvl >= meta.max || s.ap < 1) return false;\n  if (meta.requires && s.b[meta.requires.bld] < meta.requires.level) return false;'''
if old in s:
    s = s.replace(old, new, 1)
# Hospital trims injury duration on mission failure.
s = s.replace(
    'n.daysLeft = Math.max(1, d - Math.floor(s.b.shrine / 2) - (hasTech(s, "shrine_field_medicine") ? 1 : 0));',
    'n.daysLeft = Math.max(1, d - Math.floor(s.b.shrine / 2) - s.b.hospital - (hasTech(s, "shrine_field_medicine") ? 1 : 0));'
)
# Security operation function before scout.
if 'export function securityOperation' not in s:
    anchor = '/** Spend an action to bring three hopefuls to the gate. */'
    fn = '''/** Spend an action and supplies to deliberately lower raid hostility. */\nexport function securityOperation(s: GameState, ev: Ev[]): boolean {\n  const securityLevel = s.b.tower + s.b.intel + s.b.anbu + s.b.embassy;\n  if (securityLevel <= 0 || s.ap < 1 || s.threat <= 0) return false;\n  if (s.gold < SECURITY_OPERATION_COST.gold || s.rice < SECURITY_OPERATION_COST.rice) return false;\n  const before = s.threat;\n  const reduction = Math.min(before, securityOperationReduction(s));\n  s.gold -= SECURITY_OPERATION_COST.gold;\n  s.rice -= SECURITY_OPERATION_COST.rice;\n  s.ap -= 1;\n  s.threat = Math.max(0, s.threat - reduction);\n  ev.push({ type: "security_operation", reduction: Math.round(reduction), before: Math.round(before), after: Math.round(s.threat) });\n  pushLog(s, `Border security operation lowered raid threat by ${Math.round(reduction)}%.`, "good");\n  return true;\n}\n\n'''
    s = replace_once(s, anchor, fn + anchor, 'scout comment')
# Post-raid grace + new daily threat formula + ANBU interception.
old_threat = '''  // 7. threat & raids\n  s.threat += THREAT_PER_DAY * (1 + s.raids * 0.05) * (hasTech(s, "tower_raid_forecast") ? 0.80 : 1);\n  if (s.threat >= 100) {\n    s.threat = 0;\n    s.clan = pick(CLANS);'''
new_threat = '''  // 7. threat & raids\n  if (s.raidGraceDays > 0) {\n    s.raidGraceDays = Math.max(0, s.raidGraceDays - 1);\n  } else {\n    s.threat += raidThreatPerDay(s);\n  }\n  if (s.threat >= 100) {\n    const intercept = raidInterceptChance(s);\n    if (intercept > 0 && Math.random() < intercept) {\n      s.threat = 55;\n      ev.push({ type: "raid_intercepted", chance: intercept });\n      pushLog(s, `Intelligence teams intercepted the incoming raid before it reached the village. Threat reset to 55%.`, "great");\n      return false;\n    }\n    s.threat = 0;\n    s.clan = pick(CLANS);'''
if old_threat in s:
    s = s.replace(old_threat, new_threat, 1)
else:
    raise SystemExit('threat block anchor missing')
write(p, s)

# ---------------------------------------------------------------------------
# Battle: hospital injury mitigation + two/three day post-raid protection.
# ---------------------------------------------------------------------------
p = 'src/game/battle.ts'
s = read(p)
s = s.replace(
    'n.daysLeft = Math.max(1, 2 - Math.floor(s.b.shrine / 2) - (n.traits.includes("stoic") ? 1 : 0) - (s.techs.includes("shrine_field_medicine") ? 1 : 0));',
    'n.daysLeft = Math.max(1, 2 - Math.floor(s.b.shrine / 2) - s.b.hospital - (n.traits.includes("stoic") ? 1 : 0) - (s.techs.includes("shrine_field_medicine") ? 1 : 0));'
)
s = s.replace('    s.threat = 5;\n    ev.push({ type: "raid_win"', '    s.threat = 5;\n    s.raidGraceDays = 3;\n    ev.push({ type: "raid_win"', 1)
s = s.replace('    s.threat = 25;\n    ev.push({', '    s.threat = 25;\n    s.raidGraceDays = 2;\n    ev.push({', 1)
# Visible forecast uses same threat formula and accounts for grace days.
if 'raidThreatPerDay' not in '\n'.join(s.splitlines()[:15]):
    s = s.replace('import { JUTSU_BY_ID, type JutsuDef } from "./jutsu";', 'import { JUTSU_BY_ID, type JutsuDef } from "./jutsu";\nimport { raidThreatPerDay } from "./villageSecurity";', 1)
s = s.replace(
    '  const dailyThreat = 19 * (1 + s.raids * 0.05);',
    '  const dailyThreat = raidThreatPerDay(s);'
)
s = s.replace(
    '    daysUntil: Math.max(0, Math.ceil((100 - s.threat) / dailyThreat)),',
    '    daysUntil: s.raidGraceDays > 0 ? s.raidGraceDays + Math.max(0, Math.ceil((100 - s.threat) / Math.max(0.01, raidThreatPerDay({ ...s, raidGraceDays: 0 })))) : Math.max(0, Math.ceil((100 - s.threat) / Math.max(0.01, dailyThreat))),'
)
write(p, s)

# ---------------------------------------------------------------------------
# Save normalisation keeps current three slots compatible.
# ---------------------------------------------------------------------------
p = 'src/game/save.ts'
s = read(p)
if 'state.b.intel' not in s:
    anchor = '    if (!Array.isArray(state.techs)) state.techs = [];\n'
    add = '''    if (!state.b) state.b = { hall: 1, farm: 1, tea: 0, dojo: 0, tower: 0, shrine: 0, intel: 0, anbu: 0, hospital: 0, embassy: 0 };\n    if (typeof state.b.intel !== "number") state.b.intel = 0;\n    if (typeof state.b.anbu !== "number") state.b.anbu = 0;\n    if (typeof state.b.hospital !== "number") state.b.hospital = 0;\n    if (typeof state.b.embassy !== "number") state.b.embassy = 0;\n    if (typeof state.raidGraceDays !== "number") state.raidGraceDays = 0;\n    if (!Array.isArray(state.techs)) state.techs = [];\n'''
    s = replace_once(s, anchor, add, 'save techs')
write(p, s)

# ---------------------------------------------------------------------------
# Build UI: prerequisites + active Border Security Operation.
# ---------------------------------------------------------------------------
p = 'src/components/BuildMenu.tsx'
s = read(p)
s = s.replace('                if (s.b[branch] <= 0) return null;', '                if (s.b[branch] <= 0 || techs.length === 0) return null;')
if 'villageSecurity' not in '\n'.join(s.splitlines()[:12]):
    s = s.replace('import { cn } from "../utils/cn";', 'import { cn } from "../utils/cn";\nimport { securityOperationReduction, SECURITY_OPERATION_COST } from "../game/villageSecurity";', 1)
s = s.replace('  onResearch,\n}: {', '  onResearch,\n  onSecurity,\n}: {', 1)
s = s.replace('  onResearch: (id: VillageTechId, r: DOMRect) => void;\n}) {', '  onResearch: (id: VillageTechId, r: DOMRect) => void;\n  onSecurity: (r: DOMRect) => void;\n}) {', 1)
# Prereq-aware build cards.
s = s.replace(
    '            const afford = cost ? s.gold >= cost.gold && s.rice >= cost.rice : false;',
    '            const afford = cost ? s.gold >= cost.gold && s.rice >= cost.rice : false;\n            const reqOk = !meta.requires || s.b[meta.requires.bld] >= meta.requires.level;'
)
s = s.replace(
    '<p className="truncate text-[9.5px] font-medium text-paper/45">{meta.desc}</p>',
    '<p className="truncate text-[9.5px] font-medium text-paper/45">{meta.desc}</p>\n                  {!reqOk && meta.requires && <p className="mt-0.5 text-[8px] font-bold text-[#ff8f7a]">Requires {BUILDINGS[meta.requires.bld].name} Lv {meta.requires.level}</p>}'
)
s = s.replace(
    'disabled={maxed || !afford}',
    'disabled={maxed || !afford || !reqOk || s.ap < 1}',
    1,
)
s = s.replace(
    '{maxed ? "MAX" : lvl === 0 ? "BUILD" : "UPGRADE"}',
    '{maxed ? "MAX" : !reqOk ? "LOCKED" : lvl === 0 ? "BUILD" : "UPGRADE"}',
    1,
)
# Security operation card before repair.
if 'Border Security Operation' not in s:
    marker = '          {/* repair */}'
    card = '''          {/* active raid prevention */}\n          {(() => {\n            const securityLevel = s.b.tower + s.b.intel + s.b.anbu + s.b.embassy;\n            const reduction = Math.min(s.threat, securityOperationReduction(s));\n            const afford = s.gold >= SECURITY_OPERATION_COST.gold && s.rice >= SECURITY_OPERATION_COST.rice;\n            const ok = securityLevel > 0 && s.ap >= 1 && s.threat > 0 && afford;\n            return (\n              <article className="col-span-full flex items-center gap-2 rounded-lg bg-black/25 p-1.5 ring-1 ring-inset ring-white/5">\n                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-gradient-to-b from-[#8fa7d8] to-[#4f567d] font-display text-[16px] font-black text-[#11131c]">防</span>\n                <div className="min-w-0 flex-1">\n                  <span className="block truncate text-[11.5px] font-bold text-paper/90">Border Security Operation</span>\n                  <p className="text-[9.5px] font-medium text-paper/45">Spend 1 action to cut current threat by up to {Math.round(reduction)}% · stronger with Watchtower / Intelligence / ANBU.</p>\n                  <p className="mt-0.5 text-[9px] font-bold text-paper/35">{SECURITY_OPERATION_COST.gold} gold · {SECURITY_OPERATION_COST.rice} rice</p>\n                </div>\n                <button disabled={!ok} onClick={(e) => onSecurity(e.currentTarget.getBoundingClientRect())} className="btn-ink h-8 w-[68px] shrink-0 rounded-lg text-[9px] font-black tracking-wide">SECURE</button>\n              </article>\n            );\n          })()}\n\n'''
    s = replace_once(s, marker, card + marker, 'repair marker')
write(p, s)

# ---------------------------------------------------------------------------
# Scene: show the advanced facilities and honest reduced threat/grace forecast.
# ---------------------------------------------------------------------------
p = 'src/components/Scene.tsx'
s = read(p)
s = s.replace(
    'const DISPLAY_ORDER = ["tea", "farm", "hall", "dojo", "tower", "shrine"] as const;',
    'const DISPLAY_ORDER = ["tea", "farm", "hall", "dojo", "tower", "shrine", "intel", "hospital", "embassy", "anbu"] as const;'
)
s = s.replace(
    '<p>+{raid.dailyThreat.toFixed(0)}%/day · {raid.daysUntil === 0 ? "RAID NEXT" : `${raid.daysUntil}d`}</p>',
    '<p>{s.raidGraceDays > 0 ? `PROTECTED ${s.raidGraceDays}d` : `+${raid.dailyThreat.toFixed(1)}%/day`} · {raid.daysUntil === 0 ? "RAID NEXT" : `${raid.daysUntil}d`}</p>'
)
s = s.replace(
    'className={cn("building pop-in", t === "hall" && "scale-110")}',
    'className={cn("building pop-in", t === "hall" && "scale-110", ["intel", "hospital", "embassy", "anbu"].includes(t) && "scale-[0.78] origin-bottom")}'
)
s = s.replace('gap-2 px-2 sm:gap-3', 'gap-1 px-1 sm:gap-2')
write(p, s)

# ---------------------------------------------------------------------------
# App handler wiring for active security operation.
# ---------------------------------------------------------------------------
p = 'src/App.tsx'
s = read(p)
if 'const doSecurity' not in s:
    anchor = '  const doRepair = (r?: DOMRect) => {'
    handler = '''  const doSecurity = (r?: DOMRect) => {\n    const st = sRef.current;\n    if (st.ap < 1) return noAp();\n    const evs: Ev[] = [];\n    if (eng.securityOperation(st, evs)) {\n      const rect = r ?? fallbackRect();\n      audio.dispatch();\n      fx.burst(rect.left + rect.width / 2, rect.top + rect.height / 2, "spark", 10);\n      fx.shake(2);\n    } else {\n      audio.click();\n      fx.shake(2);\n    }\n    handleEvs(evs);\n    force();\n  };\n\n'''
    s = replace_once(s, anchor, handler + anchor, 'doRepair')
s = s.replace(
    '<BuildMenu s={s} className={cn(tab !== "build" && "max-lg:hidden")} onBuild={doBuild} onRepair={doRepair} onResearch={doResearch} />',
    '<BuildMenu s={s} className={cn(tab !== "build" && "max-lg:hidden")} onBuild={doBuild} onRepair={doRepair} onResearch={doResearch} onSecurity={doSecurity} />'
)
write(p, s)

# ---------------------------------------------------------------------------
# Cache bump so mobile installs receive this village layer immediately.
# ---------------------------------------------------------------------------
p = 'public/sw.js'
s = read(p)
s, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-depth-v5-infrastructure-threat";', s, count=1)
if n != 1:
    raise SystemExit('service worker cache anchor missing')
write(p, s)

print('Village depth v5: advanced facilities + threat control + raid grace/interception applied')
