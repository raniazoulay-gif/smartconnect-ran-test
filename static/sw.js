// UNICO Service Worker
const CACHE = 'unico-v5';

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(clients.claim());
});

// Network-first: תמיד מביא מהשרת, fallback לcache אם אין רשת
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

// ── PUSH NOTIFICATIONS ────────────────────────────────────────────────────────
self.addEventListener('push', event => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch(e) {
    data = { title: 'UNICO', body: event.data ? event.data.text() : '' };
  }

  const title   = data.title || 'UNICO';
  const options = {
    body:     data.body  || '',
    icon:     '/static/logo.png',
    badge:    '/static/logo.png',
    dir:      'rtl',
    lang:     'he',
    tag:      'unico-chat',
    renotify: true,
    data:     { url: data.url || '/manager?tab=notifications' }
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// כותב URL ל-IndexedDB (נגיש גם לדף וגם ל-SW)
function idbWritePendingNav(url) {
  return new Promise(resolve => {
    try {
      const req = indexedDB.open('unico-nav', 1);
      req.onupgradeneeded = e => e.target.result.createObjectStore('q');
      req.onsuccess = e => {
        const tx = e.target.result.transaction('q', 'readwrite');
        tx.objectStore('q').put(url, 'pending');
        tx.oncomplete = resolve;
        tx.onerror = resolve;
      };
      req.onerror = resolve;
    } catch(e) { resolve(); }
  });
}

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/manager?tab=notifications';

  event.waitUntil((async () => {
    const all = await clients.matchAll({ type: 'window', includeUncontrolled: true });
    const existing = all.find(c => c.url.includes(self.location.origin));

    if (!existing) {
      // אפליקציה סגורה — פתח חלון חדש עם URL (IIFE מטפל בפרמטרים)
      if (clients.openWindow) await clients.openWindow(url);
      return;
    }

    // אפליקציה ברקע:
    // 1. כתוב ל-IDB (גיבוי למקרה שpostMessage לא מגיע)
    await idbWritePendingNav(url);
    // 2. focus — מביא לפורגראונד ומחכה שהדף יהיה ער
    try { await existing.focus(); } catch(e) {}
    // 3. postMessage — הדף כבר ער ובפורגראונד, מקבל מיד
    existing.postMessage({ action: 'open-notif', url });
  })());
});
