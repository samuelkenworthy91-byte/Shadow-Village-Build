from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path("app")
SRC = Path("overrides/bingo_book")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, value: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding="utf-8")


def copy(rel: str) -> None:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f"{rel}: copied")


# ---------------------------------------------------------------------------
# Bingo Book v1: state/data/event engine and first dossier UI.
# ---------------------------------------------------------------------------
copy("src/game/bingo.ts")
copy("src/game/huntEvents.ts")
copy("src/components/BingoBookScreen.tsx")

# ---------------------------------------------------------------------------
# Save migration: Bingo state is optional on old saves and normalised on load.
# ---------------------------------------------------------------------------
p = "src/game/save.ts"
s = read(p)
if 'from "./bingo"' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith("import ")), default=0)
    lines.insert(insert_at, 'import { ensureBingoState } from "./bingo";')
    s = "\n".join(lines) + ("\n" if read(p).endswith("\n") else "")

s, n = re.subn(r"const SAVE_VERSION = \d+;", "const SAVE_VERSION = 3;", s, count=1)
if n != 1:
    raise SystemExit("bingo save migration: SAVE_VERSION anchor not found")

if "ensureBingoState(state);" not in s:
    anchors = [
        '    if (state.phase === "menu") state.phase = "playing";\n',
        '    if (!Array.isArray(state.reports)) state.reports = [];\n',
    ]
    for anchor in anchors:
        if anchor in s:
            s = s.replace(anchor, anchor + "    ensureBingoState(state);\n", 1)
            break
    else:
        raise SystemExit("bingo save migration: normalisation anchor not found")
write(p, s)
print("save Bingo migration: applied")

# ---------------------------------------------------------------------------
# Re-export roster/Bingo helpers through engine, matching existing App actions.
# ---------------------------------------------------------------------------
p = "src/game/engine.ts"
s = read(p)
if 'export { exileNinja, ensureBingoState, refreshPendingMissingNin } from "./bingo";' not in s:
    s = s.rstrip() + '\n\nexport { exileNinja, ensureBingoState, refreshPendingMissingNin } from "./bingo";\n'
write(p, s)
print("engine Bingo exports: applied")

# ---------------------------------------------------------------------------
# App: add Bingo as a management tab and wire exile persistence.
# ---------------------------------------------------------------------------
p = "src/App.tsx"
s = read(p)
if 'BingoBookScreen' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith("import ")), default=0)
    lines.insert(insert_at, 'import BingoBookScreen from "./components/BingoBookScreen";')
    s = "\n".join(lines) + ("\n" if read(p).endswith("\n") else "")

mt = re.search(r"type Tab\s*=\s*([^;]+);", s)
if not mt:
    raise SystemExit("bingo app tab: type Tab union not found")
if '"bingo"' not in mt.group(1):
    union = mt.group(1).rstrip()
    s = s[:mt.start(1)] + union + ' | "bingo"' + s[mt.end(1):]

order = re.search(r"const order: Tab\[\] = \[([^\]]+)\];", s)
if order and '"bingo"' not in order.group(1):
    vals = order.group(1).rstrip()
    s = s[:order.start(1)] + vals + ', "bingo"' + s[order.end(1):]

tabs = re.search(r"(const tabs: \{ id: Tab; kanji: string; label: string; badge: string \}\[\] = \[)([\s\S]*?)(\n  \];)", s)
if not tabs:
    raise SystemExit("bingo app tabs: tabs array not found")
if 'id: "bingo"' not in tabs.group(2):
    body = tabs.group(2).rstrip() + '\n    { id: "bingo", kanji: "帳", label: "Bingo", badge: "" },'
    s = s[:tabs.start(2)] + body + s[tabs.end(2):]

if 'tab === "bingo" && <BingoBookScreen' not in s:
    equipment_render = re.search(r'(\s*\{tab === "equipment" && <EquipmentScreen[^\n]+\}\}\s*)', s)
    bingo_render = '          {tab === "bingo" && <BingoBookScreen s={s} onChanged={force} />}\n\n'
    if equipment_render:
        pos = equipment_render.end()
        s = s[:pos] + bingo_render + s[pos:]
    else:
        grid = re.search(r'<div className=\{cn\("[^\"]*grid min-h-0 flex-1', s)
        if not grid:
            raise SystemExit("bingo app content: render anchor not found")
        s = s[:grid.start()] + bingo_render + s[grid.start():]

# Equipment already hides the management grid on its full screen. Bingo does the same.
s = s.replace('tab === "equipment" && "hidden"', '(tab === "equipment" || tab === "bingo") && "hidden"')

