from pathlib import Path
import base64, gzip
parts = Path('overrides/v11_clans_dojutsu_parts')
payload = ''.join(p.read_text(encoding='utf-8') for p in sorted(parts.glob('part_*')))
code = gzip.decompress(base64.b64decode(payload)).decode('utf-8')
exec(compile(code, 'v11_clans_dojutsu.py.gz.b64', 'exec'), {'__name__': '__main__'})
