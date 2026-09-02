"""v30: daily resource projections move off the top bar into a dedicated
collapsible panel on the Mission Board.

The HUD chips currently render inline next-day previews (+gold from Tea
Houses, +/- rice) on the top bar. The user wants those previews in a
dedicated panel instead: this adds a collapsible "Tomorrow's Projections"
section at the top of the Mission Board (gold, rice with production and
consumption breakdown, energy refill) and strips the inline previews and
next-day tooltips from the HUD chips.

Runs after apply_ninja_portraits_v29.py, before the v18/v19 patches.
ASCII only - the v19 dekanji sweep runs afterwards.
"""

from pathlib import Path

ROOT = Path("app")
MB = ROOT / "src/components/MissionBoard.tsx"
HUD = ROOT / "src/components/HUD.tsx"

# ---------------------------------------------------------------- MissionBoard
mb = MB.read_text(encoding="utf-8")

imp_old = 'import { ArrowLeft, Coins, Lock, ScrollText, ShieldAlert, Sun, Users, Wheat } from "lucide-react";'
imp_new = 'import { ArrowLeft, ChevronDown, Coins, Lock, ScrollText, ShieldAlert, Sun, Users, Wheat, Zap } from "lucide-react";'
if imp_new not in mb:
    if imp_old not in mb:
        raise RuntimeError("MissionBoard lucide import line not found")
    mb = mb.replace(imp_old, imp_new, 1)

ct_old = 'import { RANK_COLOR, RANK_KANJI, RANK_META, SKILL_META } from "../game/content";'
ct_new = 'import { EAT_PER_DAY, FARM_RICE, RANK_COLOR, RANK_KANJI, RANK_META, SKILL_META, TEA_GOLD } from "../game/content";'
if ct_new not in mb:
    if ct_old not in mb:
        raise RuntimeError("MissionBoard content import line not found")
    mb = mb.replace(ct_old, ct_new, 1)

en_old = 'import { autoSquad, coverage, meetsRank, squadChance, squadOf } from "../game/engine";'
en_new = 'import { apMax, autoSquad, coverage, hasTech, meetsRank, squadChance, squadOf } from "../game/engine";'
if en_new not in mb:
    if en_old not in mb:
        raise RuntimeError("MissionBoard engine import line not found")
    mb = mb.replace(en_old, en_new, 1)

ins_old = """        {folder === null ? <>
          {running.length > 0 && <div className="mb-1 text-[9px] font-black tracking-[0.2em] text-paper/40">ACTIVE MISSIONS</div>}"""
ins_new = """        {folder === null ? <>
          <DailyProjections s={s} />
          {running.length > 0 && <div className="mb-1 text-[9px] font-black tracking-[0.2em] text-paper/40">ACTIVE MISSIONS</div>}"""
if "<DailyProjections s={s} />" not in mb:
    if ins_old not in mb:
        raise RuntimeError("MissionBoard folder-null block not found")
    mb = mb.replace(ins_old, ins_new, 1)

comp_anchor = 'function Empty({text="No contracts — end the day for new work."}:{text?:string}) { return <div className="flex min-h-24 flex-col items-center justify-center gap-2 text-paper/40"><ScrollText size={22} className="opacity-50"/><p className="text-center text-[11px]">{text}</p></div>; }'
comp = """function projFmt(v: number): string {
  return Number.isInteger(v) ? v.toLocaleString() : v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function DailyProjections({ s }: { s: GameState }) {
  const [open, setOpen] = useState(false);
  const nextGold = TEA_GOLD * s.b.tea * (hasTech(s, "tea_merchant_contacts") ? 1.25 : 1);
  const nextRice = FARM_RICE * s.b.farm * (hasTech(s, "farm_efficiency") ? 1.25 : 1);
  const eaten = EAT_PER_DAY * s.ninjas.length * (hasTech(s, "farm_ration_stores") ? 0.75 : 1);
  const netRice = nextRice - eaten;
  const maxAp = apMax(s);
  const goldTmrw = Math.floor(s.gold + nextGold);
  const riceTmrw = Math.floor(s.rice + netRice);
  return (
    <div className="mb-2 overflow-hidden rounded-xl bg-black/25 ring-1 ring-white/8">
      <button onClick={() => setOpen(!open)} className="flex h-9 w-full items-center gap-1.5 px-2.5 text-[9px] font-black tracking-[0.2em] text-paper/55">
        <Sun size={11} className="text-gold" /> TOMORROW'S PROJECTIONS
        <ChevronDown size={13} className={cn("ml-auto text-paper/45 transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="grid grid-cols-3 gap-1.5 border-t border-white/8 p-2">
          <div className="rounded-lg bg-black/25 p-2 ring-1 ring-inset ring-white/5" title={`Tea Houses produce ${projFmt(nextGold)} gold overnight`}>
            <p className="flex items-center gap-1 text-[8.5px] font-black tracking-wider text-paper/45"><Coins size={10} className="text-gold" /> GOLD</p>
            <p className="mt-1 text-[13px] font-black tabular-nums text-paper/90">{Math.floor(s.gold).toLocaleString()}</p>
            <p className="text-[9.5px] font-bold tabular-nums text-jade">+{projFmt(nextGold)} &rarr; {goldTmrw.toLocaleString()}</p>
          </div>
          <div className="rounded-lg bg-black/25 p-2 ring-1 ring-inset ring-white/5" title={`Paddies produce ${projFmt(nextRice)} rice; ${s.ninjas.length} ninja eat ${projFmt(eaten)}`}>
            <p className="flex items-center gap-1 text-[8.5px] font-black tracking-wider text-paper/45"><Wheat size={10} className={s.hungry ? "text-vermil" : "text-[#8fce6a]"} /> RICE</p>
            <p className="mt-1 text-[13px] font-black tabular-nums text-paper/90">{Math.floor(s.rice).toLocaleString()}</p>
            <p className={cn("text-[9.5px] font-bold tabular-nums", netRice >= 0 ? "text-jade" : "text-vermil")}>
              {netRice >= 0 ? "+" : ""}{projFmt(netRice)} &rarr; {riceTmrw.toLocaleString()}
            </p>
            <p className="mt-0.5 text-[8px] font-semibold tabular-nums text-paper/35">+{projFmt(nextRice)} paddies / -{projFmt(eaten)} eaten</p>
          </div>
          <div className="rounded-lg bg-black/25 p-2 ring-1 ring-inset ring-white/5" title="Actions fully restore at dawn">
            <p className="flex items-center gap-1 text-[8.5px] font-black tracking-wider text-paper/45"><Zap size={10} className="text-gold" /> ENERGY</p>
            <p className="mt-1 text-[13px] font-black tabular-nums text-paper/90">{s.ap}/{maxAp}</p>
            <p className="text-[9.5px] font-bold tabular-nums text-jade">restores to {maxAp}</p>
          </div>
        </div>
      )}
    </div>
  );
}

"""
if "function DailyProjections" not in mb:
    if comp_anchor not in mb:
        raise RuntimeError("MissionBoard Empty anchor not found")
    mb = mb.replace(comp_anchor, comp + comp_anchor, 1)

