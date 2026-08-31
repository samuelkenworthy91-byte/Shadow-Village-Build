from pathlib import Path
import re

ROOT = Path("app")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Types: Bingo contact/fate state plus battle context.
# ---------------------------------------------------------------------------
p = "src/game/bingo.ts"
s = read(p)
if '| "defeated"' not in s:
    s = s.replace('  | "active_hunt"\n  | "escaped"', '  | "active_hunt"\n  | "defeated"\n  | "escaped"', 1)
if "pendingCaptureBonus?: number;" not in s:
    s = s.replace('  rewardsClaimed?: boolean;\n}', '  rewardsClaimed?: boolean;\n  /** Preserved modifier from the hunt until the player chooses the target fate. */\n  pendingCaptureBonus?: number;\n}', 1)
write(p, s)

p = "src/game/types.ts"
s = read(p)
s, n = re.subn(r'mode\?: "raid" \| "exam";', 'mode?: "raid" | "exam" | "bingo";', s, count=1)
if n == 0 and 'mode?: "raid" | "exam" | "bingo";' not in s:
    raise SystemExit("Bingo battle mode anchor not found")
if "bingoTargetId?: string | null;" not in s:
    anchor = '  examTargetRank?: NinRank | null;\n'
    if anchor not in s:
        raise SystemExit("Bingo Battle context anchor not found")
    s = s.replace(anchor, anchor + '  bingoTargetId?: string | null;\n  bingoCaptureBonus?: number;\n  bingoTargetCannotFleeRounds?: number;\n', 1)
write(p, s)
print("Bingo battle types: applied")

# ---------------------------------------------------------------------------
# Battle engine: construct one bespoke target against the three hunt members.
# Hunt-event HP/chakra/injury/ambush state is carried into the real fight.
# ---------------------------------------------------------------------------
p = "src/game/battle.ts"
s = read(p)
if 'from "./bingo"' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith("import ")), default=0)
    lines.insert(insert_at, 'import { ensureBingoState } from "./bingo";')
    s = "\n".join(lines) + ("\n" if read(p).endswith("\n") else "")

