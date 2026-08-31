(() => {
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
