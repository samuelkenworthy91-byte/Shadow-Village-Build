# Kage Life gameplay update v34

Work in progress: restored and compiling; gameplay and mobile verification pending.

- 296 given names and 200 surnames (59,200 combinations); scout candidates reserve names and portraits within a batch.
- Ordinary clan inheritance: 10/16/22/28/34% at potential 1–5, +4 percentage points with elite recruitment. Mythic bloodlines retain tiny relative weights and potential-5 gating.
- Kekkei Talent: 8% at potential 1–3, 12% at 4–5; elite recruitment adds 2 percentage points. Existing Yuki and Wood inheritance still sets the matching pair.
- Legends: 2% per three-person search, rising only with Hall/research to a 6% cap; no day-based inflation. Jinchuriki has 0.25 relative weight.
- Kamiori paper seals, Hibiki resonance, and Kasumori venom mist: four paths and four tiers each, 48 clan techniques total.
- Burn/poison/bleed tick at `(5 + skill × 0.55/0.45/0.50) × jutsu power`; AoE ticks use 65% and burn mastery also applies. Defence and guard do not reduce ticks; summon shields do. Reapplication keeps stronger damage and longer duration. Corrected two legacy bone techniques with erroneous 12/20-round bleed durations.
- Combined-nature jutsu remain accessible alongside clan trees; all ten elemental pairs are being audited for complete unique progression tables.
- Restored ten summon pacts, original IDs, artwork, gacha, bonding and interventions from Arena commit `2a1112d1f1d2b0c2ab6342e615658858276f5bcd`. Only the summon feature was recovered from the older content-expansion patch; unrelated old UI/gameplay changes are excluded. Fixed 12th-draw pity and first-turn hawk initiative. Restored save data remains compatible.

`apply_gameplay_v34.py` follows `apply_portrait_qc_v33.py`. Input/output hashes guard every changed file; rerunning an applied patch verifies it without applying it twice. New main builds must run this final patch before uploading source and compiling.
