from pathlib import Path
import re

ROOT = Path('app')

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')
def write(rel, s):
    p=ROOT/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding='utf-8')

# TS target compatibility fix from v1.
p='src/components/JutsuTree.tsx'; s=read(p)
s=s.replace('j.target.replaceAll("_", " ")','j.target.replace(/_/g, " ")')
write(p,s)

# Mission/report/state metadata for special contracts.
p='src/game/types.ts'; s=read(p)
if 'specialId?: string;' not in s:
    s=s.replace('  squad: number[];\n}', '''  squad: number[];\n  /** Special missions always require a warning/review before deployment. */\n  specialId?: string;\n  specialWarning?: string;\n  specialRewardLabel?: string;\n  specialRewardKind?: "potential" | "trait" | "unlock" | "jutsu";\n  specialRewardId?: string;\n}''',1)
if 'specialReward?: string;' not in s:
    s=s.replace('  xp: ReportXp[];\n}', '  xp: ReportXp[];\n  specialReward?: string;\n}',1)
if 'specialUnlocks?: string[];' not in s:
    s=s.replace('  reports: Report[];\n}', '  reports: Report[];\n  /** Permanent discoveries earned from special missions. */\n  specialUnlocks?: string[];\n}',1)
write(p,s)

# Replace special mission data with a broad D-S catalogue.
special_ts = r'''import type { Nature, Rank, Skill, TraitId } from "./types";

export type SpecialReward =
  | { kind: "potential"; amount: 1; maxPerNinja: 2 }
  | { kind: "trait"; trait: TraitId }
  | { kind: "unlock"; key: string }
  | { kind: "jutsu"; jutsuId: string };

export interface SpecialMissionDef {
  id: string;
  name: string;
  grade: Rank;
  desc: string;
  warning: string;
  focus: Skill[];
  slots: number;
  reward: SpecialReward;
  requiredNature?: Nature;
}

export const SPECIAL_MISSIONS: SpecialMissionDef[] = [
  { id: "academy_prodigy_assessment", name: "Academy Prodigy Assessment", grade: "D", desc: "An academy examiner wants one shinobi tested beyond the normal curriculum.", warning: "UNUSUAL TRAINING: the participant will be judged alone. Success permanently grants Quick Learner if they do not already have it.", focus: ["tac", "nin"], slots: 1, reward: { kind: "trait", trait: "quickLearner" } },
  { id: "veterans_survival_course", name: "Veteran's Survival Course", grade: "C", desc: "An old field captain offers a brutal three-day survival assessment.", warning: "HARD TRAINING: failure may cause injury. Success permanently grants Field Survivor.", focus: ["ste", "tai", "med"], slots: 1, reward: { kind: "trait", trait: "fieldSurvivor" } },
  { id: "breakthrough_trial", name: "The Breakthrough Trial", grade: "B", desc: "A sealed training ground is opened for a single shinobi to push beyond their natural ceiling.", warning: "EXTREME TRAINING: failure can cause a long injury. Success raises natural Potential by 1. A ninja can gain at most 2 Potential this way and cannot exceed 5★.", focus: ["tai", "nin", "tac"], slots: 1, reward: { kind: "potential", amount: 1, maxPerNinja: 2 } },
  { id: "night_hunter_oath", name: "Night Hunter's Oath", grade: "B", desc: "A covert order tests candidates in a live infiltration exercise.", warning: "COVERT TRIAL: discovery triggers an elite pursuit force. Success permanently grants Night Operative.", focus: ["ste", "spd", "tac"], slots: 1, reward: { kind: "trait", trait: "nightOperative" } },
  { id: "duelists_mark", name: "The Duelist's Mark", grade: "B", desc: "A wandering sword master offers one formal challenge at the old bridge.", warning: "SINGLE COMBAT: failure is likely to injure the challenger. Success permanently grants Duelist.", focus: ["ken", "spd", "tac"], slots: 1, reward: { kind: "trait", trait: "duelist" } },
  { id: "ancient_chakra_path", name: "Ancient Chakra Path", grade: "A", desc: "A ruined shrine contains a chakra-pressure route once used by elite clans.", warning: "FORBIDDEN SITE: unstable chakra conditions may injure or permanently alter the participant. Success grants Dense Chakra.", focus: ["nin", "med", "tac"], slots: 1, reward: { kind: "trait", trait: "chakraDense" } },
  { id: "thunder_master", name: "Audience with the Thunder Master", grade: "A", desc: "A hermit agrees to teach one lightning-nature shinobi who survives the approach.", warning: "ELEMENT LOCKED: only a Lightning-nature participant can claim Flash Step Strike. Special missions never quick-deploy; choose the recipient deliberately.", focus: ["nin", "spd", "tac"], slots: 1, reward: { kind: "jutsu", jutsuId: "light_flash" }, requiredNature: "light" },
  { id: "village_barrier_secret", name: "The Buried Barrier Formula", grade: "A", desc: "A collapsed archive may contain a lost village-scale barrier formula.", warning: "ANCIENT RUINS: success permanently unlocks Barrier Research for future village development.", focus: ["nin", "gen", "tac"], slots: 3, reward: { kind: "unlock", key: "barrier_research" } },
  { id: "legendary_breakthrough", name: "The Legendary Mentor's Challenge", grade: "S", desc: "A nameless veteran offers one final test to a shinobi already near the limits of ordinary training.", warning: "EXTREME S-RANK TRAINING: failure causes severe injury. Success raises natural Potential by 1, subject to the normal 2-raise/5★ cap.", focus: ["tac", "nin", "tai", "spd"], slots: 1, reward: { kind: "potential", amount: 1, maxPerNinja: 2 } },
  { id: "war_hero_trial", name: "Trial of the War Hero", grade: "S", desc: "A veteran order stages a live battlefield exercise against overwhelming odds.", warning: "LIVE-FIRE EXERCISE: serious injury is expected on failure. Success permanently grants Battle Hardened.", focus: ["tac", "ken", "med", "nin"], slots: 2, reward: { kind: "trait", trait: "battleHardened" } },
];

export const SPECIAL_BY_ID: Record<string, SpecialMissionDef> = Object.fromEntries(SPECIAL_MISSIONS.map((m) => [m.id, m]));

export function specialRewardLabel(def: SpecialMissionDef): string {
  const r = def.reward;
  if (r.kind === "potential") return "+1 NATURAL POTENTIAL";
  if (r.kind === "trait") return `UNIQUE TRAIT: ${r.trait}`;
  if (r.kind === "jutsu") return `UNIQUE JUTSU: ${r.jutsuId}`;
  return `VILLAGE UNLOCK: ${r.key}`;
}

export function specialRecipientEligible(def: SpecialMissionDef, n: { pot: number; potentialRaises?: number; nature: Nature; secondaryNature?: Nature | null }): boolean {
  if (def.requiredNature && n.nature !== def.requiredNature && n.secondaryNature !== def.requiredNature) return false;
  if (def.reward.kind === "potential" && (n.pot >= 5 || (n.potentialRaises ?? 0) >= def.reward.maxPerNinja)) return false;
  return true;
}
'''
write('src/game/specialMissions.ts', special_ts)

