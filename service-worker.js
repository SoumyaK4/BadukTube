
const CACHE_NAME = 'baduk-lectures-v1';
const STATIC_RESOURCES = [
  '/static/css/style.css',
  '/static/css/pwa-install.css',
  '/static/css/mobile-menu.css',
  '/static/js/theme.js',
  '/static/js/search.js',
  '/static/js/video.js',
  '/static/js/mobile-menu.js',
  '/static/js/main.js',
  '/static/js/pwa-install.js',
  '/static/images/logo.webp',
  '/static/images/favicons/favicon.ico',
  '/static/images/favicons/android-chrome-512x512.png',
  '/static/images/favicons/apple-touch-icon.png',
  '/static/images/favicons/favicon-32x32.png',
  '/static/images/screenshots/search.png',
  '/static/images/screenshots/collections.png',
  '/static/images/screenshots/collection.png',
  '/static/images/screenshots/menu.png',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
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

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
