"""
Funksione ndihmëse të përbashkëta për platformën.
"""

import logging

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def file_exists(field):
    """Kontrollo nëse skedari i një FileField ekziston realisht në storage."""
    try:
        return bool(field and default_storage.exists(field.name))
    except Exception:
        return False


def send_notification_email(email, subject, message=None, template_name=None, context=None):
    """Dërgo email.

    Kur EMAIL_BACKEND është console, vetëm log-o në vend që të dërgohet —
    kjo mban log-ët e zhvillimit të pastër dhe parandalon dërgime aksidentale
    derisa të konfigurohet një backend i vërtetë.
    """
    try:
        backend = getattr(settings, 'EMAIL_BACKEND', '') or ''
        if 'console' in backend:
            logger.info("EMAIL (console) -> to=%s subject=%s context=%s", email, subject, context)
            return True

        html_message = None
        if template_name and context is not None:
            html_message = render_to_string(template_name, context)

        recipient_list = email if isinstance(email, (list, tuple)) else [email]

        send_mail(
            subject=subject,
            message=message or html_message or '',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Email sent to: %s subject=%s", recipient_list, subject)
        return True
    except Exception as e:
        logger.error(f"Gabim gjatë dërgimit të email-it: {e}")
        return False
