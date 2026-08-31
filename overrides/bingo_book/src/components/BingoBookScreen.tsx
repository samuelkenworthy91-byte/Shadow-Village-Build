import { useEffect, useMemo, useState } from "react";
import type { GameState } from "../game/types";
import {
  BINGO_ORGANISATIONS,
  BINGO_TARGETS,
  ensureBingoState,
  intelBand,
  refreshPendingMissingNin,
  type BingoTargetDef,
  type BingoTargetProgress,
} from "../game/bingo";
import { cn } from "../utils/cn";

type View = "active" | "rumours" | "captured" | "resolved" | "organisations" | "black";

const threatClass: Record<string, string> = {
  B: "text-[#87c99a] bg-[#87c99a]/10 ring-[#87c99a]/25",
  A: "text-[#72b7ef] bg-[#72b7ef]/10 ring-[#72b7ef]/25",
  S: "text-[#d88ae7] bg-[#d88ae7]/10 ring-[#d88ae7]/25",
  "S+": "text-[#f29b65] bg-[#f29b65]/10 ring-[#f29b65]/25",
  SS: "text-vermil bg-vermil/10 ring-vermil/25",
  BLACK: "text-gold bg-black/45 ring-gold/25",
};

function intelLabel(value: number): string {
  return intelBand(value).replace(/^./, (x) => x.toUpperCase());
}

function TargetCard({
  target,
  progress,
  selected,
  onSelect,
}: {
  target: BingoTargetDef;
  progress: BingoTargetProgress;
  selected: boolean;
  onSelect: () => void;
}) {
  const identified = progress.intel >= 20 || progress.status !== "unknown";
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full rounded-xl bg-black/20 p-2 text-left ring-1 ring-inset transition",
        selected ? "ring-gold/55 bg-gold/[0.06]" : "ring-white/7 hover:bg-white/[0.03]",
      )}
    >
      <div className="flex items-start gap-2">
        <div className="grid h-14 w-12 shrink-0 place-items-end overflow-hidden rounded-lg bg-[#0b0c15] ring-1 ring-white/8">
          {identified ? (
            <img
              src={target.sprite}
              alt=""
              className="max-h-full max-w-full object-contain"
              onError={(e) => { e.currentTarget.style.display = "none"; }}
              draggable={false}
            />
          ) : (
            <span className="mb-2 font-display text-xl font-black text-paper/15">?</span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-[11px] font-black text-paper">
              {identified ? `${target.name} — ${target.epithet}` : "Unknown Missing-nin"}
            </p>
            <span className={cn("shrink-0 rounded px-1.5 py-0.5 text-[8px] font-black ring-1", threatClass[target.threat])}>{target.threat}</span>
          </div>
          <p className="mt-1 text-[8.5px] font-bold uppercase tracking-[0.14em] text-paper/35">{progress.status.replaceAll("_", " ")}</p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/8">
            <div className="h-full rounded-full bg-gold transition-all" style={{ width: `${Math.max(2, progress.intel)}%` }} />
          </div>
          <div className="mt-1 flex items-center justify-between text-[8px] font-bold text-paper/40">
            <span>INTEL {progress.intel}%</span>
            <span>{intelLabel(progress.intel)}</span>
          </div>
        </div>
      </div>
    </button>
  );
}

