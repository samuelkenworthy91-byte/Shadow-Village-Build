from pathlib import Path
import base64
import gzip
import subprocess
import tempfile

root = Path('app')
parts = [Path(f'overrides/v13_element_roles_patch_part_{i:02d}.txt') for i in range(1, 6)]
for p in parts:
    if not p.exists():
        raise SystemExit(f'v13 payload part missing: {p}')
encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
patch_bytes = gzip.decompress(base64.b64decode(encoded))
with tempfile.NamedTemporaryFile(suffix='.patch') as tmp:
    tmp.write(patch_bytes)
    tmp.flush()
    subprocess.run(['patch', '-p1', '--forward', '-i', tmp.name], cwd=root, check=True)

checks = {
    root / 'src/game/jutsu.ts': ['"Armour Shred"', 'executeBelow: 0.26', 'extraTurnChance: 0.40', 'retaliationPct: 0.45', 'ranged: true', 'allyCpRestorePct: 0.12'],
    root / 'src/game/battle.ts': ['effectiveDefense', 'BONUS TURN!', 'Earth retaliation returns', 'jutsuExtraTurnBonus', 'tauntStrength', 't.confusionRounds = 0'],
    root / 'src/game/types.ts': ['defShredRounds?: number', 'extraTurnPending?: boolean', 'jutsuRetaliationBonus?: number'],
    root / 'src/components/JutsuTree.tsx': ['ARMOUR SHRED · RANGE', 'EXTRA-TURN PRESSURE', 'RANGED · BYPASS GUARD'],
    root / 'public/sw.js': ['shadow-village-depth-v1-jutsu-potential-v13-element-roles'],
}
for path, needles in checks.items():
    text = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v13 validation failed: {needle} missing from {path}')
print('Village depth v13 locked elemental role overhaul applied')
