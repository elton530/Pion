from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ToursConfig(AppConfig):
    """Konfigurimi i aplikacionit Tours - Menaxhimi i Tureve"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tours'
    verbose_name = _('Turet')
    
    def ready(self):
        """Inicializim kur aplikacioni është i gatshëm"""
        # Importo signals kur aplikacioni ndërkohë
        import tours.signals  # noqa