from pathlib import Path
import subprocess

root = Path('app')
patch_path = Path('overrides/v15_dynamic_technique_rows.patch').resolve()
subprocess.run(
    ['patch', '-p1', '--forward', '--batch', '-i', str(patch_path)],
    cwd=root,
    check=True,
)

# Force installed/PWA clients onto the corrected progression runtime.
sw = root / 'public/sw.js'
sw_text = sw.read_text(encoding='utf-8')
old_cache = 'shadow-village-depth-v1-jutsu-potential-v14-purchase-reliability'
new_cache = 'shadow-village-depth-v1-jutsu-potential-v15-dynamic-technique-rows'
if old_cache not in sw_text:
    raise SystemExit('v15 expected v14 cache marker was not found')
sw.write_text(sw_text.replace(old_cache, new_cache, 1), encoding='utf-8')

checks = {
    'src/game/types.ts': [
        'Future rows remain dynamic.',
        'techniqueTree?: string[][];',
    ],
    'src/game/perks.ts': [
        'frozenRows: string[][] = []',
        'Stable per-candidate random score.',
        'used.has(p.id)',
        'return buildTechniqueTree(n, techs, n.techniqueTree ?? []);',
        'const unlocked = Math.min(10, tiersUnlocked(n.level));',
        'while (frozen.length < unlocked)',
        'a technique shown at Level 2 can never reappear at Level 6, 8, etc.',
        'export function perkPurchaseCheck',
    ],
    'src/game/engine.ts': [
        'lockTechniqueTree(n, s.techs);\n  const check = perkPurchaseCheck',
        'lockTechniqueTree(n, s.techs);\n  n.sp--;',
        'lockTechniqueTree(recipient, s.techs);',
        'const check = perkPurchaseCheck(n, s.techs, perkId);',
        'skillTrainingBlockReason(n, k)',
    ],
    'src/game/battle.ts': [
        'import { lockTechniqueTree, perkById, perkFx } from "./perks";',
        'lockTechniqueTree(n, s.techs);',
    ],
    'src/components/PerkTree.tsx': [
        'Rows lock when their level is reached.',
        'cannot appear again later.',
        'TREE COMPLETE',
        'const purchase = perkPurchaseCheck(n, techs, p.id);',
    ],
    'src/components/NinjaDetail.tsx': [
        'Purchase blocked. Nothing was spent.',
    ],
    'src/game/jutsu.ts': [
        'export function jutsuLearnBlockReason',
        'Duplicate Jutsu id detected',
    ],
    'src/game/genjutsu.ts': [
        'export function genjutsuLearnBlockReason',
        'Duplicate Genjutsu id detected',
    ],
    'public/sw.js': [new_cache],
}
for rel, needles in checks.items():
    text = (root / rel).read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v15 integrity check failed: {needle!r} missing from {rel}')

engine = (root / 'src/game/engine.ts').read_text(encoding='utf-8')
if 'lockTechniqueTree(n, s.techs, true);' in engine:
    raise SystemExit('v15 failed: a whole-tree forced lock remains in engine.ts')
if 'Locked at recruitment so training/research can never reshuffle' in (root / 'src/game/types.ts').read_text(encoding='utf-8'):
    raise SystemExit('v15 failed: old whole-tree-at-recruitment semantics remain')

print('Village depth v15 dynamic/frozen-row technique reliability pass applied and audited')
