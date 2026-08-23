const CACHE = 'beast-v1';
const ASSETS = [
  '/',
  '/static/index.html',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css',
  'https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js',
  'https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js',
  'https://cdn.jsdelivr.net/npm/socket.io-client@4.7.4/dist/socket.io.min.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Network-first for WebSocket/API, cache-first for static
  if (e.request.method !== 'GET' || e.request.url.includes('socket.io')) return;
  e.respondWith(
    caches.match(e.request).then(cached => {
      const fetchPromise = fetch(e.request).then(resp => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return resp;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});