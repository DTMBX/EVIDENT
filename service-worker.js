// Service Worker for BarberX Progressive Web App (PWA)
// Enables offline mode, caching, and push notifications

const CACHE_NAME = 'barberx-v1.0.0';
const RUNTIME_CACHE = 'barberx-runtime';

// Files to cache immediately on install
const PRECACHE_URLS = [
  '/',
  '/command-center',
  '/evidence/dashboard',
  '/integrated-analysis',
  '/assets/css/main.css',
  '/assets/css/dashboard.css',
  '/assets/js/main.js',
  '/offline.html'
];

// Install event - cache essential files
self.addEventListener('install', event => {
  console.log('[ServiceWorker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[ServiceWorker] Caching app shell');
        return cache.addAll(PRECACHE_URLS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(cacheName => {
            return cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE;
          })
          .map(cacheName => {
            console.log('[ServiceWorker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fall back to network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // API requests - network first, cache as fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }
  
  // Evidence files - network only (too large to cache)
  if (url.pathname.startsWith('/uploads/') || url.pathname.startsWith('/exports/')) {
    event.respondWith(fetch(request));
    return;
  }
  
  // Everything else - cache first, network as fallback
  event.respondWith(cacheFirst(request));
});

// Cache-first strategy
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  
  if (cached) {
    console.log('[ServiceWorker] Serving from cache:', request.url);
    return cached;
  }
  
  try {
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.status === 200) {
      const responseClone = response.clone();
      cache.put(request, responseClone);
    }
    
    return response;
  } catch (error) {
    console.error('[ServiceWorker] Fetch failed:', error);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlinePage = await cache.match('/offline.html');
      if (offlinePage) {
        return offlinePage;
      }
    }
    
    throw error;
  }
}

// Network-first strategy (for API calls)
async function networkFirst(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  
  try {
    const response = await fetch(request);
    
    // Cache successful API responses
    if (response.status === 200) {
      const responseClone = response.clone();
      cache.put(request, responseClone);
    }
    
    return response;
  } catch (error) {
    console.log('[ServiceWorker] Network failed, serving from cache:', request.url);
    
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    
    // Return error response
    return new Response(JSON.stringify({
      error: 'Offline',
      message: 'You are currently offline. Some features may be unavailable.'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Push notification handler
self.addEventListener('push', event => {
  console.log('[ServiceWorker] Push received:', event);
  
  let data = {
    title: 'BarberX Notification',
    body: 'You have a new update',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    tag: 'barberx-notification',
    requireInteraction: false
  };
  
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    tag: data.tag,
    requireInteraction: data.requireInteraction,
    data: {
      url: data.url || '/',
      timestamp: Date.now()
    },
    actions: [
      { action: 'open', title: 'Open', icon: '/assets/icons/open.png' },
      { action: 'dismiss', title: 'Dismiss', icon: '/assets/icons/close.png' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  console.log('[ServiceWorker] Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(windowClients => {
        // Check if there's already a window open
        for (let client of windowClients) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background sync (for offline evidence uploads)
self.addEventListener('sync', event => {
  console.log('[ServiceWorker] Background sync:', event.tag);
  
  if (event.tag === 'sync-evidence-uploads') {
    event.waitUntil(syncEvidenceUploads());
  }
});

async function syncEvidenceUploads() {
  // Get pending uploads from IndexedDB
  // Upload when connection is restored
  console.log('[ServiceWorker] Syncing evidence uploads...');
  
  try {
    // Implementation would fetch from IndexedDB and retry failed uploads
    // This is a placeholder for the actual sync logic
    return Promise.resolve();
  } catch (error) {
    console.error('[ServiceWorker] Sync failed:', error);
    throw error;
  }
}

// Periodic background sync (for checking new evidence analysis)
self.addEventListener('periodicsync', event => {
  console.log('[ServiceWorker] Periodic sync:', event.tag);
  
  if (event.tag === 'check-analysis-updates') {
    event.waitUntil(checkForUpdates());
  }
});

async function checkForUpdates() {
  try {
    const response = await fetch('/api/evidence/updates');
    const data = await response.json();
    
    if (data.hasUpdates) {
      // Show notification about new analysis results
      await self.registration.showNotification('Analysis Complete', {
        body: `${data.count} evidence file(s) have been analyzed`,
        icon: '/assets/icons/icon-192x192.png',
        tag: 'analysis-complete',
        data: { url: '/command-center' }
      });
    }
  } catch (error) {
    console.error('[ServiceWorker] Update check failed:', error);
  }
}

// Message handler (for communication with main app)
self.addEventListener('message', event => {
  console.log('[ServiceWorker] Message received:', event.data);
  
  if (event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
  
  if (event.data.action === 'clearCache') {
    event.waitUntil(
      caches.delete(CACHE_NAME).then(() => {
        return caches.delete(RUNTIME_CACHE);
      })
    );
  }
});

console.log('[ServiceWorker] Loaded successfully');
