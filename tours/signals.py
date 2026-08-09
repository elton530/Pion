from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

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
        logger.info(f"Notifikimi i admin-it për turin: {instance.title}")


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
        logger.info(f"Notifikimi të guide-it për review-in: {instance.tour.title}")


@receiver(post_save, sender=TourReview)
def notify_tourist_review_approved(sender, instance, created, **kwargs):
    """Dërgoni notifikimin te turist kur review-i i tyre aprovohet.

    Uses a cached pre-save value `_old_is_approved` to detect transition
    from not-approved -> approved.
    """
    old_approved = getattr(instance, '_old_is_approved', None)
    if old_approved is False and instance.is_approved:
        logger.info("Notifikimi të turistit për aprovim të review-it")


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