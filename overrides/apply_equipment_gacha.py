from pathlib import Path
import re
import shutil

ROOT = Path('app')
SRC = Path('overrides/equipment')


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel: str, value: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding='utf-8')


def copy(rel: str) -> None:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f'{rel}: copied')


copy('src/game/equipment.ts')
copy('src/components/EquipmentScreen.tsx')
copy('src/components/NinjaEquipment.tsx')

# Effective skill values include flat bonuses from all four slots.
# The live game signature is effSkill(GameState, Ninja, Skill).
p = 'src/game/engine.ts'
s = read(p)
if 'equipmentSkillBonus' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith('import ')), default=0)
    lines.insert(insert_at, 'import { equipmentSkillBonus } from "./equipment";')
    s = '\n'.join(lines) + ('\n' if read(p).endswith('\n') else '')
    if 'export function effSkill' in s:
        s = s.replace('export function effSkill', 'function baseEffSkill', 1)
    elif 'export const effSkill' in s:
        s = s.replace('export const effSkill', 'const baseEffSkill', 1)
    else:
        raise SystemExit('engine equipment stats: effSkill export not found')
    s += '\n\nexport function effSkill(s: GameState, n: Ninja, k: Skill): number {\n  return baseEffSkill(s, n, k) + equipmentSkillBonus(n, k);\n}\n'
    write(p, s)
    print('engine equipment stats: applied')
else:
    print('engine equipment stats: already applied')

# Battle units inherit flat skill boosts before the normal stat formulas run, then passive gear multipliers.
p = 'src/game/battle.ts'
s = read(p)
if 'applyEquipmentToBattleUnit' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith('import ')), default=0)
    lines.insert(insert_at, 'import { applyEquipmentToBattleUnit, equipmentSkillBonus } from "./equipment";')
    s = '\n'.join(lines) + ('\n' if read(p).endswith('\n') else '')
    if 'export function unitFromNinja' in s:
        s = s.replace('export function unitFromNinja', 'function baseUnitFromNinja', 1)
    elif 'export const unitFromNinja' in s:
        s = s.replace('export const unitFromNinja', 'const baseUnitFromNinja', 1)
    else:
        raise SystemExit('battle equipment wrapper: unitFromNinja export not found')
    s += '''\n\nexport function unitFromNinja(n: Ninja): Unit {\n  const equipped = { ...n, s: { ...n.s } };\n  const gearSkills = ["nin", "tai", "gen", "ste", "med", "spd", "ken", "doj", "tac"] as const;\n  for (const k of gearSkills) equipped.s[k] += equipmentSkillBonus(n, k);\n  return applyEquipmentToBattleUnit(n, baseUnitFromNinja(equipped)) as Unit;\n}\n'''
    write(p, s)
    print('battle equipment wrapper: applied')
else:
    print('battle equipment wrapper: already applied')

# Bridge generated gear techniques into the existing 奥義/special-action resolver.
p = 'src/game/perks.ts'
s = read(p)
if 'equipmentAbilityPerk' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith('import ')), default=0)
    lines.insert(insert_at, 'import { equipmentAbilityPerk } from "./equipment";')
    s = '\n'.join(lines) + ('\n' if read(p).endswith('\n') else '')
    if 'export function perkById' in s:
        s = s.replace('export function perkById', 'function basePerkById', 1)
        s += '\n\nexport function perkById(id: string): any {\n  return basePerkById(id) ?? equipmentAbilityPerk(id);\n}\n'
    elif 'export const perkById' in s:
        s = s.replace('export const perkById', 'const basePerkById', 1)
        s += '\n\nexport const perkById = (id: string): any => basePerkById(id) ?? equipmentAbilityPerk(id);\n'
    else:
        raise SystemExit('equipment technique bridge: perkById not found')
    write(p, s)
    print('equipment technique bridge: applied')
else:
    print('equipment technique bridge: already applied')

