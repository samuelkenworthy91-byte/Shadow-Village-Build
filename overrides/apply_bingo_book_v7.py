from pathlib import Path
import shutil

ROOT = Path("app")
OVR = Path("overrides")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise SystemExit(f"Bingo v7 patch anchor missing: {label}")
    return text.replace(old, new, 1)


# Physical book UI source.
src = OVR / "bingo_book/src/components/BingoBookOverlay.tsx"
if not src.exists():
    raise SystemExit("Bingo v7 book overlay source missing")
shutil.copyfile(src, ROOT / "src/components/BingoBookOverlay.tsx")

# Persistent dossier discoveries.
p = "src/game/bingo.ts"
s = read(p)
s = replace_once(
    s,
    'export type BingoOutcome = "captured" | "killed" | "recruited" | "transferred" | "released" | "executed";\n',
    'export type BingoOutcome = "captured" | "killed" | "recruited" | "transferred" | "released" | "executed";\n\nexport type BingoDiscoveryKey =\n  | "rumour" | "identity" | "portrait" | "threat" | "level" | "elements"\n  | "bounty_dead" | "bounty_alive" | "organisation"\n  | "crime_1" | "crime_2" | "crime_3" | "focus"\n  | "combat_1" | "combat_2" | "escape" | "capture" | "full";\n',
    "discovery type",
)
s = replace_once(
    s,
    '  lastRecruitAttemptDay?: number;\n}',
    '  lastRecruitAttemptDay?: number;\n  discoveries?: BingoDiscoveryKey[];\n  seenDiscoveries?: BingoDiscoveryKey[];\n}',
    "progress discovery fields",
)
s = replace_once(
    s,
    'function blankProgress(): BingoTargetProgress {\n  return { intel: 0, status: "unknown", attempts: 0, locationKnown: false };\n}\n\nexport function ensureBingoState(s: GameState): BingoState {',
    '''function blankProgress(): BingoTargetProgress {\n  return { intel: 0, status: "unknown", attempts: 0, locationKnown: false, discoveries: [], seenDiscoveries: [] };\n}\n\nfunction discoveryKeysForIntel(target: BingoTargetDef, intel: number): BingoDiscoveryKey[] {\n  const keys: BingoDiscoveryKey[] = [];\n  if (intel > 0) keys.push("rumour", "threat");\n  if (intel >= 10) keys.push("bounty_dead");\n  if (intel >= 20) keys.push("identity", "portrait", "level", "elements", "bounty_alive");\n  if (intel >= 30) keys.push("crime_1");\n  if (intel >= 40) keys.push("organisation", "crime_2");\n  if (intel >= 50) keys.push("focus");\n  if (intel >= 60) keys.push("combat_1", "escape");\n  if (intel >= 70) keys.push("crime_3");\n  if (intel >= 80) keys.push("capture");\n  if (intel >= 80 && target.bossMechanics.length > 1) keys.push("combat_2");\n  if (intel >= 100) keys.push("full");\n  return keys;\n}\n\nfunction syncDiscoveryByIntel(target: BingoTargetDef, progress: BingoTargetProgress): boolean {\n  if (!Array.isArray(progress.discoveries)) progress.discoveries = [];\n  if (!Array.isArray(progress.seenDiscoveries)) progress.seenDiscoveries = [];\n  let changed = false;\n  for (const key of discoveryKeysForIntel(target, progress.intel)) {\n    if (!progress.discoveries.includes(key)) { progress.discoveries.push(key); changed = true; }\n  }\n  progress.seenDiscoveries = progress.seenDiscoveries.filter((key) => progress.discoveries!.includes(key));\n  return changed;\n}\n\nexport function recordBingoDiscovery(s: GameState, targetId: string, key: BingoDiscoveryKey): boolean {\n  const b = ensureBingoState(s);\n  const progress = b.targets[targetId];\n  if (!progress) return false;\n  if (!Array.isArray(progress.discoveries)) progress.discoveries = [];\n  if (!Array.isArray(progress.seenDiscoveries)) progress.seenDiscoveries = [];\n  if (progress.discoveries.includes(key)) return false;\n  progress.discoveries.push(key);\n  return true;\n}\n\nexport function markBingoDiscoveriesSeen(s: GameState, targetId: string): boolean {\n  const b = ensureBingoState(s);\n  const progress = b.targets[targetId];\n  if (!progress) return false;\n  if (!Array.isArray(progress.discoveries)) progress.discoveries = [];\n  if (!Array.isArray(progress.seenDiscoveries)) progress.seenDiscoveries = [];\n  const before = progress.seenDiscoveries.length;\n  progress.seenDiscoveries = [...progress.discoveries];\n  return progress.seenDiscoveries.length !== before;\n}\n\nexport function bingoUnreadCount(s: GameState): number {\n  const b = ensureBingoState(s);\n  let count = 0;\n  for (const target of BINGO_TARGETS) {\n    const p = b.targets[target.id];\n    if (!p) continue;\n    const seen = new Set(p.seenDiscoveries ?? []);\n    count += (p.discoveries ?? []).filter((key) => !seen.has(key)).length;\n  }\n  return count;\n}\n\nexport function ensureBingoState(s: GameState): BingoState {''',
    "discovery helpers",
)
s = replace_once(
    s,
    '  for (const target of BINGO_TARGETS) if (!b.targets[target.id]) b.targets[target.id] = blankProgress();',
    '  for (const target of BINGO_TARGETS) {\n    if (!b.targets[target.id]) b.targets[target.id] = blankProgress();\n    syncDiscoveryByIntel(target, b.targets[target.id]);\n  }',
    "discovery migration",
)
s = replace_once(
    s,
    '    b.targets.bb_003 = { ...b.targets.bb_003, intel: Math.max(5, b.targets.bb_003.intel), status: "rumoured" };\n    s.log.push',
    '    b.targets.bb_003 = { ...b.targets.bb_003, intel: Math.max(5, b.targets.bb_003.intel), status: "rumoured" };\n    syncDiscoveryByIntel(BINGO_TARGET_BY_ID.bb_001, b.targets.bb_001);\n    syncDiscoveryByIntel(BINGO_TARGET_BY_ID.bb_002, b.targets.bb_002);\n    syncDiscoveryByIntel(BINGO_TARGET_BY_ID.bb_003, b.targets.bb_003);\n    s.log.push',
    "initial discoveries",
)
s = s.replace(
    '        progress.intel = 5;\n        progress.status = "rumoured";\n',
    '        progress.intel = 5;\n        progress.status = "rumoured";\n        syncDiscoveryByIntel(target, progress);\n',
)
s = replace_once(
    s,
    '  } else if (progress.intel > 0 && progress.status === "unknown") {\n    progress.status = "rumoured";\n  }\n  return progress;\n}',
    '  } else if (progress.intel > 0 && progress.status === "unknown") {\n    progress.status = "rumoured";\n  }\n  const target = BINGO_TARGET_BY_ID[targetId];\n  if (target) syncDiscoveryByIntel(target, progress);\n  return progress;\n}',
    "intel discovery sync",
)
write(p, s)

