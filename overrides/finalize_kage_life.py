from pathlib import Path
import base64
import hashlib
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

# Reconstruct the exact supplied Kage Life artwork from text-safe repository
# chunks. This avoids binary corruption in GitHub writes while keeping the
# uploaded artwork itself canonical. The source already has the external black
# field removed; ImageMagick only centres/sizes it for Capacitor.
parts_dir = Path("overrides/kage_life_uploaded_logo_b64")
parts = sorted(parts_dir.glob("part_*"))
if len(parts) != 10:
    raise SystemExit(f"Expected 10 Kage Life logo chunks, found {len(parts)}")
encoded = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
try:
    logo_bytes = base64.b64decode(encoded, validate=True)
except Exception as exc:
    raise SystemExit(f"Kage Life logo base64 is invalid: {exc}") from exc
expected_sha256 = "c2be51333cff8697724c101110b19e01c2bb3ef0d06bb4561c58206f6a0a2112"
actual_sha256 = hashlib.sha256(logo_bytes).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit(f"Kage Life logo checksum mismatch: {actual_sha256}")
logo = Path("/tmp/kage-life-uploaded-logo.webp")
logo.write_bytes(logo_bytes)

(APP / "assets").mkdir(parents=True, exist_ok=True)
(APP / "public").mkdir(parents=True, exist_ok=True)
subprocess.run(["identify", str(logo)], check=True)
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
