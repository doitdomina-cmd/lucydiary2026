const CACHE_NAME = 'novel-writer-v11';
const ASSETS = ['./novel.html', './novel-manifest.json', './icon-192.png', './icon-512.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k.startsWith('novel-writer-') && k !== CACHE_NAME).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

// 네트워크 우선: 온라인이면 최신 파일, 오프라인일 때만 캐시 사용 (같은 출처 GET만)
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  event.respondWith(
    fetch(req)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        return response;
      })
      .catch(() => caches.match(req))
  );
});
