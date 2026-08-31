from pathlib import Path
import json
import re

ROOT = Path("app")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, value: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


# Kage Life identity migration.
# Keep the Android package id and old local-storage key names unchanged so
# installed builds and existing save slots remain upgrade-compatible.

# GameState owns the village identity. Optional keeps old saves compatible.
p = "src/game/types.ts"
s = read(p)
if "villageName?: string;" not in s:
    s, n = re.subn(
        r"(export interface GameState\s*\{\s*\n)",
        r'\1  /** Player-chosen village identity. Added by the Kage Life rename. */\n  villageName?: string;\n',
        s,
        count=1,
    )
    if n != 1:
        raise SystemExit("Kage Life: GameState interface anchor not found")
    write(p, s)
print("Kage Life: GameState villageName ready")

# Save-slot summaries expose village names while retaining the existing save
# payload/state structure and backup behaviour.
p = "src/game/save.ts"
s = read(p)
if "villageName: string | null;" not in s:
    anchor = "  exists: boolean;\n"
    if anchor not in s:
        raise SystemExit("Kage Life: SaveSlotSummary anchor not found")
    s = s.replace(anchor, anchor + "  villageName: string | null;\n", 1)

old_empty = "return { slot, exists: false, savedAt: null, day: null, ninjas: null, gold: null, clan: null, raids: null };"
new_empty = "return { slot, exists: false, villageName: null, savedAt: null, day: null, ninjas: null, gold: null, clan: null, raids: null };"
if old_empty in s:
    s = s.replace(old_empty, new_empty, 1)
elif new_empty not in s:
    raise SystemExit("Kage Life: empty save summary anchor not found")

if "villageName: typeof st.villageName" not in s:
    anchor = "      exists: true,\n      savedAt: stored.savedAt,"
    if anchor not in s:
        raise SystemExit("Kage Life: populated save summary anchor not found")
    s = s.replace(
        anchor,
        '      exists: true,\n      villageName: typeof st.villageName === "string" && st.villageName.trim() ? st.villageName.trim() : null,\n      savedAt: stored.savedAt,',
        1,
    )
write(p, s)
print("Kage Life: save-slot village summaries ready")

# Starting a slot commits the typed village name to the actual GameState.
# Existing named saves keep their identity; an old pre-rename save can be
# named once by typing a village name before continuing.
p = "src/App.tsx"
s = read(p)
anchor = '    sRef.current = loaded ?? eng.createState("playing");\n'
addition = '''    const typedVillageName = name.trim();\n    const chosenVillageName = loaded?.villageName?.trim() || typedVillageName;\n    if (!chosenVillageName) {\n      activeSlotRef.current = null;\n      window.alert(loaded ? "Name this village before continuing the save." : "Name your village before starting a new save.");\n      return;\n    }\n    sRef.current.villageName = chosenVillageName.slice(0, 30);\n    setName(sRef.current.villageName);\n    setPlayerName(sRef.current.villageName);\n'''
if "const chosenVillageName = loaded?.villageName?.trim()" not in s:
    if anchor not in s:
        raise SystemExit("Kage Life: App begin/load anchor not found")
    s = s.replace(anchor, anchor + addition, 1)
write(p, s)
print("Kage Life: slot start/load identity ready")

# Opening screen: village naming rather than a personal player identity.
p = "src/components/Overlays.tsx"
s = read(p)
s = s.replace("PLAYER NAME", "VILLAGE NAME")
s = s.replace('placeholder="YOUR NAME"', 'placeholder="NAME YOUR VILLAGE"')
s = s.replace("maxLength={12}", "maxLength={30}", 1)
s = s.replace("onName(e.target.value.toUpperCase())", "onName(e.target.value)", 1)
s = s.replace("HIGH SCORES", "VILLAGE RECORDS")
s = s.replace(">PLAYER<", ">VILLAGE<")

if "slot.villageName ? `${slot.villageName} · `" not in s:
    old = "                    Day {slot.day} · {slot.ninjas} ninja · {slot.gold?.toLocaleString()} gold · {slot.raids} raids held"
    new = "                    {slot.villageName ? `${slot.villageName} · ` : \"\"}Day {slot.day} · {slot.ninjas} ninja · {slot.gold?.toLocaleString()} gold · {slot.raids} raids held"
    if old not in s:
        raise SystemExit("Kage Life: existing slot summary anchor not found")
    s = s.replace(old, new, 1)

