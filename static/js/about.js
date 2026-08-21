/**
 * Open Map - About Page JavaScript
 * Handles scroll-reveal animations and animated stat counters
 */

document.addEventListener('DOMContentLoaded', () => {

    const aboutPage = document.querySelector('.about-page');

    // This script only drives the about page. On any other page it must be a no-op.
    if (!aboutPage) {
        return;
    }

    const pageRoot = aboutPage;

    // ==================== SCROLL-REVEAL ====================

    const revealTargets = pageRoot.querySelectorAll(
        '.story-content, .story-image, .step-card, .value-card, ' +
        '.benefit-item, .testimonial-card, .cta-card, .band-stat'
    );

    revealTargets.forEach((el) => el.classList.add('reveal'));

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (!entry.isIntersecting || entry.target.dataset.revealed) {
                return;
            }

            entry.target.dataset.revealed = 'true';

            setTimeout(() => {
                entry.target.classList.add('is-visible');
            }, (index % 6) * 90); // Stagger animation
        });
    }, {
        threshold: 0.12,
        rootMargin: '0px 0px -60px 0px'
    });

    revealTargets.forEach((el) => revealObserver.observe(el));

    // ==================== ANIMATED COUNTERS ====================

    /**
     * Animate counter from 0 to target value using requestAnimationFrame
     */
    function animateCounter(element) {
        const target = Number(element.dataset.count);

        if (!target || target <= 0) {
            element.textContent = target;
            return;
        }

        const duration = 1800;
        const startTime = performance.now();

        function update(time) {
            const progress = Math.min((time - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);

            element.textContent = Math.floor(eased * target);

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = target;
            }
        }

        requestAnimationFrame(update);
    }

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting || entry.target.dataset.animated) {
                return;
            }

            entry.target.dataset.animated = 'true';
            animateCounter(entry.target);
        });
    }, {
        threshold: 0.4
    });

    pageRoot.querySelectorAll('.band-number[data-count]').forEach((el) => {
        counterObserver.observe(el);
    });

    // ==================== LAZY LOADING ENHANCEMENT ====================

    pageRoot.querySelectorAll('img[loading="lazy"]').forEach((img) => {
        img.addEventListener('load', function () {
            this.classList.add('loaded');
        });

        if (!img.complete) {
            img.classList.add('loading');
        }
    });

});
