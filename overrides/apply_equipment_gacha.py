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
p = 'src/game/engine.ts'
s = read(p)
if 'equipmentSkillBonus' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith('import ')), default=0)
    lines.insert(insert_at, 'import { equipmentSkillBonus } from "./equipment";')
    s = '\n'.join(lines) + ('\n' if read(p).endswith('\n') else '')
    m = re.search(r'export function effSkill\s*\(\s*n:\s*Ninja\s*,\s*k:\s*Skill\s*\)\s*(?::\s*number\s*)?\{', s)
    if not m:
        raise SystemExit('engine equipment stats: effSkill signature not found')
    s = s[:m.start()] + m.group(0).replace('export function effSkill', 'function baseEffSkill') + s[m.end():]
    s += '\n\nexport function effSkill(n: Ninja, k: Skill): number {\n  return baseEffSkill(n, k) + equipmentSkillBonus(n, k);\n}\n'
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
    m = re.search(r'export function unitFromNinja\s*\(\s*n:\s*Ninja\s*\)\s*(?::\s*Unit\s*)?\{', s)
    if not m:
        raise SystemExit('battle equipment wrapper: unitFromNinja signature not found')
    s = s[:m.start()] + m.group(0).replace('export function unitFromNinja', 'function baseUnitFromNinja') + s[m.end():]
    s += '''\n\nexport function unitFromNinja(n: Ninja): Unit {\n  const equipped = { ...n, s: { ...n.s } };\n  const gearSkills: Skill[] = ["nin", "tai", "gen", "ste", "med", "spd", "ken", "doj", "tac"];\n  for (const k of gearSkills) equipped.s[k] += equipmentSkillBonus(n, k);\n  return applyEquipmentToBattleUnit(n, baseUnitFromNinja(equipped)) as Unit;\n}\n'''
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
    s = s.replace(modal_anchor, '        {showEquipment && <NinjaEquipment s={s} n={n} onClose={() => setShowEquipment(false)} />}\n\n' + modal_anchor, 1)
    write(p, s)
    print('ninja portrait equipment entry: applied')
else:
    print('ninja portrait equipment entry: already applied')

# Add the bottom Equipment tab and main gacha/inventory screen.
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

    content_anchor = re.search(r'\{tab\s*===\s*"ninjas"\s*&&', s)
    if not content_anchor:
        raise SystemExit('app equipment content: ninjas tab render not found')
    s = s[:content_anchor.start()] + '{tab === "equipment" && <EquipmentScreen s={s} onChanged={force} />}\n      ' + s[content_anchor.start():]

    nav_button = re.search(r'<button\b(?:(?!</button>)[\s\S])*?setTab\("ninjas"\)(?:(?!</button>)[\s\S])*?</button>', s)
    if not nav_button:
        raise SystemExit('app equipment nav: ninjas button block not found')
    new_button = r'''
          <button
            onClick={() => { audio.click(); setTab("equipment"); setDetailFor(null); setSquadFor(null); }}
            className={cn(
              "relative flex min-w-0 flex-1 flex-col items-center justify-center gap-0.5 rounded-xl px-1 py-1.5 text-[8.5px] font-black tracking-[0.08em] transition active:scale-95",
              tab === "equipment" ? "bg-gold/12 text-gold ring-1 ring-gold/25" : "text-paper/45 hover:text-paper/70"
            )}
            aria-label="Equipment"
          >
            <span className="font-display text-[15px] leading-none">具</span>
            <span>EQUIP</span>
          </button>'''
    s = s[:nav_button.end()] + new_button + s[nav_button.end():]
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