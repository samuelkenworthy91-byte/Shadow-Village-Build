from pathlib import Path

# Final post-stack cleanup for legacy personal Genjutsu-tree nodes.
perks_path = Path("app/src/game/perks.ts")
battle_path = Path("app/src/game/battle.ts")

perks = perks_path.read_text(encoding="utf-8")

# Mind Dagger belonged to the pre-v12 generic Genjutsu action. Learned Genjutsu now
# routes through genjutsu.ts/useLearnedGenjutsu, so the old auto-land/stun hook no
# longer affects the techniques players actually equip. Keep the legacy ID readable
# for old saves, but translate it to a normal working development node.
old_def = '''  minddagger: {
    id: "minddagger", name: "Mind Dagger", kanji: "刃", branch: "gen", kind: "combat", color: "#b46ae0",
    desc: "Genjutsu automatically lands and stuns the target for 2 rounds.",
  },'''
new_def = '''  minddagger: {
    id: "minddagger", name: "Mind Dagger", kanji: "刃", branch: "gen", kind: "combat", color: "#b46ae0",
    desc: "Legacy Genjutsu-tree node retained for old saves; current trees replace it with Illusion Discipline.",
  },'''
if old_def in perks:
    perks = perks.replace(old_def, new_def, 1)
elif new_def not in perks:
    raise SystemExit("Mind Dagger definition anchor not found")

mechanics_old = '  if (p.id === "minddagger") out.push("Genjutsu automatically lands and stuns the target for 2 rounds");\n'
if mechanics_old in perks:
    perks = perks.replace(mechanics_old, "", 1)

anchor = '  mindpressure: { id: "mindpressure", name: "Mental Pressure", kanji: "圧", branch: "gen", kind: "passive", color: "#b46ae0", desc: "+10% battle defence and +12% maximum chakra.", fx: { def: 1.10, cp: 1.12 } },\n'
replacement_node = '  illusiondiscipline: { id: "illusiondiscipline", name: "Illusion Discipline", kanji: "幻", branch: "gen", kind: "passive", color: "#b46ae0", desc: "+12% maximum chakra, +6 percentage points dodge and +4 percentage points mission success.", fx: { cp: 1.12, dodge: 0.06 }, village: { missionBonus: 0.04 } },\n'
if 'id: "illusiondiscipline"' not in perks:
    if anchor not in perks:
        raise SystemExit("Genjutsu replacement-node anchor not found")
    perks = perks.replace(anchor, anchor + replacement_node, 1)

obsolete_anchor = 'const OBSOLETE_TREE_TECHNIQUES = new Set([\n  "gatekeeper",'
if 'const OBSOLETE_TREE_TECHNIQUES = new Set([\n  "minddagger", "gatekeeper",' not in perks:
    if obsolete_anchor not in perks:
        raise SystemExit("Obsolete-technique set anchor not found")
    perks = perks.replace(obsolete_anchor, 'const OBSOLETE_TREE_TECHNIQUES = new Set([\n  "minddagger", "gatekeeper",', 1)

map_anchor = 'const TREE_TECHNIQUE_REPLACEMENTS: Record<string, string> = {\n  gatekeeper: "impactconditioning",'
if '  minddagger: "illusiondiscipline",' not in perks:
    if map_anchor not in perks:
        raise SystemExit("Technique replacement map anchor not found")
    perks = perks.replace(map_anchor, 'const TREE_TECHNIQUE_REPLACEMENTS: Record<string, string> = {\n  minddagger: "illusiondiscipline",\n  gatekeeper: "impactconditioning",', 1)

perks_path.write_text(perks, encoding="utf-8")

battle = battle_path.read_text(encoding="utf-8")
old_sure = '      const sure = u.perks.includes("minddagger");'
new_sure = '      const sure = false; // legacy Mind Dagger no longer overrides the modern learned-Genjutsu system'
if old_sure in battle:
    battle = battle.replace(old_sure, new_sure, 1)
elif new_sure not in battle:
    raise SystemExit("Legacy Mind Dagger battle hook anchor not found")
battle_path.write_text(battle, encoding="utf-8")

print("Genjutsu cleanup applied: Mind Dagger retired; old saves map to Illusion Discipline")
