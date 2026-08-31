from pathlib import Path

p = Path('app/src/components/BattleScreen.tsx')
text = p.read_text(encoding='utf-8')
replacements = [
    ('function targetModeForAction(cur: Unit | null, b: Battle, a: BAction): TargetMode {',
     'function targetModeForAction(a: BAction): TargetMode {'),
    ('targetModeForAction(cur, b, pending)', 'targetModeForAction(pending)'),
    ('targetModeForAction(cur, b, a)', 'targetModeForAction(a)'),
]
for old, new in replacements:
    if old not in text:
        raise SystemExit(f'v16 typefix expected source missing: {old}')
    text = text.replace(old, new)
p.write_text(text, encoding='utf-8')
print('Village depth v16 strict-TypeScript target-mode parameter fix applied')
