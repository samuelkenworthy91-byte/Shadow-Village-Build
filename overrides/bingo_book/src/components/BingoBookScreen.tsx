import { useEffect, useMemo, useState } from "react";
import type { GameState, Ninja } from "../game/types";
import {
  BINGO_ORGANISATIONS,
  BINGO_TARGETS,
  ensureBingoState,
  intelBand,
  refreshPendingMissingNin,
  type BingoTargetDef,
  type BingoTargetProgress,
} from "../game/bingo";
import {
  abandonBingoHunt,
  activeBingoHunt,
  currentHuntEvent,
  huntEventCount,
  huntReadyForBoss,
  queueBingoIntelMission,
  queuedIntelMission,
  resolveCurrentHuntEvent,
  startBingoHunt,
  syncHuntIntelToDossier,
} from "../game/bingoHunt";
import type { HuntBiome } from "../game/huntEvents";
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

const BIOMES: { id: HuntBiome; label: string }[] = [
  { id: "forest", label: "Forest" },
  { id: "mountain", label: "Mountain" },
  { id: "river", label: "River" },
  { id: "urban", label: "Settlement" },
  { id: "desert", label: "Drylands" },
  { id: "marsh", label: "Marsh" },
  { id: "ruins", label: "Ruins" },
  { id: "road", label: "Trade Road" },
];

function intelLabel(value: number): string {
  return intelBand(value).replace(/^./, (x) => x.toUpperCase());
}

function TargetCard({ target, progress, selected, onSelect }: { target: BingoTargetDef; progress: BingoTargetProgress; selected: boolean; onSelect: () => void }) {
  const identified = progress.intel >= 20 || progress.status !== "unknown";
  return (
    <button type="button" onClick={onSelect} className={cn("w-full rounded-xl bg-black/20 p-2 text-left ring-1 ring-inset transition", selected ? "ring-gold/55 bg-gold/[0.06]" : "ring-white/7 hover:bg-white/[0.03]")}>
      <div className="flex items-start gap-2">
        <div className="grid h-14 w-12 shrink-0 place-items-end overflow-hidden rounded-lg bg-[#0b0c15] ring-1 ring-white/8">
          {identified ? <img src={target.sprite} alt="" className="max-h-full max-w-full object-contain" onError={(e) => { e.currentTarget.style.display = "none"; }} draggable={false} /> : <span className="mb-2 font-display text-xl font-black text-paper/15">?</span>}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2"><p className="truncate text-[11px] font-black text-paper">{identified ? `${target.name} — ${target.epithet}` : "Unknown Missing-nin"}</p><span className={cn("shrink-0 rounded px-1.5 py-0.5 text-[8px] font-black ring-1", threatClass[target.threat])}>{target.threat}</span></div>
          <p className="mt-1 text-[8.5px] font-bold uppercase tracking-[0.14em] text-paper/35">{progress.status.replaceAll("_", " ")}</p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/8"><div className="h-full rounded-full bg-gold transition-all" style={{ width: `${Math.max(2, progress.intel)}%` }} /></div>
          <div className="mt-1 flex items-center justify-between text-[8px] font-bold text-paper/40"><span>INTEL {progress.intel}%</span><span>{intelLabel(progress.intel)}</span></div>
        </div>
      </div>
    </button>
  );
}

function HunterRow({ n, selected, disabled, onToggle }: { n: Ninja; selected: boolean; disabled: boolean; onToggle: () => void }) {
  return (
    <button type="button" disabled={disabled && !selected} onClick={onToggle} className={cn("flex w-full items-center gap-2 rounded-xl p-2 text-left ring-1 transition", selected ? "bg-gold/10 ring-gold/40" : "bg-black/20 ring-white/7", disabled && !selected && "opacity-35")}>
      <div className="grid h-9 w-9 place-items-center rounded-lg bg-black/30 font-display text-[10px] font-black text-paper/60 ring-1 ring-white/7">{n.rank.slice(0, 2).toUpperCase()}</div>
      <div className="min-w-0 flex-1"><p className="truncate text-[10px] font-black text-paper">{n.name}</p><p className="text-[8px] font-bold text-paper/35">Lv {n.level} · {n.nature.toUpperCase()} · POT {n.pot}★</p></div>
      <span className={cn("rounded px-2 py-1 text-[8px] font-black", selected ? "bg-gold text-[#241d12]" : "bg-white/5 text-paper/35")}>{selected ? "SELECTED" : "ADD"}</span>
    </button>
  );
}

