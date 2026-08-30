from pathlib import Path
import subprocess, base64, gzip

root = Path('app')
parts = sorted(Path('overrides/v9_identity_patch_parts').glob('part_*'))
if not parts:
    raise SystemExit('v9 identity patch parts not found')
encoded = ''.join(x.read_text(encoding='utf-8').strip() for x in parts)
patch_file = Path('/tmp/v9_identity_uniques.patch')
patch_file.write_bytes(gzip.decompress(base64.b64decode(encoded)))
if not root.exists():
    raise SystemExit('app source tree not found')
subprocess.run(['patch', '-p1', '--forward', '-i', str(patch_file)], cwd=root, check=True)

checks = {
    'src/game/jutsu.ts': ['requiresKekkei', 'jutsuPassiveFx', 'COMBINED_JUTSU', 'PASSIVE_JUTSU_OVERRIDES'],
    'src/game/perks.ts': ['LEGEND_EXTRA_PERKS', 'lgx_tempest_heart', 'lgx_reversal_formula'],
    'src/components/JutsuTree.tsx': ['KEKKEI GENKAI · COMBINED NATURE', 'PASSIVE ACTIVE'],
    'src/game/battle.ts': ['jutsuBurnAmp', 'jutsuGuardStrength', 'jutsuChakraCost'],
}
for rel, needles in checks.items():
    text = (root / rel).read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v9 validation failed: {needle} missing from {rel}')
print('Village depth v9 elemental identity, Kekkei trees and unique main-tree abilities applied')