# Every normal/special title gets its own report framing.
mission_reports_ts = r'''export interface MissionReportBeat { open: string; win: string; fail: string; }

const B: Record<string, MissionReportBeat> = {
  "Find the Lost Cat Tama": { open: "Tama's owner swore the cat had vanished into the roof district again.", win: "Tama was cornered above the dye shop and returned with only minor scratches to the retrieval team.", fail: "Tama escaped across the tiles at the last moment; the embarrassed cell returned without the cat." },
  "Weed the Elder's Garden": { open: "The elder marked every weed with red string and watched from the veranda.", win: "The beds were cleared before sunset, including the hornet nest hidden beneath the squash vines.", fail: "The work went badly after the hornets were disturbed; half the garden remains untouched." },
  "Deliver the Sealed Letter": { open: "The sealed letter was placed inside a waxed inner pouch and timed at the gate.", win: "The message reached its recipient with the seal unbroken and ahead of the requested time.", fail: "A road delay made the delivery late; the letter arrived, but the contract conditions were not met." },
  "Patch Up the Academy Class": { open: "An academy sparring lesson ended with more blood than the instructor expected.", win: "Every student was treated, calmed and returned to their families before dusk.", fail: "The clinic was overwhelmed and outside help had to be called in; the village forfeited the fee." },
  "Dōjō Blade Drill": { open: "The academy floor was lined with wooden swords and very nervous first-years.", win: "The drill ended with bruises, better footwork and no serious injuries.", fail: "The lesson broke down into chaos and the instructor ended the session early." },
  "Scare Off Mushroom Thieves": { open: "Fresh footprints led from the mushroom sheds toward the eastern ditch.", win: "The thieves abandoned their sacks and fled before a real fight was needed.", fail: "The thieves slipped away with another night's harvest before the cell could corner them." },
  "Repair the South Footbridge": { open: "Carpenters began work while the cell watched both banks of the river.", win: "The bridge reopened by dusk and the workers finished without interruption.", fail: "Repeated harassment drove the workers off the site; repairs will need another day." },
  "Catch the Runaway Messenger Hawk": { open: "The missing hawk was last seen circling the old bell tower with a coded strip still attached.", win: "The hawk was coaxed down and the message recovered intact.", fail: "The bird vanished beyond the tree line before the cell could bring it down safely." },
  "Guard the Festival Lanterns": { open: "Hundreds of paper lanterns turned the market street into a maze of light and blind corners.", win: "The saboteurs were spotted before they could start a fire and the festival continued uninterrupted.", fail: "Several lantern frames were destroyed before the culprits escaped into the crowd." },
  "Clear the Training Grounds": { open: "Broken targets, old wire traps and scorched posts littered the academy grounds.", win: "The grounds were made safe before the morning class arrived.", fail: "A concealed trap injured a worker and the grounds remained closed." },
  "Escort the Tea Merchant": { open: "The tea wagons left at first light with scouts watching the wooded shoulders of the road.", win: "An ambush was broken before the bandits reached the wagons; every crate arrived intact.", fail: "Bandits scattered the convoy and made off with enough cargo to void the escort contract." },
  "Catch the Rice Thief": { open: "Loose grains formed a trail between the storehouse and the canal roofs.", win: "The thief was caught at a hidden cache beneath the old mill.", fail: "The trail was lost at the canal and the stolen rice was not recovered." },
  "Break the Illusion Trap": { open: "Travellers described the same impossible bamboo road appearing where no road should be.", win: "The illusion anchor was found and broken, restoring the true road before another caravan arrived.", fail: "The cell became caught in the false route and withdrew before the trap could close completely." },
  "Field Clinic at the Ford": { open: "A fever camp had formed beside the ford with supplies already running short.", win: "The sick were stabilised and the source of the fever isolated before it spread upriver.", fail: "The clinic ran out of time and medicine; regional healers took over the camp." },
  "Map the Northern Pass": { open: "The survey team entered the pass with rope, ink and strict instructions to mark every choke point.", win: "A complete route map returned, including two hidden paths and a dangerous rockfall zone.", fail: "Bad weather forced the survey back with only a partial map." },
  "Challenge the Roadside Duelist": { open: "The duelist waited beside the milestone, sword already drawn but point lowered.", win: "The challenge ended cleanly and the duelist agreed to leave village travellers alone.", fail: "The challenger was beaten and the duelist kept control of the road for another day." },
  "Guard the Shrine Procession": { open: "The shrine procession moved slowly through streets too narrow for a conventional guard formation.", win: "Pickpockets and would-be attackers were intercepted without breaking the procession.", fail: "The crowd split the escort and thieves reached the offering chests." },
  "Investigate the Empty Village": { open: "No smoke rose from the farming settlement when the cell reached the ridge above it.", win: "The villagers were found hiding from raiders in irrigation tunnels and escorted back safely.", fail: "The settlement yielded clues but no survivors or clear answer before the cell withdrew." },
  "Drive Off the River Pirates": { open: "Three low pirate boats were sighted using the reed islands as cover.", win: "The pirate crews were driven from the river and two stolen barges recovered.", fail: "The pirates escaped downstream after damaging another merchant barge." },
  "Recover the Stolen Medicine": { open: "Broken crate slats and medicinal powder marked the route of the stolen shipment.", win: "The medicine was recovered before heat spoiled the most fragile supplies.", fail: "The thieves destroyed the shipment when cornered, leaving nothing usable to recover." },
  "Infiltrate the Bandit Camp": { open: "The bandit camp had doubled its sentries after sunset and changed its challenge signs.", win: "The cell identified the commanders, stores and escape routes without exposing the infiltration.", fail: "A sentry challenged the wrong disguise and the cell fought its way out before the camp could close around them." },
  "Retrieve the Stolen Scroll": { open: "The stolen scroll's seal was designed to survive theft, but not prolonged tampering.", win: "The scroll was recovered with every seal intact and returned directly to the archive.", fail: "The thieves moved the scroll before the cell reached the hideout; its location is unknown again." },
  "Duel the Rogue Swordsman": { open: "The missing-nin chose an abandoned bridge where only two people could stand abreast.", win: "The rogue swordsman was defeated and their blade taken into village custody.", fail: "The swordsman broke the cell's formation and escaped into the gorge." },
  "Sabotage the Storehouse": { open: "Enemy stores were guarded by patrols whose routes overlapped every seven minutes.", win: "The supports were cut and the supplies destroyed after the cell was already clear of the perimeter.", fail: "An alarm forced an early withdrawal; the storehouse survived." },
  "Rescue the Poisoned Caravan": { open: "The caravan's distress flare was visible above the trees before the cell reached the road.", win: "Antidote was administered in time and the survivors were escorted home.", fail: "The poison progressed too quickly and the cell could only recover part of the cargo." },
  "Intercept the Border Couriers": { open: "Two couriers were expected to cross the border markers before moonrise.", win: "Both dispatches were captured before either courier could destroy them.", fail: "One courier broke through the interception line and carried the message onward." },
  "Destroy the Hidden Bridge": { open: "The bridge could only be seen from below the ravine, hidden by woven camouflage.", win: "Its main supports were destroyed and the enemy reinforcement route collapsed with them.", fail: "The demolition team was spotted before charges could be placed." },
  "Expose the False Magistrate": { open: "The magistrate's handwriting, habits and household staff all appeared correct at first inspection.", win: "A contradiction in the official seals exposed the infiltrator and the real magistrate's location was recovered.", fail: "The evidence remained circumstantial and the suspect disappeared before a second interview." },
  "Hunt the Marsh Beast": { open: "Patrol tracks ended abruptly in water too shallow to hide anything that large.", win: "The beast was tracked to its nest and driven away from the patrol route.", fail: "The marsh swallowed the trail and the creature struck again during the withdrawal." },
  "Protect the Defecting Informant": { open: "The informant arrived early, terrified and already convinced they had been followed.", win: "The pursuit team was misdirected and the informant reached the extraction point alive.", fail: "The escort was compromised and the informant vanished during the fighting." },
  "Silence the War-Horn Tower": { open: "The horn tower could warn three forts within seconds of a signal fire.", win: "The horn mechanism was disabled without a signal leaving the tower.", fail: "A sentry reached the horn before the cell could stop the alarm." },
  "Steal the Fox Lord's Ledger": { open: "The Fox Lord kept the ledger inside a private wing guarded by servants who knew one another by name.", win: "The ledger was copied and replaced before its absence could be noticed.", fail: "The estate locked down and the cell abandoned the ledger to escape unseen." },
  "Extract the Captured Scout": { open: "Interrogation was scheduled to begin before dawn, leaving only one viable extraction window.", win: "The scout was removed from custody and stabilised before crossing friendly lines.", fail: "The prison wing sealed before the cell reached the captive." },
  "Hunt the Missing-nin": { open: "The missing-nin had begun selling route maps only village operatives should know.", win: "The traitor was cornered before the next exchange and the stolen route book recovered.", fail: "A prepared escape route let the target disappear moments before capture." },
  "Read the Crimson Eye": { open: "Every previous ambush had failed as though the target had seen it before it happened.", win: "The cell baited the ocular technique into a false read and finally broke the target's prediction loop.", fail: "The Crimson Eye read the formation too quickly and forced the cell into retreat." },
  "Break the Siege Engineers": { open: "The siege train moved under heavy escort and could reach allied walls by the next night.", win: "The engines burned before they could be deployed and the surviving crews scattered.", fail: "The escort held long enough for the siege train to reach the protected road." },
  "Escort the Daimyo's Envoy": { open: "The envoy refused to delay negotiations despite three separate assassination warnings.", win: "The convoy survived two attacks and delivered the envoy to the negotiating hall on time.", fail: "The route became untenable and the envoy was forced to turn back under guard." },
  "Capture the Poison Master": { open: "The target carried enough toxins to kill themselves, the cell and any careless pursuer.", win: "The Poison Master was restrained alive with their antidote kit intact.", fail: "A cloud of toxin covered the target's escape and forced immediate medical withdrawal." },
  "Raid the Hidden Arsenal": { open: "The arsenal was built beneath a dye warehouse with weapons moving out every hour.", win: "The stockpile was seized and the tunnel exits collapsed behind the retreating cell.", fail: "The guards moved the most valuable weapons before the raid reached the vault." },
  "Hold the Mountain Gate": { open: "Refugees were still crossing the pass when enemy scouts appeared below the gate.", win: "The cell held until the last civilians cleared the ridge, then withdrew in order.", fail: "The line broke early and the evacuation scattered into secondary routes." },
  "Storm the Obsidian Keep": { open: "The keep's black walls had never been breached in a direct assault.", win: "The inner gate fell before the defenders could reorganise and the keep was taken by dawn.", fail: "The assault reached the inner wall but could not hold the breach." },
  "Steal the Shogun's Seal": { open: "The seal never left the Shogun's inner apartments except during formal audiences.", win: "The seal was removed, copied and replaced without the palace understanding how close the breach had come.", fail: "The palace entered full lockdown before the cell reached the inner chambers." },
  "The Nine-Tailed Contract": { open: "The contract chamber was sealed with bindings older than the current village system.", win: "The contract was secured and resealed for transport without triggering its final ward.", fail: "The warding pattern destabilised and forced the cell to abandon the chamber." },
  "Sever the Serpent's Head": { open: "The Serpent commander moved headquarters every night and executed anyone who learned the next location.", win: "The command tent was found and the Serpent's chain of command collapsed before sunrise.", fail: "A decoy headquarters bought the commander enough time to escape." },
  "Mirror-Eye Conspiracy": { open: "Deployment orders were being anticipated before they left the village, pointing to a network rather than one spy.", win: "The Mirror-Eye relay was exposed and its observers captured in a coordinated sweep.", fail: "The network burned its safe houses and disappeared before the cell could close the circle." },
  "Break the Five-Fortress Line": { open: "Five forts covered one another so precisely that attacking any single position strengthened the other four.", win: "The cell disrupted the relay timing and opened a corridor through the entire defensive line.", fail: "The forts recovered their coordination faster than expected and sealed the breach." },
  "Recover the Forbidden Archive": { open: "The underground archive was already collapsing when its outer seals finally opened.", win: "The core records were extracted moments before the lower vault disappeared beneath the rubble.", fail: "The collapse cut off the central archive and the cell escaped with only fragments." },
  "Defend the Kage Summit": { open: "The summit hall was already compromised; the assassins had entered before the leaders arrived.", win: "The assassination force was isolated and every protected leader survived the summit.", fail: "The attackers forced an emergency evacuation and the summit ended without agreement." },
  "Hunt the Living Weapon": { open: "The target's chakra signature registered more like a siege engine than a human shinobi.", win: "The Living Weapon was subdued without allowing the altered chakra system to detonate.", fail: "The target broke containment and disappeared after levelling the pursuit route." },
  "End the Silent War": { open: "The covert network had operated inside allied territory long enough to become part of the landscape.", win: "Safe houses, handlers and compromised officials were struck in one night, ending the network before it could scatter.", fail: "The first arrest alerted the remaining cells and the Silent War vanished back underground." },
  "Academy Prodigy Assessment": { open: "The academy examiner cleared the training hall and admitted only one candidate.", win: "The examiner signed the candidate's record with a rare recommendation for accelerated study.", fail: "The candidate was stopped before the final exercise and sent home to recover." },
  "Veteran's Survival Course": { open: "The veteran took away the candidate's map, spare food and every comfort item before opening the gate.", win: "The candidate returned under their own power and earned the veteran's field mark.", fail: "A recovery team found the candidate before the course's final marker." },
  "The Breakthrough Trial": { open: "The sealed ground closed behind the candidate; no instructor entered with them.", win: "The candidate emerged with their chakra pattern measurably changed by the ordeal.", fail: "The trial ended in exhaustion and injury before the breakthrough point was reached." },
  "Night Hunter's Oath": { open: "The covert order gave the candidate a target, a time and no extraction plan.", win: "The target marker was returned without a single alarm being raised.", fail: "The pursuit force identified the candidate and drove them out before completion." },
  "The Duelist's Mark": { open: "The sword master drew a circle in the dust and asked the challenger to step inside alone.", win: "The master lowered their blade first and awarded the Duelist's Mark.", fail: "The challenger was disarmed before landing a decisive strike." },
  "Ancient Chakra Path": { open: "Each stone on the ruined path pressed harder against the candidate's chakra network.", win: "The candidate reached the final shrine and returned with a denser, more stable chakra flow.", fail: "The pressure became unsafe and the candidate was pulled from the path before permanent damage." },
  "Audience with the Thunder Master": { open: "Lightning struck the hermit's ridge often enough that every tree bore a black scar.", win: "The Thunder Master demonstrated Flash Step Strike once, then made the student reproduce it under live lightning.", fail: "The master ended the lesson after the candidate failed to control the discharge safely." },
  "The Buried Barrier Formula": { open: "The archive entrance was found beneath three generations of collapsed foundation stone.", win: "The complete barrier formula was recovered and copied into the village research archive.", fail: "The inner chamber collapsed before the formula could be fully transcribed." },
  "The Legendary Mentor's Challenge": { open: "The mentor refused introductions and began the test the moment the candidate arrived.", win: "The mentor finally smiled; the candidate had pushed past a limit everyone else treated as fixed.", fail: "The mentor stopped the fight before the candidate destroyed themselves chasing the breakthrough." },
  "Trial of the War Hero": { open: "The exercise began with the candidates already surrounded and outnumbered.", win: "The veterans accepted the candidates into their order after they held the field under impossible pressure.", fail: "The formation broke before the final wave and the exercise was called." },
};

export function missionReportBeat(name: string): MissionReportBeat | undefined { return B[name]; }
'''
write('src/game/missionReports.ts', mission_reports_ts)