# Wire the detail modal's exile callback directly to the mutable game state + existing force/save path.
if 'onExile={(id) =>' not in s:
    nd = re.search(r'(<NinjaDetail[\s\S]*?onEquipmentChanged=\{force\}[\s\S]*?)(/>)', s)
    if not nd:
        raise SystemExit("bingo exile app wiring: NinjaDetail invocation anchor not found")
    addition = '          onExile={(id) => { const result = eng.exileNinja(sRef.current, id); if (result.ok) { setDetailFor(null); force(); } }}\n        '
    block = nd.group(1) + addition
    s = s[:nd.start()] + block + nd.group(2) + s[nd.end():]

write(p, s)
print("App Bingo tab + exile wiring: applied")

# ---------------------------------------------------------------------------
# Ninja detail: explicit, double-confirmed exile action. No historical archive.
# ---------------------------------------------------------------------------
p = "src/components/NinjaDetail.tsx"
s = read(p)
if "onExile" not in s:
    s = s.replace('  onEquipmentChanged,\n}: {', '  onEquipmentChanged,\n  onExile,\n}: {', 1)
    s = s.replace('  onEquipmentChanged: () => void;\n}) {', '  onEquipmentChanged: () => void;\n  onExile: (id: number) => void;\n}) {', 1)

if 'const [confirmExile, setConfirmExile]' not in s:
    anchor = '  const [showEquipment, setShowEquipment] = useState(false);'
    if anchor not in s:
        raise SystemExit("bingo exile detail: showEquipment state anchor not found")
    s = s.replace(anchor, anchor + '\n  const [confirmExile, setConfirmExile] = useState(false);', 1)

if "EXILE NINJA" not in s:
    marker = '<span className="pointer-events-none absolute inset-x-1 bottom-1 rounded bg-black/65 px-1.5 py-1 text-center text-[7.5px] font-black tracking-[0.12em] text-gold/85 opacity-90 ring-1 ring-white/10">TAP FOR EQUIPMENT</span>\n</button>'
    if marker not in s:
        raise SystemExit("bingo exile detail: equipment portrait marker not found")
    button = '''\n<button type="button" onClick={() => setConfirmExile(true)} className="mt-1 w-full rounded-lg bg-vermil/10 px-2 py-1.5 text-[8px] font-black tracking-[0.12em] text-vermil ring-1 ring-vermil/20 transition hover:bg-vermil/15 active:scale-[0.98]">EXILE NINJA</button>'''
    s = s.replace(marker, marker + button, 1)

if 'confirmExile &&' not in s:
    modal_anchor = '        {showEquipment && <NinjaEquipment'
    if modal_anchor not in s:
        raise SystemExit("bingo exile detail: modal anchor not found")
    modal = '''        {confirmExile && (\n          <div className="fixed inset-0 z-[120] grid place-items-center bg-black/75 p-4 backdrop-blur-sm">\n            <div className="w-full max-w-sm rounded-2xl bg-[#171925] p-4 ring-1 ring-vermil/35 shadow-2xl">\n              <p className="font-display text-lg font-black text-vermil">EXILE {n.name.toUpperCase()}?</p>\n              <p className="mt-2 text-[10px] leading-relaxed text-paper/60">This ninja will permanently leave Shadow Village. Their equipped items return to storage, their roster slot is freed, and their unspent progression is not refunded.</p>\n              <p className="mt-2 rounded-lg bg-vermil/[0.06] p-2 text-[9px] font-bold leading-relaxed text-vermil/80 ring-1 ring-vermil/15">This cannot be undone.</p>\n              <div className="mt-4 grid grid-cols-2 gap-2">\n                <button type="button" onClick={() => setConfirmExile(false)} className="rounded-xl bg-black/30 px-3 py-2.5 text-[9px] font-black text-paper/65 ring-1 ring-white/10">CANCEL</button>\n                <button type="button" onClick={() => { setConfirmExile(false); onExile(n.id); }} className="rounded-xl bg-vermil px-3 py-2.5 text-[9px] font-black text-white">CONFIRM EXILE</button>\n              </div>\n            </div>\n          </div>\n        )}\n\n'''
    s = s.replace(modal_anchor, modal + modal_anchor, 1)

write(p, s)
print("Ninja exile UI: applied")

# Cache bump ensures installed clients fetch the new tab and roster controls.
p = "public/sw.js"
s = read(p)
s, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-bingo-book-v1";', s, count=1)
if n != 1:
    raise SystemExit("bingo service worker CACHE constant not found")
write(p, s)
print("Bingo Book v1 patch complete")

# v2 extends the same branch build with real intelligence contracts and the
# deterministic multi-stage hunt loop. Keeping this chained here means the
# existing branch CI remains the single reproducible build entrypoint.
subprocess.run([sys.executable, "overrides/apply_bingo_book_v2.py"], check=True)
