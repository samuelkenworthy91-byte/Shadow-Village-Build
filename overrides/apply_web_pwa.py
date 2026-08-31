from __future__ import annotations

import json
import re
from pathlib import Path

APP = Path("app")
PUBLIC = APP / "public"
INDEX = APP / "index.html"

if not INDEX.exists():
    raise SystemExit("app/index.html was not found; assemble the game before applying the web PWA patch")

PUBLIC.mkdir(parents=True, exist_ok=True)

manifest = {
    "name": "Shadow Village — Ninja Settlement",
    "short_name": "Shadow Village",
    "description": "Build a hidden ninja village, train shinobi, deploy squads on missions, and survive the raids.",
    "id": "./",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "display_override": ["fullscreen", "standalone"],
    "orientation": "any",
    "background_color": "#0d0e1a",
    "theme_color": "#0d0e1a",
    "categories": ["games", "strategy"],
    "icons": [
        {"src": "icon.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icon.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(PUBLIC / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

register_sw = r'''(() => {
  if (!("serviceWorker" in navigator)) return;

  const script = document.currentScript;
  const base = new URL("./", script?.src || document.baseURI);
  const workerUrl = new URL("sw.js", base);

  window.addEventListener("load", () => {
    navigator.serviceWorker.register(workerUrl, { scope: base.pathname }).catch((error) => {
      console.warn("Shadow Village service worker registration failed", error);
    });

    if (navigator.storage && typeof navigator.storage.persist === "function") {
      navigator.storage.persist().catch(() => undefined);
    }
  });
})();
'''
(PUBLIC / "register-sw.js").write_text(register_sw, encoding="utf-8")

html = INDEX.read_text(encoding="utf-8")

# Remove deployment-host-specific PWA tags so the browser build can use portable relative paths.
html = re.sub(r"\s*<link\b[^>]*\brel=[\"']manifest[\"'][^>]*>", "", html, flags=re.IGNORECASE)
html = re.sub(r"\s*<link\b[^>]*\brel=[\"']apple-touch-icon[\"'][^>]*>", "", html, flags=re.IGNORECASE)
html = re.sub(r"\s*<meta\b[^>]*\bname=[\"']apple-mobile-web-app-capable[\"'][^>]*>", "", html, flags=re.IGNORECASE)
html = re.sub(r"\s*<meta\b[^>]*\bname=[\"']apple-mobile-web-app-status-bar-style[\"'][^>]*>", "", html, flags=re.IGNORECASE)
html = re.sub(r"\s*<meta\b[^>]*\bname=[\"']apple-mobile-web-app-title[\"'][^>]*>", "", html, flags=re.IGNORECASE)
html = re.sub(r"\s*<script\b[^>]*\bsrc=[\"'][^\"']*register-sw\.js[\"'][^>]*>\s*</script>", "", html, flags=re.IGNORECASE)

viewport = '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
if re.search(r"<meta\b[^>]*\bname=[\"']viewport[\"'][^>]*>", html, flags=re.IGNORECASE):
    html = re.sub(r"<meta\b[^>]*\bname=[\"']viewport[\"'][^>]*>", viewport, html, count=1, flags=re.IGNORECASE)
else:
    html = html.replace("<head>", "<head>\n    " + viewport, 1)

pwa_head = '''
    <meta name="theme-color" content="#0d0e1a">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Shadow Village">
    <link rel="manifest" href="./manifest.webmanifest">
    <link rel="apple-touch-icon" href="./icon.png">
    <style>
      :root {
        --shadow-safe-top: env(safe-area-inset-top, 0px);
        --shadow-safe-right: env(safe-area-inset-right, 0px);
        --shadow-safe-bottom: env(safe-area-inset-bottom, 0px);
        --shadow-safe-left: env(safe-area-inset-left, 0px);
      }
      html, body, #root { min-height: 100%; min-height: 100dvh; background: #0d0e1a; }
      body { margin: 0; overscroll-behavior: none; -webkit-tap-highlight-color: transparent; }
    </style>
'''
html = html.replace("</head>", pwa_head + "  </head>", 1)
html = html.replace("</body>", '    <script src="./register-sw.js" defer></script>\n  </body>', 1)
INDEX.write_text(html, encoding="utf-8")

print("Applied portable browser/iPhone PWA metadata, relative manifest paths and service-worker bootstrap.")
