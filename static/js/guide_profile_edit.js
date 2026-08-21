/**
 * Guide Profile Edit Module
 * Handles image preview, character counting, and message management
 */

class GuideProfileEditor {
    constructor() {
        this.init();
    }

    /**
     * Initialize all event listeners and setup
     */
    init() {
        this.setupPhotoUpload();
        this.setupBioCounter();
        this.setupFormValidation();
        this.markServerErrors();
        this.disableFormOnSubmit();
    }

    /**
     * Setup photo upload and preview
     */
    setupPhotoUpload() {
        const photoInput = document.querySelector('input[type="file"][name="photo"]');
        const previewImage = document.getElementById('preview-image');
        const photoPlaceholder = document.getElementById('photo-placeholder');

        if (!photoInput) return;

        photoInput.addEventListener('change', (e) => this.handlePhotoChange(e, previewImage, photoPlaceholder));

        // Click handler for overlay
        const photoOverlay = document.querySelector('.photo-overlay');
        if (photoOverlay) {
            photoOverlay.addEventListener('click', () => photoInput.click());
        }

        // Click handler for placeholder
        if (photoPlaceholder) {
            photoPlaceholder.addEventListener('click', () => photoInput.click());
        }
    }

    /**
     * Handle photo file selection and preview
     */
    handlePhotoChange(event, previewImage, photoPlaceholder) {
        const file = event.target.files[0];

        if (!file) return;

        // Validate file type
        if (!this.isValidImageFile(file)) {
            this.showErrorMessage('Zgjidh një skedar të vlefshëm (JPG, PNG)');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            this.showErrorMessage('Skedar shumë i madh (max 5MB)');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.updatePhotoPreview(e.target.result, previewImage, photoPlaceholder);
        };
        reader.readAsDataURL(file);
    }

    /**
     * Validate image file type
     */
    isValidImageFile(file) {
        const validTypes = ['image/jpeg', 'image/png'];
        return validTypes.includes(file.type);
    }

    /**
     * Setup photo upload and preview
     */

    /**
     * Update photo preview in DOM
     */
    updatePhotoPreview(dataUrl, previewImage, photoPlaceholder) {
        if (previewImage) {
            previewImage.src = dataUrl;
            previewImage.parentElement.classList.add('fade-in');
        } else if (photoPlaceholder) {
            const img = document.createElement('img');
            img.src = dataUrl;
            img.alt = 'Përshkrimi';
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '50%';
            photoPlaceholder.innerHTML = '';
            photoPlaceholder.appendChild(img);
        }
    }

    /**
     * Setup bio character counter
     */
    setupBioCounter() {
        const bioTextarea = document.querySelector('textarea[name="bio"]');
        const charCounter = document.getElementById('bio-count');

        if (!bioTextarea || !charCounter) return;

        const maxChars = 500;

        // Initialize counter
        this.updateCharCounter(bioTextarea.value.length, charCounter, maxChars);

        // Update on input
        bioTextarea.addEventListener('input', (e) => {
            let value = e.target.value;

            // Enforce max length
            if (value.length > maxChars) {
                e.target.value = value.substring(0, maxChars);
                value = e.target.value;
            }

            this.updateCharCounter(value.length, charCounter, maxChars);
        });

        // Warn when near limit
        bioTextarea.addEventListener('keyup', (e) => {
            const remaining = maxChars - e.target.value.length;
            if (remaining < 50 && remaining > 0) {
                this.setWarningState(bioTextarea, true);
            } else {
                this.setWarningState(bioTextarea, false);
            }
        });
    }

    /**
     * Update character counter display
     */
    updateCharCounter(current, element, max) {
        element.textContent = current;
        const percentage = (current / max) * 100;

        if (percentage > 90) {
            element.parentElement.style.color = '#ef4444';
        } else if (percentage > 75) {
            element.parentElement.style.color = '#f59e0b';
        } else {
            element.parentElement.style.color = '#94a3b8';
        }
    }

    /**
     * Set warning state for textarea
     */
    setWarningState(element, isWarning) {
        if (isWarning) {
            element.style.borderColor = '#f59e0b';
            element.style.boxShadow = '0 0 0 4px rgba(245, 158, 11, 0.1)';
        } else {
            element.style.borderColor = '#e2e8f0';
            element.style.boxShadow = 'none';
        }
    }

