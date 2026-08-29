from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{label}: anchor not found in {path}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: applied")

# ---------- types ----------
replace_once(
    "src/game/types.ts",
    '  title: string | null;\n}',
    '  title: string | null;\n  /** Failed attempts at the current promotion exam; reset on promotion. */\n  examFails?: number;\n}',
    "ninja exam failure state",
)
replace_once(
    "src/game/types.ts",
    '  acting: string | null;\n}',
    '  acting: string | null;\n  /** Battle presentation / resolution context. */\n  mode?: "raid" | "exam";\n  examTargetRank?: NinRank | null;\n}',
    "battle exam context",
)

# ---------- battle ----------
replace_once(
    "src/game/battle.ts",
    '    acting: null,\n  };\n  rollOrder(b, s.b.tower, true);\n  return b;\n}\n\n/* ---------------- turn order ---------------- */',
    '''    acting: null,\n    mode: "raid",\n    examTargetRank: null,\n  };\n  rollOrder(b, s.b.tower, true);\n  return b;\n}\n\n/** Start a promotion exam: exactly one candidate versus one generated rival. */\nexport function startExamBattle(s: GameState, candidate: Ninja, rival: Ninja, targetRank: Ninja["rank"]): Battle {\n  const ally = unitFromNinja(candidate);\n  const foe = unitFromNinja(rival);\n  foe.uid = "e0";\n  foe.foe = true;\n  foe.ninjaId = null;\n  foe.kind = "exam_rival";\n  foe.name = rival.name.split(" ")[0];\n\n  const target = RANK_META[targetRank];\n  const b: Battle = {\n    round: 1,\n    units: [ally, foe],\n    order: [],\n    idx: 0,\n    state: "choose",\n    log: [{ t: `${candidate.name.split(" ")[0]} faces ${foe.name} in the ${target.name} Exam.`, kind: "info" }],\n    clan: `${target.name} EXAM`,\n    gold: 0,\n    score: 0,\n    flash: null,\n    acting: null,\n    mode: "exam",\n    examTargetRank: targetRank,\n  };\n  rollOrder(b, s.b.tower, true);\n  return b;\n}\n\n/* ---------------- turn order ---------------- */''',
    "exam battle start",
)
replace_once(
    "src/game/battle.ts",
    '''export function finishBattle(s: GameState, ev: { type: string; [k: string]: unknown }[]): void {\n  const b = s.battle;\n  if (!b) return;\n  const won = b.state === "won";\n\n  for (const u of b.units) {''',
    '''export function finishBattle(s: GameState, ev: { type: string; [k: string]: unknown }[]): void {\n  const b = s.battle;\n  if (!b) return;\n  const won = b.state === "won";\n\n  // Promotion exams are self-contained duels: no village damage, raid rewards or injury state.\n  if (b.mode === "exam") {\n    const ally = b.units.find((u) => !u.foe && u.ninjaId != null);\n    const n = ally?.ninjaId == null ? null : s.ninjas.find((x) => x.id === ally.ninjaId);\n    const targetRank = b.examTargetRank ?? null;\n    if (n && targetRank) {\n      n.fatigue = Math.min(100, n.fatigue + 12);\n      const req = RANK_META[targetRank];\n      if (won) {\n        n.rank = targetRank;\n        n.examFails = 0;\n        n.sp += 3;\n        for (const k of SKILLS) {\n          n.s[k] += Math.max(1, Math.round(req.boost * 1.35 * (n.growth[k] / 1.4)));\n        }\n        s.stats.promos++;\n        s.score += 75 * (rankIndex(targetRank) + 1);\n        ev.push({ type: "promoted", name: n.name, rank: targetRank, kanji: req.kanji });\n        s.log.push({ txt: `${n.name} passed the ${req.name} Exam and earned promotion!`, kind: "great", id: Date.now() });\n      } else {\n        n.examFails = (n.examFails ?? 0) + 1;\n        const mult = n.examFails === 1 ? 0.75 : 0.5;\n        const nextCost = Math.round(req.gold * mult);\n        ev.push({ type: "exam_failed", name: n.name, rank: targetRank, nextCost });\n        s.log.push({ txt: `${n.name} failed the ${req.name} Exam - retry cost reduced to ${nextCost} gold.`, kind: "bad", id: Date.now() });\n      }\n    }\n    s.battle = null;\n    s.phase = "playing";\n    return;\n  }\n\n  for (const u of b.units) {''',
    "exam battle resolution",
)

