/**
 * Deprecated service worker — intentionally neutralized.
 *
 * The previous version used a cache-first strategy that served a stale app
 * shell to returning users forever, breaking every deploy. The app no longer
 * uses offline SW caching. This self-destructing worker unregisters itself and
 * deletes all caches so any browser still holding the old worker recovers on
 * its next visit.
 */
self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
      await self.registration.unregister();
      const clients = await self.clients.matchAll({ type: "window" });
      clients.forEach((client) => client.navigate(client.url));
    })(),
  );
});

// Never intercept fetches — always go to network.
