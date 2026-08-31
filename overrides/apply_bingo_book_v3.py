from pathlib import Path

ROOT = Path("app")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, value: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding="utf-8")


# ---------------------------------------------------------------------------
# Bingo Book v3: expand the three authored prototypes into the complete
# 80-target endgame roster, all using the committed unique battle portraits.
# ---------------------------------------------------------------------------
p = "src/game/bingo.ts"
s = read(p)

if "BINGO_GENERATED_NAMES" not in s:
    anchor = "];\n\nexport const BINGO_TARGET_BY_ID"
    if anchor not in s:
        raise SystemExit("Bingo v3 roster anchor not found")

    roster = r'''

const BINGO_GENERATED_NAMES = [
  "Daichi", "Ayame", "Toru", "Shiori", "Goro", "Naoko", "Riku", "Hotaru", "Jin", "Kanna",
  "Masaru", "Yuna", "Isamu", "Reika", "Kenshin", "Mei", "Akio", "Sayuri", "Haru", "Chiyo",
  "Raiden", "Natsumi", "Kuro", "Emiko", "Shin", "Kaede", "Ryo", "Mika", "Genji", "Fumiko",
  "Hayate", "Airi", "Osamu", "Ren", "Satsuki", "Takao", "Nozomi", "Kiyoshi", "Yori", "Atsuko",
  "Makoto", "Hana", "Saburo", "Rin", "Koji", "Yumi", "Arata", "Nami", "Keiji", "Mio",
  "Shiro", "Asami", "Daisuke", "Koharu", "Kazuo", "Eri", "Takeshi", "Maya", "Noboru", "Suzu",
  "Yashiro", "Akane", "Tetsu", "Misaki", "Hideo", "Rena", "Jiro", "Sora", "Katsuro", "Ume",
  "Seiji", "Maki", "Ichiro", "Kiku", "Ryoma", "Nanami", "Zen",
] as const;

const BINGO_GENERATED_EPITHETS = [
  "The Stone Crow", "The Violet Fang", "The Thunder Reed", "The Silent Bloom", "The Iron Ox", "The Poison Bell", "The Gale Rat", "The Lantern Moth", "The Black Spear", "The Glass Crane",
  "The War Drum", "The Drowned Lily", "The Grave Wolf", "The Scarlet Veil", "The Broken Sword", "The Moon Needle", "The Ember Fox", "The Pale Serpent", "The Sand Kite", "The Hollow Bell",
  "The Storm Jackal", "The Snow Orchid", "The Night Ape", "The Paper Wasp", "The White Knife", "The Jade Spider", "The Red Heron", "The Mist Cat", "The Bronze Mask", "The Ash Lotus",
  "The Cutting Wind", "The Blue Scorpion", "The Bone Monk", "The Crooked Moon", "The Rain Crow", "The Mountain Hound", "The Quiet Viper", "The Iron Cicada", "The Dust Wolf", "The Thread Witch",
  "The Mirror Hawk", "The Crimson Mantis", "The Stone Tiger", "The Ghost Koi", "The Chain Hound", "The Frost Sparrow", "The Smoke Boar", "The River Ghost", "The Copper Raven", "The Black Iris",
  "The White Oni", "The Thorn Deer", "The Hollow Blade", "The Burning Crane", "The Mud Serpent", "The Silent Hornet", "The Storm Bear", "The Glass Fox", "The Iron Widow", "The Red Owl",
  "The Grave General", "The Pale Shogun", "The Black Tempest", "The Empty Crown", "The Blood Saint", "The Nine-Blade", "The Thunder Kage", "The Ash Daimyo", "The Moon Tyrant", "The Bone Emperor",
  "The White Calamity", "The Red Eclipse", "The Hollow Kage", "The Last Fang", "The Iron God", "The Black Sun", "The Nameless Storm",
] as const;

const BINGO_ELEMENT_SETS: string[][] = [
  ["Earth"], ["Fire"], ["Lightning"], ["Water"], ["Wind"],
  ["Fire", "Wind"], ["Water", "Lightning"], ["Earth", "Fire"], ["Wind", "Lightning"], ["Water", "Wind"],
  ["Earth", "Lightning"], ["Fire", "Lightning"], ["Water", "Earth"], ["Ice", "Water"], ["Magnet", "Wind"],
  ["Lava", "Earth"], ["Boil", "Water"], ["Storm", "Lightning"],
];

const BINGO_FOCUS_SETS: Skill[][] = [
  ["ken", "tac", "spd"], ["nin", "ste", "tac"], ["doj", "spd", "nin"], ["gen", "ste", "doj"],
  ["tai", "ken", "spd"], ["med", "nin", "tac"], ["ste", "spd", "ken"], ["tac", "gen", "nin"],
  ["doj", "ken", "tac"], ["tai", "nin", "spd"], ["med", "ste", "gen"], ["ken", "nin", "doj"],
];

const BINGO_MECHANICS = [
  "Opens combat with a prepared ambush unless the hunt reaches contact with superior intelligence.",
  "Every third damaging technique gains a large critical-hit bonus.",
  "Drops a decoy at half health; striking the wrong body gives the target a free action.",
  "Builds momentum when acting consecutively, increasing speed until interrupted by control effects.",
  "Marks one hunter at the start of each round; attacks against that hunter deal increased damage.",
  "Creates a two-round elemental hazard that punishes repeated use of the same action type.",
  "Converts part of incoming ninjutsu damage into chakra and releases it on the next technique.",
  "Uses a counter stance after taking heavy melee damage; tactical and genjutsu actions bypass it safely.",
  "At low health attempts to disengage unless restrained, stunned, sealed or blocked by a hunt modifier.",
  "Begins with layered armour that must be broken by sustained damage before critical hits become effective.",
  "Punishes healing with an immediate pressure attack unless the healer is protected by Guard.",
  "Rotates elemental resistance each round, rewarding mixed-element teams.",
  "Can delay one random hunter for a round by collapsing the battlefield around them.",
  "Starts with a powerful barrier that weakens for every successful pre-fight hunt event.",
  "Applies stacking bleed with weapon attacks; medical skill and cleansing techniques remove the stacks.",
  "Uses a battlefield clone whenever a hunter is downed, increasing enemy action pressure.",
  "Gains dodge chance while above half chakra, but becomes substantially easier to hit once exhausted.",
  "Charges a devastating signature technique over two rounds; stun, genjutsu or a heavy critical can interrupt it.",
  "Steals initiative after being critically hit, preventing simple burst-damage strategies.",
  "Creates sealing marks on the field; three active marks sharply reduce the hunters' chakra recovery.",
  "Recovers a small amount of health whenever an attack misses them.",
  "Alternates between offensive and defensive phases, changing the safest target priority each round.",
  "Begins enraged if the pursuit included an enemy ambush event, trading defence for very high opening damage.",
  "Carries an emergency smoke seal that gives one escape attempt below 20% health unless the route was blocked during the hunt.",
] as const;

const BINGO_CRIMES = [
  "Assassination of a contracted village operative",
  "Theft of restricted technique scrolls",
  "Attack on a border patrol",
  "Kidnapping of a chakra researcher",
  "Destruction of a merchant convoy",
  "Murder of pursuing hunter-nin",
  "Sabotage of a village supply route",
  "Illegal bloodline experimentation",
  "Raid on a fortified archive",
  "Extortion of a neutral settlement",
  "Breaking prisoners out of a shinobi transport",
  "Selling classified mission intelligence",
] as const;

function generatedThreat(index: number): BingoThreat {
  if (index >= 71) return "BLACK";
  if (index >= 61) return "SS";
  if (index >= 46) return "S+";
  if (index >= 26) return "S";
  if (index >= 11) return "A";
  return "B";
}

function generatedLevel(index: number, threat: BingoThreat): number {
  const base: Record<BingoThreat, number> = { B: 24, A: 32, S: 42, "S+": 52, SS: 62, BLACK: 72 };
  return base[threat] + ((index * 7) % 9) - 4;
}

function generatedPotential(index: number, threat: BingoThreat): 1 | 2 | 3 | 4 | 5 {
  if (threat === "BLACK" || threat === "SS" || threat === "S+") return 5;
  if (threat === "S") return index % 3 === 0 ? 5 : 4;
  if (threat === "A") return 4;
  return index % 3 === 0 ? 4 : 3;
}

function generatedCaptureChance(threat: BingoThreat): number {
  return ({ B: 0.62, A: 0.50, S: 0.36, "S+": 0.28, SS: 0.20, BLACK: 0.12 } as const)[threat];
}

function makeGeneratedBingoTarget(index: number): BingoTargetDef {
  const offset = index - 4;
  const threat = generatedThreat(index);
  const level = generatedLevel(index, threat);
  const deadBase = ({ B: 18000, A: 36000, S: 72000, "S+": 125000, SS: 195000, BLACK: 320000 } as const)[threat];
  const bountyDead = Math.round((deadBase + level * 900 + index * 275) / 1000) * 1000;
  const name = BINGO_GENERATED_NAMES[offset];
  const epithet = BINGO_GENERATED_EPITHETS[offset];
  const mechanicA = BINGO_MECHANICS[(index * 5 + 1) % BINGO_MECHANICS.length];
  const mechanicB = BINGO_MECHANICS[(index * 7 + 9) % BINGO_MECHANICS.length];
  const organisation = index >= 71 || index % 4 === 0 ? undefined : BINGO_ORGANISATIONS[(index + 1) % BINGO_ORGANISATIONS.length].id;
  const highThreat = threat === "S+" || threat === "SS" || threat === "BLACK";
  const recruitable = threat !== "BLACK" && (index % 6 === 0 || index % 11 === 0);

  return {
    id: `bb_${String(index).padStart(3, "0")}`,
    name,
    epithet,
    sprite: `/bingo/bingo_${String(index).padStart(3, "0")}.png`,
    threat,
    level,
    potential: generatedPotential(index, threat),
    elements: BINGO_ELEMENT_SETS[(index * 3) % BINGO_ELEMENT_SETS.length],
    focus: BINGO_FOCUS_SETS[(index * 5) % BINGO_FOCUS_SETS.length],
    organisationId: organisation,
    recruitable,
    bossMechanics: highThreat ? [mechanicA, mechanicB] : [mechanicA],
    summary: `${name}, known as ${epithet}, is a veteran missing-nin whose fighting style has survived repeated hunter-cell encounters. The dossier warns that their preferred tactics change rapidly once pressured.`,
    knownCrimes: [
      BINGO_CRIMES[index % BINGO_CRIMES.length],
      BINGO_CRIMES[(index * 3 + 2) % BINGO_CRIMES.length],
      BINGO_CRIMES[(index * 7 + 5) % BINGO_CRIMES.length],
    ],
    bountyDead,
    bountyAlive: Math.round((bountyDead * (threat === "BLACK" ? 1.45 : 1.30)) / 1000) * 1000,
    captureBaseChance: generatedCaptureChance(threat),
    fleeAtHp: index % 5 === 0 ? (highThreat ? 0.28 : 0.22) : undefined,
    intel: INTEL_STANDARD,
  };
}

for (let i = 4; i <= 80; i++) BINGO_TARGETS.push(makeGeneratedBingoTarget(i));
'''
    s = s.replace(anchor, "];" + roster + "\n\nexport const BINGO_TARGET_BY_ID", 1)

