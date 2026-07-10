// Përmirësime të avancuara për edit_tour.js
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
        const buttons = document.querySelectorAll('.edit-tour button');
        buttons.forEach(btn => {
            btn.classList.add('ripple');

            if (btn.tagName.toLowerCase() !== 'a' && !btn.hasAttribute('tabindex')) {
                btn.setAttribute('tabindex', '0');
            }

            btn.addEventListener('mousedown', createRipple);
            btn.addEventListener('touchstart', createRipple, {passive: true});

            btn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    btn.click();
                }
            });
        });
    }

    function addTooltip() {
        const fields = document.querySelectorAll('.edit-tour input, .edit-tour textarea, .edit-tour select');
        fields.forEach(field => {
            field.addEventListener('focus', () => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = field.getAttribute('placeholder') || 'Plotëso këtë fushë';
                field.parentElement.appendChild(tooltip);
                setTimeout(() => tooltip.remove(), 2000);
            });
        });
    }

    function addImagePreviews() {
        const map = [
            {selector: 'input[type=file][name="main_image"]', previewId: 'main-image-preview'},
            {selector: 'input[type=file][name="thumbnail"]', previewId: 'thumbnail-preview'}
        ];

        map.forEach(item => {
            const input = document.querySelector(item.selector);
            const preview = document.getElementById(item.previewId);
            if (!input || !preview) return;

            input.addEventListener('change', (e) => {
                const file = e.target.files && e.target.files[0];
                if (!file) return;
                if (!file.type.startsWith('image/')) return;

                const reader = new FileReader();
                reader.onload = function(ev) {
                    preview.innerHTML = '';
                    const img = document.createElement('img');
                    img.src = ev.target.result;
                    preview.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        enhanceButtons();
        addTooltip();
        addImagePreviews();
    });
})();