# ---------- engine promotion flow ----------
replace_once(
    "src/game/engine.ts",
    'import { startBattle } from "./battle";',
    'import { startBattle, startExamBattle } from "./battle";',
    "exam battle import",
)
replace_once(
    "src/game/engine.ts",
    '''export interface PromoInfo {\n  next: NinRank | null;\n  okLevel: boolean;\n  okMissions: boolean;\n  okGold: boolean;\n  okAp: boolean;\n  ready: boolean;\n  need: { level: number; missions: number; gold: number } | null;\n}\n\nexport function promoInfo(s: GameState, n: Ninja): PromoInfo {\n  const next = nextRank(n.rank);\n  if (!next) return { next: null, okLevel: false, okMissions: false, okGold: false, okAp: false, ready: false, need: null };\n  const req = RANK_META[next];\n  // only one Kage may hold office\n  const kageTaken = next === "kage" && s.ninjas.some((o) => o.rank === "kage");\n  const okLevel = n.level >= req.level;\n  const okMissions = n.wins >= req.missions;\n  const okGold = s.gold >= req.gold;\n  const okAp = s.ap >= 1;\n  return {\n    next,\n    okLevel,\n    okMissions,\n    okGold,\n    okAp,\n    ready: okLevel && okMissions && okGold && okAp && !kageTaken && n.status === "ready",\n    need: { level: req.level, missions: req.missions, gold: req.gold },\n  };\n}\n\nexport function promote(s: GameState, ninjaId: number, ev: Ev[]): boolean {\n  const n = s.ninjas.find((x) => x.id === ninjaId);\n  if (!n) return false;\n  const info = promoInfo(s, n);\n  if (!info.ready || !info.next) return false;\n  const req = RANK_META[info.next];\n  s.gold -= req.gold;\n  s.ap -= 1;\n  n.rank = info.next;\n  n.sp += 2;\n  // the exam sharpens everything, best skills most of all\n  for (const k of SKILLS) n.s[k] += Math.max(1, Math.round(req.boost * (n.growth[k] / 1.4)));\n  s.stats.promos++;\n  s.score += 60 * (rankIndex(info.next) + 1);\n  ev.push({ type: "promoted", name: n.name, rank: info.next, kanji: req.kanji });\n  pushLog(s, `${n.name} promoted to ${req.name}!`, "great");\n  return true;\n}\n''',
    '''export interface PromoInfo {\n  next: NinRank | null;\n  okLevel: boolean;\n  okMissions: boolean;\n  okGold: boolean;\n  okAp: boolean;\n  ready: boolean;\n  cost: number;\n  failures: number;\n  need: { level: number; missions: number; gold: number } | null;\n}\n\nfunction examGoldCost(n: Ninja, next: NinRank): number {\n  const base = RANK_META[next].gold;\n  const failures = n.examFails ?? 0;\n  const mult = failures <= 0 ? 1 : failures === 1 ? 0.75 : 0.5;\n  return Math.round(base * mult);\n}\n\nexport function promoInfo(s: GameState, n: Ninja): PromoInfo {\n  const next = nextRank(n.rank);\n  if (!next) return { next: null, okLevel: false, okMissions: false, okGold: false, okAp: false, ready: false, cost: 0, failures: 0, need: null };\n  const req = RANK_META[next];\n  const cost = examGoldCost(n, next);\n  const failures = n.examFails ?? 0;\n  // only one Kage may hold office\n  const kageTaken = next === "kage" && s.ninjas.some((o) => o.rank === "kage");\n  const okLevel = n.level >= req.level;\n  const okMissions = n.wins >= req.missions;\n  const okGold = s.gold >= cost;\n  const okAp = s.ap >= 1;\n  return {\n    next,\n    okLevel,\n    okMissions,\n    okGold,\n    okAp,\n    ready: okLevel && okMissions && okGold && okAp && !kageTaken && n.status === "ready",\n    cost,\n    failures,\n    need: { level: req.level, missions: req.missions, gold: cost },\n  };\n}\n\nfunction makeExamRival(s: GameState, candidate: Ninja): Ninja {\n  const rival = makeNinja(s);\n  rival.rank = candidate.rank;\n  rival.level = Math.max(1, candidate.level + ri(-1, 1));\n  rival.legend = null;\n  rival.title = "Exam Rival";\n  rival.perks = [];\n  for (const k of SKILLS) {\n    rival.s[k] = Math.max(1, Math.round(candidate.s[k] * (0.90 + Math.random() * 0.18) + ri(-1, 1)));\n  }\n  return rival;\n}\n\n/** Pay for and begin the promotion exam. Promotion itself occurs only on victory. */\nexport function promote(s: GameState, ninjaId: number, _ev: Ev[]): boolean {\n  const n = s.ninjas.find((x) => x.id === ninjaId);\n  if (!n) return false;\n  const info = promoInfo(s, n);\n  if (!info.ready || !info.next) return false;\n  s.gold -= info.cost;\n  s.ap -= 1;\n  const rival = makeExamRival(s, n);\n  s.battle = startExamBattle(s, n, rival, info.next);\n  s.phase = "battle";\n  pushLog(s, `${n.name} enters the ${RANK_META[info.next].name} Exam against ${rival.name}.`, "info");\n  return true;\n}\n''',
    "promotion becomes exam",
)

