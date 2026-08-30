from pathlib import Path
import re

ROOT = Path('app')

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')

def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

# ---------------------------------------------------------------------------
# Battle state fields for persistent elemental effects.
# ---------------------------------------------------------------------------
p = 'src/game/types.ts'
s = read(p)
if 'burnRounds?: number;' not in s:
    anchor = '  equipmentSpecial: string | null; // gear technique id; separate from personal 奥義\n'
    add = '''  equipmentSpecial: string | null; // gear technique id; separate from personal 奥義\n  /** Temporary elemental-jutsu battle states. */\n  burnRounds?: number;\n  burnDamage?: number;\n  slowRounds?: number;\n  slowPct?: number;\n  jutsuGuardRounds?: number;\n  jutsuRegenRounds?: number;\n  jutsuRegen?: number;\n  jutsuCritRounds?: number;\n  jutsuCritBonus?: number;\n  jutsuSpeedRounds?: number;\n  jutsuSpeedBonus?: number;\n'''
    if anchor not in s:
        raise SystemExit('Unit equipmentSpecial anchor missing')
    s = s.replace(anchor, add, 1)
write(p, s)

# ---------------------------------------------------------------------------
# Battle engine: selected jutsu, target ranges and elemental identities.
# ---------------------------------------------------------------------------
p = 'src/game/battle.ts'
s = read(p)
if 'JUTSU_BY_ID' not in '\n'.join(s.splitlines()[:12]):
    s = s.replace('import { applyEquipmentToBattleUnit, equipmentSkillBonus } from "./equipment";', 'import { applyEquipmentToBattleUnit, equipmentSkillBonus } from "./equipment";\nimport { JUTSU_BY_ID, type JutsuDef } from "./jutsu";', 1)

# Slow/speed buffs affect initiative without permanently changing base SPD.
s = s.replace(
    'roll: u.spd * rnd(0.85, 1.15) + (u.foe ? 0 : towerLvl * 4) + (first && u.firstStrike ? 500 : u.firstStrike ? 12 : 0),',
    'roll: u.spd * (1 - ((u.slowRounds ?? 0) > 0 ? (u.slowPct ?? 0) : 0)) * (1 + ((u.jutsuSpeedRounds ?? 0) > 0 ? (u.jutsuSpeedBonus ?? 0) : 0)) * rnd(0.85, 1.15) + (u.foe ? 0 : towerLvl * 4) + (first && u.firstStrike ? 500 : u.firstStrike ? 12 : 0),'
)

# Jutsu barriers are weaker than the active Guard command but persist for rounds.
s = s.replace(
    '  if (target.guard && !pierce) dmg = Math.max(1, Math.round(dmg * 0.42));',
    '  if (target.guard && !pierce) dmg = Math.max(1, Math.round(dmg * 0.42));\n  else if ((target.jutsuGuardRounds ?? 0) > 0 && !pierce) dmg = Math.max(1, Math.round(dmg * 0.70));'
)

# Temporary Wind crit buff also affects normal strikes.
s = s.replace(
    '      const crit = Math.random() < u.crit;',
    '      const crit = Math.random() < clamp(u.crit + ((u.jutsuCritRounds ?? 0) > 0 ? (u.jutsuCritBonus ?? 0) : 0), 0, 0.9);',
    1,
)

