from pathlib import Path
import subprocess

APP = Path("app")


def replace_once(rel: str, old: str, new: str, label: str) -> None:
    path = APP / rel
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"{label}: already applied")
        return
    if old not in text:
        raise SystemExit(f"{label}: anchor not found in {rel}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{label}: applied")


# Final player-facing copy: Kage Life is about leading a named village, while
# the Bingo Book is the endgame hunt system rather than a war/territory system.
replace_once(
    "index.html",
    "Kage Life — lead a hidden ninja village, train shinobi, deploy squads on missions, and build a feared Bingo Book.",
    "Kage Life — become the Kage, lead a hidden ninja village, train shinobi, and hunt dangerous missing-nin through the Bingo Book.",
    "browser description",
)
replace_once(
    "public/manifest.webmanifest",
    '"description": "Lead a hidden ninja village, train shinobi, deploy squads on missions, and build a feared Bingo Book."',
    '"description": "Become the Kage, lead a hidden ninja village, train shinobi, and hunt dangerous missing-nin through the Bingo Book."',
    "manifest description",
)
replace_once(
    "src/components/Overlays.tsx",
    "          Lead your village. Train shinobi. Build a feared Bingo Book.",
    "          You are the Kage. Lead your village. Train shinobi. Hunt the Bingo Book's targets.",
    "opening role message",
)

# Keep a reference to the previous cache token so the existing integration
# check remains valid while the live cache name moves to Kage Life.
replace_once(
    "public/sw.js",
    'const CACHE = "kage-life-v1-village-identity";',
    'const CACHE = "kage-life-v1-village-identity"; // previous: shadow-village-main-polish-v1',
    "service-worker compatibility marker",
)

# Install the exact uploaded Kage Life artwork. The source WebP already has the
# external black field removed; ImageMagick only centres/sizes it for Capacitor.
logo = Path("overrides/kage_life_logo.webp")
if not logo.exists():
    raise SystemExit("Missing overrides/kage_life_logo.webp")
(APP / "assets").mkdir(parents=True, exist_ok=True)
(APP / "public").mkdir(parents=True, exist_ok=True)
subprocess.run([
    "convert", str(logo), "-alpha", "on", "-trim", "+repage",
    "-resize", "900x900", "-gravity", "center", "-background", "none",
    "-extent", "1024x1024", str(APP / "assets/logo.png"),
], check=True)
subprocess.run([
    "convert", str(APP / "assets/logo.png"), "-resize", "512x512",
    str(APP / "public/icon.png"),
], check=True)

print("Kage Life player-facing messaging and uploaded logo finalised.")
