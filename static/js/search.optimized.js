// Optimized Search functionality
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
    let isSearching = false; // Flag to prevent concurrent searches
    window.results = []; // Global results array for duration badges
    
    // Cache DOM elements that won't change
    const pageCache = {
        loadingIndicator: '<div class="col-12 text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>',
        noResultsMessage: '<div class="col-12 text-center">No results found</div>',
        errorMessage: '<div class="col-12 text-center">Error loading results</div>',
        loadingButtonHtml: '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...',
        loadMoreButtonHtml: 'Load More'
    };

    // Function to format duration from seconds to MM:SS with memoization
    const durationCache = new Map(); // Cache for formatted durations
    function formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return "0:00";
        
        // Return from cache if available
        const cacheKey = parseInt(seconds);
        if (durationCache.has(cacheKey)) {
            return durationCache.get(cacheKey);
        }
        
        // Format and cache the result
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        const formatted = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        durationCache.set(cacheKey, formatted);
        
        return formatted;
    }

    // Create lecture card more efficiently
    function createLectureCard(lecture) {
        // Use template strings for better performance than DOM manipulation
        const card = document.createElement('div');
        card.className = 'col-md-4 mb-4';
        
        // Build HTML in a single string operation
        let html = `
            <div class="card lecture-card h-100" data-video-id="${lecture.youtube_id}" ${lecture.duration_seconds ? `data-duration="${lecture.duration_seconds}"` : ''}>
                <div class="lecture-thumbnail">
                    <img src="${lecture.thumbnail_url}" class="card-img-top" alt="${lecture.title}" loading="lazy">
                    ${lecture.duration_seconds ? `<span class="duration-badge">${formatDuration(lecture.duration_seconds)}</span>` : ''}
                    <div class="play-button"><i class="fas fa-play-circle"></i></div>
                </div>
                <div class="card-body">
                    <h5 class="card-title">${lecture.title}</h5>
                    <div class="row mt-2">`;
        
        // Add topics
        if (lecture.topics && lecture.topics.length > 0) {
            html += `
                <div class="col-12 mb-2">
                    <span class="badge bg-primary me-1">${lecture.topics[0]}</span>
                </div>`;
        }
        
        // Add tags
        if (lecture.tags && lecture.tags.length > 0) {
            html += `<div class="col-12 mb-2">`;
            lecture.tags.forEach(tag => {
                html += `<span class="badge bg-secondary me-1">${tag}</span>`;
            });
            html += `</div>`;
        }
        
        // Add rank
        if (lecture.rank) {
            html += `
                <div class="col-12 mb-2">
                    <span class="badge bg-info me-1">${lecture.rank}</span>
                </div>`;
        }
        
        html += `
                    </div>
                </div>
            </div>`;
        
        card.innerHTML = html;
        
        // Add click event with event delegation
        const lectureCard = card.querySelector('.lecture-card');
        if (lectureCard) {
            lectureCard.addEventListener('click', function() {
                openVideoModal(lecture.youtube_id, lecture.title);
            });
        }
        
        return card;
    }

    // Optimized search function with request cancellation
    let currentRequest = null;
    function performSearch(page = 1, resetResults = true) {
        // Prevent concurrent searches
        if (isSearching) return;
        isSearching = true;
        
        // Show loading indicator
        if (resetResults) {
            resultsContainer.innerHTML = pageCache.loadingIndicator;
        } else {
            loadMoreButton.innerHTML = pageCache.loadingButtonHtml;
        }

        // Build search parameters
        const params = new URLSearchParams();
        params.append('page', page);
        params.append('per_page', perPage);

        // Add search query if present
        const searchQuery = searchInput.value.trim();
        if (searchQuery) {
            params.append('q', searchQuery);
        }

        // Add filters if selected
        if (topicFilter.value) {
            params.append('topics[]', topicFilter.value);
        }
        if (tagFilter.value) {
            params.append('tags[]', tagFilter.value);
        }
        if (rankFilter.value) {
            params.append('rank', rankFilter.value);
        }

        // Save current search params
        currentSearchParams = {
            q: searchQuery,
            topics: topicFilter.value ? [topicFilter.value] : [],
            tags: tagFilter.value ? [tagFilter.value] : [],
            rank: rankFilter.value
        };

        // Cancel previous request if still pending
        if (currentRequest && currentRequest.abort) {
            currentRequest.abort();
        }

        // Use AbortController if supported
        let signal = null;
        let controller = null;
        if (window.AbortController) {
            controller = new AbortController();
            signal = controller.signal;
            currentRequest = controller;
        }

        // Fetch results with ability to cancel if supported
        const fetchOptions = signal ? { signal } : {};
        
        fetch(`/api/search?${params.toString()}`, fetchOptions)
        .then(response => response.json())
        .then(data => {
            // Store results globally for duration badges
            window.results = data.lectures || [];
            
            // Clear results if this is a new search
            if (resetResults) {
                resultsContainer.innerHTML = '';
            }

            // Display results
            if (data.lectures && data.lectures.length > 0) {
                // Use document fragment for better performance
                const fragment = document.createDocumentFragment();
                data.lectures.forEach(lecture => {
                    fragment.appendChild(createLectureCard(lecture));
                });
                resultsContainer.appendChild(fragment);

                // Update pagination
                hasMore = data.has_next;
                currentPage = data.current_page;

                // Show/hide load more button
                loadMoreButton.style.display = hasMore ? 'inline-block' : 'none';
            } else {
                if (resetResults) {
                    resultsContainer.innerHTML = pageCache.noResultsMessage;
                }
                loadMoreButton.style.display = 'none';
            }

            // Reset load more button if needed
            if (!resetResults) {
                loadMoreButton.innerHTML = pageCache.loadMoreButtonHtml;
            }
            
            // Reset searching flag
            isSearching = false;
            currentRequest = null;
        })
        .catch(error => {
            // Only show error for non-aborted requests
            if (!error.name || error.name !== 'AbortError') {
                console.error('Error fetching search results:', error);
                resultsContainer.innerHTML = pageCache.errorMessage;
                loadMoreButton.style.display = 'none';
            }
            
            // Reset searching flag
            isSearching = false;
            currentRequest = null;
        });
    }

    // Efficient debounce function
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

    // Event listeners with optimized debounce
    const debouncedSearch = debounce(function() {
        currentPage = 1;
        performSearch(1);
    }, 300);

    searchInput.addEventListener('input', debouncedSearch);
    topicFilter.addEventListener('change', debouncedSearch);
    tagFilter.addEventListener('change', debouncedSearch);
    rankFilter.addEventListener('change', debouncedSearch);

    loadMoreButton.addEventListener('click', function() {
        performSearch(currentPage + 1, false);
    });

    // Initial search on page load
    performSearch();
});

// Video modal functionality
function openVideoModal(videoId, title) {
    if (typeof window.openYouTubeModal === 'function') {
        window.openYouTubeModal(videoId, title);
    } else {
        console.error("YouTube modal player not available");
        alert("Unable to play video. Please try again later.");
    }
}

// Global utility function for formatting durations
function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return "0:00";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}