if 'function useElementalJutsu' not in s:
    marker = 'export function doAction(b: Battle, action: BAction, targetUid?: string): { kind: string; targets: string[] } {'
    pos = s.find(marker)
    if pos < 0:
        raise SystemExit('doAction signature anchor missing')
    helper = r'''function useElementalJutsu(b: Battle, u: Unit, j: JutsuDef, targetUid?: string): { kind: string; targets: string[] } {
  if (u.cp < j.chakra) return { kind: "none", targets: [] };
  const foesSide = u.foe ? aliveAllies(b) : aliveFoes(b);
  const alliesSide = u.foe ? aliveFoes(b) : aliveAllies(b);
  const requested = targetUid ? unitById(b, targetUid) : undefined;
  let targets: Unit[] = [];
  if (j.target === "all_foes") targets = foesSide;
  else if (j.target === "all_allies") targets = alliesSide;
  else if (j.target === "self") targets = [u];
  else if (j.target === "ally") {
    const fallback = [...alliesSide].sort((a, z) => a.hp / a.maxHp - z.hp / z.maxHp)[0];
    const chosen = requested && requested.alive && requested.foe === u.foe ? requested : fallback;
    if (chosen) targets = [chosen];
  } else {
    const chosen = requested && requested.alive && requested.foe !== u.foe ? requested : foesSide[0];
    if (chosen) targets = [chosen];
  }
  if (!targets.length) return { kind: "none", targets: [] };

  u.cp -= j.chakra;
  let total = 0;
  let healed = 0;
  const hitNames: string[] = [];

  for (const t of targets) {
    if (!t.alive) continue;
    const friendly = t.foe === u.foe;
    if (j.power > 0 && !friendly) {
      const piercePct = j.effect === "pierce" ? (j.effectValue ?? 0) / 100 : 0;
      const critBonus = j.effect === "crit" ? (j.effectValue ?? 0) / 100 : 0;
      const tempCrit = (u.jutsuCritRounds ?? 0) > 0 ? (u.jutsuCritBonus ?? 0) : 0;
      const crit = Math.random() < clamp(u.crit + critBonus + tempCrit, 0, 0.92);
      const raw = (u.nin * 1.65 * u.jutsuPower * j.power) * rnd(0.9, 1.16) - t.def * 0.18 * (1 - piercePct);
      total += damage(b, u, t, raw * (crit ? u.critMult : 1), crit ? "crit" : "hit", piercePct > 0);
      hitNames.push(t.name);
    } else if (j.power > 0 && friendly) {
      const amt = Math.max(1, Math.round((u.nin * 0.55 + u.med * 0.65) * j.power));
      t.hp = Math.min(t.maxHp, t.hp + amt);
      healed += amt;
      b.flash = { uid: t.uid, amount: amt, kind: "heal", n: (b.flash?.n ?? 0) + 1 };
    }

    switch (j.effect) {
      case "burn": {
        if (!friendly && t.alive) {
          t.burnRounds = Math.max(t.burnRounds ?? 0, j.effectValue ?? 2);
          t.burnDamage = Math.max(t.burnDamage ?? 0, Math.max(1, Math.round(u.nin * (j.target === "all_foes" ? 0.13 : 0.18))));
        }
        break;
      }
      case "slow": {
        if (!friendly && t.alive) {
          t.slowRounds = Math.max(t.slowRounds ?? 0, Math.max(1, j.effectValue ?? 1));
          t.slowPct = Math.max(t.slowPct ?? 0, Math.min(0.35, 0.08 + (j.effectValue ?? 1) * 0.06));
        }
        break;
      }
      case "guard": {
        if (friendly) t.jutsuGuardRounds = Math.max(t.jutsuGuardRounds ?? 0, j.effectValue ?? 2);
        break;
      }
      case "stun": {
        if (!friendly && t.alive) {
          const chance = j.target === "all_foes" ? 0.32 : 0.58;
          if (Math.random() < chance) t.stun = Math.max(t.stun, j.effectValue ?? 1);
        }
        break;
      }
      case "cleanse": {
        if (friendly) {
          t.stun = 0;
          t.burnRounds = 0; t.burnDamage = 0;
          t.slowRounds = 0; t.slowPct = 0;
        }
        break;
      }
      case "regen": {
        if (friendly) {
          t.jutsuRegenRounds = Math.max(t.jutsuRegenRounds ?? 0, j.effectValue ?? 2);
          t.jutsuRegen = Math.max(t.jutsuRegen ?? 0, Math.max(2, Math.round(u.med * 0.42 + u.nin * 0.18)));
          t.jutsuGuardRounds = Math.max(t.jutsuGuardRounds ?? 0, 1);
        }
        break;
      }
      case "crit": {
        if (friendly && j.power <= 0) {
          t.jutsuCritRounds = Math.max(t.jutsuCritRounds ?? 0, 2);
          t.jutsuCritBonus = Math.max(t.jutsuCritBonus ?? 0, (j.effectValue ?? 10) / 100);
          t.jutsuSpeedRounds = Math.max(t.jutsuSpeedRounds ?? 0, 2);
          t.jutsuSpeedBonus = Math.max(t.jutsuSpeedBonus ?? 0, 0.18);
        }
        break;
      }
    }
  }

  const effectText = j.effect === "none" ? "" : ` · ${j.effect.toUpperCase()}`;
  const resultText = total > 0 ? ` for ${total}` : healed > 0 ? ` restoring ${healed} HP` : "";
  log(b, `${u.name} uses ${j.name}${resultText}${effectText}`, total > 0 ? "hit" : healed > 0 ? "heal" : "info");
  return { kind: "jutsu", targets: targets.map((t) => t.uid) };
}

'''
    s = s[:pos] + helper + s[pos:]

