/**
 * Tour Detail Page Interactions
 * Handles: Star rating, Form validation, Review management
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==================== STAR RATING ====================
    initStarRating();
    
    // ==================== SMOOTH SCROLL ====================
    initSmoothScroll();
    
    // ==================== FORM VALIDATION ====================
    initFormValidation();
});

/**
 * Initialize interactive star rating
 */
function initStarRating() {
    const starRating = document.getElementById('star-rating');
    const ratingInput = document.getElementById('rating-value');
    
    if (!starRating) return;
    
    const stars = starRating.querySelectorAll('.star');
    
    stars.forEach(star => {
        // Click event
        star.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            ratingInput.value = value;
            updateStars(stars, value);
        });
        
        // Hover event
        star.addEventListener('mouseover', function() {
            const value = this.getAttribute('data-value');
            updateStars(stars, value);
        });
        
        // Mouse out event
        star.addEventListener('mouseout', function() {
            const current = ratingInput.value;
            updateStars(stars, current);
        });
    });
    
    /**
     * Update star display based on rating value
     */
    function updateStars(starsNodeList, value) {
        starsNodeList.forEach(s => {
            if (parseInt(s.getAttribute('data-value')) <= value) {
                s.classList.add('active');
            } else {
                s.classList.remove('active');
            }
        });
    }
}

/**
 * Initialize smooth scroll for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize form validation for review form
 */
function initFormValidation() {
    const reviewForm = document.getElementById('review-form');
    if (!reviewForm) return;
    
    reviewForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const ratingValue = document.getElementById('rating-value').value;
        const comment = document.getElementById('comment').value.trim();
        
        // Validate rating
        if (!ratingValue || ratingValue === '0') {
            showNotification('Ju lutemi zgjidhni një vlerësim me yje', 'error');
            return;
        }
        
        // Validate comment length
        if (comment.length < 10) {
            showNotification('Komentari duhet të ketë të paktën 10 karaktere', 'error');
            return;
        }
        
        if (comment.length > 500) {
            showNotification('Komentari nuk duhet të kalojë 500 karaktere', 'error');
            return;
        }
        
        // Submit form
        submitReview(this);
    });
}

/**
 * Submit review via AJAX
 */
function submitReview(form) {
    const submitBtn = form.querySelector('.btn-submit');
    const originalHTML = submitBtn.innerHTML;
    
    // Disable button and show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Duke dërguar...';
    
    const formData = new FormData(form);
    const url = form.getAttribute('action');
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            // Success
            showNotification('Vlerësimi u dërgua me sukses! 🎉', 'success');
            
            // Reset form
            form.reset();
            document.getElementById('rating-value').value = '0';
            document.querySelectorAll('#star-rating .star').forEach(star => {
                star.classList.remove('active');
            });
            
            // Redirect after 2 seconds
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            showNotification('Ndodhi një gabim. Ju lutemi provoni përsëri.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ndodhi një gabim në lidhje. Kontrolloni internetin tuaj.', 'error');
    })
    .finally(() => {
        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHTML;
    });
}

/**
 * Show notification message
 */
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" aria-label="Mbyll">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Add styles if not already present
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                max-width: 400px;
                padding: 16px 20px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                animation: slideInRight 0.3s ease-out;
            }
            
            .notification-success {
                background: #d1fae5;
                border: 1px solid #6ee7b7;
                color: #047857;
            }
            
            .notification-error {
                background: #fee2e2;
                border: 1px solid #fca5a5;
                color: #dc2626;
            }
            
            .notification-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .notification-close {
                background: none;
                border: none;
                cursor: pointer;
                opacity: 0.7;
                transition: opacity 0.2s;
            }
            
            .notification-close:hover {
                opacity: 1;
            }
            
            @keyframes slideInRight {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @media (max-width: 576px) {
                .notification {
                    left: 20px;
                    right: 20px;
                    max-width: none;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Close notification
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOutRight 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto close after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.style.animation = 'slideOutRight 0.3s ease-out forwards';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

/**
 * Lazy load images on scroll
 */
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    // Image is already in src, just observe
                    observer.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
}

// Initialize lazy loading
initLazyLoading();