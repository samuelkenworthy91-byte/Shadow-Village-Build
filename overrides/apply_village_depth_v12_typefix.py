from pathlib import Path

# Fix the generated Ninja Detail progression-tab JSX.
p = Path('app/src/components/NinjaDetail.tsx')
text = p.read_text(encoding='utf-8')
old = 'onClick={() => setProgressionView("skills") className='
new = 'onClick={() => setProgressionView("skills")} className='
if old not in text:
    raise SystemExit('v12 NinjaDetail skills-tab JSX anchor not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8')

battle = Path('app/src/game/battle.ts')
battle_text = battle.read_text(encoding='utf-8')

# Ordinary learned Jutsu genuinely need both sides: ally-target/AoE healing and
# squad-restoration effects read alliesSide. Restore that declaration if the earlier
# strict-typefix revision removed it.
elemental_anchor = '''  const foesSide = u.foe ? aliveAllies(b) : aliveFoes(b);\n  const requested = targetUid ? unitById(b, targetUid) : undefined;\n'''
elemental_fixed = '''  const foesSide = u.foe ? aliveAllies(b) : aliveFoes(b);\n  const alliesSide = u.foe ? aliveFoes(b) : aliveAllies(b);\n  const requested = targetUid ? unitById(b, targetUid) : undefined;\n'''
start = battle_text.find('function useElementalJutsu(')
end = battle_text.find('function genjutsuLandChance(', start)
if start < 0 or end < 0:
    raise SystemExit('v12 elemental Jutsu function bounds not found')
elemental = battle_text[start:end]
if elemental_anchor in elemental:
    elemental = elemental.replace(elemental_anchor, elemental_fixed, 1)
elif elemental_fixed not in elemental:
    raise SystemExit('v12 elemental alliesSide restoration anchor not found')
battle_text = battle_text[:start] + elemental + battle_text[end:]

# Genjutsu ally techniques validate the explicitly selected same-side target and do
# not need a materialised alliesSide array. Remove only this function's declaration.
gen_start = battle_text.find('function useLearnedGenjutsu(')
if gen_start < 0:
    raise SystemExit('v12 Genjutsu resolver not found')
gen_end = battle_text.find('\nfunction ', gen_start + 1)
if gen_end < 0:
    gen_end = len(battle_text)
gen_block = battle_text[gen_start:gen_end]
unused = '  const alliesSide = u.foe ? aliveFoes(b) : aliveAllies(b);\n'
if unused not in gen_block:
    raise SystemExit('v12 Genjutsu unused alliesSide declaration anchor not found')
gen_block = gen_block.replace(unused, '', 1)
battle_text = battle_text[:gen_start] + gen_block + battle_text[gen_end:]
battle.write_text(battle_text, encoding='utf-8')

print('Village depth v12 JSX and function-scoped Genjutsu strict-TypeScript fixes applied')