# MissionBoard grade-first rewrite.
mission_board = r'''import { useState } from "react";
import { ArrowLeft, Coins, Lock, ScrollText, ShieldAlert, Sun, Users, Wheat } from "lucide-react";
import type { GameState, Mission, Rank, Skill } from "../game/types";
import { RANK_COLOR, RANK_KANJI, RANK_META, SKILL_META } from "../game/content";
import { autoSquad, coverage, meetsRank, squadChance, squadOf } from "../game/engine";
import NinjaSprite from "./NinjaSprite";
import { cn } from "../utils/cn";

export function chanceColor(c: number): string { return c >= 0.75 ? "text-jade" : c >= 0.5 ? "text-gold" : "text-vermil"; }
type Folder = Rank | "SPECIAL";
const FOLDERS: Folder[] = ["D", "C", "B", "A", "S", "SPECIAL"];

export default function MissionBoard({ s, className, onOpen, onQuick }: { s: GameState; className?: string; onOpen: (id: number) => void; onQuick: (id: number, r: DOMRect) => void; }) {
  const [folder, setFolder] = useState<Folder | null>(null);
  const open = s.missions.filter((m) => m.squad.length === 0);
  const running = s.missions.filter((m) => m.squad.length > 0);
  const inFolder = folder ? open.filter((m) => folder === "SPECIAL" ? !!m.specialId : !m.specialId && m.rank === folder) : [];

  return (
    <section className={cn("panel flex min-h-0 flex-col", className)}>
      <header className="panel-h"><span className="p-kanji">任</span><span className="panel-title">Mission Board</span><span className="ml-auto rounded-md bg-black/30 px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-paper/60">{open.length} open · {running.length} out</span></header>
      <div className="scroller min-h-0 flex-1 space-y-2 overflow-y-auto p-2">
        {folder === null ? <>
          {running.length > 0 && <div className="mb-1 text-[9px] font-black tracking-[0.2em] text-paper/40">ACTIVE MISSIONS</div>}
          {running.map((m) => <RunningMission key={m.id} s={s} m={m} />)}
          <div className="pt-1 text-[9px] font-black tracking-[0.2em] text-paper/40">CHOOSE MISSION GRADE</div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">{FOLDERS.map((f) => { const missions=open.filter((m)=>f==="SPECIAL"?!!m.specialId:!m.specialId&&m.rank===f); const special=f==="SPECIAL"; const color=special?"#d6a4ff":RANK_COLOR[f as Rank]; return <button key={f} onClick={()=>setFolder(f)} className={cn("min-h-[92px] rounded-xl bg-black/25 p-3 text-left ring-1 transition active:scale-[0.98]",special?"ring-[#d6a4ff]/25":"ring-white/7")}><div className="flex items-start justify-between gap-2"><span className="grid h-9 w-9 place-items-center rounded-lg font-display text-sm font-black text-white" style={{backgroundColor:color}}>{special?"特":f}</span><span className="rounded-md bg-black/30 px-2 py-1 text-[10px] font-black tabular-nums" style={{color}}>{missions.length} OPEN</span></div><p className="mt-2 text-[11px] font-black text-paper/90">{special?"Special Missions":`${f}-Rank Missions`}</p><p className="mt-0.5 text-[8.5px] leading-relaxed text-paper/40">{special?"Rare contracts with permanent rewards, unique traits, techniques or unlocks.":missions.length?"Open this grade to inspect individual contracts.":"No contracts at this grade today."}</p></button>})}</div>
          {open.length===0&&running.length===0&&<Empty/>}
        </> : <>
          <button onClick={()=>setFolder(null)} className="mb-1 inline-flex h-8 items-center gap-1.5 rounded-lg bg-black/25 px-2.5 text-[9.5px] font-black tracking-wider text-paper/65 ring-1 ring-white/8"><ArrowLeft size={12}/> BACK TO GRADES</button>
          <div className="mb-1 flex items-center gap-2"><span className="text-[10px] font-black tracking-[0.18em] text-paper/55">{folder==="SPECIAL"?"SPECIAL MISSIONS":`${folder}-RANK CONTRACTS`}</span><span className="rounded bg-black/30 px-1.5 py-0.5 text-[9px] font-bold text-paper/40">{inFolder.length}</span></div>
          {inFolder.length===0?<Empty text="No contracts in this folder — end the day for new work."/>:inFolder.map((m,idx)=><OpenMission key={m.id} s={s} m={m} idx={idx} onOpen={onOpen} onQuick={onQuick}/>) }
        </>}
      </div>
    </section>
  );
}

function RunningMission({s,m}:{s:GameState;m:Mission}) { const squad=squadOf(s,m); const pct=100*(1-m.days/m.totalDays); return <article id={`mission-${m.id}`} className="scroll-card running" style={{"--rc":RANK_COLOR[m.rank]} as React.CSSProperties}><Seal rank={m.rank} special={!!m.specialId}/><div className="min-w-0 flex-1"><div className="flex items-center gap-1"><div className="flex -space-x-1">{squad.map((n)=><span key={n.id} className="overflow-hidden rounded-full bg-black/50 ring-1 ring-white/15"><NinjaSprite n={n} h={20}/></span>)}</div><h4 className="ml-1 truncate text-[12px] font-bold text-paper/90">{m.name}</h4></div><div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-black/45"><div className="h-full rounded-full bg-gradient-to-r from-[var(--rc)] to-white/70" style={{width:`${pct}%`}}/></div></div><div className="flex w-14 shrink-0 flex-col items-end justify-center"><span className="text-[13px] font-black tabular-nums text-paper/85">{m.days}d</span><span className="text-[8.5px] tracking-wider text-paper/45">REMAINING</span></div></article>; }

function OpenMission({s,m,idx,onOpen,onQuick}:{s:GameState;m:Mission;idx:number;onOpen:(id:number)=>void;onQuick:(id:number,r:DOMRect)=>void}) { const auto=autoSquad(s,m); const autoN=auto.map((id)=>s.ninjas.find((n)=>n.id===id)!).filter(Boolean); const ch=squadChance(s,m,autoN); const cov=coverage(s,m,autoN); const daysLeft=m.expiresDay-s.day; const expiring=daysLeft<=1; const rankOk=autoN.length>0&&meetsRank(m,autoN); const rm=RANK_META[m.minRank]; const special=!!m.specialId; return <article id={`mission-${m.id}`} className={cn("scroll-card pop-in flex-col !items-stretch",m.rank==="S"&&"rank-s",expiring&&"expiring",special&&"ring-1 ring-[#d6a4ff]/25")} style={{"--rc":RANK_COLOR[m.rank]} as React.CSSProperties}><div className="flex items-center gap-2"><Seal rank={m.rank} special={special}/><div className="min-w-0 flex-1"><div className="flex items-center gap-1"><h4 className="truncate text-[12.5px] font-bold text-[#2b2118]">{m.name}</h4>{special&&<span className="rounded bg-[#6c3a86]/15 px-1.5 py-0.5 text-[8px] font-black text-[#6c3a86]">SPECIAL</span>}</div><div className="mt-0.5 flex flex-wrap items-center gap-x-2 text-[10px] font-semibold text-[#5c4c3a]"><span className="inline-flex items-center gap-0.5"><Users size={10}/>{m.slots}-man</span><span className="inline-flex items-center gap-0.5"><Sun size={10}/>{m.totalDays}d</span><span className="inline-flex items-center gap-0.5 text-[#8a6a1d]"><Coins size={10}/>{m.gold}</span>{m.rice>0&&<span className="inline-flex items-center gap-0.5 text-[#4d7a35]"><Wheat size={10}/>{m.rice}</span>}<span className={cn(expiring?"font-bold text-vermil":"text-[#7a6a55]")}>{daysLeft<=0?"last day":`${daysLeft}d left`}</span></div></div></div>{special&&<div className="mt-1.5 rounded-lg bg-[#6c3a86]/8 px-2 py-1.5 ring-1 ring-[#6c3a86]/15"><p className="flex items-center gap-1 text-[8px] font-black tracking-wider text-[#6c3a86]"><ShieldAlert size={10}/> PERMANENT REWARD</p><p className="mt-0.5 text-[9.5px] font-black text-[#3d2948]">{m.specialRewardLabel}</p></div>}<div className="mt-1.5 flex flex-wrap gap-1"><span className={cn("inline-flex items-center gap-1 rounded-md px-1.5 py-[3px] text-[9.5px] font-bold",rankOk?"bg-[#2f6b45]/12 text-[#2f6b45]":"bg-[#a33a2a]/12 text-[#a33a2a]")} title={`Requires a ${rm.name} or higher in the cell`}>{!rankOk&&<Lock size={9}/>}<b className="font-display">{rm.kanji}</b>{rm.name}+</span>{cov.map((c)=>{const meta=SKILL_META[c.k as Skill]; const ok=c.cov>=1; return <span key={c.k} className={cn("inline-flex items-center gap-1 rounded-md px-1.5 py-[3px] text-[9.5px] font-bold tabular-nums",ok?"bg-[#2f6b45]/15 text-[#2f6b45]":"bg-[#a33a2a]/12 text-[#a33a2a]")} style={{boxShadow:`inset 0 0 0 1px ${meta.color}55`}}><b style={{color:meta.color}} className="font-display">{meta.kanji}</b>{meta.short}<span className="opacity-70">{Math.round(c.have)}/{c.need}</span></span>})}</div><div className="mt-1.5 flex items-center gap-1.5"><span className={cn("rounded-md bg-black/10 px-1.5 py-1 text-[10px] font-black tabular-nums",chanceColor(ch),auto.length===0&&"text-[#8a7a68]")}>{auto.length?`${Math.round(ch*100)}%`:"NO CELL"}</span><button onClick={()=>onOpen(m.id)} className="btn-ink h-8 flex-1 rounded-lg text-[10.5px] font-black tracking-wider">{special?"⚠ REVIEW + SELECT":"編成 SELECT SQUAD"}</button>{!special&&<button disabled={auto.length===0} onClick={(e)=>onQuick(m.id,e.currentTarget.getBoundingClientRect())} className="btn-primary relative h-8 w-[74px] shrink-0 rounded-lg text-[10.5px] font-black tracking-wider">派遣{idx>=0&&idx<9&&<kbd className="kbd">{idx+1}</kbd>}</button>}</div></article>; }

function Empty({text="No contracts — end the day for new work."}:{text?:string}) { return <div className="flex min-h-24 flex-col items-center justify-center gap-2 text-paper/40"><ScrollText size={22} className="opacity-50"/><p className="text-center text-[11px]">{text}</p></div>; }
function Seal({rank,special=false}:{rank:Mission["rank"];special?:boolean}) { return <div className="seal-col" style={{backgroundColor:special?"#6c3a86":`color-mix(in srgb, ${RANK_COLOR[rank]} 88%, black)`}}><span className="font-display text-[13px] font-black leading-none text-white drop-shadow">{special?"特":rank}</span><span className="font-display text-[9px] leading-none text-white/70">{special?rank:RANK_KANJI[rank]}</span></div>; }
'''
write('src/components/MissionBoard.tsx', mission_board)

