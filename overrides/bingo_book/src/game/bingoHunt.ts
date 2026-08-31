import type { GameState, Mission, Ninja, Rank, Skill } from "./types";
import { MISSION_MIN_RANK } from "./content";
import { addBingoIntel, BINGO_ACTIVE_PARTY_SIZE, BINGO_TARGET_BY_ID, ensureBingoState, type BingoState, type BingoTargetDef } from "./bingo";
import { applyHuntEffect, createHuntRun, HUNT_EVENTS, resolveSkillCheck, rollHuntEvent, type HuntBiome, type HuntChoiceEffect, type HuntEventDef, type HuntRunState } from "./huntEvents";

export type BingoRuntimeState = BingoState & {
  activeHunt?: HuntRunState | null;
};

const INTEL_MISSION_PREFIX = "bingo_intel:";

const INTEL_MISSION_VARIANTS = [
  { title: "Question the Black-Market Courier", desc: "A courier tied to the target's network has been identified. Bring back route information before they disappear.", focus: ["ste", "tac"] as Skill[] },
  { title: "Search the Abandoned Hideout", desc: "A recently vacated safehouse may still contain maps, seals or discarded equipment linked to the target.", focus: ["ste", "doj", "tac"] as Skill[] },
  { title: "Follow the Chakra Trail", desc: "Sensor reports suggest the target crossed this region recently. Track the fading signature without alerting them.", focus: ["doj", "spd", "ste"] as Skill[] },
  { title: "Protect the Informant", desc: "A witness is willing to identify the target's associates if your cell can keep them alive long enough to talk.", focus: ["tac", "med", "ken"] as Skill[] },
  { title: "Capture an Associate", desc: "One of the target's known runners is moving between safehouses. Take them alive and extract useful information.", focus: ["ste", "ken", "tac"] as Skill[] },
  { title: "Recover the Stolen Dossier", desc: "A partial hunter-nin file was stolen before reaching the village. Recover it before the target's organisation destroys it.", focus: ["spd", "nin", "tac"] as Skill[] },
];

function rankForThreat(target: BingoTargetDef): Rank {
  if (target.threat === "B") return "B";
  if (target.threat === "A") return "A";
  return "S";
}

function targetMissionScale(target: BingoTargetDef): number {
  return target.threat === "BLACK" ? 1.35 : target.threat === "SS" ? 1.28 : target.threat === "S+" ? 1.18 : target.threat === "S" ? 1.10 : 1;
}

export function isBingoIntelMission(m: Mission): boolean {
  return typeof m.specialId === "string" && m.specialId.startsWith(INTEL_MISSION_PREFIX);
}

export function bingoMissionTargetId(m: Mission): string | null {
  return isBingoIntelMission(m) ? m.specialId!.slice(INTEL_MISSION_PREFIX.length) : null;
}

export function queuedIntelMission(s: GameState, targetId: string): Mission | null {
  return s.missions.find((m) => bingoMissionTargetId(m) === targetId) ?? null;
}