# ---------- Ninja detail UI ----------
replace_once(
    "src/components/NinjaDetail.tsx",
    '<Req ok={promo.okGold} label={`${nextMeta.gold} gold`} />',
    '<Req ok={promo.okGold} label={`${promo.cost} gold`} />',
    "dynamic exam cost UI",
)
replace_once(
    "src/components/NinjaDetail.tsx",
    '<TrendingUp size={12} /> PROMOTE',
    '<TrendingUp size={12} /> TAKE EXAM',
    "exam button label",
)
replace_once(
    "src/components/NinjaDetail.tsx",
    '''            {promo.ready && (\n              <p className="mt-1.5 text-[9.5px] text-gold/80">\n                Grants +2 SP, a permanent skill boost and access to higher-grade contracts.\n              </p>\n            )}''',
    '''            <p className="mt-1.5 text-[9.5px] text-gold/80">\n              1v1 duel - same-rank rival - level +/-1. Win to promote with +3 SP and a stronger permanent skill boost.\n              {promo.failures > 0 && <span className="ml-1 text-jade">Retry discount active: {promo.failures === 1 ? "25%" : "50%"} off.</span>}\n            </p>''',
    "exam help text",
)

# ---------- app event + modal handoff ----------
replace_once(
    "src/App.tsx",
    '''        case "trained":\n          audio.level();''',
    '''        case "exam_failed":\n          audio.fail();\n          fx.shake(8);\n          floater(50, 34, `EXAM FAILED - RETRY ${e.nextCost} GOLD`, "bad");\n          break;\n        case "trained":\n          audio.level();''',
    "exam failure event",
)
replace_once(
    "src/App.tsx",
    '''    if (eng.promote(sRef.current, ninjaId, evs)) {\n      const rect = r ?? fallbackRect();\n      fx.burst(rect.left + rect.width / 2, rect.top + rect.height / 2, "star", 22);\n    } else {''',
    '''    if (eng.promote(sRef.current, ninjaId, evs)) {\n      setDetailFor(null);\n      const rect = r ?? fallbackRect();\n      fx.burst(rect.left + rect.width / 2, rect.top + rect.height / 2, "star", 12);\n      audio.dispatch();\n    } else {''',
    "exam modal handoff",
)

