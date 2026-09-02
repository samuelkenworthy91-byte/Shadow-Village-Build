# v18 — Bingo Book presentation, animal summons, tree variety

Three requests: audit and improve the Bingo Book's visuals, add a summon gacha
with a genuinely different mechanic, and widen the tech/jutsu/genjutsu trees so
options stop feeling interchangeable.

## 1. Bingo Book

The audit found the screen was mechanically complete but visually generic — it
used the same flat dark cards as every other panel, so the game's endgame read
as a settings list. It is now a hunter's ledger.

- Aged paper ground with ruled case-file lines behind the entries.
- Dossier cards edged by threat tier, so an S-rank target is identifiable at a
  glance without reading the label.
- Rotated verdict stamps — `TERMINATED`, `IN CUSTODY`, `DEFECTED` — struck
  across resolved entries.
- Unidentified targets carry a pulsing redaction bar instead of a name.
- The intel meter fills with a sweeping highlight as leads accumulate.
- The active hunt banner has a live danger sweep and a stage-pip track showing
  how far the hunt has progressed.

All of it is CSS-driven; no new images, and nothing was added to the bundle.

## 2. Animal summons

**The design problem.** A summon that just adds stats is a fifth equipment
slot. A summon you spend chakra and a turn to activate is another Jutsu. Either
way it is an existing system wearing a new coat.

**The mechanic: interventions.** Every summon has a *trigger* and fires at most
once per battle, automatically, the instant its condition is met. It costs no
chakra and does not consume the ninja's turn. Summons are the only system in
the game that acts outside the turn order, which makes them read as a genuinely
separate axis — you are not choosing what to *do* with a summon, you are
choosing what your squad is *insured against*.

Because an unspent intervention would otherwise be a dead slot, each pact also
carries a small always-on bond bonus.

| Summon | Trigger | Intervention |
| --- | --- | --- |
| Gamaza (toad) | bonded ninja below 35% HP | heavy shielding barrier |
| Enma (monkey) | bonded ninja below 35% HP | adamantine guard + counter stance |
| Sagiri (crane) | bonded ninja below 35% HP | squad-wide restorative mist |
| Byakko (fox) | blow would kill the bonded ninja | negates it, leaves them at 1 HP |
| Kiba (wolf) | any ally falls | pack frenzy, attack up for the squad |
| Inoshishi (boar) | round three | shattering charge, breaks guard |
| Murasaki (serpent) | round three | stacking venom on the strongest foe |
| Shirakaze (hawk) | battle start | squad speed and first-strike priority |
| Genbu (turtle) | battle start | standing damage reduction |
| Kabuto (beetle) | bonded ninja's chakra falls to 25% | chakra transfusion |

Ten summons, each with cropped generated art. A bonded creature is drawn beside
its ninja's portrait, but only in the large portrait views — in the roster,
squad, report and mission lists it is suppressed so the overhanging art cannot
collide with neighbouring rows.

Pulls come from a dedicated summon gacha, separate from the equipment one.

**Verification.** Triggers were checked with a throwaway simulation harness
across 60 losing battles per summon; all ten now fire reliably. Two bugs were
found and fixed this way:

- `chakra_empty` never fired. It was originally checked inside the round tick,
  which runs *after* chakra regeneration, so it only ever saw a topped-up
  value. Moving it to the chakra-spend sites was still wrong — there are seven
  such sites and the common ones were missed. It is now checked once at the end
  of `doAction`, a single choke point a future action type cannot bypass.
- The 25% threshold itself: at +3 regen per round, chakra bottoms out around
  18% of maximum, so the original 15% trigger was mathematically unreachable.

## 3. Tree variety

The elemental lanes drew from one small effect pool, so the same decision
recurred in different colours. Five new mechanics now anchor a new fifth lane
per element:

- **drain** (Fire, *Consumption*) — damage over time that heals the caster.
- **mark** (Water, *Erosion*) — marked targets take amplified damage from
  everyone, rewarding focus fire.
- **echo** (Wind, *Delay*) — a portion of the hit lands again next round.
- **siphon** (Earth, *Siphon*) — steals chakra rather than dealing damage.
- **momentum** (Lightning, *Cascade*) — consecutive uses escalate; `Final
  Relay` at full momentum is intentionally the hardest-hitting single
  elemental technique in the game, and the ramp is the cost.

Two new Genjutsu schools attack targets nothing else touched:

- **Famine** (飢) — burns chakra per round, denying the enemy their economy.
- **Reflection** (鏡) — rebounds a share of damage onto the attacker. Cast on
  an enemy it also feeds the caster health on each rebound; cast on an ally it
  is pure protection. Reflected damage never routes back through the damage
  function, so two reflections cannot chain into a loop.

Content totals afterwards: **833** jutsu ids with no duplicates, and **30**
genjutsu ids across eight schools.

## Applying it

`overrides/apply_v18_content_expansion.py` applies
`overrides/v18_content_expansion.patch` to `app/`, copies the ten summon images
from `summon_assets_v18/`, and verifies every landmark. It is idempotent, so
the Kage Life branch build can re-run it over the already-patched main
artifact safely.

Verified: the script applies cleanly to a from-scratch v17 tree and reproduces
this working tree byte-for-byte, `tsc --noEmit` is clean, and `vite build`
succeeds.

## Action required from you

The build automation runs with a token that has no GitHub `workflows`
permission, so the CI step cannot be pushed directly to the files under
`.github/workflows/`. It is therefore staged as two ready-to-apply patches
(exactly as v17 was shipped). Apply them to complete the wiring:

    git apply overrides/v18_workflow_step.patch
    git apply overrides/v18_workflow_step_kage_life.patch

Both patches are verified to apply cleanly, individually and together. They
insert an "Apply v18 content expansion" step immediately after the v17 step
and before the patched-source snapshot upload:

- `overrides/v18_workflow_step.patch` → `.github/workflows/build-apk.yml`.
  Runs `python overrides/apply_v18_content_expansion.py` and verifies the
  summon/battle/genjutsu/bingo landmarks plus the summon artwork.
- `overrides/v18_workflow_step_kage_life.patch` →
  `.github/workflows/build-kage-life-branch.yml`. Runs the same step; the
  script is idempotent, so re-running it over the already-patched main
  artifact the branch downloads is a no-op verification (mirrors v17).

The frozen `build-v16-apk.yml` deliberately stops at v16 and does not receive
the step.
