#!/usr/bin/env python3
"""v19 — Remove all kanji from the game and recenter affected text.

Every Japanese character is stripped from the UI: data files keep their
`kanji` fields (blanked) so saves and types stay valid, while icon-style
glyphs are replaced with Latin equivalents (skill short codes, initials,
"ryō" currency) so no box ends up empty. Decorative kanji (panel-header
glyphs, modal watermarks, battle-log prefixes) is removed outright and the
surrounding text keeps its centering.

Validation enforces a ZERO Japanese-character scan across src/, index.html
and sw.js — the patch fails loudly if any straggler survives.

Runs after v18 in the patch chain. Idempotent.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
MARKER = "V19_DEKANJI"

CJK = re.compile(r"[\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef\u30a0-\u30ff]")

BUILDING_INITIALS = {
    "Rice Paddy": "R", "Tea House": "T", "Dōjō": "D", "Watchtower": "W", "Shrine": "S",
    "Main Hall": "H", "Intelligence Bureau": "I", "Advanced Hospital": "H",
    "Diplomacy Office": "D", "ANBU Headquarters": "A",
}

UNIQ_GEAR_ICONS = {"煙": "S", "鉄": "I", "雷": "S", "鷺": "W", "影": "K", "封": "N"}


def rep(path: Path, old: str, new: str, count: int = 1) -> None:
    s = path.read_text(encoding="utf-8")
    found = s.count(old)
    if found != count:
        print(f"FAIL [{path.name}]: anchor found {found}x, expected {count}x:\n{old[:140]}")
        sys.exit(1)
    path.write_text(s.replace(old, new, count), encoding="utf-8")


def blank_kanji_fields(path: Path) -> int:
    s = path.read_text(encoding="utf-8")
    n = len(re.findall(r'kanji: "[^"]*"', s))
    s = re.sub(r'kanji: "[^"]*"', 'kanji: ""', s)
    path.write_text(s, encoding="utf-8")
    return n


def patch_content() -> None:
    p = APP / "src/game/content.ts"
    blank_kanji_fields(p)
    # buildings keep a Latin glyph for the village map / build menu boxes
    s = p.read_text(encoding="utf-8")
    for name, initial in BUILDING_INITIALS.items():
        s = s.replace(f'name: "{name}", kanji: ""', f'name: "{name}", kanji: "{initial}"')
    # mission-rank seals become grade numerals
    s = s.replace('D: "丁", C: "丙", B: "乙", A: "甲", S: "神",',
                  'D: "I", C: "II", B: "III", A: "IV", S: "V",')
    # trait icons become name initials so chips keep their glyph
    out = []
    for line in s.splitlines():
        if re.search(r'icon: "[^"]*[\u3000-\u30ff\u4e00-\u9fff][^"]*"', line):
            m = re.search(r'name: "([^"]+)"', line)
            name = m.group(1) if m else "?"
            toks = [t for t in name.replace("·", " ").split() if t]
            ab = "".join(t[0] for t in toks[:2]).upper() or name[:1].upper()
            line = re.sub(r'icon: "[^"]*"', lambda _: f'icon: "{ab}"', line, count=1)
        out.append(line)
    s = "\n".join(out)
    # 両 currency in any content strings
    s = s.replace("両", " ryō")
    p.write_text(s, encoding="utf-8")
    print("  content.ts: kanji blanked, buildings/ranks/traits get Latin glyphs")


def patch_game_data() -> None:
    # perks + techniques: blank kanji, drop 奥義 honorifics from descriptions
    for f in ["src/game/perks.ts", "src/game/techniques.ts"]:
        p = APP / f
        n = blank_kanji_fields(p)
        s = p.read_text(encoding="utf-8")
        s = s.replace("奥義 ", "").replace("奥義", "signature")
        p.write_text(s, encoding="utf-8")
        print(f"  {f}: {n} kanji fields blanked")
    # equipment icons
    p = APP / "src/game/equipment.ts"
    s = p.read_text(encoding="utf-8")
    s = s.replace('const ICONS = ["鉢", "苦", "衣", "巻", "手", "足", "面", "符", "帯", "輪"];',
                  'const ICONS = ["H", "K", "C", "S", "G", "B", "M", "T", "W", "R"];')
    for k, v in UNIQ_GEAR_ICONS.items():
        s = s.replace(f'icon: "{k}"', f'icon: "{v}"')
    p.write_text(s, encoding="utf-8")
    print("  equipment.ts: Latin gear icons")
    # battle log prefixes
    p = APP / "src/game/battle.ts"
    s = p.read_text(encoding="utf-8")
    n1 = s.count("`技 ${tech.name}!")
    n2 = s.count("`装具 ${tech.name}!")
    if n1 != 3 or n2 != 1:
        print(f"FAIL battle.ts log prefixes: 技={n1} (want 3), 装具={n2} (want 1)")
        sys.exit(1)
    s = s.replace("`技 ${tech.name}!", "`${tech.name}!")
    s = s.replace("`装具 ${tech.name}!", "`${tech.name}!")
    p.write_text(s, encoding="utf-8")
    print("  battle.ts: technique log prefixes stripped")
    # engine log currency
    p = APP / "src/game/engine.ts"
    rep(p, "(+${m.gold}両)", "(+${m.gold} ryō)")
    print("  engine.ts: ryō currency")


def patch_components() -> None:
    # ---------- App.tsx ----------
    p = APP / "src/App.tsx"
    for tab in [("missions", "任"), ("ninjas", "忍"), ("build", "築"), ("equipment", "具")]:
        s = p.read_text(encoding="utf-8")
        s = s.replace(f'{{ id: "{tab[0]}", kanji: "{tab[1]}", label:', f'{{ id: "{tab[0]}", label:')
        p.write_text(s, encoding="utf-8")
    rep(p, "  const tabs: { id: Tab; kanji: string; label: string; badge: string }[] = [",
        "  const tabs: { id: Tab; label: string; badge: string }[] = [")
    rep(p, '                <span className="font-display">{t.kanji}</span>\n', "")
    rep(p, "`+${e.gold} 両`", "`+${e.gold} ryō`")
    rep(p, "`${e.kanji} ${e.name} → ${RANK_META[e.rank as keyof typeof RANK_META].name.toUpperCase()}`",
        "`${e.name} → ${RANK_META[e.rank as keyof typeof RANK_META].name.toUpperCase()}`")
    rep(p, "`${e.kanji} ${e.perk} LEARNED`", "`${e.perk} LEARNED`")
    print("  App.tsx: nav tabs + floaters")

    # ---------- Bits.tsx ----------
    p = APP / "src/components/Bits.tsx"
    rep(p, '      <b className="font-display">{rt.kanji}</b>\n', "")
    rep(p, '<b className="font-display" style={{ color: m.color }}>{m.kanji}</b>',
        '<b className="font-display" style={{ color: m.color }}>{m.short}</b>')
    rep(p, '<span className="text-[8.5px] font-bold tracking-wider text-paper/35">疲</span>',
        '<span className="text-[8.5px] font-bold tracking-wider text-paper/35">FTG</span>')
    print("  Bits.tsx: rank/skill chips, fatigue label")

    # ---------- BattleScreen.tsx ----------
    p = APP / "src/components/BattleScreen.tsx"
    for k in ["撃", "術", "幻", "医", "守", "技", "具"]:
        s = p.read_text(encoding="utf-8")
        s = s.replace(f', kanji: "{k}"', "")
        p.write_text(s, encoding="utf-8")
    rep(p, "const ACTIONS: { id: BAction; icon: typeof Swords; kanji: string }[] = [",
        "const ACTIONS: { id: BAction; icon: typeof Swords }[] = [")
    rep(p, '{isExam ? "EX" : "襲"}', '{isExam ? "EX" : "!"}')
    rep(p, '"勝利 — VILLAGE HELD" : "敗北 — THE WALLS BREAK"',
        '"VILLAGE HELD" : "THE WALLS BREAK"')
    print("  BattleScreen.tsx: actions + verdict text")

    # ---------- ScoutModal.tsx ----------
    p = APP / "src/components/ScoutModal.tsx"
    rep(p, "            募\n", "            R\n")
    rep(p, "<b className=\"font-display\">{nat.kanji}</b> {nat.name}", "{nat.name}")
    rep(p, "<b className=\"font-display\">{nat2.kanji}</b> {nat2.name}", "{nat2.name}")
    rep(p, '<b className="font-display" style={{ color: meta.color }}>{meta.kanji}</b>',
        '<b className="font-display" style={{ color: meta.color }}>{meta.short}</b>')
    rep(p, "<b>血 {bloodline.name}</b>", "<b>{bloodline.name}</b>")
    rep(p, "Unlocks 奥義 {LEGENDS[n.legend].perk.name}.", "Unlocks signature {LEGENDS[n.legend].perk.name}.")
    print("  ScoutModal.tsx")

    # ---------- NinjaDetail.tsx ----------
    p = APP / "src/components/NinjaDetail.tsx"
    rep(p, "<b className=\"font-display\">{nat.kanji}</b> {nat.name}", "{nat.name}")
    rep(p, "<b className=\"font-display\">{nat2.kanji}</b> {nat2.name}", "{nat2.name}")
    rep(p, ">眼 DŌJUTSU LINEAGE", ">DŌJUTSU LINEAGE")
    rep(p, "血 {bloodline.name.toUpperCase()} · {bloodline.kanji}", "{bloodline.name.toUpperCase()}")
    rep(p, "{nextMeta.kanji}", "{nextMeta.name.charAt(0)}")
    rep(p, "                    {meta.kanji}\n", "                    {meta.short}\n")
    rep(p, "{isSkill ? meta?.kanji : perk?.kanji}", "{isSkill ? meta?.short : perk?.name.charAt(0)}")
    s = p.read_text(encoding="utf-8")
    s = s.replace("奥義 ", "").replace("影 KAGE —", "KAGE —")
    p.write_text(s, encoding="utf-8")
    print("  NinjaDetail.tsx")

    # ---------- Roster.tsx ----------
    p = APP / "src/components/Roster.tsx"
    rep(p, '        <span className="p-kanji">忍</span>\n', "")
    rep(p, "<b className=\"font-display\">{meta.kanji}</b>", "<b className=\"font-display\">{meta.short}</b>")
    rep(p, ">奥</span>", ">★</span>")
    print("  Roster.tsx")

    # ---------- MissionBoard.tsx ----------
    p = APP / "src/components/MissionBoard.tsx"
    rep(p, '<header className="panel-h"><span className="p-kanji">任</span><span className="panel-title">Mission Board</span>',
        '<header className="panel-h"><span className="panel-title">Mission Board</span>')
    rep(p, '{bingo?"帳":special?"特":f}', '{bingo?"B":special?"SP":f}')
    rep(p, '{special?"特":rank}', '{special?"SP":rank}')
    rep(p, '{special?"⚠ REVIEW + SELECT":"編成 SELECT SQUAD"}', '{special?"⚠ REVIEW + SELECT":"SELECT SQUAD"}')
    rep(p, '">派遣{', '">QUICK{')
    print("  MissionBoard.tsx")

    # ---------- BuildMenu.tsx ----------
    p = APP / "src/components/BuildMenu.tsx"
    rep(p, '        <span className="p-kanji">築</span>\n', "")
    rep(p, ">防</span>", ">D</span>")
    print("  BuildMenu.tsx")

    # ---------- EquipmentScreen.tsx ----------
    p = APP / "src/components/EquipmentScreen.tsx"
    rep(p, ">具</span>", ">EQ</span>")
    print("  EquipmentScreen.tsx")

    # ---------- HUD.tsx ----------
    p = APP / "src/components/HUD.tsx"
    rep(p, """        <span className="font-display text-gold">日</span>
        <span className="whitespace-nowrap tabular-nums text-paper/90"><span className="hidden sm:inline">Day </span>{s.day}</span>""",
        """        <span className="whitespace-nowrap tabular-nums text-paper/90">Day {s.day}</span>""")
    print("  HUD.tsx")

    # ---------- Scene.tsx ----------
    p = APP / "src/components/Scene.tsx"
    rep(p, ">襲</span>", ">!</span>")
    rep(p, '        <span className="font-display text-[15px]">次</span>\n', "")
    print("  Scene.tsx")

    # ---------- GenjutsuTree.tsx ----------
    p = APP / "src/components/GenjutsuTree.tsx"
    for k in ["縛", "怖", "乱", "幻"]:
        s = p.read_text(encoding="utf-8")
        s = s.replace(f'kanji:"{k}", ', "")
        p.write_text(s, encoding="utf-8")
    rep(p, "{m.kanji}", "{m.title.charAt(0)}")
    print("  GenjutsuTree.tsx")

    # ---------- JutsuTree.tsx ----------
    p = APP / "src/components/JutsuTree.tsx"
    rep(p, "meta.kanji,meta.color,nodes)", "meta.name.charAt(0),meta.color,nodes)")
    rep(p, "KEKKEI_META[pairKey].kanji,KEKKEI_META[pairKey].color",
        "KEKKEI_META[pairKey].name.charAt(0),KEKKEI_META[pairKey].color")
    print("  JutsuTree.tsx")

    # ---------- SquadModal.tsx ----------
    p = APP / "src/components/SquadModal.tsx"
    rep(p, '<b className="font-display">{meta.kanji}</b> {meta.short}', '{meta.short}')
    rep(p, "<b className=\"font-display\">{meta.kanji}</b>", "<b className=\"font-display\">{meta.short}</b>")
    rep(p, '{nat.kanji}', '{nat.name.charAt(0)}')
    rep(p, '{nat2.kanji}', '{nat2.name.charAt(0)}')
    rep(p, "{m.gold}両", "{m.gold} ryō")
    rep(p, "{m.rice}米", "{m.rice} rice")
    rep(p, '"出撃 DEPLOY"', '"DEPLOY"')
    print("  SquadModal.tsx")

    # ---------- RaidDefenseModal.tsx ----------
    p = APP / "src/components/RaidDefenseModal.tsx"
    rep(p, "{nat.kanji} {nat.name}", "{nat.name}")
    print("  RaidDefenseModal.tsx")

    # ---------- ReportModal.tsx ----------
    p = APP / "src/components/ReportModal.tsx"
    rep(p, '{report.win ? "成功 — MISSION COMPLETE" : "失敗 — MISSION FAILED"}',
        '{report.win ? "MISSION COMPLETE" : "MISSION FAILED"}')
    rep(p, "<b className=\"font-display\">{SKILL_META[su.k].kanji}</b>",
        "<b className=\"font-display\">{SKILL_META[su.k].short}</b>")
    print("  ReportModal.tsx")

    # ---------- NinjaEquipment.tsx ----------
    p = APP / "src/components/NinjaEquipment.tsx"
    s = p.read_text(encoding="utf-8")
    s = s.replace("奥義", "signature")
    p.write_text(s, encoding="utf-8")
    print("  NinjaEquipment.tsx")

    # ---------- Overlays.tsx ----------
    p = APP / "src/components/Overlays.tsx"
    rep(p, "function Shell({ children, kanji }: { children: ReactNode; kanji: string }) {",
        "function Shell({ children }: { children: ReactNode }) {")
    rep(p, """      <span className="pointer-events-none fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 select-none font-display text-[52vmin] font-black leading-none text-white/[0.035]">
        {kanji}
      </span>
