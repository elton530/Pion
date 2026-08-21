/**
 * Tour Republish Handler
 * Ripublikon një tur të përfunduar për një datë të re.
 * Nga realizimi i mëparshëm ruhen vetëm vlerësimet (reviews).
 */

function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split('; ') : [];
    for (const cookie of cookies) {
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.slice(name.length + 1));
        }
    }
    return null;
}

class TourRepublishHandler {
    constructor() {
        this.modal = document.getElementById('republish-modal');
        this.form = document.getElementById('republish-form');
        this.dateInput = document.getElementById('republish-new-date');
        this.timeInput = document.getElementById('republish-new-time');
        this.titleEl = document.getElementById('republish-tour-title');
        this.errorEl = document.getElementById('republish-error');
        this.submitBtn = document.getElementById('republish-submit');
        this.endpoint = this.modal ? this.modal.dataset.endpoint : '/tours/api/republish/';
        this.activeTourId = null;

        this.init();
    }

    init() {
        if (!this.modal || !this.form) return;

        document.querySelectorAll('[data-republish-tour]').forEach((btn) => {
            btn.addEventListener('click', () => this.open(btn));
        });

        this.modal.querySelectorAll('[data-republish-close]').forEach((el) => {
            el.addEventListener('click', () => this.close());
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.hidden) this.close();
        });

        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Data minimale = sot
        this.dateInput.min = new Date().toISOString().split('T')[0];
    }

    open(button) {
        this.activeTourId = button.dataset.republishTour;
        this.titleEl.textContent = button.dataset.tourTitle || '';
        if (button.dataset.currentTime) {
            this.timeInput.value = button.dataset.currentTime;
        } else {
            this.timeInput.value = '';
        }
        this.hideError();
        this.modal.hidden = false;
        document.body.style.overflow = 'hidden';
        this.dateInput.focus();
    }

    close() {
        this.modal.hidden = true;
        document.body.style.overflow = '';
        this.activeTourId = null;
    }

    showError(message) {
        this.errorEl.textContent = message;
        this.errorEl.hidden = false;
    }

    hideError() {
        this.errorEl.hidden = true;
        this.errorEl.textContent = '';
    }

    async handleSubmit(event) {
        event.preventDefault();
        if (!this.activeTourId) return;

        const newDate = this.dateInput.value;
        if (!newDate) {
            this.showError('Zgjidh një datë të re.');
            return;
        }

        this.submitBtn.disabled = true;
        this.hideError();

        try {
            const response = await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    tour_id: Number(this.activeTourId),
                    new_date: newDate,
                    time_start: this.timeInput.value || null
                })
            });

            const payload = await response.json();

            if (response.ok && payload.success) {
                window.location.reload();
                return;
            }
            this.showError(payload.error || 'Ripublikimi dështoi. Provo përsëri.');
        } catch (err) {
            this.showError('Gabim rrjeti. Provo përsëri.');
        } finally {
            this.submitBtn.disabled = false;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TourRepublishHandler();
});
