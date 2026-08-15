from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BookingsConfig(AppConfig):
    """Konfigurimi i aplikacionit Bookings - Menaxhimi i prenotimeve"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'
    verbose_name = _('Prenotimet')
    
    def ready(self):
        """Inicializim kur aplikacioni është i gatshëm"""
        import bookings.signals  # noqa