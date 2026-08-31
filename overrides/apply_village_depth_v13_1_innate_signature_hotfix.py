from pathlib import Path

root = Path('app')


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'v13.1 {label} anchor not found in {path}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


# Save-compatible rule: keep the innate order signature physically stored in
# n.perks, but stop treating that slot as a level-gated technique choice.
perks = root / 'src/game/perks.ts'
replace_once(
    perks,
    '''export function pendingPerks(n: Ninja): number {\n  return Math.max(0, tiersUnlocked(n.level) - n.perks.length);\n}''',
    '''export function pendingPerks(n: Ninja, techs: VillageTechId[] = []): number {\n  const selected = techniqueTierSelections(n, techs);\n  const unlocked = Math.min(tiersUnlocked(n.level), selected.length);\n  let missing = 0;\n  for (let t = 0; t < unlocked; t++) if (!selected[t]) missing++;\n  return missing;\n}''',
    'pending-perk accounting',
)
replace_once(
    perks,
    '''    if (legendPerk && t === 2) {\n      row.unshift(legendPerk);\n      if (row.length > 3) row.pop();\n    }''',
    '''    if (legendPerk && t === 2 && innateLegendSignatureId(n) !== legendPerk.id) {\n      row.unshift(legendPerk);\n      if (row.length > 3) row.pop();\n    }''',
    'innate signature duplicate offer',
)
replace_once(
    perks,
    '''  return tiers;\n}\n\nfunction basePerkById''',
    '''  return tiers;\n}\n\n/**\n * Rare-order recruits are granted their order signature immediately on recruitment.\n * Older saves store that innate signature at n.perks[0], before any level-gated\n * technique picks. It must remain in the saved array so its combat effects stay\n * active, but it must not consume a normal technique tier.\n */\nexport function innateLegendSignatureId(n: Ninja): string | null {\n  const signature = n.legend ? LEGENDS[n.legend]?.perk.id ?? null : null;\n  return signature && n.perks[0] === signature ? signature : null;\n}\n\n/** Map saved normal technique choices back onto their deterministic tree rows.\n * This is intentionally derived at runtime rather than migrating save data, so\n * pre-hotfix rare-order saves keep every learned perk and recover any tier that\n * the innate signature previously displaced.\n */\nexport function techniqueTierSelections(n: Ninja, techs: VillageTechId[] = []): Array<string | null> {\n  const innate = innateLegendSignatureId(n);\n  const chosen = new Set(\n    n.perks.filter((id, index) => !(index === 0 && innate === id))\n  );\n  return perkTree(n, techs).map((row) => row.find((p) => chosen.has(p.id))?.id ?? null);\n}\n\nexport function firstOpenTechniqueTier(n: Ninja, techs: VillageTechId[] = []): number {\n  const selected = techniqueTierSelections(n, techs);\n  const unlocked = Math.min(tiersUnlocked(n.level), selected.length);\n  for (let t = 0; t < unlocked; t++) if (!selected[t]) return t;\n  return unlocked;\n}\n\nfunction basePerkById''',
    'save-compatible tier mapping helpers',
)

# The tree UI now renders saved choices by the row they actually belong to, so
# old affected saves can fill the displaced early tier without losing later picks.
perk_ui = root / 'src/components/PerkTree.tsx'
replace_once(
    perk_ui,
    'import { pendingPerks, perkMechanics, perkTree, tiersUnlocked } from "../game/perks";',
    'import { firstOpenTechniqueTier, innateLegendSignatureId, pendingPerks, perkMechanics, perkTree, techniqueTierSelections, tiersUnlocked } from "../game/perks";',
    'PerkTree imports',
)
replace_once(
    perk_ui,
    '''  const pending = pendingPerks(n);\n  // the tier currently being chosen = number already taken\n  const activeTier = n.perks.length;''',
    '''  const pending = pendingPerks(n, techs);\n  const tierSelections = techniqueTierSelections(n, techs);\n  const activeTier = firstOpenTechniqueTier(n, techs);\n  const innateSignature = innateLegendSignatureId(n);''',
    'PerkTree active tier',
)
replace_once(
    perk_ui,
    '''      <div className="space-y-2">\n        {tree.map((row, t) => {\n          const taken = n.perks[t];''',
    '''      {innateSignature && (\n        <div className="mb-2 rounded-lg bg-gold/8 px-2 py-1.5 ring-1 ring-inset ring-gold/20">\n          <p className="text-[9px] font-black tracking-[0.13em] text-gold/80">INNATE SIGNATURE MASTERED</p>\n          <p className="mt-0.5 text-[8.5px] font-semibold leading-snug text-paper/55">This order technique is already active and does not consume a level-gated technique choice.</p>\n        </div>\n      )}\n\n      <div className="space-y-2">\n        {tree.map((row, t) => {\n          const taken = tierSelections[t];''',
    'PerkTree saved-row rendering',
)

