from pathlib import Path

p = Path("app/src/game/jutsu.ts")
text = p.read_text(encoding="utf-8")
old = '"nin" | "gen" | "ken" | "tac" | "doj" | "med" | "spd" | "atk"'
new = '"nin" | "gen" | "ken" | "tac" | "doj" | "med" | "spd" | "ste" | "atk"'
count = text.count(old)
if count < 2:
    raise SystemExit(f"v11 stealth stat union anchors not found (found {count})")
p.write_text(text.replace(old, new), encoding="utf-8")
print(f"Village depth v11 stealth-scaling TypeScript fix applied to {count} stat unions")
