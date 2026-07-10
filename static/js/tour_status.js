/**
 * Tour Status Handler
 * Handles real-time tour status updates, validation, and UI feedback
 */

class TourStatusHandler {
    constructor() {
        this.statusSelect = document.getElementById('id_status');
        this.confirmationDiv = document.getElementById('status-change-confirmation');
        this.originalStatus = this.statusSelect ? this.statusSelect.value : null;
        this.form = document.querySelector('.profile-form');
        
        this.init();
    }

    init() {
        if (this.statusSelect) {
            this.statusSelect.addEventListener('change', (e) => this.handleStatusChange(e));
        }
        
        // Add form submission handler for real-time updates
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
    }

    handleStatusChange(event) {
        const newStatus = event.target.value;
        const statusDisplay = this.getStatusDisplay(newStatus);
        
        if (this.confirmationDiv) {
            this.confirmationDiv.style.display = 'block';
            this.confirmationDiv.innerHTML = `
                <p class="confirmation-message">
                    Statusi do të ndryshohet në: <strong>${statusDisplay}</strong>
                </p>
            `;
        }

        // Show warning if changing from published to draft
        if (this.originalStatus === 'published' && newStatus === 'draft') {
            this.showStatusWarning('Turit do ti heqet aksesi publik pas ruajtjes.');
        }
        
        // Show info if changing to published
        if (newStatus === 'published') {
            this.showStatusInfo('Turit do ti jepet aksesi publik dhe do të shfaqet në listën e tureve.');
        }
    }

    handleFormSubmit(event) {
        const newStatus = this.statusSelect.value;
        
        // Show saving indicator
        this.showAlert('Duke ruajtur ndryshimet...', 'info');
        
        // Optionally, update status immediately via AJAX (uncomment to enable)
        // if (newStatus !== this.originalStatus) {
        //     this.updateStatusViaAjax(newStatus);
        // }
    }

