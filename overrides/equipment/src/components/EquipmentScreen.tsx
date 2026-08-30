import { useMemo, useState } from "react";
import { Coins, PackageOpen, Sparkles, Wheat, Zap } from "lucide-react";
import type { GameState } from "../game/types";
import {
  EQUIPMENT_CATALOG,
  GACHA_PACKS,
  RARITY_META,
  ensureEquipmentState,
  gachaCost,
  ownedUniqueCount,
  pullEquipment,
  type EquipmentItem,
  type EquipmentRarity,
} from "../game/equipment";

const RARITIES: EquipmentRarity[] = ["legendary", "epic", "rare", "uncommon", "common"];

function ItemRow({ item, count }: { item: EquipmentItem; count: number }) {
  const r = RARITY_META[item.rarity];
  return (
    <div className="rounded-xl bg-black/25 p-2.5 ring-1 ring-inset ring-white/7">
      <div className="flex items-start gap-2.5">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg font-display text-lg font-black ring-1 ring-inset" style={{ color: r.color, background: `${r.color}18`, borderColor: `${r.color}40` }}>{item.icon}</span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <p className="truncate text-[11px] font-black text-paper">{item.name}</p>
            <span className="rounded px-1.5 py-[1px] text-[7.5px] font-black tracking-wider" style={{ color: r.color, background: `${r.color}18` }}>{r.name.toUpperCase()}</span>
            <span className="ml-auto text-[9px] font-black tabular-nums text-paper/45">×{count}</span>
          </div>
          <p className="mt-1 text-[9.5px] font-semibold leading-relaxed text-paper/60">{item.desc}</p>
        </div>
      </div>
    </div>
  );
}

