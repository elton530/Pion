from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from core.utils import send_notification_email

from .models import Booking, Payment, BookingReview

logger = logging.getLogger(__name__)


# ==================== BOOKING SIGNALS ====================

@receiver(post_save, sender=Booking)
def on_booking_create(sender, instance, created, **kwargs):
    """Veprimet kur krijohet prenotim"""
    try:
        if created:
            logger.info(f"Prenotim i ri u krijua: {instance.id} - {instance.tour.title}")
            # Update tour booking count
            instance.tour.booking_count = instance.tour.bookings.filter(
                status__in=['confirmed', 'completed']
            ).count()
            instance.tour.save(update_fields=['booking_count'])
    except Exception as e:
        logger.error(f"Gabim në on_booking_create: {e}")


@receiver(post_save, sender=Booking)
def update_guide_statistics_on_booking(sender, instance, created, **kwargs):
    """Përditëso statistikat e guide-it"""
    try:
        guide = instance.tour.guide
        
        if hasattr(guide, 'update_statistics'):
            guide.update_statistics()
        
        if hasattr(guide, 'update_earnings'):
            guide.update_earnings()
        
        logger.debug(f"Statistika të guide-it u përditësuan: {guide.user.username}")
    except Exception as e:
        logger.error(f"Gabim në update_guide_statistics_on_booking: {e}")


@receiver(post_save, sender=Booking)
def update_tourist_statistics_on_booking(sender, instance, created, **kwargs):
    """Përditëso statistikat e turistit"""
    try:
        tourist = instance.tourist
        
        if hasattr(tourist, 'update_statistics'):
            tourist.update_statistics()
        
        logger.debug(f"Statistika të turistit u përditësuan: {tourist.user.username}")
    except Exception as e:
        logger.error(f"Gabim në update_tourist_statistics_on_booking: {e}")


@receiver(pre_save, sender=Booking)
def track_status_change(sender, instance, **kwargs):
    """Ndjek ndryshimin e statusit"""
    if instance.pk:
        try:
            old_instance = Booking.objects.get(pk=instance.pk)
            
            # Cache old status for post_save handlers
            instance._old_status = old_instance.status

            # Nëse statusi ndryshon në "confirmed"
            if old_instance.status != instance.status and instance.status == "confirmed":
                instance.confirmed_at = timezone.now()
                logger.info(f"Prenotim u konfirmua: {instance.id}")
            
            # Nëse statusi ndryshon në "completed"
            elif old_instance.status != instance.status and instance.status == "completed":
                logger.info(f"Prenotim u përfundua: {instance.id}")
            
            # Nëse statusi ndryshon në "cancelled"
            elif old_instance.status != instance.status and instance.status == "cancelled":
                logger.info(f"Prenotim u anullua: {instance.id}")
        
        except Booking.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Gabim në track_status_change: {e}")


@receiver(post_save, sender=Booking)
def apply_status_transition_effects(sender, instance, created, **kwargs):
    """Apply side-effects for status transitions: adjust available_spots and booking_count."""
    try:
        old_status = getattr(instance, '_old_status', None)
        new_status = instance.status

        # If status transitioned to cancelled from a non-cancelled state, return seats
        if old_status != 'cancelled' and new_status == 'cancelled':
            instance.tour.available_spots += instance.num_people
            instance.tour.save(update_fields=['available_spots', 'updated_at'])
            logger.info(f"Vendet u kthyen pas anulimit: {instance.num_people} për turin {instance.tour.title}")

        # If status transitioned from cancelled to active (confirmed/pending), deduct seats
        if old_status == 'cancelled' and new_status != 'cancelled':
            # Ensure not to go negative
            instance.tour.available_spots = max(0, instance.tour.available_spots - instance.num_people)
            instance.tour.save(update_fields=['available_spots', 'updated_at'])
            logger.info(f"Vendet u rimbajtën pas rikthimit të prenotimit: {instance.num_people} për turin {instance.tour.title}")

        # Always refresh booking_count to reflect confirmed/completed
        instance.tour.booking_count = instance.tour.bookings.filter(
            status__in=['confirmed', 'completed']
        ).count()
        instance.tour.save(update_fields=['booking_count'])
    except Exception as e:
        logger.error(f"Gabim në apply_status_transition_effects: {e}")


