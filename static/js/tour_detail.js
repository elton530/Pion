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
    
    // ==================== GALLERY LIGHTBOX ====================
    initGalleryLightbox();
    
    // ==================== FAQ ACCORDION ====================
    initFaqAccordion();
});

/**
 * Initialize FAQ accordion
 */
function initFaqAccordion() {
    const questions = document.querySelectorAll('.faq-question');
    if (!questions.length) return;

    questions.forEach(question => {
        question.addEventListener('click', function() {
            const item = this.closest('.faq-item');
            const answer = item.querySelector('.faq-answer');
            const isOpen = item.classList.contains('open');

            // Close all others
            document.querySelectorAll('.faq-item.open').forEach(openItem => {
                if (openItem !== item) {
                    openItem.classList.remove('open');
                    openItem.querySelector('.faq-answer').style.maxHeight = null;
                    openItem.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
                }
            });

            // Toggle current
            if (isOpen) {
                item.classList.remove('open');
                answer.style.maxHeight = null;
                this.setAttribute('aria-expanded', 'false');
            } else {
                item.classList.add('open');
                answer.style.maxHeight = answer.scrollHeight + 'px';
                this.setAttribute('aria-expanded', 'true');
            }
        });
    });
}

/**
 * Initialize interactive star rating (supports multiple widgets)
 */
function initStarRating() {
    const starRatings = document.querySelectorAll('.star-rating');
    if (!starRatings.length) return;

    starRatings.forEach((starRating) => {
        const targetId = starRating.dataset.target || 'rating-value';
        const ratingInput = document.getElementById(targetId);
        const preset = starRating.dataset.value || (ratingInput ? ratingInput.value : '0');

        const stars = Array.from(starRating.querySelectorAll('.star'));

        if (preset && ratingInput && ratingInput.value === '0') {
            ratingInput.value = preset;
        }
        if (preset) {
            updateStars(stars, preset);
        }

        stars.forEach((star, index) => {
            star.setAttribute('role', 'radio');
            star.setAttribute('aria-label', `${index + 1} yll`);
            star.tabIndex = -1;

            // Click event
            star.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                setRating(ratingInput, stars, value);
            });

            // Hover event
            star.addEventListener('mouseover', function() {
                const value = this.getAttribute('data-value');
                updateStars(stars, value);
            });

            // Mouse out event
            star.addEventListener('mouseout', function() {
                const current = ratingInput ? ratingInput.value : '0';
                updateStars(stars, current);
            });

            // Keyboard activation
            star.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setRating(ratingInput, stars, this.getAttribute('data-value'));
                } else if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    const next = stars[index + 1] || stars[stars.length - 1];
                    setRating(ratingInput, stars, next.getAttribute('data-value'));
                    next.focus();
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    const prev = stars[index - 1] || stars[0];
                    setRating(ratingInput, stars, prev.getAttribute('data-value'));
                    prev.focus();
                }
            });
        });
    });

    function setRating(input, stars, value) {
        if (input) input.value = value;
        updateStars(stars, value);
        stars.forEach(s => {
            s.tabIndex = s.getAttribute('data-value') === value ? 0 : -1;
        });
    }

    /**
     * Update star display based on rating value
     */
    function updateStars(starsNodeList, value) {
        starsNodeList.forEach(s => {
            if (parseInt(s.getAttribute('data-value')) <= parseInt(value)) {
                s.classList.add('active');
                s.setAttribute('aria-checked', 'true');
            } else {
                s.classList.remove('active');
                s.setAttribute('aria-checked', 'false');
            }
        });
    }
}

/**
 * Initialize gallery lightbox (simple, no-dependency)
 */
