from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

DIST = Path("app/dist")
if not DIST.exists():
    raise SystemExit("app/dist was not found; run the browser build before finalizing the PWA")

# Vite's public assets can still be referenced by application code with root-absolute
# URLs. Convert the game-owned runtime assets to document-relative URLs so one build
# works at a domain root, a GitHub Pages project subdirectory, LAN hosting, localhost,
# or any other static directory.
portable_assets = (
    "ninjas/",
    "raiders/",
    "bg-village.jpg",
    "bg-exam-arena.jpg",
    "bg-raid-field.jpg",
    "icon.png",
    "manifest.webmanifest",
    "register-sw.js",
    "sw.js",
)

text_suffixes = {".html", ".js", ".css", ".json", ".webmanifest"}
for path in sorted(p for p in DIST.rglob("*") if p.is_file() and p.suffix.lower() in text_suffixes):
    text = path.read_text(encoding="utf-8")
    original = text
    for asset in portable_assets:
        text = text.replace(f'"/{asset}', f'"./{asset}')
        text = text.replace(f"'/{asset}", f"'./{asset}")
        text = text.replace(f'`/{asset}', f'`./{asset}')
        text = text.replace(f'url(/{asset}', f'url(./{asset}')

    # The game does not need a network font request to function. Removing these two
    # hints/stylesheets makes the downloadable build genuinely offline after caching.
    if path.name == "index.html":
        text = re.sub(r'\s*<link\b[^>]*rel=["\']preconnect["\'][^>]*fonts\.googleapis\.com[^>]*>', '', text, flags=re.I)
        text = re.sub(r'\s*<link\b[^>]*rel=["\']preconnect["\'][^>]*fonts\.gstatic\.com[^>]*>', '', text, flags=re.I)
        text = re.sub(r'\s*<link\b[^>]*href=["\']https://fonts\.googleapis\.com/[^"\']+["\'][^>]*>', '', text, flags=re.I)

    if text != original:
        path.write_text(text, encoding="utf-8")

# Fail loudly if a future patch reintroduces one of the known root-absolute runtime
# asset forms into the compiled browser output.
compiled_text = "\n".join(
    p.read_text(encoding="utf-8")
    for p in sorted(DIST.rglob("*"))
    if p.is_file() and p.suffix.lower() in text_suffixes
)
for asset in portable_assets:
    forbidden = (f'"/{asset}', f"'/{asset}", f'`/{asset}', f'url(/{asset}')
    if any(token in compiled_text for token in forbidden):
        raise SystemExit(f"browser dist still contains a root-absolute runtime asset reference for {asset}")

files: list[str] = []
hash_state = hashlib.sha256()
for path in sorted(p for p in DIST.rglob("*") if p.is_file() and p.name != "sw.js"):
    rel = path.relative_to(DIST).as_posix()
    files.append(f"./{rel}")
    hash_state.update(rel.encode("utf-8"))
    hash_state.update(b"\0")
    hash_state.update(path.read_bytes())
    hash_state.update(b"\0")

if "./index.html" not in files:
    raise SystemExit("browser dist is missing index.html")

cache_version = hash_state.hexdigest()[:16]
precache_json = json.dumps(files, ensure_ascii=False, separators=(",", ":"))

worker = f'''// Generated after the Vite build so hashed JS/CSS and all game assets are cached correctly.
const CACHE = "shadow-village-web-{cache_version}";
const CACHE_PREFIX = "shadow-village-web-";
const PRECACHE = {precache_json};
const BASE = self.registration.scope;
const absolute = (relative) => new URL(relative.replace(/^\.\//, ""), BASE).href;
const INDEX = absolute("./index.html");

async function precacheAll() {{
  const cache = await caches.open(CACHE);
  const urls = PRECACHE.map(absolute);
  const batchSize = 24;
  for (let i = 0; i < urls.length; i += batchSize) {{
    const batch = urls.slice(i, i + batchSize);
    await Promise.allSettled(batch.map(async (url) => {{
      try {{
        const response = await fetch(url, {{ cache: "reload" }});
        if (response.ok) await cache.put(url, response.clone());
      }} catch (_) {{
        // A transient failure should not prevent the PWA from installing.
      }}
    }}));
  }}
}}

self.addEventListener("install", (event) => {{
  self.skipWaiting();
  event.waitUntil(precacheAll());
}});

self.addEventListener("activate", (event) => {{
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
}});

self.addEventListener("fetch", (event) => {{
  const request = event.request;
  if (request.method !== "GET") return;

  if (request.mode === "navigate") {{
    event.respondWith(
      fetch(request)
        .then((response) => {{
          if (response.ok) {{
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(INDEX, copy));
          }}
          return response;
        }})
        .catch(() => caches.match(INDEX))
    );
    return;
  }}

  event.respondWith(
    caches.match(request).then((cached) => {{
      if (cached) return cached;
      return fetch(request).then((response) => {{
        if (response.ok && new URL(request.url).origin === self.location.origin) {{
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
        }}
        return response;
      }});
    }})
  );
}});
'''

(DIST / "sw.js").write_text(worker, encoding="utf-8")
(DIST / ".nojekyll").write_text("", encoding="utf-8")

print(f"Finalized portable browser PWA with cache {cache_version} and {len(files)} precached files.")
