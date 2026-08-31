from pathlib import Path

APP = Path('app')


def read(rel: str) -> str:
    p = APP / rel
    if not p.exists():
        raise SystemExit(f'Missing expected file: {p}')
    return p.read_text(encoding='utf-8')


def write(rel: str, text: str) -> None:
    (APP / rel).write_text(text, encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    return text.replace(old, new, 1)

# Browser/PWA branding.
text = read('index.html')
text = replace_once(text,
    '<meta name="description" content="Shadow Village — build a hidden ninja settlement, train shinobi, deploy squads on skill-based missions, and survive the raids." />',
    '<meta name="description" content="Kage Life — lead a hidden ninja village, train shinobi, deploy squads on missions, and build a feared Bingo Book." />',
    'index description')
text = replace_once(text, '<title>Shadow Village — Ninja Settlement</title>', '<title>Kage Life — Ninja Village Management</title>', 'index title')
text = replace_once(text, '<meta name="apple-mobile-web-app-title" content="Shadow Village" />', '<meta name="apple-mobile-web-app-title" content="Kage Life" />', 'apple title')
text = replace_once(text, '<meta name="application-name" content="Shadow Village" />', '<meta name="application-name" content="Kage Life" />', 'application name')
write('index.html', text)

text = read('public/manifest.webmanifest')
text = replace_once(text, '"name": "Shadow Village — Ninja Settlement"', '"name": "Kage Life — Ninja Village Management"', 'manifest name')
text = replace_once(text, '"short_name": "Shadow Village"', '"short_name": "Kage Life"', 'manifest short name')
text = replace_once(text,
    '"description": "Build a hidden ninja village, train shinobi, deploy squads on missions, and survive the raids."',
    '"description": "Lead a hidden ninja village, train shinobi, deploy squads on missions, and build a feared Bingo Book."',
    'manifest description')
write('public/manifest.webmanifest', text)

text = read('capacitor.config.ts')
text = replace_once(text, 'appName: "Shadow Village — Progression Dev",', 'appName: "Kage Life",', 'capacitor app name')
# Deliberately keep the existing appId so Android upgrades remain compatible.
write('capacitor.config.ts', text)

# Give every save its own village identity.
text = read('src/game/types.ts')
text = replace_once(text, 'export interface GameState {\n  phase: Phase;', 'export interface GameState {\n  phase: Phase;\n  villageName: string;', 'GameState villageName')
write('src/game/types.ts', text)

text = read('src/game/engine.ts')
text = replace_once(text,
    'export function createState(phase: GameState["phase"] = "menu"): GameState {\n  const s: GameState = {\n    phase,',
    'export function createState(phase: GameState["phase"] = "menu", villageName = "Hidden Village"): GameState {\n  const safeVillageName = villageName.trim().slice(0, 30) || "Hidden Village";\n  const s: GameState = {\n    phase,\n    villageName: safeVillageName,',
    'createState village identity')
text = replace_once(text, 'if (!target.recruitable) return { ok: false, error: "This missing-nin will not join Shadow Village." };', 'if (!target.recruitable) return { ok: false, error: `This missing-nin will not join ${s.villageName}.` };', 'recruit refusal village')
text = replace_once(text, 'const result = `${target.name} accepted a place in Shadow Village and joined the active roster.`;', 'const result = `${target.name} accepted a place in ${s.villageName} and joined the active roster.`;', 'recruit success village')
write('src/game/engine.ts', text)

text = read('src/game/save.ts')
text = replace_once(text, '  raids: number | null;\n}', '  raids: number | null;\n  villageName: string | null;\n}', 'save summary villageName')
text = replace_once(text,
    '    if (!Array.isArray(state.ninjas) || !Array.isArray(state.missions) || typeof state.day !== "number") return null;\n\n    // Lightweight migration/normalisation for saves made before later systems existed.',
    '    if (!Array.isArray(state.ninjas) || !Array.isArray(state.missions) || typeof state.day !== "number") return null;\n\n    // Village identity became save-scoped in Kage Life. Preserve the legacy opening name when available.\n    if (typeof state.villageName !== "string" || !state.villageName.trim()) {\n      let legacyName = "";\n      try { legacyName = localStorage.getItem("shadow-village-name")?.trim() ?? ""; } catch { /* noop */ }\n      state.villageName = legacyName.slice(0, 30) || "Hidden Village";\n    } else {\n      state.villageName = state.villageName.trim().slice(0, 30) || "Hidden Village";\n    }\n\n    // Lightweight migration/normalisation for saves made before later systems existed.',
    'save migration villageName')
text = replace_once(text,
    '      return { slot, exists: false, savedAt: null, day: null, ninjas: null, gold: null, clan: null, raids: null };',
    '      return { slot, exists: false, savedAt: null, day: null, ninjas: null, gold: null, clan: null, raids: null, villageName: null };',
    'empty save summary villageName')
text = replace_once(text,
    '      raids: st.raids,\n    };',
    '      raids: st.raids,\n      villageName: st.villageName,\n    };',
    'save summary value villageName')
write('src/game/save.ts', text)

# The opening-name helper becomes a village-name draft helper. Legacy key is read once for migration convenience.
text = read('src/game/scores.ts')
text = replace_once(text, 'const NAME_KEY = "shadow-village-name";', 'const NAME_KEY = "kage-life-village-name";\nconst LEGACY_NAME_KEY = "shadow-village-name";', 'score name keys')
text = replace_once(text,
    'export function submitScore(name: string, score: number, day: number, done: number): { list: ScoreEntry[]; idx: number } {\n  const entry: ScoreEntry = { name: name.trim().slice(0, 12) || "RONIN", score, day, done, date: Date.now() };',
    'export function submitScore(villageName: string, score: number, day: number, done: number): { list: ScoreEntry[]; idx: number } {\n  const entry: ScoreEntry = { name: villageName.trim().slice(0, 30) || "Hidden Village", score, day, done, date: Date.now() };',
    'score village name')
text = replace_once(text,
    'export function getPlayerName(): string {\n  try {\n    return localStorage.getItem(NAME_KEY) || "SHADOW";\n  } catch {\n    return "SHADOW";\n  }\n}\n\nexport function setPlayerName(n: string): void {\n  try {\n    localStorage.setItem(NAME_KEY, n.trim().slice(0, 12) || "SHADOW");\n  } catch {\n    /* noop */\n  }\n}',
    'export function getVillageName(): string {\n  try {\n    return localStorage.getItem(NAME_KEY) || localStorage.getItem(LEGACY_NAME_KEY) || "";\n  } catch {\n    return "";\n  }\n}\n\nexport function setVillageName(n: string): void {\n  try {\n    localStorage.setItem(NAME_KEY, n.trim().slice(0, 30));\n  } catch {\n    /* noop */\n  }\n}',
    'village name helper functions')
write('src/game/scores.ts', text)

# Opening overlay, save-slot identity, and game-over copy.
text = read('src/components/Overlays.tsx')
text = replace_once(text, '  name,\n  slots,\n  onName,', '  villageName,\n  slots,\n  onVillageName,', 'StartOverlay prop names')
text = replace_once(text, '  name: string;\n  slots: SaveSlotSummary[];\n  onName: (n: string) => void;', '  villageName: string;\n  slots: SaveSlotSummary[];\n  onVillageName: (n: string) => void;', 'StartOverlay prop types')
text = replace_once(text, '          SHADOW\n        </h1>\n        <h1 className="font-display text-[20px] font-black leading-tight tracking-[0.5em] text-paper/90 sm:text-[24px]">\n          VILLAGE', '          KAGE\n        </h1>\n        <h1 className="font-display text-[20px] font-black leading-tight tracking-[0.5em] text-paper/90 sm:text-[24px]">\n          LIFE', 'title logo text')
text = replace_once(text, '          Build the village. Train the shadows. Survive the raids.', '          Lead your village. Train shinobi. Build a feared Bingo Book.', 'opening tagline')
text = replace_once(text, '<label htmlFor="name-input" className="mb-1.5 block text-[9.5px] font-bold tracking-[0.22em] text-paper/40">PLAYER NAME</label>', '<label htmlFor="name-input" className="mb-1.5 block text-[9.5px] font-bold tracking-[0.22em] text-paper/40">VILLAGE NAME</label>', 'village label')
text = replace_once(text, '          value={name}\n          maxLength={12}\n          onChange={(e) => onName(e.target.value.toUpperCase())}\n          placeholder="YOUR NAME"', '          value={villageName}\n          maxLength={30}\n          onChange={(e) => onVillageName(e.target.value)}\n          placeholder="Name your hidden village"', 'village input')
text = replace_once(text,
    '                onClick={() => onStart(slot.slot)}\n                className="min-w-0 flex-1 rounded-xl bg-black/30 px-3 py-2.5 text-left ring-1 ring-inset ring-white/10 transition hover:bg-white/[0.06] hover:ring-gold/35"',
    '                onClick={() => onStart(slot.slot)}\n                disabled={!slot.exists && !villageName.trim()}\n                className="min-w-0 flex-1 rounded-xl bg-black/30 px-3 py-2.5 text-left ring-1 ring-inset ring-white/10 transition hover:bg-white/[0.06] hover:ring-gold/35 disabled:cursor-not-allowed disabled:opacity-40"',
    'new village name required')
text = replace_once(text,
    '<span className="font-display text-[12px] font-black tracking-[0.18em] text-[#ffe9b8]">SLOT {slot.slot}</span>',
    '<span className="min-w-0 truncate font-display text-[12px] font-black tracking-[0.08em] text-[#ffe9b8]">{slot.exists ? slot.villageName : `SLOT ${slot.slot}`}</span>',
    'save slot village label')
text = replace_once(text,
    '                    Day {slot.day} · {slot.ninjas} ninja · {slot.gold?.toLocaleString()} gold · {slot.raids} raids held',
    '                    Slot {slot.slot} · Day {slot.day} · {slot.ninjas} ninja · {slot.gold?.toLocaleString()} gold · {slot.raids} raids held',
    'save slot summary')
text = replace_once(text, '<p className="mt-1 text-[10.5px] text-paper/35">Empty local campaign slot</p>', '<p className="mt-1 text-[10.5px] text-paper/35">{villageName.trim() ? `Begin ${villageName.trim()} in this slot` : "Name a village above to begin"}</p>', 'empty save copy')
text = replace_once(text, '  name,\n  onRestart,', '  villageName,\n  onRestart,', 'GameOver prop name')
text = replace_once(text, '  name: string;\n  onRestart: () => void;', '  villageName: string;\n  onRestart: () => void;', 'GameOver prop type')
text = replace_once(text, '          <Sparkles size={11} className="text-gold" /> recorded as <b className="text-paper/80">{name}</b>', '          <Sparkles size={11} className="text-gold" /> the story of <b className="text-paper/80">{villageName}</b>', 'GameOver village copy')
write('src/components/Overlays.tsx', text)

# App lifecycle: draft village name for new saves, save-owned identity for existing campaigns.
text = read('src/App.tsx')
text = replace_once(text, 'import { getPlayerName, loadScores, setPlayerName, submitScore, type ScoreEntry } from "./game/scores";', 'import { getVillageName, loadScores, setVillageName, submitScore, type ScoreEntry } from "./game/scores";', 'App score imports')
text = replace_once(text, '  const [name, setName] = useState(() => getPlayerName());', '  const [villageName, setVillageNameState] = useState(() => getVillageName());', 'App village state')
text = replace_once(text, '  const nameRef = useRef(name);\n  nameRef.current = name;', '  const villageNameRef = useRef(villageName);\n  villageNameRef.current = villageName;', 'App village ref')
text = replace_once(text, '          const r = submitScore(nameRef.current, sRef.current.score, sRef.current.day, sRef.current.stats.done);', '          const r = submitScore(sRef.current.villageName, sRef.current.score, sRef.current.day, sRef.current.stats.done);', 'submit score village')
text = replace_once(text,
    '    const loaded = loadSlot(slot);\n    activeSlotRef.current = slot;\n    sRef.current = loaded ?? eng.createState("playing");\n    if (sRef.current.phase === "menu") sRef.current.phase = "playing";',
    '    const loaded = loadSlot(slot);\n    if (!loaded && !villageNameRef.current.trim()) return;\n    activeSlotRef.current = slot;\n    sRef.current = loaded ?? eng.createState("playing", villageNameRef.current);\n    if (loaded) setVillageNameState(loaded.villageName);\n    if (sRef.current.phase === "menu") sRef.current.phase = "playing";',
    'begin with save village')
text = replace_once(text,
    '    if (activeSlotRef.current === null) activeSlotRef.current = 1;\n    sRef.current = eng.createState("playing");',
    '    if (activeSlotRef.current === null) activeSlotRef.current = 1;\n    const currentVillageName = sRef.current.villageName || villageNameRef.current || "Hidden Village";\n    sRef.current = eng.createState("playing", currentVillageName);\n    setVillageNameState(currentVillageName);',
    'restart village identity')
text = replace_once(text, '          name={name}', '          villageName={villageName}', 'StartOverlay village prop')
text = replace_once(text,
    '          onName={(n) => {\n            setName(n);\n            setPlayerName(n);\n          }}',
    '          onVillageName={(n) => {\n            setVillageNameState(n);\n            setVillageName(n);\n          }}',
    'StartOverlay village setter')
text = replace_once(text, '<GameOverOverlay s={s} scores={scores} highlight={highlight} name={name} onRestart={restart} onTitle={toTitle} />', '<GameOverOverlay s={s} scores={scores} highlight={highlight} villageName={s.villageName} onRestart={restart} onTitle={toTitle} />', 'GameOver village prop')
write('src/App.tsx', text)

# Keep the HUD compact on mobile; add game/village identity only at xl widths.
text = read('src/components/HUD.tsx')
text = replace_once(text,
    '<span className="hidden font-display text-[13px] font-bold tracking-[0.22em] text-paper/90 xl:block">SHADOW VILLAGE</span>',
    '<span className="hidden max-w-[280px] truncate font-display text-[13px] font-bold tracking-[0.16em] text-paper/90 xl:block">KAGE LIFE · {s.villageName.toUpperCase()}</span>',
    'HUD Kage Life identity')
write('src/components/HUD.tsx', text)

# In-world references use the actual village, not the old product title.
text = read('src/components/NinjaDetail.tsx')
text = replace_once(text,
    '<p className="mt-2 text-[10px] leading-relaxed text-paper/60">This ninja will permanently leave Shadow Village. Their equipped items return to storage, their roster slot is freed, and their unspent progression is not refunded.</p>',
    '<p className="mt-2 text-[10px] leading-relaxed text-paper/60">This ninja will permanently leave {s.villageName}. Their equipped items return to storage, their roster slot is freed, and their unspent progression is not refunded.</p>',
    'NinjaDetail village')
write('src/components/NinjaDetail.tsx', text)

text = read('src/game/bingo.ts')
text = replace_once(text, 's.log.push({ txt: `${n.name} was exiled from Shadow Village.`, kind: "info", id: Date.now() });', 's.log.push({ txt: `${n.name} was exiled from ${s.villageName}.`, kind: "info", id: Date.now() });', 'bingo exile log village')
text = replace_once(text, 's.log.push({ txt: `Bingo Book update: reports identify former Shadow Village shinobi ${pending.ninja.name} as a missing-nin.`, kind: "bad", id: Date.now() + revealed.length });', 's.log.push({ txt: `Bingo Book update: reports identify former ${s.villageName} shinobi ${pending.ninja.name} as a missing-nin.`, kind: "bad", id: Date.now() + revealed.length });', 'bingo reveal log village')
write('src/game/bingo.ts', text)

text = read('src/components/BingoBookOverlay.tsx')
text = replace_once(text, '<p className="bb-kicker">SHADOW VILLAGE · HUNTER-NIN ARCHIVE</p>', '<p className="bb-kicker">{s.villageName.toUpperCase()} · HUNTER-NIN ARCHIVE</p>', 'Bingo summary village')
text = replace_once(text, '<p className="bb-kicker">LOOSE-LEAF FILE · FORMER SHADOW NINJA</p>', '<p className="bb-kicker">LOOSE-LEAF FILE · FORMER {s.villageName.toUpperCase()} NINJA</p>', 'Bingo dynamic dossier village')
text = replace_once(text, '<p>Former Shadow Village ninja who resurfaced after exile are inserted here as irregular field dossiers.</p>', '<p>Former {s.villageName} ninja who resurfaced after exile are inserted here as irregular field dossiers.</p>', 'Bingo dynamic divider village')
text = replace_once(text, '<small>SHADOW VILLAGE · HUNTER-NIN ARCHIVE</small>', '<small>{s.villageName.toUpperCase()} · HUNTER-NIN ARCHIVE</small>', 'Bingo cover village')
write('src/components/BingoBookOverlay.tsx', text)

# Legacy Bingo screen is not the main UI now, but keep it consistent if re-used.
text = read('src/components/BingoBookScreen.tsx')
text = replace_once(text, '<p className="mt-1 text-[8.5px] text-paper/45">Former Shadow Village ninja · dynamic missing-nin</p>', '<p className="mt-1 text-[8.5px] text-paper/45">Former {s.villageName} ninja · dynamic missing-nin</p>', 'legacy Bingo screen village')
write('src/components/BingoBookScreen.tsx', text)

# Visible service-worker branding and a cache bump so the renamed shell refreshes reliably.
text = read('public/sw.js')
text = replace_once(text, '// Offline shell for Shadow Village. Ninja portraits are external PNG assets,', '// Offline shell for Kage Life. Ninja portraits are external PNG assets,', 'service worker comment')
text = replace_once(text, 'const CACHE = "shadow-village-main-polish-v1";', 'const CACHE = "kage-life-v1-village-identity";', 'service worker cache bump')
write('public/sw.js', text)

# Build guide branding only; signing/package identifiers stay unchanged unless intentionally migrated later.
text = read('BUILD_APK.md')
text = replace_once(text, '# Shipping Shadow Village as an Android APK', '# Shipping Kage Life as an Android APK', 'build guide heading')
text = replace_once(text, '| `appName`          | `Shadow Village`          |', '| `appName`          | `Kage Life`                |', 'build guide app name')
write('BUILD_APK.md', text)

print('Kage Life rename + save-scoped village identity applied successfully.')
