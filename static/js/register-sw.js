
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then((registration) => {
        // Registration was successful
        console.log('ServiceWorker registered successfully');
        
        // Schedule background sync for cache updates
        navigator.serviceWorker.ready.then((sw) => {
          sw.active.postMessage({type: 'SCHEDULE_SYNC'});
        });
        
        // Set up periodic sync registration if supported
        if ('sync' in window.ServiceWorkerRegistration.prototype) {
          registration.sync.register('background-sync').catch(console.error);
        }
        
        // Set up periodic background sync (every 24 hours)
        setInterval(() => {
          if (registration.active) {
            registration.active.postMessage({type: 'SCHEDULE_SYNC'});
          }
        }, 24 * 60 * 60 * 1000); // 24 hours
      })
      .catch((err) => {
        // Keep error logging for critical failures
        console.error('ServiceWorker registration failed:', err);
      });
  });
}