# Squad warning + special eligibility/confirmation copy.
p='src/components/SquadModal.tsx'; s=read(p)
if 'SPECIAL_BY_ID' not in s:
    s=s.replace('import { cn } from "../utils/cn";', 'import { cn } from "../utils/cn";\nimport { SPECIAL_BY_ID, specialRecipientEligible } from "../game/specialMissions";',1)
if 'const specialDef = m?.specialId' not in s:
    s=s.replace('  const cov = m ? coverage(s, m, squad) : [];', '''  const cov = m ? coverage(s, m, squad) : [];\n  const specialDef = m?.specialId ? SPECIAL_BY_ID[m.specialId] : undefined;\n  const specialEligible = !specialDef || specialDef.reward.kind === "unlock" || squad.some((n) => specialRecipientEligible(specialDef, n));''',1)
header_close='''        </div>\n\n        {/* coverage */}'''
if 'SPECIAL MISSION WARNING' not in s:
    warning='''        </div>\n\n        {m.specialId && (\n          <div className="border-b border-[#d6a4ff]/15 bg-[#6c3a86]/10 px-3 py-2.5">\n            <p className="text-[9px] font-black tracking-[0.18em] text-[#d6a4ff]">⚠ SPECIAL MISSION WARNING</p>\n            <p className="mt-1 text-[10.5px] leading-relaxed text-paper/70">{m.specialWarning}</p>\n            <p className="mt-1.5 text-[10px] font-black text-gold">REWARD: {m.specialRewardLabel}</p>\n            {!specialEligible && sel.length > 0 && <p className="mt-1 text-[9.5px] font-black text-vermil">The selected cell contains no eligible recipient for this permanent reward.</p>}\n          </div>\n        )}\n\n        {/* coverage */}'''
    if header_close not in s: raise SystemExit('Squad warning anchor missing')
    s=s.replace(header_close,warning,1)