function HuntPrep({ s, target, onClose, onChanged }: { s: GameState; target: BingoTargetDef; onClose: () => void; onChanged: () => void }) {
  const [selected, setSelected] = useState<number[]>([]);
  const [biome, setBiome] = useState<HuntBiome>("forest");
  const [error, setError] = useState<string | null>(null);
  const ready = s.ninjas.filter((n) => n.status === "ready").sort((a, b) => b.level - a.level);
  const toggle = (id: number) => setSelected((cur) => cur.includes(id) ? cur.filter((x) => x !== id) : cur.length < 3 ? [...cur, id] : cur);
  const begin = () => {
    const result = startBingoHunt(s, target.id, selected, biome);
    if (!result.ok) { setError(result.error ?? "Unable to start hunt."); return; }
    onChanged();
    onClose();
  };
  return (
    <div className="fixed inset-0 z-[150] grid place-items-center bg-black/80 p-3 backdrop-blur-sm">
      <div className="flex max-h-[92vh] w-full max-w-xl flex-col rounded-2xl bg-[#151724] p-3 ring-1 ring-vermil/30 shadow-2xl">
        <div className="flex items-start justify-between gap-3"><div><p className="text-[8px] font-black tracking-[0.18em] text-vermil">PREPARE BINGO HUNT</p><h3 className="mt-1 font-display text-lg font-black text-paper">{target.name} — {target.epithet}</h3><p className="mt-1 text-[9px] text-paper/45">Choose exactly three active ninjas. HP and chakra will carry through every hunt stage.</p></div><button type="button" onClick={onClose} className="rounded-lg bg-black/30 px-2 py-1 text-[9px] font-black text-paper/50 ring-1 ring-white/8">CLOSE</button></div>
        <div className="mt-3 rounded-xl bg-black/20 p-2 ring-1 ring-white/6"><div className="flex items-center justify-between"><p className="text-[8px] font-black text-paper/40">HUNT TERRAIN</p><p className="text-[8px] font-black text-gold">{huntEventCount(target)} EVENT STAGES</p></div><div className="mt-2 flex gap-1 overflow-x-auto pb-1">{BIOMES.map((b) => <button key={b.id} type="button" onClick={() => setBiome(b.id)} className={cn("shrink-0 rounded-lg px-2 py-1.5 text-[8px] font-black ring-1", biome === b.id ? "bg-[#4f6f45] text-white ring-[#6b9160]" : "bg-black/25 text-paper/40 ring-white/7")}>{b.label}</button>)}</div></div>
        <div className="mt-3 flex items-center justify-between"><p className="text-[8px] font-black tracking-wider text-paper/45">HUNTER CELL</p><span className={cn("rounded px-2 py-1 text-[8px] font-black", selected.length === 3 ? "bg-jade/15 text-jade" : "bg-black/25 text-paper/35")}>{selected.length}/3</span></div>
        <div className="mt-2 min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1">{ready.map((n) => <HunterRow key={n.id} n={n} selected={selected.includes(n.id)} disabled={selected.length >= 3} onToggle={() => toggle(n.id)} />)}</div>
        {error && <p className="mt-2 rounded-lg bg-vermil/10 p-2 text-[9px] font-bold text-vermil ring-1 ring-vermil/20">{error}</p>}
        <div className="mt-3 rounded-xl bg-vermil/[0.05] p-2 text-[8.5px] leading-relaxed text-paper/50 ring-1 ring-vermil/15">Bingo hunts use normal lethal combat rules. Hunt events cannot directly kill a ninja, but can leave them at 10% HP before a fight.</div>
        <button type="button" disabled={selected.length !== 3} onClick={begin} className="mt-3 rounded-xl bg-vermil px-3 py-3 text-[10px] font-black tracking-wider text-white disabled:opacity-30">BEGIN HUNT</button>
      </div>
    </div>
  );
}

