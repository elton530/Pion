from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    """Konfigurimi i aplikacionit Core - Funksionaliteti i përgjithshëm"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = _('Baza e Platformës')
    
    def ready(self):
        """Inicializim kur aplikacioni është i gatshëm"""
        import core.signals  # noqa