    updateStatusViaAjax(newStatus) {
        const tourId = this.getTourId();
        if (!tourId) return;

        fetch(`/tours/api/status/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                tour_id: tourId,
                status: newStatus
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert(`✓ ${data.message}`, 'success');
                this.originalStatus = newStatus;
            } else {
                this.showAlert(`Gabim: ${data.error}`, 'warning');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showAlert('Gabim në lidhje me serverin', 'warning');
        });
    }

    getTourId() {
        // Try to get from URL or data attribute
        const urlMatch = window.location.pathname.match(/\/tours\/(\d+)\//);
        if (urlMatch) return urlMatch[1];
        
        const tourIdInput = document.querySelector('input[name="tour_id"]');
        if (tourIdInput) return tourIdInput.value;
        
        return null;
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    getStatusDisplay(status) {
        const statusMap = {
            'draft': 'Draft (Nuk është publikuar)',
            'published': 'Publikuar (Publik)',
            'hidden': 'I Fshehur',
            'cancelled': 'Anuluar',
            'completed': 'Përfunduar'
        };
        return statusMap[status] || status;
    }

    showStatusWarning(message) {
        this.showAlert(message, 'warning');
    }

    showStatusInfo(message) {
        this.showAlert(message, 'info');
    }

    showAlert(message, type = 'info') {
        const alerts = document.querySelectorAll('.status-change-alert');
        alerts.forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `status-change-alert ${type}`;
        alertDiv.innerHTML = `<i class="fas fa-${this.getAlertIcon(type)}"></i><span>${message}</span>`;
        
        const form = document.querySelector('.profile-form') || document.querySelector('.edit-tour');
        if (form) {
            form.insertBefore(alertDiv, form.firstChild);
        }
    }

    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

/**
 * Form Validation Handler
 * Validates tour form fields before submission
 */
class TourFormValidator {
    constructor() {
        this.form = document.querySelector('.profile-form');
        this.init();
    }

    init() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.validateForm(e));
        }
    }

    validateForm(event) {
        const errors = [];

        // Check required fields
        const requiredFields = {
            'id_title': 'Titulla i turit',
            'id_price_per_person': 'Çmimi për person',
            'id_date': 'Data e turit',
            'id_time_start': 'Koha e fillimit'
        };

        for (const [fieldId, fieldName] of Object.entries(requiredFields)) {
            const field = document.getElementById(fieldId);
            if (field && !field.value.trim()) {
                errors.push(`${fieldName} është e nevojshme`);
            }
        }

        // Check if price is positive
        const priceField = document.getElementById('id_price_per_person');
        if (priceField && parseFloat(priceField.value) <= 0) {
            errors.push('Çmimi duhet të jetë më i madh se 0');
        }

        // Show errors if any
        if (errors.length > 0) {
            event.preventDefault();
            this.showErrors(errors);
        }
    }

    showErrors(errors) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'status-change-alert warning';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <div>
                <strong>Ju lutem korrigjoni këto gabime:</strong>
                <ul style="margin: 8px 0 0 20px; padding: 0;">
                    ${errors.map(err => `<li>${err}</li>`).join('')}
                </ul>
            </div>
        `;

        const form = document.querySelector('.profile-form');
        if (form) {
            // Remove existing errors
            const existingAlerts = form.querySelectorAll('.status-change-alert');
            existingAlerts.forEach(alert => alert.remove());
            
            form.insertBefore(alertDiv, form.firstChild);
            form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

/**
 * Tour Status Display Updater
 * Updates tour status display on my_tours page in real-time
 */
class TourStatusDisplayUpdater {
    constructor() {
        this.init();
    }

    init() {
        // Check every 5 seconds if status has changed via other browser tab/window
        if (document.body.contains(document.querySelector('.tour-card'))) {
            setInterval(() => this.checkStatusUpdates(), 5000);
        }
    }

    checkStatusUpdates() {
        const tourCards = document.querySelectorAll('.tour-card');
        tourCards.forEach(card => {
            const statusBadge = card.querySelector('.status-badge-corner span');
            if (statusBadge) {
                const currentStatus = this.extractStatus(statusBadge.textContent);
                // In production, this would check against server
                this.updateCardStyling(card, currentStatus);
            }
        });
    }

    extractStatus(text) {
        if (text.includes('Publikuar')) return 'published';
        if (text.includes('Draft')) return 'draft';
        if (text.includes('I Fshehur')) return 'hidden';
        if (text.includes('Anuluar')) return 'cancelled';
        return 'unknown';
    }

    updateCardStyling(card, status) {
        card.classList.remove('status-published', 'status-draft', 'status-hidden', 'status-cancelled');
        card.classList.add(`status-${status}`);
    }
}

/**
 * Initialize all handlers when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize on edit_tour page
    if (document.querySelector('.edit-tour')) {
        new TourStatusHandler();
        new TourFormValidator();
    }

    // Initialize on my_tours page
    if (document.querySelector('.tour-grid')) {
        new TourStatusDisplayUpdater();
    }
});

/**
 * Auto-save form changes (optional - saves draft every 30 seconds)
 */
class AutoSaveHandler {
    constructor() {
        this.form = document.querySelector('.profile-form');
        this.isSaving = false;
        
        if (this.form) {
            this.init();
        }
    }

    init() {
        // Save every 30 seconds if form has changes
        setInterval(() => this.checkAndSave(), 30000);
        
        // Also save on blur for text fields
        const fields = this.form.querySelectorAll('input[type="text"], textarea, select');
        fields.forEach(field => {
            field.addEventListener('blur', () => this.showAutoSaveIndicator());
        });
    }

    checkAndSave() {
        // This would typically check if there are unsaved changes
        // and submit the form via AJAX in the background
        // For now, just show a visual indicator
        if (!this.isSaving) {
            this.showAutoSaveIndicator();
        }
    }

    showAutoSaveIndicator() {
        const indicator = document.createElement('small');
        indicator.className = 'auto-save-indicator';
        indicator.textContent = '✓ Ndryshimet ruhen automatikisht';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 8px 16px;
            border-radius: 999px;
            font-size: 0.85rem;
            animation: slideUp 0.3s ease-out, slideOut 0.3s ease-out 2.7s;
            z-index: 1000;
        `;

        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateY(0); opacity: 1; }
                to { transform: translateY(20px); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(indicator);
        setTimeout(() => indicator.remove(), 3000);
    }
}

// Initialize auto-save on edit page
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.edit-tour')) {
        // Uncomment to enable auto-save
        // new AutoSaveHandler();
    }
});
