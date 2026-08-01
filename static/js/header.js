/**
 * Header JavaScript - Mobile Menu & User Dropdown
 */

document.addEventListener('DOMContentLoaded', function () {
    
    // ==================== MOBILE MENU ====================
    
    const menuToggle = document.querySelector('.menu-toggle');
    const mobileMenu = document.getElementById('mobileMenu');
    const menuClose = document.querySelector('.menu-close');
    const overlay = document.querySelector('.mobile-menu-overlay');

    // Open mobile menu
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.add('active');
            document.body.style.overflow = 'hidden';
            menuToggle.setAttribute('aria-expanded', 'true');
            menuToggle.classList.add('active');
        });
    }

    // Close mobile menu function
    function closeMobileMenu() {
        if (!mobileMenu) return;
        mobileMenu.classList.remove('active');
        document.body.style.overflow = '';
        if (menuToggle) {
            menuToggle.setAttribute('aria-expanded', 'false');
            menuToggle.classList.remove('active');
        }
    }

    // Close mobile menu on close button click
    if (menuClose) {
        menuClose.addEventListener('click', closeMobileMenu);
    }

    // Close mobile menu on overlay click
    if (overlay) {
        overlay.addEventListener('click', closeMobileMenu);
    }

    // ==================== USER DROPDOWN ====================
    
    const userMenuToggle = document.querySelector('.user-menu-toggle');
    const userDropdown = document.querySelector('.user-dropdown');

    if (userMenuToggle && userDropdown) {
        userMenuToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function (e) {
            if (!userMenuToggle.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }

    // ==================== GLOBAL FLASH MESSAGES ====================

    const flashRows = document.querySelectorAll('.flash-message-row');

    flashRows.forEach((row) => {
        const closeButton = row.querySelector('.flash-message-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                row.style.opacity = '0';
                row.style.transform = 'translateX(12px)';
                row.style.transition = 'opacity .2s ease, transform .2s ease';

                setTimeout(() => {
                    row.remove();
                }, 180);
            });
        }
    });
});