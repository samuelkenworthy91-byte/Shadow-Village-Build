from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{label}: anchor not found in {path}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: applied")


# ---------- battle UI target selection ----------
replace_once(
    "src/components/BattleScreen.tsx",
    'import type { BAction, Battle, GameState } from "../game/types";',
    'import type { BAction, Battle, GameState, Unit } from "../game/types";',
    "battle screen Unit type import",
)

replace_once(
    "src/components/BattleScreen.tsx",
    'import { COSTS, actionLabel, aliveAllies, aliveFoes, canUse, currentUnit, unitCombatPower } from "../game/battle";\n',
    'import { COSTS, actionLabel, aliveAllies, aliveFoes, canUse, currentUnit, unitCombatPower } from "../game/battle";\nimport { perkById } from "../game/perks";\n',
    "special metadata import",
)

replace_once(
    "src/components/BattleScreen.tsx",
    '''const ACTIONS: { id: BAction; icon: typeof Swords; kanji: string }[] = [\n  { id: "attack", icon: Swords, kanji: "撃" },\n  { id: "jutsu", icon: Zap, kanji: "術" },\n  { id: "genjutsu", icon: Wand2, kanji: "幻" },\n  { id: "heal", icon: Sparkles, kanji: "医" },\n  { id: "guard", icon: Shield, kanji: "守" },\n  { id: "special", icon: Flame, kanji: "奥" },\n];\n''',
    '''const ACTIONS: { id: BAction; icon: typeof Swords; kanji: string }[] = [\n  { id: "attack", icon: Swords, kanji: "撃" },\n  { id: "jutsu", icon: Zap, kanji: "術" },\n  { id: "genjutsu", icon: Wand2, kanji: "幻" },\n  { id: "heal", icon: Sparkles, kanji: "医" },\n  { id: "guard", icon: Shield, kanji: "守" },\n  { id: "special", icon: Flame, kanji: "奥" },\n];\n\ntype TargetMode = "foe" | "ally" | "downed_ally" | null;\n\nfunction specialTargetMode(cur: Unit | null, b: Battle): TargetMode {\n  if (!cur?.special) return null;\n  const perk = perkById(cur.special);\n  if (!perk?.tech) return null;\n\n  // Field-wide techniques resolve immediately because there is no single target.\n  if (perk.id === "shadowclone" || perk.id === "lg_summon") return null;\n\n  // Mystic Revival is targetable only while there are fallen allies to choose from.\n  // With nobody down it retains its existing party-wide healing behaviour.\n  if (perk.id === "mysticrevive") {\n    return b.units.some((u) => u.foe === cur.foe && !u.alive) ? "downed_ally" : null;\n  }\n\n  // Every other signature technique in the current roster is single-target offence.\n  return "foe";\n}\n\nfunction targetModeForAction(cur: Unit | null, b: Battle, a: BAction): TargetMode {\n  switch (a) {\n    case "attack":\n    case "jutsu":\n    case "genjutsu":\n      return "foe";\n    case "heal":\n      return "ally";\n    case "special":\n      return specialTargetMode(cur, b);\n    default:\n      return null;\n  }\n}\n\nfunction targetPrompt(mode: TargetMode, action: BAction | null): string {\n  if (action === "special" && mode === "downed_ally") return "Choose a fallen ally below to revive…";\n  if (mode === "ally") return "Choose an ally below…";\n  return "Choose a target above…";\n}\n''',
    "target selection helpers",
)

replace_once(
    "src/components/BattleScreen.tsx",
    '  const [pending, setPending] = useState<BAction | null>(null);\n',
    '  const [pending, setPending] = useState<BAction | null>(null);\n  const pendingMode = pending ? targetModeForAction(cur, b, pending) : null;\n',
    "pending target mode",
)

