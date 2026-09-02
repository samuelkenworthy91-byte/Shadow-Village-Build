"""v31: generated building art replaces the CSS shape buildings in the scene.

overrides/building_assets_v31 holds individually generated, cel-shaded
anime building sprites (cut out on pure white with the gentle solo
pipeline: flood-fill background removal, no closing, strict defringe).
This patch installs them into app/public/buildings and wires them into
the village scene: building types with art render the sprite (with the
level pips kept); types without art keep the CSS shape fallback until
their art exists. The service worker precaches the new assets.

Runs after apply_ui_daily_panel_v30.py, before the v18/v19 patches.
"""

import shutil
from pathlib import Path

ROOT = Path("app")
SRC = Path("overrides/building_assets_v31")
OUT = ROOT / "public/buildings"
SCENE = ROOT / "src/components/Scene.tsx"
CSS = ROOT / "src/index.css"
SW = ROOT / "public/sw.js"

# ---------------------------------------------------------------- install art
OUT.mkdir(parents=True, exist_ok=True)
types = []
for webp in sorted(SRC.glob("bld_*.webp")):
    shutil.copy(webp, OUT / webp.name)
    types.append(webp.stem[len("bld_"):])
if not types:
    raise RuntimeError("no building art found in overrides/building_assets_v31")
print(f"building art installed: {len(types)} ({', '.join(types)})")

# ---------------------------------------------------------------- Scene.tsx
s = SCENE.read_text(encoding="utf-8")

set_line = f"const BLD_ART = new Set<string>({sorted(types)!r});".replace("'", '"')
decl = f"""// building types with generated art (CSS shapes remain the fallback)
{set_line}
"""
anchor_decl = 'const DISPLAY_ORDER = ["tea", "farm", "hall", "dojo", "tower", "shrine", "intel", "hospital", "embassy", "anbu"] as const;'
if "const BLD_ART = new Set" not in s:
    if anchor_decl not in s:
        raise RuntimeError("Scene DISPLAY_ORDER anchor not found")
    s = s.replace(anchor_decl, anchor_decl + "\n" + decl, 1)
else:
    import re
    s = re.sub(r"const BLD_ART = new Set<string>\([^)]*\);", set_line, s, count=1)

old_block = """              <div className="b-roof" />
              <div className="b-body"><span className="b-kanji">{meta.kanji}</span></div>
              <div className="b-pips">"""
new_block = """              {BLD_ART.has(t) ? (
                <img src={`/buildings/bld_${t}.webp`} alt={meta.name} className="b-art" draggable={false} />
              ) : (
                <>
                  <div className="b-roof" />
                  <div className="b-body"><span className="b-kanji">{meta.kanji}</span></div>
                </>
              )}
              <div className="b-pips">"""
if 'className="b-art"' not in s:
    if old_block not in s:
        raise RuntimeError("Scene building block not found")
    s = s.replace(old_block, new_block, 1)

SCENE.write_text(s, encoding="utf-8")
print("Scene.tsx: art-backed buildings with CSS fallback")

# ---------------------------------------------------------------- index.css
c = CSS.read_text(encoding="utf-8")
css_block = """.b-art {
  height: 76px;
  width: auto;
  filter: drop-shadow(0 3px 6px rgba(40, 30, 22, 0.5));
}

@media (max-width: 640px) {
  .b-art { height: 58px; }
}

.b-roof {"""
if ".b-art {" not in c:
    if ".b-roof {" not in c:
        raise RuntimeError("index.css .b-roof anchor not found")
    c = c.replace(".b-roof {", css_block, 1)
    CSS.write_text(c, encoding="utf-8")
print("index.css: .b-art styles added")

# ---------------------------------------------------------------- sw.js
sw = SW.read_text(encoding="utf-8")
bld_list = ", ".join(f'"/buildings/bld_{t}.webp"' for t in sorted(types))
assets_old = 'const ASSETS = ["/", "/index.html", "/icon.png", "/logo.png", "/bg-village.jpg", "/bg-raid-field.jpg", "/bg-exam-arena.jpg", "/manifest.webmanifest", ...NINJA_ART, ...RAIDER_ART];'
assets_new = f'const BLD_ART = [{bld_list}];\nconst ASSETS = ["/", "/index.html", "/icon.png", "/logo.png", "/bg-village.jpg", "/bg-raid-field.jpg", "/bg-exam-arena.jpg", "/manifest.webmanifest", ...NINJA_ART, ...RAIDER_ART, ...BLD_ART];'
if "const BLD_ART = [" not in sw:
    if assets_old not in sw:
        raise RuntimeError("sw.js ASSETS line not found")
    sw = sw.replace(assets_old, assets_new, 1)
    SW.write_text(sw, encoding="utf-8")
print("sw.js: building art precached")

# ---------------------------------------------------------------- checks
s_chk = SCENE.read_text(encoding="utf-8")
c_chk = CSS.read_text(encoding="utf-8")
sw_chk = SW.read_text(encoding="utf-8")
assert 'className="b-art"' in s_chk
assert "BLD_ART.has(t)" in s_chk
assert ".b-art {" in c_chk
assert "BLD_ART" in sw_chk
for t in types:
    assert (OUT / f"bld_{t}.webp").is_file()
print(f"Applied v31: building art for {len(types)} types")