""", "")
    for k in ["影", "休", "終"]:
        s = p.read_text(encoding="utf-8")
        s = s.replace(f'<Shell kanji="{k}">', "<Shell>")
        p.write_text(s, encoding="utf-8")
    rep(p, "{e.done}任", "{e.done}")
    print("  Overlays.tsx")

    # ---------- PerkTree.tsx: node chip shows the initial, row stays centered ----------
    p = APP / "src/components/PerkTree.tsx"
    rep(p, "                          {p.kanji}", "                          {p.name.charAt(0)}")
    print("  PerkTree.tsx")

    # ---------- Bingo book ----------
    for f in ["src/components/BingoBookOverlay.tsx", "src/components/BingoBookScreen.tsx"]:
        p = APP / f
        s = p.read_text(encoding="utf-8")
        s = s.replace(" 両`", " ryō`").replace(" 両<", " ryō<")
        p.write_text(s, encoding="utf-8")
    p = APP / "src/components/BingoBookOverlay.tsx"
    rep(p, 'bb-inside-seal">影</div>', 'bb-inside-seal">K</div>')
    rep(p, "<div><span>影</span><p>BINGO BOOK</p>", "<div><span>K</span><p>BINGO BOOK</p>")
    p = APP / "src/components/BingoBookScreen.tsx"
    rep(p, ">帳</div>", ">B</div>")
    print("  BingoBookOverlay.tsx + BingoBookScreen.tsx")


def sweep_stragglers() -> int:
    """Replace any remaining CJK in src/ — currency marks and loose glyphs."""
    total = 0
    for f in APP.glob("src/**/*.*"):
        if f.suffix not in (".ts", ".tsx", ".css"):
            continue
        s = f.read_text(encoding="utf-8")
        if not CJK.search(s):
            continue
        orig = s
        s = s.replace("両", " ryō").replace("米", " rice")
        s = re.sub(r"[\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uf900-\ufaff]+", "", s)
        if s != orig:
            total += 1
            f.write_text(s, encoding="utf-8")
            print(f"  sweep: {f.relative_to(APP)}")
    return total


def validate() -> None:
    offenders = []
    files = list(APP.glob("src/**/*.*")) + [APP / "index.html", APP / "public/sw.js"]
    for f in files:
        if f.suffix not in (".ts", ".tsx", ".css", ".html", ".js"):
            continue
        if not f.is_file():
            continue
        s = f.read_text(encoding="utf-8")
        m = CJK.search(s)
        if m:
            line = s[:m.start()].count("\n") + 1
            offenders.append(f"{f.relative_to(APP)}:{line}")
    if offenders:
        print("FAIL: Japanese characters remain in:")
        for o in offenders:
            print("  ", o)
        sys.exit(1)
    # cache bump (value-agnostic so it runs last in any patch order)
    p = APP / "public/sw.js"
    s = p.read_text(encoding="utf-8")
    s2 = re.sub(r'const CACHE = "[^"]*";', 'const CACHE = "kage-life-v4-elemental-clarity";', s, count=1)
    if s2 != s:
        p.write_text(s2, encoding="utf-8")
        print("  sw.js: cache bumped to kage-life-v4-elemental-clarity")
    print("  validated: zero Japanese characters across src/, index.html, sw.js")


def main() -> None:
    battle = APP / "src/game/battle.ts"
    if MARKER in battle.read_text(encoding="utf-8"):
        print("v19 dekanji already applied — nothing to do")
        return
    print("v19: removing all kanji + recentering text")
    patch_content()
    patch_game_data()
    patch_components()
    sweep_stragglers()
    s = battle.read_text(encoding="utf-8")
    s = s.replace("/* ================= v18 elemental type advantage =================",
                  f"// {MARKER}\n/* ================= v18 elemental type advantage =================", 1)
    battle.write_text(s, encoding="utf-8")
    validate()
    print("v19 dekanji applied cleanly")


if __name__ == "__main__":
    main()
