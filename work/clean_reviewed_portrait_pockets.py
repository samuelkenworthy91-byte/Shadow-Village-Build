"""Apply visually reviewed background seeds; preserve every original RGB pixel.

One-off asset repair. Does not guess background from clothing colour or size.
Input hashes and bounded components prevent a future portrait being modified
using a stale review. Sources remain compact lossless WebP; CI emits PNG.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'overrides/portrait_qc_v33.json'

def main():
    manifest = json.loads(MANIFEST.read_text())
    for key, entry in manifest['white_pocket_repairs'].items():
        path = ROOT / f'overrides/ninja_assets_v29/direct/ninja_{int(key):03d}.webp'
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha == entry.get('cleaned_sha256'):
            continue
        if sha != entry['source_sha256']:
            raise RuntimeError(f'{path.name}: source differs from the reviewed image')
        rgba = np.array(Image.open(path).convert('RGBA'))
        rgb = rgba[..., :3].astype(int)
        candidate = (rgb.min(2) >= 210) & (np.ptp(rgb, axis=2) <= 45) & (rgba[..., 3] > 0)
        clear = np.zeros(candidate.shape, bool)
        for pocket in entry['pockets']:
            x, y = pocket['seed']; x0, y0, x1, y1 = pocket['box']
            bounds = np.zeros_like(candidate)
            bounds[max(0,y0-2):min(536,y1+2),max(0,x0-2):min(240,x1+2)] = True
            seed = np.zeros_like(candidate); seed[y,x] = True
            if not candidate[y,x]:
                raise RuntimeError(f'{path.name}: background seed no longer matches')
            clear |= ndi.binary_propagation(seed, mask=candidate & bounds, structure=np.ones((3,3)))
        before = rgba.copy()
        rgba[clear,3] = 0
        assert np.array_equal(rgba[..., :3], before[..., :3])
        assert np.array_equal(rgba[~clear], before[~clear])
        assert clear.sum() < (before[...,3] > 0).sum() * .2, path.name
        Image.fromarray(rgba).save(path, 'WEBP', lossless=True, exact=True)
        entry['cleaned_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        entry['cleared_pixels'] = int(clear.sum())
    MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n')
    print('Reviewed background repairs:',len(manifest['white_pocket_repairs']))

if __name__ == '__main__':
    main()
