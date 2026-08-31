from pathlib import Path
import subprocess

root = Path('app')
patch_path = Path('overrides/v13_2_progression_purchase_reliability.patch').resolve()
subprocess.run(
    ['patch', '-p1', '--forward', '--batch', '-i', str(patch_path)],
    cwd=root,
    check=True,
)

checks = {
    'src/game/types.ts': ['techniqueRows?: string[][]'],
    'src/game/perks.ts': [
        'export function freezeTechniqueRows',
        'return generateTechniqueTree(n, techs, n.techniqueRows ?? [])',
        'if (!p || row.length >= want || used.has(p.id)) return;',
    ],
    'src/game/engine.ts': [
        'freezeTechniqueRows(n, s.techs);',
        'freezeTechniqueRows(recipient, s.techs);',
    ],
    'src/game/battle.ts': ['freezeTechniqueRows(n, s.techs);'],
    'src/components/PerkTree.tsx': [
        "Unlocked rows are fixed the moment their level is reached.",
        'A technique can only appear once anywhere in the tree.',
    ],
    'src/App.tsx': ['TECHNIQUE CHOICE NO LONGER AVAILABLE'],
}
for rel, needles in checks.items():
    text = (root / rel).read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v13.2 integrity check failed: {needle!r} missing from {rel}')

print('Village depth v13.2 progression purchase reliability pass applied')
