import { useEffect, useMemo, useRef, useState } from "react";
import { BookOpen, Bookmark, ChevronLeft, ChevronRight, Crosshair, Search, ShieldAlert, X } from "lucide-react";
import type { GameState, Ninja } from "../game/types";
import {
  BINGO_ORGANISATIONS,
  BINGO_TARGETS,
  bingoUnreadCount,
  ensureBingoState,
  markBingoDiscoveriesSeen,
  refreshPendingMissingNin,
  type BingoDiscoveryKey,
  type BingoTargetDef,
  type BingoTargetProgress,
  type BingoThreat,
} from "../game/bingo";
import {
  abandonBingoHunt,
  activeBingoHunt,
  beginBingoBossBattle,
  bingoCaptureChance,
  currentHuntEvent,
  huntEventCount,
  huntReadyForBoss,
  interrogateBingoPrisoner,
  queueBingoIntelMission,
  queuedIntelMission,
  resolveBingoFate,
  resolveCurrentHuntEvent,
  startBingoHunt,
  syncHuntIntelToDossier,
} from "../game/bingoHunt";
import type { HuntBiome } from "../game/huntEvents";
import { bingoRecruitChance, recruitBingoPrisoner } from "../game/engine";
import { ninjaArtSrc } from "../game/ninjaArt";
import { cn } from "../utils/cn";
import { audio } from "../game/audio";

const BIOMES: { id: HuntBiome; label: string }[] = [
  { id: "forest", label: "Forest" }, { id: "mountain", label: "Mountain" }, { id: "river", label: "River" },
  { id: "urban", label: "Settlement" }, { id: "desert", label: "Drylands" }, { id: "marsh", label: "Marsh" },
  { id: "ruins", label: "Ruins" }, { id: "road", label: "Trade Road" },
];

const THREATS: BingoThreat[] = ["B", "A", "S", "S+", "SS", "BLACK"];
const RESOLVED = new Set(["captured", "killed", "recruited", "resolved"]);

type StaticPage =
  | { kind: "summary" }
  | { kind: "contents"; chunk: number }
  | { kind: "organisations" }
  | { kind: "black-divider" }
  | { kind: "target"; target: BingoTargetDef }
  | { kind: "dynamic-divider" }
  | { kind: "dynamic"; id: string };

function has(progress: BingoTargetProgress, key: BingoDiscoveryKey): boolean {
  return (progress.discoveries ?? []).includes(key);
}

function unseen(progress: BingoTargetProgress, key: BingoDiscoveryKey): boolean {
  return has(progress, key) && !(progress.seenDiscoveries ?? []).includes(key);
}

function paperLabel(key: BingoDiscoveryKey): string {
  const labels: Record<BingoDiscoveryKey, string> = {
    rumour: "FIELD RUMOUR", identity: "IDENTITY", portrait: "VISUAL ID", threat: "THREAT CLASS", level: "EST. LEVEL",
    elements: "CHAKRA NATURE", bounty_dead: "DEAD BOUNTY", bounty_alive: "LIVE BOUNTY", organisation: "AFFILIATION",
    crime_1: "KNOWN CRIME", crime_2: "KNOWN CRIME", crime_3: "KNOWN CRIME", focus: "SPECIALIST PROFILE",
    combat_1: "COMBAT WARNING", combat_2: "SECONDARY WARNING", escape: "ESCAPE BEHAVIOUR", capture: "CAPTURE FILE", full: "COMPLETE FILE",
  };
  return labels[key];
}

function threatInk(threat: BingoThreat): string {
  return threat === "BLACK" ? "#1d1712" : threat === "SS" ? "#8f2019" : threat === "S+" ? "#a33d20" : threat === "S" ? "#603e72" : threat === "A" ? "#31577d" : "#396143";
}

function targetTitle(target: BingoTargetDef, progress: BingoTargetProgress): string {
  return has(progress, "identity") ? `${target.name} — ${target.epithet}` : "UNKNOWN MISSING-NIN";
}

function statusStamp(progress: BingoTargetProgress): string | null {
  if (progress.status === "killed") return "ELIMINATED";
  if (progress.status === "captured") return "CAPTURED";
  if (progress.status === "recruited") return "RECRUITED";
  if (progress.status === "resolved") return (progress.outcome ?? "RESOLVED").toUpperCase();
  return null;
}

function PaperFact({ label, value, fresh = false, warning = false }: { label: string; value: string; fresh?: boolean; warning?: boolean }) {
  return (
    <div className={cn("bb-note", fresh && "bb-note-new", warning && "bb-note-warning")}>
      <span>{label}</span>
      <strong>{value}</strong>
      {fresh && <em>NEW</em>}
    </div>
  );
}

function HunterRow({ n, selected, disabled, onToggle }: { n: Ninja; selected: boolean; disabled: boolean; onToggle: () => void }) {
  return (
    <button type="button" disabled={disabled && !selected} onClick={onToggle} className={cn("bb-hunter", selected && "bb-hunter-selected", disabled && !selected && "opacity-40")}>
      <div className="min-w-0 flex-1"><strong>{n.name}</strong><span>Lv {n.level} · {n.nature.toUpperCase()} · POT {n.pot}★</span></div>
      <b>{selected ? "SELECTED" : "ADD"}</b>
    </button>
  );
}

function HuntPrepModal({ s, target, onClose, onChanged }: { s: GameState; target: BingoTargetDef; onClose: () => void; onChanged: () => void }) {
  const [selected, setSelected] = useState<number[]>([]);
  const [biome, setBiome] = useState<HuntBiome>("forest");
  const [error, setError] = useState<string | null>(null);
  const ready = s.ninjas.filter((n) => n.status === "ready").sort((a, b) => b.level - a.level);
  const toggle = (id: number) => setSelected((cur) => cur.includes(id) ? cur.filter((x) => x !== id) : cur.length < 3 ? [...cur, id] : cur);
  const begin = () => {
    const result = startBingoHunt(s, target.id, selected, biome);
    if (!result.ok) { setError(result.error ?? "Unable to start hunt."); return; }
    audio.click();
    onChanged();
    onClose();
  };
  return (
    <div className="fixed inset-0 z-[220] grid place-items-center bg-black/80 p-3 backdrop-blur-sm">
      <div className="bb-paper-panel flex max-h-[92vh] w-full max-w-xl flex-col p-4 text-[#352719]">
        <div className="flex items-start justify-between gap-3 border-b border-[#654a2e]/25 pb-3">
          <div><p className="bb-kicker">HUNTER CELL ASSIGNMENT</p><h3 className="font-display text-lg font-black">{target.name} — {target.epithet}</h3><p className="mt-1 text-[10px] opacity-65">Choose exactly three active ninja. Damage and chakra loss persist through every hunt stage.</p></div>
          <button type="button" onClick={onClose} className="bb-ink-button">CLOSE</button>
        </div>
        <div className="mt-3"><p className="bb-kicker">TERRAIN</p><div className="mt-2 flex gap-1 overflow-x-auto pb-1">{BIOMES.map((b) => <button key={b.id} type="button" onClick={() => setBiome(b.id)} className={cn("bb-chip", biome === b.id && "bb-chip-selected")}>{b.label}</button>)}</div></div>
        <div className="mt-3 flex items-center justify-between"><p className="bb-kicker">ACTIVE HUNTERS</p><b className="text-xs">{selected.length}/3</b></div>
        <div className="mt-2 min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1">{ready.map((n) => <HunterRow key={n.id} n={n} selected={selected.includes(n.id)} disabled={selected.length >= 3} onToggle={() => toggle(n.id)} />)}</div>
        {error && <p className="mt-2 rounded border border-[#8a241d]/30 bg-[#8a241d]/8 p-2 text-[10px] font-bold text-[#8a241d]">{error}</p>}
        <p className="mt-3 text-[9px] leading-relaxed opacity-60">Hunt events cannot directly kill a ninja, but can reduce them to 10% HP. The target battle itself uses lethal combat rules.</p>
        <button type="button" disabled={selected.length !== 3} onClick={begin} className="bb-red-button mt-3 disabled:opacity-35">BEGIN HUNT · {huntEventCount(target)} STAGES</button>
      </div>
    </div>
  );
}