if "export interface BingoBattleConfig" not in s:
    anchor = '/* ---------------- turn order ---------------- */'
    if anchor not in s:
        raise SystemExit("Bingo battle insertion anchor not found")
    block = r'''export interface BingoBattleMemberConfig {
  ninjaId: number;
  hpRatio: number;
  chakraRatio: number;
  statuses: string[];
  delayedRounds: number;
}

export interface BingoBattleConfig {
  targetId: string;
  targetName: string;
  targetEpithet: string;
  targetSprite: string;
  targetLevel: number;
  threat: "B" | "A" | "S" | "S+" | "SS" | "BLACK";
  focus: string[];
  members: BingoBattleMemberConfig[];
  captureBonus: number;
  targetHpRatio: number;
  targetChakraRatio: number;
  playerAmbushRounds: number;
  enemyAmbushRounds: number;
  targetCannotFleeRounds: number;
}

/**
 * Start the contact battle at the end of a Bingo hunt. This deliberately uses
 * the same turn-based engine as raids/exams, but with one heavily scaled unique
 * missing-nin and exactly the three hunters whose resources survived the hunt.
 */
export function startBingoBattle(s: GameState, defenders: Ninja[], cfg: BingoBattleConfig): Battle {
  const allies = defenders.slice(0, 3).map(unitFromNinja);
  for (const ally of allies) {
    const carried = cfg.members.find((m) => m.ninjaId === ally.ninjaId);
    if (!carried) continue;
    ally.hp = Math.max(1, Math.min(ally.maxHp, Math.round(ally.maxHp * carried.hpRatio)));
    ally.cp = Math.max(0, Math.min(ally.maxCp, Math.round(ally.maxCp * carried.chakraRatio)));
    ally.stun = Math.max(ally.stun ?? 0, carried.delayedRounds + cfg.enemyAmbushRounds);
    if (carried.statuses.includes("poisoned")) {
      ally.burnRounds = Math.max(ally.burnRounds ?? 0, 3);
      ally.burnDamage = Math.max(ally.burnDamage ?? 0, Math.max(1, Math.round(ally.maxHp * 0.04)));
    }
    if (carried.statuses.includes("sealed")) ally.cp = Math.max(0, Math.round(ally.cp * 0.75));
  }

  const threatScale = ({ B: 1.0, A: 1.10, S: 1.22, "S+": 1.34, SS: 1.48, BLACK: 1.64 } as const)[cfg.threat];
  const hpScale = ({ B: 1.45, A: 1.72, S: 2.05, "S+": 2.38, SS: 2.78, BLACK: 3.25 } as const)[cfg.threat];
  const power = Math.max(18, 7 + cfg.targetLevel * 1.12);
  const foe = makeEnemy(0, "dread_veteran", power);
  foe.uid = "e0";
  foe.foe = true;
  foe.ninjaId = null;
  foe.kind = cfg.targetSprite.split("/").pop()?.replace(/\.png$/i, "") ?? "dread_veteran";
  foe.name = cfg.targetName;
  foe.level = cfg.targetLevel;
  foe.maxHp = Math.round(foe.maxHp * hpScale);
  foe.hp = Math.max(1, Math.round(foe.maxHp * Math.max(0.10, Math.min(1, cfg.targetHpRatio))));
  foe.maxCp = Math.round(foe.maxCp * (1.05 + (threatScale - 1) * 0.6));
  foe.cp = Math.max(0, Math.round(foe.maxCp * Math.max(0.10, Math.min(1, cfg.targetChakraRatio))));
  foe.atk *= threatScale;
  foe.def *= 1 + (threatScale - 1) * 0.72;
  foe.spd *= 1 + (threatScale - 1) * 0.48;
  foe.nin *= threatScale;
  foe.gen *= 1 + (threatScale - 1) * 0.80;
  foe.crit = Math.min(0.42, foe.crit + (threatScale - 1) * 0.16);
  foe.dodge = Math.min(0.30, foe.dodge + (threatScale - 1) * 0.10);
  foe.stun = Math.max(foe.stun ?? 0, cfg.playerAmbushRounds);

  // Skill-focus identities change the fight numerically without introducing a
  // second bespoke battle engine.
  for (const focus of cfg.focus) {
    if (focus === "ken") { foe.atk *= 1.08; foe.crit = Math.min(0.48, foe.crit + 0.03); }
    else if (focus === "tai") { foe.atk *= 1.06; foe.def *= 1.06; }
    else if (focus === "nin") foe.nin *= 1.10;
    else if (focus === "gen") foe.gen *= 1.12;
    else if (focus === "spd") { foe.spd *= 1.10; foe.dodge = Math.min(0.34, foe.dodge + 0.03); }
    else if (focus === "doj") { foe.crit = Math.min(0.48, foe.crit + 0.04); foe.dodge = Math.min(0.34, foe.dodge + 0.02); }
    else if (focus === "tac") { foe.def *= 1.08; foe.spd *= 1.04; }
    else if (focus === "med") { foe.maxHp = Math.round(foe.maxHp * 1.10); foe.hp = Math.min(foe.maxHp, Math.round(foe.hp * 1.10)); }
    else if (focus === "ste") { foe.crit = Math.min(0.48, foe.crit + 0.03); foe.dodge = Math.min(0.34, foe.dodge + 0.03); }
  }

  const b: Battle = {
    round: 1,
    units: [...allies, foe],
    order: [],
    idx: 0,
    state: "choose",
    log: [{ t: `Target contact: ${cfg.targetName} ${cfg.targetEpithet}.`, kind: "info" }],
    clan: `${cfg.threat} BINGO · ${cfg.targetEpithet}`,
    gold: 0,
    score: 0,
    flash: null,
    acting: null,
    mode: "bingo",
    examTargetRank: null,
    bingoTargetId: cfg.targetId,
    bingoCaptureBonus: cfg.captureBonus,
    bingoTargetCannotFleeRounds: cfg.targetCannotFleeRounds,
  };
  rollOrder(b, s.b.tower, true);
  return b;
}

'''
    s = s.replace(anchor, block + anchor, 1)

