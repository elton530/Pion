from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
import logging

from .models import ContactMessage, NewsletterSubscription, FAQ
from core.utils import send_notification_email

logger = logging.getLogger(__name__)


# ==================== CONTACT MESSAGE SIGNALS ====================

@receiver(post_save, sender=ContactMessage)
def on_contact_message_create(sender, instance, created, **kwargs):
    """Veprimet kur krijohet mesazh kontakti"""
    try:
        if created:
            logger.info(f"Mesazh i ri kontakti: {instance.email} - {instance.subject}")
            
            # Dërgoni email confirmimi te përdoruesi
            send_contact_confirmation_email(instance)
    
    except Exception as e:
        logger.error(f"Gabim në on_contact_message_create: {e}")


@receiver(post_save, sender=ContactMessage)
def notify_admin_on_new_contact(sender, instance, created, **kwargs):
    """Njoftim te admin kur ka mesazh të ri"""
    if not created:
        return

    admin_emails = [admin[1] for admin in settings.ADMINS]

    if admin_emails:
        subject = f"📬 Mesazh i ri kontakti: {instance.subject}"
        message = f"Mesazh i ri nga {instance.name}: {instance.subject}"

        send_notification_email(admin_emails, subject, message=message)
        logger.info(f"Email notifikimi u dërgua te admin për: {instance.email}")


# ==================== NEWSLETTER SIGNALS ====================

@receiver(post_save, sender=NewsletterSubscription)
def on_newsletter_subscribe(sender, instance, created, **kwargs):
    """Veprimet kur nënshkrohet në newsletter"""
    try:
        if created:
            logger.info(f"Nënshkrim i ri newsletter: {instance.email}")
            
            # Dërgoni email welcome
            send_newsletter_welcome_email(instance)
    
    except Exception as e:
        logger.error(f"Gabim në on_newsletter_subscribe: {e}")


@receiver(post_save, sender=NewsletterSubscription)
def on_newsletter_unsubscribe(sender, instance, **kwargs):
    """Veprimet kur anullohet nënshkrimi"""
    try:
        if not instance.is_active and instance.unsubscribed_at:
            logger.info(f"Anulim nënshkrimi: {instance.email}")
            
            # Dërgoni email confirmimi anulimi
            send_newsletter_unsubscribe_confirmation(instance)
    
    except Exception as e:
        logger.error(f"Gabim në on_newsletter_unsubscribe: {e}")


# ==================== FAQ SIGNALS ====================

@receiver(post_save, sender=FAQ)
def on_faq_create(sender, instance, created, **kwargs):
    """Veprimet kur krijohet FAQ"""
    try:
        if created:
            logger.info(f"FAQ e re u krijua: {instance.question[:50]}...")
    
    except Exception as e:
        logger.error(f"Gabim në on_faq_create: {e}")


@receiver(pre_save, sender=FAQ)
def on_faq_status_change(sender, instance, **kwargs):
    """Ndjek ndryshimin e statusit të FAQ (pre-save, se DB ka ende vlerën e vjetër)"""
    if not instance.pk:
        return
    try:
        old_is_active = FAQ.objects.filter(pk=instance.pk).values_list('is_active', flat=True).first()
        if old_is_active is None:
            return

        # Nëse FAQ u aktivizua
        if not old_is_active and instance.is_active:
            logger.info(f"FAQ u aktivizua: {instance.question[:50]}...")

        # Nëse FAQ u deaktivizua
        elif old_is_active and not instance.is_active:
            logger.info(f"FAQ u deaktivizua: {instance.question[:50]}...")

    except FAQ.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Gabim në on_faq_status_change: {e}")


# ==================== EMAIL HELPER FUNCTIONS ====================

def send_contact_confirmation_email(contact_msg):
    """Dërgoni email confirmimi te përdoruesi"""
    subject = f"✅ Mesazhi juaj u pranua - {contact_msg.subject}"
    message = "Faleminderit për kontaktin! Do t'ju përgjigjen në brëndësi të 24 orëve."
    send_notification_email(contact_msg.email, subject, message=message)
    logger.info(f"Confirmation email i dërgua: {contact_msg.email}")


def send_newsletter_welcome_email(subscription):
    """Dërgoni email welcome te nënshkruesit e ri"""
    subject = "✅ Mirë se erdhët në newsletter-in tonë!"
    message = "Faleminderit për nënshkrimin! Pritet të marr lajme të reja nga ne."
    send_notification_email(subscription.email, subject, message=message)
    logger.info(f"Welcome email i dërgua: {subscription.email}")


def send_newsletter_unsubscribe_confirmation(subscription):
    """Dërgoni email confirmimi anulimi"""
    subject = "❌ Nënshkrimi u anullua"
    message = "Nënshkrimi juaj u anullua me sukses. Nuk do t'ju dërgojmë më email-a."
    send_notification_email(subscription.email, subject, message=message)
    logger.info(f"Unsubscribe confirmation email i dërgua: {subscription.email}")


def notify_admin_bulk_newsletter(count, subject):
    """Njoftim te admin kur dërgohet bulk newsletter"""
    admin_emails = [admin[1] for admin in settings.ADMINS]

    if admin_emails:
        subject_line = f"📬 Bulk newsletter u dërgua - {subject}"
        message = f"Bulk newsletter u dërgua me sukses te {count} nënshkruesit."
        send_notification_email(admin_emails, subject_line, message=message)
        logger.info(f"Admin notification: Bulk newsletter u dërgua te {count} adresa")


# ==================== UTILITY FUNCTIONS ====================

def send_bulk_newsletter(subject, message, recipients=None):
    """Dërgim bulk newsletter"""
    try:
        if recipients is None:
            # Merr të gjithë nënshkruesit aktivë
            recipients = NewsletterSubscription.objects.filter(
                is_active=True
            ).values_list('email', flat=True)

        count = 0

        for email in recipients:
            if send_notification_email(email, subject, message=message):
                count += 1

        logger.info(f"Bulk newsletter u dërgua te {count} adresa")

        # Njoftim te admin
        notify_admin_bulk_newsletter(count, subject)

        return count

    except Exception as e:
        logger.error(f"Gabim në send_bulk_newsletter: {e}")
        return 0