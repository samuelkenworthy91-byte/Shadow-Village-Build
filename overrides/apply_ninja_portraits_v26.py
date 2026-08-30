from pathlib import Path

ROOT = Path("app")
ART = ROOT / "src/game/ninjaArt.ts"
SW = ROOT / "public/sw.js"

META = {
    81:124,82:124,83:124,84:124,85:124,86:124,87:124,88:124,89:124,90:124,
    91:124,92:124,93:124,94:124,95:124,96:124,97:124,98:124,99:124,100:124,
    101:155,102:124,103:124,104:182,105:124,106:124,107:124,108:124,109:124,110:124,
    111:124,112:124,113:124,114:124,115:124,116:124,117:124,118:124,119:124,120:124,
    121:124,122:124,123:124,124:124,125:124,126:126,127:124,128:124,129:124,130:124,
    131:146,132:124,133:124,134:124,135:124,136:124,137:124,138:162,139:124,140:124,
    141:129,142:124,143:124,144:124,145:135,146:124,147:124,148:124,149:124,150:124,
    151:138,152:124,153:124,154:124,155:124,156:124,157:126,158:124,159:124,160:124,
    161:179,162:124,163:124,164:124,165:124,166:124,167:124,168:150,169:124,170:124,
    171:138,172:124,173:124,174:124,175:124,176:124,177:124,178:124,179:124,180:124,
    181:150,182:124,183:124,184:124,185:124,186:162,187:124,188:124,189:167,190:161,
}
# The 191-250 generation was authored with consistent framing, so the standard
# bust crop is appropriate for the whole new batch.
META.update({i: 124 for i in range(191, 251)})

s = ART.read_text()
old_pool = '''/**
 * Image-backed player ninja art. Six generated portraits are reserved for
 * legendary archetypes; the remaining 74 form the deterministic general pool.
 */
export const LEGEND_ART: Record<string, number> = {
  sannin: 62,
  jinchuriki: 66,
  doujutsu: 67,
  puppeteer: 68,
  swordsman: 69,
  sage: 70,
};

export const GENERAL_ART_IDS: number[] = Array.from({ length: 80 }, (_, i) => i + 1)
  .filter((id) => !Object.values(LEGEND_ART).includes(id));'''
new_pool = '''/**
 * Image-backed player ninja art. All 250 portraits share one unrestricted
 * deterministic pool. Legendary status never forces or excludes a portrait.
 */
export const GENERAL_ART_IDS: number[] = Array.from({ length: 250 }, (_, i) => i + 1);'''
if old_pool not in s:
    raise RuntimeError("Expected legacy 80-portrait pool was not found")
s = s.replace(old_pool, new_pool)

marker = "  80: { bustTop: 150 }\n};"
if marker not in s:
    raise RuntimeError("Expected NINJA_ART_META tail was not found")
extra = "  80: { bustTop: 150 },\n" + "\n".join(
    f"  {i}: {{ bustTop: {META[i]} }}," for i in range(81, 251)
) + "\n};"
s = s.replace(marker, extra)

s = s.replace(
    '  if (n.legend && LEGEND_ART[n.legend]) return LEGEND_ART[n.legend];\n\n',
    '  // Legendary ninjas deliberately use the same unrestricted pool.\n',
)
s = s.replace(
    'return NINJA_ART_META[ninjaArtId(n)] ?? { bustTop: 72 };',
    'return NINJA_ART_META[ninjaArtId(n)] ?? { bustTop: 124 };',
)
ART.write_text(s)

sw = SW.read_text()
old_art = 'const NINJA_ART = Array.from({ length: 80 }, (_, i) => `/ninjas/ninja_${String(i + 1).padStart(3, "0")}.png`);'
new_art = 'const NINJA_ART = Array.from({ length: 250 }, (_, i) => `/ninjas/ninja_${String(i + 1).padStart(3, "0")}.png`);'
if old_art not in sw:
    raise RuntimeError("Expected final 80-portrait service-worker list was not found")
sw = sw.replace(old_art, new_art)
sw = sw.replace('shadow-village-progression-dev-v3', 'shadow-village-progression-dev-v4-ninja250')
SW.write_text(sw)

art_check = ART.read_text()
sw_check = SW.read_text()
assert "LEGEND_ART" not in art_check
assert "length: 250" in art_check
assert "250: { bustTop: 124 }" in art_check
assert '.webp' not in art_check
assert "length: 250" in sw_check
assert "shadow-village-progression-dev-v4-ninja250" in sw_check
print("Applied unrestricted 1-250 ninja portrait library with PNG runtime paths")
