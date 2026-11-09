/* Houlalah : mode hors ligne.
   - Pages et prévisions du site : le réseau d'abord (toujours le plus récent), la copie enregistrée si le réseau manque ou tarde trop.
   - Polices et carte (jsDelivr, Google Fonts) : copie enregistrée tout de suite, mise à jour en arrière-plan.
   - Les appels directs à Open-Meteo et les autres sites ne sont jamais enregistrés. */
const VERSION = 'houlalah-v1';
const CDN = ['cdn.jsdelivr.net', 'fonts.googleapis.com', 'fonts.gstatic.com'];
const SHELL = ['./', 'brand/symbol.svg', 'brand/wordmark.svg', 'brand/favicon.svg', 'data/forecast.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => Promise.allSettled(SHELL.map(u => c.add(u)))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

async function networkFirst(req) {
  const cache = await caches.open(VERSION);
  try {
    const res = await Promise.race([fetch(req), new Promise((_, rej) => setTimeout(() => rej(new Error('trop lent')), 6000))]);
    if (res && res.status === 200) cache.put(req, res.clone());
    return res;
  } catch (err) {
    const hit = (await cache.match(req)) || (await cache.match(req, { ignoreSearch: true }));
    if (hit) return hit;
    if (req.mode === 'navigate') { const home = await cache.match('./'); if (home) return home; }
    throw err;
  }
}

async function staleWhileRevalidate(req) {
  const cache = await caches.open(VERSION);
  const hit = await cache.match(req);
  const net = fetch(req).then(res => { if (res && (res.status === 200 || res.type === 'opaque')) cache.put(req, res.clone()); return res; }).catch(() => hit);
  return hit || net;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) e.respondWith(networkFirst(req));
  else if (CDN.includes(url.hostname)) e.respondWith(staleWhileRevalidate(req));
});