export default function EquipmentScreen({ s, onChanged }: { s: GameState; onChanged: () => void }) {
  const [, redraw] = useState(0);
  const [message, setMessage] = useState("Pull equipment with village resources. Every bundle costs 1 action.");
  const [lastPull, setLastPull] = useState<EquipmentItem[]>([]);
  const st = ensureEquipmentState(s);
  const unique = ownedUniqueCount(s);
  const owned = useMemo(() => EQUIPMENT_CATALOG.filter((x) => (st.inventory[x.id] ?? 0) > 0).sort((a, b) => RARITY_META[b.rarity].rank - RARITY_META[a.rarity].rank || a.name.localeCompare(b.name)), [st.inventory, st.totalPulls]);

  const doPull = (pulls: 1 | 10 | 100) => {
    const result = pullEquipment(s, pulls);
    if (!result.ok) {
      setMessage(result.error ?? "Unable to pull equipment.");
      redraw((x) => x + 1);
      return;
    }
    setLastPull(result.items.slice(-12).reverse());
    const best = [...result.items].sort((a, b) => RARITY_META[b.rarity].rank - RARITY_META[a.rarity].rank)[0];
    setMessage(`${pulls} pull${pulls === 1 ? "" : "s"} complete · best: ${RARITY_META[best.rarity].name} ${best.name}${result.newIds.length ? ` · ${result.newIds.length} new` : ""}`);
    redraw((x) => x + 1);
    onChanged();
  };

  return (
    <section className="min-h-0 flex-1 overflow-y-auto pb-24">
      <div className="mx-auto w-full max-w-4xl space-y-3 p-2 sm:p-3">
        <div className="rounded-2xl bg-[#17192a]/95 p-3 ring-1 ring-white/10">
          <div className="flex items-center gap-2">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-gold/12 font-display text-xl font-black text-gold ring-1 ring-gold/25">具</span>
            <div className="min-w-0 flex-1">
              <p className="text-[9px] font-black tracking-[0.2em] text-gold/70">EQUIPMENT GACHA</p>
              <h2 className="text-lg font-black text-paper">Shinobi Supply Draw</h2>
              <p className="text-[9.5px] font-semibold text-paper/45">200 pieces · no slot restrictions · duplicates are usable if owned</p>
            </div>
            <div className="rounded-lg bg-black/30 px-2.5 py-1.5 text-right ring-1 ring-white/8">
              <p className="text-[8px] font-black tracking-wider text-paper/35">COLLECTION</p>
              <p className="text-sm font-black tabular-nums text-jade">{unique}/200</p>
            </div>
          </div>

          <div className="mt-3 rounded-xl bg-black/25 p-2.5 text-[9.5px] font-semibold leading-relaxed text-paper/60 ring-1 ring-inset ring-white/6">
            {message}
          </div>

          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
            {GACHA_PACKS.map((pack) => {
              const cost = gachaCost(pack.pulls);
              const can = s.ap >= 1 && s.gold >= cost.gold && s.rice >= cost.rice;
              return (
                <button key={pack.pulls} disabled={!can} onClick={() => doPull(pack.pulls)} className="rounded-xl bg-black/30 p-3 text-left ring-1 ring-white/10 transition hover:bg-black/40 disabled:opacity-35 active:scale-[0.99]">
                  <div className="flex items-center gap-2">
                    <PackageOpen size={17} className="text-gold" />
                    <p className="text-[12px] font-black text-paper">{pack.label}</p>
                    {pack.discount > 0 && <span className="ml-auto rounded bg-jade/15 px-1.5 py-0.5 text-[8px] font-black text-jade">-{Math.round(pack.discount * 100)}%</span>}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5 text-[9px] font-black tabular-nums text-paper/60">
                    <span className="inline-flex items-center gap-1 rounded bg-black/35 px-1.5 py-1"><Coins size={10} className="text-gold" />{cost.gold.toLocaleString()}</span>
                    <span className="inline-flex items-center gap-1 rounded bg-black/35 px-1.5 py-1"><Wheat size={10} className="text-[#8fce6a]" />{cost.rice.toLocaleString()}</span>
                    <span className="inline-flex items-center gap-1 rounded bg-black/35 px-1.5 py-1"><Zap size={10} className="text-gold" />1 action</span>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-3 flex flex-wrap gap-1.5">
            {RARITIES.map((rarity) => {
              const meta = RARITY_META[rarity];
              return <span key={rarity} className="rounded-md px-2 py-1 text-[8px] font-black tracking-wider" style={{ color: meta.color, background: `${meta.color}15` }}>{meta.name.toUpperCase()} {meta.weight}%</span>;
            })}
          </div>
        </div>

        {lastPull.length > 0 && (
          <div className="rounded-2xl bg-[#17192a]/95 p-3 ring-1 ring-white/10">
            <div className="flex items-center gap-2"><Sparkles size={14} className="text-gold" /><p className="text-[9px] font-black tracking-[0.18em] text-paper/65">LATEST RESULTS</p></div>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {lastPull.map((item, i) => <ItemRow key={`${item.id}-${i}`} item={item} count={1} />)}
            </div>
          </div>
        )}

        <div className="rounded-2xl bg-[#17192a]/95 p-3 ring-1 ring-white/10">
          <div className="flex items-end gap-2">
            <div>
              <p className="text-[9px] font-black tracking-[0.18em] text-paper/50">OWNED EQUIPMENT</p>
              <p className="mt-0.5 text-[10px] font-semibold text-paper/40">Tap a ninja portrait in their detail screen to equip any four pieces.</p>
            </div>
            <p className="ml-auto text-[9px] font-black tabular-nums text-paper/45">{st.totalPulls.toLocaleString()} total pulls</p>
          </div>
          {owned.length === 0 ? (
            <div className="mt-3 grid min-h-28 place-items-center rounded-xl border border-dashed border-white/10 text-center text-[10px] font-semibold text-paper/35">No equipment owned yet.</div>
          ) : (
            <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">{owned.map((item) => <ItemRow key={item.id} item={item} count={st.inventory[item.id] ?? 0} />)}</div>
          )}
        </div>
      </div>
    </section>
  );
}
