from pathlib import Path

ROOT = Path("app")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Captured targets can now be interrogated and, where the dossier permits it,
# recruited into the village while retaining their unique Bingo portrait.
# ---------------------------------------------------------------------------
p = "src/game/types.ts"
s = read(p)
if "bingoArt?: string | null;" not in s:
    s = s.replace(
        "  examFails?: number;\n}",
        "  examFails?: number;\n  /** Unique recruited Bingo Book portrait; normal recruits leave this unset. */\n  bingoArt?: string | null;\n}",
        1,
    )
write(p, s)

p = "src/game/bingo.ts"
s = read(p)
if "interrogated?: boolean;" not in s:
    s = s.replace(
        "  pendingCaptureBonus?: number;\n}",
        "  pendingCaptureBonus?: number;\n  interrogated?: boolean;\n  recruitAttempts?: number;\n  lastRecruitAttemptDay?: number;\n}",
        1,
    )
write(p, s)
print("Bingo detention state fields: applied")

# ---------------------------------------------------------------------------
# Unique recruited target portraits. Bingo sprites use a squarer source canvas
# than normal player ninja art, so the renderer gets a dedicated fit/crop.
# ---------------------------------------------------------------------------
p = "src/game/ninjaArt.ts"
s = read(p)
s = s.replace(
    'export function ninjaArtSrc(n: { id: number; look: Look; legend?: string | null }): string {\n  return `/ninjas/ninja_${String(ninjaArtId(n)).padStart(3, "0")}.png`;\n}',
    'export function ninjaArtSrc(n: { id: number; look: Look; legend?: string | null; bingoArt?: string | null }): string {\n  if (n.bingoArt) return n.bingoArt;\n  return `/ninjas/ninja_${String(ninjaArtId(n)).padStart(3, "0")}.png`;\n}',
    1,
)
write(p, s)

p = "src/components/NinjaSprite.tsx"
s = read(p)
s = s.replace(
    '  n: { id: number; look: Look; nature: Nature; level: number; rank: NinRank; legend?: string | null };',
    '  n: { id: number; look: Look; nature: Nature; level: number; rank: NinRank; legend?: string | null; bingoArt?: string | null };',
    1,
)
if "const bingoPortrait = !!n.bingoArt;" not in s:
    s = s.replace(
        "  const src = ninjaArtSrc(n);\n  const artMeta = ninjaArtMeta(n);",
        "  const src = ninjaArtSrc(n);\n  const bingoPortrait = !!n.bingoArt;\n  const artMeta = ninjaArtMeta(n);",
        1,
    )
    s = s.replace(
        '  const width = h * (crop === "bust" ? BUST_RATIO : FULL_RATIO);\n  const bustImageH = h * BUST_SCALE;\n  const bustImageW = bustImageH * FULL_RATIO;\n  const bustTopPx = -(artMeta.bustTop / SPRITE_H) * bustImageH;',
        '  const width = h * (bingoPortrait ? (crop === "bust" ? 0.86 : 0.96) : (crop === "bust" ? BUST_RATIO : FULL_RATIO));\n  const bustImageH = bingoPortrait ? h * 1.62 : h * BUST_SCALE;\n  const bustImageW = bingoPortrait ? bustImageH * (438 / 422) : bustImageH * FULL_RATIO;\n  const bustTopPx = bingoPortrait ? -h * 0.18 : -(artMeta.bustTop / SPRITE_H) * bustImageH;',
        1,
    )
    s = s.replace(
        '              width: `${FULL_SCALE * 100}%`,\n              height: `${FULL_SCALE * 100}%`,',
        '              width: bingoPortrait ? "100%" : `${FULL_SCALE * 100}%`,\n              height: bingoPortrait ? "100%" : `${FULL_SCALE * 100}%`,',
        1,
    )
write(p, s)
print("Recruited Bingo portrait rendering: applied")

