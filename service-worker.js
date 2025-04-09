
const CACHE_NAME = 'baduk-lectures-v2';
const STATIC_RESOURCES = [
  '/static/css/style.css',
  '/static/css/pwa-install.css',
  '/static/css/admin.css',
  '/static/js/theme.js',
  '/static/js/search.js',
  '/static/js/video.js',
  '/static/js/main.js',
  '/static/js/pwa-install.js',
  '/static/js/register-sw.js',
  '/static/images/logo.webp',
  '/static/images/og-image.png',
  '/static/images/favicons/favicon.ico',
  '/static/images/favicons/android-chrome-512x512.png',
  '/static/images/favicons/android-chrome-192x192.png',
  '/static/images/favicons/apple-touch-icon.png',
  '/static/images/favicons/favicon-32x32.png',
  '/static/images/screenshots/mobile.png',
  '/static/images/screenshots/home.png',
  '/static/images/screenshots/collections.png',
  '/static/images/screenshots/about1.png',
  '/static/images/screenshots/about2.png',
  '/static/manifest.json'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(STATIC_RESOURCES);
      })
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event with improved error handling
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        
        // Clone the request because it's a one-time use stream
        const fetchRequest = event.request.clone();
        
        return fetch(fetchRequest)
          .then((response) => {
            // Check if valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone the response because it's a one-time use stream
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then((cache) => {
                // Only cache same-origin requests to avoid CORS issues
                if (event.request.url.startsWith(self.location.origin)) {
                  cache.put(event.request, responseToCache);
                }
              });
              
            return response;
          })
          .catch(() => {
            // Return a fallback or just re-throw the error
            // If it's a navigation request, could return a cached fallback page
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
            
            // Otherwise just propagate the error
            throw new Error('Network request failed');
          });
      })
  );
});