# Add optional jutsu id argument and route selected techniques through the new resolver.
s = s.replace(
    'export function doAction(b: Battle, action: BAction, targetUid?: string): { kind: string; targets: string[] } {',
    'export function doAction(b: Battle, action: BAction, targetUid?: string, jutsuId?: string): { kind: string; targets: string[] } {'
)
old_jutsu = '''    case "jutsu": {\n      const t = target && target.foe !== u.foe ? target : foesSide[0];'''
new_jutsu = '''    case "jutsu": {\n      const selectedJutsu = jutsuId ? JUTSU_BY_ID[jutsuId] : undefined;\n      if (selectedJutsu) return useElementalJutsu(b, u, selectedJutsu, targetUid);\n      const t = target && target.foe !== u.foe ? target : foesSide[0];'''
if old_jutsu not in s:
    raise SystemExit('generic jutsu case anchor missing')
s = s.replace(old_jutsu, new_jutsu, 1)

# Tick burns, regen and temporary elemental states at round boundaries.
old_round = '''        u.cp = Math.min(u.maxCp, u.cp + 3 + u.regen);\n        if (u.regen > 0) u.hp = Math.min(u.maxHp, u.hp + u.regen);\n        if (u.stun > 0) u.stun--;'''
new_round = '''        u.cp = Math.min(u.maxCp, u.cp + 3 + u.regen);\n        if (u.regen > 0) u.hp = Math.min(u.maxHp, u.hp + u.regen);\n        if ((u.jutsuRegenRounds ?? 0) > 0 && (u.jutsuRegen ?? 0) > 0) {\n          const heal = Math.min(u.maxHp - u.hp, u.jutsuRegen ?? 0);\n          if (heal > 0) { u.hp += heal; log(b, `${u.name} recovers ${heal} HP from a water current`, "heal"); }\n          u.jutsuRegenRounds = Math.max(0, (u.jutsuRegenRounds ?? 0) - 1);\n        }\n        if ((u.burnRounds ?? 0) > 0 && (u.burnDamage ?? 0) > 0) {\n          const burn = Math.min(u.hp, u.burnDamage ?? 0);\n          u.hp = Math.max(0, u.hp - burn);\n          u.burnRounds = Math.max(0, (u.burnRounds ?? 0) - 1);\n          log(b, `${u.name} burns for ${burn}`, "hit");\n          if (u.hp <= 0) { u.alive = false; log(b, `${u.name} is down!`, "down"); }\n        }\n        if ((u.slowRounds ?? 0) > 0) u.slowRounds = Math.max(0, (u.slowRounds ?? 0) - 1);\n        if ((u.jutsuGuardRounds ?? 0) > 0) u.jutsuGuardRounds = Math.max(0, (u.jutsuGuardRounds ?? 0) - 1);\n        if ((u.jutsuCritRounds ?? 0) > 0) u.jutsuCritRounds = Math.max(0, (u.jutsuCritRounds ?? 0) - 1);\n        if ((u.jutsuSpeedRounds ?? 0) > 0) u.jutsuSpeedRounds = Math.max(0, (u.jutsuSpeedRounds ?? 0) - 1);\n        if (u.stun > 0) u.stun--;'''
if old_round not in s:
    raise SystemExit('round status anchor missing')
s = s.replace(old_round, new_round, 1)
write(p, s)

# ---------------------------------------------------------------------------
# Battle UI: Jutsu opens the equipped-technique submenu, then respects each range.
# ---------------------------------------------------------------------------
p = 'src/components/BattleScreen.tsx'
s = read(p)
if 'JUTSU_BY_ID' not in '\n'.join(s.splitlines()[:15]):
    s = s.replace('import { NATURE_META } from "../game/content";', 'import { NATURE_META } from "../game/content";\nimport { JUTSU_BY_ID, type JutsuDef } from "../game/jutsu";', 1)
