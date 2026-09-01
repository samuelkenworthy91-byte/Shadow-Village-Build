from pathlib import Path

ROOT = Path("app")
ART = ROOT / "src/game/ninjaArt.ts"
SW = ROOT / "public/sw.js"

# bustTop crop lines measured from the final 240x536 normalized portraits
# (figure head top minus ~24px headroom, clamped to the established range).
META = {
    251: 92,
    252: 92,
    253: 92,
    254: 171,
    255: 92,
    256: 92,
    257: 92,
    258: 92,
    259: 158,
    260: 92,
    261: 92,
    262: 92,
    263: 155,
    264: 92,
    265: 92,
    266: 92,
    267: 92,
    268: 92,
    269: 139,
    270: 92,
    271: 92,
    272: 145,
    273: 92,
    274: 92,
    275: 92,
    276: 92,
    277: 92,
    278: 92,
    279: 92,
    280: 92,
    281: 92,
    282: 92,
    283: 92,
    284: 134,
    285: 92,
    286: 92,
    287: 92,
    288: 92,
    289: 116,
    290: 92,
    291: 92,
    292: 109,
    293: 113,
    294: 111,
    295: 92,
    296: 92,
    297: 92,
    298: 92,
    299: 92,
    300: 92,
    301: 92,
    302: 92,
    303: 92,
    304: 92,
    305: 92,
    306: 92,
    307: 92,
    308: 92,
    309: 92,
    310: 92
}

s = ART.read_text(encoding="utf-8")

old_pool = """/**
 * Image-backed player ninja art. All 250 portraits share one unrestricted
 * deterministic pool. Legendary status never forces or excludes a portrait.
 */
export const GENERAL_ART_IDS: number[] = Array.from({ length: 250 }, (_, i) => i + 1);"""
new_pool = """/**
 * Image-backed player ninja art. All 310 portraits share one unrestricted
 * deterministic pool. Legendary status never forces or excludes a portrait.
 */
export const GENERAL_ART_IDS: number[] = Array.from({ length: 310 }, (_, i) => i + 1);"""
if new_pool in s:
    print("ninjaArt pool already at 310 portraits")
elif old_pool in s:
    s = s.replace(old_pool, new_pool)
else:
    raise RuntimeError("Expected 250-portrait pool block was not found")

if "  310: { bustTop:" not in s:
    marker = "  250: { bustTop: 124 },\n};"
    if marker not in s:
        raise RuntimeError("Expected NINJA_ART_META tail (id 250) was not found")
    extra = "  250: { bustTop: 124 },\n" + "\n".join(
        f"  {i}: {{ bustTop: {META[i]} }}," for i in range(251, 311)
    ) + "\n};"
    s = s.replace(marker, extra)

ART.write_text(s, encoding="utf-8")

sw = SW.read_text(encoding="utf-8")
old_art = 'const NINJA_ART = Array.from({ length: 250 }, (_, i) => `/ninjas/ninja_${String(i + 1).padStart(3, "0")}.png`);'
new_art = 'const NINJA_ART = Array.from({ length: 310 }, (_, i) => `/ninjas/ninja_${String(i + 1).padStart(3, "0")}.png`);'
if new_art in sw:
    print("service worker art list already at 310 portraits")
elif old_art in sw:
    sw = sw.replace(old_art, new_art)
else:
    raise RuntimeError("Expected 250-portrait service-worker list was not found")
# The service-worker CACHE constant is intentionally left alone here;
# later pipeline stages anchor patches on it. The final stage bumps it.
SW.write_text(sw, encoding="utf-8")

art_check = ART.read_text(encoding="utf-8")
sw_check = SW.read_text(encoding="utf-8")
assert "length: 310" in art_check
assert "310: { bustTop:" in art_check
assert "length: 310" in sw_check
print("Applied 251-310 ninja portrait library expansion")
