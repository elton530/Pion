/**
 * Footer JavaScript - Newsletter Form
 */

document.addEventListener('DOMContentLoaded', function () {
    
    // ==================== NEWSLETTER FORM ====================
    
    const newsletterForm = document.getElementById('footerNewsletterForm');
    
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function (e) {
            e.preventDefault();
            
            const emailInput = this.querySelector('input[type="email"]');
            const button = this.querySelector('button');
            const originalHTML = button.innerHTML;
            
            if (!emailInput.value) return;

            // Show loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;

            // Simulate API call (replace with actual API endpoint)
            setTimeout(() => {
                // Success state
                button.innerHTML = '<i class="fas fa-check"></i>';
                button.style.background = '#10b981';
                
                // Show success message
                alert('Faleminderit! U regjistruat me sukses në newsletter.');
                
                // Reset form
                this.reset();
                
                // Reset button after 2 seconds
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.disabled = false;
                    button.style.background = '';
                }, 2000);
            }, 1500);
        });
    }
});