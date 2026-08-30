from pathlib import Path
import base64, gzip, runpy

parts = Path('overrides/v11_clans_dojutsu_parts')
payload = ''.join(p.read_text(encoding='utf-8') for p in sorted(parts.glob('part_*')))
code = gzip.decompress(base64.b64decode(payload)).decode('utf-8')
exec(compile(code, 'v11_clans_dojutsu.py.gz.b64', 'exec'), {'__name__': '__main__'})
runpy.run_path('overrides/apply_village_depth_v11_typefix.py', run_name='__main__')