s=s.replace('if (sel.length) onDeploy(sel);','if (sel.length && specialEligible) onDeploy(sel);')
s=s.replace('            disabled={sel.length === 0}\n            onClick={() => onDeploy(sel)}', '            disabled={sel.length === 0 || !specialEligible}\n            onClick={() => onDeploy(sel)}')
s=s.replace('            出撃 DEPLOY<kbd className="kbd">↵</kbd>', '            {m.specialId ? "⚠ I UNDERSTAND — DEPLOY" : "出撃 DEPLOY"}<kbd className="kbd">↵</kbd>')
write(p,s)

# Engine special generation, reward processing, title-specific reports.
p='src/game/engine.ts'; s=read(p)
if 'missionReportBeat' not in s:
    s=s.replace('import { equipmentSkillBonus } from "./equipment";', 'import { equipmentSkillBonus } from "./equipment";\nimport { missionReportBeat } from "./missionReports";\nimport { SPECIAL_BY_ID, SPECIAL_MISSIONS, specialRecipientEligible, specialRewardLabel } from "./specialMissions";',1)
if 'function genSpecialMission' not in s:
    anchor='export function genMission(s: GameState, forced?: Rank): Mission {'; pos=s.find(anchor)
    if pos<0: raise SystemExit('genMission anchor missing')
    helper=r'''const SPECIAL_UNLOCK_DAY: Record<Rank, number> = { D: 1, C: 2, B: 4, A: 7, S: 11 };

function genSpecialMission(s: GameState): Mission | null {
  const eligible = SPECIAL_MISSIONS.filter((d) => s.day >= SPECIAL_UNLOCK_DAY[d.grade]).filter((d) => !d.requiredNature || s.ninjas.some((n) => n.nature === d.requiredNature || n.secondaryNature === d.requiredNature));
  if (!eligible.length) return null;
  const d = pick(eligible); const spec = MISSION_SPEC[d.grade]; const scale = 1 + (s.day - 1) * 0.03; const req: Partial<Record<Skill, number>> = {};
  d.focus.forEach((k, i) => { const base = ri(spec.req[0], spec.req[1]) * (i === 0 ? 1 : 0.75); req[k] = Math.max(3, Math.round(base * scale * 1.08)); });
  const reward = d.reward;
  return { id: s.nextId++, rank: d.grade, name: d.name, desc: d.desc, req, slots: d.slots, days: spec.days, totalDays: spec.days, gold: Math.round(ri(spec.gold[0], spec.gold[1]) * scale * 1.15), rice: Math.round(ri(spec.rice[0], spec.rice[1]) * scale * 1.15), xp: spec.xp * 1.2, score: Math.round(spec.score * 1.2), expiresDay: s.day + ri(4, 6), minRank: MISSION_MIN_RANK[d.grade], squad: [], specialId: d.id, specialWarning: d.warning, specialRewardLabel: specialRewardLabel(d), specialRewardKind: reward.kind, specialRewardId: reward.kind === "trait" ? reward.trait : reward.kind === "jutsu" ? reward.jutsuId : reward.kind === "unlock" ? reward.key : undefined };
}

function maybeAddSpecialMission(s: GameState): void {
  if (s.missions.some((m) => m.specialId && m.squad.length === 0)) return;
  if (Math.random() >= 0.14) return;
  const special = genSpecialMission(s); if (special) s.missions.push(special);
}

'''
    s=s[:pos]+helper+s[pos:]
