from __future__ import annotations

import hashlib
import json
from pathlib import Path

DIST = Path("app/dist")
if not DIST.exists():
    raise SystemExit("app/dist was not found; run the browser build before finalizing the PWA")

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

print(f"Finalized browser PWA with cache {cache_version} and {len(files)} precached files.")