function HuntSlip({ s, target, onChanged }: { s: GameState; target: BingoTargetDef; onChanged: () => void }) {
  const run = activeBingoHunt(s);
  const [lastResult, setLastResult] = useState<string | null>(null);
  if (!run || run.targetId !== target.id) return null;
  const event = currentHuntEvent(s);
  const readyForBoss = huntReadyForBoss(s);
  const complete = (choice = 0) => {
    const result = resolveCurrentHuntEvent(s, choice);
    if (result.ok) {
      syncHuntIntelToDossier(s);
      setLastResult(`${result.success === true ? "SUCCESS — " : result.success === false ? "FAILED — " : ""}${result.result ?? "The pursuit continues."}`);
      onChanged();
    }
  };
  const abandon = () => {
    if (!window.confirm("Abandon this hunt? Exact location is lost, but most dossier intelligence remains.")) return;
    if (abandonBingoHunt(s)) onChanged();
  };
  return (
    <div className="bb-hunt-slip">
      <div className="flex items-start justify-between gap-2"><div><p className="bb-kicker text-[#8a241d]">ACTIVE HUNT · BOOKMARKED</p><p className="text-[10px] font-black">Stage {Math.min(run.stage + 1, huntEventCount(target))}/{huntEventCount(target)} · {run.biome.toUpperCase()}</p></div><button type="button" onClick={abandon} className="bb-ink-button text-[#8a241d]">ABANDON</button></div>
      <div className="mt-2 grid grid-cols-3 gap-1">{run.members.map((member) => { const n = s.ninjas.find((x) => x.id === member.ninjaId); return <div key={member.ninjaId} className="rounded border border-[#654a2e]/20 bg-[#fff7df]/55 p-1.5"><p className="truncate text-[8px] font-black">{n?.name.split(" ")[0] ?? "Hunter"}</p><p className="mt-0.5 text-[7px]">HP {Math.round(member.hpRatio * 100)}% · CP {Math.round(member.chakraRatio * 100)}%</p>{member.statuses.length > 0 && <p className="truncate text-[7px] font-bold text-[#8a241d]">{member.statuses.join(", ")}</p>}</div>; })}</div>
      {lastResult && <p className="mt-2 border-l-2 border-[#654a2e]/35 pl-2 text-[8.5px] italic opacity-70">{lastResult}</p>}
      {!readyForBoss && event && <div className="mt-2 border-t border-[#654a2e]/20 pt-2"><p className="text-[10px] font-black">{event.title}</p><p className="mt-1 text-[9px] leading-relaxed opacity-65">{event.blurb}</p><div className="mt-2 space-y-1">{event.check ? <button type="button" onClick={() => complete(0)} className="bb-gold-button w-full">{event.check.skill.toUpperCase()} CHECK · DIFFICULTY {event.check.difficulty}</button> : event.choices?.length ? event.choices.map((choice, index) => <button key={choice.label} type="button" onClick={() => complete(index)} className="bb-paper-choice"><strong>{choice.label}</strong><span>{choice.result}</span></button>) : <button type="button" onClick={() => complete(0)} className="bb-gold-button w-full">{event.effect?.label ?? "CONTINUE"}</button>}</div></div>}
      {readyForBoss && <div className="mt-2 border-t-2 border-[#8a241d]/25 pt-2 text-center"><p className="font-display text-sm font-black text-[#8a241d]">TARGET CONTACT</p><p className="mt-1 text-[8.5px] opacity-65">All hunt injuries, ambushes, statuses and capture modifiers carry into combat.</p><button type="button" onClick={() => { const r = beginBingoBossBattle(s); if (!r.ok) setLastResult(r.error ?? "Unable to begin battle."); else onChanged(); }} className="bb-red-button mt-2">BEGIN TARGET BATTLE</button></div>}
    </div>
  );
}