if 'function applySpecialReward' not in s:
    marker='const WIN_CLOSERS = ['; pos=s.find(marker)
    if pos<0: raise SystemExit('WIN_CLOSERS anchor missing')
    helper=r'''function applySpecialReward(s: GameState, m: Mission, squad: Ninja[]): string | undefined {
  if (!m.specialId) return undefined;
  const def = SPECIAL_BY_ID[m.specialId]; if (!def) return undefined;
  if (def.reward.kind === "unlock") { const list = s.specialUnlocks ?? (s.specialUnlocks = []); if (!list.includes(def.reward.key)) list.push(def.reward.key); return `Village discovery unlocked: ${m.specialRewardLabel}.`; }
  const recipient = squad.find((n) => specialRecipientEligible(def, n)); if (!recipient) return `No eligible shinobi could receive ${m.specialRewardLabel}.`;
  if (def.reward.kind === "potential") { if (increaseNaturalPotential(recipient)) return `${recipient.name}'s natural Potential increased to ${recipient.pot}★.`; return `${recipient.name} reached the limit of this Potential training.`; }
  if (def.reward.kind === "trait") { if (!recipient.traits.includes(def.reward.trait)) recipient.traits.push(def.reward.trait); return `${recipient.name} gained the permanent trait ${TRAIT_META[def.reward.trait].name}.`; }
  const known = recipient.jutsuKnown ?? (recipient.jutsuKnown = []); if (!known.includes(def.reward.jutsuId)) known.push(def.reward.jutsuId); return `${recipient.name} learned the unique jutsu ${m.specialRewardLabel?.replace("UNIQUE JUTSU: ", "") ?? def.reward.jutsuId}.`;
}

'''
    s=s[:pos]+helper+s[pos:]