# Bingo combat is lethal to the hunter cell. A victory enters a fate decision
# instead of paying a bounty automatically. A defeat makes the target escape.
if "Bingo target contact resolution" not in s:
    anchor = '  // Promotion exams are self-contained duels: no village damage, raid rewards or injury state.\n'
    if anchor not in s:
        raise SystemExit("Bingo finishBattle anchor not found")
    block = r'''  // Bingo target contact resolution: normal 0 HP is permanent death here.
  if (b.mode === "bingo") {
    const targetId = b.bingoTargetId ?? null;
    const bingo = ensureBingoState(s);
    const progress = targetId ? bingo.targets[targetId] : null;
    const deadIds = new Set(
      b.units.filter((u) => !u.foe && !u.alive && u.ninjaId != null).map((u) => u.ninjaId as number),
    );

    for (const u of b.units.filter((x) => !x.foe && x.ninjaId != null)) {
      const n = s.ninjas.find((x) => x.id === u.ninjaId);
      if (!n) continue;
      if (!deadIds.has(n.id)) {
        n.status = "ready";
        n.daysLeft = 0;
        n.missionId = null;
      }
    }
    for (const id of deadIds) {
      const n = s.ninjas.find((x) => x.id === id);
      if (n) s.log.push({ txt: `${n.name} was killed during the Bingo hunt.`, kind: "bad", id: Date.now() + id });
    }
    if (deadIds.size) s.ninjas = s.ninjas.filter((n) => !deadIds.has(n.id));

    if (progress) {
      if (won) {
        progress.status = "defeated";
        progress.locationKnown = true;
        progress.pendingCaptureBonus = Math.max(0, b.bingoCaptureBonus ?? 0);
        s.log.push({ txt: "The missing-nin is beaten. Decide whether to kill them or attempt a live capture.", kind: "great", id: Date.now() });
      } else {
        progress.status = "escaped";
        progress.locationKnown = false;
        progress.intel = Math.max(40, progress.intel - 8);
        progress.pendingCaptureBonus = undefined;
        s.log.push({ txt: "The hunter cell was defeated. The target escaped and changed operating area.", kind: "bad", id: Date.now() });
      }
    }
    const runtime = bingo as typeof bingo & { activeHunt?: unknown };
    runtime.activeHunt = null;
    s.battle = null;
    s.phase = "playing";
    return;
  }

'''
    s = s.replace(anchor, block + anchor, 1)

write(p, s)
print("Bingo target battle engine: applied")

# ---------------------------------------------------------------------------
# Hunt runtime: launch contact battle and resolve post-battle kill/capture fate.
# ---------------------------------------------------------------------------
p = "src/game/bingoHunt.ts"
s = read(p)
if 'from "./battle"' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith("import ")), default=0)
    lines.insert(insert_at, 'import { startBingoBattle } from "./battle";')
    s = "\n".join(lines) + ("\n" if read(p).endswith("\n") else "")

