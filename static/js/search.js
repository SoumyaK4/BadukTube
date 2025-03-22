// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const topicFilter = document.getElementById('topic-filter');
    const tagFilter = document.getElementById('tag-filter');
    const rankFilter = document.getElementById('rank-filter');
    const resultsContainer = document.getElementById('results-container');
    const loadMoreButton = document.getElementById('load-more');

    let currentPage = 1;
    const perPage = 9;
    let hasMore = false;
    let currentSearchParams = {};

    // Function to format duration from seconds to MM:SS
    function formatDuration(seconds) {
        if (!seconds) return "0:00";
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    // Function to create a lecture card
    function createLectureCard(lecture) {
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-4';

        const card = document.createElement('div');
        card.className = 'card lecture-card h-100';
        card.setAttribute('data-video-id', lecture.youtube_id);

        // Create thumbnail with duration badge
        const thumbnailDiv = document.createElement('div');
        thumbnailDiv.className = 'lecture-thumbnail';

        const img = document.createElement('img');
        img.src = lecture.thumbnail_url;
        img.className = 'card-img-top';
        img.alt = lecture.title;

        // Add duration badge if available
        if (lecture.duration_seconds) {
            const durationBadge = document.createElement('span');
            durationBadge.className = 'duration-badge';
            durationBadge.textContent = formatDuration(lecture.duration_seconds);
            thumbnailDiv.appendChild(durationBadge);
        }

        thumbnailDiv.appendChild(img);
        card.appendChild(thumbnailDiv);

        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';

        const title = document.createElement('h5');
        title.className = 'card-title';
        title.textContent = lecture.title;

        // Metadata row
        const metadataRow = document.createElement('div');
        metadataRow.className = 'row mt-2';

        // Topics
        if (lecture.topics && lecture.topics.length > 0) {
            const topicCol = document.createElement('div');
            topicCol.className = 'col-12 mb-2';

            const topicBadge = document.createElement('span');
            topicBadge.className = 'badge bg-primary me-1';
            topicBadge.textContent = lecture.topics[0];
            topicCol.appendChild(topicBadge);

            metadataRow.appendChild(topicCol);
        }

        // Tags
        if (lecture.tags && lecture.tags.length > 0) {
            const tagCol = document.createElement('div');
            tagCol.className = 'col-12 mb-2';

            lecture.tags.forEach(tag => {
                const tagBadge = document.createElement('span');
                tagBadge.className = 'badge bg-secondary me-1';
                tagBadge.textContent = tag;
                tagCol.appendChild(tagBadge);
            });

            metadataRow.appendChild(tagCol);
        }

        // Rank
        if (lecture.rank) {
            const rankCol = document.createElement('div');
            rankCol.className = 'col-12 mb-2';

            const rankBadge = document.createElement('span');
            rankBadge.className = 'badge bg-info me-1';
            rankBadge.textContent = lecture.rank;
            rankCol.appendChild(rankBadge);

            metadataRow.appendChild(rankCol);
        }

        cardBody.appendChild(title);
        cardBody.appendChild(metadataRow);
        card.appendChild(cardBody);

        // Add click event to open video
        card.addEventListener('click', function() {
            openVideoModal(lecture.youtube_id, lecture.title);
        });

        col.appendChild(card);
        return col;
    }

    // Function to perform search
    function performSearch(page = 1, resetResults = true) {
        // Show loading indicator
        if (resetResults) {
            resultsContainer.innerHTML = '<div class="col-12 text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        } else {
            loadMoreButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
        }

        // Build search parameters
        const params = new URLSearchParams();
        params.append('page', page);
        params.append('per_page', perPage);

        // Add search query if present
        if (searchInput.value.trim()) {
            params.append('q', searchInput.value.trim());
        }

        // Add topic filter if selected
        if (topicFilter.value) {
            params.append('topics[]', topicFilter.value);
        }

        // Add tag filter if selected
        if (tagFilter.value) {
            params.append('tags[]', tagFilter.value);
        }

        // Add rank filter if selected
        if (rankFilter.value) {
            params.append('rank', rankFilter.value);
        }

        // Save current search params
        currentSearchParams = {
            q: searchInput.value.trim(),
            topics: topicFilter.value ? [topicFilter.value] : [],
            tags: tagFilter.value ? [tagFilter.value] : [],
            rank: rankFilter.value
        };

        // Fetch results
        fetch(`/api/search?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                results = data.lectures; //Update the global results array
                // Clear results if this is a new search
                if (resetResults) {
                    resultsContainer.innerHTML = '';
                }

                // Display results
                if (data.lectures && data.lectures.length > 0) {
                    data.lectures.forEach(lecture => {
                        const card = createLectureCard(lecture);
                        resultsContainer.appendChild(card);
                    });

                    // Update pagination
                    hasMore = data.has_next;
                    currentPage = data.current_page;

                    // Show/hide load more button
                    loadMoreButton.style.display = hasMore ? 'block' : 'none';
                } else {
                    if (resetResults) {
                        resultsContainer.innerHTML = '<div class="col-12 text-center">No results found</div>';
                    }
                    loadMoreButton.style.display = 'none';
                }

                // Reset load more button if needed
                if (!resetResults) {
                    loadMoreButton.innerHTML = 'Load More';
                }
            })
            .catch(error => {
                console.error('Error fetching search results:', error);
                resultsContainer.innerHTML = '<div class="col-12 text-center">Error loading results</div>';
                loadMoreButton.style.display = 'none';
            });
    }

    // Event listeners
    searchInput.addEventListener('input', debounce(function() {
        currentPage = 1;
        performSearch(1);
    }, 300));

    topicFilter.addEventListener('change', function() {
        currentPage = 1;
        performSearch(1);
    });

    tagFilter.addEventListener('change', function() {
        currentPage = 1;
        performSearch(1);
    });

    rankFilter.addEventListener('change', function() {
        currentPage = 1;
        performSearch(1);
    });

    loadMoreButton.addEventListener('click', function() {
        performSearch(currentPage + 1, false);
    });

    // Debounce function to prevent too many requests
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this, args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                func.apply(context, args);
            }, wait);
        };
    }

    // Initial search on page load
    performSearch();
    
    // Call the additional setup function to avoid duplicate event listeners
    setupAdditionalFeatures();
});

// Video modal functionality
function openVideoModal(videoId, title) {
    const modal = new bootstrap.Modal(document.getElementById('videoModal'));
    const modalTitle = document.getElementById('videoModalLabel');
    const playerContainer = document.getElementById('player-container');

    // Set modal title
    modalTitle.textContent = title;

    // Create YouTube iframe
    playerContainer.innerHTML = `<iframe width="100%" height="400" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;

    // Show modal
    modal.show();

    // Clean up when modal is hidden
    document.getElementById('videoModal').addEventListener('hidden.bs.modal', function() {
        playerContainer.innerHTML = '';
    });
}

// Format duration from seconds to MM:SS
function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return "0:00";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Create lecture card with proper duration badge
function createLectureCard(lecture) {
    const card = document.createElement('div');
    card.className = 'col-md-4 col-sm-6 mb-4';
    
    // Create the HTML structure
    card.innerHTML = `
        <div class="lecture-card" data-video-id="${lecture.youtube_id}" data-duration="${lecture.duration_seconds || 0}">
            <div class="lecture-thumbnail">
                <img src="${lecture.thumbnail_url}" alt="${lecture.title}" loading="lazy">
                ${lecture.duration_seconds ? `<span class="duration-badge">${formatDuration(lecture.duration_seconds)}</span>` : ''}
                <div class="play-button"><i class="fas fa-play-circle"></i></div>
            </div>
            <div class="lecture-content">
                <h3>${lecture.title}</h3>
                <div class="lecture-meta">
                    ${lecture.topic ? `<span class="topic-tag">${lecture.topic}</span>` : ''}
                    ${lecture.rank ? `<span class="rank-tag">${lecture.rank}</span>` : ''}
                </div>
            </div>
        </div>
    `;
    
    // Add click handler
    card.querySelector('.lecture-card').addEventListener('click', function() {
        openVideoModal(lecture.youtube_id, lecture.title);
    });
    
    // Ensure the duration badge exists and is properly positioned
    const lectureCard = card.querySelector('.lecture-card');
    if (lecture.duration_seconds && lectureCard) {
        // Store duration in a data attribute for persistence
        lectureCard.setAttribute('data-duration', lecture.duration_seconds);
    }
    
    return card;
}

// Function to ensure duration badges are added
function ensureDurationBadges() {
    const cards = document.querySelectorAll('.lecture-card');
    cards.forEach(card => {
        const thumbnail = card.querySelector('.lecture-thumbnail');
        const videoId = card.dataset.videoId;
        
        // Remove all existing badges to prevent duplicates
        const existingBadges = thumbnail ? thumbnail.querySelectorAll('.duration-badge') : [];
        existingBadges.forEach(badge => badge.remove());
        
        // Add a new badge if we have duration data
        if (thumbnail && videoId) {
            // Try to get duration from the card's dataset
            let duration = card.dataset.duration;
            
            if (duration && parseInt(duration) > 0) {
                const durationBadge = document.createElement('span');
                durationBadge.className = 'duration-badge';
                durationBadge.textContent = formatDuration(parseInt(duration));
                durationBadge.style.position = 'absolute';
                durationBadge.style.bottom = '8px';
                durationBadge.style.right = '8px';
                durationBadge.style.zIndex = '30'; // Increase z-index to ensure visibility
                thumbnail.appendChild(durationBadge);
            } else if (window.results && Array.isArray(window.results)) {
                // Try to find duration in results array
                const lecture = window.results.find(l => l.youtube_id === videoId);
                if (lecture && lecture.duration_seconds) {
                    const durationBadge = document.createElement('span');
                    durationBadge.className = 'duration-badge';
                    durationBadge.textContent = formatDuration(lecture.duration_seconds);
                    durationBadge.style.position = 'absolute';
                    durationBadge.style.bottom = '8px';
                    durationBadge.style.right = '8px';
                    durationBadge.style.zIndex = '30'; // Increase z-index to ensure visibility
                    thumbnail.appendChild(durationBadge);
                    
                    // Store duration in the card's dataset for future reference
                    card.dataset.duration = lecture.duration_seconds;
                }
            }
            
            // Make sure the play button is always visible too
            if (!thumbnail.querySelector('.play-button')) {
                const playButton = document.createElement('div');
                playButton.className = 'play-button';
                playButton.innerHTML = '<i class="fas fa-play-circle"></i>';
                playButton.style.zIndex = '20'; // Ensure play button is above image but below duration
                thumbnail.appendChild(playButton);
            }
        }
    });
}

// Add this function call to the first DOMContentLoaded event listener
// at the end of the first addEventListener function
function setupAdditionalFeatures() {
    // Run duration badge function immediately
    setTimeout(ensureDurationBadges, 100);
    
    // Handle window resize to ensure duration badges remain visible on mobile
    window.addEventListener('resize', ensureDurationBadges);

    // Handle page visibility changes (when user returns to the tab)
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            setTimeout(ensureDurationBadges, 200);
        }
    });
    
    // Add mutation observer to watch for dynamic content changes
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        const observer = new MutationObserver(function(mutations) {
            setTimeout(ensureDurationBadges, 100);
            
            // Run it again after a longer delay to catch any late changes
            setTimeout(ensureDurationBadges, 500);
            setTimeout(ensureDurationBadges, 1000);
        });
        
        observer.observe(resultsContainer, { 
            childList: true,
            subtree: true,
            attributes: true
        });
    }
    
    // Apply duration badges on initial load and window load event
    ensureDurationBadges();
    window.addEventListener('load', function() {
        ensureDurationBadges();
        // Run again after delays to ensure all elements are loaded
        setTimeout(ensureDurationBadges, 500);
        setTimeout(ensureDurationBadges, 1000);
        setTimeout(ensureDurationBadges, 2000);
    });
}