s=s.replace('  const lines: ReportLine[] = [];\n  lines.push({ txt: pick(OPENERS), kind: "flavour" });', '  const lines: ReportLine[] = [];\n  const specific = missionReportBeat(m.name);\n  lines.push({ txt: specific?.open ?? pick(OPENERS), kind: "flavour" });')
s=s.replace('  lines.push({ txt: `Odds were read at ${Math.round(ch * 100)}%.`, kind: "beat" });\n  lines.push({ txt: pick(win ? WIN_CLOSERS : LOSS_CLOSERS), kind: "flavour" });', '  lines.push({ txt: `Odds were read at ${Math.round(ch * 100)}%.`, kind: "beat" });\n  if (specific) lines.push({ txt: win ? specific.win : specific.fail, kind: win ? "good" : "bad" });\n  lines.push({ txt: pick(win ? WIN_CLOSERS : LOSS_CLOSERS), kind: "flavour" });')
if 'const specialReward = win ? applySpecialReward' not in s:
    s=s.replace('  s.reports.push({\n    id: reportId++,', '  const specialReward = win ? applySpecialReward(s, m, squad) : undefined;\n  const reportLines = reportFor(s, m, squad, win, ch, cov);\n  if (specialReward) reportLines.push({ txt: specialReward, kind: "clutch" });\n\n  s.reports.push({\n    id: reportId++,',1)
    s=s.replace('    lines: reportFor(s, m, squad, win, ch, cov),\n    xp: xpRows,', '    lines: reportLines,\n    xp: xpRows,\n    specialReward,',1)
