from pathlib import Path
import re
import runpy

# This branch's workflow runs equipment immediately before the dedicated village-depth
# progression step. v2 was authored against v1-shaped files, so stage the generated
# mission board/special catalogue here, preserve that catalogue, then let the normal
# v1 step run. The shim also arranges for v3 to run after v1 so content additions are
# not overwritten by v1's deliberate mission-catalogue replacement.
root = Path('app')
jutsu = root / 'src/components/JutsuTree.tsx'
if not jutsu.exists():
    jutsu.parent.mkdir(parents=True, exist_ok=True)
    jutsu.write_text('const j = { target: "all_foes" };\nvoid j.target.replaceAll("_", " ");\n', encoding='utf-8')

# The project TS target predates String.replaceAll; v1's generated JutsuTree uses it.
(root / 'src/village-depth-compat.d.ts').write_text(
    'interface String { replaceAll(searchValue: string | RegExp, replaceValue: string): string; }\n',
    encoding='utf-8',
)

runpy.run_path('overrides/apply_village_depth_v2.py', run_name='__main__')

special = root / 'src/game/specialMissions.ts'
special_v2 = root / 'src/game/specialMissionsV2.ts'
if special.exists():
    special_v2.write_text(special.read_text(encoding='utf-8'), encoding='utf-8')

# v1 subsequently writes its own starter specialMissions.ts. Keep the v2 consumers
# pointed at the richer catalogue so that overwrite cannot regress the feature.
for rel in ['src/game/engine.ts', 'src/components/SquadModal.tsx']:
    p = root / rel
    text = p.read_text(encoding='utf-8')
    text = text.replace('from "./specialMissions"', 'from "./specialMissionsV2"')
    text = text.replace('from "../game/specialMissions"', 'from "../game/specialMissionsV2"')
    p.write_text(text, encoding='utf-8')

# The equipment workflow validates its own cache namespace before the dedicated
# progression step. Preserve that namespace while still forcing a cache refresh.
sw = root / 'public/sw.js'
sw_text = sw.read_text(encoding='utf-8')
sw_text, n = re.subn(
    r'const CACHE = "[^"]+";',
    'const CACHE = "shadow-village-equipment-gacha-v2-400gear-v5-mobile-hud-village-depth-v2-staged";',
    sw_text,
    count=1,
)
if n != 1:
    raise SystemExit('Unable to restore staged equipment cache namespace')
sw.write_text(sw_text, encoding='utf-8')

# Modify only the CI workspace copy of the v1 runner. The repository's v1 source
# remains unchanged; when the next workflow step runs it will finish by applying v3.
v1_runner = Path('overrides/apply_village_depth_v1.py')
v1_text = v1_runner.read_text(encoding='utf-8')
hook_marker = '# VILLAGE_DEPTH_V3_RUNTIME_HOOK'
if hook_marker not in v1_text:
    v1_text += '''\n\n# VILLAGE_DEPTH_V3_RUNTIME_HOOK\nimport runpy as _village_depth_runpy\n_village_depth_runpy.run_path("overrides/apply_village_depth_v3.py", run_name="__main__")\n'''
    v1_runner.write_text(v1_text, encoding='utf-8')

print('Applied village depth v2 staging shim; v3 queued after v1.')
