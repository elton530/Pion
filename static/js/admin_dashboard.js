document.addEventListener('DOMContentLoaded', function () {
    const rows = document.querySelectorAll('.admin-dashboard tbody tr');

    rows.forEach((row) => {
        row.addEventListener('mouseenter', function () {
            row.style.transform = 'translateY(-1px)';
            row.style.transition = 'transform 0.18s ease';
        });

        row.addEventListener('mouseleave', function () {
            row.style.transform = 'translateY(0)';
        });
    });

    // Konfirmim i veprimeve (Mirato/Refuzo/Pezullo/Riaktivizo)
    document.querySelectorAll('.admin-dashboard form[data-confirm]').forEach((form) => {
        form.addEventListener('submit', function (event) {
            const message = form.getAttribute('data-confirm') || 'A je i sigurt që dëshiron ta kryesh këtë veprim?';
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Kërkim live në tabelën e guide-ve të miratuar
    const searchInput = document.getElementById('guideSearch');
    const verifiedTable = document.getElementById('verifiedTable');
    if (searchInput && verifiedTable) {
        const rows = verifiedTable.querySelectorAll('.guide-row');
        const emptyMessage = document.querySelector('.search-empty');

        searchInput.addEventListener('input', function () {
            const query = this.value.trim().toLowerCase();
            let visible = 0;

            rows.forEach((row) => {
                const haystack = (row.getAttribute('data-search') || '').toLowerCase();
                const matches = query === '' || haystack.includes(query);
                row.style.display = matches ? '' : 'none';
                if (matches) visible += 1;
            });

            if (emptyMessage) {
                emptyMessage.hidden = visible !== 0;
            }
        });
    }
});
