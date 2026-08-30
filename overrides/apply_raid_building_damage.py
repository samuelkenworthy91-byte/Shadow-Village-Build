from pathlib import Path


def replace_once(path: Path, old: str, new: str):
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'Expected snippet not found in {path}: {old[:120]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

battle = Path('app/src/game/battle.ts')
engine = Path('app/src/game/engine.ts')
app = Path('app/src/App.tsx')
sw = Path('app/public/sw.js')

replace_once(
    battle,
    'import type { BAction, Battle, GameState, Ninja, Unit } from "./types";',
    'import type { BAction, Battle, Bld, GameState, Ninja, Unit } from "./types";'
)
replace_once(
    battle,
    'import { ENEMY_KINDS, NATURE_META, RANK_META, SKILLS, rankIndex } from "./content";',
    'import { BUILDINGS, ENEMY_KINDS, NATURE_META, RANK_META, SKILLS, rankIndex } from "./content";'
)
replace_once(
    battle,
    'const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));\n',
    '''const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));\n\nfunction damageRandomRaidBuilding(s: GameState): { name: string; level: number } | null {\n  const candidates = (Object.keys(s.b) as Bld[]).filter((id) => s.b[id] > 0);\n  if (candidates.length === 0) return null;\n  const id = pick(candidates);\n  s.b[id] = Math.max(0, s.b[id] - 1);\n  return { name: BUILDINGS[id].name, level: s.b[id] };\n}\n'''
)
replace_once(
    battle,
    '''  } else {\n    const dmg = 1 + (b.round <= 2 ? 1 : 0);\n    s.hp = Math.max(0, s.hp - dmg);\n    s.threat = 25;\n    ev.push({ type: "raid_loss", clan: b.clan, dmg });\n    if (s.hp <= 0) {\n''',
    '''  } else {\n    const dmg = 1 + (b.round <= 2 ? 1 : 0);\n    const damagedBuilding = damageRandomRaidBuilding(s);\n    s.hp = Math.max(0, s.hp - dmg);\n    s.threat = 25;\n    ev.push({\n      type: "raid_loss",\n      clan: b.clan,\n      dmg,\n      building: damagedBuilding?.name,\n      buildingLevel: damagedBuilding?.level,\n    });\n    if (damagedBuilding) {\n      s.log.push({\n        txt: `${damagedBuilding.name} was damaged in the raid and fell to level ${damagedBuilding.level}.`,\n        kind: "bad",\n        id: Date.now() + 1,\n      });\n    }\n    if (s.hp <= 0) {\n'''
)

replace_once(
    engine,
    'export const hasTech = (s: Pick<GameState, "techs">, id: VillageTechId) => s.techs.includes(id);\n',
    '''export const hasTech = (s: Pick<GameState, "techs">, id: VillageTechId) => s.techs.includes(id);\n\nfunction damageRandomRaidBuilding(s: GameState): { name: string; level: number } | null {\n  const candidates = (Object.keys(s.b) as Bld[]).filter((id) => s.b[id] > 0);\n  if (candidates.length === 0) return null;\n  const id = pick(candidates);\n  s.b[id] = Math.max(0, s.b[id] - 1);\n  return { name: BUILDINGS[id].name, level: s.b[id] };\n}\n'''
)
replace_once(
    engine,
    '''    if (defenders.length === 0) {\n      // nobody home — the village eats the hit\n      s.hp = Math.max(0, s.hp - 2);\n      ev.push({ type: "raid_undefended", clan: s.clan });\n      pushLog(s, `${s.clan} struck an undefended village! −2 ♥`, "bad");\n      if (s.hp <= 0) {\n''',
    '''    if (defenders.length === 0) {\n      // nobody home — the village eats the hit and one standing building loses a level\n      const damagedBuilding = damageRandomRaidBuilding(s);\n      s.hp = Math.max(0, s.hp - 2);\n      ev.push({\n        type: "raid_undefended",\n        clan: s.clan,\n        dmg: 2,\n        building: damagedBuilding?.name,\n        buildingLevel: damagedBuilding?.level,\n      });\n      pushLog(s, `${s.clan} struck an undefended village! −2 ♥`, "bad");\n      if (damagedBuilding) {\n        pushLog(s, `${damagedBuilding.name} was damaged in the raid and fell to level ${damagedBuilding.level}.`, "bad");\n      }\n      if (s.hp <= 0) {\n'''
)

replace_once(
    app,
    '''          floater(48, 30, `−${e.dmg ?? 2} ♥  BREACH!`, "bad");\n          break;\n''',
    '''          floater(48, 30, `−${e.dmg ?? 2} ♥  BREACH!`, "bad");\n          if (e.building) {\n            floater(48, 36, `${e.building} DAMAGED → LV ${e.buildingLevel}`, "bad");\n          }\n          break;\n'''
)

text = sw.read_text(encoding='utf-8')
old_cache = 'shadow-village-equipment-gacha-v2-400gear-v3-reveal'
new_cache = 'shadow-village-equipment-gacha-v2-400gear-v4-raid-damage'
if old_cache not in text:
    raise SystemExit('Expected service-worker cache key not found')
sw.write_text(text.replace(old_cache, new_cache, 1), encoding='utf-8')

print('Applied failed-raid building downgrade and raid damage reporting.')
