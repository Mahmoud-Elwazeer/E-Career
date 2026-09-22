import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import '@/i18n/i18n';

/**
 * Service-worker kill switch.
 *
 * A legacy cache-first service worker (public/sw.js) was shipped previously and
 * is still registered in some returning browsers, where it serves a STALE app
 * shell forever (ignoring hard refresh + query strings) — which made new
 * deploys appear "not to update". The app does not use offline SW caching, so
 * we unregister any existing worker and purge its caches on every load. This
 * self-heals stranded browsers on their next visit. Safe no-op when no SW
 * exists.
 */
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((reg) => reg.unregister());
  }).catch(() => {});
  if (window.caches?.keys) {
    caches.keys().then((keys) => keys.forEach((k) => caches.delete(k))).catch(() => {});
  }
}

createRoot(document.getElementById("root")!).render(<App />);
