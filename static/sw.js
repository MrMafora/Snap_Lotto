// Snap Lotto Service Worker  
// Version 1.0.5 - CRITICAL FIX - Converted prediction_result to native dict to prevent string iteration

const CACHE_NAME = 'snap-lotto-v6-dict-fix';
const urlsToCache = [
  '/',
  '/static/css/lottery.css',
  '/static/css/custom.css',
  '/static/css/badge-fix.css',
  '/static/css/dropdown-fix.css',
  '/static/css/pwa-mobile.css',
  '/static/css/lottery-results-fix.css',
  '/static/css/mobile-charts.css',
  '/static/js/mobile-optimized.js',
  '/static/js/chart-renderer.js',
  '/static/js/ads.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/ticket-scanner',
  '/results',
  '/analytics'
];

// Install Service Worker
self.addEventListener('install', function(event) {
  console.log('Snap Lotto SW: Installing service worker');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Snap Lotto SW: Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .catch(function(error) {
        console.log('Snap Lotto SW: Cache install failed:', error);
      })
  );
});

// Fetch events - Network First strategy for dynamic content
self.addEventListener('fetch', function(event) {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(function(response) {
        // If we got a response, clone it and store it in the cache
        if (response.status === 200) {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            });
        }
        return response;
      })
      .catch(function() {
        // Network failed, try to get it from the cache
        return caches.match(event.request)
          .then(function(response) {
            if (response) {
              return response;
            }
            // If not in cache and it's a navigation request, return the homepage
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
            return new Response('Offline - Content not available', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({
                'Content-Type': 'text/plain'
              })
            });
          });
      })
  );
});

// Activate Service Worker
self.addEventListener('activate', function(event) {
  console.log('Snap Lotto SW: Activating service worker');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('Snap Lotto SW: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Handle background sync for lottery data updates
self.addEventListener('sync', function(event) {
  if (event.tag === 'lottery-data-sync') {
    console.log('Snap Lotto SW: Background sync triggered for lottery data');
    event.waitUntil(syncLotteryData());
  }
});

// Background sync function
function syncLotteryData() {
  return fetch('/api/lottery-analysis/frequency?days=365')
    .then(function(response) {
      if (response.ok) {
        console.log('Snap Lotto SW: Lottery data synced successfully');
        return response.json();
      }
    })
    .catch(function(error) {
      console.log('Snap Lotto SW: Background sync failed:', error);
    });
}

// Handle push notifications (for future lottery result alerts)
self.addEventListener('push', function(event) {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || 'New lottery results available!',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-72x72.png',
      vibrate: [200, 100, 200],
      data: {
        url: data.url || '/',
        timestamp: Date.now()
      },
      actions: [
        {
          action: 'view-results',
          title: 'View Results',
          icon: '/static/icons/icon-96x96.png'
        },
        {
          action: 'scan-ticket',
          title: 'Scan Ticket',
          icon: '/static/icons/icon-96x96.png'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification(data.title || 'Snap Lotto', options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  let targetUrl = '/';
  if (event.action === 'view-results') {
    targetUrl = '/results';
  } else if (event.action === 'scan-ticket') {
    targetUrl = '/ticket-scanner';
  } else if (event.notification.data && event.notification.data.url) {
    targetUrl = event.notification.data.url;
  }

  event.waitUntil(
    clients.matchAll().then(function(clientList) {
      // Check if there's already a window/tab open with the target URL
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url.includes(targetUrl) && 'focus' in client) {
          return client.focus();
        }
      }
      // If no existing window/tab, open a new one
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});

console.log('Snap Lotto SW: Service worker script loaded');