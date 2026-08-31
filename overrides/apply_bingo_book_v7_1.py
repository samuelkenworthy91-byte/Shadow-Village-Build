from pathlib import Path

p = Path("app/src/App.tsx")
s = p.read_text(encoding="utf-8")
old = '<BingoBookOverlay s={s} onChanged={force} onClose={() => setBingoBookOpen(false)} />'
new = '<BingoBookOverlay s={s} onChanged={() => { if (sRef.current.phase !== "paused") setBingoBookOpen(false); force(); }} onClose={() => setBingoBookOpen(false)} />'
if old not in s:
    if new in s:
        print("Bingo Book v7.1 battle-close fix already applied")
    else:
        raise SystemExit("Bingo Book v7.1 App anchor not found")
else:
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("Bingo Book v7.1 battle-close fix applied")