function ActiveHuntPanel({ s, onChanged }: { s: GameState; onChanged: () => void }) {
  const run = activeBingoHunt(s);
  const [lastResult, setLastResult] = useState<string | null>(null);
  if (!run) return null;
  const target = BINGO_TARGETS.find((x) => x.id === run.targetId);
  if (!target) return null;
  const event = currentHuntEvent(s);
  const readyForBoss = huntReadyForBoss(s);
  const completeEvent = (choice = 0) => {
    const result = resolveCurrentHuntEvent(s, choice);
    if (result.ok) {
      syncHuntIntelToDossier(s);
      setLastResult(`${result.success === true ? "SUCCESS — " : result.success === false ? "FAILED CHECK — " : ""}${result.result ?? "The hunt continues."}`);
      onChanged();
    }
  };
  const abandon = () => {
    if (!window.confirm("Abandon this hunt? The target's exact location will be lost, although most intelligence is retained.")) return;
    if (abandonBingoHunt(s)) onChanged();
  };
  return (
    <div className="mb-2 rounded-2xl bg-vermil/[0.055] p-3 ring-1 ring-vermil/20">
      <div className="flex items-start justify-between gap-2"><div><p className="text-[8px] font-black tracking-[0.18em] text-vermil">ACTIVE HUNT</p><h3 className="mt-1 font-display text-base font-black text-paper">{target.name} — {target.epithet}</h3><p className="text-[8.5px] text-paper/40">Stage {Math.min(run.stage + 1, huntEventCount(target))}/{huntEventCount(target)} · {run.biome.toUpperCase()} · dossier {run.intel}%</p></div><button type="button" onClick={abandon} className="rounded-lg bg-black/30 px-2 py-1.5 text-[8px] font-black text-vermil ring-1 ring-vermil/15">ABANDON</button></div>
      <div className="mt-2 grid grid-cols-3 gap-1.5">{run.members.map((member) => { const n = s.ninjas.find((x) => x.id === member.ninjaId); return <div key={member.ninjaId} className="rounded-xl bg-black/25 p-2 ring-1 ring-white/6"><p className="truncate text-[8.5px] font-black text-paper">{n?.name.split(" ")[0] ?? "Hunter"}</p><div className="mt-1 flex items-center justify-between text-[7px] font-bold text-paper/35"><span>HP</span><span>{Math.round(member.hpRatio * 100)}%</span></div><div className="mt-0.5 h-1.5 overflow-hidden rounded bg-white/8"><div className={cn("h-full", member.hpRatio <= .25 ? "bg-vermil" : "bg-jade")} style={{ width: `${member.hpRatio * 100}%` }} /></div><div className="mt-1 flex items-center justify-between text-[7px] font-bold text-paper/35"><span>CP</span><span>{Math.round(member.chakraRatio * 100)}%</span></div><div className="mt-0.5 h-1.5 overflow-hidden rounded bg-white/8"><div className="h-full bg-[#5ba8dd]" style={{ width: `${member.chakraRatio * 100}%` }} /></div>{member.statuses.length > 0 && <p className="mt-1 truncate text-[7px] font-black text-vermil">{member.statuses.join(", ")}</p>}</div>; })}</div>
      {lastResult && <p className="mt-2 rounded-lg bg-black/20 p-2 text-[8.5px] font-bold text-paper/55 ring-1 ring-white/6">{lastResult}</p>}
      {!readyForBoss && event && <div className="mt-2 rounded-xl bg-[#151724] p-3 ring-1 ring-white/8"><div className="flex items-center justify-between gap-2"><p className="text-[10px] font-black text-paper">{event.title}</p><span className={cn("rounded px-1.5 py-0.5 text-[7px] font-black uppercase", event.tone === "positive" ? "bg-jade/10 text-jade" : event.tone === "negative" ? "bg-vermil/10 text-vermil" : "bg-gold/10 text-gold")}>{event.tone}</span></div><p className="mt-1.5 text-[9px] leading-relaxed text-paper/50">{event.blurb}</p><div className="mt-3 space-y-1.5">{event.check ? <button type="button" onClick={() => completeEvent(0)} className="w-full rounded-lg bg-gold px-2 py-2 text-[8.5px] font-black text-[#251e13]">{event.check.skill.toUpperCase()} CHECK · DIFFICULTY {event.check.difficulty}</button> : event.choices?.length ? event.choices.map((choice, index) => <button key={choice.label} type="button" onClick={() => completeEvent(index)} className="w-full rounded-lg bg-black/30 px-2 py-2 text-left text-[8.5px] font-black text-paper/65 ring-1 ring-white/8"><span className="text-gold">{choice.label}</span><span className="ml-1 font-normal text-paper/35">— {choice.result}</span></button>) : <button type="button" onClick={() => completeEvent(0)} className="w-full rounded-lg bg-gold px-2 py-2 text-[8.5px] font-black text-[#251e13]">{event.effect?.label ?? "CONTINUE"}</button>}</div></div>}
      {readyForBoss && <div className="mt-2 rounded-xl bg-black/30 p-3 text-center ring-1 ring-gold/20"><p className="font-display text-sm font-black text-gold">TARGET CONTACT</p><p className="mt-1 text-[9px] leading-relaxed text-paper/50">The pursuit stages are complete. Current HP, chakra, statuses, ambush rounds and capture modifiers are preserved for the target battle.</p><button type="button" disabled className="mt-2 rounded-lg bg-vermil px-3 py-2 text-[9px] font-black text-white opacity-50">BOSS BATTLE · NEXT IMPLEMENTATION PASS</button></div>}
    </div>
  );
}

