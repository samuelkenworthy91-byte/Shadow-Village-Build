"""v32: preserve each ninja's exact portrait identity inside battle units.

v29 introduced a persistent per-ninja ``portrait`` assignment so roster/detail
screens can use a fair no-repeat art draw. The transient battle ``Unit`` type
predates that field, so converting a Ninja into a Unit discarded the portrait
ID. BattleScreen then reconstructed a small Ninja-like object and ninjaArtId
fell back to the legacy hash, which could display different art in combat.

This patch carries both ``portrait`` and ``bingoArt`` through Unit creation and
passes them into NinjaSprite for allies and ninja-backed foes. Legacy saves that
do not have an assigned portrait still use the existing deterministic hash.
"""

from pathlib import Path

ROOT = Path("app")
TYPES = ROOT / "src/game/types.ts"
BATTLE = ROOT / "src/game/battle.ts"
BATTLE_SCREEN = ROOT / "src/components/BattleScreen.tsx"
NINJA_SPRITE = ROOT / "src/components/NinjaSprite.tsx"
ART = ROOT / "src/game/ninjaArt.ts"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = read(path)
    if new in text:
        print(f"{label}: already applied")
        return
    if old not in text:
        raise RuntimeError(f"{label}: expected anchor not found in {path}")
    write(path, text.replace(old, new, 1))
    print(f"{label}: applied")


# 1) The transient battle Unit must retain the same visual identity as Ninja.
replace_once(
    TYPES,
    "  ninjaId: number | null;\n  kind: string;",
    "  ninjaId: number | null;\n"
    "  /** Exact roster portrait identity carried into combat. */\n"
    "  portrait?: number;\n"
    "  /** Optional named/special portrait source (e.g. Bingo Book target). */\n"
    "  bingoArt?: string | null;\n"
    "  kind: string;",
    "Unit portrait fields",
)

# 2) Every Unit derived from a Ninja copies those identity fields.
replace_once(
    BATTLE,
    "    ninjaId: n.id,\n    kind: \"ally\",",
    "    ninjaId: n.id,\n"
    "    portrait: n.portrait,\n"
    "    bingoArt: n.bingoArt ?? null,\n"
    "    kind: \"ally\",",
    "unitFromNinja portrait copy",
)

# 3) BattleScreen must pass the copied identity to NinjaSprite for both sides.
replace_once(
    BATTLE_SCREEN,
    'n={{ id: 900000 + Number(u.uid.replace(/\\D/g, "") || 0), look: u.look, nature: u.nature ?? "fire", level: u.level, rank: u.rank ?? "genin", legend: u.legend }}',
    'n={{ id: 900000 + Number(u.uid.replace(/\\D/g, "") || 0), look: u.look, nature: u.nature ?? "fire", level: u.level, rank: u.rank ?? "genin", legend: u.legend, portrait: u.portrait, bingoArt: u.bingoArt }}',
    "enemy/rival battle portrait identity",
)
replace_once(
    BATTLE_SCREEN,
    'n={{ id: u.ninjaId ?? 0, look: u.look, nature: u.nature ?? "fire", level: u.level, rank: u.rank ?? "genin", legend: u.legend }}',
    'n={{ id: u.ninjaId ?? 0, look: u.look, nature: u.nature ?? "fire", level: u.level, rank: u.rank ?? "genin", legend: u.legend, portrait: u.portrait, bingoArt: u.bingoArt }}',
    "ally battle portrait identity",
)

# 4) Make the renderer/helper contracts explicitly acknowledge the assigned ID.
sprite = read(NINJA_SPRITE)
sprite_new = "n: { id: number; look: Look; nature: Nature; level: number; rank: NinRank; legend?: string | null; portrait?: number; bingoArt?: string | null };"
if sprite_new not in sprite:
    sprite_old = "n: { id: number; look: Look; nature: Nature; level: number; rank: NinRank; legend?: string | null; bingoArt?: string | null };"
    sprite_older = "n: { id: number; look: Look; nature: Nature; level: number; rank: NinRank; legend?: string | null };"
    if sprite_old in sprite:
        sprite = sprite.replace(sprite_old, sprite_new, 1)
    elif sprite_older in sprite:
        sprite = sprite.replace(sprite_older, sprite_new, 1)
    else:
        raise RuntimeError("NinjaSprite portrait contract: expected anchor not found")
    write(NINJA_SPRITE, sprite)
    print("NinjaSprite portrait contract: applied")
else:
    print("NinjaSprite portrait contract: already applied")

art = read(ART)
meta_old = "export function ninjaArtMeta(n: { id: number; look: Look; legend?: string | null }): NinjaArtMeta {"
meta_new = "export function ninjaArtMeta(n: { id: number; look: Look; legend?: string | null; portrait?: number }): NinjaArtMeta {"
if meta_new not in art:
    if meta_old not in art:
        raise RuntimeError("ninjaArtMeta portrait contract: expected anchor not found")
    art = art.replace(meta_old, meta_new, 1)

src_old = "export function ninjaArtSrc(n: { id: number; look: Look; legend?: string | null; bingoArt?: string | null }): string {"
src_new = "export function ninjaArtSrc(n: { id: number; look: Look; legend?: string | null; portrait?: number; bingoArt?: string | null }): string {"
if src_new not in art:
    if src_old not in art:
        raise RuntimeError("ninjaArtSrc portrait contract: expected anchor not found")
    art = art.replace(src_old, src_new, 1)
write(ART, art)
print("ninjaArt helper portrait contracts: applied")

# 5) Wiring assertions catch any future regression in the patch chain.
types_chk = read(TYPES)
battle_chk = read(BATTLE)
screen_chk = read(BATTLE_SCREEN)
sprite_chk = read(NINJA_SPRITE)
art_chk = read(ART)
assert types_chk.count("portrait?: number;") >= 2, "Ninja + Unit portrait fields expected"
assert "bingoArt?: string | null;" in types_chk
assert "portrait: n.portrait" in battle_chk
assert "bingoArt: n.bingoArt ?? null" in battle_chk
assert screen_chk.count("portrait: u.portrait") >= 2
assert screen_chk.count("bingoArt: u.bingoArt") >= 2
assert "portrait?: number; bingoArt?: string | null" in sprite_chk
assert "ninjaArtMeta(n: { id: number; look: Look; legend?: string | null; portrait?: number })" in art_chk
assert "ninjaArtSrc(n: { id: number; look: Look; legend?: string | null; portrait?: number; bingoArt?: string | null })" in art_chk
print("Applied v32: battle portraits now preserve exact roster identity")