export function queueBingoIntelMission(s: GameState, targetId: string): { ok: boolean; error?: string; mission?: Mission } {
  const bingo = ensureBingoState(s);
  if (!bingo.unlocked) return { ok: false, error: "The Bingo Book is still locked." };
  const target = BINGO_TARGET_BY_ID[targetId];
  const progress = bingo.targets[targetId];
  if (!target || !progress) return { ok: false, error: "Target dossier not found." };
  if (["captured", "killed", "recruited", "resolved"].includes(progress.status)) return { ok: false, error: "That dossier is already resolved." };
  const existing = queuedIntelMission(s, targetId);
  if (existing) return { ok: false, error: existing.squad.length ? "An intelligence operation is already underway." : "An intelligence operation is already on the Mission Board." };

  const variant = INTEL_MISSION_VARIANTS[(progress.attempts + Math.floor(progress.intel / 20) + target.id.charCodeAt(target.id.length - 1)) % INTEL_MISSION_VARIANTS.length];
  const rank = rankForThreat(target);
  const scale = targetMissionScale(target);
  const reqBase = rank === "B" ? 34 : rank === "A" ? 56 : 86;
  const req: Partial<Record<Skill, number>> = {};
  variant.focus.forEach((skill, index) => {
    req[skill] = Math.round(reqBase * scale * (index === 0 ? 1 : 0.78));
  });
  const intelReward = Math.max(8, Math.min(24, 18 - Math.floor(progress.intel / 20) * 2 + (rank === "S" ? 3 : 0)));
  const days = rank === "B" ? 2 : rank === "A" ? 3 : 4;
  const mission: Mission = {
    id: s.nextId++,
    rank,
    name: `${variant.title}: ${target.epithet}`,
    desc: variant.desc,
    req,
    slots: 3,
    days,
    totalDays: days,
    gold: Math.round((rank === "B" ? 90 : rank === "A" ? 180 : 320) * scale),
    rice: rank === "B" ? 12 : rank === "A" ? 22 : 36,
    xp: rank === "B" ? 9 : rank === "A" ? 14 : 22,
    score: rank === "B" ? 55 : rank === "A" ? 110 : 220,
    expiresDay: s.day + 6,
    minRank: MISSION_MIN_RANK[rank],
    squad: [],
    specialId: `${INTEL_MISSION_PREFIX}${targetId}`,
    specialWarning: `BINGO INTELLIGENCE: Success adds approximately ${intelReward}% intelligence to ${target.epithet}. Failure still yields a small amount of information, but may injure the deployed cell.`,
    specialRewardLabel: `BINGO INTEL +${intelReward}%`,
  };
  s.missions.push(mission);
  s.log.push({ txt: `Bingo intelligence operation added to the Mission Board: ${mission.name}.`, kind: "info", id: Date.now() });
  return { ok: true, mission };
}

export function resolveBingoIntelMission(s: GameState, m: Mission, win: boolean): string | undefined {
  const targetId = bingoMissionTargetId(m);
  if (!targetId) return undefined;
  const target = BINGO_TARGET_BY_ID[targetId];
  if (!target) return undefined;
  const match = /\+(\d+)%/.exec(m.specialRewardLabel ?? "");
  const promised = match ? Number(match[1]) : 14;
  const amount = win ? promised : Math.max(2, Math.round(promised * 0.25));
  const progress = addBingoIntel(s, targetId, amount);
  if (!progress) return undefined;
  const suffix = progress.locationKnown ? " The target's current operating area is now narrow enough to launch a hunt." : "";
  return `${target.name} dossier intelligence increased by ${amount}% to ${progress.intel}%.${suffix}`;
}

export function activeBingoHunt(s: GameState): HuntRunState | null {
  return (ensureBingoState(s) as BingoRuntimeState).activeHunt ?? null;
}

export function huntEventCount(target: BingoTargetDef): number {
  if (target.threat === "B") return 1;
  if (target.threat === "A") return 2;
  if (target.threat === "S") return 3;
  if (target.threat === "S+") return 3;
  if (target.threat === "SS") return 4;
  return 5;
}

export function startBingoHunt(s: GameState, targetId: string, ninjaIds: number[], biome: HuntBiome = "forest"): { ok: boolean; error?: string; run?: HuntRunState } {
  const bingo = ensureBingoState(s) as BingoRuntimeState;
  if (bingo.activeHunt) return { ok: false, error: "A Bingo hunt is already active." };
  const target = BINGO_TARGET_BY_ID[targetId];
  const progress = bingo.targets[targetId];
  if (!target || !progress) return { ok: false, error: "Target dossier not found." };
  if (!progress.locationKnown && progress.status !== "escaped") return { ok: false, error: "The target has not been located yet." };
  const ids = [...new Set(ninjaIds)];
  if (ids.length !== BINGO_ACTIVE_PARTY_SIZE) return { ok: false, error: `Select exactly ${BINGO_ACTIVE_PARTY_SIZE} active ninjas.` };
  const squad = ids.map((id) => s.ninjas.find((n) => n.id === id)).filter((n): n is Ninja => !!n);
  if (squad.length !== BINGO_ACTIVE_PARTY_SIZE || squad.some((n) => n.status !== "ready")) return { ok: false, error: "Every hunter must be ready." };

  const seed = (Date.now() ^ (targetId.length * 2654435761) ^ (s.day * 104729)) >>> 0;
  const run = createHuntRun(targetId, ids, progress.intel, biome, seed);
  bingo.activeHunt = run;
  progress.status = "active_hunt";
  progress.attempts += 1;
  for (const n of squad) {
    n.status = "mission";
    n.daysLeft = 0;
    n.missionId = null;
  }
  s.log.push({ txt: `${squad.map((n) => n.name.split(" ")[0]).join(", ")} begin the hunt for ${target.name} ${target.epithet}.`, kind: "info", id: Date.now() });
  return { ok: true, run };
}

