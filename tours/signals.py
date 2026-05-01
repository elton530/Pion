from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Tour, TourReview, TourStatistic, TourImage, TourSchedule

logger = logging.getLogger(__name__)


# ==================== TOUR SIGNALS ====================

@receiver(post_save, sender=Tour)
def create_tour_statistics(sender, instance, created, **kwargs):
    """Krijoni statistika automatikisht kur krijohet tur i ri"""
    if created:
        try:
            TourStatistic.objects.get_or_create(tour=instance)
            logger.info(f"Statistika u krijon për turin: {instance.title}")
        except Exception as e:
            logger.error(f"Gabim gjatë krijimit të statistikave: {e}")


@receiver(pre_save, sender=Tour)
def update_tour_timestamps(sender, instance, **kwargs):
    """Përditëso timestamp-in e modified-it automatikisht"""
    if instance.pk:
        try:
            old = Tour.objects.filter(pk=instance.pk).values('available_spots', 'booking_count').first()

            # Kontrollo nëse ka ndryshime në booking-related fields
            if old and (
                old.get('available_spots') != instance.available_spots or
                old.get('booking_count') != instance.booking_count
            ):
                instance.last_booking_at = timezone.now()
                logger.info(f"Last booking time u përditëso për: {instance.title}")
        except Tour.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Gabim gjatë përditësimit të timestamp-it: {e}")


@receiver(post_save, sender=Tour)
def update_guide_statistics(sender, instance, created, **kwargs):
    """Përditëso statistikat e guide-it kur ndryshon tur"""
    try:
        # Call guide update helpers if implemented on profile
        try:
            instance.guide.update_rating()
        except Exception:
            logger.debug("Guide does not implement update_rating or it failed")
        try:
            instance.guide.update_tour_count()
        except Exception:
            logger.debug("Guide does not implement update_tour_count or it failed")
        logger.info(f"Statistika të guide-it u përditësuan për: {instance.guide.user.username}")
    except Exception as e:
        logger.error(f"Gabim gjatë përditësimit të statistikave të guide-it: {e}")


@receiver(post_save, sender=Tour)
def notify_admin_on_new_tour(sender, instance, created, **kwargs):
    """Dërgoni notifikimin te admin kur krijohet tur i ri"""
    if created and instance.status == 'published':
        try:
            admin_emails = [admin[1] for admin in settings.ADMINS]
            if admin_emails:
                context = {
                    'tour_title': instance.title,
                    'guide_name': instance.guide.user.get_full_name(),
                    'date': instance.date,
                    'location': f"{instance.location_city}, {instance.location_region}",
                }
                # Këtu mund të përdorësh template për email
                subject = f"Tur i ri u publikua: {instance.title}"
                message = f"Tur i ri u publikua nga {context['guide_name']}: {instance.title} në {context['location']}"
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, admin_emails)
                logger.info(f"Notifikimi i admin-it për turin: {instance.title}")
        except Exception as e:
            logger.error(f"Gabim gjatë dërgimit të notifikimit të admin-it: {e}")


# ==================== REVIEW SIGNALS ====================

@receiver(post_save, sender=TourReview)
def update_tour_rating_on_review_save(sender, instance, created, **kwargs):
    """Përditëso vlerësimin e turit kur shtohet ose edituhet review"""
    try:
        if instance.is_approved:
            instance.update_tour_ratings()
            logger.info(f"Rating të turit u përditësuan për: {instance.tour.title}")
    except Exception as e:
        logger.error(f"Gabim gjatë përditësimit të rating-ut: {e}")


@receiver(post_delete, sender=TourReview)
def update_tour_rating_on_review_delete(sender, instance, **kwargs):
    """Përditëso vlerësimin e turit kur fshihet review"""
    try:
        # After delete, use the tour reference preserved on the instance
        tour = getattr(instance, 'tour', None)
        if tour:
            # Use the model helper to recalc ratings
            instance.update_tour_ratings(tour)
            logger.info(f"Rating të turit u përditësuan pas fshirjes: {tour.title}")
    except Exception as e:
        logger.error(f"Gabim gjatë përditësimit të rating-ut pas fshirjes: {e}")


@receiver(post_save, sender=TourReview)
def notify_guide_on_new_review(sender, instance, created, **kwargs):
    """Dërgoni notifikimin te guide kur ka review të ri"""
    if created and instance.is_approved:
        try:
            guide_email = instance.tour.guide.user.email
            if guide_email:
                context = {
                    'guide_name': instance.tour.guide.user.get_full_name(),
                    'tourist_name': instance.tourist.user.get_full_name(),
                    'tour_title': instance.tour.title,
                    'rating': instance.rating,
                    'comment': instance.comment[:100],
                }
                subject = f"Review i ri për turin tuaj: {instance.tour.title}"
                message = f"Turist u lë review për turin '{instance.tour.title}' me vlerësim {instance.rating}/5"
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [guide_email])
                logger.info(f"Notifikimi të guide-it për review-in: {instance.tour.title}")
        except Exception as e:
            logger.error(f"Gabim gjatë dërgimit të notifikimit për review-in: {e}")