# Reveal the roster progressively instead of dumping 80 identified targets on
# the player at once. Twelve rumours are available immediately, then new files
# surface with time and successful hunts. The ten Black Book targets unlock as
# a later layer of the same system.
if "BINGO_PROGRESSIVE_ROSTER_V3" not in s:
    anchor = "  return b;\n}\n\nexport function bingoUnlocked"
    if anchor not in s:
        raise SystemExit("Bingo v3 progression anchor not found")
    progression = r'''  // BINGO_PROGRESSIVE_ROSTER_V3
  if (typeof b.blackBookUnlocked !== "boolean") b.blackBookUnlocked = false;
  if (typeof b.finalTargetUnlocked !== "boolean") b.finalTargetUnlocked = false;

  if (b.unlocked) {
    const resolvedStatuses: BingoTargetStatus[] = ["captured", "killed", "recruited", "resolved"];
    const standardTargets = BINGO_TARGETS.filter((target) => target.threat !== "BLACK");
    const resolvedStandard = standardTargets.filter((target) => resolvedStatuses.includes(b.targets[target.id]?.status)).length;
    const daysOpen = Math.max(0, s.day - (b.unlockedDay ?? s.day));
    const revealCount = Math.min(standardTargets.length, 12 + resolvedStandard * 2 + Math.floor(daysOpen / 4));

    for (const target of standardTargets.slice(0, revealCount)) {
      const progress = b.targets[target.id];
      if (progress && progress.intel <= 0 && progress.status === "unknown") {
        progress.intel = 5;
        progress.status = "rumoured";
      }
    }

    for (const target of standardTargets) {
      const progress = b.targets[target.id];
      if (target.organisationId && progress && (progress.intel >= 40 || resolvedStatuses.includes(progress.status)) && !b.organisationsKnown.includes(target.organisationId)) {
        b.organisationsKnown.push(target.organisationId);
      }
    }

    if (!b.blackBookUnlocked && resolvedStandard >= 24) {
      b.blackBookUnlocked = true;
      s.log.push({ txt: "Twenty-four major Bingo dossiers have been resolved. The classified Black Book has been opened.", kind: "great", id: Date.now() });
    }

    if (b.blackBookUnlocked) {
      const blackTargets = BINGO_TARGETS.filter((target) => target.threat === "BLACK");
      const resolvedBlack = blackTargets.filter((target) => resolvedStatuses.includes(b.targets[target.id]?.status)).length;
      const blackRevealCount = Math.min(blackTargets.length, 3 + resolvedBlack);
      for (const target of blackTargets.slice(0, blackRevealCount)) {
        const progress = b.targets[target.id];
        if (progress && progress.intel <= 0 && progress.status === "unknown") {
          progress.intel = 5;
          progress.status = "rumoured";
        }
      }
      if (!b.finalTargetUnlocked && resolvedBlack >= 8) {
        b.finalTargetUnlocked = true;
        s.log.push({ txt: "Eight Black Book targets have fallen. The final classified dossier has been authorised.", kind: "great", id: Date.now() });
      }
    }
  }

'''
    s = s.replace(anchor, progression + anchor, 1)

