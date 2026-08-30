import { useMemo, useState } from "react";
import { ChevronLeft, PackageOpen, X } from "lucide-react";
import type { GameState, Ninja } from "../game/types";
import {
  EQUIPMENT_CATALOG,
  RARITY_META,
  availableCount,
  equipItem,
  equipmentSlots,
  equipmentSummary,
  ensureEquipmentState,
  unequipItem,
  type EquipmentItem,
} from "../game/equipment";
import NinjaSprite from "./NinjaSprite";

export default function NinjaEquipment({ s, n, onClose, onChanged }: { s: GameState; n: Ninja; onClose: () => void; onChanged: () => void }) {
  const [, redraw] = useState(0);
  const [pickSlot, setPickSlot] = useState<number | null>(null);
  const st = ensureEquipmentState(s);
  const slots = equipmentSlots(n);
  const owned = useMemo(() => EQUIPMENT_CATALOG.filter((x) => (st.inventory[x.id] ?? 0) > 0).sort((a, b) => RARITY_META[b.rarity].rank - RARITY_META[a.rarity].rank || a.name.localeCompare(b.name)), [st.inventory, st.totalPulls]);

  const choose = (item: EquipmentItem) => {
    if (pickSlot == null) return;
    if (equipItem(s, n, pickSlot, item.id)) {
      setPickSlot(null);
      redraw((x) => x + 1);
      onChanged();
    }
  };

  const remove = (slot: number) => {
    unequipItem(n, slot);
    redraw((x) => x + 1);
    onChanged();
  };

  return (
    <div className="fixed inset-0 z-[75] bg-[#0d0e1a]/95 p-2 backdrop-blur-md sm:p-4" onClick={onClose}>
      <div className="mx-auto flex h-full w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-[#17192a] shadow-2xl ring-1 ring-white/12" onClick={(e) => e.stopPropagation()}>
        <div className="flex h-11 shrink-0 items-center gap-2 border-b border-white/8 px-3">
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg bg-black/25 text-paper/60 ring-1 ring-white/8"><ChevronLeft size={16} /></button>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[12px] font-black text-paper">{n.name}</p>
            <p className="text-[8px] font-black tracking-[0.18em] text-gold/65">EQUIPMENT LOADOUT · ANY FOUR PIECES</p>
          </div>
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg bg-black/25 text-paper/55 ring-1 ring-white/8"><X size={15} /></button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3">
          <div className="grid gap-3 md:grid-cols-[220px_1fr]">
            <div className="rounded-2xl bg-black/25 p-3 ring-1 ring-inset ring-white/8">
              <div className="grid place-items-center overflow-hidden rounded-xl bg-gradient-to-b from-white/[0.035] to-black/20 py-3 ring-1 ring-inset ring-white/6">
                <NinjaSprite n={n} h={350} crop="full" aura />
              </div>
              <p className="mt-2 text-center text-[9px] font-black tracking-[0.17em] text-paper/35">FULL PORTRAIT</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {equipmentSummary(n).map((x) => <span key={x} className="rounded-md bg-jade/10 px-2 py-1 text-[8.5px] font-black text-jade/85 ring-1 ring-inset ring-jade/15">{x}</span>)}
              </div>
            </div>

            <div>
              <p className="text-[9px] font-black tracking-[0.18em] text-paper/45">EQUIPPED</p>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {slots.map((id, slot) => {
                  const item = id ? EQUIPMENT_CATALOG.find((x) => x.id === id) : null;
                  const rarity = item ? RARITY_META[item.rarity] : null;
                  return (
                    <button key={slot} onClick={() => setPickSlot(slot)} className="min-h-28 rounded-xl bg-black/25 p-2.5 text-left ring-1 ring-white/9 transition hover:bg-black/35">
                      <div className="flex items-center gap-2">
                        <span className="grid h-8 w-8 place-items-center rounded-lg bg-black/35 font-display text-base font-black" style={{ color: rarity?.color ?? "#717784" }}>{item?.icon ?? "+"}</span>
                        <div className="min-w-0">
                          <p className="text-[8px] font-black tracking-wider text-paper/30">SLOT {slot + 1}</p>
                          <p className="truncate text-[10px] font-black" style={{ color: rarity?.color ?? "#d7d9df" }}>{item?.name ?? "Empty"}</p>
                        </div>
                      </div>
                      <p className="mt-2 line-clamp-3 text-[8.5px] font-semibold leading-relaxed text-paper/50">{item?.desc ?? "Tap to choose any owned equipment."}</p>
                      {item && (
                        <span onClick={(e) => { e.stopPropagation(); remove(slot); }} className="mt-2 inline-flex rounded bg-vermil/12 px-1.5 py-1 text-[8px] font-black text-vermil/80">UNEQUIP</span>
                      )}
                    </button>
                  );
                })}
              </div>

              <div className="mt-3 rounded-xl bg-black/20 p-2.5 text-[9px] font-semibold leading-relaxed text-paper/45 ring-1 ring-inset ring-white/6">
                Equipment has no class, rank, weapon or armour restrictions. Stat bonuses are included in the ninja's effective stats; combat passives apply in raids and exams. Technique gear grants its 奥義 through the existing Special command when the ninja does not already have a personal signature technique.
              </div>
            </div>
          </div>

          {pickSlot != null && (
            <div className="mt-3 rounded-2xl bg-[#121421] p-3 ring-1 ring-white/10">
              <div className="flex items-center gap-2"><PackageOpen size={14} className="text-gold" /><p className="text-[9px] font-black tracking-[0.17em] text-paper/60">CHOOSE FOR SLOT {pickSlot + 1}</p><button onClick={() => setPickSlot(null)} className="ml-auto text-[9px] font-black text-paper/40">CANCEL</button></div>
              {owned.length === 0 ? (
                <div className="mt-3 rounded-xl border border-dashed border-white/10 p-5 text-center text-[10px] font-semibold text-paper/35">No equipment owned. Use the Equipment tab to make pulls.</div>
              ) : (
                <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {owned.map((item) => {
                    const avail = availableCount(s, item.id);
                    const r = RARITY_META[item.rarity];
                    return (
                      <button key={item.id} disabled={avail <= 0} onClick={() => choose(item)} className="rounded-xl bg-black/25 p-2.5 text-left ring-1 ring-white/8 disabled:opacity-30">
                        <div className="flex items-center gap-2"><span className="grid h-8 w-8 place-items-center rounded-lg font-display font-black" style={{ color: r.color, background: `${r.color}16` }}>{item.icon}</span><div className="min-w-0 flex-1"><p className="truncate text-[10px] font-black text-paper">{item.name}</p><p className="text-[8px] font-black" style={{ color: r.color }}>{r.name.toUpperCase()} · {avail} AVAILABLE</p></div></div>
                        <p className="mt-1.5 text-[8.5px] font-semibold leading-relaxed text-paper/50">{item.desc}</p>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
