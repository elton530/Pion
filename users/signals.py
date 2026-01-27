from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

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
                # Këtu mund të përdorësh template për email
                # html_message = render_to_string('users/emails/guide_welcome.html', context)
                message = f"Mirëseerdhët {context['guide_name']}! Plotëso profilin tënd për të filluar të ofrosh ture."
                
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [guide_email])
                logger.info(f"Welcome email i dërgua për guide: {instance.user.username}")
        except Exception as e:
            logger.error(f"Gabim në dërgimin e welcome email për guide: {e}")


@receiver(post_save, sender=GuideProfile)
def notify_on_verification_status_change(sender, instance, created, **kwargs):
    """Dërgoni email kur guide-i verifikohet ose refuzohet"""
    if not created and instance.is_verified:
        try:
            guide_email = instance.user.email
            if guide_email:
                subject = "🎉 Profili juaj u verifikua!"
                message = f"Përshëndetje {instance.user.get_full_name()}! Profili juaj si guide u verifikua. Tani mund të krijoni ture!"
                
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [guide_email])
                logger.info(f"Verification email i dërgua për guide: {instance.user.username}")
        except Exception as e:
            logger.error(f"Gabim në dërgimin e verification email: {e}")


@receiver(pre_save, sender=GuideProfile)
def track_verification_status_change(sender, instance, **kwargs):
    """Ndjek ndryshimin e statusit të verifikimit"""
    if instance.pk:
        try:
            old_instance = GuideProfile.objects.get(pk=instance.pk)
            
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
                
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [tourist_email])
                logger.info(f"Welcome email i dërgua për turist: {instance.user.username}")
        except Exception as e:
            logger.error(f"Gabim në dërgimin e welcome email për turist: {e}")


# ==================== USER SIGNALS ====================

@receiver(post_save, sender=User)
def on_user_email_change(sender, instance, created, **kwargs):
    """Veprimet kur user ndryshon email-in"""
    if not created:
        try:
            old_user = User.objects.get(pk=instance.pk)
            
            # Nëse email u ndryshua
            if old_user.email != instance.email:
                # Marko emailin si neverifikuar
                if hasattr(instance, 'guide_profile'):
                    instance.guide_profile.email_verified = False
                    instance.guide_profile.save(update_fields=['email_verified'])
                
                if hasattr(instance, 'tourist_profile'):
                    instance.tourist_profile.email_verified = False
                    instance.tourist_profile.save(update_fields=['email_verified'])
                
                logger.info(f"Email u ndryshua për user: {instance.username}")
        except User.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Gabim në on_user_email_change: {e}")


# ==================== UTILITY FUNCTIONS ====================

def send_notification_email(email, subject, template_name, context):
    """Funksion ndihmës për dërgimin e email-eve"""
    try:
        html_message = render_to_string(template_name, context)
        send_mail(
            subject=subject,
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email u dërgua në: {email}")
        return True
    except Exception as e:
        logger.error(f"Gabim në dërgimin e email-it: {e}")
        return False


def send_bulk_notification(users, subject, template_name, context):
    """Dërgoni bulk emails"""
    emails = [user.email for user in users if user.email]
    
    if not emails:
        logger.warning("Nuk ka email-e për dërgim")
        return False
    
    try:
        for email in emails:
            send_notification_email(email, subject, template_name, context)
        logger.info(f"Bulk email u dërgua në {len(emails)} adresa")
        return True
    except Exception as e:
        logger.error(f"Gabim në dërgimin e bulk email: {e}")
        return False