function TargetPage({ s, target, progress, pageNo, onChanged, onPrep }: { s: GameState; target: BingoTargetDef; progress: BingoTargetProgress; pageNo: number; onChanged: () => void; onPrep: () => void }) {
  const discovered = new Set(progress.discoveries ?? []);
  const queued = queuedIntelMission(s, target.id);
  const resolved = RESOLVED.has(progress.status);
  const captured = progress.status === "captured";
  const defeated = progress.status === "defeated";
  const stamp = statusStamp(progress);
  const captureChance = defeated ? bingoCaptureChance(s, target.id) : 0;
  const recruitChance = captured && target.recruitable ? bingoRecruitChance(s, target.id) : 0;
  const active = activeBingoHunt(s);
  const org = target.organisationId ? BINGO_ORGANISATIONS.find((x) => x.id === target.organisationId) : null;
  const gather = () => {
    const result = queueBingoIntelMission(s, target.id);
    if (!result.ok) { window.alert(result.error ?? "Unable to create intelligence operation."); return; }
    onChanged();
  };
  return (
    <article className={cn("bb-page bb-target-page", target.threat === "BLACK" && "bb-page-black")}>
      {active?.targetId === target.id && <span className="bb-bookmark"><Bookmark size={12} fill="currentColor" /> HUNT</span>}
      <div className="bb-page-number">{pageNo}</div>
      <header className="bb-dossier-head">
        <div className="bb-portrait-frame">
          {discovered.has("portrait") ? <img src={target.sprite} alt={target.name} draggable={false} /> : <div className="bb-silhouette">?</div>}
          <span style={{ background: threatInk(target.threat) }}>{discovered.has("threat") ? target.threat : "?"}</span>
        </div>
        <div className="min-w-0 flex-1"><p className="bb-kicker">MISSING-NIN DOSSIER · {String(BINGO_TARGETS.indexOf(target) + 1).padStart(3, "0")}</p><h2>{discovered.has("identity") ? target.name : "IDENTITY UNKNOWN"}</h2><h3>{discovered.has("identity") ? target.epithet : "FIELD DESIGNATION PENDING"}</h3><p className="bb-summary">{discovered.has("rumour") ? target.summary : "No reliable account has yet been committed to this page."}</p><div className="bb-intel-meter"><i style={{ width: `${Math.max(2, progress.intel)}%` }} /><span>INTEL {progress.intel}%</span></div></div>
      </header>

      <div className="bb-facts-grid">
        {has(progress, "level") ? <PaperFact label={paperLabel("level")} value={`~${target.level}`} fresh={unseen(progress, "level")} /> : <PaperFact label="LEVEL" value="???" />}
        {has(progress, "elements") ? <PaperFact label={paperLabel("elements")} value={target.elements.join(" / ")} fresh={unseen(progress, "elements")} /> : <PaperFact label="CHAKRA NATURE" value="UNKNOWN" />}
        {has(progress, "bounty_dead") ? <PaperFact label={paperLabel("bounty_dead")} value={`${target.bountyDead.toLocaleString()} 両`} fresh={unseen(progress, "bounty_dead")} /> : <PaperFact label="DEAD BOUNTY" value="CLASSIFIED" />}
        {has(progress, "bounty_alive") ? <PaperFact label={paperLabel("bounty_alive")} value={`${target.bountyAlive.toLocaleString()} 両`} fresh={unseen(progress, "bounty_alive")} /> : <PaperFact label="LIVE BOUNTY" value="CLASSIFIED" />}
      </div>

      <div className="bb-dossier-columns">
        <section>
          <p className="bb-section-title">FIELD NOTES</p>
          {has(progress, "organisation") && <PaperFact label={paperLabel("organisation")} value={org?.name ?? "Unaffiliated"} fresh={unseen(progress, "organisation")} />}
          {has(progress, "focus") && <PaperFact label={paperLabel("focus")} value={target.focus.map((x) => x.toUpperCase()).join(" · ")} fresh={unseen(progress, "focus")} />}
          {["crime_1", "crime_2", "crime_3"].map((key, i) => has(progress, key as BingoDiscoveryKey) && target.knownCrimes[i] ? <PaperFact key={key} label={paperLabel(key as BingoDiscoveryKey)} value={target.knownCrimes[i]} fresh={unseen(progress, key as BingoDiscoveryKey)} /> : null)}
          {!has(progress, "crime_1") && <p className="bb-redacted">████████████ · CRIMINAL RECORD SEALED</p>}
        </section>
        <section>
          <p className="bb-section-title">TACTICAL ANNOTATIONS</p>
          {has(progress, "combat_1") && target.bossMechanics[0] && <PaperFact label={paperLabel("combat_1")} value={target.bossMechanics[0]} fresh={unseen(progress, "combat_1")} warning />}
          {has(progress, "combat_2") && target.bossMechanics[1] && <PaperFact label={paperLabel("combat_2")} value={target.bossMechanics[1]} fresh={unseen(progress, "combat_2")} warning />}
          {has(progress, "escape") && <PaperFact label={paperLabel("escape")} value={target.fleeAtHp ? `Known to break contact below roughly ${Math.round(target.fleeAtHp * 100)}% health unless restrained.` : "No fixed retreat threshold confirmed; smoke seals and hunt events may still alter escape behaviour."} fresh={unseen(progress, "escape")} warning />}
          {has(progress, "capture") && <PaperFact label={paperLabel("capture")} value={`Base live restraint chance ${Math.round(target.captureBaseChance * 100)}%. Dossier intelligence and hunt events can improve it.`} fresh={unseen(progress, "capture")} />}
          {!has(progress, "combat_1") && <p className="bb-redacted">TACTICAL FILE █████████████████</p>}
        </section>
      </div>

      <HuntSlip s={s} target={target} onChanged={onChanged} />

      {defeated && <div className="bb-decision"><p className="bb-section-title">TARGET DEFEATED · AUTHORISE FATE</p><div className="grid grid-cols-2 gap-2"><button type="button" onClick={() => { if (!window.confirm(`Eliminate ${target.name}? This permanently resolves the dossier.`)) return; const r = resolveBingoFate(s, target.id, "kill"); if (r.ok) onChanged(); else window.alert(r.error); }} className="bb-red-button">ELIMINATE · {target.bountyDead.toLocaleString()}</button><button type="button" onClick={() => { if (!window.confirm(`Attempt live capture? ${Math.round(captureChance * 100)}% current chance. Failure lets the target escape.`)) return; const r = resolveBingoFate(s, target.id, "capture"); window.alert(r.result ?? r.error ?? "Capture resolved."); if (r.ok) onChanged(); }} className="bb-gold-button">CAPTURE · {Math.round(captureChance * 100)}%</button></div></div>}

      {captured && <div className="bb-detention"><p className="bb-section-title">DETENTION ANNOTATION · SECURITY {ensureBingoState(s).detention.securityAlert}%</p><div className="grid grid-cols-2 gap-2"><button type="button" disabled={!!progress.interrogated} onClick={() => { const r = interrogateBingoPrisoner(s, target.id); window.alert(r.result ?? r.error ?? "Interrogation complete."); if (r.ok) onChanged(); }} className="bb-ink-button disabled:opacity-35">{progress.interrogated ? "INTERROGATED" : "INTERROGATE"}</button>{target.recruitable ? <button type="button" disabled={!progress.interrogated} onClick={() => { const r = recruitBingoPrisoner(s, target.id); window.alert(r.result ?? r.error ?? "Recruitment resolved."); if (r.ok) onChanged(); }} className="bb-gold-button disabled:opacity-35">RECRUIT · {Math.round(recruitChance * 100)}%</button> : <button type="button" disabled className="bb-ink-button opacity-40">WILL NOT DEFECT</button>}</div></div>}

      {!defeated && !captured && !resolved && active?.targetId !== target.id && <div className="bb-page-actions"><button type="button" disabled={!!queued} onClick={gather} className="bb-ink-button disabled:opacity-35">{queued ? queued.squad.length ? "INTEL TEAM DEPLOYED" : "INTEL MISSION QUEUED" : "GATHER INTELLIGENCE"}</button><button type="button" disabled={!progress.locationKnown || !!active} onClick={onPrep} className="bb-red-button disabled:opacity-35">PREPARE HUNT</button></div>}
      {queued && <p className="bb-pencil-note">A target-specific intelligence operation has been entered on the Mission Board.</p>}
      {stamp && <div className={cn("bb-stamp", `bb-stamp-${progress.status}`)}>{stamp}</div>}
    </article>
  );
}