# ---------------------------------------------------------------------------
# Engine recruitment. Attempts are deliberately not ultra-rare: base chance is
# 65% at B down to 30% at SS, and every failed attempt adds +8pp after a 3-day
# cooldown. Roster capacity remains a hard rule so Exile keeps its purpose.
# ---------------------------------------------------------------------------
p = "src/game/engine.ts"
s = read(p)
s = s.replace(
    'import { refreshPendingMissingNin } from "./bingo";',
    'import { BINGO_TARGET_BY_ID, ensureBingoState, refreshPendingMissingNin } from "./bingo";',
    1,
)
if "export function bingoRecruitChance" not in s:
    anchor = "\nconst MISSION_SPEC: Record<Rank,"
    pos = s.find(anchor)
    if pos < 0:
        raise SystemExit("Bingo recruitment insertion anchor missing")
    block = r'''

export function bingoRecruitChance(s: GameState, targetId: string): number {
  const target = BINGO_TARGET_BY_ID[targetId];
  const progress = ensureBingoState(s).targets[targetId];
  if (!target || !progress || !target.recruitable) return 0;
  const base = ({ B: 0.65, A: 0.55, S: 0.45, "S+": 0.38, SS: 0.30, BLACK: 0 } as const)[target.threat];
  return Math.min(0.85, base + (progress.recruitAttempts ?? 0) * 0.08);
}

export function recruitBingoPrisoner(s: GameState, targetId: string): { ok: boolean; error?: string; result?: string; ninja?: Ninja } {
  const bingo = ensureBingoState(s);
  const target = BINGO_TARGET_BY_ID[targetId];
  const progress = bingo.targets[targetId];
  if (!target || !progress) return { ok: false, error: "Prisoner dossier not found." };
  if (progress.status !== "captured" || !bingo.detention.prisonerIds.includes(targetId)) return { ok: false, error: "That target is not in detention." };
  if (!target.recruitable) return { ok: false, error: "This missing-nin will not join Shadow Village." };
  if (!progress.interrogated) return { ok: false, error: "Interrogate the prisoner before attempting recruitment." };
  if (s.ninjas.length >= capOf(s)) return { ok: false, error: "The ninja roster is full. Exile someone or expand the Main Hall first." };
  const last = progress.lastRecruitAttemptDay ?? -999;
  if (s.day - last < 3) return { ok: false, error: `They will not negotiate again for ${3 - (s.day - last)} more day(s).` };

  const chance = bingoRecruitChance(s, targetId);
  progress.recruitAttempts = (progress.recruitAttempts ?? 0) + 1;
  progress.lastRecruitAttemptDay = s.day;
  if (Math.random() > chance) {
    bingo.detention.securityAlert = Math.min(100, bingo.detention.securityAlert + 6);
    const result = `${target.name} rejected the offer. A new approach can be made in three days; future attempts are slightly easier.`;
    s.log.push({ txt: result, kind: "bad", id: Date.now() });
    return { ok: true, result };
  }

  const n = makeNinja(s, true);
  const natureMap: Partial<Record<string, Nature>> = { Fire: "fire", Water: "water", Wind: "wind", Earth: "earth", Lightning: "light" };
  n.name = target.name;
  n.title = target.epithet;
  n.legend = null;
  n.bingoArt = target.sprite;
  n.pot = target.potential;
  n.level = target.level;
  n.xp = 0;
  n.sp = 3 + target.potential;
  n.rank = target.threat === "B" ? "chunin" : target.threat === "A" ? "jonin" : "anbu";
  n.nature = natureMap[target.elements[0]] ?? n.nature;
  n.secondaryNature = natureMap[target.elements[1]] ?? null;
  n.dojutsuAwakening = target.focus.includes("doj") ? "mission" : null;
  const potGrowth = potentialDevelopmentMultiplier(target.potential);
  for (const k of SKILLS) {
    if (k === "doj" && !target.focus.includes("doj")) { n.s[k] = 0; n.growth[k] = 0; continue; }
    const specialist = target.focus.includes(k);
    n.s[k] = Math.max(n.s[k], Math.round(13 + target.level * (specialist ? 1.38 : 1.05)));
    n.growth[k] = Math.max(n.growth[k], (specialist ? 1.48 : 1.05) * potGrowth);
  }
  n.status = "ready";
  n.daysLeft = 0;
  n.missionId = null;
  s.ninjas.push(n);

  progress.status = "recruited";
  progress.outcome = "recruited";
  bingo.detention.prisonerIds = bingo.detention.prisonerIds.filter((id) => id !== targetId);
  bingo.detention.securityAlert = Math.max(0, bingo.detention.securityAlert - 8);
  const result = `${target.name} accepted a place in Shadow Village and joined the active roster.`;
  s.log.push({ txt: result, kind: "great", id: Date.now() });
  return { ok: true, result, ninja: n };
}
'''
    s = s[:pos] + block + s[pos:]
