/**
 * Home Page JavaScript
 * Handles hero slider, counter animations, and interactive elements
 */

document.addEventListener('DOMContentLoaded', function () {
    
    // ==================== HERO SLIDER ====================
    
    const slides = document.querySelectorAll('.hero-slider .slide');
    const prevBtn = document.querySelector('.slider-control.prev');
    const nextBtn = document.querySelector('.slider-control.next');
    const indicators = document.querySelectorAll('.slider-indicators .indicator');
    
    if (slides.length > 1) {
        let currentSlide = 0;
        let slideInterval;
        
        /**
         * Go to specific slide
         */
        function goToSlide(index) {
            // Remove active class from current slide and indicator
            slides[currentSlide].classList.remove('active');
            if (indicators[currentSlide]) {
                indicators[currentSlide].classList.remove('active');
            }
            
            // Update current slide
            currentSlide = index;
            
            // Add active class to new slide and indicator
            slides[currentSlide].classList.add('active');
            if (indicators[currentSlide]) {
                indicators[currentSlide].classList.add('active');
            }
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
            slideInterval = setInterval(nextSlide, 5500);
        }
        
        /**
         * Stop auto-play
         */
        function stopAutoPlay() {
            clearInterval(slideInterval);
        }
        
        // Next button click
        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                stopAutoPlay();
                nextSlide();
                startAutoPlay();
            });
        }
        
        // Previous button click
        if (prevBtn) {
            prevBtn.addEventListener('click', function() {
                stopAutoPlay();
                prevSlide();
                startAutoPlay();
            });
        }
        
        // Indicator clicks
        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', function() {
                stopAutoPlay();
                goToSlide(index);
                startAutoPlay();
            });
        });
        
        // Pause on hover
        const slider = document.querySelector('.hero-slider');
        if (slider) {
            slider.addEventListener('mouseenter', stopAutoPlay);
            slider.addEventListener('mouseleave', startAutoPlay);
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
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
    
    // ==================== COUNTER ANIMATION ====================
    
    const statNumbers = document.querySelectorAll('.stat-number[data-target]');
    
    /**
     * Animate counter from 0 to target value
     */
    function animateCounter(element) {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 2000; // 2 seconds
        const step = target / (duration / 16); // 60fps
        let current = 0;
        
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }
    
    /**
     * Intersection Observer for counter animation
     */
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
                animateCounter(entry.target);
                entry.target.classList.add('counted');
            }
        });
    }, observerOptions);
    
    statNumbers.forEach(stat => observer.observe(stat));
    
    // ==================== SMOOTH SCROLL ====================
    
    /**
     * Smooth scroll to section on anchor click
     */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '#!') {
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
    
    // ==================== SCROLL ANIMATIONS ====================
    
    /**
     * Add fade-in animation to elements on scroll
     */
    const animateOnScroll = document.querySelectorAll('.tour-card, .feature-card');
    
    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100); // Stagger animation
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animateOnScroll.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        scrollObserver.observe(element);
    });
    
    // ==================== PARALLAX EFFECT ====================
    
    /**
     * Simple parallax effect for hero section (disabled to prevent overlap)
     */
    // Commented out to prevent overlap issues during scroll
    /*
    const hero = document.querySelector('.hero');
    
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallax = scrolled * 0.5;
            hero.style.transform = `translateY(${parallax}px)`;
        });
    }
    */
    
    // ==================== TOUR CARD INTERACTIONS ====================
    
    /**
     * Add ripple effect on tour card click
     */
    const tourCards = document.querySelectorAll('.tour-card');
    
    tourCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Create ripple element
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            
            // Calculate position
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            this.appendChild(ripple);
            
            // Remove ripple after animation
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // ==================== LAZY LOADING ENHANCEMENT ====================
    
    /**
     * Add loading state to images
     */
    const images = document.querySelectorAll('img[loading="lazy"]');
    
    images.forEach(img => {
        img.addEventListener('load', function() {
            this.classList.add('loaded');
        });
        
        // Add loading class
        if (!img.complete) {
            img.classList.add('loading');
        }
    });
    
    // ==================== UTILS ====================
    
    /**
     * Debounce function for performance
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Check if element is in viewport
     */
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // ==================== INITIALIZATION ====================
    
    console.log('✅ Home page JavaScript initialized');
    
    // Track page view (example for analytics)
    if (typeof gtag !== 'undefined') {
        gtag('event', 'page_view', {
            'page_title': 'Home',
            'page_location': window.location.href,
            'page_path': window.location.pathname
        });
    }
});