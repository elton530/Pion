// guide_dashboard.js — small enhancements: ripple effect
(function(){
    'use strict';

    function createRipple(event) {
        const button = event.currentTarget;
        const rect = button.getBoundingClientRect();
        const wave = document.createElement('span');
        wave.className = 'ripple__wave';
        const size = Math.max(rect.width, rect.height) * 0.6;

        const clientX = event.type === 'touchstart' && event.touches && event.touches[0]
            ? event.touches[0].clientX : event.clientX;
        const clientY = event.type === 'touchstart' && event.touches && event.touches[0]
            ? event.touches[0].clientY : event.clientY;

        wave.style.width = wave.style.height = size + 'px';
        wave.style.left = (clientX - rect.left - size/2) + 'px';
        wave.style.top = (clientY - rect.top - size/2) + 'px';
        button.appendChild(wave);
        setTimeout(() => wave.remove(), 700);
    }

    function enhanceButtons() {
        const buttons = document.querySelectorAll('.guide-dashboard .btn-small, .guide-dashboard .btn-create, .guide-dashboard .btn-edit-profile');
        buttons.forEach(btn => {
            btn.classList.add('ripple');
            btn.addEventListener('mousedown', createRipple);
            btn.addEventListener('touchstart', createRipple, {passive: true});
        });
    }

    document.addEventListener('DOMContentLoaded', function(){
        enhanceButtons();
    });
})();