write(p, s)
print("Bingo prisoner recruitment: applied")

# ---------------------------------------------------------------------------
# First interrogation exposes organisations and advances up to three linked
# dossiers. Unaffiliated prisoners still reveal one useful target lead.
# ---------------------------------------------------------------------------
p = "src/game/bingoHunt.ts"
s = read(p)
s = s.replace(
    'import { addBingoIntel, BINGO_ACTIVE_PARTY_SIZE, BINGO_TARGET_BY_ID, ensureBingoState, type BingoState, type BingoTargetDef } from "./bingo";',
    'import { addBingoIntel, BINGO_ACTIVE_PARTY_SIZE, BINGO_TARGET_BY_ID, BINGO_TARGETS, ensureBingoState, type BingoState, type BingoTargetDef } from "./bingo";',
    1,
)
if "export function interrogateBingoPrisoner" not in s:
    anchor = "\nexport function bingoCaptureChance"
    pos = s.find(anchor)
    if pos < 0:
        raise SystemExit("Bingo interrogation insertion anchor missing")
    block = r'''
export function interrogateBingoPrisoner(s: GameState, targetId: string): { ok: boolean; error?: string; result?: string } {
  const bingo = ensureBingoState(s);
  const target = BINGO_TARGET_BY_ID[targetId];
  const progress = bingo.targets[targetId];
  if (!target || !progress) return { ok: false, error: "Prisoner dossier not found." };
  if (progress.status !== "captured" || !bingo.detention.prisonerIds.includes(targetId)) return { ok: false, error: "That target is not in detention." };
  if (progress.interrogated) return { ok: false, error: "This prisoner has already given everything useful they know." };

  progress.interrogated = true;
  const affected: string[] = [];
  if (target.organisationId) {
    if (!bingo.organisationsKnown.includes(target.organisationId)) bingo.organisationsKnown.push(target.organisationId);
    for (const linked of BINGO_TARGETS.filter((x) => x.organisationId === target.organisationId && x.id !== targetId)) {
      const lp = bingo.targets[linked.id];
      if (!lp || ["captured", "killed", "recruited", "resolved"].includes(lp.status)) continue;
      lp.intel = Math.min(100, Math.max(lp.intel, 5) + 14);
      if (lp.status === "unknown") lp.status = "rumoured";
      if (lp.intel >= 20 && lp.status === "rumoured") lp.status = "identified";
      affected.push(linked.epithet);
      if (affected.length >= 3) break;
    }
  } else {
    for (const linked of BINGO_TARGETS) {
      const lp = bingo.targets[linked.id];
      if (!lp || linked.id === targetId || ["captured", "killed", "recruited", "resolved"].includes(lp.status)) continue;
      lp.intel = Math.min(100, Math.max(lp.intel, 5) + 7);
      if (lp.status === "unknown") lp.status = "rumoured";
      affected.push(linked.epithet);
      break;
    }
  }
  bingo.detention.securityAlert = Math.max(0, bingo.detention.securityAlert - 4);
  const result = affected.length ? `${target.name} gave up actionable intelligence on ${affected.join(", ")}.` : `${target.name} confirmed the dossier, but had no new active associates to expose.`;
  s.log.push({ txt: result, kind: "good", id: Date.now() });
  return { ok: true, result };
}

'''
    s = s[:pos] + block + s[pos:]
