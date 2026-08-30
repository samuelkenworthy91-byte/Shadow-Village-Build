from pathlib import Path

p = Path('app/src/game/jutsu.ts')
s = p.read_text(encoding='utf-8')
old = 'export function prerequisiteJutsu(n: Ninja, id: string): JutsuDef | undefined {'
new = 'export function prerequisiteJutsu(_n: Ninja, id: string): JutsuDef | undefined {'
if new in s:
    print('Village depth v8 TypeScript fix already applied')
elif old in s:
    p.write_text(s.replace(old, new, 1), encoding='utf-8')
    print('Village depth v8 TypeScript prerequisite parameter fix applied')
else:
    raise SystemExit('v8 prerequisite helper anchor missing')