old_empty_text = '<p className="mt-1 text-[10.5px] text-paper/35">Empty local campaign slot</p>'
new_empty_text = '<p className="mt-1 text-[10.5px] text-paper/35">{name.trim() ? `Start ${name.trim()}` : "Name your village above to start"}</p>'
if old_empty_text in s:
    s = s.replace(old_empty_text, new_empty_text, 1)
elif new_empty_text not in s:
    raise SystemExit("Kage Life: empty slot prompt anchor not found")
write(p, s)
print("Kage Life: opening village-name UI ready")

# Main HUD identifies the current village. Kage Life remains the fallback brand
# before a named state is present.
p = "src/components/HUD.tsx"
s = read(p)
old = '<span className="hidden font-display text-[13px] font-bold tracking-[0.22em] text-paper/90 xl:block">SHADOW VILLAGE</span>'
new = '<span className="hidden max-w-[220px] truncate font-display text-[13px] font-bold tracking-[0.16em] text-paper/90 xl:block" title={s.villageName?.trim() || "Kage Life"}>{s.villageName?.trim() || "KAGE LIFE"}</span>'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("Kage Life: HUD brand anchor not found")
write(p, s)
print("Kage Life: HUD village identity ready")

# In-world copy must no longer treat the old product title as the settlement.
phrase_replacements = {
    "leave Shadow Village": "leave your village",
    "join Shadow Village": "join your village",
    "to Shadow Village": "to your village",
    "from Shadow Village": "from your village",
    "in Shadow Village": "in your village",
    "of Shadow Village": "of your village",
    "for Shadow Village": "for your village",
    "Shadow Village's": "your village's",
}
for path in (ROOT / "src").rglob("*"):
    if path.suffix not in {".ts", ".tsx"} or not path.is_file():
        continue
    value = path.read_text(encoding="utf-8")
    original = value
    for before, after in phrase_replacements.items():
        value = value.replace(before, after)
    value = value.replace("SHADOW VILLAGE", "KAGE LIFE")
    if value != original:
        path.write_text(value, encoding="utf-8")
print("Kage Life: in-world old-name wording audited")

# PWA/browser branding.
p = "public/manifest.webmanifest"
manifest = json.loads(read(p))
manifest["name"] = "Kage Life"
manifest["short_name"] = "Kage Life"
manifest["description"] = "Lead a hidden ninja village, recruit and train shinobi, develop your settlement, take missions, survive raids, and hunt dangerous missing-nin through the Bingo Book."
write(p, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

index = ROOT / "index.html"
if index.exists():
    value = index.read_text(encoding="utf-8")
    value, n = re.subn(r"<title>[^<]*</title>", "<title>Kage Life</title>", value, count=1)
    if n == 0 and "<head" in value:
        value = value.replace(">", ">\n  <title>Kage Life</title>", 1)
    index.write_text(value, encoding="utf-8")

# Capacitor uses appName for the visible Android label. Keep appId untouched so
# the renamed build remains an upgrade of the existing app.
for rel in ("capacitor.config.ts", "capacitor.config.json"):
    path = ROOT / rel
    if not path.exists():
        continue
    value = path.read_text(encoding="utf-8")
    value = re.sub(r'(appName\s*:\s*)["\'][^"\']*["\']', r'\1"Kage Life"', value, count=1)
    value = re.sub(r'("appName"\s*:\s*)"[^"]*"', r'\1"Kage Life"', value, count=1)
    path.write_text(value, encoding="utf-8")

# Installed PWAs need a cache bump to reliably pick up the renamed shell.
p = "public/sw.js"
s = read(p)
s, n = re.subn(r'const CACHE = "[^"]+";', 'const CACHE = "kage-life-v1-village-identity";', s, count=1)
if n != 1:
    raise SystemExit("Kage Life: service worker CACHE anchor not found")
write(p, s)

print("Kage Life village identity migration complete")
