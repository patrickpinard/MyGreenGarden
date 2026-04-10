/**
 * MyGreenGarden V7.0 — Service Worker PWA
 * Gère le cache offline et les notifications push entrantes.
 */

'use strict';

const CACHE_NAME = 'mgg-v7-cache-v1';

// Ressources mises en cache pour le mode offline
const PRECACHE = [
  '/',
  '/dashboard',
  '/static/js/app.js',
  '/static/js/charts.js',
  '/static/manifest.json',
];


// ─── Installation ─────────────────────────────────────────────────────────────

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});


// ─── Activation (nettoyage anciens caches) ────────────────────────────────────

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});


// ─── Fetch (réseau d'abord, cache en fallback) ────────────────────────────────

self.addEventListener('fetch', event => {
  // Ne pas intercepter les appels API (toujours en direct)
  if (event.request.url.includes('/api/') || event.request.url.includes('/push/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Mettre en cache les nouvelles ressources statiques
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});


// ─── Notifications push reçues ────────────────────────────────────────────────

self.addEventListener('push', event => {
  let data = { title: 'MyGreenGarden', body: 'Notification', icon: '/static/img/icon-192.png', data: {} };

  try {
    if (event.data) {
      const payload = event.data.json();
      data = { ...data, ...payload };
    }
  } catch {
    data.body = event.data?.text() || 'Notification MyGreenGarden';
  }

  const options = {
    body:    data.body,
    icon:    data.icon || '/static/img/icon-192.png',
    badge:   '/static/img/badge-72.png',
    vibrate: [200, 100, 200],
    data:    { url: data.data?.url || '/dashboard' },
    actions: [
      { action: 'open',    title: 'Voir' },
      { action: 'dismiss', title: 'Ignorer' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});


// ─── Clic sur une notification ────────────────────────────────────────────────

self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'dismiss') return;

  const url = event.notification.data?.url || '/dashboard';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      // Ouvrir un onglet existant si possible
      const existing = clientList.find(c => c.url.includes(self.location.origin));
      if (existing) {
        existing.focus();
        existing.navigate(url);
      } else {
        clients.openWindow(url);
      }
    })
  );
});
