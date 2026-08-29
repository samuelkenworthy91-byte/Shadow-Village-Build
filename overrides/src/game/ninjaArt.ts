import type { Look } from "./types";

/**
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
  .filter((id) => !Object.values(LEGEND_ART).includes(id));

export type NinjaArtMeta = {
  bustTop: number;
};

export const NINJA_ART_META: Record<number, NinjaArtMeta> = {
  1: { bustTop: 153 },
  2: { bustTop: 98 },
  3: { bustTop: 116 },
  4: { bustTop: 148 },
  5: { bustTop: 142 },
  6: { bustTop: 145 },
  7: { bustTop: 37 },
  8: { bustTop: 126 },
  9: { bustTop: 143 },
  10: { bustTop: 145 },
  11: { bustTop: 125 },
  12: { bustTop: 142 },
  13: { bustTop: 145 },
  14: { bustTop: 120 },
  15: { bustTop: 116 },
  16: { bustTop: 112 },
  17: { bustTop: 96 },
  18: { bustTop: 115 },
  19: { bustTop: 112 },
  20: { bustTop: 129 },
  21: { bustTop: 140 },
  22: { bustTop: 131 },
  23: { bustTop: 135 },
  24: { bustTop: 133 },
  25: { bustTop: 127 },
  26: { bustTop: 141 },
  27: { bustTop: 81 },
  28: { bustTop: 146 },
  29: { bustTop: 151 },
  30: { bustTop: 68 },
  31: { bustTop: 146 },
  32: { bustTop: 136 },
  33: { bustTop: 126 },
  34: { bustTop: 100 },
  35: { bustTop: 136 },
  36: { bustTop: 147 },
  37: { bustTop: 120 },
  38: { bustTop: 122 },
  39: { bustTop: 154 },
  40: { bustTop: 106 },
  41: { bustTop: 139 },
  42: { bustTop: 83 },
  43: { bustTop: 131 },
  44: { bustTop: 144 },
  45: { bustTop: 117 },
  46: { bustTop: 146 },
  47: { bustTop: 169 },
  48: { bustTop: 139 },
  49: { bustTop: 147 },
  50: { bustTop: 149 },
  51: { bustTop: 186 },
  52: { bustTop: 61 },
  53: { bustTop: 145 },
  54: { bustTop: 155 },
  55: { bustTop: 86 },
  56: { bustTop: 108 },
  57: { bustTop: 106 },
  58: { bustTop: 106 },
  59: { bustTop: 105 },
  60: { bustTop: 113 },
  61: { bustTop: 142 },
  62: { bustTop: 117 },
  63: { bustTop: 152 },
  64: { bustTop: 175 },
  65: { bustTop: 77 },
  66: { bustTop: 149 },
  67: { bustTop: 6 },
  68: { bustTop: 120 },
  69: { bustTop: 154 },
  70: { bustTop: 117 },
  71: { bustTop: 127 },
  72: { bustTop: 130 },
  73: { bustTop: 142 },
  74: { bustTop: 120 },
  75: { bustTop: 149 },
  76: { bustTop: 138 },
  77: { bustTop: 126 },
  78: { bustTop: 117 },
  79: { bustTop: 151 },
  80: { bustTop: 150 }
};

function mix32(x: number): number {
  x = Math.imul(x ^ (x >>> 16), 0x45d9f3b);
  x = Math.imul(x ^ (x >>> 16), 0x45d9f3b);
  return (x ^ (x >>> 16)) >>> 0;
}

/** Stable portrait assignment: a ninja keeps the same art for the life of the save. */
export function ninjaArtId(n: { id: number; look: Look; legend?: string | null }): number {
  if (n.legend && LEGEND_ART[n.legend]) return LEGEND_ART[n.legend];

  // Include immutable appearance rolls as salt so sequential IDs distribute well.
  const L = n.look;
  let salt = n.id >>> 0;
  salt ^= (L.hair & 15) << 1;
  salt ^= (L.hairColor & 15) << 5;
  salt ^= (L.skin & 7) << 9;
  salt ^= (L.outfit & 15) << 12;
  salt ^= (L.acc & 7) << 17;
  salt ^= (L.build & 7) << 20;
  const idx = mix32(salt) % GENERAL_ART_IDS.length;
  return GENERAL_ART_IDS[idx];
}

export function ninjaArtMeta(n: { id: number; look: Look; legend?: string | null }): NinjaArtMeta {
  return NINJA_ART_META[ninjaArtId(n)] ?? { bustTop: 72 };
}

export function ninjaArtSrc(n: { id: number; look: Look; legend?: string | null }): string {
  return `/ninjas/ninja_${String(ninjaArtId(n)).padStart(3, "0")}.png`;
}
