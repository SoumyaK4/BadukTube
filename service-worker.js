
const CACHE_NAME = 'baduk-lectures-v3';
const CACHE_UPDATE_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

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

// Dynamic content endpoints that should be checked for updates
const DYNAMIC_ENDPOINTS = [
  '/',
  '/search',
  '/api/search',
  '/collections',
  '/paid-collections'
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

// Helper function to check if cache needs updating
function shouldUpdateCache(url) {
  const lastUpdate = localStorage.getItem(`cache-update-${url}`);
  if (!lastUpdate) return true;
  
  const timeSinceUpdate = Date.now() - parseInt(lastUpdate);
  return timeSinceUpdate > CACHE_UPDATE_INTERVAL;
}

// Helper function to mark cache as updated
function markCacheUpdated(url) {
  localStorage.setItem(`cache-update-${url}`, Date.now().toString());
}

// Helper function to check if URL is dynamic content
function isDynamicContent(url) {
  const pathname = new URL(url).pathname;
  return DYNAMIC_ENDPOINTS.some(endpoint => 
    pathname === endpoint || pathname.startsWith(endpoint + '/')
  );
}

// Function to update cache for dynamic content
async function updateDynamicCache(request, cache) {
  try {
    const response = await fetch(request.clone());
    if (response && response.status === 200) {
      await cache.put(request, response.clone());
      markCacheUpdated(request.url);
      return response;
    }
  } catch (error) {
    console.log('Cache update failed for:', request.url);
  }
  return null;
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

// Fetch event with smart cache update strategy
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cachedResponse = await cache.match(event.request);
      
      // For dynamic content, check if we need to update the cache
      if (isDynamicContent(event.request.url) && shouldUpdateCache(event.request.url)) {
        // Try to update cache in background, but return cached response immediately if available
        if (cachedResponse) {
          // Return cached response immediately
          updateDynamicCache(event.request, cache).catch(console.error);
          return cachedResponse;
        } else {
          // No cached response, fetch fresh content
          try {
            const freshResponse = await fetch(event.request.clone());
            if (freshResponse && freshResponse.status === 200) {
              await cache.put(event.request, freshResponse.clone());
              markCacheUpdated(event.request.url);
              return freshResponse;
            }
          } catch (error) {
            console.log('Failed to fetch fresh content:', error);
          }
        }
      }
      
      // Return cached response if available
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // No cached response, fetch from network
      try {
        const fetchRequest = event.request.clone();
        const response = await fetch(fetchRequest);
        
        // Check if valid response
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        
        // Clone the response because it's a one-time use stream
        const responseToCache = response.clone();
        
        // Only cache same-origin requests to avoid CORS issues
        if (event.request.url.startsWith(self.location.origin)) {
          await cache.put(event.request, responseToCache);
          if (isDynamicContent(event.request.url)) {
            markCacheUpdated(event.request.url);
          }
        }
        
        return response;
      } catch (error) {
        // Return a fallback or just re-throw the error
        // If it's a navigation request, could return a cached fallback page
        if (event.request.mode === 'navigate') {
          const fallback = await cache.match('/');
          if (fallback) return fallback;
        }
        
        throw new Error('Network request failed and no cached fallback available');
      }
    })
  );
});

// Background sync for periodic cache updates
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(performBackgroundSync());
  }
});

// Periodic background sync function
async function performBackgroundSync() {
  try {
    const cache = await caches.open(CACHE_NAME);
    
    // Check and update dynamic content that might have changed
    for (const endpoint of DYNAMIC_ENDPOINTS) {
      const url = self.location.origin + endpoint;
      if (shouldUpdateCache(url)) {
        try {
          const response = await fetch(url);
          if (response && response.status === 200) {
            await cache.put(url, response.clone());
            markCacheUpdated(url);
            console.log('Background sync updated:', endpoint);
          }
        } catch (error) {
          console.log('Background sync failed for:', endpoint, error);
        }
      }
    }
  } catch (error) {
    console.log('Background sync error:', error);
  }
}

// Schedule periodic cache checks when service worker starts
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SCHEDULE_SYNC') {
    // Schedule background sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      navigator.serviceWorker.ready.then((registration) => {
        return registration.sync.register('background-sync');
      }).catch(console.error);
    }
  }
});

