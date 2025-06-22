
const CACHE_NAME = 'baduk-lectures-basic-v1';

// Only cache static assets - no dynamic content
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
  '/static/images/favicons/favicon-16x16.png',
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

// Helper function to check if request is for static resources only
function isStaticResource(url) {
  const pathname = new URL(url).pathname;
  return pathname.startsWith('/static/') || pathname === '/manifest.json';
}

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

// Basic fetch strategy - only cache static resources
self.addEventListener('fetch', (event) => {
  // Only handle static resources
  if (!isStaticResource(event.request.url)) {
    // For non-static resources, just fetch from network
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        // Return cached response if available
        if (cachedResponse) {
          return cachedResponse;
        }
        
        // Fetch from network and cache if it's a static resource
        return fetch(event.request)
          .then((response) => {
            // Only cache successful responses
            if (response && response.status === 200) {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, responseToCache);
                });
            }
            return response;
          });
      })
  );
});
