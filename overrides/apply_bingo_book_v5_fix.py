from pathlib import Path

p = Path("app/src/game/engine.ts")
s = p.read_text(encoding="utf-8")
old = 'const natureMap: Partial<Record<string, Nature>> = { Fire: "fire", Water: "water", Wind: "wind", Earth: "earth", Lightning: "lightning" };'
new = 'const natureMap: Partial<Record<string, Nature>> = { Fire: "fire", Water: "water", Wind: "wind", Earth: "earth", Lightning: "light" };'
if old not in s:
    if new in s:
        print("Bingo v5 nature type fix already applied")
    else:
        raise SystemExit("Bingo v5 nature-map anchor missing")
else:
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("Bingo v5 lightning nature mapped to canonical 'light'")
