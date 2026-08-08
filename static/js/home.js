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

    // ==================== SCROLL-TRIGGERED EFFECTS ====================
    // (stat counters + card fade-in share a single observer)

    const statNumbers = pageRoot.querySelectorAll('.hero-stat-number[data-target]');
    const revealCards = pageRoot.querySelectorAll('.tour-card, .feature-card, .cta-card');

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

            if (entry.target.matches('.hero-stat-number[data-target]')) {
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