# Ninja detail portrait becomes the entry point into a large-art equipment loadout.
p = 'src/components/NinjaDetail.tsx'
s = read(p)
if 'NinjaEquipment' not in s:
    if 'import NinjaSprite from "./NinjaSprite";' not in s:
        raise SystemExit('ninja equipment import: NinjaSprite import not found')
    s = s.replace('import NinjaSprite from "./NinjaSprite";', 'import NinjaSprite from "./NinjaSprite";\nimport NinjaEquipment from "./NinjaEquipment";', 1)

    # Add an immediate persistence callback to the component API.
    s = s.replace('  onPerk,\n}: {', '  onPerk,\n  onEquipmentChanged,\n}: {', 1)
    s = s.replace('  onPerk: (id: string, r: DOMRect) => void;\n}) {', '  onPerk: (id: string, r: DOMRect) => void;\n  onEquipmentChanged: () => void;\n}) {', 1)

    state_anchor = re.search(r'(const \[confirmSpend, setConfirmSpend\][\s\S]*?= useState<[\s\S]*?>\(null\);)', s)
    if state_anchor:
        block = state_anchor.group(1)
        s = s.replace(block, block + '\n  const [showEquipment, setShowEquipment] = useState(false);', 1)
    else:
        anchor = '  const n = s.ninjas.find((x) => x.id === ninjaId);'
        if anchor not in s:
            raise SystemExit('ninja equipment state: ninja lookup not found')
        s = s.replace(anchor, '  const [showEquipment, setShowEquipment] = useState(false);\n' + anchor, 1)

    sprite = re.search(r'<NinjaSprite\b[\s\S]*?/>', s)
    if not sprite:
        raise SystemExit('ninja equipment portrait: NinjaSprite JSX not found')
    wrapped = '<button type="button" onClick={() => setShowEquipment(true)} className="group relative rounded-xl transition active:scale-[0.99]" aria-label="Open equipment loadout">\n' + sprite.group(0) + '\n<span className="pointer-events-none absolute inset-x-1 bottom-1 rounded bg-black/65 px-1.5 py-1 text-center text-[7.5px] font-black tracking-[0.12em] text-gold/85 opacity-90 ring-1 ring-white/10">TAP FOR EQUIPMENT</span>\n</button>'
    s = s[:sprite.start()] + wrapped + s[sprite.end():]

    modal_anchor = '        {confirmSpend && (() => {'
    if modal_anchor not in s:
        raise SystemExit('ninja equipment modal: point-spend modal anchor not found')
    s = s.replace(modal_anchor, '        {showEquipment && <NinjaEquipment s={s} n={n} onChanged={onEquipmentChanged} onClose={() => setShowEquipment(false)} />}\n\n' + modal_anchor, 1)
    write(p, s)
    print('ninja portrait equipment entry: applied')
else:
    print('ninja portrait equipment entry: already applied')

# Add Equipment as a real fourth responsive tab. The existing desktop layout shows
# the three management panels simultaneously, so selecting Equipment temporarily
# replaces that grid with the full equipment/inventory screen.
p = 'src/App.tsx'
s = read(p)
if 'EquipmentScreen' not in s:
    if 'import NinjaDetail from "./components/NinjaDetail";' in s:
        s = s.replace('import NinjaDetail from "./components/NinjaDetail";', 'import NinjaDetail from "./components/NinjaDetail";\nimport EquipmentScreen from "./components/EquipmentScreen";', 1)
    else:
        lines = s.splitlines()
        insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith('import ')), default=0)
        lines.insert(insert_at, 'import EquipmentScreen from "./components/EquipmentScreen";')
        s = '\n'.join(lines)

    mt = re.search(r'type Tab\s*=\s*([^;]+);', s)
    if not mt:
        raise SystemExit('app equipment tab: type Tab union not found')
    union = mt.group(1)
    if '"equipment"' not in union:
        s = s[:mt.start(1)] + union.rstrip() + ' | "equipment"' + s[mt.end(1):]

    # Keyboard left/right navigation includes Equipment.
    order = re.search(r'const order: Tab\[\] = \[([^\]]+)\];', s)
    if order and '"equipment"' not in order.group(1):
        vals = order.group(1).rstrip()
        s = s[:order.start(1)] + vals + ', "equipment"' + s[order.end(1):]

    # Append the Equipment button to the existing tabs data array.
    tabs = re.search(r'(const tabs: \{ id: Tab; kanji: string; label: string; badge: string \}\[\] = \[)([\s\S]*?)(\n  \];)', s)
    if not tabs:
        raise SystemExit('app equipment tabs: tabs array not found')
    body = tabs.group(2)
    if 'id: "equipment"' not in body:
        body = body.rstrip() + '\n    { id: "equipment", kanji: "具", label: "Equip", badge: "" },'
        s = s[:tabs.start(2)] + body + s[tabs.end(2):]

    # The equipment tab must be reachable on desktop as well as mobile.
    s = s.replace('<nav className="flex h-10 shrink-0 gap-1.5 lg:hidden">', '<nav className="flex h-10 shrink-0 gap-1.5">', 1)

    grid = re.search(r'<div className="([^"]*grid min-h-0 flex-1[^"]*)">', s)
    if not grid:
        raise SystemExit('app equipment content: management grid not found')
    grid_class = grid.group(1)
    equipment_render = '          {tab === "equipment" && <EquipmentScreen s={s} onChanged={force} />}\n\n'
    replacement = equipment_render + '<div className={cn("' + grid_class + '", tab === "equipment" && "hidden")}> '
    s = s[:grid.start()] + replacement + s[grid.end():]

    # Persist gear changes through the same force/save path as all other actions.
    nd = re.search(r'(<NinjaDetail[\s\S]*?onPerk=\{\(id, r\) => doPerk\(detailFor, id, r\)\}[\s\S]*?)(/>)', s)
    if not nd:
        raise SystemExit('app equipment persistence: NinjaDetail invocation not found')
    if 'onEquipmentChanged' not in nd.group(1):
        block = nd.group(1) + '          onEquipmentChanged={force}\n        '
        s = s[:nd.start()] + block + nd.group(2) + s[nd.end():]

    write(p, s)
    print('app equipment tab: applied')
else:
    print('app equipment tab: already applied')

# Force a cache refresh for installed builds.
p = 'public/sw.js'
s = read(p)
if 'equipment-gacha-v1' not in s:
    s, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-equipment-gacha-v1";', s, count=1)
    if n != 1:
        raise SystemExit('service worker cache constant not found')
    write(p, s)
    print('service worker cache bump: applied')

print('equipment gacha patch complete')