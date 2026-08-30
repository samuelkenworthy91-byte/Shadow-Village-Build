import { useState } from "react";
import { Eye, Flag, Map, Shield, Swords } from "lucide-react";
import type { GameState, Ninja, WarFactionId, WarOperationType } from "../game/types";
import { WAR_FACTIONS, WAR_INTERVENTIONS, WAR_LINKS, isShadowFrontier, resolveWarIntervention, type WarInterventionKind } from "../game/war";
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

interface WarSkirmish {
  kind: WarInterventionKind;
  territoryId: string;
  enemyHp: number;
  enemyMaxHp: number;
  round: number;
  team: { id: number; name: string; hp: number; maxHp: number }[];
  log: string[];
  result: "won" | "lost" | null;
  resultText: string;
}

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
  const [battle, setBattle] = useState<WarSkirmish | null>(null);
  const [, setVersion] = useState(0);

  const selected = s.war.territories.find((t) => t.id === selectedId) ?? s.war.territories[0];
  const ready = [...s.ninjas]
    .filter((n) => n.status === "ready")
    .sort((a, b) => (b.s.tac + b.s.ste + b.level) - (a.s.tac + a.s.ste + a.level))
    .slice(0, 10);
  const controlled = s.war.territories.filter((t) => t.owner === "shadow").length;
  const founder = s.ninjas.find((n) => n.id === s.war.founderId);

  const toggleNinja = (id: number) => {
    setSelectedNinjas((ids) => ids.includes(id) ? ids.filter((x) => x !== id) : ids.length >= 4 ? ids : [...ids, id]);
  };

  const startIntervention = (kind: WarInterventionKind) => {
    if (!selected || s.war.operationsLeft <= 0 || selectedNinjas.length === 0 || selected.owner === "shadow") return;
    const frontierNow = isShadowFrontier(s, selected.id);
    if (kind !== "scout_force" && !frontierNow) return;
    if (kind === "eliminate_commander" && (selected.owner === "neutral" || selected.intel < 1)) return;
    const team = selectedNinjas.map((id) => s.ninjas.find((n) => n.id === id)).filter((n): n is Ninja => !!n && n.status === "ready");
    if (!team.length) return;
    const mult = kind === "scout_force" ? 0.82 : kind === "sabotage_supplies" ? 0.95 : kind === "eliminate_commander" ? 1.12 : 1.28;
    const enemyMaxHp = Math.round((150 + selected.strength * 6.2 + s.war.turn * 8) * mult);
    s.war.operationsLeft -= 1;
    s.war.history.unshift(`${WAR_INTERVENTIONS[kind].name} launched at ${selected.name}.`);
    setBattle({
      kind, territoryId: selected.id, enemyHp: enemyMaxHp, enemyMaxHp, round: 1, result: null, resultText: "",
      team: team.map((n) => ({ id: n.id, name: n.name, maxHp: 45 + n.level * 4 + n.s.tai * 2 + n.s.tac, hp: 45 + n.level * 4 + n.s.tai * 2 + n.s.tac })),
      log: [`${WAR_INTERVENTIONS[kind].name}: ${WAR_FACTIONS[selected.owner].name} forces engaged at ${selected.name}.`],
    });
  };

  const battleAct = (style: "strike" | "jutsu" | "tactics") => {
    if (!battle || battle.result) return;
    const territory = s.war.territories.find((t) => t.id === battle.territoryId);
    if (!territory) return;
    const alive = battle.team.filter((x) => x.hp > 0);
    const ninjas = alive.map((x) => s.ninjas.find((n) => n.id === x.id)).filter((n): n is Ninja => !!n);
    if (!ninjas.length) return;
    const raw = ninjas.reduce((sum, n) => sum + (style === "strike" ? n.s.tai + n.s.ken : style === "jutsu" ? n.s.nin + n.s.gen : n.s.tac + n.s.ste), 0);
    const damage = Math.max(12, Math.round(raw * (style === "tactics" ? 0.13 : 0.18) * (0.88 + Math.random() * 0.24)));
    const enemyHp = Math.max(0, battle.enemyHp - damage);
    const logs = [`Round ${battle.round}: ${style === "strike" ? "the cell crashes into the line" : style === "jutsu" ? "coordinated jutsu tears through the force" : "a tactical feint opens the formation"} (−${damage}).`, ...battle.log].slice(0, 7);
    if (enemyHp <= 0) {
      const msg = resolveWarIntervention(s, battle.territoryId, battle.kind, true, battle.team.map((x) => x.id));
      setBattle({ ...battle, enemyHp: 0, result: "won", resultText: msg, log: [msg, ...logs].slice(0, 7) });
      setVersion((v) => v + 1);
      return;
    }
    const nextTeam = battle.team.map((x) => ({ ...x }));
    const livingIndexes = nextTeam.map((x, i) => x.hp > 0 ? i : -1).filter((i) => i >= 0);
    const target = livingIndexes[Math.floor(Math.random() * livingIndexes.length)];
    const incoming = Math.max(7, Math.round((10 + territory.strength * 0.32) * (style === "tactics" ? 0.48 : 1) * (0.82 + Math.random() * 0.36)));
    nextTeam[target].hp = Math.max(0, nextTeam[target].hp - incoming);
    logs.unshift(`${nextTeam[target].name} takes ${incoming} damage from the counterattack.`);
    if (nextTeam.every((x) => x.hp <= 0)) {
      const msg = resolveWarIntervention(s, battle.territoryId, battle.kind, false, nextTeam.map((x) => x.id));
      setBattle({ ...battle, enemyHp, team: nextTeam, result: "lost", resultText: msg, log: [msg, ...logs].slice(0, 7) });
      setVersion((v) => v + 1);
      return;
    }
    setBattle({ ...battle, enemyHp, team: nextTeam, round: battle.round + 1, log: logs });
  };

  if (battle) {
    const t = s.war.territories.find((x) => x.id === battle.territoryId);
    return (
      <section className="min-h-0 overflow-y-auto rounded-xl bg-[#111322]/95 p-3 ring-1 ring-white/10 lg:col-span-3">
        <div className="mx-auto max-w-3xl">
          <div className="mb-3 flex items-center gap-2">
            <Swords size={17} className="text-vermil" />
            <div className="mr-auto"><div className="font-display text-sm font-bold tracking-[0.15em] text-paper">{WAR_INTERVENTIONS[battle.kind].name.toUpperCase()}</div><div className="text-[10px] text-paper/40">{t?.name} · Round {battle.round}</div></div>
            <div className="rounded-lg bg-black/30 px-2 py-1 text-[10px] text-gold">WAR OP SPENT</div>
          </div>
          <div className="rounded-xl bg-black/30 p-3 ring-1 ring-vermil/20">
            <div className="mb-1 flex justify-between text-[10px] font-bold text-paper/70"><span>{t ? WAR_FACTIONS[t.owner].name : "Enemy Force"}</span><span>{battle.enemyHp}/{battle.enemyMaxHp}</span></div>
            <div className="h-3 overflow-hidden rounded-full bg-white/10"><div className="h-full bg-vermil transition-all" style={{ width: `${Math.max(0, battle.enemyHp / battle.enemyMaxHp * 100)}%` }} /></div>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {battle.team.map((n) => <div key={n.id} className="rounded-lg bg-black/25 p-2 ring-1 ring-white/8"><div className="flex justify-between text-[10px]"><span className="font-bold text-paper/80">{n.name}</span><span className={n.hp > 0 ? "text-jade" : "text-vermil"}>{n.hp}/{n.maxHp}</span></div><div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full bg-jade/80" style={{ width: `${n.hp / n.maxHp * 100}%` }} /></div></div>)}
          </div>
          {!battle.result ? <div className="mt-3 grid grid-cols-3 gap-2">
            <button onClick={() => battleAct("strike")} className="btn-primary h-11 rounded-xl text-[10px] font-bold">STRIKE<br/><span className="text-[8px] opacity-60">TAI + KEN</span></button>
            <button onClick={() => battleAct("jutsu")} className="btn-primary h-11 rounded-xl text-[10px] font-bold">JUTSU<br/><span className="text-[8px] opacity-60">NIN + GEN</span></button>
            <button onClick={() => battleAct("tactics")} className="btn-ghost h-11 rounded-xl text-[10px] font-bold">TACTICS<br/><span className="text-[8px] opacity-60">TAC + STE · less counter</span></button>
          </div> : <button onClick={() => setBattle(null)} className="btn-primary mt-3 h-11 w-full rounded-xl text-[11px] font-bold tracking-widest">{battle.result === "won" ? "VICTORY — RETURN TO MAP" : "DEFEAT — RETURN TO MAP"}</button>}
          <div className="mt-3 space-y-1">{battle.log.map((line, i) => <p key={`${i}-${line}`} className="rounded-md bg-white/[0.025] px-2 py-1.5 text-[9.5px] text-paper/50">{line}</p>)}</div>
        </div>
      </section>
    );
  }

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
              className="btn-primary mt-3 h-10 w-full rounded-lg text-[10px] font-bold tracking-[0.14em] disabled:cursor-not-allowed disabled:opacity-30"
            >
              LAUNCH {OP_META[operation].label.toUpperCase()}
            </button>
          </div>
        </div>
      </div>

      <div className="mt-3 rounded-xl bg-[#15111c]/80 p-3 ring-1 ring-vermil/20">
        <div className="mb-2"><div className="text-[9px] font-bold uppercase tracking-[0.18em] text-vermil/80">Field interventions</div><p className="mt-1 text-[9.5px] text-paper/40">Spend 1 war operation to enter a tactical skirmish. Victory changes this territory immediately.</p></div>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {(["scout_force", "sabotage_supplies", "eliminate_commander", "breakthrough"] as WarInterventionKind[]).map((kind) => {
            const blocked = s.war.operationsLeft <= 0 || selectedNinjas.length === 0 || selected.owner === "shadow" || (kind !== "scout_force" && !frontier) || (kind === "eliminate_commander" && (selected.owner === "neutral" || selected.intel < 1));
            return <button key={kind} disabled={blocked} onClick={() => startIntervention(kind)} className="rounded-lg bg-black/30 p-2.5 text-left ring-1 ring-inset ring-white/8 transition hover:bg-vermil/10 hover:ring-vermil/30 disabled:cursor-not-allowed disabled:opacity-30"><div className="text-[10px] font-bold text-paper/90">{WAR_INTERVENTIONS[kind].name}</div><p className="mt-1 text-[9px] leading-relaxed text-paper/40">{WAR_INTERVENTIONS[kind].desc}</p></button>;
          })}
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
