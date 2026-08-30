from pathlib import Path

p = Path('app/src/components/NinjaDetail.tsx')
text = p.read_text(encoding='utf-8')
old = 'onClick={() => setProgressionView("skills") className='
new = 'onClick={() => setProgressionView("skills")} className='
if old not in text:
    raise SystemExit('v12 NinjaDetail skills-tab JSX anchor not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8')
print('Village depth v12 NinjaDetail Genjutsu-tab JSX fix applied')
