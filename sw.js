// Offline shell for Kage Life. Ninja portraits are external PNG assets,
// so pre-cache the 340 approved portraits as well as the app shell.
// Previous cache: shadow-village-bingo-book-v7-physical-dossier
const CACHE = "kage-life-v8-jutsu-mechanics"; // previous: shadow-village-main-polish-v1, kage-life-v1-village-identity
const NINJA_ART = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 57, 59, 60, 61, 62, 63, 64, 65, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 163, 164, 165, 166, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 194, 195, 196, 197, 198, 199, 200, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 214, 215, 216, 217, 218, 219, 220, 222, 223, 224, 226, 228, 230, 231, 232, 233, 235, 236, 237, 238, 240, 241, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369].map((id) => `./ninjas/ninja_${String(id).padStart(3, "0")}.png`);
const RAIDER_ART = ["rogue_genin","bandit_scout","war_monk","ash_bowman","oni_brawler","mist_assassin","clan_guard","torch_saboteur","clan_captain","dread_veteran"].map((n) => `./raiders/${n}.webp`);
const BLD_ART = ["./buildings/bld_anbu.webp", "./buildings/bld_dojo.webp", "./buildings/bld_embassy.webp", "./buildings/bld_farm.webp", "./buildings/bld_hall.webp", "./buildings/bld_hospital.webp", "./buildings/bld_intel.webp", "./buildings/bld_shrine.webp", "./buildings/bld_tea.webp", "./buildings/bld_tower.webp"];
const SUMMON_ART = ["toad", "hawk", "wolf", "serpent", "monkey", "turtle", "beetle", "crane", "boar", "fox"].map(n => `./summons/${n}.png`);
const ASSETS = ["./", "./index.html", "./icon.png", "./logo.png", "./bg-village.jpg", "./bg-raid-field.jpg", "./bg-exam-arena.jpg", "./manifest.webmanifest", ...NINJA_ART, ...RAIDER_ART, ...BLD_ART, ...SUMMON_ART];

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
          caches.open(CACHE).then((c) => c.put("./index.html", copy));
          return res;
        })
        .catch(() => caches.match("./index.html").then((r) => r || caches.match("./")))
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
