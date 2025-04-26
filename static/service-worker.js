/**
 * Snap Lotto Service Worker
 * Provides offline functionality and improved performance for the Snap Lotto PWA
 */

// Cache name - increment version number when making significant changes
const CACHE_NAME = 'snap-lotto-cache-v1';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/',
  '/static/css/custom.css',
  '/static/css/lottery.css',
  '/static/css/mobile.css',
  '/static/js/mobile-enhancements.js',
  '/static/js/ads.js',
  '/static/manifest.json',
  '/static/icons/android-chrome-192x192.png',
  '/static/icons/android-chrome-512x512.png',
  '/static/icons/favicon-16x16.png',
  '/static/icons/favicon-32x32.png',
  '/static/apple-touch/apple-icon-180x180.png',
  '/templates/offline.html'
];

// App shell paths that should always come from the cache first
const CACHE_FIRST_ASSETS = [
  '/static/',
  '/static/css/',
  '/static/js/',
  '/static/icons/',
  '/static/apple-touch/'
];

// Routes that should be available offline
const OFFLINE_ROUTES = [
  '/',
  '/results',
  '/scanner-landing',
  '/ticket-scanner',
  '/visualizations'
];

// Install event - precache important assets
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service worker precaching assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service worker deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service worker activated and controlling the page');
      return self.clients.claim();
    })
  );
});

// Helper function to determine if a request is for an asset that should be cached
function isCacheableAsset(url) {
  const requestUrl = new URL(url);
  
  // Check if it matches any of our cache-first patterns
  return CACHE_FIRST_ASSETS.some(path => requestUrl.pathname.startsWith(path));
}

// Helper function to determine if a request is for a route that should have offline support
function isOfflineRoute(url) {
  const requestUrl = new URL(url);
  
  // Check if it's an HTML request for a main route
  const isHTMLRequest = requestUrl.pathname === '/' || !requestUrl.pathname.includes('.');
  
  return isHTMLRequest && OFFLINE_ROUTES.some(route => 
    requestUrl.pathname === route || 
    requestUrl.pathname === `${route}/`
  );
}

// Helper function to determine if a request is for an API
function isAPIRequest(url) {
  const requestUrl = new URL(url);
  return requestUrl.pathname.startsWith('/api/');
}

// Fetch event - handle caching strategy based on request type
self.addEventListener('fetch', event => {
  const requestUrl = new URL(event.request.url);

  // Skip cross-origin requests
  if (requestUrl.origin !== location.origin) {
    return;
  }

  // For API requests, use network first with cache fallback
  if (isAPIRequest(event.request.url)) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Only cache successful responses
          if (response.ok) {
            const clonedResponse = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => cache.put(event.request, clonedResponse));
          }
          return response;
        })
        .catch(() => {
          // If network fails, try to get from cache
          return caches.match(event.request);
        })
    );
    return;
  }

  // For cacheable assets, use cache first with network fallback
  if (isCacheableAsset(event.request.url)) {
    event.respondWith(
      caches.match(event.request)
        .then(cachedResponse => {
          if (cachedResponse) {
            // Return cached response but also update cache in background
            const fetchPromise = fetch(event.request)
              .then(networkResponse => {
                if (networkResponse.ok) {
                  caches.open(CACHE_NAME)
                    .then(cache => cache.put(event.request, networkResponse.clone()));
                }
                return networkResponse;
              })
              .catch(() => {
                console.log('Failed to update asset in cache, but using cached version');
              });
            
            // Return cached response immediately
            return cachedResponse;
          }
          
          // If not in cache, fetch from network and cache
          return fetch(event.request)
            .then(response => {
              if (!response || !response.ok) {
                console.log('Failed to fetch asset:', requestUrl.pathname);
                return response;
              }

              // Cache the response
              const responseToCache = response.clone();
              caches.open(CACHE_NAME)
                .then(cache => cache.put(event.request, responseToCache));
              
              return response;
            });
        })
    );
    return;
  }

  // For main routes that should work offline
  if (isOfflineRoute(event.request.url)) {
    event.respondWith(
      // Try network first
      fetch(event.request)
        .then(response => {
          // Cache the response for offline use
          const clonedResponse = response.clone();
          caches.open(CACHE_NAME)
            .then(cache => cache.put(event.request, clonedResponse));
          
          return response;
        })
        .catch(error => {
          console.log('Fetch failed, serving cached version or offline page:', error);
          
          // Try to get from cache
          return caches.match(event.request)
            .then(cachedResponse => {
              // If in cache, return that
              if (cachedResponse) {
                return cachedResponse;
              }
              
              // Otherwise, return the offline page
              return caches.match('/templates/offline.html');
            });
        })
    );
    return;
  }

  // Default behavior for all other requests - network first, then cache
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Cache successful HTML responses
        if (response.ok && (response.headers.get('content-type') || '').includes('text/html')) {
          const clonedResponse = response.clone();
          caches.open(CACHE_NAME)
            .then(cache => cache.put(event.request, clonedResponse));
        }
        return response;
      })
      .catch(() => {
        // If network fails, try the cache
        return caches.match(event.request)
          .then(cachedResponse => {
            // If in cache, return that
            if (cachedResponse) {
              return cachedResponse;
            }
            
            // If it was an HTML request, return the offline page
            if (event.request.headers.get('accept').includes('text/html')) {
              return caches.match('/templates/offline.html');
            }
            
            // Otherwise, we can't fulfill this request
            console.log('No cached content available for:', event.request.url);
          });
      })
  );
});

// Push event - handle push notifications
self.addEventListener('push', event => {
  if (!event.data) {
    console.log('Push event but no data');
    return;
  }
  
  try {
    const data = event.data.json();
    const title = data.title || 'Snap Lotto';
    const options = {
      body: data.body || 'New lottery data available',
      icon: '/static/icons/android-chrome-192x192.png',
      badge: '/static/icons/favicon-32x32.png',
      data: data.url || '/',
      vibrate: [100, 50, 100],
      actions: [
        {
          action: 'view',
          title: 'View',
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(title, options)
    );
  } catch (error) {
    console.error('Error handling push event:', error);
  }
});

// Notification click event
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  // Get the URL from the notification data if available
  const urlToOpen = event.notification.data || '/';
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    })
    .then(windowClients => {
      // Check if there is already a window open with the URL
      for (const client of windowClients) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      // If no window is open with URL, open it
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Log when service worker is run
console.log('Snap Lotto service worker loaded');