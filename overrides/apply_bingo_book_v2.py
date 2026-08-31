from pathlib import Path
import shutil

ROOT = Path("app")
SRC = Path("overrides/bingo_book")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, value: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding="utf-8")


def copy(rel: str) -> None:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f"{rel}: copied")


# The current BingoBookScreen source now contains v2 dossier actions and hunt UI.
copy("src/game/bingoHunt.ts")
copy("src/components/BingoBookScreen.tsx")

# Engine: resolve target-specific intelligence missions inside the normal mission
# system and reveal delayed exiled missing-nin as soon as their day arrives.
p = "src/game/engine.ts"
s = read(p)
if 'from "./bingoHunt"' not in s:
    lines = s.splitlines()
    insert_at = max((i + 1 for i, line in enumerate(lines) if line.startswith("import ")), default=0)
    lines.insert(insert_at, 'import { resolveBingoIntelMission } from "./bingoHunt";')
    lines.insert(insert_at + 1, 'import { refreshPendingMissingNin } from "./bingo";')
    s = "\n".join(lines) + ("\n" if read(p).endswith("\n") else "")

old = '  const specialReward = win ? applySpecialReward(s, m, squad) : undefined;'
new = '  const specialReward = resolveBingoIntelMission(s, m, win) ?? (win ? applySpecialReward(s, m, squad) : undefined);'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("Bingo intel mission resolution anchor not found")

old = '  s.day++;\n  ev.push({ type: "day", day: s.day });'
new = '  s.day++;\n  ev.push({ type: "day", day: s.day });\n  refreshPendingMissingNin(s);'
if old in s:
    s = s.replace(old, new, 1)
elif 'refreshPendingMissingNin(s);' not in s:
    raise SystemExit("Bingo exile reveal day anchor not found")
write(p, s)
print("engine Bingo missions + timed exile reveals: applied")

# Mission Board: give Bingo investigations their own folder rather than mixing
# them into ordinary Special Missions.
p = "src/components/MissionBoard.tsx"
s = read(p)
if 'from "../game/bingoHunt"' not in s:
    s = s.replace(
        'import { autoSquad, coverage, meetsRank, squadChance, squadOf } from "../game/engine";',
        'import { autoSquad, coverage, meetsRank, squadChance, squadOf } from "../game/engine";\nimport { isBingoIntelMission } from "../game/bingoHunt";',
        1,
    )

s = s.replace(
    'type Folder = Rank | "SPECIAL";\nconst FOLDERS: Folder[] = ["D", "C", "B", "A", "S", "SPECIAL"];',
    'type Folder = Rank | "SPECIAL" | "BINGO";\nconst FOLDERS: Folder[] = ["D", "C", "B", "A", "S", "SPECIAL", "BINGO"];',
    1,
)
s = s.replace(
    'const inFolder = folder ? open.filter((m) => folder === "SPECIAL" ? !!m.specialId : !m.specialId && m.rank === folder) : [];',
    'const inFolder = folder ? open.filter((m) => folder === "BINGO" ? isBingoIntelMission(m) : folder === "SPECIAL" ? !!m.specialId && !isBingoIntelMission(m) : !m.specialId && m.rank === folder) : [];',
    1,
)

