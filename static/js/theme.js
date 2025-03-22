
/**
 * Dark Mode Theme
 * Forces dark theme application
 */
document.addEventListener('DOMContentLoaded', function() {
    // Always force dark theme
    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.classList.add('dark-mode');
    
    // Apply dark mode to body
    document.body.classList.add('dark-mode');

    // Handle video modal functionality
    const lectureCards = document.querySelectorAll('.lecture-card');
    const videoModal = document.querySelector('.video-modal');
    const closeVideo = document.querySelector('.close-video');
    
    if (lectureCards && videoModal) {
        lectureCards.forEach(card => {
            card.addEventListener('click', function() {
                videoModal.style.display = 'block';
            });
        });
        
        if (closeVideo) {
            closeVideo.addEventListener('click', function() {
                videoModal.classList.add('fade-out');
                setTimeout(() => {
                    videoModal.style.display = 'none';
                    videoModal.classList.remove('fade-out');
                }, 300);
            });
        }
    }
});