write(p, s)
print("Bingo prisoner interrogation: applied")

# ---------------------------------------------------------------------------
# Captured-dossier controls stay inside the Bingo Book as requested.
# ---------------------------------------------------------------------------
p = "src/components/BingoBookScreen.tsx"
s = read(p)
if "interrogateBingoPrisoner," not in s:
    s = s.replace("  huntReadyForBoss,\n", "  huntReadyForBoss,\n  interrogateBingoPrisoner,\n", 1)
if "bingoRecruitChance" not in s:
    s = s.replace(
        'import type { HuntBiome } from "../game/huntEvents";',
        'import type { HuntBiome } from "../game/huntEvents";\nimport { bingoRecruitChance, recruitBingoPrisoner } from "../game/engine";',
        1,
    )
if 'const captured = progress.status === "captured";' not in s:
    s = s.replace(
        '  const defeated = progress.status === "defeated";\n  const captureChance',
        '  const defeated = progress.status === "defeated";\n  const captured = progress.status === "captured";\n  const recruitChance = captured && target.recruitable ? bingoRecruitChance(s, target.id) : 0;\n  const captureChance',
        1,
    )

if "DETENTION FILE" not in s:
    anchor = '{queued && <p className="mt-2 rounded-lg bg-[#355f8c]/10 p-2 text-[8.5px] font-bold text-[#86bce8] ring-1 ring-[#355f8c]/20">'
    pos = s.find(anchor)
    if pos < 0:
        raise SystemExit("Bingo detention UI anchor missing")
    block = '''{captured && <div className="mt-3 rounded-xl bg-[#1a2530] p-3 ring-1 ring-[#72b7ef]/20"><div className="flex items-center justify-between gap-2"><p className="text-[9px] font-black tracking-wider text-[#72b7ef]">DETENTION FILE</p><span className="text-[8px] font-black text-paper/35">SECURITY {ensureBingoState(s).detention.securityAlert}%</span></div><p className="mt-1 text-[8.5px] leading-relaxed text-paper/50">Captured targets can expose connected dossiers. Some can eventually be persuaded to defect into your roster.</p><div className="mt-2 grid grid-cols-2 gap-2"><button disabled={!!progress.interrogated} onClick={() => { const r=interrogateBingoPrisoner(s,target.id); if(r.ok){ window.alert(r.result ?? "Interrogation complete."); onChanged(); } else window.alert(r.error); }} className="rounded-lg bg-[#355f8c] px-2 py-2 text-[8.5px] font-black text-white disabled:opacity-35">{progress.interrogated ? "INTERROGATED" : "INTERROGATE"}</button>{target.recruitable ? <button disabled={!progress.interrogated} onClick={() => { const r=recruitBingoPrisoner(s,target.id); window.alert(r.result ?? r.error ?? "Recruitment attempt resolved."); if(r.ok) onChanged(); }} className="rounded-lg bg-jade px-2 py-2 text-[8.5px] font-black text-[#102016] disabled:opacity-35">RECRUIT · {Math.round(recruitChance*100)}%</button> : <button disabled className="rounded-lg bg-black/25 px-2 py-2 text-[8.5px] font-black text-paper/30">WILL NOT DEFECT</button>}</div>{(progress.recruitAttempts ?? 0)>0 && <p className="mt-2 text-[8px] font-bold text-paper/35">Recruitment attempts: {progress.recruitAttempts}. Each failed attempt adds +8 percentage points after the three-day cooldown.</p>}</div>}\n      '''
    s = s[:pos] + block + s[pos:]
write(p, s)
print("Bingo detention UI: applied")

p = "public/sw.js"
s = read(p)
s = s.replace('const CACHE = "shadow-village-bingo-book-v4-boss-battles";', 'const CACHE = "shadow-village-bingo-book-v5-detention-recruitment";')
write(p, s)
print("Bingo Book v5 detention/recruitment complete")