@receiver(post_save, sender=TourReview)
def notify_tourist_review_approved(sender, instance, created, **kwargs):
    """Dërgoni notifikimin te turist kur review-i i tyre aprovohet.

    Uses a cached pre-save value `_old_is_approved` to detect transition
    from not-approved -> approved.
    """
    old_approved = getattr(instance, '_old_is_approved', None)
    if old_approved is False and instance.is_approved:
        try:
            tourist_email = instance.tourist.user.email
            if tourist_email:
                subject = f"Review-i juaj u aprova për: {instance.tour.title}"
                message = f"Review-i juaj për turin '{instance.tour.title}' u aprova dhe është duke shfaqet në faqen e turit."
                # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [tourist_email])
                logger.info(f"Notifikimi të turistit për aprovim të review-it")
        except Exception as e:
            logger.error(f"Gabim gjatë dërgimit të notifikimit për aprovim: {e}")


@receiver(pre_save, sender=TourReview)
def cache_review_old_approval(sender, instance, **kwargs):
    """Cache previous `is_approved` value so post_save can see the change."""
    if instance.pk:
        try:
            old = TourReview.objects.filter(pk=instance.pk).values('is_approved').first()
            instance._old_is_approved = old.get('is_approved') if old else None
        except Exception:
            instance._old_is_approved = None
    else:
        instance._old_is_approved = None


# ==================== IMAGE SIGNALS ====================

@receiver(post_save, sender=TourImage)
def set_primary_image_automatically(sender, instance, created, **kwargs):
    """Nëse nuk ka foto primäre, vendose këtë si primäre automatikisht"""
    if created and instance.tour:
        try:
            if not instance.tour.images.filter(is_primary=True).exists():
                instance.is_primary = True
                instance.save(update_fields=['is_primary'])
                logger.info(f"Foto u vendos si primäre për turin: {instance.tour.title}")
        except Exception as e:
            logger.error(f"Gabim gjatë vendosjes së fotos primäre: {e}")


@receiver(post_delete, sender=TourImage)
def delete_tour_image_file(sender, instance, **kwargs):
    """Fshi file-in fizikisht kur fshihet image model"""
    try:
        if instance.image:
            storage = instance.image.storage
            storage.delete(instance.image.name)
            logger.info(f"Foto u fshi për turin: {instance.tour.title}")
    except Exception as e:
        logger.error(f"Gabim gjatë fshirjes së fotos: {e}")


@receiver(post_save, sender=TourImage)
def deselect_other_primary_images(sender, instance, **kwargs):
    """Siguro që vetëm një foto të jetë primäre"""
    if instance.is_primary:
        try:
            TourImage.objects.filter(
                tour=instance.tour,
                is_primary=True
            ).exclude(pk=instance.pk).update(is_primary=False)
            logger.info(f"Imazhet e tjera u deselektuan për turin: {instance.tour.title}")
        except Exception as e:
            logger.error(f"Gabim gjatë deselektimit të imazheve: {e}")


# ==================== SCHEDULE SIGNALS ====================

@receiver(post_save, sender=TourSchedule)
def validate_schedule_consistency(sender, instance, **kwargs):
    """Valido konsistencën e programit ditor"""
    try:
        # Kontrollo nëse day_number është unik për këtë tur
        duplicate = TourSchedule.objects.filter(
            tour=instance.tour,
            day_number=instance.day_number
        ).exclude(pk=instance.pk)
        
        if duplicate.exists():
            logger.warning(f"Dita {instance.day_number} ekziston tashmë për turin: {instance.tour.title}")
    except Exception as e:
        logger.error(f"Gabim gjatë validimit të programit: {e}")


# ==================== STATISTIC SIGNALS ====================

@receiver(post_save, sender=TourStatistic)
def log_statistic_changes(sender, instance, created, **kwargs):
    """Log-o ndryshimet e statistikave"""
    try:
        if created:
            logger.info(f"Statistika të reja u krijon për turin: {instance.tour.title}")
        else:
            logger.debug(f"Statistika u përditësuan për turin: {instance.tour.title}")
    except Exception as e:
        logger.error(f"Gabim gjatë logging-ut të statistikave: {e}")


# ==================== UTILITY FUNCTIONS ====================

def send_notification_email(email, subject, template_name=None, context=None):
    """Send email; when EMAIL_BACKEND is console, log instead of sending.

    This keeps development logs clean and prevents accidental real sends
    until a real backend is configured.
    """
    try:
        backend = getattr(settings, 'EMAIL_BACKEND', '') or ''
        if 'console' in backend:
            logger.info("EMAIL (console) -> to=%s subject=%s context=%s", email, subject, context)
            return True

        html_message = None
        if template_name and context is not None:
            html_message = render_to_string(template_name, context)

        send_mail(
            subject=subject,
            message=html_message or '',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Email sent to: %s subject=%s", email, subject)
        return True
    except Exception as e:
        logger.error(f"Gabim gjatë dërgimit të email-it: {e}")
        return False