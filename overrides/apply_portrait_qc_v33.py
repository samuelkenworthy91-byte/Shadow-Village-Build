"""Finalize the curated portrait pool after all gameplay/presentation patches.

Retains approved IDs, repairs retired saved assignments deterministically,
updates replacement-art bust crops, and precaches only real approved files.
"""
import re
from portrait_library import APP, QC, approved_ids, install, validate_assets

ART = APP / 'src/game/ninjaArt.ts'
SW = APP / 'public/sw.js'
MARKER = '// Portrait QC v33: approved IDs remain stable across pool reductions.'


def main():
    art = ART.read_text()
    # Reinstall the checked sources last so an old build artifact cannot restore
    # a white pocket or a retired portrait over the reviewed assets.
    install()
    ids = approved_ids()
    pool = 'export const GENERAL_ART_IDS: number[] = [' + ', '.join(map(str, ids)) + '];'
    if MARKER not in art:
        art, count = re.subn(r'export const GENERAL_ART_IDS: number\[\] = [^\n]+;', pool + '\n' + MARKER + '\nconst APPROVED_ART_IDS = new Set(GENERAL_ART_IDS);', art, count=1)
        if count != 1:
            raise RuntimeError('Expected general portrait pool declaration')
        old = 'typeof n.portrait === "number" && n.portrait >= 1 && n.portrait <= GENERAL_ART_IDS.length'
        new = 'typeof n.portrait === "number" && Number.isInteger(n.portrait) && APPROVED_ART_IDS.has(n.portrait)'
        if old not in art:
            raise RuntimeError('Expected v29 assigned-portrait validation')
        art = art.replace(old, new, 1)
        old = '  const idx = mix32(salt) % GENERAL_ART_IDS.length;\n  return GENERAL_ART_IDS[idx];'
        new = '''  // Preserve the previous 370-ID hash for every approved legacy portrait.
  // Only retired/invalid assignments fall back into the smaller approved pool.
  const legacyId = (mix32(salt) % 370) + 1;
  if (APPROVED_ART_IDS.has(legacyId)) return legacyId;
  return GENERAL_ART_IDS[mix32(salt ^ 0x33a7f19d) % GENERAL_ART_IDS.length];'''
        if old not in art:
            raise RuntimeError('Expected legacy portrait hash tail')
        art = art.replace(old, new, 1)
    else:
        art = re.sub(r'export const GENERAL_ART_IDS: number\[\] = [^\n]+;', pool, art, count=1)
    art = art.replace('All 370 portraits share one unrestricted', f'All {len(ids)} approved portraits share one unrestricted')
    for key in QC['removed']:
        art = re.sub(rf'^  {key}: \{{ bustTop: \d+ \}},?\n', '', art, flags=re.M)
    # v29 replaced these images, but retained several v27 crop coordinates.
    # Reset to the replacement figure headroom, with measured tall-prop cases.
    measured = {272: 145, 313: 145, 350: 135, 354: 112, 362: 125, 363: 174}
    for i in ids:
        if i >= 251:
            art = re.sub(rf'  {i}: \{{ bustTop: \d+ \}}', f'  {i}: {{ bustTop: {measured.get(i, 92)} }}', art)
    ART.write_text(art)

    sw = SW.read_text()
    sw, count = re.subn(r'^const NINJA_ART = .*?;$', 'const NINJA_ART = [' + ', '.join(map(str, ids)) + '].map((id) => `/ninjas/ninja_${String(id).padStart(3, "0")}.png`);', sw, count=1, flags=re.M)
    if count != 1:
        raise RuntimeError('Expected service worker portrait cache list')
    sw = re.sub(r'const CACHE = "[^"]+";', 'const CACHE = "kage-life-v5-portrait-qc";', sw, count=1)
    sw = re.sub(r'// so pre-cache the complete .*?art library as well as the app shell\.', f'// so pre-cache the {len(ids)} approved portraits as well as the app shell.', sw)
    SW.write_text(sw)
    validate_assets()
    print(f'Applied portrait QC v33: {len(ids)} portraits; safe saved-ID fallback; matching offline cache')


if __name__ == '__main__':
    main()
