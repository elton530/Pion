/**
 * Tour Status Handler
 * Handles real-time tour status updates, validation, and UI feedback
 */

class TourStatusHandler {
    constructor() {
        this.statusSelect = document.getElementById('id_status');
        this.confirmationDiv = document.getElementById('status-change-confirmation');
        this.originalStatus = this.statusSelect ? this.statusSelect.value : null;
        
        this.init();
    }

    init() {
        if (this.statusSelect) {
            this.statusSelect.addEventListener('change', (e) => this.handleStatusChange(e));
        }
    }

    handleStatusChange(event) {
        const newStatus = event.target.value;
        const statusDisplay = this.getStatusDisplay(newStatus);
        
        if (this.confirmationDiv) {
            this.confirmationDiv.style.display = 'block';
            const message = document.createElement('p');
            message.className = 'confirmation-message';
            message.textContent = 'Statusi do të ndryshohet në: ';
            const strong = document.createElement('strong');
            strong.textContent = statusDisplay;
            message.appendChild(strong);
            this.confirmationDiv.innerHTML = '';
            this.confirmationDiv.appendChild(message);
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

        const icon = document.createElement('i');
        icon.className = `fas fa-${this.getAlertIcon(type)}`;

        const span = document.createElement('span');
        span.textContent = message;

        alertDiv.appendChild(icon);
        alertDiv.appendChild(span);
        
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

        const icon = document.createElement('i');
        icon.className = 'fas fa-exclamation-circle';

        const content = document.createElement('div');
        const strong = document.createElement('strong');
        strong.textContent = 'Ju lutem korrigjoni këto gabime:';
        const ul = document.createElement('ul');
        ul.style.margin = '8px 0 0 20px';
        ul.style.padding = '0';
        errors.forEach(err => {
            const li = document.createElement('li');
            li.textContent = err;
            ul.appendChild(li);
        });
        content.appendChild(strong);
        content.appendChild(ul);

        alertDiv.appendChild(icon);
        alertDiv.appendChild(content);

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
 * Initialize all handlers when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize on edit_tour page
    if (document.querySelector('.edit-tour')) {
        new TourStatusHandler();
        new TourFormValidator();
    }
});
