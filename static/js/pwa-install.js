
// Variables to store popup state
let deferredPrompt;
const POPUP_DISMISSED_KEY = 'pwaPromptDismissed';
const POPUP_DELAY = 60000; // 1 minute in milliseconds

// Check if the device is mobile
function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Check if the app is already installed
function isPWAInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches || 
         window.matchMedia('(display-mode: fullscreen)').matches;
}

// Check if user has dismissed the popup before
function hasUserDismissedPopup() {
  const dismissedTimestamp = localStorage.getItem(POPUP_DISMISSED_KEY);
  if (!dismissedTimestamp) return false;
  
  const dismissedDate = new Date(dismissedTimestamp);
  return !isNaN(dismissedDate.getTime()); // Return true if it's a valid date
}

// Create and display the popup
function createAndShowPopup() {
  // Only show for mobile devices, if the PWA is not already installed, and if the user hasn't dismissed it
  if (!isMobile() || isPWAInstalled() || !deferredPrompt) return;
  
  // Create popup element if it doesn't exist
  let popup = document.querySelector('.pwa-install-popup');
  if (!popup) {
    popup = document.createElement('div');
    popup.className = 'pwa-install-popup';
    popup.innerHTML = `
      <div class="pwa-install-content">
        <p>Install our app for a better experience!</p>
        <div class="pwa-install-buttons">
          <button class="pwa-install-btn">Install</button>
          <button class="pwa-close-btn">Close</button>
        </div>
      </div>
    `;
    document.body.appendChild(popup);
    
    // Add event listeners to buttons
    popup.querySelector('.pwa-install-btn').addEventListener('click', handleInstallClick);
    popup.querySelector('.pwa-close-btn').addEventListener('click', handleCloseClick);
  }
  
  // Show the popup with animation
  popup.style.display = 'block';
}

// Handle install button click
function handleInstallClick() {
  const popup = document.querySelector('.pwa-install-popup');
  
  if (deferredPrompt) {
    // Show the installation prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the PWA installation');
      } else {
        console.log('User dismissed the PWA installation');
      }
      
      // Clear the saved prompt
      deferredPrompt = null;
      
      // Hide the popup
      if (popup) popup.style.display = 'none';
    });
  }
}

// Handle close button click
function handleCloseClick() {
  const popup = document.querySelector('.pwa-install-popup');
  
  // Hide the popup
  if (popup) popup.style.display = 'none';
  
  // Save dismissal to localStorage with current timestamp
  localStorage.setItem(POPUP_DISMISSED_KEY, new Date().toISOString());
}

// Initialize the PWA installation flow
document.addEventListener('DOMContentLoaded', () => {
  // Wait for the beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    // Store the event without preventing default
    deferredPrompt = e;
    
    // If the user hasn't dismissed the popup, show it after the delay
    if (!hasUserDismissedPopup()) {
      setTimeout(createAndShowPopup, POPUP_DELAY);
    }
  });
  
  // Also detect standalone mode changes (useful for when the app gets installed)
  window.matchMedia('(display-mode: standalone)').addEventListener('change', (e) => {
    if (e.matches) {
      // The app was installed
      const popup = document.querySelector('.pwa-install-popup');
      if (popup) popup.style.display = 'none';
    }
  });
  
  // Reset dismissal on page load if the PWA is not installed
  // This allows the popup to show again on subsequent visits
  if (!isPWAInstalled() && hasUserDismissedPopup()) {
    // Clear the dismissal timestamp and set the timeout again
    setTimeout(createAndShowPopup, POPUP_DELAY);
  }
});
