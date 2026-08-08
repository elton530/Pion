/**
 * Open Map - Home Page JavaScript
 * Handles hero slider, counter animations, and interactive elements
 */

document.addEventListener('DOMContentLoaded', () => {

    const homePage = document.querySelector('.home-page');

    // This script only drives the homepage. On any other page it must be a no-op.
    if (!homePage) {
        return;
    }

    const pageRoot = homePage;

    // ==================== HERO SLIDER ====================

    const slider = pageRoot.querySelector('.hero-slider');
    const slides = pageRoot.querySelectorAll('.hero-slider .slide');
    const prevBtn = pageRoot.querySelector('.slider-control.prev');
    const nextBtn = pageRoot.querySelector('.slider-control.next');
    const indicators = pageRoot.querySelectorAll('.slider-indicators .indicator');

    if (slider && slides.length > 1) {

        let currentSlide = 0;
        let slideInterval = null;
        const autoplayDelay = 5500;

        /**
         * Go to specific slide
         */
        function goToSlide(index) {
            slides[currentSlide]?.classList.remove('active');
            indicators[currentSlide]?.classList.remove('active');

            currentSlide = index;

            slides[currentSlide]?.classList.add('active');
            indicators[currentSlide]?.classList.add('active');
        }

        /**
         * Go to next slide
         */
        function nextSlide() {
            const next = (currentSlide + 1) % slides.length;
            goToSlide(next);
        }

        /**
         * Go to previous slide
         */
        function prevSlide() {
            const prev = (currentSlide - 1 + slides.length) % slides.length;
            goToSlide(prev);
        }

        /**
         * Start auto-play
         */
        function startAutoPlay() {
            if (!slideInterval) {
                slideInterval = setInterval(nextSlide, autoplayDelay);
            }
        }

        /**
         * Stop auto-play
         */
        function stopAutoPlay() {
            clearInterval(slideInterval);
            slideInterval = null;
        }

        // Next button click
        nextBtn?.addEventListener('click', () => {
            stopAutoPlay();
            nextSlide();
            startAutoPlay();
        });

        // Previous button click
        prevBtn?.addEventListener('click', () => {
            stopAutoPlay();
            prevSlide();
            startAutoPlay();
        });

        // Indicator clicks
        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                stopAutoPlay();
                goToSlide(index);
                startAutoPlay();
            });
        });

        // Pause on hover
        slider.addEventListener('mouseenter', stopAutoPlay);
        slider.addEventListener('mouseleave', startAutoPlay);

        // Keyboard navigation (only when not typing in a form field)
        document.addEventListener('keydown', (e) => {
            const tag = document.activeElement && document.activeElement.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
                return;
            }
            if (e.key === 'ArrowLeft') {
                stopAutoPlay();
                prevSlide();
                startAutoPlay();
            } else if (e.key === 'ArrowRight') {
                stopAutoPlay();
                nextSlide();
                startAutoPlay();
            }
        });

        // Start auto-play
        startAutoPlay();
    }

    // ==================== SCROLL-TRIGGERED EFFECTS ====================
    // (stat counters + card fade-in share a single observer)

    const statNumbers = pageRoot.querySelectorAll('.stat-number[data-target]');
    const revealCards = pageRoot.querySelectorAll('.tour-card, .feature-card');

    /**
     * Animate counter from 0 to target value using requestAnimationFrame
     */
    function animateCounter(element) {
        const target = Number(element.dataset.target);

        if (!target || target <= 0) {
            return;
        }

        const duration = 1800;
        const startTime = performance.now();

        function update(time) {
            const progress = Math.min((time - startTime) / duration, 1);
            const value = Math.floor(progress * target);

            element.textContent = value;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = target;
            }
        }

        requestAnimationFrame(update);
    }

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (!entry.isIntersecting || entry.target.dataset.animated) {
                return;
            }

            entry.target.dataset.animated = 'true';

            if (entry.target.matches('.stat-number[data-target]')) {
                animateCounter(entry.target);
            } else {
                setTimeout(() => {
                    entry.target.classList.add('is-visible');
                }, index * 100); // Stagger animation
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    statNumbers.forEach((stat) => revealObserver.observe(stat));

    revealCards.forEach((card) => {
        card.classList.add('reveal-on-scroll');
        revealObserver.observe(card);
    });

    // ==================== SMOOTH SCROLL ====================

    /**
     * Smooth scroll to section on anchor click
     */
    pageRoot.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '#!' && href !== '#main-content') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // ==================== TOUR CARD INTERACTIONS ====================

    /**
     * Add ripple effect on tour card click
     */
    const tourCards = homePage.querySelectorAll('.tour-card');

    function addRipple(card, x, y) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');

        const rect = card.getBoundingClientRect();
        const left = x - rect.left;
        const top = y - rect.top;

        ripple.style.left = `${left}px`;
        ripple.style.top = `${top}px`;

        card.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    tourCards.forEach((card) => {
        card.addEventListener('click', function (e) {
            addRipple(this, e.clientX, e.clientY);
        });

        card.addEventListener('touchstart', function (e) {
            const touch = e.touches && e.touches[0];
            if (touch) {
                addRipple(this, touch.clientX, touch.clientY);
            }
        });
    });

    // ==================== LAZY LOADING ENHANCEMENT ====================

    /**
     * Add loading state to images
     */
    const images = homePage.querySelectorAll('img[loading="lazy"]');

    images.forEach((img) => {
        img.addEventListener('load', function () {
            this.classList.add('loaded');
        });

        if (!img.complete) {
            img.classList.add('loading');
        }
    });

});