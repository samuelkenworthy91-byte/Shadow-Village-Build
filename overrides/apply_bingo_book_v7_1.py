from pathlib import Path

p = Path("app/src/App.tsx")
s = p.read_text(encoding="utf-8")

# Keep the physical Bingo Book closed when an action inside it transitions the
# game out of pause (for example starting the target battle).
old = '<BingoBookOverlay s={s} onChanged={force} onClose={() => setBingoBookOpen(false)} />'
new = '<BingoBookOverlay s={s} onChanged={() => { if (sRef.current.phase !== "paused") setBingoBookOpen(false); force(); }} onClose={() => setBingoBookOpen(false)} />'
if old not in s:
    if new in s:
        print("Bingo Book v7.1 battle-close fix already applied")
    else:
        raise SystemExit("Bingo Book v7.1 App anchor not found")
else:
    s = s.replace(old, new, 1)
    print("Bingo Book v7.1 battle-close fix applied")

# TEST BUILD ONLY: on first launch of this APK, replace save slot 3 with a
# purpose-built Kage save so the Bingo Book can be play-tested immediately.
# The marker means subsequent launches preserve whatever progress the tester
# makes in slot 3 instead of resetting it every time the app opens.
old_slots = '  const [saveSlots, setSaveSlots] = useState(() => listSaveSlots());'
new_slots = '''  const [saveSlots, setSaveSlots] = useState(() => {
    const testSeedMarker = "shadow-village-bingo-slot3-kage-test-v1";
    try {
      if (!window.localStorage.getItem(testSeedMarker)) {
        const test = eng.createState("playing");
        test.day = 40;
        test.ap = 12;
        test.gold = 500000;
        test.rice = 1200;
        test.score = 7500;
        test.raidGraceDays = 20;
        test.b = { ...test.b, hall: 5, farm: 4, tea: 3, dojo: 4, tower: 3, shrine: 3, intel: 3, anbu: 2, hospital: 3, embassy: 2 };

        const kage = test.ninjas[0];
        kage.name = "Bingo Test Kage";
        kage.title = "Village Kage · Test Unit";
        kage.rank = "kage";
        kage.level = 70;
        kage.pot = 5;
        kage.xp = 0;
        kage.sp = 30;
        kage.traits = Array.from(new Set([...kage.traits, "naturalLeader", "battleHardened", "hunterInstinct", "sealingExpert"]));
        for (const skill of Object.keys(kage.s) as Skill[]) {
          if (skill === "doj" && !kage.dojutsuAwakening) continue;
          kage.s[skill] = Math.max(kage.s[skill], skill === "tac" || skill === "ken" || skill === "nin" ? 125 : 105);
          kage.growth[skill] = Math.max(kage.growth[skill], 1.55);
        }

        // Two capable partners are included because Bingo hunts require exactly
        // three active ninja; only the lead test ninja is Kage-ranked.
        for (const support of test.ninjas.slice(1, 3)) {
          support.rank = "jonin";
          support.level = 45;
          support.pot = Math.max(4, support.pot);
          support.sp = 12;
          for (const skill of Object.keys(support.s) as Skill[]) {
            if (skill === "doj" && !support.dojutsuAwakening) continue;
            support.s[skill] = Math.max(support.s[skill], 68);
            support.growth[skill] = Math.max(support.growth[skill], 1.25);
          }
        }

        ensureBingoState(test);
        test.log.push({ txt: "TEST SAVE: Kage-class Bingo Book play-test state loaded in save slot 3.", kind: "great", id: Date.now() + 500 });
        saveSlot(3, test);
        window.localStorage.setItem(testSeedMarker, "1");
      }
    } catch {
      // A storage failure must never prevent the game booting normally.
    }
    return listSaveSlots();
  });'''
if old_slots in s:
    s = s.replace(old_slots, new_slots, 1)
    print("Bingo test slot 3 Kage seed applied")
elif testSeedMarker := "shadow-village-bingo-slot3-kage-test-v1":
    if testSeedMarker in s:
        print("Bingo test slot 3 Kage seed already applied")
    else:
        raise SystemExit("Bingo test slot 3 App save-list anchor not found")

p.write_text(s, encoding="utf-8")
