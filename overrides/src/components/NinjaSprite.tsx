import { ENEMY_KINDS, NATURE_META } from "../game/content";
import { ninjaArtMeta, ninjaArtSrc } from "../game/ninjaArt";
import type { Look, Nature, NinRank } from "../game/types";

function shade(hex: string, amt: number): string {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.max(0, Math.min(255, ((n >> 16) & 255) + amt));
  const g = Math.max(0, Math.min(255, ((n >> 8) & 255) + amt));
  const b = Math.max(0, Math.min(255, (n & 255) + amt));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}

// Master raster assets are all normalized to this canvas.
export const SPRITE_W = 240;
export const SPRITE_H = 536;
const FULL_RATIO = SPRITE_W / SPRITE_H;
const BUST_RATIO = 34 / 40;
const FULL_SCALE = 1.08;
const BUST_VISIBLE_H = 208;
const BUST_SCALE = SPRITE_H / BUST_VISIBLE_H;

/**
 * Image-backed shinobi renderer. The rest of the game keeps using the same
 * NinjaSprite API as before, so this is an art-only swap rather than a UI rewrite.
 */
export default function NinjaSprite({
  n,
  h,
  crop = "bust",
  grey = false,
  aura = false,
  className,
}: {
  n: { id: number; look: Look; nature: Nature; level: number; rank: NinRank; legend?: string | null };
  h: number;
  crop?: "bust" | "full";
  grey?: boolean;
  aura?: boolean;
  className?: string;
}) {
  const src = ninjaArtSrc(n);
  const artMeta = ninjaArtMeta(n);
  const nat = NATURE_META[n.nature];
  const width = h * (crop === "bust" ? BUST_RATIO : FULL_RATIO);
  const bustImageH = h * BUST_SCALE;
  const bustImageW = bustImageH * FULL_RATIO;
  const bustTopPx = -(artMeta.bustTop / SPRITE_H) * bustImageH;

  return (
    <span
      className={className}
      aria-hidden
      style={{
        position: "relative",
        display: "inline-block",
        flex: "0 0 auto",
        width,
        height: h,
        overflow: crop === "bust" ? "hidden" : "visible",
        verticalAlign: "middle",
      }}
    >
      {aura && (
        <span
          style={{
            position: "absolute",
            inset: crop === "bust" ? "3% 3%" : "7% 0% 3%",
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${nat.color}66 0%, ${nat.color}30 43%, transparent 72%)`,
            filter: `blur(${Math.max(1.5, h * 0.035)}px)`,
            opacity: 0.9,
            pointerEvents: "none",
          }}
        />
      )}
      <img
        src={src}
        alt=""
        draggable={false}
        decoding="async"
        style={crop === "full"
          ? {
              position: "absolute",
              left: "50%",
              bottom: 0,
              width: `${FULL_SCALE * 100}%`,
              height: `${FULL_SCALE * 100}%`,
              maxWidth: "none",
              transform: "translateX(-50%)",
              objectFit: "contain",
              objectPosition: "center bottom",
              filter: grey ? "grayscale(1) saturate(0.15) brightness(0.72)" : undefined,
              opacity: grey ? 0.78 : 1,
              userSelect: "none",
              pointerEvents: "none",
            }
          : {
              position: "absolute",
              left: "50%",
              top: bustTopPx,
              width: bustImageW,
              height: bustImageH,
              maxWidth: "none",
              transform: "translateX(-50%)",
              objectFit: "contain",
              objectPosition: "center top",
              filter: grey ? "grayscale(1) saturate(0.15) brightness(0.72)" : undefined,
              opacity: grey ? 0.78 : 1,
              userSelect: "none",
              pointerEvents: "none",
            }}
      />
    </span>
  );
}

/* ---------------- enemy art ---------------- */

export function EnemyArt({ kind, h, dead }: { kind: string; h: number; dead?: boolean }) {
  const meta = ENEMY_KINDS[kind] ?? ENEMY_KINDS.grunt;
  const c = meta.color;
  const body = "#2a2733";
  const dark = shade(body, -10);
  return (
    <svg width={h * 0.62} height={h} viewBox="0 -2 62 102" fill="none" aria-hidden style={{ opacity: dead ? 0.28 : 1 }}>
      <ellipse cx="31" cy="98" rx="16" ry="3.4" fill="#2b2118" opacity="0.25" />
      <path d="M22 60q-2 20-2.5 29l-.5 9h8.5l1-9 2.5-27z" fill={dark} />
      <path d="M40 60q2 20 2.5 29l.5 9h-8.5l-1-9-2.5-27z" fill={body} />
      <path
        d={`M${kind === "brute" ? 13 : 16.5} 35q${kind === "brute" ? 18 : 14.5} -9 ${kind === "brute" ? 36 : 29} 0 q-2 15-3.5 27 q-${kind === "brute" ? 15 : 11} 5 -${kind === "brute" ? 30 : 22} 0z`}
        fill={body}
      />
      <path d="M31 33v30" stroke={c} strokeWidth="2" opacity="0.5" />
      <path d="M16.5 36q-7 4-8.5 15l-1 13 6.5 2 5.5-17z" fill={dark} />
      <path d="M45.5 36q7 4 8.5 15l1 13-6.5 2-5.5-17z" fill={dark} />
      <ellipse cx="31" cy="20" rx="12" ry="13" fill="#211f2a" />
      <path d="M19 16q12-4 24 0-.5 4-1 7-11-4-22 0z" fill={shade(c, -34)} />
      <path d="M23.5 18.4l5 1.9-5 1.9z" fill={c}>
        <animate attributeName="opacity" values="1;0.42;1" dur="2.1s" repeatCount="indefinite" />
      </path>
      <path d="M38.5 18.4l-5 1.9 5 1.9z" fill={c}>
        <animate attributeName="opacity" values="1;0.42;1" dur="2.1s" repeatCount="indefinite" />
      </path>
      {kind === "brute" && <path d="M19.5 7.5q3 3 5 6.5M42.5 7.5q-3 3-5 6.5" stroke={c} strokeWidth="3.4" strokeLinecap="round" fill="none" />}
      {kind === "shadow" && <path d="M19 12q12-9.5 24 0-12-3.6-24 0z" fill={c} opacity="0.6" />}
      {kind === "boss" && (
        <>
          <path d="M17.5 9.5q3.5 2.6 6 5.5M44.5 9.5q-3.5 2.6-6 5.5" stroke={c} strokeWidth="3.4" strokeLinecap="round" fill="none" />
          <path d="M31 2l4 8h-8z" fill={c} />
          <path d="M13 39l-6 26 8.5-2.5 4-20z" fill={c} opacity="0.4" />
        </>
      )}
      {(kind === "shadow" || kind === "boss") && <path d="M52 39l7-24 3 2-6.4 24z" fill="#d3d8de" stroke="#8a9099" strokeWidth="0.7" />}
    </svg>
  );
}