# Successful hunt events reveal individual dossier facts.
p = "src/game/bingoHunt.ts"
s = read(p)
s = replace_once(
    s,
    'import { addBingoIntel, BINGO_ACTIVE_PARTY_SIZE, BINGO_TARGET_BY_ID, BINGO_TARGETS, ensureBingoState, type BingoState, type BingoTargetDef } from "./bingo";',
    'import { addBingoIntel, BINGO_ACTIVE_PARTY_SIZE, BINGO_TARGET_BY_ID, BINGO_TARGETS, ensureBingoState, recordBingoDiscovery, type BingoDiscoveryKey, type BingoState, type BingoTargetDef } from "./bingo";',
    "hunt discovery imports",
)
s = replace_once(
    s,
    'function recordEvent(run: HuntRunState, ev: HuntEventDef, effect: HuntChoiceEffect): void {',
    '''function huntDiscoveryKey(ev: HuntEventDef, target: BingoTargetDef): BingoDiscoveryKey {\n  const pool: BingoDiscoveryKey[] = ["crime_1", "crime_2", "crime_3", "organisation", "focus", "combat_1", "escape", "capture"];\n  if (target.bossMechanics.length > 1) pool.push("combat_2");\n  let hash = 0;\n  for (let i = 0; i < ev.id.length; i++) hash = ((hash << 5) - hash + ev.id.charCodeAt(i)) | 0;\n  return pool[Math.abs(hash) % pool.length];\n}\n\nfunction recordEvent(run: HuntRunState, ev: HuntEventDef, effect: HuntChoiceEffect): void {''',
    "hunt discovery selector",
)
s = replace_once(
    s,
    '  applyHuntEffect(run, effect, run.stage + choiceIndex + 11);\n  recordEvent(run, ev, effect);\n  return { ok: true, result: effect.result, success };',
    '  applyHuntEffect(run, effect, run.stage + choiceIndex + 11);\n  recordEvent(run, ev, effect);\n  if (success !== false) {\n    const target = BINGO_TARGET_BY_ID[run.targetId];\n    if (target) recordBingoDiscovery(s, run.targetId, huntDiscoveryKey(ev, target));\n  }\n  return { ok: true, result: effect.result, success };',
    "hunt event discovery",
)
s = replace_once(
    s,
    '      lp.intel = Math.min(100, Math.max(lp.intel, 5) + 14);\n      if (lp.status === "unknown") lp.status = "rumoured";\n      if (lp.intel >= 20 && lp.status === "rumoured") lp.status = "identified";',
    '      if (lp.intel <= 0) lp.intel = 5;\n      addBingoIntel(s, linked.id, 14);\n      if (lp.status === "unknown") lp.status = "rumoured";',
    "interrogation linked intel",
)
s = replace_once(
    s,
    '      lp.intel = Math.min(100, Math.max(lp.intel, 5) + 7);\n      if (lp.status === "unknown") lp.status = "rumoured";',
    '      if (lp.intel <= 0) lp.intel = 5;\n      addBingoIntel(s, linked.id, 7);\n      if (lp.status === "unknown") lp.status = "rumoured";',
    "interrogation loose intel",
)
s = replace_once(
    s,
    '  if (progress && run.intel > progress.intel) progress.intel = Math.min(100, run.intel);',
    '  if (progress && run.intel > progress.intel) addBingoIntel(s, run.targetId, run.intel - progress.intel);',
    "hunt intel sync",
)
write(p, s)