if "export function beginBingoBossBattle" not in s:
    anchor = '\nexport function abandonBingoHunt(s: GameState): boolean {'
    if anchor not in s:
        raise SystemExit("Bingo boss launch insertion anchor not found")
    block = r'''
export function beginBingoBossBattle(s: GameState): { ok: boolean; error?: string } {
  const run = activeBingoHunt(s);
  if (!run) return { ok: false, error: "No active hunt." };
  const target = BINGO_TARGET_BY_ID[run.targetId];
  if (!target) return { ok: false, error: "Target dossier not found." };
  if (!huntReadyForBoss(s)) return { ok: false, error: "Complete the pursuit stages first." };
  const hunters = run.members.map((m) => s.ninjas.find((n) => n.id === m.ninjaId)).filter((n): n is Ninja => !!n);
  if (hunters.length !== BINGO_ACTIVE_PARTY_SIZE) return { ok: false, error: "The hunter cell is no longer complete." };

  s.battle = startBingoBattle(s, hunters, {
    targetId: target.id,
    targetName: target.name,
    targetEpithet: target.epithet,
    targetSprite: target.sprite,
    targetLevel: target.level,
    threat: target.threat,
    focus: target.focus,
    members: run.members,
    captureBonus: run.captureBonus,
    targetHpRatio: run.targetHpRatio,
    targetChakraRatio: run.targetChakraRatio,
    playerAmbushRounds: run.playerAmbushRounds,
    enemyAmbushRounds: run.enemyAmbushRounds,
    targetCannotFleeRounds: run.targetCannotFleeRounds,
  });
  s.phase = "battle";
  return { ok: true };
}

export function bingoCaptureChance(s: GameState, targetId: string): number {
  const target = BINGO_TARGET_BY_ID[targetId];
  const progress = ensureBingoState(s).targets[targetId];
  if (!target || !progress) return 0;
  const intelBonus = Math.min(0.20, progress.intel * 0.002);
  return Math.max(0.08, Math.min(0.92, target.captureBaseChance + intelBonus + (progress.pendingCaptureBonus ?? 0)));
}

export function resolveBingoFate(s: GameState, targetId: string, fate: "kill" | "capture"): { ok: boolean; error?: string; result?: string; captured?: boolean } {
  const bingo = ensureBingoState(s);
  const target = BINGO_TARGET_BY_ID[targetId];
  const progress = bingo.targets[targetId];
  if (!target || !progress) return { ok: false, error: "Target dossier not found." };
  if (progress.status !== "defeated") return { ok: false, error: "This target is not awaiting a fate decision." };

  if (fate === "kill") {
    progress.status = "killed";
    progress.outcome = "killed";
    progress.locationKnown = false;
    progress.rewardsClaimed = true;
    progress.pendingCaptureBonus = undefined;
    s.gold += target.bountyDead;
    s.score += Math.round(target.bountyDead / 150);
    const result = `${target.name} was killed. Dead bounty collected: ${target.bountyDead.toLocaleString()} gold.`;
    s.log.push({ txt: result, kind: "great", id: Date.now() });
    return { ok: true, result, captured: false };
  }

  const chance = bingoCaptureChance(s, targetId);
  if (Math.random() <= chance) {
    progress.status = "captured";
    progress.outcome = "captured";
    progress.locationKnown = false;
    progress.rewardsClaimed = true;
    progress.pendingCaptureBonus = undefined;
    if (!bingo.detention.prisonerIds.includes(targetId)) bingo.detention.prisonerIds.push(targetId);
    s.gold += target.bountyAlive;
    s.score += Math.round(target.bountyAlive / 125);
    const result = `${target.name} was captured alive. Live bounty collected: ${target.bountyAlive.toLocaleString()} gold.`;
    s.log.push({ txt: result, kind: "great", id: Date.now() });
    return { ok: true, result, captured: true };
  }

  progress.status = "escaped";
  progress.locationKnown = false;
  progress.intel = Math.max(45, progress.intel - 6);
  progress.pendingCaptureBonus = undefined;
  const result = `${target.name} broke free during the capture attempt. Re-establish their location before hunting again.`;
  s.log.push({ txt: result, kind: "bad", id: Date.now() });
  return { ok: true, result, captured: false };
}
'''
    s = s.replace(anchor, block + anchor, 1)
write(p, s)
print("Bingo boss launch + fate resolution: applied")

# ---------------------------------------------------------------------------
# Enemy art: unique Bingo portrait instead of a generic raid class image.
# ---------------------------------------------------------------------------
p = "src/components/NinjaSprite.tsx"
s = read(p)
if 'kind.startsWith("bingo_")' not in s:
    anchor = '  const meta = ENEMY_KINDS[kind] ?? ENEMY_KINDS.rogue_genin;\n'
    if anchor not in s:
        raise SystemExit("Bingo enemy art anchor not found")
    add = '''  if (kind.startsWith("bingo_")) {\n    return (\n      <img src={`/bingo/${kind}.png`} alt="" aria-hidden draggable={false} decoding="async"\n        style={{ width: h * 0.95, height: h, objectFit: "contain", objectPosition: "center bottom", opacity: dead ? 0.28 : 1,\n          filter: dead ? "grayscale(1) brightness(0.65)" : "drop-shadow(0 3px 7px rgba(0,0,0,.45))", userSelect: "none", pointerEvents: "none" }} />\n    );\n  }\n'''
    s = s.replace(anchor, add + anchor, 1)
write(p, s)
print("Bingo unique enemy art: applied")

# ---------------------------------------------------------------------------
# Bingo UI: enable the real boss battle button and add the post-fight fate UI.
# ---------------------------------------------------------------------------
p = "src/components/BingoBookScreen.tsx"
s = read(p)
if "beginBingoBossBattle," not in s:
    s = s.replace('  abandonBingoHunt,\n', '  abandonBingoHunt,\n  beginBingoBossBattle,\n  bingoCaptureChance,\n', 1)
    s = s.replace('  resolveCurrentHuntEvent,\n', '  resolveCurrentHuntEvent,\n  resolveBingoFate,\n', 1)

