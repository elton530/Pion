// guide_dashboard.js — small enhancements: ripple effect, tooltips, keyboard accessibility
(function(){
    'use strict';

    function createRipple(event) {
        const button = event.currentTarget;
        const rect = button.getBoundingClientRect();
        const wave = document.createElement('span');
        wave.className = 'ripple__wave';
        const size = Math.max(rect.width, rect.height) * 0.6;
        wave.style.width = wave.style.height = size + 'px';
        wave.style.left = (event.clientX - rect.left - size/2) + 'px';
        wave.style.top = (event.clientY - rect.top - size/2) + 'px';
        button.appendChild(wave);
        setTimeout(() => wave.remove(), 700);
    }

    function enhanceButtons() {
        const buttons = document.querySelectorAll('.guide-dashboard .btn-small, .guide-dashboard .btn-create, .guide-dashboard .btn-edit-profile');
        buttons.forEach(btn => {
            // make ripple container
            btn.classList.add('ripple');

            // accessibility: make non-anchor buttons keyboard focusable
            if (btn.tagName.toLowerCase() !== 'a' && !btn.hasAttribute('tabindex')) {
                btn.setAttribute('tabindex', '0');
            }

            btn.addEventListener('mousedown', createRipple);
            btn.addEventListener('touchstart', createRipple, {passive: true});

            // keyboard activation
            btn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    // simulate click for keyboard
                    e.preventDefault();
                    btn.click();
                }
            });
        });
    }

    function confirmSensitiveActions() {
        // If any action link has data-confirm attribute, show a confirm dialog
        document.addEventListener('click', function(e){
            const target = e.target.closest('[data-confirm]');
            if (!target) return;
            const message = target.getAttribute('data-confirm') || 'A jeni i sigurt?';
            if (!confirm(message)) {
                e.preventDefault();
                e.stopImmediatePropagation();
                return false;
            }
            return true;
        }, true);
    }

    function initTooltips() {
        // For simple mobile-friendly tooltips we rely on CSS [data-tooltip]
        // Add aria attributes for screen readers
        document.querySelectorAll('[data-tooltip]').forEach(el => {
            el.setAttribute('aria-describedby', '');
            el.setAttribute('tabindex', el.tabIndex >= 0 ? el.tabIndex : 0);
        });
    }

    document.addEventListener('DOMContentLoaded', function(){
        enhanceButtons();
        confirmSensitiveActions();
        initTooltips();
    });
})();