write(p, s)
print("Bingo Book full 80-target roster + progressive reveal: applied")

# ---------------------------------------------------------------------------
# UI text now reflects the real roster rather than the prototype pipeline.
# Black Book targets surface as rumours/active dossiers once classification is
# lifted; the dedicated Black Book panel continues to show unlock progress.
# ---------------------------------------------------------------------------
p = "src/components/BingoBookScreen.tsx"
s = read(p)
s = s.replace("3 target prototypes · 80-target pipeline", "80 unique targets · 10 Black Book superbosses")
s = s.replace("Eight Kage-class superboss dossiers remain classified until the village proves itself against the S-rank network.", "Ten Kage-class superboss dossiers remain classified until the village resolves 24 standard Bingo targets.")
s = s.replace("CLASSIFICATION LIFTED — roster authoring pending", "CLASSIFICATION LIFTED — Black Book rumours now appear in the active dossier lists")
write(p, s)
print("Bingo Book v3 roster UI copy: applied")

# Cache bump for the 80 new runtime portraits and roster data.
p = "public/sw.js"
s = read(p)
s = s.replace('const CACHE = "shadow-village-bingo-book-v1";', 'const CACHE = "shadow-village-bingo-book-v3-80-targets";')
write(p, s)
print("Bingo Book v3 patch complete")
