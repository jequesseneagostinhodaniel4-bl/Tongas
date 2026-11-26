const CACHE = 'tongas-v2';
const FILES = ['/', '/static/index.html', '/static/style.css', '/static/app.js', '/static/manifest.json'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(()=>self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith('/api/')) { e.respondWith(fetch(e.request).catch(()=> new Response(JSON.stringify({offline:true}), {headers:{'Content-Type':'application/json'}}))); return; }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res; }).catch(()=> caches.match('/static/index.html'))));
});