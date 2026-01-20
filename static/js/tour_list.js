/**
 * Tour List Page Interactions
 * Handles: Search, Filtering, Sorting
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initSearch();
    initFilters();
    initSort();
    initRangeSlider();
    updateToursCount();
});

// ==================== SEARCH FUNCTIONALITY ====================

function initSearch() {
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        // Show/hide clear button
        if (this.value.length > 0) {
            searchClear.classList.remove('hidden');
        } else {
            searchClear.classList.add('hidden');
        }
        
        // Filter tours
        filterTours();
    });
    
    searchClear.addEventListener('click', function() {
        searchInput.value = '';
        this.classList.add('hidden');
        filterTours();
        searchInput.focus();
    });
}

// ==================== FILTER FUNCTIONALITY ====================

function initFilters() {
    const filterType = document.getElementById('filter-type');
    const filterDifficulty = document.getElementById('filter-difficulty');
    const filterReset = document.getElementById('filter-reset');
    
    if (filterType) {
        filterType.addEventListener('change', filterTours);
    }
    
    if (filterDifficulty) {
        filterDifficulty.addEventListener('change', filterTours);
    }
    
    if (filterReset) {
        filterReset.addEventListener('click', resetFilters);
    }
}

function resetFilters() {
    // Reset all filter inputs
    document.getElementById('search-input').value = '';
    document.getElementById('filter-type').value = '';
    document.getElementById('filter-difficulty').value = '';
    document.getElementById('filter-price').value = '10000';
    document.getElementById('price-value').textContent = '10000';
    document.getElementById('search-clear').classList.add('hidden');
    
    // Reset sort
    document.getElementById('sort-by').value = 'newest';
    
    // Filter and sort
    filterTours();
}

// ==================== PRICE RANGE SLIDER ====================

function initRangeSlider() {
    const priceRange = document.getElementById('filter-price');
    const priceValue = document.getElementById('price-value');
    
    if (!priceRange) return;
    
    priceRange.addEventListener('input', function() {
        priceValue.textContent = new Intl.NumberFormat('en-US').format(this.value);
        filterTours();
    });
}

// ==================== SORT FUNCTIONALITY ====================

function initSort() {
    const sortBy = document.getElementById('sort-by');
    
    if (sortBy) {
        sortBy.addEventListener('change', function() {
            sortTours(this.value);
        });
    }
}

function sortTours(sortType) {
    const tourGrid = document.getElementById('tour-grid');
    const tours = Array.from(tourGrid.querySelectorAll('.tour-card'));
    
    switch(sortType) {
        case 'price-asc':
            tours.sort((a, b) => {
                const priceA = parseInt(a.querySelector('.price-amount').textContent);
                const priceB = parseInt(b.querySelector('.price-amount').textContent);
                return priceA - priceB;
            });
            break;
        case 'price-desc':
            tours.sort((a, b) => {
                const priceA = parseInt(a.querySelector('.price-amount').textContent);
                const priceB = parseInt(b.querySelector('.price-amount').textContent);
                return priceB - priceA;
            });
            break;
        case 'oldest':
            tours.sort((a, b) => {
                const dateA = new Date(a.getAttribute('data-date'));
                const dateB = new Date(b.getAttribute('data-date'));
                return dateA - dateB;
            });
            break;
        case 'rating':
            tours.sort((a, b) => {
                const ratingA = parseFloat(a.getAttribute('data-rating') || 0);
                const ratingB = parseFloat(b.getAttribute('data-rating') || 0);
                return ratingB - ratingA;
            });
            break;
        case 'newest':
        default:
            tours.sort((a, b) => {
                const dateA = new Date(b.getAttribute('data-date'));
                const dateB = new Date(a.getAttribute('data-date'));
                return dateA - dateB;
            });
    }
    
    // Re-append sorted tours to grid
    tours.forEach(tour => tourGrid.appendChild(tour));
}

// ==================== MAIN FILTER FUNCTION ====================

function filterTours() {
    const searchValue = document.getElementById('search-input').value.toLowerCase();
    const typeValue = document.getElementById('filter-type').value;
    const difficultyValue = document.getElementById('filter-difficulty').value;
    const priceValue = parseInt(document.getElementById('filter-price').value);
    
    const tourCards = document.querySelectorAll('.tour-card');
    let visibleCount = 0;
    
    tourCards.forEach(card => {
        let show = true;
        
        // Search filter
        if (searchValue) {
            const title = card.querySelector('.tour-title').textContent.toLowerCase();
            const guide = card.querySelector('.tour-guide').textContent.toLowerCase();
            const location = card.textContent.toLowerCase();
            
            if (!title.includes(searchValue) && 
                !guide.includes(searchValue) && 
                !location.includes(searchValue)) {
                show = false;
            }
        }
        
        // Type filter
        if (show && typeValue) {
            const tourType = card.querySelector('.meta-item:nth-child(2)')?.textContent.toLowerCase() || '';
            if (!tourType.includes(typeValue)) {
                show = false;
            }
        }
        
        // Difficulty filter
        if (show && difficultyValue) {
            const difficultyBadge = card.querySelector('.difficulty-badge');
            if (difficultyBadge) {
                const difficulty = difficultyBadge.textContent.toLowerCase();
                if (!difficulty.includes(difficultyValue)) {
                    show = false;
                }
            }
        }
        
        // Price filter
        if (show) {
            const priceText = card.querySelector('.price-amount').textContent;
            const price = parseInt(priceText.replace(/\D/g, ''));
            if (price > priceValue) {
                show = false;
            }
        }
        
        // Show or hide card
        if (show) {
            card.style.display = '';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show/hide no results message
    showNoResults(visibleCount === 0);
    
    // Update count
    updateToursCount();
}

// ==================== UPDATE TOURS COUNT ====================

function updateToursCount() {
    const tourCards = document.querySelectorAll('.tour-card');
    let visibleCount = 0;
    
    tourCards.forEach(card => {
        if (card.style.display !== 'none') {
            visibleCount++;
        }
    });
    
    const countText = document.getElementById('tours-count-text');
    if (countText) {
        countText.innerHTML = `Shfaqja e <strong>${visibleCount}</strong> turash`;
    }
}

// ==================== NO RESULTS MESSAGE ====================

function showNoResults(show) {
    const noResults = document.getElementById('no-results');
    const resetBtn = document.getElementById('reset-all-btn');
    
    if (noResults) {
        if (show) {
            noResults.classList.remove('hidden');
        } else {
            noResults.classList.add('hidden');
        }
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            resetFilters();
        });
    }
}

// ==================== KEYBOARD SHORTCUTS ====================

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search-input').focus();
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('search-input');
        if (searchInput.value) {
            searchInput.value = '';
            document.getElementById('search-clear').classList.add('hidden');
            filterTours();
        }
    }
});

// ==================== RIPPLE EFFECT ON TOUR CARDS ====================

document.querySelectorAll('.tour-card-link').forEach(link => {
    link.addEventListener('click', function(e) {
        // Only add ripple if not clicking the action button
        if (!e.target.closest('.tour-action')) {
            addRippleEffect(e);
        }
    });
});

function addRippleEffect(e) {
    const button = e.currentTarget;
    const ripple = document.createElement('span');
    
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    button.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
}

// ==================== UTILITY: ADD RIPPLE STYLES ====================

const style = document.createElement('style');
style.textContent = `
    .tour-card-link {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(14, 165, 233, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);