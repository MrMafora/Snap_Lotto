// Service Worker for Snap Lotto PWA
const CACHE_NAME = 'snaplotto-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/offline',
  '/static/css/custom.css',
  '/static/css/lottery.css',
  '/static/js/ads.js',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Install event - cache initial assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching files');
        cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('Service Worker: Clearing old cache');
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached response if available
        if (response) {
          return response;
        }
        
        // Clone the request for network attempt
        const fetchRequest = event.request.clone();
        
        // Try network and cache the response if successful
        return fetch(fetchRequest)
          .then(response => {
            // Don't cache if response is invalid or not GET request
            if (!response || response.status !== 200 || response.type !== 'basic' || event.request.method !== 'GET') {
              return response;
            }
            
            // Clone the response for caching and returning
            const responseToCache = response.clone();
            
            // Add response to cache
            caches.open(CACHE_NAME)
              .then(cache => {
                // Only cache same-origin resources
                if (event.request.url.startsWith(self.location.origin)) {
                  cache.put(event.request, responseToCache);
                }
              });
              
            return response;
          })
          .catch(() => {
            // If both cache and network fail, show offline page for HTML requests
            if (event.request.headers.get('Accept').includes('text/html')) {
              return caches.match('/offline');
            }
          });
      })
  );
});