# Pause menu becomes the canonical book entrance.
p = "src/App.tsx"
s = read(p)
s = replace_once(
    s,
    'import BingoBookScreen from "./components/BingoBookScreen";\n\ntype Tab = "missions" | "ninjas" | "build" | "equipment" | "bingo";',
    'import BingoBookOverlay from "./components/BingoBookOverlay";\nimport { bingoUnreadCount, ensureBingoState } from "./game/bingo";\nimport { activeBingoHunt } from "./game/bingoHunt";\n\ntype Tab = "missions" | "ninjas" | "build" | "equipment";',
    "App Bingo imports",
)
s = replace_once(s, '  const [busy, setBusy] = useState(false);', '  const [busy, setBusy] = useState(false);\n  const [bingoBookOpen, setBingoBookOpen] = useState(false);', "book state")
s = replace_once(
    s,
    '  const modalRef = useRef(false);\n  modalRef.current = squadFor !== null || detailFor !== null || s.scout !== null;',
    '  const bingoBookOpenRef = useRef(bingoBookOpen);\n  bingoBookOpenRef.current = bingoBookOpen;\n  const modalRef = useRef(false);\n  modalRef.current = squadFor !== null || detailFor !== null || s.scout !== null || bingoBookOpen;',
    "book modal ref",
)
s = replace_once(s, '    setDetailFor(null);\n    audio.start();', '    setDetailFor(null);\n    setBingoBookOpen(false);\n    audio.start();', "book reset begin")
s = replace_once(s, '    setDetailFor(null);\n    audio.unlock();', '    setDetailFor(null);\n    setBingoBookOpen(false);\n    audio.unlock();', "book reset restart")
s = replace_once(s, '    setTab("missions");\n    rawForce();', '    setTab("missions");\n    setBingoBookOpen(false);\n    rawForce();', "book reset title")
s = replace_once(
    s,
    '      if (modalRef.current) {\n        if (k === "m" || k === "M") muteToggle();\n        if (k === "Escape") setDetailFor(null);\n        return;\n      }',
    '      if (modalRef.current) {\n        if (k === "m" || k === "M") muteToggle();\n        if (bingoBookOpenRef.current) {\n          if (k === "Escape") setBingoBookOpen(false);\n          return;\n        }\n        if (k === "Escape") setDetailFor(null);\n        return;\n      }',
    "book keyboard guard",
)
s = replace_once(s, 'const order: Tab[] = ["missions", "ninjas", "build", "equipment", "bingo"];', 'const order: Tab[] = ["missions", "ninjas", "build", "equipment"];', "tab keyboard order")
s = replace_once(s, '    { id: "bingo", kanji: "帳", label: "Bingo", badge: "" },\n', '', "remove Bingo nav tab")
s = replace_once(s, '          {tab === "bingo" && <BingoBookScreen s={s} onChanged={force} />}\n\n', '', "remove old Bingo screen")
s = replace_once(s, '(tab === "equipment" || tab === "bingo") && "hidden"', 'tab === "equipment" && "hidden"', "main grid visibility")
s = replace_once(
    s,
    '{s.phase === "paused" && <PauseOverlay onResume={pauseToggle} onTitle={toTitle} onRestart={restart} />}',
    '{s.phase === "paused" && !bingoBookOpen && <PauseOverlay onResume={pauseToggle} onTitle={toTitle} onRestart={restart} onBingoBook={() => { setBingoBookOpen(true); audio.click(); }} bingoUnlocked={ensureBingoState(s).unlocked} bingoUnread={bingoUnreadCount(s)} bingoActive={!!activeBingoHunt(s)} />}\n      {s.phase === "paused" && bingoBookOpen && <BingoBookOverlay s={s} onChanged={force} onClose={() => setBingoBookOpen(false)} />}',
    "pause menu book route",
)
write(p, s)

