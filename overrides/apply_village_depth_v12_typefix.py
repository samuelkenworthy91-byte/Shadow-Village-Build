from pathlib import Path

# Fix the generated Ninja Detail progression-tab JSX.
p = Path('app/src/components/NinjaDetail.tsx')
text = p.read_text(encoding='utf-8')
old = 'onClick={() => setProgressionView("skills") className='
new = 'onClick={() => setProgressionView("skills")} className='
if old not in text:
    raise SystemExit('v12 NinjaDetail skills-tab JSX anchor not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8')

# The Genjutsu targeting helper no longer needs a separately-materialised allied
# side array: ally techniques validate the explicitly selected same-side target.
battle = Path('app/src/game/battle.ts')
battle_text = battle.read_text(encoding='utf-8')
unused = '  const alliesSide = u.foe ? aliveFoes(b) : aliveAllies(b);\n'
if unused not in battle_text:
    raise SystemExit('v12 unused alliesSide declaration anchor not found')
battle.write_text(battle_text.replace(unused, '', 1), encoding='utf-8')

print('Village depth v12 JSX and Genjutsu strict-TypeScript fixes applied')
