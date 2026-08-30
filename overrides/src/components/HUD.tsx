import { Coins, Flame, Menu, Trophy, Volume2, VolumeX, Wheat, Zap } from "lucide-react";
import type { GameState } from "../game/types";
import { FARM_RICE, TEA_GOLD } from "../game/content";
import { apMax, hasTech, streakMult } from "../game/engine";
import { cn } from "../utils/cn";
import type { ReactNode } from "react";

function formatGain(value: number): string {
  return Number.isInteger(value)
    ? value.toLocaleString()
    : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function Chip({
  id,
  icon,
  value,
  gain,
  title,
  warn,
}: {
  id?: string;
  icon: ReactNode;
  value: string;
  gain?: number;
  title?: string;
  warn?: boolean;
}) {
  return (
    <span
      id={id}
      title={title}
      className={cn(
        "inline-flex h-7 items-center gap-1 rounded-lg bg-black/30 px-2 text-[13px] font-semibold tabular-nums ring-1 ring-inset ring-white/5",
        warn && "animate-pulse"
      )}
    >
      {icon}
      <span>{value}</span>
      {gain !== undefined && (
        <span className="text-[10px] font-bold text-[#8fce6a]">+{formatGain(gain)}</span>
      )}
    </span>
  );
}

export default function HUD({
  s,
  muted,
  onMute,
  onPause,
}: {
  s: GameState;
  muted: boolean;
  onMute: () => void;
  onPause: () => void;
}) {
  const max = apMax(s);
  const nextGoldFromBuildings = TEA_GOLD * s.b.tea * (hasTech(s, "tea_merchant_contacts") ? 1.25 : 1);
  const nextRiceFromBuildings = FARM_RICE * s.b.farm * (hasTech(s, "farm_efficiency") ? 1.25 : 1);

  return (
    <header className="flex h-11 shrink-0 items-center gap-1.5 rounded-xl bg-[#151728]/85 px-2 ring-1 ring-white/10 backdrop-blur sm:gap-2 sm:px-3">
      <span className="grid h-7 w-7 shrink-0 place-items-center overflow-hidden rounded-lg bg-[#0d0e1a] ring-1 ring-white/10 shadow-[0_0_14px_rgba(226,69,47,0.25)]">
        <img src="/icon.png" alt="" className="h-full w-full object-cover" draggable={false} />
      </span>
      <span className="hidden font-display text-[13px] font-bold tracking-[0.22em] text-paper/90 xl:block">SHADOW VILLAGE</span>
      <div className="mx-0.5 hidden h-5 w-px bg-white/10 xl:block" />

      <Chip
        id="hud-gold"
        icon={<Coins size={13} className="text-gold" />}
        value={Math.floor(s.gold).toLocaleString()}
        gain={nextGoldFromBuildings}
        title={`Next day from Tea Houses: +${formatGain(nextGoldFromBuildings)} gold`}
      />
      <Chip
        id="hud-rice"
        icon={<Wheat size={13} className={s.hungry ? "text-vermil" : "text-[#8fce6a]"} />}
        value={Math.floor(s.rice).toLocaleString()}
        gain={nextRiceFromBuildings}
        title={`Next day from Rice Paddies: +${formatGain(nextRiceFromBuildings)} rice before ninja consumption`}
        warn={s.hungry}
      />
      <Chip icon={<Trophy size={13} className="text-[#ffe9b8]" />} value={s.score.toLocaleString()} />

      <span id="hud-ap" className="inline-flex h-7 items-center gap-1 rounded-lg bg-black/30 px-2 ring-1 ring-inset ring-white/5" title={`${s.ap} of ${max} actions left today`}>
        <Zap size={12} className={s.ap > 0 ? "text-gold" : "text-paper/25"} />
        <span className="flex gap-[3px]">
          {Array.from({ length: max }, (_, i) => (
            <i key={i} className={cn("block h-3 w-[5px] rounded-sm transition-colors", i < s.ap ? "bg-gold" : "bg-white/12")} />
          ))}
        </span>
      </span>

      {s.streak >= 2 && (
        <span className="hidden h-7 items-center gap-1 rounded-lg bg-gold/15 px-2 text-[12px] font-bold text-gold ring-1 ring-inset ring-gold/30 sm:inline-flex">
          <Flame size={12} />×{streakMult(s).toFixed(1)}
        </span>
      )}

      <div className="flex-1" />

      <span className="inline-flex h-7 items-center gap-1.5 rounded-lg bg-black/30 px-2 text-[12px] font-semibold ring-1 ring-inset ring-white/5">
        <span className="font-display text-gold">日</span>
        <span className="tabular-nums text-paper/90">Day {s.day}</span>
      </span>

      <button
        onClick={onMute}
        aria-label="Toggle sound"
        className="grid h-7 w-7 place-items-center rounded-lg bg-black/30 text-paper/70 ring-1 ring-inset ring-white/5 transition hover:text-paper active:scale-90"
      >
        {muted ? <VolumeX size={14} /> : <Volume2 size={14} />}
      </button>
      <button
        onClick={onPause}
        aria-label="Menu"
        className="grid h-7 w-7 place-items-center rounded-lg bg-black/30 text-paper/70 ring-1 ring-inset ring-white/5 transition hover:text-paper active:scale-90"
      >
        <Menu size={14} />
      </button>
    </header>
  );
}
