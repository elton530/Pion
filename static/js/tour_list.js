// static/js/tour_list.js
document.addEventListener('DOMContentLoaded', function() {
    
    // Elements
    const tourGrid = document.getElementById('tour-grid');
    const tourCards = document.querySelectorAll('.tour-card');
    
    let allTours = Array.from(tourCards);
    
    // ==================== ANIMATIONS ====================
    
    // Add smooth entrance animation
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    allTours.forEach((card, index) => {
        card.style.animationDelay = `${index * 50}ms`;
        observer.observe(card);
    });
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .tour-card {
            opacity: 0;
            transform: translateY(30px);
            animation: fadeInUp 0.6s cubic-bezier(0.23, 1, 0.320, 1) forwards;
        }
        
        .tour-card.visible {
            opacity: 1;
            transform: translateY(0);
        }
    `;
    document.head.appendChild(style);
});