old = '{FOLDERS.map((f) => { const missions=open.filter((m)=>f==="SPECIAL"?!!m.specialId:!m.specialId&&m.rank===f); const special=f==="SPECIAL"; const color=special?"#d6a4ff":RANK_COLOR[f as Rank]; return <button key={f} onClick={()=>setFolder(f)} className={cn("min-h-[92px] rounded-xl bg-black/25 p-3 text-left ring-1 transition active:scale-[0.98]",special?"ring-[#d6a4ff]/25":"ring-white/7")}><div className="flex items-start justify-between gap-2"><span className="grid h-9 w-9 place-items-center rounded-lg font-display text-sm font-black text-white" style={{backgroundColor:color}}>{special?"特":f}</span><span className="rounded-md bg-black/30 px-2 py-1 text-[10px] font-black tabular-nums" style={{color}}>{missions.length} OPEN</span></div><p className="mt-2 text-[11px] font-black text-paper/90">{special?"Special Missions":`${f}-Rank Missions`}</p><p className="mt-0.5 text-[8.5px] leading-relaxed text-paper/40">{special?"Rare contracts with permanent rewards: traits, jutsu, unique gear, Potential breakthroughs or village unlocks.":missions.length?"Open this grade to inspect individual contracts.":"No contracts at this grade today."}</p></button>})}'
new = '{FOLDERS.map((f) => { const bingo=f==="BINGO"; const special=f==="SPECIAL"; const missions=open.filter((m)=>bingo?isBingoIntelMission(m):special?!!m.specialId&&!isBingoIntelMission(m):!m.specialId&&m.rank===f); const color=bingo?"#d55245":special?"#d6a4ff":RANK_COLOR[f as Rank]; return <button key={f} onClick={()=>setFolder(f)} className={cn("min-h-[92px] rounded-xl bg-black/25 p-3 text-left ring-1 transition active:scale-[0.98]",bingo?"ring-vermil/30":special?"ring-[#d6a4ff]/25":"ring-white/7")}><div className="flex items-start justify-between gap-2"><span className="grid h-9 w-9 place-items-center rounded-lg font-display text-sm font-black text-white" style={{backgroundColor:color}}>{bingo?"帳":special?"特":f}</span><span className="rounded-md bg-black/30 px-2 py-1 text-[10px] font-black tabular-nums" style={{color}}>{missions.length} OPEN</span></div><p className="mt-2 text-[11px] font-black text-paper/90">{bingo?"Bingo Intelligence":special?"Special Missions":`${f}-Rank Missions`}</p><p className="mt-0.5 text-[8.5px] leading-relaxed text-paper/40">{bingo?"Target-specific investigations that increase dossier intelligence and can locate missing-nin.":special?"Rare contracts with permanent rewards: traits, jutsu, unique gear, Potential breakthroughs or village unlocks.":missions.length?"Open this grade to inspect individual contracts.":"No contracts at this grade today."}</p></button>})}'
if old in s:
    s = s.replace(old, new, 1)
elif 'Bingo Intelligence' not in s:
    raise SystemExit("Bingo mission folder cards anchor not found")

s = s.replace(
    '{folder==="SPECIAL"?"SPECIAL MISSIONS":`${folder}-RANK CONTRACTS`}',
    '{folder==="BINGO"?"BINGO INTELLIGENCE":folder==="SPECIAL"?"SPECIAL MISSIONS":`${folder}-RANK CONTRACTS`}',
    1,
)
s = s.replace(
    'const rm=RANK_META[m.minRank]; const special=!!m.specialId; return',
    'const rm=RANK_META[m.minRank]; const bingo=isBingoIntelMission(m); const special=!!m.specialId&&!bingo; return',
    1,
)
s = s.replace(
    '<h4 className="truncate text-[12.5px] font-bold text-[#2b2118]">{m.name}</h4>{special&&<span',
    '<h4 className="truncate text-[12.5px] font-bold text-[#2b2118]">{m.name}</h4>{bingo&&<span className="rounded bg-vermil/10 px-1.5 py-0.5 text-[8px] font-black text-vermil">BINGO INTEL</span>}{special&&<span',
    1,
)
reward_anchor = '{special&&<div className="mt-1.5 rounded-lg bg-[#6c3a86]/8 px-2 py-1.5 ring-1 ring-[#6c3a86]/15"><p className="flex items-center gap-1 text-[8px] font-black tracking-wider text-[#6c3a86]"><ShieldAlert size={10}/> PERMANENT REWARD</p><p className="mt-0.5 text-[9.5px] font-black text-[#3d2948]">{m.specialRewardLabel}</p></div>}'
if reward_anchor in s and 'BINGO DOSSIER' not in s:
    bingo_box = '{bingo&&<div className="mt-1.5 rounded-lg bg-vermil/[0.05] px-2 py-1.5 ring-1 ring-vermil/15"><p className="flex items-center gap-1 text-[8px] font-black tracking-wider text-vermil"><ShieldAlert size={10}/> BINGO DOSSIER</p><p className="mt-0.5 text-[9.5px] font-black text-[#6b342c]">{m.specialRewardLabel}</p></div>}'
    s = s.replace(reward_anchor, bingo_box + reward_anchor, 1)

if 'type Folder = Rank | "SPECIAL" | "BINGO";' not in s or 'const bingo=isBingoIntelMission(m);' not in s:
    raise SystemExit("Bingo Mission Board integration incomplete")
write(p, s)
print("Mission Board Bingo folder: applied")

# v1 already establishes the branch-specific cache key. Keep it stable until the
# boss-battle integration lands, so the existing workflow validation remains valid.
print("Bingo Book v2 patch complete")
