from pathlib import Path

p = Path('app/src/game/engine.ts')
s = p.read_text(encoding='utf-8')

old = 'const eligible = SPECIAL_MISSIONS.filter((d) => s.day >= SPECIAL_UNLOCK_DAY[d.grade]).filter((d) => !d.requiredNature || s.ninjas.some((n) => n.nature === d.requiredNature || n.secondaryNature === d.requiredNature)).filter((d) => d.reward.kind !== "recruit" || s.ninjas.filter((n) => n.legend === d.reward.legendId).length < d.reward.maxOwned);'
new = 'const eligible = SPECIAL_MISSIONS.filter((d) => s.day >= SPECIAL_UNLOCK_DAY[d.grade]).filter((d) => !d.requiredNature || s.ninjas.some((n) => n.nature === d.requiredNature || n.secondaryNature === d.requiredNature)).filter((d) => { const reward = d.reward; if (reward.kind !== "recruit") return true; return s.ninjas.filter((n) => n.legend === reward.legendId).length < reward.maxOwned; });'
if old not in s:
    raise SystemExit('rare-order eligibility narrowing anchor missing')
s = s.replace(old, new, 1)

old = '''  if (def.reward.kind === "recruit") {
    const count = s.ninjas.filter((n) => n.legend === def.reward.legendId).length;
    if (count >= def.reward.maxOwned) return `${def.reward.name} order is already at its ${def.reward.maxOwned}-member limit.`;
    const recruit = makeRareOrderRecruit(s, def.reward.legendId, def.reward.startingRank);
    s.ninjas.push(recruit);
    return `Rare recruit joined: ${recruit.name} — ${LEGENDS[def.reward.legendId].title} ${LEGENDS[def.reward.legendId].epithet}. Order strength ${count + 1}/${def.reward.maxOwned}.`;
  }
'''
new = '''  if (def.reward.kind === "recruit") {
    const reward = def.reward;
    const count = s.ninjas.filter((n) => n.legend === reward.legendId).length;
    if (count >= reward.maxOwned) return `${reward.name} order is already at its ${reward.maxOwned}-member limit.`;
    const recruit = makeRareOrderRecruit(s, reward.legendId, reward.startingRank);
    s.ninjas.push(recruit);
    return `Rare recruit joined: ${recruit.name} — ${LEGENDS[reward.legendId].title} ${LEGENDS[reward.legendId].epithet}. Order strength ${count + 1}/${reward.maxOwned}.`;
  }
'''
if old not in s:
    raise SystemExit('rare-order reward narrowing anchor missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Village depth v6 TypeScript narrowing fix applied')