export function currentHuntEvent(s: GameState): HuntEventDef | null {
  const run = activeBingoHunt(s);
  if (!run) return null;
  const target = BINGO_TARGET_BY_ID[run.targetId];
  if (!target || run.stage >= huntEventCount(target)) return null;
  return rollHuntEvent(run);
}

function recordEvent(run: HuntRunState, ev: HuntEventDef, effect: HuntChoiceEffect): void {
  if (!run.eventIds.includes(ev.id)) run.eventIds.push(ev.id);
  run.notes.push(`${ev.title}: ${effect.result}`);
  run.stage += 1;
}

export function resolveCurrentHuntEvent(s: GameState, choiceIndex = 0): { ok: boolean; error?: string; result?: string; success?: boolean } {
  const run = activeBingoHunt(s);
  const ev = currentHuntEvent(s);
  if (!run || !ev) return { ok: false, error: "No unresolved hunt event." };
  let effect: HuntChoiceEffect | null = null;
  let success: boolean | undefined;
  if (ev.check) {
    const checked = resolveSkillCheck(s, run, ev, run.stage + 1);
    if (!checked) return { ok: false, error: "Unable to resolve skill check." };
    effect = checked.effect;
    success = checked.success;
  } else if (ev.choices?.length) {
    effect = ev.choices[Math.max(0, Math.min(ev.choices.length - 1, choiceIndex))];
  } else if (ev.effect) {
    effect = ev.effect;
  }
  if (!effect) return { ok: false, error: "This event has no valid outcome." };
  applyHuntEffect(run, effect, run.stage + choiceIndex + 11);
  recordEvent(run, ev, effect);
  return { ok: true, result: effect.result, success };
}

export function huntReadyForBoss(s: GameState): boolean {
  const run = activeBingoHunt(s);
  if (!run) return false;
  const target = BINGO_TARGET_BY_ID[run.targetId];
  return !!target && run.stage >= huntEventCount(target);
}

export function abandonBingoHunt(s: GameState): boolean {
  const bingo = ensureBingoState(s) as BingoRuntimeState;
  const run = bingo.activeHunt;
  if (!run) return false;
  const progress = bingo.targets[run.targetId];
  for (const member of run.members) {
    const n = s.ninjas.find((x) => x.id === member.ninjaId);
    if (n && n.status === "mission" && n.missionId == null) {
      n.status = "ready";
      n.daysLeft = 0;
    }
  }
  if (progress) {
    progress.status = "escaped";
    progress.locationKnown = false;
    progress.intel = Math.max(40, progress.intel - 8);
  }
  bingo.activeHunt = null;
  s.log.push({ txt: "The hunter cell abandoned the pursuit. The target has relocated, but most dossier intelligence remains valid.", kind: "bad", id: Date.now() });
  return true;
}

export function syncHuntIntelToDossier(s: GameState): void {
  const run = activeBingoHunt(s);
  if (!run) return;
  const progress = ensureBingoState(s).targets[run.targetId];
  if (progress && run.intel > progress.intel) progress.intel = Math.min(100, run.intel);
}

export { HUNT_EVENTS };
