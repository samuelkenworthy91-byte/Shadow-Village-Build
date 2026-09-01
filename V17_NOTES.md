# v17 gameplay polish

Six player-reported issues, fixed as one reviewed override.

## What changed

**1. Potential audit — it was genuinely broken.**
Natural potential was a flat 1-5 roll, so 20% of every recruit was a true
5-star (about 36% with Talent Scouts). Worse, the star readout drew the *top*
of the uncertainty band, so any ninja who *might* be a 5 displayed as a 5.
Between the two, effectively everyone looked maxed. Potential is now a
weighted roll and the display distinguishes an estimate from a confirmed
value.

| Potential | Natural | With Talent Scouts |
|---|---|---|
| 1 | 14% | 2% |
| 2 | 28% | 16% |
| 3 | 34% | 40% |
| 4 | 18% | 31% |
| 5 | **6%** | **12%** |

The uncertainty band also tightens with observation: +/-2 stars below level 5,
+/-1 to level 9, exact from level 10.

**2. Flavour *and* mechanics everywhere.** Jutsu, Genjutsu, gear techniques and
skill-tree techniques all show an italic flavour line plus a generated
mechanics line. The mechanics text is derived from the same structured numbers
combat resolves with, so descriptions cannot drift out of sync with behaviour.

**3. Equipment unrestricted.** The rarity gate is gone: any four owned pieces
on any ninja, any slot, repeats allowed. Every numeric bonus is always shown as
a tag, on both the equip screen and the per-ninja panel.

**4. Resource forecasts on the home screen.** Gold shows `+N/day` beneath the
total; rice shows income, consumption and the net figure, so a starving village
is visible before it starves.

**5. Item pictures.** Each item renders drawn artwork matching its written
appearance in place of the old kanji tile.

**6. New buildings and research.** Four buildings and sixteen technologies.

| Building | Levels | Requires | Level effect |
|---|---|---|---|
| Ninja Academy 学 | 3 | Dojo 2 | +10% XP/lv, scout cost -10%/lv |
| Armourer's Forge 鍛 | 3 | Tea House 2 | gacha -8%/lv, +2% ATK/DEF per lv |
| Merchant Quarter 市 | 3 | Tea House 2 | +9 gold/day/lv, +4% mission gold/lv |
| Scroll Archive 書 | 2 | Academy 2 | extra JP = lv x floor(ninjaLv/3) |

Research: curriculum (x1.20 XP), graduation exams (recruits start Lv 3), clan
outreach (better potential rolls, +4pp unique trait), chakra theory (+1 JP per
6 levels); village smithy (-15% gacha), chakra tempering (x1.25 gear skill
bonuses), supply line (repairs half cost, 0 AP), masterwork bench (6% rarity
upgrade per pull); scroll catalogue (-10% chakra costs), illusion studies
(+8pp genjutsu land), field manuals (+4pp mission success, x1.06 XP),
forbidden vault (+10% jutsu power); caravan routes (x1.30 market gold), bounty
office (x1.20 mission gold and bingo bounties), rice exchange (+6 rice/day,
x1.20 mission rice), war chest (+1 AP/day).

**7. Crit and dodge unified at an 80% ceiling.** There *were* limits, and they
were a mess: crit was clamped at 0.42, 0.48, 0.70, 0.85 and 0.92 in different
code paths, dodge at 0.30, 0.34, 0.45, 0.55 and 0.60. Which one applied
depended on whether the bonus came from skills, gear, a jutsu passive, raid
threat scaling or the jutsu attack roll, so **the percentage on a ninja's sheet
was not the percentage combat rolled against**. Both stats now clamp to single
shared constants (`CRIT_CAP` / `DODGE_CAP` in `content.ts`) everywhere, so the
displayed number is the real one.

I capped at 80% rather than uncapping, for two reasons: an uncapped dodge build
becomes literally unhittable and trivialises the raid and Bingo content, and an
uncapped crit rate collides with the crit-damage multiplier to produce runaway
scaling. 80% is reachable but expensive — roughly 105 SPD/DŌJ/TAC for dodge, or
less with gear — and still leaves one hit in five landing. The personal screen
now warns you when a stat is at the ceiling so you stop pouring points into a
stat that is discarding them.

**8. Gear contributions on the personal screen.** The battle profile shows the
gear delta beneath every stat — HP, ATK, DEF, CRIT, DODGE, CHAKRA, plus crit
damage. These are computed by building the unit twice, once geared and once
with empty slots, and differencing the results, so the figures account for
multiplicative stacking and the shared cap rather than naively re-adding item
numbers. If gear pushes crit past the ceiling, the delta shows the portion that
actually applied.

## Applying it

`overrides/apply_v17_gameplay_polish.py` applies
`overrides/v17_gameplay_polish.patch` to `app/`, verifies every landmark, and
bumps the service-worker cache key. It is idempotent, so the Kage Life branch
build can re-run it over the already-patched main artifact safely.

Verified: patch applies cleanly on a from-scratch pipeline run,
`tsc --noEmit` is clean, and `vite build` succeeds.

## Action required from you

GitHub blocks this agent from pushing workflow-file changes, so the two CI
steps are staged as a patch instead:

    git apply overrides/v17_workflow_steps.patch

That inserts the "Apply v17 gameplay polish" step into
`.github/workflows/build-apk.yml` (before the source-snapshot upload) and into
`.github/workflows/build-kage-life-branch.yml`.