if 'function jutsuTargetMode' not in s:
    anchor = 'function targetPrompt(mode: TargetMode, action: BAction | null): string {'
    helper = '''function jutsuTargetMode(j: JutsuDef): TargetMode {\n  if (j.target === "foe") return "foe";\n  if (j.target === "ally") return "ally";\n  return null;\n}\n\n'''
    if anchor not in s:
        raise SystemExit('targetPrompt anchor missing')
    s = s.replace(anchor, helper + anchor, 1)

s = s.replace('  onAction: (a: BAction, target?: string) => void;', '  onAction: (a: BAction, target?: string, jutsuId?: string) => void;')
if 'const [pendingJutsu' not in s:
    s = s.replace('  const [pending, setPending] = useState<BAction | null>(null);', '  const [pending, setPending] = useState<BAction | null>(null);\n  const [pendingJutsu, setPendingJutsu] = useState<string | null>(null);\n  const [jutsuOpen, setJutsuOpen] = useState(false);', 1)

# Current ninja/loadout is derived directly from live game state.
if 'const equippedJutsu' not in s:
    anchor = '  const isPlayerTurn = b.state === "choose" && cur && !cur.foe;'
    add = '''  const isPlayerTurn = b.state === "choose" && cur && !cur.foe;\n  const activeNinja = cur?.ninjaId != null ? s.ninjas.find((n) => n.id === cur.ninjaId) : undefined;\n  const equippedJutsu = (activeNinja?.jutsuEquipped ?? []).map((id) => JUTSU_BY_ID[id]).filter((j): j is JutsuDef => !!j);'''
    if anchor not in s:
        raise SystemExit('isPlayerTurn anchor missing')
    s = s.replace(anchor, add, 1)

s = s.replace('  const pendingMode = pending ? targetModeForAction(cur, b, pending) : null;', '  const pendingMode = pending === "jutsu" && pendingJutsu ? jutsuTargetMode(JUTSU_BY_ID[pendingJutsu]) : pending ? targetModeForAction(cur, b, pending) : null;')
s = s.replace('    setPending(null);\n  }, [b.idx, b.round]);', '    setPending(null);\n    setPendingJutsu(null);\n    setJutsuOpen(false);\n  }, [b.idx, b.round]);')

# Main Jutsu command opens submenu when a loadout exists.
old_choose = '''  const choose = (a: BAction) => {\n    const mode = targetModeForAction(cur, b, a);'''
new_choose = '''  const choose = (a: BAction) => {\n    if (a === "jutsu" && equippedJutsu.length > 0) {\n      setPending(null);\n      setPendingJutsu(null);\n      setJutsuOpen(true);\n      return;\n    }\n    const mode = targetModeForAction(cur, b, a);'''
if old_choose not in s:
    raise SystemExit('choose action anchor missing')
s = s.replace(old_choose, new_choose, 1)

if 'const chooseJutsu =' not in s:
    marker = '  const allies = b.units.filter((u) => !u.foe);'
    helper = '''  const chooseJutsu = (j: JutsuDef) => {\n    if (!cur || cur.cp < j.chakra) return;\n    const mode = jutsuTargetMode(j);\n    if (!mode) {\n      onAction("jutsu", undefined, j.id);\n      setJutsuOpen(false);\n      return;\n    }\n    const targets = mode === "foe" ? aliveFoes(b) : aliveAllies(b);\n    if (targets.length === 1) {\n      onAction("jutsu", targets[0].uid, j.id);\n      setJutsuOpen(false);\n    } else {\n      setPending("jutsu");\n      setPendingJutsu(j.id);\n      setJutsuOpen(false);\n    }\n  };\n\n'''
    if marker not in s:
        raise SystemExit('allies UI anchor missing')
    s = s.replace(marker, helper + marker, 1)

# Target clicks carry the chosen jutsu id through to App/battle engine.
s = s.replace('onAction(pending, u.uid);\n                    setPending(null);', 'onAction(pending, u.uid, pendingJutsu ?? undefined);\n                    setPending(null);\n                    setPendingJutsu(null);')
# There are enemy and ally target buttons; replacement applies both occurrences.

