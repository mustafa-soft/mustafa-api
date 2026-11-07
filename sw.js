const V = 'ms-v2';
const SHELL = ['/', '/manifest.json', '/192x192_.png', '/512x512_.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(V)
      .then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== V).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || u.origin !== location.origin) return;
  // الصفحة الرئيسية: الشبكة أولًا ثم النسخة المحفوظة عند انقطاع النت
  if (r.mode === 'navigate' && u.pathname === '/') {
    e.respondWith(
      fetch(r)
        .then(res => { const cp = res.clone(); caches.open(V).then(c => c.put('/', cp)); return res; })
        .catch(() => caches.match('/'))
    );
    return;
  }
  // الملفات الثابتة فقط. أي مسار آخر (الخدمات، الطلبات، الإدارة) يمر مباشرة دون تخزين
  if (SHELL.includes(u.pathname)) {
    e.respondWith(caches.match(r).then(hit => hit || fetch(r)));
  }
});
