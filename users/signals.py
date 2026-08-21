from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
import logging

from core.utils import send_notification_email

from .models import GuideProfile, TouristProfile

logger = logging.getLogger(__name__)


# ==================== GUIDE PROFILE SIGNALS ====================

@receiver(post_save, sender=GuideProfile)
def on_guide_profile_save(sender, instance, created, **kwargs):
    """Veprimet kur krijohet ose ndryshohet guide profile"""
    try:
        if created:
            logger.info(f"Guide profile u krijua për: {instance.user.username}")
        else:
            logger.debug(f"Guide profile u përditësua për: {instance.user.username}")
    except Exception as e:
        logger.error(f"Gabim në guide profile signal: {e}")


@receiver(post_save, sender=GuideProfile)
def send_verification_email(sender, instance, created, **kwargs):
    """Dërgoni email kur guide i ri regjistrohet"""
    if created:
        try:
            guide_email = instance.user.email
            if guide_email:
                subject = "Mirëseerdhët në platformën e tureve! 🏔️"
                context = {
                    'guide_name': instance.user.get_full_name() or instance.user.username,
                    'username': instance.user.username,
                }
                message = f"Mirëseerdhët {context['guide_name']}! Plotëso profilin tënd për të filluar të ofrosh ture."
                send_notification_email(guide_email, subject, message=message)
                logger.info(f"Welcome email i dërgua për guide: {instance.user.username}")
        except Exception as e:
            logger.error(f"Gabim në dërgimin e welcome email për guide: {e}")


@receiver(post_save, sender=GuideProfile)
def notify_on_verification_status_change(sender, instance, created, **kwargs):
    """Dërgoni email kur guide-i verifikohet (vetëm në kalimin e statusit)"""
    old_verified = getattr(instance, '_old_is_verified', None)
    if not created and instance.is_verified and old_verified is False:
        try:
            guide_email = instance.user.email
            if guide_email:
                subject = "🎉 Profili juaj u verifikua!"
                message = f"Përshëndetje {instance.user.get_full_name()}! Profili juaj si guide u verifikua. Tani mund të krijoni ture!"
                send_notification_email(guide_email, subject, message=message)
                logger.info(f"Verification email i dërgua për guide: {instance.user.username}")
        except Exception as e:
            logger.error(f"Gabim në dërgimin e verification email: {e}")


@receiver(pre_save, sender=GuideProfile)
def track_verification_status_change(sender, instance, **kwargs):
    """Ndjek ndryshimin e statusit të verifikimit"""
    if instance.pk:
        try:
            old_instance = GuideProfile.objects.get(pk=instance.pk)
            instance._old_is_verified = old_instance.is_verified

            # Nëse statusi ndryshon në "verified"
            if old_instance.status != instance.status and instance.status == "verified":
                instance.is_verified = True
                instance.verified_at = timezone.now()
                logger.info(f"Guide {instance.user.username} u verifikua")
            
            # Nëse statusi ndryshon në "rejected"
            elif old_instance.status != instance.status and instance.status == "rejected":
                instance.is_verified = False
                logger.warning(f"Guide {instance.user.username} u refuzua")
        
        except GuideProfile.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Gabim në track_verification_status_change: {e}")


# ==================== TOURIST PROFILE SIGNALS ====================

@receiver(post_save, sender=TouristProfile)
def on_tourist_profile_save(sender, instance, created, **kwargs):
    """Veprimet kur krijohet ose ndryshohet tourist profile"""
    try:
        if created:
            logger.info(f"Tourist profile u krijua për: {instance.user.username}")
        else:
            logger.debug(f"Tourist profile u përditësua për: {instance.user.username}")
    except Exception as e:
        logger.error(f"Gabim në tourist profile signal: {e}")


@receiver(post_save, sender=TouristProfile)
def send_tourist_welcome_email(sender, instance, created, **kwargs):
    """Dërgoni email kur turist i ri regjistrohet"""
    if created:
        try:
            tourist_email = instance.user.email
            if tourist_email:
                subject = "Mirëseerdhët në aventurën tuaj! 🧗"
                context = {
                    'tourist_name': instance.user.get_full_name() or instance.user.username,
                }
                message = f"Mirëseerdhët {context['tourist_name']}! Filloni të kërkoni turet tuaj të favorizuar."
                send_notification_email(tourist_email, subject, message=message)
                logger.info(f"Welcome email i dërgua për turist: {instance.user.username}")
        except Exception as e:
            logger.error(f"Gabim në dërgimin e welcome email për turist: {e}")


# ==================== USER SIGNALS ====================

@receiver(pre_save, sender=User)
def reset_email_verified_on_email_change(sender, instance, **kwargs):
    """Rivlerëso email_verified kur user ndryshon email-in.

    Pre-save: baza e të dhënave ka ende email-in e vjetër, kështu që
    ndryshimi zbulohet saktë. QuerySet.update() shmang rekursion.
    """
    if instance.pk:
        try:
            old_email = User.objects.filter(pk=instance.pk).values_list('email', flat=True).first()

            # Nëse email u ndryshua
            if old_email != instance.email:
                GuideProfile.objects.filter(user_id=instance.pk).update(email_verified=False)
                TouristProfile.objects.filter(user_id=instance.pk).update(email_verified=False)
                logger.info(f"Email u ndryshua për user: {instance.username}")
        except User.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Gabim në reset_email_verified_on_email_change: {e}")