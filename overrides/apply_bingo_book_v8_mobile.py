from pathlib import Path

ROOT = Path("app")


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
        raise SystemExit(f"Bingo v8 patch anchor missing: {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Pause overlay: prevent tall panels being vertically centred partly outside
# the viewport. On touch-sized screens hide the desktop keyboard cheat-sheet.
# ---------------------------------------------------------------------------
p = "src/components/Overlays.tsx"
s = read(p)
s = replace_once(
    s,
    '<div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#0d0e1a]/72 p-4 backdrop-blur-sm">',
    '<div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-[#0d0e1a]/72 p-2 backdrop-blur-sm sm:p-4">',
    "pause shell viewport alignment",
)
s = replace_once(
    s,
    '<div className="modal-pop relative w-full max-w-md rounded-2xl bg-[#161828]/95 p-5 shadow-2xl ring-1 ring-white/10 sm:p-6">',
    '<div className="modal-pop relative my-auto max-h-[calc(100dvh-1rem)] w-full max-w-md overflow-y-auto rounded-2xl bg-[#161828]/95 p-4 shadow-2xl ring-1 ring-white/10 sm:max-h-[calc(100dvh-2rem)] sm:p-6">',
    "pause shell scroll container",
)
s = replace_once(
    s,
    '<div className="mt-4 space-y-1 rounded-lg bg-black/25 p-3 text-[10.5px] leading-relaxed text-paper/55 ring-1 ring-inset ring-white/5">',
    '<div className="mt-4 hidden space-y-1 rounded-lg bg-black/25 p-3 text-[10.5px] leading-relaxed text-paper/55 ring-1 ring-inset ring-white/5 sm:block">',
    "hide keyboard help on mobile",
)
write(p, s)
print("Pause overlay portrait-safe layout: applied")

# ---------------------------------------------------------------------------
# Physical book portrait layout: preserve the book/page proportions rather
# than stretching to the full tall phone viewport. Threat tabs move to the top
# edge on portrait phones, page chrome is compact, and target art is shown in a
# near-square frame matching the source Bingo sprites.
# ---------------------------------------------------------------------------
p = "src/components/BingoBookOverlay.tsx"
s = read(p)
s = replace_once(
    s,
    '<span className="truncate">BINGO BOOK · {pageIndex + 1}/{pages.length}</span>',
    '<span className="bb-top-title truncate">BINGO BOOK <span className="bb-top-page">· {pageIndex + 1}/{pages.length}</span></span>',
    "book topbar title",
)
s = replace_once(
    s,
    '<button type="button" onClick={() => jumpTarget(active.targetId)} className="bb-top-button bb-top-active"><Bookmark size={12} fill="currentColor" /> ACTIVE HUNT</button>',
    '<button type="button" onClick={() => jumpTarget(active.targetId)} className="bb-top-button bb-top-active"><Bookmark size={12} fill="currentColor" /><span className="bb-top-label">ACTIVE HUNT</span></button>',
    "book active hunt label",
)
s = replace_once(
    s,
    '<button type="button" onClick={onClose} className="bb-top-button"><X size={14} /> PAUSE MENU</button>',
    '<button type="button" onClick={onClose} className="bb-top-button"><X size={14} /><span className="bb-top-label">PAUSE MENU</span></button>',
    "book pause label",
)

old_mobile = '@media(max-width:767px){.bb-book-shell{height:calc(100vh - 8px);border-radius:16px}.bb-book-stage{padding:5px 12px 5px 5px}.bb-spread{inset:5px 12px 5px 5px;display:block}.bb-right-page{display:none}.bb-left-page{height:100%;border:0}.bb-spine{left:5px;top:6px;bottom:6px;width:7px}.bb-threat-tabs{right:-1px;top:50px}.bb-threat-tab{min-height:27px;min-width:31px;font-size:6px;padding:3px}.bb-page{padding:14px 15px 13px 17px}.bb-dossier-head{gap:8px}.bb-portrait-frame{height:94px;width:76px}.bb-target-page h2{font-size:17px}.bb-summary{font-size:8px}.bb-facts-grid{grid-template-columns:1fr 1fr}.bb-dossier-columns{grid-template-columns:1fr}.bb-note strong{font-size:8px}.bb-book-footer span:last-child{display:none}.bb-top-button{padding:4px 6px;font-size:7px}.bb-top-active{max-width:120px;overflow:hidden}.bb-flip-desktop{display:none}.bb-flip-mobile{display:block;left:5px;right:12px}.bb-page-arrow-right{right:4px}.bb-stamp{font-size:15px}.bb-opening-cover{inset:42px 0 28px}}'
new_mobile = '''@media(max-width:767px){.bb-book-shell{height:calc(100dvh - 8px);width:calc(100vw - 8px);border-radius:16px}.bb-book-topbar{min-height:38px;padding:6px 8px;font-size:8px;letter-spacing:.08em}.bb-book-footer{min-height:22px;padding:4px 8px;font-size:7px}.bb-book-stage{padding:29px 5px 5px}.bb-spread{inset:29px 5px 5px;display:block;border-radius:7px 11px 11px 7px}.bb-right-page{display:none}.bb-left-page{height:100%;border:0}.bb-spine{left:5px;top:30px;bottom:6px;width:6px}.bb-threat-tabs{left:8px;right:8px;top:3px;display:flex;flex-direction:row;justify-content:flex-start;gap:2px;overflow-x:auto;padding-bottom:2px;transform:none;scrollbar-width:none}.bb-threat-tabs::-webkit-scrollbar{display:none}.bb-threat-tab{min-height:23px;min-width:36px;border-radius:0 0 5px 5px;padding:3px 5px;font-size:6px}.bb-index-tab{min-width:42px}.bb-page{padding:12px 12px 12px 14px}.bb-dossier-head{gap:7px;padding-bottom:7px}.bb-portrait-frame{height:82px;width:78px;border-width:4px}.bb-target-page h2{font-size:16px}.bb-target-page h3{font-size:9.5px}.bb-summary{margin-top:5px;font-size:7.8px;line-height:1.35}.bb-facts-grid{grid-template-columns:1fr 1fr;gap:4px;margin-top:7px}.bb-dossier-columns{grid-template-columns:1fr;gap:6px;margin-top:6px}.bb-note{margin-top:3px;padding:4px 5px}.bb-note strong{font-size:7.8px}.bb-page-actions,.bb-decision,.bb-detention{margin-top:6px;padding-top:6px}.bb-hunt-slip{margin-top:6px;padding:6px}.bb-book-footer span:last-child{display:none}.bb-top-button{min-height:28px;padding:4px 6px;font-size:7px}.bb-top-label{display:none}.bb-top-active{max-width:none;overflow:visible}.bb-top-title{font-size:8px}.bb-top-page{opacity:.55}.bb-flip-desktop{display:none}.bb-flip-mobile{display:block;left:5px;right:5px;top:29px;bottom:5px}.bb-page-arrow{height:34px;width:24px}.bb-page-arrow-left{left:1px}.bb-page-arrow-right{right:1px}.bb-stamp{font-size:14px}.bb-opening-cover{inset:38px 0 22px}}
@media(max-width:767px) and (orientation:portrait){.bb-book-shell{height:min(calc(100dvh - 12px),calc((100vw - 12px)*1.52),720px);width:min(calc(100vw - 12px),520px)}.bb-portrait-frame img{height:100%;width:100%;object-fit:contain}.bb-page{overscroll-behavior:contain}.bb-page-title{font-size:17px}.bb-summary-page .bb-inside-seal{height:52px;width:52px;font-size:25px}.bb-ledger>div{padding:6px}.bb-ledger strong{font-size:13px}}'''
s = replace_once(s, old_mobile, new_mobile, "portrait mobile book CSS")

s = replace_once(
    s,
    'const CACHE = "shadow-village-bingo-book-v7-physical-dossier";',
    'const CACHE = "shadow-village-bingo-book-v8-mobile-polish";',
    "inline cache marker if present",
) if 'const CACHE = "shadow-village-bingo-book-v7-physical-dossier";' in s else s
write(p, s)

# Service worker cache lives in its own file.
p = "public/sw.js"
s = read(p)
s = replace_once(
    s,
    'const CACHE = "shadow-village-bingo-book-v7-physical-dossier";',
    'const CACHE = "shadow-village-bingo-book-v8-mobile-polish";',
    "service worker cache",
)
write(p, s)
print("Bingo Book v8 portrait proportions and mobile chrome: applied")
