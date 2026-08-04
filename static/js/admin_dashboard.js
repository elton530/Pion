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

    document.querySelectorAll('.admin-dashboard .btn-action').forEach((button) => {
        button.addEventListener('click', function (event) {
            const action = button.classList.contains('approve') ? 'mirato' : 'refuzo';
            const confirmed = window.confirm('A je i sigurt që dëshiron ta ' + action + ' këtë guide?');
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
});