function Dossier({ target, progress, s, onChanged, onPrepare }: { target: BingoTargetDef; progress: BingoTargetProgress; s: GameState; onChanged: () => void; onPrepare: () => void }) {
  const intel = progress.intel;
  const showIdentity = intel >= 20;
  const showAssociates = intel >= 40;
  const showCombat = intel >= 60;
  const showDossier = intel >= 80;
  const queued = queuedIntelMission(s, target.id);
  const resolved = ["captured", "killed", "resolved", "recruited"].includes(progress.status);
  const gather = () => {
    const result = queueBingoIntelMission(s, target.id);
    if (!result.ok) { window.alert(result.error ?? "Unable to create intelligence operation."); return; }
    onChanged();
  };
  return (
    <div className="h-full overflow-y-auto rounded-2xl bg-[#11131f]/95 p-3 ring-1 ring-white/8">
      <div className="flex items-start gap-3"><div className="grid h-28 w-24 shrink-0 place-items-end overflow-hidden rounded-xl bg-black/35 ring-1 ring-white/8">{showIdentity ? <img src={target.sprite} alt="" className="max-h-full max-w-full object-contain" onError={(e) => { e.currentTarget.style.display = "none"; }} draggable={false} /> : <span className="mb-7 font-display text-4xl font-black text-paper/10">?</span>}</div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className={cn("rounded px-2 py-1 text-[9px] font-black ring-1", threatClass[target.threat])}>{target.threat} THREAT</span><span className="rounded bg-black/30 px-2 py-1 text-[8px] font-black text-paper/45 ring-1 ring-white/7">INTEL {intel}%</span></div><h2 className="mt-2 font-display text-xl font-black text-paper">{showIdentity ? target.name : "IDENTITY UNKNOWN"}</h2><p className="text-[11px] font-black tracking-wide text-vermil/85">{showIdentity ? target.epithet : "BINGO BOOK TARGET"}</p><p className="mt-2 text-[9.5px] leading-relaxed text-paper/55">{intel > 0 ? target.summary : "Gather intelligence missions to build a usable dossier before committing a hunter team."}</p></div></div>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4"><div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">LEVEL</p><p className="mt-1 text-[11px] font-black text-paper">{showIdentity ? `~${target.level}` : "???"}</p></div><div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">ELEMENTS</p><p className="mt-1 text-[10px] font-black text-paper">{showIdentity ? target.elements.join(" / ") : "Unknown"}</p></div><div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">DEAD</p><p className="mt-1 text-[10px] font-black text-gold">{showIdentity ? `${target.bountyDead.toLocaleString()} 両` : "???"}</p></div><div className="rounded-lg bg-black/25 p-2 ring-1 ring-white/6"><p className="text-[7px] font-black tracking-wider text-paper/30">ALIVE</p><p className="mt-1 text-[10px] font-black text-jade">{showIdentity ? `${target.bountyAlive.toLocaleString()} 両` : "???"}</p></div></div>
      <section className="mt-3 rounded-xl bg-black/20 p-3 ring-1 ring-white/6"><p className="text-[8px] font-black tracking-[0.18em] text-gold/75">INTELLIGENCE FILE</p><div className="mt-2 space-y-2">{target.intel.map((reveal) => <div key={reveal.at} className={cn("rounded-lg p-2 ring-1 ring-inset", intel >= reveal.at ? "bg-white/[0.025] ring-white/6" : "bg-black/15 ring-white/4 opacity-45")}><div className="flex items-center justify-between gap-2"><p className="text-[9px] font-black text-paper/75">{reveal.label}</p><span className="text-[8px] font-black text-paper/30">{reveal.at}%</span></div><p className="mt-1 text-[8.5px] leading-relaxed text-paper/45">{intel >= reveal.at ? reveal.detail : "CLASSIFIED"}</p></div>)}</div></section>
      {showAssociates && <section className="mt-3 rounded-xl bg-black/20 p-3 ring-1 ring-white/6"><p className="text-[8px] font-black tracking-[0.18em] text-paper/45">KNOWN CRIMES</p><div className="mt-2 space-y-1">{target.knownCrimes.map((crime) => <p key={crime} className="text-[9px] text-paper/55">• {crime}</p>)}</div></section>}
      {showCombat && <section className="mt-3 rounded-xl bg-vermil/[0.06] p-3 ring-1 ring-vermil/15"><p className="text-[8px] font-black tracking-[0.18em] text-vermil/80">COMBAT WARNING</p><div className="mt-2 space-y-1.5">{target.bossMechanics.map((mechanic) => <p key={mechanic} className="text-[9px] leading-relaxed text-paper/65">• {mechanic}</p>)}</div>{showDossier && <p className="mt-2 text-[8.5px] font-bold text-paper/40">Specialist focus: {target.focus.map((x) => x.toUpperCase()).join(" · ")}</p>}</section>}
      <div className="mt-3 grid grid-cols-2 gap-2"><button disabled={resolved || !!queued} onClick={gather} className="rounded-xl bg-[#355f8c] px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">{queued ? queued.squad.length ? "INTEL TEAM OUT" : "INTEL ON BOARD" : "GATHER INTEL"}</button><button disabled={!progress.locationKnown || resolved || !!activeBingoHunt(s)} onClick={onPrepare} className="rounded-xl bg-vermil px-3 py-2.5 text-[9px] font-black tracking-wider text-white disabled:opacity-35">PREPARE HUNT</button></div>
      {queued && <p className="mt-2 rounded-lg bg-[#355f8c]/10 p-2 text-[8.5px] font-bold text-[#86bce8] ring-1 ring-[#355f8c]/20">{queued.squad.length ? "Intelligence team deployed. Results arrive when the mission ends." : "A target-specific intelligence operation is waiting in Mission Board → Bingo Intelligence."}</p>}
    </div>
  );
}

