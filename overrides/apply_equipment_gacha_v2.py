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

# Raid consequence v4: failed/undefended raids also knock one existing building down a level.
source_v4 = Path('overrides/apply_raid_building_damage.py').read_text(encoding='utf-8')
exec(compile(source_v4, 'raid_building_damage_v4.py', 'exec'))

# Mobile HUD v5: apply the compact income/consumption presentation last so the forecast cannot be squeezed away.
hud_src = Path('overrides/src/components/HUD.tsx')
hud_dst = Path('app/src/components/HUD.tsx')
hud_dst.write_text(hud_src.read_text(encoding='utf-8'), encoding='utf-8')

sw = Path('app/public/sw.js')
sw_text = sw.read_text(encoding='utf-8')
old_cache = 'shadow-village-equipment-gacha-v2-400gear-v4-raid-damage'
new_cache = 'shadow-village-equipment-gacha-v2-400gear-v5-mobile-hud'
if old_cache not in sw_text:
    raise SystemExit('Expected v4 service-worker cache key not found')
sw.write_text(sw_text.replace(old_cache, new_cache, 1), encoding='utf-8')

print('Applied compact mobile resource forecast HUD and cache refresh.')
