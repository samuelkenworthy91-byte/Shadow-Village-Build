"""Validate the built inventory, reviewed asset hashes, and transparent pockets."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'overrides'))
from portrait_library import QC, OUT, validate_assets

validate_assets()
for key, entry in QC['white_pocket_repairs'].items():
    source = ROOT / f'overrides/ninja_assets_v29/direct/ninja_{int(key):03d}.webp'
    if hashlib.sha256(source.read_bytes()).hexdigest() != entry['cleaned_sha256']:
        raise RuntimeError(f'Reviewed source changed: {source.name}')
    png = OUT / f'ninja_{int(key):03d}.png'
    raw = subprocess.check_output(['convert', str(png), '-depth', '8', 'rgba:-'])
    if len(raw) != 240 * 536 * 4:
        raise RuntimeError(f'Wrong runtime canvas: {png.name}')
    for pocket in entry['pockets']:
        x, y = pocket['seed']
        if raw[(y * 240 + x) * 4 + 3] != 0:
            raise RuntimeError(f'Background pocket returned in {png.name}: {x},{y}')
for key in QC['removed']:
    if list((ROOT / 'overrides').glob(f'ninja_assets_v*/direct/ninja_{int(key):03d}.webp')):
        raise RuntimeError(f'Retired direct portrait source remains: {key}')
print(f"Verified {len(QC['white_pocket_repairs'])} repaired portraits and {len(QC['removed'])} retired IDs")
