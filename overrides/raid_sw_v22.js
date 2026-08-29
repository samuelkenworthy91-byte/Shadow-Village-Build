// Offline shell for Shadow Village. Ninja portraits are external PNG assets,
// so pre-cache the complete 80-character art library as well as the app shell.
const CACHE = "shadow-village-v5-raiders10-field";
const NINJA_ART = Array.from({ length: 80 }, (_, i) => `/ninjas/ninja_${String(i + 1).padStart(3, "0")}.png`);
const RAIDER_ART = ["rogue_genin","bandit_scout","war_monk","ash_bowman","oni_brawler","mist_assassin","clan_guard","torch_saboteur","clan_captain","dread_veteran"].map((n) => `/raiders/${n}.webp`);
const ASSETS = ["/", "/index.html", "/icon.png", "/logo.png", "/bg-village.jpg", "/bg-raid-field.jpg", "/manifest.webmanifest", ...NINJA_ART, ...RAIDER_ART];

self.addEventListener("install", (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS).catch(() => undefined)));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("/index.html", copy));
          return res;
        })
        .catch(() => caches.match("/index.html").then((r) => r || caches.match("/")))
    );
    return;
  }
  e.respondWith(
    caches.match(req).then(
      (hit) =>
        hit ||
        fetch(req).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
    )
  );
});