function Dossier({ target, progress }: { target: BingoTargetDef; progress: BingoTargetProgress }) {
  const intel = progress.intel;
  const showIdentity = intel >= 20;
  const showAssociates = intel >= 40;
  const showCombat = intel >= 60;
  const showDossier = intel >= 80;
  return (
    <div className="h-full overflow-y-auto rounded-2xl bg-[#11131f]/95 p-3 ring-1 ring-white/8">
      <div className="flex items-start gap-3">
        <div className="grid h-28 w-24 shrink-0 place-items-end overflow-hidden rounded-xl bg-black/35 ring-1 ring-white/8">
          {showIdentity ? (
            <img src={target.sprite} alt="" className="max-h-full max-w-full object-contain" onError={(e) => { e.currentTarget.style.display = "none"; }} draggable={false} />
          ) : (
            <span className="mb-7 font-display text-4xl font-black text-paper/10">?</span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded px-2 py-1 text-[9px] font-black ring-1", threatClass[target.threat])}>{target.threat} THREAT</span>
            <span className="rounded bg-black/30 px-2 py-1 text-[8px] font-black text-paper/45 ring-1 ring-white/7">INTEL {intel}%</span>
          </div>
          <h2 className="mt-2 font-display text-xl font-black text-paper">{showIdentity ? target.name : "IDENTITY UNKNOWN"}</h2>
          <p className="text-[11px] font-black tracking-wide text-vermil/85">{showIdentity ? target.epithet : "BINGO BOOK TARGET"}</p>
          <p className="mt-2 text-[9.5px] leading-relaxed text-paper/55">{intel > 0 ? target.summary : "Gather intelligence missions to build a usable dossier before committing a hunter team."}</p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">LEVEL</p><p className="mt-1 text-[11px] font-black text-paper">{showIdentity ? `~${target.level}` : "???"}</p></div>
        <div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">ELEMENTS</p><p className="mt-1 text-[10px] font-black text-paper">{showIdentity ? target.elements.join(" / ") : "Unknown"}</p></div>
        <div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">DEAD</p><p className="mt-1 text-[10px] font-black text-gold">{showIdentity ? `${target.bountyDead.toLocaleString()} 両` : "???"}</p></div>
        <div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">ALIVE</p><p className="mt-1 text-[10px] font-black text-jade">{showIdentity ? `${target.bountyAlive.toLocaleString()} 両` : "???"}</p></div>
      </div>

      <section className="mt-3 rounded-xl bg-black/20 p-3 ring-1 ring-white/6">
        <p className="text-[8px] font-black tracking-[0.18em] text-gold/75">INTELLIGENCE FILE</p>
        <div className="mt-2 space-y-2">
          {target.intel.map((reveal) => (
            <div key={reveal.at} className={cn("rounded-lg p-2 ring-1 ring-inset", intel >= reveal.at ? "bg-white/[0.025] ring-white/6" : "bg-black/15 ring-white/4 opacity-45")}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-[9px] font-black text-paper/75">{reveal.label}</p>
                <span className="text-[8px] font-black text-paper/30">{reveal.at}%</span>
              </div>
              <p className="mt-1 text-[8.5px] leading-relaxed text-paper/45">{intel >= reveal.at ? reveal.detail : "CLASSIFIED"}</p>
            </div>
          ))}
        </div>
      </section>

      {showAssociates && (
        <section className="mt-3 rounded-xl bg-black/20 p-3 ring-1 ring-white/6">
          <p className="text-[8px] font-black tracking-[0.18em] text-paper/45">KNOWN CRIMES</p>
          <div className="mt-2 space-y-1">
            {target.knownCrimes.map((crime) => <p key={crime} className="text-[9px] text-paper/55">• {crime}</p>)}
          </div>
        </section>
      )}

      {showCombat && (
        <section className="mt-3 rounded-xl bg-vermil/[0.06] p-3 ring-1 ring-vermil/15">
          <p className="text-[8px] font-black tracking-[0.18em] text-vermil/80">COMBAT WARNING</p>
          <div className="mt-2 space-y-1.5">
            {target.bossMechanics.map((mechanic) => <p key={mechanic} className="text-[9px] leading-relaxed text-paper/65">• {mechanic}</p>)}
          </div>
          {showDossier && <p className="mt-2 text-[8.5px] font-bold text-paper/40">Specialist focus: {target.focus.map((x) => x.toUpperCase()).join(" · ")}</p>}
        </section>
      )}

      <div className="mt-3 grid grid-cols-2 gap-2">
        <button disabled={intel <= 0 || ["captured", "killed", "resolved"].includes(progress.status)} className="rounded-xl bg-[#355f8c] px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">GATHER INTEL</button>
        <button disabled={!progress.locationKnown || ["captured", "killed", "resolved"].includes(progress.status)} className="rounded-xl bg-vermil px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">PREPARE HUNT</button>
      </div>
      <p className="mt-1.5 text-center text-[7.5px] font-bold text-paper/25">Buttons are staged for the mission/hunt implementation pass.</p>
    </div>
  );
}

export default function BingoBookScreen({ s, onChanged }: { s: GameState; onChanged: () => void }) {
  const [view, setView] = useState<View>("active");
  const [selected, setSelected] = useState<string | null>(null);
  const bingo = ensureBingoState(s);

  useEffect(() => {
    const revealed = refreshPendingMissingNin(s);
    if (revealed.length) onChanged();
  }, [s.day]); // eslint-disable-line react-hooks/exhaustive-deps

  const visibleTargets = useMemo(() => BINGO_TARGETS.filter((target) => {
    const p = bingo.targets[target.id];
    if (!p) return false;
    if (view === "active") return ["identified", "located", "active_hunt", "escaped"].includes(p.status);
    if (view === "rumours") return ["unknown", "rumoured"].includes(p.status) && p.intel > 0;
    if (view === "captured") return p.status === "captured";
    if (view === "resolved") return ["killed", "recruited", "resolved"].includes(p.status);
    return false;
  }), [bingo.targets, view]);

  useEffect(() => {
    if (!selected && visibleTargets.length) setSelected(visibleTargets[0].id);
    if (selected && !visibleTargets.some((x) => x.id === selected) && visibleTargets.length) setSelected(visibleTargets[0].id);
  }, [selected, visibleTargets]);

  if (!bingo.unlocked) {
    return (
      <div className="grid h-full min-h-0 place-items-center overflow-y-auto rounded-2xl bg-[#10121d]/95 p-5 ring-1 ring-white/8">
        <div className="max-w-md text-center">
          <div className="mx-auto grid h-20 w-20 place-items-center rounded-2xl bg-black/30 font-display text-4xl font-black text-paper/20 ring-1 ring-white/8">帳</div>
          <h2 className="mt-4 font-display text-xl font-black text-paper">BINGO BOOK LOCKED</h2>
          <p className="mt-2 text-[10px] leading-relaxed text-paper/50">The village is not yet trusted with the most dangerous missing-nin contracts.</p>
          <div className="mt-4 rounded-xl bg-gold/[0.06] p-3 ring-1 ring-gold/15">
            <p className="text-[9px] font-black text-gold">UNLOCK CONDITION</p>
            <p className="mt-1 text-[10px] text-paper/60">Produce your first Kage-level ninja.</p>
          </div>
        </div>
      </div>
    );
  }

  const selectedTarget = selected ? BINGO_TARGETS.find((x) => x.id === selected) ?? null : null;
  const selectedProgress = selectedTarget ? bingo.targets[selectedTarget.id] : null;

  const views: { id: View; label: string }[] = [
    { id: "active", label: "ACTIVE" },
    { id: "rumours", label: "RUMOURS" },
    { id: "captured", label: "CAPTURED" },
    { id: "resolved", label: "RESOLVED" },
    { id: "organisations", label: "ORGS" },
    { id: "black", label: "BLACK BOOK" },
  ];

  return (
    <div className="flex h-full min-h-0 flex-col rounded-2xl bg-[#0f111c]/95 p-2 ring-1 ring-white/8">
      <div className="flex items-center justify-between gap-2 px-1 pb-2">
        <div>
          <p className="font-display text-[15px] font-black text-paper">BINGO BOOK</p>
          <p className="text-[8px] font-bold tracking-[0.16em] text-paper/35">MISSING-NIN HUNTER DOSSIERS</p>
        </div>
        <div className="text-right">
          <p className="text-[8px] font-black text-gold">3 ACTIVE PROTOTYPES</p>
          <p className="text-[7.5px] text-paper/30">80-target roster pipeline</p>
        </div>
      </div>

      <div className="mb-2 flex gap-1 overflow-x-auto pb-1">
        {views.map((item) => (
          <button key={item.id} type="button" onClick={() => { setView(item.id); setSelected(null); }} className={cn("shrink-0 rounded-lg px-2 py-1.5 text-[8px] font-black tracking-wider ring-1", view === item.id ? "bg-gold text-[#211b13] ring-gold" : "bg-black/25 text-paper/45 ring-white/7")}>{item.label}</button>
        ))}
      </div>

      {view === "organisations" ? (
        <div className="min-h-0 flex-1 overflow-y-auto rounded-xl bg-black/15 p-2 ring-1 ring-white/5">
          <div className="grid gap-2 sm:grid-cols-2">
            {BINGO_ORGANISATIONS.map((org) => {
              const known = bingo.organisationsKnown.includes(org.id);
              return (
                <div key={org.id} className={cn("rounded-xl p-3 ring-1 ring-inset", known ? "bg-white/[0.025] ring-white/7" : "bg-black/25 ring-white/4 opacity-55")}>
                  <div className="flex items-center justify-between gap-2"><p className="text-[10px] font-black text-paper">{known ? org.name : "UNKNOWN ORGANISATION"}</p><span className="text-[8px] font-black text-paper/30">{known ? `${org.members} MEMBERS` : "???"}</span></div>
                  <p className="mt-2 text-[9px] leading-relaxed text-paper/45">{known ? org.description : "Resolve connected dossiers and interrogate captured targets to expose this network."}</p>
                </div>
              );
            })}
          </div>
        </div>
      ) : view === "black" ? (
        <div className="grid min-h-0 flex-1 place-items-center rounded-xl bg-black/30 p-5 ring-1 ring-white/5">
          <div className="max-w-sm text-center">
            <p className="font-display text-2xl font-black text-gold">BLACK BOOK</p>
            <p className="mt-2 text-[10px] leading-relaxed text-paper/45">Eight Kage-class superboss dossiers remain classified until the village proves itself against the S-rank network.</p>
            <p className="mt-3 text-[9px] font-black text-vermil">{bingo.blackBookUnlocked ? "CLASSIFICATION LIFTED — roster authoring pending" : "CLASSIFIED"}</p>
          </div>
        </div>
      ) : (
        <div className="grid min-h-0 flex-1 gap-2 lg:grid-cols-[320px_1fr]">
          <div className="min-h-0 space-y-2 overflow-y-auto rounded-xl bg-black/15 p-2 ring-1 ring-white/5">
            {visibleTargets.length ? visibleTargets.map((target) => (
              <TargetCard key={target.id} target={target} progress={bingo.targets[target.id]} selected={selected === target.id} onSelect={() => setSelected(target.id)} />
            )) : (
              <div className="rounded-xl bg-black/20 p-4 text-center ring-1 ring-white/5">
                <p className="text-[10px] font-black text-paper/45">NO DOSSIERS HERE</p>
                <p className="mt-1 text-[8.5px] text-paper/30">Progress investigations and hunts to populate this section.</p>
              </div>
            )}
            {view === "active" && bingo.dynamicTargets.map((target) => (
              <div key={target.id} className="rounded-xl bg-vermil/[0.05] p-3 ring-1 ring-vermil/15">
                <div className="flex items-center justify-between gap-2"><p className="text-[10px] font-black text-paper">{target.name} — {target.epithet}</p><span className="text-[8px] font-black text-vermil">{target.threat}</span></div>
                <p className="mt-1 text-[8.5px] text-paper/45">Former Shadow Village ninja · dynamic missing-nin</p>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/8"><div className="h-full bg-gold" style={{ width: `${target.intel}%` }} /></div>
                <p className="mt-1 text-[8px] font-bold text-paper/35">INTEL {target.intel}% · ALIVE {target.bountyAlive.toLocaleString()} 両</p>
              </div>
            ))}
          </div>
          <div className="min-h-0">
            {selectedTarget && selectedProgress ? <Dossier target={selectedTarget} progress={selectedProgress} /> : <div className="grid h-full place-items-center rounded-xl bg-black/15 text-[9px] font-bold text-paper/30 ring-1 ring-white/5">SELECT A DOSSIER</div>}
          </div>
        </div>
      )}
    </div>
  );
}