function SummaryPage({ s, pageNo, onJumpTarget, onJumpContents }: { s: GameState; pageNo: number; onJumpTarget: (id: string) => void; onJumpContents: () => void }) {
  const bingo = ensureBingoState(s);
  const resolved = BINGO_TARGETS.filter((t) => RESOLVED.has(bingo.targets[t.id]?.status)).length;
  const killed = BINGO_TARGETS.filter((t) => bingo.targets[t.id]?.status === "killed").length;
  const captured = BINGO_TARGETS.filter((t) => bingo.targets[t.id]?.status === "captured").length;
  const recruited = BINGO_TARGETS.filter((t) => bingo.targets[t.id]?.status === "recruited").length;
  const active = activeBingoHunt(s);
  const activeTarget = active ? BINGO_TARGETS.find((t) => t.id === active.targetId) : null;
  const unread = bingoUnreadCount(s);
  return <article className="bb-page bb-summary-page"><div className="bb-page-number">{pageNo}</div><div className="bb-inside-seal">影</div><p className="bb-kicker">SHADOW VILLAGE · HUNTER-NIN ARCHIVE</p><h2 className="font-display text-3xl font-black tracking-[0.08em]">BINGO BOOK</h2><p className="mt-2 max-w-sm text-[11px] leading-relaxed opacity-65">Classified field dossiers for missing-nin considered dangerous to the village and its allies. Information is added as hunter cells confirm it.</p><div className="bb-ledger mt-5"><div><span>FILES RESOLVED</span><strong>{resolved}/80</strong></div><div><span>ELIMINATED</span><strong>{killed}</strong></div><div><span>CAPTURED</span><strong>{captured}</strong></div><div><span>RECRUITED</span><strong>{recruited}</strong></div></div>{unread > 0 && <button type="button" onClick={onJumpContents} className="bb-new-intel mt-4"><Search size={13} /> {unread} NEW DOSSIER {unread === 1 ? "ENTRY" : "ENTRIES"}</button>}{activeTarget && <button type="button" onClick={() => onJumpTarget(activeTarget.id)} className="bb-active-bookmark mt-4"><Bookmark size={14} fill="currentColor" /><span><small>ACTIVE HUNT</small><strong>{activeTarget.name} — {activeTarget.epithet}</strong></span><ChevronRight size={16} /></button>}<div className="mt-auto border-t border-[#654a2e]/20 pt-3 text-[9px] italic opacity-50">“A name written here is not a victory. It is a warning.”</div></article>;
}

function ContentsPage({ s, targets, chunk, pageNo, pageByTarget, onJumpTarget }: { s: GameState; targets: BingoTargetDef[]; chunk: number; pageNo: number; pageByTarget: Map<string, number>; onJumpTarget: (id: string) => void }) {
  const bingo = ensureBingoState(s);
  return <article className="bb-page"><div className="bb-page-number">{pageNo}</div><p className="bb-kicker">FIELD INDEX · VOLUME {chunk + 1}</p><h2 className="bb-page-title">DOSSIER CONTENTS</h2><div className="mt-3 space-y-1">{targets.map((target) => { const p = bingo.targets[target.id]; const identified = has(p, "identity"); const unread = (p.discoveries ?? []).some((k) => !(p.seenDiscoveries ?? []).includes(k)); const blackLocked = target.threat === "BLACK" && !bingo.blackBookUnlocked; return <button key={target.id} type="button" disabled={blackLocked} onClick={() => onJumpTarget(target.id)} className="bb-index-row"><span className="bb-index-thumb">{identified ? <img src={target.sprite} alt="" draggable={false} /> : "?"}</span><span className="min-w-0 flex-1"><strong>{blackLocked ? "CLASSIFIED DOSSIER" : targetTitle(target, p)}</strong><small>{blackLocked ? "BLACK BOOK SEAL" : `${target.threat} · ${p.status.replaceAll("_", " ")} · intel ${p.intel}%`}</small></span>{unread && !blackLocked && <i>NEW</i>}<b>p.{(pageByTarget.get(target.id) ?? 0) + 1}</b></button>; })}</div></article>;
}

function OrganisationPage({ s, pageNo, onJumpTarget }: { s: GameState; pageNo: number; onJumpTarget: (id: string) => void }) {
  const bingo = ensureBingoState(s);
  return <article className="bb-page"><div className="bb-page-number">{pageNo}</div><p className="bb-kicker">NETWORK INTELLIGENCE</p><h2 className="bb-page-title">KNOWN ORGANISATIONS</h2><div className="mt-3 space-y-2">{BINGO_ORGANISATIONS.map((org) => { const known = bingo.organisationsKnown.includes(org.id); const linked = BINGO_TARGETS.filter((t) => t.organisationId === org.id && bingo.targets[t.id]?.intel > 0).slice(0, 4); return <div key={org.id} className={cn("bb-org-card", !known && "opacity-45")}><div className="flex items-center justify-between gap-2"><strong>{known ? org.name : "UNKNOWN NETWORK"}</strong><span>{known ? `${org.members} MEMBERS` : "SEALED"}</span></div><p>{known ? org.description : "Interrogate captured targets and develop associated dossiers to reveal this organisation."}</p>{known && linked.length > 0 && <div className="mt-2 flex flex-wrap gap-1">{linked.map((t) => <button key={t.id} type="button" onClick={() => onJumpTarget(t.id)} className="bb-mini-link">{has(bingo.targets[t.id], "identity") ? t.name : "Unknown"}</button>)}</div>}</div>; })}</div></article>;
}

function BlackDividerPage({ s, pageNo }: { s: GameState; pageNo: number }) {
  const bingo = ensureBingoState(s);
  const resolvedStandard = BINGO_TARGETS.filter((t) => t.threat !== "BLACK" && RESOLVED.has(bingo.targets[t.id]?.status)).length;
  return <article className="bb-page bb-black-divider"><div className="bb-page-number">{pageNo}</div><ShieldAlert size={36} /><p className="bb-kicker">KAGE EYES ONLY</p><h2>THE BLACK BOOK</h2><p>Ten Kage-class targets whose dossiers are sealed behind the highest hunter clearance.</p><div className="bb-black-seal">{bingo.blackBookUnlocked ? "CLASSIFICATION LIFTED" : "CLASSIFIED"}</div><p className="mt-4 text-[10px] opacity-60">Standard files resolved: {resolvedStandard}/24</p></article>;
}

function DynamicPage({ s, id, pageNo }: { s: GameState; id: string; pageNo: number }) {
  const target = ensureBingoState(s).dynamicTargets.find((x) => x.id === id);
  if (!target) return <article className="bb-page"><div className="bb-page-number">{pageNo}</div><p>Loose-leaf dossier unavailable.</p></article>;
  const identified = target.intel >= 20;
  const src = ninjaArtSrc(target.ninja);
  return <article className="bb-page bb-target-page"><div className="bb-page-number">{pageNo}</div><header className="bb-dossier-head"><div className="bb-portrait-frame">{identified ? <img src={src} alt={target.name} draggable={false} /> : <div className="bb-silhouette">?</div>}<span style={{ background: threatInk(target.threat) }}>{target.threat}</span></div><div><p className="bb-kicker">LOOSE-LEAF FILE · FORMER SHADOW NINJA</p><h2>{identified ? target.name : "IDENTITY UNCONFIRMED"}</h2><h3>{target.epithet}</h3><p className="bb-summary">An exiled village ninja who disappeared after release and later surfaced as a missing-nin. Their original training profile has hardened outside the village.</p><div className="bb-intel-meter"><i style={{ width: `${Math.max(2, target.intel)}%` }} /><span>INTEL {target.intel}%</span></div></div></header><div className="bb-facts-grid"><PaperFact label="DEAD BOUNTY" value={identified ? `${target.bountyDead.toLocaleString()} 両` : "CLASSIFIED"} /><PaperFact label="LIVE BOUNTY" value={identified ? `${target.bountyAlive.toLocaleString()} 両` : "CLASSIFIED"} /><PaperFact label="FORMER RANK" value={identified ? target.ninja.rank.toUpperCase() : "UNKNOWN"} /><PaperFact label="POTENTIAL" value={identified ? `${target.ninja.pot}★` : "UNKNOWN"} /></div><p className="bb-pencil-note mt-4">Dynamic exile targets currently use the missing-nin tracking layer. Their full hunt/fate workflow remains tied to that system rather than the fixed 80-target archive.</p></article>;
}