old = '<button type="button" disabled className="mt-2 rounded-lg bg-vermil px-3 py-2 text-[9px] font-black text-white opacity-50">BOSS BATTLE · NEXT IMPLEMENTATION PASS</button>'
if old in s:
    new = '<button type="button" onClick={() => { const result = beginBingoBossBattle(s); if (!result.ok) setLastResult(result.error ?? "Unable to begin target battle."); else onChanged(); }} className="mt-2 rounded-lg bg-vermil px-3 py-2 text-[9px] font-black text-white">BEGIN TARGET BATTLE</button>'
    s = s.replace(old, new, 1)
elif "BEGIN TARGET BATTLE" not in s:
    raise SystemExit("Bingo boss button anchor not found")

if "const defeated = progress.status === \"defeated\";" not in s:
    s = s.replace('  const resolved = ["captured", "killed", "resolved", "recruited"].includes(progress.status);', '  const resolved = ["captured", "killed", "resolved", "recruited"].includes(progress.status);\n  const defeated = progress.status === "defeated";\n  const captureChance = defeated ? bingoCaptureChance(s, target.id) : 0;', 1)

# Replace the standard action row with a fate decision when contact battle was won.
old = '<div className="mt-3 grid grid-cols-2 gap-2"><button disabled={resolved || !!queued} onClick={gather} className="rounded-xl bg-[#355f8c] px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">{queued ? queued.squad.length ? "INTEL TEAM OUT" : "INTEL ON BOARD" : "GATHER INTEL"}</button><button disabled={!progress.locationKnown || resolved || !!activeBingoHunt(s)} onClick={onPrepare} className="rounded-xl bg-vermil px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">PREPARE HUNT</button></div>'
if old in s:
    new = '''{defeated ? <div className="mt-3 rounded-xl bg-gold/[0.06] p-3 ring-1 ring-gold/20"><p className="text-[9px] font-black tracking-wider text-gold">TARGET DEFEATED · FATE DECISION</p><p className="mt-1 text-[8.5px] leading-relaxed text-paper/50">Kill guarantees the dead bounty. Live capture pays more and sends the missing-nin to detention, but a failed restraint attempt lets them escape.</p><div className="mt-2 grid grid-cols-2 gap-2"><button onClick={() => { if (!window.confirm(`Kill ${target.name}? This resolves the dossier permanently.`)) return; const r=resolveBingoFate(s,target.id,"kill"); if(r.ok) onChanged(); else window.alert(r.error); }} className="rounded-xl bg-vermil px-3 py-2.5 text-[9px] font-black text-white">KILL · {target.bountyDead.toLocaleString()}</button><button onClick={() => { if (!window.confirm(`Attempt live capture? Current chance: ${Math.round(captureChance*100)}%. A failure lets the target escape.`)) return; const r=resolveBingoFate(s,target.id,"capture"); if(r.ok) { window.alert(r.result ?? "Fate resolved."); onChanged(); } else window.alert(r.error); }} className="rounded-xl bg-jade px-3 py-2.5 text-[9px] font-black text-[#102016]">CAPTURE · {Math.round(captureChance*100)}%</button></div></div> : <div className="mt-3 grid grid-cols-2 gap-2"><button disabled={resolved || !!queued} onClick={gather} className="rounded-xl bg-[#355f8c] px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">{queued ? queued.squad.length ? "INTEL TEAM OUT" : "INTEL ON BOARD" : "GATHER INTEL"}</button><button disabled={!progress.locationKnown || resolved || !!activeBingoHunt(s)} onClick={onPrepare} className="rounded-xl bg-vermil px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">PREPARE HUNT</button></div>}'''
    s = s.replace(old, new, 1)
elif "TARGET DEFEATED · FATE DECISION" not in s:
    raise SystemExit("Bingo dossier action row anchor not found")

s = s.replace('["identified", "located", "active_hunt", "escaped"].includes(p.status)', '["identified", "located", "active_hunt", "defeated", "escaped"].includes(p.status)')
write(p, s)
print("Bingo boss + fate UI: applied")

# Cache bump.
p = "public/sw.js"
s = read(p)
s = s.replace('const CACHE = "shadow-village-bingo-book-v3-80-targets";', 'const CACHE = "shadow-village-bingo-book-v4-boss-battles";')
write(p, s)
print("Bingo Book v4 boss battles complete")