MB.write_text(mb, encoding="utf-8")
print("MissionBoard: Tomorrow's Projections panel added")

# ---------------------------------------------------------------- HUD
hud = HUD.read_text(encoding="utf-8")

gold_old = """        value={Math.floor(s.gold).toLocaleString()}
        gain={nextGoldFromBuildings}
        title={`Next day from Tea Houses: +${formatGain(nextGoldFromBuildings)} gold`}
      />"""
gold_new = """        value={Math.floor(s.gold).toLocaleString()}
        title="Village gold - tomorrow's projection is on the Mission Board"
      />"""
if gold_old not in hud:
    if gold_new in hud:
        print("HUD: gold chip already cleaned")
    else:
        raise RuntimeError("HUD gold chip block not found")
else:
    hud = hud.replace(gold_old, gold_new, 1)

rice_old = """        value={Math.floor(s.rice).toLocaleString()}
        gain={nextRiceFromBuildings}
        loss={nextRiceConsumption}
        title={`Next day: +${formatGain(nextRiceFromBuildings)} rice from Paddies −${formatGain(nextRiceConsumption)} rice consumed by ${s.ninjas.length} ninja`}
        warn={s.hungry}
      />"""
rice_new = """        value={Math.floor(s.rice).toLocaleString()}
        title={`Rice stores${s.hungry ? " - the village is hungry" : ""} - tomorrow's projection is on the Mission Board`}
        warn={s.hungry}
      />"""
if rice_old not in hud:
    if rice_new in hud:
        print("HUD: rice chip already cleaned")
    else:
        raise RuntimeError("HUD rice chip block not found")
else:
    hud = hud.replace(rice_old, rice_new, 1)

calc_old = """  const max = apMax(s);
  const nextGoldFromBuildings = TEA_GOLD * s.b.tea * (hasTech(s, "tea_merchant_contacts") ? 1.25 : 1);
  const nextRiceFromBuildings = FARM_RICE * s.b.farm * (hasTech(s, "farm_efficiency") ? 1.25 : 1);
  const nextRiceConsumption = EAT_PER_DAY * s.ninjas.length * (hasTech(s, "farm_ration_stores") ? 0.75 : 1);
"""
calc_new = """  const max = apMax(s);
"""
if calc_old in hud:
    hud = hud.replace(calc_old, calc_new, 1)

imp_old_hud = 'import { EAT_PER_DAY, FARM_RICE, TEA_GOLD } from "../game/content";\nimport { apMax, hasTech, streakMult } from "../game/engine";'
imp_new_hud = 'import { apMax, streakMult } from "../game/engine";'
if imp_old_hud in hud:
    hud = hud.replace(imp_old_hud, imp_new_hud, 1)
elif "EAT_PER_DAY" not in hud:
    pass  # already cleaned
else:
    raise RuntimeError("HUD import lines not in expected shape")

# drop formatGain if nothing references it anymore
if "formatGain(" not in hud.replace("function formatGain", ""):
    fg_old = """function formatGain(value: number): string {
  return Number.isInteger(value)
    ? value.toLocaleString()
    : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

"""
    if fg_old in hud:
        hud = hud.replace(fg_old, "", 1)
HUD.write_text(hud, encoding="utf-8")
print("HUD: inline next-day previews removed from the top bar")

# ---------------------------------------------------------------- checks
mb_chk = MB.read_text(encoding="utf-8")
hud_chk = HUD.read_text(encoding="utf-8")
assert "function DailyProjections" in mb_chk
assert "<DailyProjections s={s} />" in mb_chk
assert "TOMORROW'S PROJECTIONS" in mb_chk
assert "gain={nextGoldFromBuildings}" not in hud_chk
assert "gain={nextRiceFromBuildings}" not in hud_chk
assert "loss={nextRiceConsumption}" not in hud_chk
assert "EAT_PER_DAY" not in hud_chk
mb_chk + hud_chk  # files are non-empty
for c in set(mb_chk + hud_chk):
    assert not (0x4e00 <= ord(c) <= 0x9fff or 0x3040 <= ord(c) <= 0x30ff or 0x3000 <= ord(c) <= 0x303f), f"CJK slipped in: {c!r}"
print("Applied v30: daily projections panel")
