from pathlib import Path
import runpy

# This branch's workflow runs equipment immediately before the new v1 depth pass.
# v2 was authored against the v1 output, so provide the one generated-file shim it
# needs, run it, then preserve its richer special-mission catalogue under a v2 name.
root = Path('app')
jutsu = root / 'src/components/JutsuTree.tsx'
if not jutsu.exists():
    jutsu.parent.mkdir(parents=True, exist_ok=True)
    jutsu.write_text('const j = { target: "all_foes" };\nvoid j.target.replaceAll("_", " ");\n', encoding='utf-8')

# The project TS target predates String.replaceAll; v1's generated JutsuTree uses it.
# This declaration keeps the generated source compatible without weakening tsconfig.
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

print('Applied village depth v2 build-order shim.')