    /**
     * Fade out element with animation
     */
    fadeOutElement(element) {
        element.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            element.remove();
        }, 300);
    }

    /**
     * Show error message (temporary)
     */
    showErrorMessage(message) {
        const container = document.getElementById('messages-container') || 
                         document.querySelector('.messages-container') ||
                         document.querySelector('.profile-form');

        if (!container) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message error';
        messageDiv.setAttribute('role', 'alert');

        const icon = document.createElement('i');
        icon.className = 'fas fa-exclamation-circle';

        const span = document.createElement('span');
        span.textContent = message;

        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'close-message';
        closeButton.setAttribute('aria-label', 'Mbyll mesazhin');
        closeButton.textContent = '×';

        messageDiv.appendChild(icon);
        messageDiv.appendChild(span);
        messageDiv.appendChild(closeButton);

        const firstMessage = container.querySelector('.message');
        if (firstMessage) {
            firstMessage.parentElement.insertBefore(messageDiv, firstMessage);
        } else {
            container.insertBefore(messageDiv, container.firstChild);
        }

        // Add close handler
        messageDiv.querySelector('.close-message').addEventListener('click', () => 
            this.fadeOutElement(messageDiv)
        );

        // Auto-close after 5 seconds
        setTimeout(() => this.fadeOutElement(messageDiv), 5000);
    }

    /**
     * Setup form validation before submit
     */
    setupFormValidation() {
        const form = document.getElementById('profile-form');
        if (!form) return;

        form.addEventListener('submit', (e) => this.validateForm(e));
    }

    /**
     * Validate form before submission
     */
    validateForm(event) {
        const form = event.currentTarget;
        const phoneInput = form.querySelector('input[name="phone"]');
        const locationInput = form.querySelector('input[name="location"]');

        let isValid = true;
        let errors = [];

        // Validate phone if provided
        if (phoneInput && phoneInput.value && !this.isValidPhone(phoneInput.value)) {
            errors.push('Numri i telefonit nuk është valid');
            isValid = false;
        }

        // Validate location if provided
        if (locationInput && locationInput.value.trim().length < 2) {
            errors.push('Vendndodhja duhet të ketë të paktën 2 karaktere');
            isValid = false;
        }

        if (!isValid) {
            event.preventDefault();
            errors.forEach(error => this.showErrorMessage(error));
        }
    }

    /**
     * Highlight inputs that have server-side validation errors and focus the first
     */
    markServerErrors() {
        const form = document.getElementById('profile-form');
        if (!form) return;

        // Find all inline error lists and mark the related input
        const errorLists = form.querySelectorAll('.messages.error');
        let firstFocused = false;
        errorLists.forEach((errList) => {
            // Prefer finding the field inside the same form-group
            let field = errList.closest('.form-group')?.querySelector('input,select,textarea');

            if (!field) {
                // Fall back to the element right before the error list
                field = errList.previousElementSibling;
                if (field && field.tagName === 'LABEL') {
                    field = field.previousElementSibling;
                }
            }

            if (field) {
                field.classList.add('input-error');
                if (!firstFocused && field.focus && typeof field.focus === 'function') {
                    field.focus();
                    firstFocused = true;
                }
            }
        });
    }

    /**
     * Validate phone number format
     */
    isValidPhone(phone) {
        // Accept +359 format or similar international formats
        const phoneRegex = /^\+?[1-9]\d{1,14}$/;
        return phoneRegex.test(phone.replace(/[\s\-()]/g, ''));
    }

    /**
     * Disable form on submit
     */
    disableFormOnSubmit() {
        const submitBtn = document.getElementById('submit-btn');
        const form = document.getElementById('profile-form');

        if (!form || !submitBtn) return;

        form.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <span>Duke ruajtur...</span>
            `;
        });
    }
}

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    new GuideProfileEditor();
});

/**
 * Add fade-in animation class for photo
 */
const style = document.createElement('style');
style.textContent = `
    .fade-in {
        animation: fadeInScale 0.3s ease;
    }

    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
`;
document.head.appendChild(style);