function initGalleryLightbox() {
    const galleryItems = document.querySelectorAll('.gallery-item');
    if (!galleryItems || galleryItems.length === 0) return;

    // Create modal element
    const modal = document.createElement('div');
    modal.className = 'tl-lightbox';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.innerHTML = `
        <div class="tl-lightbox-inner">
            <button class="tl-close" aria-label="Mbyll">×</button>
            <img class="tl-img" src="" alt="" />
            <div class="tl-caption"></div>
        </div>
    `;
    document.body.appendChild(modal);

    const tlImg = modal.querySelector('.tl-img');
    const tlCaption = modal.querySelector('.tl-caption');
    const tlClose = modal.querySelector('.tl-close');
    let lastFocused = null;

    galleryItems.forEach(item => {
        item.addEventListener('click', () => {
            const img = item.querySelector('img');
            const src = img.getAttribute('src') || img.dataset.src || '';
            const caption = item.querySelector('.gallery-caption')?.innerText || '';
            tlImg.src = src;
            tlImg.alt = img.alt || '';
            tlCaption.textContent = caption;
            lastFocused = document.activeElement;
            modal.classList.add('open');
            document.body.style.overflow = 'hidden';
            tlClose.focus();
        });
    });

    tlClose.addEventListener('click', closeLightbox);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeLightbox();
    });

    // Close on Escape and restore focus
    document.addEventListener('keydown', function onKeydown(e) {
        if (e.key === 'Escape' && modal.classList.contains('open')) {
            closeLightbox();
        }
    });

    function closeLightbox() {
        modal.classList.remove('open');
        document.body.style.overflow = '';
        tlImg.src = '';
        tlCaption.textContent = '';
        if (lastFocused && lastFocused.focus) {
            lastFocused.focus();
        }
        lastFocused = null;
    }

    // Inject minimal styles
    if (!document.getElementById('tl-lightbox-styles')) {
        const s = document.createElement('style');
        s.id = 'tl-lightbox-styles';
        s.textContent = `
            .tl-lightbox{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(2,6,23,0.6);opacity:0;pointer-events:none;transition:opacity .25s ease;z-index:9999}
            .tl-lightbox.open{opacity:1;pointer-events:auto}
            .tl-lightbox-inner{max-width:90%;max-height:90%;position:relative;background:transparent;border-radius:12px;overflow:hidden;display:flex;flex-direction:column;align-items:center}
            .tl-lightbox .tl-img{max-width:100%;max-height:80vh;display:block;border-radius:8px;box-shadow:0 20px 50px rgba(2,6,23,0.6)}
            .tl-lightbox .tl-caption{margin-top:12px;color:#e6eef8;opacity:0.95;text-align:center}
            .tl-lightbox .tl-close{position:absolute;top:-10px;right:-10px;background:#fff;border-radius:50%;width:40px;height:40px;border:none;font-size:22px;cursor:pointer;box-shadow:0 8px 24px rgba(2,6,23,0.6)}
            @media (max-width:600px){.tl-lightbox .tl-close{width:36px;height:36px;font-size:20px}}
        `;
        document.head.appendChild(s);
    }
}

/**
 * Initialize smooth scroll for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#' || href === '#!' || href === '#main-content') return;
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
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
    .then(response => response.text().then(text => ({ ok: response.ok, text })))
    .then(({ ok, text }) => {
        if (!ok) {
            let message = 'Ndodhi një gabim. Ju lutemi provoni përsëri.';
            try {
                const data = JSON.parse(text);
                if (data && data.message) message = data.message;
            } catch (e) {
                // Server may have returned an HTML error page; keep default message
            }
            showNotification(message, 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHTML;
            return;
        }

        // Success
        showNotification('Vlerësimi u dërgua me sukses! 🎉', 'success');

        // Reset form
        form.reset();
        document.querySelectorAll('.star-rating').forEach(ratingWidget => {
            const targetId = ratingWidget.dataset.target || 'rating-value';
            const input = document.getElementById(targetId);
            if (input) input.value = '0';
            ratingWidget.querySelectorAll('.star').forEach(star => {
                star.classList.remove('active');
                star.setAttribute('aria-checked', 'false');
            });
        });

        // Redirect after 2 seconds
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ndodhi një gabim në lidhje. Kontrolloni internetin tuaj.', 'error');
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
    notification.setAttribute('role', 'status');

    const content = document.createElement('div');
    content.className = 'notification-content';

    const icon = document.createElement('i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    icon.setAttribute('aria-hidden', 'true');

    const span = document.createElement('span');
    span.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.className = 'notification-close';
    closeBtn.setAttribute('aria-label', 'Mbyll');
    closeBtn.innerHTML = '<i class="fas fa-times" aria-hidden="true"></i>';

    content.appendChild(icon);
    content.appendChild(span);
    notification.appendChild(content);
    notification.appendChild(closeBtn);

    document.body.appendChild(notification);
    
    // Close notification
    const closeBtnRef = notification.querySelector('.notification-close');
    closeBtnRef.addEventListener('click', () => {
        notification.style.animation = 'notification-slide-out 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto close after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.style.animation = 'notification-slide-out 0.3s ease-out forwards';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}