replace_once(
    "src/components/BattleScreen.tsx",
    '''  const needsTarget = (a: BAction) => a === "attack" || a === "jutsu" || a === "genjutsu";\n\n  const choose = (a: BAction) => {\n    if (!needsTarget(a)) {\n      onAction(a);\n      return;\n    }\n    const foes = aliveFoes(b);\n    if (foes.length === 1) onAction(a, foes[0].uid);\n    else setPending(a);\n  };\n''',
    '''  const choose = (a: BAction) => {\n    const mode = targetModeForAction(cur, b, a);\n    if (!mode) {\n      onAction(a);\n      return;\n    }\n\n    const foeTargets = aliveFoes(b);\n    const allyTargets = aliveAllies(b);\n    const downedAllyTargets = b.units.filter((u) => u.foe === cur?.foe && !u.alive);\n    const targets = mode === "foe" ? foeTargets : mode === "ally" ? allyTargets : downedAllyTargets;\n\n    // If only one valid target exists there is no meaningful choice to present.\n    if (targets.length === 1) {\n      onAction(a, targets[0].uid);\n    } else {\n      setPending(a);\n    }\n  };\n''',
    "action targeting flow",
)

replace_once(
    "src/components/BattleScreen.tsx",
    '            const targetable = pending !== null && u.alive;',
    '            const targetable = pendingMode === "foe" && u.alive;',
    "enemy target eligibility",
)

replace_once(
    "src/components/BattleScreen.tsx",
    '''          {allies.map((u) => {\n            const active = cur?.uid === u.uid && b.state === "choose";\n            const hit = flash?.uid === u.uid;\n            return (\n              <div\n                key={u.uid}\n                className={cn(\n                  "relative flex items-center gap-1.5 rounded-xl bg-black/45 p-1.5 ring-1 backdrop-blur transition",\n                  active ? "ring-gold shadow-[0_0_16px_rgba(244,198,79,0.3)]" : "ring-white/10",\n                  !u.alive && "opacity-40"\n                )}\n              >\n''',
    '''          {allies.map((u) => {\n            const active = cur?.uid === u.uid && b.state === "choose";\n            const hit = flash?.uid === u.uid;\n            const allyTargetable =\n              (pendingMode === "ally" && u.alive) ||\n              (pendingMode === "downed_ally" && !u.alive);\n            return (\n              <button\n                key={u.uid}\n                disabled={!allyTargetable}\n                onClick={() => {\n                  if (pending && allyTargetable) {\n                    onAction(pending, u.uid);\n                    setPending(null);\n                  }\n                }}\n                className={cn(\n                  "relative flex items-center gap-1.5 rounded-xl bg-black/45 p-1.5 text-left ring-1 backdrop-blur transition",\n                  active ? "ring-gold shadow-[0_0_16px_rgba(244,198,79,0.3)]" : "ring-white/10",\n                  allyTargetable && "cursor-pointer ring-2 ring-jade animate-pulse",\n                  !u.alive && !allyTargetable && "opacity-40",\n                  !allyTargetable && "cursor-default"\n                )}\n              >\n''',
    "ally target buttons",
)

replace_once(
    "src/components/BattleScreen.tsx",
    '''                </div>\n              </div>\n            );\n          })}\n        </div>\n\n        {/* command menu */}''',
    '''                </div>\n              </button>\n            );\n          })}\n        </div>\n\n        {/* command menu */}''',
    "ally target button close",
)

replace_once(
    "src/components/BattleScreen.tsx",
    '<p className="flex-1 text-[11.5px] font-bold text-gold">Choose a target above…</p>',
    '<p className="flex-1 text-[11.5px] font-bold text-gold">{targetPrompt(pendingMode, pending)}</p>',
    "contextual target prompt",
)


# ---------- targeted revival ----------
replace_once(
    "src/game/battle.ts",
    '''      if (p.id === "mysticrevive") {\n        const downed = b.units.find((x) => x.foe === u.foe && !x.alive);\n        if (downed) {''',
    '''      if (p.id === "mysticrevive") {\n        const downed = target && target.foe === u.foe && !target.alive\n          ? target\n          : b.units.find((x) => x.foe === u.foe && !x.alive);\n        if (downed) {''',
    "Mystic Revival chosen target",
)

print("v2.5 target selection patch complete")