export default function BingoBookScreen({ s, onChanged }: { s: GameState; onChanged: () => void }) {
  const [view, setView] = useState<View>("active");
  const [selected, setSelected] = useState<string | null>(null);
  const [prepTarget, setPrepTarget] = useState<BingoTargetDef | null>(null);
  const bingo = ensureBingoState(s);
  useEffect(() => { const revealed = refreshPendingMissingNin(s); if (revealed.length) onChanged(); }, [s.day]);

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

  if (!bingo.unlocked) return <div className="grid h-full min-h-0 place-items-center overflow-y-auto rounded-2xl bg-[#10121d]/95 p-5 ring-1 ring-white/8"><div className="max-w-md text-center"><div className="mx-auto grid h-20 w-20 place-items-center rounded-2xl bg-black/30 font-display text-4xl font-black text-paper/20 ring-1 ring-white/8">帳</div><h2 className="mt-4 font-display text-xl font-black text-paper">BINGO BOOK LOCKED</h2><p className="mt-2 text-[10px] leading-relaxed text-paper/50">The village is not yet trusted with the most dangerous missing-nin contracts.</p><div className="mt-4 rounded-xl bg-gold/[0.06] p-3 ring-1 ring-gold/15"><p className="text-[9px] font-black text-gold">UNLOCK CONDITION</p><p className="mt-1 text-[10px] text-paper/60">Produce your first Kage-level ninja.</p></div></div></div>;

  const selectedTarget = selected ? BINGO_TARGETS.find((x) => x.id === selected) ?? null : null;
  const selectedProgress = selectedTarget ? bingo.targets[selectedTarget.id] : null;
  const views: { id: View; label: string }[] = [{ id: "active", label: "ACTIVE" }, { id: "rumours", label: "RUMOURS" }, { id: "captured", label: "CAPTURED" }, { id: "resolved", label: "RESOLVED" }, { id: "organisations", label: "ORGS" }, { id: "black", label: "BLACK BOOK" }];

  return (
    <div className="flex h-full min-h-0 flex-col rounded-2xl bg-[#0f111c]/95 p-2 ring-1 ring-white/8">
      {prepTarget && <HuntPrep s={s} target={prepTarget} onClose={() => setPrepTarget(null)} onChanged={onChanged} />}
      <ActiveHuntPanel s={s} onChanged={onChanged} />
      <div className="flex items-center justify-between gap-2 px-1 pb-2"><div><p className="font-display text-[15px] font-black text-paper">BINGO BOOK</p><p className="text-[8px] font-bold tracking-[0.16em] text-paper/35">MISSING-NIN HUNTER DOSSIERS</p></div><div className="text-right"><p className="text-[8px] font-black text-gold">INTEL + HUNT FRAMEWORK LIVE</p><p className="text-[7.5px] text-paper/30">3 target prototypes · 80-target pipeline</p></div></div>
      <div className="mb-2 flex gap-1 overflow-x-auto pb-1">{views.map((item) => <button key={item.id} type="button" onClick={() => { setView(item.id); setSelected(null); }} className={cn("shrink-0 rounded-lg px-2 py-1.5 text-[8px] font-black tracking-wider ring-1", view === item.id ? "bg-gold text-[#211b13] ring-gold" : "bg-black/25 text-paper/45 ring-white/7")}>{item.label}</button>)}</div>
      {view === "organisations" ? <div className="min-h-0 flex-1 overflow-y-auto rounded-xl bg-black/15 p-2 ring-1 ring-white/5"><div className="grid gap-2 sm:grid-cols-2">{BINGO_ORGANISATIONS.map((org) => { const known = bingo.organisationsKnown.includes(org.id); return <div key={org.id} className={cn("rounded-xl p-3 ring-1 ring-inset", known ? "bg-white/[0.025] ring-white/7" : "bg-black/25 ring-white/4 opacity-55")}><div className="flex items-center justify-between gap-2"><p className="text-[10px] font-black text-paper">{known ? org.name : "UNKNOWN ORGANISATION"}</p><span className="text-[8px] font-black text-paper/30">{known ? `${org.members} MEMBERS` : "???"}</span></div><p className="mt-2 text-[9px] leading-relaxed text-paper/45">{known ? org.description : "Resolve connected dossiers and interrogate captured targets to expose this network."}</p></div>; })}</div></div> : view === "black" ? <div className="grid min-h-0 flex-1 place-items-center rounded-xl bg-black/30 p-5 ring-1 ring-white/5"><div className="max-w-sm text-center"><p className="font-display text-2xl font-black text-gold">BLACK BOOK</p><p className="mt-2 text-[10px] leading-relaxed text-paper/45">Eight Kage-class superboss dossiers remain classified until the village proves itself against the S-rank network.</p><p className="mt-3 text-[9px] font-black text-vermil">{bingo.blackBookUnlocked ? "CLASSIFICATION LIFTED — roster authoring pending" : "CLASSIFIED"}</p></div></div> : <div className="grid min-h-0 flex-1 gap-2 lg:grid-cols-[320px_1fr]"><div className="min-h-0 space-y-2 overflow-y-auto rounded-xl bg-black/15 p-2 ring-1 ring-white/5">{visibleTargets.length ? visibleTargets.map((target) => <TargetCard key={target.id} target={target} progress={bingo.targets[target.id]} selected={selected === target.id} onSelect={() => setSelected(target.id)} />) : <div className="rounded-xl bg-black/20 p-4 text-center ring-1 ring-white/5"><p className="text-[10px] font-black text-paper/45">NO DOSSIERS HERE</p><p className="mt-1 text-[8.5px] text-paper/30">Progress investigations and hunts to populate this section.</p></div>}{view === "active" && bingo.dynamicTargets.map((target) => <div key={target.id} className="rounded-xl bg-vermil/[0.05] p-3 ring-1 ring-vermil/15"><div className="flex items-center justify-between gap-2"><p className="text-[10px] font-black text-paper">{target.name} — {target.epithet}</p><span className="text-[8px] font-black text-vermil">{target.threat}</span></div><p className="mt-1 text-[8.5px] text-paper/45">Former Shadow Village ninja · dynamic missing-nin</p><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/8"><div className="h-full bg-gold" style={{ width: `${target.intel}%` }} /></div><p className="mt-1 text-[8px] font-bold text-paper/35">INTEL {target.intel}% · ALIVE {target.bountyAlive.toLocaleString()} 両</p></div>)}</div><div className="min-h-0">{selectedTarget && selectedProgress ? <Dossier target={selectedTarget} progress={selectedProgress} s={s} onChanged={onChanged} onPrepare={() => setPrepTarget(selectedTarget)} /> : <div className="grid h-full place-items-center rounded-xl bg-black/15 text-[9px] font-bold text-paper/30 ring-1 ring-white/5">SELECT A DOSSIER</div>}</div></div>}
    </div>
  );
}