# Pause overlay entry with active-hunt bookmark and unread dossier badge.
p = "src/components/Overlays.tsx"
s = read(p)
s = replace_once(
    s,
    'import { Hammer, Play, RotateCcw, ScrollText, Sparkles, Swords, Trash2, Trophy, Users } from "lucide-react";',
    'import { BookOpen, Bookmark, Hammer, Play, RotateCcw, ScrollText, Sparkles, Swords, Trash2, Trophy, Users } from "lucide-react";',
    "pause icons",
)
s = replace_once(
    s,
    'export function PauseOverlay({ onResume, onTitle, onRestart }: { onResume: () => void; onTitle: () => void; onRestart: () => void }) {',
    'export function PauseOverlay({ onResume, onTitle, onRestart, onBingoBook, bingoUnlocked, bingoUnread, bingoActive }: { onResume: () => void; onTitle: () => void; onRestart: () => void; onBingoBook: () => void; bingoUnlocked: boolean; bingoUnread: number; bingoActive: boolean }) {',
    "pause props",
)
s = replace_once(
    s,
    '        <button onClick={onResume} autoFocus className="btn-primary flex h-11 w-full items-center justify-center gap-2 rounded-xl text-[13px] font-black tracking-widest">\n          <Play size={15} /> RESUME\n        </button>\n',
    '        <button onClick={onResume} autoFocus className="btn-primary flex h-11 w-full items-center justify-center gap-2 rounded-xl text-[13px] font-black tracking-widest">\n          <Play size={15} /> RESUME\n        </button>\n        <button onClick={onBingoBook} disabled={!bingoUnlocked} className="relative flex min-h-12 w-full items-center gap-3 overflow-hidden rounded-xl bg-[#2b1b12] px-3 py-2.5 text-left ring-1 ring-inset ring-[#d7bb82]/18 transition hover:bg-[#382319] disabled:cursor-not-allowed disabled:opacity-45">\n          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-[#e6d3aa]/10 text-[#e6d3aa] ring-1 ring-[#e6d3aa]/15"><BookOpen size={18} /></span>\n          <span className="min-w-0 flex-1"><strong className="block font-display text-[12px] font-black tracking-[0.14em] text-[#f2dfb8]">BINGO BOOK</strong><small className="mt-0.5 block truncate text-[9px] font-bold text-[#d7c49f]/50">{bingoUnlocked ? bingoActive ? "Active hunt bookmarked inside" : "Open missing-nin hunter dossiers" : "Locked until your first Kage-level ninja"}</small></span>\n          {bingoActive && <Bookmark size={14} className="shrink-0 text-vermil" fill="currentColor" />}\n          {bingoUnread > 0 && bingoUnlocked && <span className="absolute right-2 top-1.5 rounded-full bg-vermil px-1.5 py-0.5 text-[7px] font-black text-white">{bingoUnread} NEW</span>}\n        </button>\n',
    "pause Bingo button",
)
write(p, s)

# Cache bump.
p = "public/sw.js"
s = read(p)
s = s.replace('const CACHE = "shadow-village-bingo-book-v6-events-mechanics";', 'const CACHE = "shadow-village-bingo-book-v7-physical-dossier";')
write(p, s)

print("Bingo Book v7 physical page dossier experience: applied")
