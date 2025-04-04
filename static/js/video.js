/**
 * Simple YouTube video player in a modal
 * This implementation provides a basic video experience with clean modal handling
 */
document.addEventListener('DOMContentLoaded', function() {
    // Global state - minimal to avoid conflicts
    let youtubePlayer = null;
    let activeModal = null;
    let escapeListener = null;
    
    // Load YouTube API - only if it's not already loaded
    if (!window.YT) {
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }

    // Main function to open a YouTube video in a modal - simplified
    window.openYouTubeModal = function(videoId, title) {
        // If there's already an active modal, close it first
        if (activeModal) {
            cleanupModal();
        }
        
        // Create modal element
        const modal = document.createElement('div');
        modal.className = 'video-modal';
        modal.id = 'youtube-video-modal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('role', 'dialog');
        modal.innerHTML = `
            <div class="video-container">
                <div id="youtube-player-container"></div>
                <button class="close-video" aria-label="Close video">&times;</button>
                ${title ? `<div class="video-title">${title}</div>` : ''}
            </div>
        `;

        // Add to DOM and display
        document.body.appendChild(modal);
        // Do NOT add modal-open class, it's causing issues
        modal.style.display = 'flex';
        activeModal = modal;

        // Create YouTube player
        if (window.YT && window.YT.Player) {
            createYouTubePlayer();
        } else {
            // If YT API is not loaded yet, wait for it
            window.onYouTubeIframeAPIReady = createYouTubePlayer;
        }

        function createYouTubePlayer() {
            // Clean up any existing player
            if (youtubePlayer) {
                try {
                    youtubePlayer.pauseVideo && youtubePlayer.pauseVideo();
                    youtubePlayer.destroy && youtubePlayer.destroy();
                } catch (e) {
                    console.error("Error destroying YouTube player:", e);
                }
                youtubePlayer = null;
            }
            
            // Create a new player
            try {
                youtubePlayer = new YT.Player('youtube-player-container', {
                    height: '100%',
                    width: '100%',
                    videoId: videoId,
                    playerVars: {
                        autoplay: 1,
                        modestbranding: 1,
                        rel: 0,
                        showinfo: 0,
                        fs: 1,
                        playsinline: 1,
                        enablejsapi: 1,
                        origin: window.location.origin
                    },
                    events: {
                        onReady: function(event) {
                            // Player is ready, play video
                            event.target.playVideo();
                        },
                        onStateChange: function(event) {
                            // If the video ended, close the modal
                            if (event.data === YT.PlayerState.ENDED) {
                                closeVideoModal();
                            }
                        },
                        onError: function(event) {
                            console.error("YouTube player error:", event.data);
                            // Display error message in the modal
                            const container = document.getElementById('youtube-player-container');
                            if (container) {
                                container.innerHTML = `
                                    <div class="video-error">
                                        <p>Error loading video. Please try again later.</p>
                                        <p>Error code: ${event.data}</p>
                                    </div>
                                `;
                            }
                        }
                    }
                });
            } catch (e) {
                console.error("Error creating YouTube player:", e);
                // Display friendly error message
                const container = document.getElementById('youtube-player-container');
                if (container) {
                    container.innerHTML = `
                        <div class="video-error">
                            <p>Error loading video player. Please try again later.</p>
                        </div>
                    `;
                }
            }
        }

        // Close button handler
        const closeBtn = modal.querySelector('.close-video');
        closeBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeVideoModal();
        };

        // Close on background click
        modal.onclick = function(e) {
            if (e.target === modal) {
                closeVideoModal();
            }
        };

        // Remove any existing escape key listener
        if (escapeListener) {
            document.removeEventListener('keydown', escapeListener);
        }

        // Close on escape key - with a properly scoped listener
        escapeListener = function(e) {
            if (e.key === 'Escape') {
                closeVideoModal();
            }
        };
        document.addEventListener('keydown', escapeListener);
    };

    // Make a global function for closing the modal
    window.closeYouTubeModal = closeVideoModal;

    // Primary function to close the video modal
    function closeVideoModal() {
        cleanupModal();
    }
    
    // Simple cleanup function that completely destroys everything
    function cleanupModal() {
        if (!activeModal) return;
        
        // Add fade-out animation
        activeModal.classList.add('fade-out');
        
        // Clean up YouTube player immediately to stop sound
        if (youtubePlayer) {
            try {
                // Pause the video first to immediately stop sound
                if (youtubePlayer.pauseVideo) {
                    youtubePlayer.pauseVideo();
                }
                
                // Set volume to 0 for immediate silence
                if (youtubePlayer.setVolume) {
                    youtubePlayer.setVolume(0);
                }
                
                // Then destroy the player
                if (youtubePlayer.destroy) {
                    youtubePlayer.destroy();
                }
            } catch (e) {
                console.error("Error stopping YouTube player:", e);
            } finally {
                // Always nullify the player reference
                youtubePlayer = null;
                
                // Force cleanup YouTube iframe
                const container = document.getElementById('youtube-player-container');
                if (container) {
                    container.innerHTML = '';
                }
            }
        }
        
        // Remove the modal immediately without delay
        // First reset any body styles
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
            
        // Remove any modal-open class if it exists
        if (document.body.classList.contains('modal-open')) {
            document.body.classList.remove('modal-open');
        }
        
        // Remove the modal element immediately
        if (activeModal && activeModal.parentNode) {
            activeModal.parentNode.removeChild(activeModal);
        }
        activeModal = null;
        
        // Remove escape key listener
        if (escapeListener) {
            document.removeEventListener('keydown', escapeListener);
            escapeListener = null;
        }
        
        // Remove any lingering modal backdrop elements
        const modalBackdrops = document.querySelectorAll('.modal-backdrop');
        modalBackdrops.forEach(backdrop => {
            if (backdrop.parentNode) {
                backdrop.parentNode.removeChild(backdrop);
            }
        });
    }

    // For backward compatibility
    window.openVideoModal = window.openYouTubeModal;
    
    // Listen for page unload to clean up any players
    window.addEventListener('beforeunload', function() {
        if (youtubePlayer) {
            try {
                youtubePlayer.destroy();
            } catch (e) {
                console.error("Error destroying YouTube player on page unload:", e);
            }
            youtubePlayer = null;
        }
    });
});