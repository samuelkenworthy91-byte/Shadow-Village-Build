from pathlib import Path
import subprocess, gzip

root = Path('app')
gz_file = Path('overrides/v10_personal_legend_arts.patch.gz')
if not gz_file.exists():
    raise SystemExit('v10 personal legend patch archive not found')
patch_file = Path('/tmp/v10_personal_legend_arts.patch')
patch_file.write_bytes(gzip.decompress(gz_file.read_bytes()))
if not root.exists():
    raise SystemExit('app source tree not found')
subprocess.run(['patch', '-p1', '--forward', '-i', str(patch_file)], cwd=root, check=True)

# Preserve the compatibility prefix expected by the existing workflow while forcing
# installed test builds onto the new personal-arts cache.
sw = root / 'public/sw.js'
sw_text = sw.read_text(encoding='utf-8')
import re
sw_text, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-depth-v1-jutsu-potential-v10-personal-legend-arts";', sw_text, count=1)
if n != 1:
    raise SystemExit('v10 cache marker rewrite failed')
sw.write_text(sw_text, encoding='utf-8')

checks = {
    'src/game/jutsu.ts': [
        'requiresLegend?: string', 'const LEGEND_JUTSU',
        'legend_jinchuriki_beast_chakra_arm',
        'legend_doujutsu_illusion_ocular_lock',
        'legend_gate_master_sacrifice_final_gate_meteor',
        'legend_seal_bearer_binding_sixfold_binding_array',
    ],
    'src/game/battle.ts': ['j.cpDrainPct', 'j.hits ?? 1', 'poisonRounds', 'bleedRounds', 'j.executeBelow'],
    'src/components/JutsuTree.tsx': ['PERSONAL LEGEND ARTS', 'specialText(j)', 'requiresLegend===n.legend'],
    'public/sw.js': ['shadow-village-depth-v1-jutsu-potential-v10-personal-legend-arts'],
}
for rel, needles in checks.items():
    text = (root / rel).read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v10 validation failed: {needle} missing from {rel}')
print('Village depth v10 personal legend Jutsu trees applied')