# Cancel target selection clears selected jutsu too.
s = s.replace('<button onClick={() => setPending(null)} className="btn-ghost h-9 rounded-lg px-4 text-[11px] font-black">CANCEL</button>', '<button onClick={() => { setPending(null); setPendingJutsu(null); }} className="btn-ghost h-9 rounded-lg px-4 text-[11px] font-black">CANCEL</button>')

# Render jutsu submenu before generic target prompt.
old_branch = '''          ) : pending ? (\n            <div className="flex h-11 items-center gap-2">'''
new_branch = '''          ) : jutsuOpen && isPlayerTurn && cur ? (\n            <div className="space-y-1.5">\n              <div className="flex items-center gap-2">\n                <span className="text-[9px] font-black tracking-[0.18em] text-gold">EQUIPPED JUTSU</span>\n                <span className="text-[8.5px] text-paper/40">Choose technique · range/effect shown below</span>\n                <button onClick={() => setJutsuOpen(false)} className="btn-ghost ml-auto h-7 rounded-lg px-2.5 text-[9px] font-black">BACK</button>\n              </div>\n              <div className="grid grid-cols-2 gap-1 sm:grid-cols-4">\n                {equippedJutsu.map((j) => {\n                  const affordable = cur.cp >= j.chakra;\n                  return <button key={j.id} disabled={!affordable} onClick={() => chooseJutsu(j)} className="btn-ink min-h-[54px] rounded-lg px-2 py-1.5 text-left disabled:opacity-35">\n                    <div className="flex items-center justify-between gap-1"><span className="truncate text-[9.5px] font-black text-paper">{j.name}</span><span className="text-[8px] font-black text-[#7db9ec]">{j.chakra}cp</span></div>\n                    <p className="mt-0.5 text-[7.5px] font-bold uppercase tracking-wide text-gold/70">{j.target.replace(/_/g, " ")} · {j.effect}{j.effectValue ? ` ${j.effectValue}` : ""}</p>\n                    <p className="mt-0.5 line-clamp-1 text-[7.5px] text-paper/35">{j.desc}</p>\n                  </button>;\n                })}\n              </div>\n            </div>\n          ) : pending ? (\n            <div className="flex h-11 items-center gap-2">'''
if old_branch not in s:
    raise SystemExit('pending render branch anchor missing')
s = s.replace(old_branch, new_branch, 1)

# Main Jutsu button is enabled whenever at least one equipped jutsu is affordable;
# its fixed generic cost is replaced by a SELECT cue.
s = s.replace('                  const ok = canUse(cur, a.id);', '                  const ok = a.id === "jutsu" && equippedJutsu.length > 0 ? equippedJutsu.some((j) => cur.cp >= j.chakra) : canUse(cur, a.id);')
s = s.replace('{COSTS[a.id] > 0 && <span className="text-[7.5px] font-bold text-[#7db9ec]">{COSTS[a.id]}cp</span>}', '{a.id === "jutsu" && equippedJutsu.length > 0 ? <span className="text-[7.5px] font-bold text-gold/75">SELECT</span> : COSTS[a.id] > 0 && <span className="text-[7.5px] font-bold text-[#7db9ec]">{COSTS[a.id]}cp</span>}')
write(p, s)

# App passes selected jutsu through to battle.doAction.
p = 'src/App.tsx'
s = read(p)
s = s.replace('  const playerAct = (action: BAction, target?: string) => {', '  const playerAct = (action: BAction, target?: string, jutsuId?: string) => {', 1)
s = s.replace('  const playerAct = (action: BAction, target?: string, jutsuId?: string) => {\n    const st = sRef.current;\n    const b = st.battle;\n    if (!b || b.state !== "choose") return;\n    const res = bat.doAction(b, action, target);', '  const playerAct = (action: BAction, target?: string, jutsuId?: string) => {\n    const st = sRef.current;\n    const b = st.battle;\n    if (!b || b.state !== "choose") return;\n    const res = bat.doAction(b, action, target, jutsuId);', 1)
write(p, s)

# Cache bump while preserving v1 workflow validation namespace.
p = 'public/sw.js'
s = read(p)
s, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-depth-v1-jutsu-potential-v4-battle-jutsu";', s, count=1)
if n != 1:
    raise SystemExit('service worker cache constant missing')
write(p, s)

print('Village depth v4: equipped elemental jutsu battle submenu and effects applied')
