from pathlib import Path
import base64
import gzip

payload = Path('overrides/equipment_gacha_v2.py.gz.b64').read_text(encoding='utf-8').strip()
source = gzip.decompress(base64.b64decode(payload)).decode('utf-8')
exec(compile(source, 'equipment_gacha_v2_payload.py', 'exec'))
