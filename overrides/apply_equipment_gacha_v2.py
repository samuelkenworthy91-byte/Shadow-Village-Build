from pathlib import Path
import base64
import gzip

payload = Path('overrides/equipment_gacha_v2.py.gz.b64').read_text(encoding='utf-8').strip()
source = gzip.decompress(base64.b64decode(payload)).decode('utf-8')
exec(compile(source, 'equipment_gacha_v2_payload.py', 'exec'))

# Small presentation-only v3 pass: pull reveal pop-up and generated appearance flavour.
payload_v3 = Path('overrides/equipment_gacha_v3b.py.gz.b64').read_text(encoding='utf-8').strip()
source_v3 = gzip.decompress(base64.b64decode(payload_v3)).decode('utf-8')
exec(compile(source_v3, 'equipment_gacha_v3_payload.py', 'exec'))