# Reject stale/off-row modal selections in the engine, and make every perk-ready
# calculation use the same village-tech-aware tier interpretation.
engine = root / 'src/game/engine.ts'
replace_once(
    engine,
    'import { LEGENDS, SCOUT_LEGEND_IDS, pendingPerks, perkById, perkFx, perkTree } from "./perks";',
    'import { firstOpenTechniqueTier, LEGENDS, SCOUT_LEGEND_IDS, pendingPerks, perkById, perkFx, perkTree } from "./perks";',
    'engine imports',
)
replace_once(
    engine,
    '''  if (!n || pendingPerks(n) <= 0) return false;\n  if (n.perks.includes(perkId)) return false;\n  const p = perkById(perkId);''',
    '''  if (!n || pendingPerks(n, s.techs) <= 0) return false;\n  if (n.perks.includes(perkId)) return false;\n  const activeTier = firstOpenTechniqueTier(n, s.techs);\n  const activeRow = perkTree(n, s.techs)[activeTier] ?? [];\n  if (!activeRow.some((candidate) => candidate.id === perkId)) return false;\n  const p = perkById(perkId);''',
    'choosePerk row validation',
)
replace_once(
    engine,
    'perkReady: pendingPerks(n) > 0,',
    'perkReady: pendingPerks(n, s.techs) > 0,',
    'mission perk-ready flag',
)

roster = root / 'src/components/Roster.tsx'
replace_once(
    roster,
    'pendingPerks(n) > 0 && (',
    'pendingPerks(n, s.techs) > 0 && (',
    'roster perk-ready flag',
)

# Cache refresh only. The actual local-save version/key is intentionally unchanged.
sw = root / 'public/sw.js'
replace_once(
    sw,
    'shadow-village-depth-v1-jutsu-potential-v13-element-roles',
    'shadow-village-depth-v1-jutsu-potential-v13-1-signature-hotfix',
    'cache namespace',
)

# Hard safety checks for the requested in-place update behaviour.
save_text = (root / 'src/game/save.ts').read_text(encoding='utf-8')
if 'const SAVE_VERSION = 3;' not in save_text or 'shadow-village-save-v${SAVE_VERSION}-slot-${slot}' not in save_text:
    raise SystemExit('v13.1 save-compatibility check failed: save version/key changed')
if 'if (signature && !n.perks.includes(signature)) n.perks.push(signature);' not in engine.read_text(encoding='utf-8'):
    raise SystemExit('v13.1 save-compatibility check failed: innate signature storage changed')

checks = {
    perks: ['techniqueTierSelections', 'firstOpenTechniqueTier', 'innateLegendSignatureId', 'innateLegendSignatureId(n) !== legendPerk.id'],
    perk_ui: ['INNATE SIGNATURE MASTERED', 'const taken = tierSelections[t]'],
    engine: ['const activeTier = firstOpenTechniqueTier(n, s.techs);', 'pendingPerks(n, s.techs)'],
    sw: ['shadow-village-depth-v1-jutsu-potential-v13-1-signature-hotfix'],
}
for path, needles in checks.items():
    text = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v13.1 validation failed: {needle} missing from {path}')

print('Village depth v13.1 save-compatible innate-signature technique-tree hotfix applied')