if 'maybeAddSpecialMission(s);' not in s:
    s=s.replace('  for (let i = 0; i < want; i++) {\n    if (openMissions(s).length >= missionCap(s)) break;\n    s.missions.push(genMission(s));\n  }\n\n  // 4. economy', '  for (let i = 0; i < want; i++) {\n    if (openMissions(s).length >= missionCap(s)) break;\n    s.missions.push(genMission(s));\n  }\n  maybeAddSpecialMission(s);\n\n  // 4. economy',1)
write(p,s)

# Report reward callout.
p='src/components/ReportModal.tsx'; s=read(p)
if 'SPECIAL REWARD' not in s:
    anchor='          {/* spoils */}\n          {report.win && ('
    block='''          {report.specialReward && (\n            <div className="border-b border-[#d6a4ff]/15 bg-[#6c3a86]/10 px-3 py-2">\n              <p className="text-[8.5px] font-black tracking-[0.18em] text-[#d6a4ff]">SPECIAL REWARD</p>\n              <p className="mt-0.5 text-[10.5px] font-black text-gold">{report.specialReward}</p>\n            </div>\n          )}\n\n          {/* spoils */}\n          {report.win && ('''
    if anchor not in s: raise SystemExit('Report spoils anchor missing')
    s=s.replace(anchor,block,1)
write(p,s)

# Cache bump.
p='public/sw.js'; s=read(p); s=re.sub(r'const CACHE = "[^"]+";', 'const CACHE = "shadow-village-depth-v2-mission-board";', s, count=1); write(p,s)
print('Village depth v2 mission board/special missions/report pass applied')
