
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then((registration) => {
        // Registration was successful
      })
      .catch((err) => {
        // Keep error logging for critical failures
        console.error('ServiceWorker registration failed:', err);
      });
  });
}
