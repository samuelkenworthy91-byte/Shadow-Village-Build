# Kage Life gameplay update v34

Production compilation, gameplay regression tests and portrait checks pass. The APK workflow also gates builds on mobile browser verification.

- 296 given names and 200 surnames (59,200 combinations); scout candidates reserve names and portraits within a batch.
- Ordinary clan inheritance: 10/16/22/28/34% at potential 1–5, +4 percentage points with elite recruitment. Mythic bloodlines retain tiny relative weights and potential-5 gating.
- Kekkei Talent: 8% at potential 1–3, 12% at 4–5; elite recruitment adds 2 percentage points. Existing Yuki and Wood inheritance still sets the matching pair.
- Legends: 2% per three-person search, rising only with Hall/research to a 6% cap; no day-based inflation. Jinchuriki has 0.25 relative weight.
- Kamiori paper seals, Hibiki resonance, and Kasumori venom mist: four paths and four tiers each, 48 clan techniques total.
- Burn/poison/bleed tick at `(5 + skill × 0.55/0.45/0.50) × jutsu power`; AoE ticks use 65% and burn mastery also applies. Defence and guard do not reduce ticks; summon shields do. Reapplication keeps stronger damage and longer duration. Corrected two legacy bone techniques with erroneous 12/20-round bleed durations.
- Combined-nature jutsu remain accessible alongside clan trees; all ten elemental pairs pass both-order, prerequisite, learning and clan-combination checks (12 unique techniques and four paths per pair).
- Restored ten summon pacts, original IDs, artwork, gacha, bonding and interventions from Arena commit `2a1112d1f1d2b0c2ab6342e615658858276f5bcd`. Only the summon feature was recovered from the older content-expansion patch; unrelated old UI/gameplay changes are excluded. Fixed 12th-draw pity and first-turn hawk initiative. Restored save data remains compatible.

`apply_gameplay_v34.py` follows `apply_portrait_qc_v33.py`. Input/output hashes guard every changed file; rerunning an applied patch verifies it without applying it twice. New main builds must run this final patch before uploading source and compiling.

## Elemental table audit

| Pair | Unique table | Techniques | Paths |
| --- | --- | ---: | ---: |
| Fire + Water | Steam Veil | 12 | 4 |
| Fire + Wind | Cinderstorm | 12 | 4 |
| Earth + Fire | Magma Vein | 12 | 4 |
| Fire + Lightning | Plasma Arc | 12 | 4 |
| Water + Wind | Frost Weave | 12 | 4 |
| Earth + Water | Briar Flow | 12 | 4 |
| Lightning + Water | Tempest Current | 12 | 4 |
| Earth + Wind | Sandstorm | 12 | 4 |
| Lightning + Wind | Thunder Gale | 12 | 4 |
| Earth + Lightning | Lodestone | 12 | 4 |

## Verification

- 6,000 seeded searches: 123 searches with legends; 3,876 clan recruits among 18,000 candidates; 200 Nara and one Jinchuriki. Distribution checks are bounds-based; these counts describe the fixed test seed.
- New clan progression: 48 unique techniques; innate foundations; prerequisites; shared JP; four equipped actives; no access for unrelated ninjas.
- Actual burn, poison and bleed casts and round ticks at skill 10, 60 and 200; exact preview agreement, refresh and cleanse.
- All ten summon interventions, one use per battle, fatal and DoT rescue, gacha pity, resource costs, copy ownership, deployment locks, save/load and offline artwork.
- Portrait regression: 340 approved portraits; all 370 historical saved IDs; 10,000 legacy identities; 82 repairs and 30 retired portraits retained.
- Patch replay verifies exact source hashes and an idempotent second application.
- Mobile browser gate covers 360px and 412px screens, artwork, five-pact draw, pity reveal, bonding/releasing, reload persistence, clan + Kekkei rendering and learning.
