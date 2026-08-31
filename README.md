# Shadow Village Build

Shadow Village now has three supported ways to play from the same game source:

- **Android APK** — native Android wrapper built with Capacitor.
- **Browser** — portable Vite build that can be hosted as a normal website.
- **iPhone / iPad PWA** — the browser build with iOS home-screen metadata, safe-area support, offline caching and local saves. Open the hosted build in Safari and use **Share → Add to Home Screen**.

## Build architecture

`overrides/assemble_current_game.sh` assembles the current game from the base source ZIP plus the full patch/asset stack. Both Android and browser workflows use this same assembler so gameplay content does not diverge between platforms.

### Android

Workflow: `.github/workflows/build-apk.yml`

Output artifact: `Shadow-Village-APK`

### Browser + iPhone/iPad

Workflow: `.github/workflows/build-web-pwa.yml`

Output artifact: `Shadow-Village-Browser-iPhone-PWA`

The workflow builds and validates the browser/PWA bundle and publishes the generated static site to the `gh-pages` branch. GitHub Pages needs to be enabled once in repository **Settings → Pages** with **Deploy from a branch**, branch **gh-pages**, folder **/(root)**. After that one-time repository setting, future browser/iPhone builds update the hosted game automatically.

The browser build uses relative asset paths so it works under the repository's GitHub Pages subdirectory as well as other static hosts.

## Saves

Each installation/browser profile keeps its own local Shadow Village save slots. Saves are not automatically synced between Android, desktop browsers and iPhone/iPad.
