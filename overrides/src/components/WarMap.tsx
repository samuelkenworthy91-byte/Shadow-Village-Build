import { useMemo, useState } from "react";
import { Eye, Flag, Map, Shield, Swords } from "lucide-react";
import type { GameState, WarFactionId, WarOperationType } from "../game/types";
import { WAR_FACTIONS, WAR_LINKS, isShadowFrontier } from "../game/war";
import { cn } from "../utils/cn";

const OWNER_STYLE: Record<WarFactionId, string> = {
  shadow: "border-vermil/70 bg-vermil/20 text-[#ffd0c8] shadow-[0_0_18px_rgba(226,69,47,0.18)]",
  ember: "border-orange-400/60 bg-orange-950/55 text-orange-200",
  mist: "border-cyan-400/50 bg-cyan-950/50 text-cyan-100",
  stone: "border-slate-400/50 bg-slate-800/75 text-slate-100",
  gold: "border-amber-400/55 bg-amber-950/55 text-amber-100",
  neutral: "border-white/15 bg-black/45 text-paper/65",
};

const OWNER_LINE: Record<WarFactionId, string> = {
  shadow: "#e2452f",
  ember: "#f97316",
  mist: "#22d3ee",
  stone: "#94a3b8",
  gold: "#fbbf24",
  neutral: "#596174",
};

const OP_META: Record<WarOperationType, { label: string; help: string }> = {
  scout: { label: "Scout", help: "Reveal strength. Can reach any territory." },
  raid: { label: "Raid", help: "Use Stealth, Ninjutsu and Tactics to weaken a frontier territory." },
  assault: { label: "Assault", help: "Try to seize a neighbouring territory for Shadow Village." },
  fortify: { label: "Fortify", help: "Strengthen a Shadow-controlled territory." },
};