# ---------- battle presentation ----------
replace_once(
    "src/components/BattleScreen.tsx",
    '  const over = b.state === "won" || b.state === "lost";',
    '  const over = b.state === "won" || b.state === "lost";\n  const isExam = b.mode === "exam";',
    "exam presentation flag",
)
replace_once(
    "src/components/BattleScreen.tsx",
    '<img src="/bg-raid-field.jpg" alt="" className="h-full w-full object-cover opacity-50" draggable={false} />',
    '<img src={isExam ? "/bg-exam-arena.jpg" : "/bg-raid-field.jpg"} alt="" className="h-full w-full object-cover opacity-50" draggable={false} />',
    "exam arena background",
)
replace_once(
    "src/components/BattleScreen.tsx",
    '''          <span className="font-display text-[15px] font-black text-vermil">襲</span>\n          <div className="min-w-0 flex-1">\n            <p className="truncate text-[12px] font-black tracking-wide text-paper">{b.clan}</p>\n            <p className="text-[9.5px] font-bold tracking-[0.2em] text-paper/45">RAID ON THE VILLAGE</p>\n          </div>''',
    '''          <span className="font-display text-[15px] font-black text-vermil">{isExam ? "EX" : "襲"}</span>\n          <div className="min-w-0 flex-1">\n            <p className="truncate text-[12px] font-black tracking-wide text-paper">{b.clan}</p>\n            <p className="text-[9.5px] font-bold tracking-[0.2em] text-paper/45">{isExam ? "RANK-UP EXAM - 1V1 DUEL" : "RAID ON THE VILLAGE"}</p>\n          </div>''',
    "exam battle header",
)
replace_once(
    "src/components/BattleScreen.tsx",
    '<span className="rounded-md bg-black/40 px-2 py-1 text-jade">HOME {homePower.toLocaleString()}</span>',
    '<span className="rounded-md bg-black/40 px-2 py-1 text-jade">{isExam ? "YOU" : "HOME"} {homePower.toLocaleString()}</span>',
    "exam home power label",
)
replace_once(
    "src/components/BattleScreen.tsx",
    '<span className="rounded-md bg-black/40 px-2 py-1 text-[#ff7a5c]">RAID {raidPower.toLocaleString()}</span>',
    '<span className="rounded-md bg-black/40 px-2 py-1 text-[#ff7a5c]">{isExam ? "RIVAL" : "RAID"} {raidPower.toLocaleString()}</span>',
    "exam rival power label",
)
replace_once(
    "src/components/BattleScreen.tsx",
    '<EnemyArt kind={u.kind} h={74} dead={!u.alive} />',
    '''{u.look ? (\n                    <NinjaSprite\n                      n={{ id: 900000 + Number(u.uid.replace(/\\D/g, "") || 0), look: u.look, nature: u.nature ?? "fire", level: u.level, rank: u.rank ?? "genin", legend: u.legend }}\n                      h={74}\n                      grey={!u.alive}\n                    />\n                  ) : (\n                    <EnemyArt kind={u.kind} h={74} dead={!u.alive} />\n                  )}''',
    "exam rival ninja art",
)
replace_once(
    "src/components/BattleScreen.tsx",
    '''                  {b.state === "won" ? "勝利 — VILLAGE HELD" : "敗北 — THE WALLS BREAK"}\n                </p>\n                <p className="truncate text-[10.5px] text-paper/55">\n                  {b.state === "won" ? `+${b.gold} gold · +${b.score} score` : "The village takes damage."}''',
    '''                  {isExam\n                    ? (b.state === "won" ? "EXAM PASSED" : "EXAM FAILED")\n                    : (b.state === "won" ? "勝利 — VILLAGE HELD" : "敗北 — THE WALLS BREAK")}\n                </p>\n                <p className="truncate text-[10.5px] text-paper/55">\n                  {isExam\n                    ? (b.state === "won" ? "Promotion earned - +3 SP - stronger permanent skill boost" : "No promotion - next gold entry fee reduced")\n                    : (b.state === "won" ? `+${b.gold} gold · +${b.score} score` : "The village takes damage.")}''',
    "exam battle result copy",
)

# ---------- service worker ----------
replace_once(
    "public/sw.js",
    'const CACHE = "shadow-village-v5-raiders10-field";',
    'const CACHE = "shadow-village-v6-rank-exams";',
    "exam cache version",
)
replace_once(
    "public/sw.js",
    '"/bg-raid-field.jpg", "/manifest.webmanifest"',
    '"/bg-raid-field.jpg", "/bg-exam-arena.jpg", "/manifest.webmanifest"',
    "exam arena cache asset",
)

print("rank exam patch complete")