@receiver(post_delete, sender=Booking)
def restore_tour_spots_on_booking_delete(sender, instance, **kwargs):
    """Kthe vendet kur fshihet prenotim"""
    try:
        if instance.status != "cancelled":
            instance.tour.available_spots += instance.num_people
            instance.tour.save(update_fields=['available_spots'])
            logger.info(f"Vendet u kthyen: {instance.num_people} për turin {instance.tour.title}")
    except Exception as e:
        logger.error(f"Gabim në restore_tour_spots_on_booking_delete: {e}")


# ==================== PAYMENT SIGNALS ====================

@receiver(post_save, sender=Payment)
def on_payment_confirmation(sender, instance, created, **kwargs):
    """Veprimet kur pagesa konfirmohet"""
    try:
        if instance.status == "paid":
            # Konfirmo prenotimin automatikisht
            booking = instance.booking
            if booking.status == "pending":
                booking.confirm()
                logger.info(f"Prenotim u konfirmua automatikisht: {booking.id}")
            
            # Dërgoni email confirmimi
            send_payment_confirmation_email(instance)
    
    except Exception as e:
        logger.error(f"Gabim në on_payment_confirmation: {e}")


@receiver(post_save, sender=Payment)
def notify_on_payment_failure(sender, instance, **kwargs):
    """Njoftim kur pagesa dështon"""
    try:
        if instance.status == "failed":
            send_payment_failed_email(instance)
            logger.warning(f"Pagesa dështoi: {instance.id}")
    except Exception as e:
        logger.error(f"Gabim në notify_on_payment_failure: {e}")


# ==================== REVIEW SIGNALS ====================

@receiver(post_save, sender=BookingReview)
def update_tour_rating_on_review(sender, instance, created, **kwargs):
    """Përditëso vlerësimin e turit kur shtohet review"""
    try:
        from tours.models import TourReview
        
        tour = instance.booking.tour
        if hasattr(tour, 'update_rating'):
            # Merr vlerësimet e aprovuara
            reviews = TourReview.objects.filter(
                tour=tour,
                is_approved=True
            )
            
            if reviews.exists():
                from django.db.models import Avg, Count
                stats = reviews.aggregate(avg=Avg('rating'), cnt=Count('id'))
                tour.average_rating = stats['avg'] or 0
                tour.reviews_count = stats['cnt'] or 0
                tour.save(update_fields=['average_rating', 'reviews_count'])
                logger.debug(f"Rating të turit u përditësuv: {tour.title}")
    except Exception as e:
        logger.error(f"Gabim në update_tour_rating_on_review: {e}")


@receiver(post_save, sender=BookingReview)
def update_guide_rating_on_review(sender, instance, created, **kwargs):
    """Përditëso vlerësimin e guide-it"""
    try:
        guide = instance.booking.tour.guide
        if hasattr(guide, 'update_rating'):
            guide.update_rating()
            logger.debug(f"Rating të guide-it u përditësua: {guide.user.username}")
    except Exception as e:
        logger.error(f"Gabim në update_guide_rating_on_review: {e}")


# ==================== EMAIL HELPERS ====================

def send_payment_confirmation_email(payment):
    """Dërgoni email confirmimi pagese"""
    try:
        booking = payment.booking
        tourist_email = booking.tourist.user.email

        if tourist_email:
            subject = f"✅ Pagesa u konfirmua për '{booking.tour.title}'"
            context = {
                'tourist_name': booking.tourist.user.get_full_name() or booking.tourist.user.username,
                'tour_title': booking.tour.title,
                'tour_date': booking.tour.date,
                'amount': payment.amount,
                'currency': payment.currency,
            }
            message = f"Pagesa u konfirmua. Prenotim i përfunduar për {booking.tour.title}."
            send_notification_email(tourist_email, subject, message=message, context=context)
    except Exception as e:
        logger.error(f"Gabim në send_payment_confirmation_email: {e}")


def send_payment_failed_email(payment):
    """Dërgoni email kur pagesa dështon"""
    try:
        booking = payment.booking
        tourist_email = booking.tourist.user.email

        if tourist_email:
            subject = f"❌ Pagesa dështoi për '{booking.tour.title}'"
            message = "Pagesa dështoi. Provo të ri ose kontakto ne."
            send_notification_email(tourist_email, subject, message=message)
    except Exception as e:
        logger.error(f"Gabim në send_payment_failed_email: {e}")