export default function WarMap({
  s,
  onOperation,
  onReturn,
}: {
  s: GameState;
  onOperation: (territoryId: string, op: WarOperationType, ninjaIds: number[]) => void;
  onReturn: () => void;
}) {
  const [selectedId, setSelectedId] = useState(() => s.war.territories[0]?.id ?? "shadow_village");
  const [selectedNinjas, setSelectedNinjas] = useState<number[]>([]);
  const [operation, setOperation] = useState<WarOperationType>("scout");

  const selected = s.war.territories.find((t) => t.id === selectedId) ?? s.war.territories[0];
  const ready = useMemo(
    () => [...s.ninjas].filter((n) => n.status === "ready").sort((a, b) => (b.s.tac + b.s.ste + b.level) - (a.s.tac + a.s.ste + a.level)).slice(0, 10),
    [s.ninjas]
  );
  const controlled = s.war.territories.filter((t) => t.owner === "shadow").length;
  const founder = s.ninjas.find((n) => n.id === s.war.founderId);

  const toggleNinja = (id: number) => {
    setSelectedNinjas((ids) => ids.includes(id) ? ids.filter((x) => x !== id) : ids.length >= 4 ? ids : [...ids, id]);
  };

  if (!selected) return null;
  const frontier = isShadowFrontier(s, selected.id);
  const opDisabled = s.war.operationsLeft <= 0 || selectedNinjas.length === 0 ||
    (operation === "fortify" && selected.owner !== "shadow") ||
    (operation === "assault" && (selected.owner === "shadow" || !frontier)) ||
    (operation === "raid" && !frontier);

  return (
    <section className="min-h-0 overflow-y-auto rounded-xl bg-[#111322]/92 p-3 ring-1 ring-white/10 lg:col-span-3">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="mr-auto">
          <div className="flex items-center gap-2 font-display text-sm font-bold tracking-[0.16em] text-paper/90">
            <Map size={16} className="text-vermil" /> KAGE ERA WAR MAP
          </div>
          <p className="mt-1 text-[10px] text-paper/45">
            Day {s.day} · War turn {s.war.turn} · {controlled}/{s.war.territories.length} territories controlled
            {founder ? ` · Founded by ${founder.name}` : ""}
          </p>
        </div>
        <div className="rounded-lg bg-black/30 px-3 py-2 text-center ring-1 ring-white/10">
          <div className="text-[9px] uppercase tracking-[0.18em] text-paper/35">Operations</div>
          <div className="font-display text-lg font-bold text-gold">{s.war.operationsLeft}/3</div>
        </div>
        <button onClick={onReturn} className="btn-ink h-9 rounded-lg px-3 text-[10px] font-bold tracking-wider">RETURN TO VILLAGE</button>
      </div>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.7fr)_minmax(290px,0.8fr)]">
        <div className="relative min-h-[430px] overflow-hidden rounded-xl bg-[radial-gradient(circle_at_50%_45%,rgba(67,74,102,0.25),rgba(6,8,16,0.96)_70%)] ring-1 ring-white/8">
          <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(rgba(255,255,255,.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.04)_1px,transparent_1px)] [background-size:28px_28px]" />
          <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            {WAR_LINKS.map(([a, b]) => {
              const ta = s.war.territories.find((t) => t.id === a);
              const tb = s.war.territories.find((t) => t.id === b);
              if (!ta || !tb) return null;
              const active = ta.owner === "shadow" || tb.owner === "shadow";
              return <line key={`${a}-${b}`} x1={ta.x} y1={ta.y} x2={tb.x} y2={tb.y} stroke={active ? OWNER_LINE.shadow : "#394052"} strokeWidth={active ? 0.7 : 0.45} strokeDasharray={active ? undefined : "1.2 1.2"} opacity={active ? 0.8 : 0.52} />;
            })}
          </svg>

          {s.war.territories.map((t) => {
            const hidden = t.intel <= 0 && t.owner !== "shadow";
            return (
              <button
                key={t.id}
                onClick={() => setSelectedId(t.id)}
                style={{ left: `${t.x}%`, top: `${t.y}%` }}
                className={cn(
                  "absolute w-[88px] -translate-x-1/2 -translate-y-1/2 rounded-lg border px-1.5 py-1.5 text-left transition hover:z-10 hover:scale-105 active:scale-95 sm:w-[104px]",
                  OWNER_STYLE[t.owner],
                  selectedId === t.id && "z-10 scale-105 ring-2 ring-gold/70"
                )}
              >
                <div className="truncate text-[9px] font-bold sm:text-[10px]">{t.name}</div>
                <div className="mt-0.5 flex items-center justify-between gap-1 text-[8px] opacity-75">
                  <span>{WAR_FACTIONS[t.owner].short}</span>
                  <span>{hidden ? "STR ?" : `STR ${t.strength}`}</span>
                </div>
              </button>
            );
          })}
        </div>

        <div className="space-y-3">
          <div className="rounded-xl bg-black/25 p-3 ring-1 ring-white/8">
            <div className="flex items-start gap-2">
              <div className="mr-auto">
                <h3 className="font-display text-base font-bold text-paper">{selected.name}</h3>
                <p className="text-[10px] text-paper/45">{WAR_FACTIONS[selected.owner].name} · {selected.status.replace("_", " ")}</p>
              </div>
              <div className="rounded-md bg-black/35 px-2 py-1 text-[10px] text-paper/65">Intel {selected.intel}/3</div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
              <div className="rounded-lg bg-white/[0.035] p-2"><span className="text-paper/35">Strength</span><div className="font-display text-lg text-paper">{selected.intel > 0 || selected.owner === "shadow" ? selected.strength : "?"}</div></div>
              <div className="rounded-lg bg-white/[0.035] p-2"><span className="text-paper/35">Frontier</span><div className="mt-1 font-bold text-paper/80">{frontier ? "YES" : "NO"}</div></div>
            </div>
          </div>

          <div className="rounded-xl bg-black/25 p-3 ring-1 ring-white/8">
            <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.18em] text-paper/40">Strategic operation</div>
            <div className="grid grid-cols-2 gap-1.5">
              {(["scout", "raid", "assault", "fortify"] as WarOperationType[]).map((op) => (
                <button key={op} onClick={() => setOperation(op)} className={cn("rounded-lg px-2 py-2 text-[10px] font-bold ring-1 ring-inset transition", operation === op ? "bg-vermil/20 text-[#ffb4a4] ring-vermil/50" : "bg-white/[0.03] text-paper/55 ring-white/8")}>
                  <span className="inline-flex items-center gap-1.5">{op === "scout" ? <Eye size={12} /> : op === "fortify" ? <Shield size={12} /> : op === "assault" ? <Flag size={12} /> : <Swords size={12} />}{OP_META[op].label}</span>
                </button>
              ))}
            </div>
            <p className="mt-2 min-h-8 text-[9.5px] leading-relaxed text-paper/40">{OP_META[operation].help}</p>
          </div>

          <div className="rounded-xl bg-black/25 p-3 ring-1 ring-white/8">
            <div className="mb-2 flex items-center justify-between text-[9px] font-bold uppercase tracking-[0.18em] text-paper/40">
              <span>Assign shinobi</span><span>{selectedNinjas.length}/4</span>
            </div>
            <div className="max-h-44 space-y-1 overflow-y-auto pr-1">
              {ready.length === 0 && <p className="py-3 text-center text-[10px] text-paper/35">No ready shinobi.</p>}
              {ready.map((n) => {
                const active = selectedNinjas.includes(n.id);
                return (
                  <button key={n.id} onClick={() => toggleNinja(n.id)} className={cn("flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left ring-1 ring-inset", active ? "bg-jade/10 text-jade ring-jade/35" : "bg-white/[0.025] text-paper/60 ring-white/5")}>
                    <span className="min-w-0 flex-1 truncate text-[10px] font-semibold">{n.name}</span>
                    <span className="text-[8px] opacity-60">{n.rank.toUpperCase()} · TAC {n.s.tac}</span>
                  </button>
                );
              })}
            </div>
            <button
              disabled={opDisabled}
              onClick={() => onOperation(selected.id, operation, selectedNinjas)}
              className="btn-vermil mt-3 h-10 w-full rounded-lg text-[10px] font-bold tracking-[0.14em] disabled:cursor-not-allowed disabled:opacity-30"
            >
              LAUNCH {OP_META[operation].label.toUpperCase()}
            </button>
          </div>
        </div>
      </div>

      {s.war.history.length > 0 && (
        <div className="mt-3 rounded-xl bg-black/20 p-3 ring-1 ring-white/8">
          <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.18em] text-paper/35">War chronicle</div>
          <div className="grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
            {s.war.history.slice(0, 6).map((line, i) => <p key={`${i}-${line}`} className="truncate rounded-md bg-white/[0.025] px-2 py-1.5 text-[9px] text-paper/45">{line}</p>)}
          </div>
        </div>
      )}
    </section>
  );
}
