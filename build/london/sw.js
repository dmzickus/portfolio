// London trainer service worker. Network first so new deploys show up right away,
// cache fallback so drills work offline. VERSION is stamped in by build.py.
const VERSION = "__V__";
const CACHE = "london-" + VERSION;
const CORE = ["/london/", "/london/data.js?v=" + VERSION, "/london/manifest.webmanifest", "/london/icon.svg", "/london/icon-192.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith("london-") && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const fonts = url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com";
  if (!fonts && !(url.origin === location.origin && url.pathname.startsWith("/london/"))) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    if (fonts) {  // fonts never change: cache first
      const hit = await cache.match(req);
      if (hit) return hit;
    }
    try {
      const res = await fetch(req, fonts ? {} : { cache: "no-cache" });
      if (res.ok || res.type === "opaque") cache.put(req, res.clone());
      return res;
    } catch (err) {
      const hit = await cache.match(req, { ignoreSearch: req.mode === "navigate" }) ||
                  (req.mode === "navigate" && await cache.match("/london/"));
      if (hit) return hit;
      throw err;
    }
  })());
});