export default function BingoBookOverlay({ s, onChanged, onClose, initialTargetId = null }: { s: GameState; onChanged: () => void; onClose: () => void; initialTargetId?: string | null }) {
  const bingo = ensureBingoState(s);
  const [pageIndex, setPageIndex] = useState(0);
  const [pendingIndex, setPendingIndex] = useState<number | null>(null);
  const [turnDirection, setTurnDirection] = useState<"next" | "prev" | null>(null);
  const [prepTarget, setPrepTarget] = useState<BingoTargetDef | null>(null);
  const [coverVisible, setCoverVisible] = useState(true);
  const pointerStart = useRef<number | null>(null);

  const pages = useMemo<StaticPage[]>(() => {
    const built: StaticPage[] = [{ kind: "summary" }];
    for (let chunk = 0; chunk < 8; chunk++) built.push({ kind: "contents", chunk });
    built.push({ kind: "organisations" });
    for (const target of BINGO_TARGETS.filter((t) => t.threat !== "BLACK")) built.push({ kind: "target", target });
    built.push({ kind: "black-divider" });
    for (const target of BINGO_TARGETS.filter((t) => t.threat === "BLACK")) built.push({ kind: "target", target });
    if (bingo.dynamicTargets.length) {
      built.push({ kind: "dynamic-divider" });
      for (const target of bingo.dynamicTargets) built.push({ kind: "dynamic", id: target.id });
    }
    return built;
  }, [bingo.dynamicTargets.length, bingo.blackBookUnlocked]);

  const pageByTarget = useMemo(() => {
    const map = new Map<string, number>();
    pages.forEach((page, i) => { if (page.kind === "target") map.set(page.target.id, i); if (page.kind === "dynamic") map.set(page.id, i); });
    return map;
  }, [pages]);

  useEffect(() => {
    const revealed = refreshPendingMissingNin(s);
    if (revealed.length) onChanged();
    const timer = window.setTimeout(() => setCoverVisible(false), 430);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (initialTargetId) {
      const idx = pageByTarget.get(initialTargetId);
      if (idx != null) setPageIndex(idx);
    }
  }, [initialTargetId, pageByTarget]);

  useEffect(() => {
    const page = pages[pageIndex];
    const right = pages[pageIndex + 1];
    const showRight = typeof window !== "undefined" && window.matchMedia("(min-width: 768px)").matches;
    const ids = [page, showRight ? right : undefined].flatMap((p) => p?.kind === "target" ? [p.target.id] : []);
    let changed = false;
    for (const id of ids) changed = markBingoDiscoveriesSeen(s, id) || changed;
    if (changed) {
      const t = window.setTimeout(onChanged, 650);
      return () => window.clearTimeout(t);
    }
  }, [pageIndex]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { e.preventDefault(); onClose(); }
      else if (e.key === "ArrowRight") { e.preventDefault(); turnTo(Math.min(pages.length - 1, pageIndex + 1)); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); turnTo(Math.max(0, pageIndex - 1)); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const turnTo = (index: number) => {
    if (turnDirection || index === pageIndex || index < 0 || index >= pages.length) return;
    audio.click();
    const direction = index > pageIndex ? "next" : "prev";
    setPendingIndex(index);
    setTurnDirection(direction);
    window.setTimeout(() => { setPageIndex(index); setPendingIndex(null); setTurnDirection(null); }, 330);
  };

  const jumpTarget = (id: string) => {
    const index = pageByTarget.get(id);
    if (index == null) return;
    const target = BINGO_TARGETS.find((t) => t.id === id);
    if (target?.threat === "BLACK" && !bingo.blackBookUnlocked) {
      const divider = pages.findIndex((p) => p.kind === "black-divider");
      turnTo(divider);
      return;
    }
    turnTo(index);
  };

  const jumpThreat = (threat: BingoThreat) => {
    if (threat === "BLACK" && !bingo.blackBookUnlocked) { const i = pages.findIndex((p) => p.kind === "black-divider"); turnTo(i); return; }
    const target = BINGO_TARGETS.find((t) => t.threat === threat && bingo.targets[t.id]?.intel > 0) ?? BINGO_TARGETS.find((t) => t.threat === threat);
    if (target) jumpTarget(target.id);
  };

  const renderPage = (page: StaticPage | undefined, index: number) => {
    if (!page) return <article className="bb-page bb-blank-page" />;
    const pageNo = index + 1;
    if (page.kind === "summary") return <SummaryPage s={s} pageNo={pageNo} onJumpTarget={jumpTarget} onJumpContents={() => turnTo(1)} />;
    if (page.kind === "contents") return <ContentsPage s={s} targets={BINGO_TARGETS.slice(page.chunk * 10, page.chunk * 10 + 10)} chunk={page.chunk} pageNo={pageNo} pageByTarget={pageByTarget} onJumpTarget={jumpTarget} />;
    if (page.kind === "organisations") return <OrganisationPage s={s} pageNo={pageNo} onJumpTarget={jumpTarget} />;
    if (page.kind === "black-divider") return <BlackDividerPage s={s} pageNo={pageNo} />;
    if (page.kind === "dynamic-divider") return <article className="bb-page bb-black-divider"><div className="bb-page-number">{pageNo}</div><Crosshair size={36} /><p className="bb-kicker">LOOSE-LEAF ADDENDUM</p><h2>EXILED MISSING-NIN</h2><p>Former Shadow Village ninja who resurfaced after exile are inserted here as irregular field dossiers.</p></article>;
    if (page.kind === "dynamic") return <DynamicPage s={s} id={page.id} pageNo={pageNo} />;
    return <TargetPage s={s} target={page.target} progress={bingo.targets[page.target.id]} pageNo={pageNo} onChanged={onChanged} onPrep={() => setPrepTarget(page.target)} />;
  };

  const active = activeBingoHunt(s);
  return (
    <div className="fixed inset-0 z-[180] flex items-center justify-center overflow-hidden bg-[#07070b]/94 p-2 backdrop-blur-md sm:p-4" onPointerDown={(e) => { pointerStart.current = e.clientX; }} onPointerUp={(e) => { if (pointerStart.current == null) return; const dx = e.clientX - pointerStart.current; pointerStart.current = null; if (Math.abs(dx) < 55) return; if (dx < 0) turnTo(Math.min(pages.length - 1, pageIndex + 1)); else turnTo(Math.max(0, pageIndex - 1)); }}>
      <style>{BOOK_CSS}</style>
      {prepTarget && <HuntPrepModal s={s} target={prepTarget} onClose={() => setPrepTarget(null)} onChanged={onChanged} />}
      <div className="bb-book-shell">
        <div className="bb-book-topbar">
          <div className="flex min-w-0 items-center gap-2"><BookOpen size={16} /><span className="truncate">BINGO BOOK · {pageIndex + 1}/{pages.length}</span>{bingoUnreadCount(s) > 0 && <b>{bingoUnreadCount(s)} NEW</b>}</div>
          <div className="flex items-center gap-1">{active && <button type="button" onClick={() => jumpTarget(active.targetId)} className="bb-top-button bb-top-active"><Bookmark size={12} fill="currentColor" /> ACTIVE HUNT</button>}<button type="button" onClick={onClose} className="bb-top-button"><X size={14} /> PAUSE MENU</button></div>
        </div>
        <div className="bb-book-stage">
          <div className="bb-threat-tabs"><button type="button" onClick={() => turnTo(1)} className="bb-threat-tab bb-index-tab">INDEX</button>{THREATS.map((threat) => <button key={threat} type="button" onClick={() => jumpThreat(threat)} className="bb-threat-tab" style={{ background: threatInk(threat) }}>{threat}</button>)}</div>
          <div className="bb-spine" />
          {pendingIndex != null && <div className="bb-spread bb-under-spread"><div className="bb-left-page">{renderPage(pages[pendingIndex], pendingIndex)}</div><div className="bb-right-page">{renderPage(pages[pendingIndex + 1], pendingIndex + 1)}</div></div>}
          <div className="bb-spread"><div className="bb-left-page">{renderPage(pages[pageIndex], pageIndex)}</div><div className="bb-right-page">{renderPage(pages[pageIndex + 1], pageIndex + 1)}</div></div>
          {turnDirection === "next" && <><div className="bb-flip bb-flip-next bb-flip-mobile">{renderPage(pages[pageIndex], pageIndex)}</div><div className="bb-flip bb-flip-next bb-flip-desktop">{renderPage(pages[pageIndex + 1], pageIndex + 1)}</div></>}
          {turnDirection === "prev" && <><div className="bb-flip bb-flip-prev bb-flip-mobile">{renderPage(pages[pageIndex], pageIndex)}</div><div className="bb-flip bb-flip-prev bb-flip-desktop">{renderPage(pages[pageIndex], pageIndex)}</div></>}
          <button type="button" aria-label="Previous page" disabled={pageIndex <= 0 || !!turnDirection} onClick={() => turnTo(Math.max(0, pageIndex - 1))} className="bb-page-arrow bb-page-arrow-left"><ChevronLeft size={22} /></button>
          <button type="button" aria-label="Next page" disabled={pageIndex >= pages.length - 1 || !!turnDirection} onClick={() => turnTo(Math.min(pages.length - 1, pageIndex + 1))} className="bb-page-arrow bb-page-arrow-right"><ChevronRight size={22} /></button>
        </div>
        <div className="bb-book-footer"><span>Swipe or use ← → to turn pages</span><span>{pageIndex > 0 ? "Tap INDEX or a threat tab to jump" : "Hunter archive opened from the pause menu"}</span></div>
        {coverVisible && <div className="bb-opening-cover"><div><span>影</span><p>BINGO BOOK</p><small>SHADOW VILLAGE · HUNTER-NIN ARCHIVE</small></div></div>}
      </div>
    </div>
  );
}

const BOOK_CSS = `
.bb-book-shell{position:relative;display:flex;height:min(94vh,900px);width:min(1180px,100%);flex-direction:column;overflow:hidden;border-radius:26px;background:linear-gradient(145deg,#2a1a11,#130d09 70%);box-shadow:0 28px 80px rgba(0,0,0,.65),inset 0 0 0 1px rgba(255,225,170,.08)}
.bb-book-topbar,.bb-book-footer{display:flex;align-items:center;justify-content:space-between;gap:8px;flex:0 0 auto;color:#e7d7b7}.bb-book-topbar{min-height:42px;padding:8px 12px;border-bottom:1px solid rgba(231,215,183,.08);font-size:10px;font-weight:900;letter-spacing:.12em}.bb-book-topbar b{border-radius:999px;background:#8e241c;padding:3px 7px;font-size:8px;color:#fff0d4}.bb-book-footer{min-height:28px;padding:5px 12px;border-top:1px solid rgba(231,215,183,.07);font-size:8px;opacity:.48}
.bb-top-button{display:flex;min-height:30px;align-items:center;justify-content:center;gap:5px;border:1px solid rgba(231,215,183,.12);border-radius:8px;background:rgba(0,0,0,.22);padding:5px 8px;font-size:8px;font-weight:900;color:#e7d7b7}.bb-top-active{border-color:rgba(176,49,35,.35);color:#ffab91}
.bb-book-stage{position:relative;min-height:0;flex:1;perspective:1800px;padding:7px 18px 7px 8px}.bb-spread{position:absolute;inset:7px 18px 7px 8px;display:grid;grid-template-columns:1fr 1fr;overflow:hidden;border-radius:8px 16px 16px 8px;background:#e8d4a9;box-shadow:0 7px 25px rgba(0,0,0,.4)}.bb-under-spread{z-index:0}.bb-left-page,.bb-right-page{min-width:0;min-height:0;overflow:hidden}.bb-left-page{border-right:1px solid rgba(83,57,31,.22)}.bb-right-page{border-left:1px solid rgba(255,255,255,.28)}.bb-spine{position:absolute;z-index:24;left:calc(50% - 5px);top:8px;bottom:8px;width:12px;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(58,38,22,.18),rgba(255,255,255,.22),rgba(45,29,17,.19),transparent)}
.bb-page{position:relative;display:flex;height:100%;min-height:0;flex-direction:column;overflow-y:auto;padding:18px 20px 16px;color:#382918;background:radial-gradient(circle at 14% 18%,rgba(255,255,255,.45),transparent 28%),linear-gradient(92deg,rgba(104,73,40,.065),transparent 7%,transparent 92%,rgba(83,54,29,.06)),#ead9b5;font-family:ui-serif,Georgia,serif;scrollbar-width:thin;scrollbar-color:rgba(86,56,28,.25) transparent}.bb-page:after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.18;background-image:repeating-linear-gradient(0deg,transparent,transparent 25px,rgba(78,54,31,.08) 26px)}.bb-page>*{position:relative;z-index:1}.bb-page-black{background:radial-gradient(circle at 20% 10%,rgba(225,199,145,.12),transparent 36%),linear-gradient(90deg,#1d1915,#272019 50%,#1c1814);color:#ddc99f}.bb-page-number{position:absolute;right:12px;bottom:7px;font-size:8px;font-weight:900;opacity:.32}.bb-page-title{font-family:var(--font-display,ui-serif);font-size:20px;font-weight:900;letter-spacing:.06em}.bb-kicker{font-family:ui-sans-serif,system-ui,sans-serif;font-size:7.5px;font-weight:900;letter-spacing:.18em;opacity:.55}.bb-target-page h2{margin-top:4px;font-family:var(--font-display,ui-serif);font-size:21px;font-weight:900;line-height:1}.bb-target-page h3{margin-top:3px;font-size:11px;font-weight:900;color:#8a241d}.bb-page-black h3{color:#d9ad58}.bb-summary{margin-top:7px;font-size:9px;line-height:1.45;opacity:.68}.bb-dossier-head{display:flex;gap:12px;padding-bottom:10px;border-bottom:1px solid rgba(86,56,28,.22)}.bb-portrait-frame{position:relative;display:grid;height:118px;width:96px;flex:0 0 auto;place-items:end center;overflow:hidden;border:5px solid #f4e4c2;outline:1px solid rgba(64,42,23,.32);background:linear-gradient(#c9b58f,#e5d2ad);box-shadow:2px 3px 0 rgba(65,42,21,.13);transform:rotate(-1deg)}.bb-portrait-frame img{max-height:100%;max-width:100%;object-fit:contain;filter:drop-shadow(0 2px 2px rgba(0,0,0,.18))}.bb-portrait-frame>span{position:absolute;right:2px;bottom:2px;border-radius:2px;padding:2px 5px;color:#fff1d5;font-family:ui-sans-serif,system-ui;font-size:8px;font-weight:1000}.bb-silhouette{display:grid;height:100%;width:100%;place-items:center;font-size:42px;font-weight:900;color:rgba(46,33,21,.18)}.bb-intel-meter{position:relative;margin-top:8px;height:5px;overflow:hidden;border-radius:99px;background:rgba(70,46,25,.12)}.bb-intel-meter i{display:block;height:100%;background:#8a241d}.bb-intel-meter span{position:absolute;right:0;top:7px;font-family:ui-sans-serif,system-ui;font-size:7px;font-style:normal;font-weight:900;opacity:.55}
.bb-facts-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-top:10px}.bb-note{position:relative;margin-top:5px;border-left:2px solid rgba(82,54,29,.28);background:rgba(255,249,226,.36);padding:5px 6px}.bb-note span{display:block;font-family:ui-sans-serif,system-ui;font-size:6.5px;font-weight:900;letter-spacing:.12em;opacity:.48}.bb-note strong{display:block;margin-top:2px;font-size:8.5px;line-height:1.25}.bb-note em{position:absolute;right:4px;top:3px;border-radius:2px;background:#b73727;padding:1px 3px;font-family:ui-sans-serif,system-ui;font-size:5.5px;font-style:normal;font-weight:1000;color:white;letter-spacing:.08em}.bb-note-new{background:#fff5c5;box-shadow:inset 0 0 0 1px rgba(183,55,39,.18);animation:bbNewNote 1.4s ease-out}.bb-note-warning{border-left-color:#9e2d23}.bb-dossier-columns{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.bb-section-title{font-family:ui-sans-serif,system-ui;font-size:7px;font-weight:1000;letter-spacing:.16em;opacity:.55}.bb-redacted{margin-top:7px;font-size:7.5px;letter-spacing:.1em;opacity:.3}.bb-pencil-note{margin-top:7px;font-size:8px;font-style:italic;opacity:.5;transform:rotate(-.3deg)}
.bb-page-actions,.bb-decision,.bb-detention{margin-top:8px;border-top:1px solid rgba(86,56,28,.2);padding-top:8px}.bb-page-actions{display:grid;grid-template-columns:1fr 1fr;gap:6px}.bb-ink-button,.bb-red-button,.bb-gold-button{min-height:30px;border-radius:5px;padding:5px 8px;font-family:ui-sans-serif,system-ui;font-size:7.5px;font-weight:1000;letter-spacing:.08em}.bb-ink-button{border:1px solid rgba(58,41,25,.25);background:rgba(57,43,29,.08);color:inherit}.bb-red-button{border:1px solid #7f211a;background:#922a20;color:#fff0d7}.bb-gold-button{border:1px solid #9a742d;background:#c7a24d;color:#33230e}.bb-paper-choice{display:flex;width:100%;flex-direction:column;border:1px solid rgba(78,54,31,.2);border-radius:5px;background:rgba(255,248,222,.35);padding:6px;text-align:left;font-size:8px}.bb-paper-choice strong{font-weight:1000}.bb-paper-choice span{margin-top:2px;font-size:7.5px;opacity:.55}.bb-chip{border:1px solid rgba(58,41,25,.22);border-radius:99px;padding:5px 8px;font-size:8px;font-weight:800}.bb-chip-selected{background:#4d5b36;color:#fff9e9}.bb-hunter{display:flex;width:100%;align-items:center;gap:7px;border:1px solid rgba(58,41,25,.18);border-radius:6px;background:rgba(255,249,229,.32);padding:7px;text-align:left}.bb-hunter strong,.bb-hunter span{display:block}.bb-hunter strong{font-size:9px}.bb-hunter span{font-size:7.5px;opacity:.55}.bb-hunter>b{font-size:7px}.bb-hunter-selected{background:#d9c885;border-color:#907126}.bb-paper-panel{border-radius:12px;background:#ead9b5;box-shadow:0 20px 60px rgba(0,0,0,.55),inset 0 0 0 1px rgba(75,48,26,.18)}
.bb-hunt-slip{margin-top:8px;border:1px solid rgba(113,34,26,.25);background:#e4cfa6;padding:8px;box-shadow:2px 3px 0 rgba(69,42,20,.08);transform:rotate(.2deg)}.bb-bookmark{position:absolute;right:27px;top:0;display:flex;align-items:center;gap:3px;background:#9d2c22;padding:8px 7px 12px;color:#fff0d7;font-family:ui-sans-serif,system-ui;font-size:6px;font-weight:1000;clip-path:polygon(0 0,100% 0,100% 82%,50% 100%,0 82%)}
.bb-stamp{position:absolute;right:8%;top:37%;z-index:5;max-width:70%;transform:rotate(-12deg);border:4px double currentColor;border-radius:7px;padding:7px 11px;font-family:ui-sans-serif,system-ui;font-size:20px;font-weight:1000;letter-spacing:.08em;opacity:.63;mix-blend-mode:multiply;animation:bbStamp .38s cubic-bezier(.2,1.6,.4,1)}.bb-stamp-killed{color:#8c211b}.bb-stamp-captured{color:#31577d}.bb-stamp-recruited{color:#396143}
.bb-summary-page{align-items:flex-start}.bb-inside-seal{display:grid;height:62px;width:62px;place-items:center;border:3px double #8a241d;border-radius:50%;font-family:var(--font-display,ui-serif);font-size:30px;font-weight:900;color:#8a241d;transform:rotate(-7deg);opacity:.68}.bb-ledger{display:grid;width:100%;grid-template-columns:1fr 1fr;border-top:1px solid rgba(73,48,27,.25);border-left:1px solid rgba(73,48,27,.25)}.bb-ledger>div{border-right:1px solid rgba(73,48,27,.25);border-bottom:1px solid rgba(73,48,27,.25);padding:8px}.bb-ledger span,.bb-ledger strong{display:block}.bb-ledger span{font-family:ui-sans-serif,system-ui;font-size:7px;font-weight:900;letter-spacing:.12em;opacity:.45}.bb-ledger strong{margin-top:2px;font-size:15px}.bb-new-intel,.bb-active-bookmark{display:flex;width:100%;align-items:center;gap:8px;border:1px solid rgba(126,34,27,.28);background:rgba(150,45,34,.07);padding:9px;text-align:left;color:#7e221b}.bb-new-intel{width:auto;border-radius:4px;font-family:ui-sans-serif,system-ui;font-size:8px;font-weight:1000}.bb-active-bookmark span{min-width:0;flex:1}.bb-active-bookmark small,.bb-active-bookmark strong{display:block}.bb-active-bookmark small{font-size:6.5px;font-weight:1000;letter-spacing:.13em}.bb-active-bookmark strong{margin-top:2px;font-size:10px}
.bb-index-row{display:flex;width:100%;align-items:center;gap:7px;border-bottom:1px dotted rgba(75,49,27,.25);padding:4px 2px;text-align:left}.bb-index-row:disabled{opacity:.35}.bb-index-thumb{display:grid;height:31px;width:26px;flex:0 0 auto;place-items:center;overflow:hidden;background:rgba(70,45,25,.08);font-size:14px;font-weight:900;color:rgba(53,38,24,.25)}.bb-index-thumb img{max-height:100%;max-width:100%;object-fit:contain}.bb-index-row strong,.bb-index-row small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bb-index-row strong{font-size:8.5px}.bb-index-row small{margin-top:1px;font-size:6.5px;opacity:.5}.bb-index-row>b{font-size:7px;opacity:.42}.bb-index-row>i{border-radius:2px;background:#a32e23;padding:1px 3px;font-family:ui-sans-serif,system-ui;font-size:5px;font-style:normal;font-weight:1000;color:#fff}.bb-org-card{border-left:3px solid rgba(80,55,31,.28);background:rgba(255,248,220,.28);padding:8px}.bb-org-card strong{font-size:9px}.bb-org-card span{font-family:ui-sans-serif,system-ui;font-size:6px;font-weight:900;opacity:.45}.bb-org-card p{margin-top:4px;font-size:8px;line-height:1.35;opacity:.62}.bb-mini-link{border:1px solid rgba(74,48,27,.2);border-radius:99px;padding:3px 5px;font-size:6.5px;font-weight:800}
.bb-black-divider{align-items:center;justify-content:center;background:radial-gradient(circle at 50% 36%,#30271d,#15120f 67%);color:#d9c49a;text-align:center}.bb-black-divider h2{margin-top:7px;font-family:var(--font-display,ui-serif);font-size:28px;font-weight:1000;letter-spacing:.08em}.bb-black-divider p{margin-top:8px;max-width:290px;font-size:10px;line-height:1.55;opacity:.58}.bb-black-seal{margin-top:18px;transform:rotate(-6deg);border:4px double #a32b21;border-radius:5px;padding:7px 12px;font-family:ui-sans-serif,system-ui;font-size:11px;font-weight:1000;letter-spacing:.12em;color:#c45b4c;opacity:.8}
.bb-threat-tabs{position:absolute;right:0;top:25px;z-index:50;display:flex;flex-direction:column;gap:3px;transform:translateX(2px)}.bb-threat-tab{min-height:29px;min-width:37px;border-radius:0 6px 6px 0;padding:4px 5px;color:#fff1d6;font-size:7px;font-weight:1000;box-shadow:1px 2px 4px rgba(0,0,0,.25)}.bb-index-tab{background:#715638;color:#fff2d6}.bb-page-arrow{position:absolute;z-index:60;top:50%;display:grid;height:38px;width:26px;place-items:center;border-radius:7px;background:rgba(27,17,11,.66);color:#e8d5b0;transform:translateY(-50%);backdrop-filter:blur(3px)}.bb-page-arrow:disabled{opacity:.15}.bb-page-arrow-left{left:1px}.bb-page-arrow-right{right:9px}
.bb-flip{position:absolute;z-index:40;top:7px;bottom:7px;overflow:hidden;backface-visibility:hidden;transform-style:preserve-3d}.bb-flip-next{animation:bbFlipNext .33s ease-in forwards;transform-origin:left center}.bb-flip-prev{animation:bbFlipPrev .33s ease-in forwards;transform-origin:right center}.bb-flip-desktop{right:18px;width:calc((100% - 26px)/2)}.bb-flip-mobile{display:none}.bb-opening-cover{position:absolute;z-index:100;inset:42px 0 28px;display:grid;place-items:center;background:linear-gradient(135deg,#372116,#160e0a 65%);transform-origin:left center;animation:bbOpenCover .42s ease-in forwards;backface-visibility:hidden}.bb-opening-cover>div{text-align:center;color:#d9c49a}.bb-opening-cover span{display:grid;margin:auto;height:70px;width:70px;place-items:center;border:2px solid rgba(218,196,154,.28);border-radius:12px;font-family:var(--font-display,ui-serif);font-size:38px;font-weight:1000}.bb-opening-cover p{margin-top:13px;font-family:var(--font-display,ui-serif);font-size:27px;font-weight:1000;letter-spacing:.18em}.bb-opening-cover small{font-size:7px;font-weight:900;letter-spacing:.2em;opacity:.45}
@keyframes bbOpenCover{0%{transform:rotateY(0);opacity:1}78%{opacity:1}100%{transform:rotateY(-94deg);opacity:0}}@keyframes bbFlipNext{0%{transform:rotateY(0)}100%{transform:rotateY(-178deg)}}@keyframes bbFlipPrev{0%{transform:rotateY(0)}100%{transform:rotateY(178deg)}}@keyframes bbStamp{0%{transform:rotate(-12deg) scale(2.2);opacity:0}100%{transform:rotate(-12deg) scale(1);opacity:.63}}@keyframes bbNewNote{0%{box-shadow:inset 0 0 0 2px rgba(183,55,39,.65),0 0 15px rgba(183,55,39,.25)}100%{box-shadow:inset 0 0 0 1px rgba(183,55,39,.18)}}
@media(max-width:767px){.bb-book-shell{height:calc(100vh - 8px);border-radius:16px}.bb-book-stage{padding:5px 12px 5px 5px}.bb-spread{inset:5px 12px 5px 5px;display:block}.bb-right-page{display:none}.bb-left-page{height:100%;border:0}.bb-spine{left:5px;top:6px;bottom:6px;width:7px}.bb-threat-tabs{right:-1px;top:50px}.bb-threat-tab{min-height:27px;min-width:31px;font-size:6px;padding:3px}.bb-page{padding:14px 15px 13px 17px}.bb-dossier-head{gap:8px}.bb-portrait-frame{height:94px;width:76px}.bb-target-page h2{font-size:17px}.bb-summary{font-size:8px}.bb-facts-grid{grid-template-columns:1fr 1fr}.bb-dossier-columns{grid-template-columns:1fr}.bb-note strong{font-size:8px}.bb-book-footer span:last-child{display:none}.bb-top-button{padding:4px 6px;font-size:7px}.bb-top-active{max-width:120px;overflow:hidden}.bb-flip-desktop{display:none}.bb-flip-mobile{display:block;left:5px;right:12px}.bb-page-arrow-right{right:4px}.bb-stamp{font-size:15px}.bb-opening-cover{inset:42px 0 28px}}
@media(prefers-reduced-motion:reduce){.bb-opening-cover,.bb-flip,.bb-stamp,.bb-note-new{animation-duration:.01ms!important}}
`;
