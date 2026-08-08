// Përmirësime të avancuara për edit_tour.js
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
        const buttons = document.querySelectorAll('.edit-tour button');
        buttons.forEach(btn => {
            btn.classList.add('ripple');

            btn.addEventListener('mousedown', createRipple);
            btn.addEventListener('touchstart', createRipple, {passive: true});
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
                if (!file.type.startsWith('image/')) {
                    alert('Zgjidh një skedar imazhi të vlefshëm.');
                    return;
                }
                if (file.size > 5 * 1024 * 1024) {
                    alert('Skedari është shumë i madh (max 5MB).');
                    return;
                }

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
        addImagePreviews();
    });
})();