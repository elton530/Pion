from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import re
import uuid

from tours.models import Tour
from users.models import TouristProfile


def _to_decimal(value, field_name=None):
    """Konverto në mënyrë të sigurt vlerën në Decimal.

    Nëse konvertimi dështon, ngre ValueError me emrin e fushës për lehtësi debugging.
    """
    if isinstance(value, Decimal):
        return value
    if value is None:
        fname = field_name or 'value'
        raise ValueError(f"{fname} is None; expected a numeric value.")

    s = str(value).strip()
    # Fast path
    try:
        return Decimal(s)
    except InvalidOperation:
        # Try removing spaces and thousands separators
        cleaned = s.replace(' ', '')
        # Extract first numeric-looking substring (handles currency symbols)
        m = re.search(r'[-+]?[0-9]+(?:[\.,][0-9]+)?', cleaned)
        if m:
            num = m.group(0).replace(',', '.')
            try:
                return Decimal(num)
            except InvalidOperation:
                pass
        fname = field_name or 'value'
        raise ValueError(f"{fname} could not be converted to Decimal: {value!r}")


# ==================== CHOICES ====================

BOOKING_STATUS = [
    ("pending", "Në pritje"),
    ("confirmed", "Konfirmuar"),
    ("completed", "Përfunduar"),
    ("cancelled", "Anulluar"),
    ("no_show", "Nuk u paraqit"),
]

ALLOWED_STATUS_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled"},
    "cancelled": set(),
    "completed": set(),
    # Legacy status kept for compatibility with existing records, but no new transitions should target it.
    "no_show": set(),
}

PAYMENT_STATUS = [
    ("pending", "Në pritje"),
    ("paid", "Paguar"),
    ("failed", "Dështoi"),
    ("refunded", "Kthyer"),
]

PAYMENT_METHOD = [
    ("card", "Kartë krediti"),
    ("paypal", "PayPal"),
    ("bank_transfer", "Transferim bankare"),
    ("cash", "Në vend"),
]

CANCELLATION_REASON = [
    ("personal", "Arsyje personale"),
    ("health", "Probleme shëndetësore"),
    ("weather", "Kushte të këqija motit"),
    ("guide_cancelled", "Guide-i anuloi"),
    ("other", "Tjetër"),
]


# ==================== BOOKING MODEL ====================

class Booking(models.Model):
    """Model për rezervimet e tureve"""
    
    # ===== BASIC INFORMATION =====
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tourist = models.ForeignKey(
        TouristProfile,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    
    # ===== PARTICIPANTS =====
    num_people = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Numri i personave (përfshirë veten)"
    )
    
    participants_info = models.TextField(
        blank=True,
        help_text="Emrat dhe informacioni i pjesëmarrësve (JSON ose tekst)"
    )
    
    # ===== PRICING =====
    price_per_person = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Çmimi për person në kohën e prenotimit"
    )
    
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Total çmim = price_per_person * num_people"
    )
    
    discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Zbritja e aplikuar (nëse ka)"
    )
    
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Çmimi final = total_price - discount_applied"
    )
    
    # ===== STATUS & WORKFLOW =====
    status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS,
        default="pending",
        help_text="Statusi i prenotimit"
    )
    
    is_confirmed_24h = models.BooleanField(
        default=False,
        help_text="Turist konfirmoi pjesëmarrjen 24h përpara"
    )
    
    confirmed_24h_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Kur konfirmoi pjesëmarrjen"
    )
    
    # ===== COMMUNICATION =====
    notes = models.TextField(
        blank=True,
        help_text="Kërkesa speciale, pyetje, notat e turistit"
    )
    
    special_requirements = models.TextField(
        blank=True,
        help_text="Kërkesa speciale (ushqim, mobilitet, etj.)"
    )
    
    guide_notes = models.TextField(
        blank=True,
        help_text="Shënime nga guide-i"
    )
    
    # ===== CANCELLATION =====
    cancellation_reason = models.CharField(
        max_length=20,
        choices=CANCELLATION_REASON,
        blank=True,
        help_text="Arsyeja e anulimit"
    )
    
    cancellation_notes = models.TextField(
        blank=True,
        help_text="Detaje shtesë për anulim"
    )
    
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Kur u anulua"
    )
    
    cancelled_by = models.CharField(
        max_length=20,
        choices=[("tourist", "Turist"), ("guide", "Guide"), ("admin", "Admin")],
        blank=True,
        help_text="Kush anuloi"
    )
    
    # ===== SYSTEM FIELDS =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Kur guide-i konfirmoi"
    )
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['tourist', 'status']),
            models.Index(fields=['tour', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['tourist', 'tour']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(num_people__gte=1),
                name='booking_num_people_positive',
            ),
            models.UniqueConstraint(
                fields=['tourist', 'tour'],
                condition=~models.Q(status='cancelled'),
                name='unique_active_booking_per_tourist_tour',
            ),
        ]
        verbose_name = "Prenotim"
        verbose_name_plural = "Prenotimet"
    
    def __str__(self):
        tourist_name = self.tourist.user.get_full_name() or self.tourist.user.username
        return f"{tourist_name} - {self.tour.title} ({self.num_people} persona)"

    def _validate_status_transition(self, old_status, new_status):
        """Validate lifecycle transition for booking status updates."""
        if old_status == new_status:
            return

        allowed_targets = ALLOWED_STATUS_TRANSITIONS.get(old_status, set())
        if new_status not in allowed_targets:
            raise ValueError(
                f"Kalim statusi i pavlefshëm: {old_status} -> {new_status}."
            )
    
    def save(self, *args, **kwargs):
        """Llogarit çmimet dhe menaxhon vendet"""
        created = getattr(self, '_state', None) and getattr(self._state, 'adding', False)

        if created:
            with transaction.atomic():
                original_tour = self.tour
                tour = Tour.objects.select_for_update().get(pk=self.tour_id)
                self.tour = tour

                if tour.available_spots < self.num_people:
                    raise ValueError(
                        f"Nuk ka vende të mjaftueshme. Vende të lira: {tour.available_spots}"
                    )

                self.price_per_person = tour.current_price

                if self.price_per_person is None:
                    raise ValueError(
                        "Turi nuk ka një çmim të vendosur. Ju lutem kontrolloni konfigurimin e turit."
                    )

                self.total_price = _to_decimal(self.price_per_person, 'price_per_person') * _to_decimal(self.num_people, 'num_people')
                self.discount_applied = Decimal('0.00')
                self.final_price = self.total_price

                tour.available_spots -= self.num_people

                if original_tour is not None and original_tour.pk == tour.pk:
                    original_tour.available_spots = tour.available_spots

                self.tour = original_tour or tour
                tour.save(update_fields=['available_spots', 'updated_at'])

                super().save(*args, **kwargs)

                Payment.objects.get_or_create(
                    booking=self,
                    defaults={
                        'amount': self.final_price,
                        'currency': tour.currency,
                        'payment_method': 'card',
                        'status': 'pending',
                    }
                )
                return

        if self.pk:
            old_status = Booking.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            if old_status is not None:
                self._validate_status_transition(old_status, self.status)

        self.total_price = _to_decimal(self.price_per_person, 'price_per_person') * _to_decimal(self.num_people, 'num_people')
        self.final_price = self.total_price - _to_decimal(self.discount_applied, 'discount_applied')

        super().save(*args, **kwargs)
    
    def cancel(self, reason=None, cancelled_by="tourist", notes=""):
        """Anulo prenotimin dhe kthej vendet"""
        
        if self.status in ["cancelled", "completed", "no_show"]:
            if self.status == "cancelled":
                raise ValueError("Ky prenotim është tashmë anuluar.")
            if self.status == "completed":
                raise ValueError("Nuk mund të anulohet një tur i përfunduar.")
            raise ValueError("Nuk mund të anulohet një prenotim që është shënuar si nuk u paraqit.")
        
        # Përditëso prenotimin
        self.status = "cancelled"
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by
        
        if reason:
            self.cancellation_reason = reason
        
        if notes:
            self.cancellation_notes = notes
        
        self.save(update_fields=[
            'status', 'cancelled_at', 'cancelled_by',
            'cancellation_reason', 'cancellation_notes'
        ])
    
    def confirm(self):
        """Konfirmim i prenotimit nga guide-i"""
        if self.status != "pending":
            raise ValueError(f"Nuk mund të konfirmosh prenotimin me status {self.status}")
        
        self.status = "confirmed"
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at'])
    
    def complete(self):
        """Marko turin si të përfunduar"""
        if self.status != "confirmed":
            raise ValueError(f"Nuk mund të përfundosh prenotimin me status {self.status}")

        self.status = "completed"
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_no_show(self):
        """Marko si nuk u paraqit"""
        raise ValueError("Statusi 'no_show' nuk përdoret në lifecycle-in aktual të prenotimeve.")
    
    def confirm_participation_24h(self):
        """Konfirmim i pjesëmarrjes 24h përpara"""
        if not self.is_24h_before_tour():
            raise ValueError(
                "Mund të konfirmosh vetëm 24 orë përpara fillimit të turit."
            )
        
        self.is_confirmed_24h = True
        self.confirmed_24h_at = timezone.now()
        self.save(update_fields=['is_confirmed_24h', 'confirmed_24h_at'])
    
    def is_24h_before_tour(self):
        """Kontrollo nëse turi fillon brenda 24 orësh"""
        tour_datetime = timezone.make_aware(
            timezone.datetime.combine(self.tour.date, self.tour.time_start)
        )
        
        now = timezone.now()
        hours_until = (tour_datetime - now).total_seconds() / 3600
        
        return 0 <= hours_until <= 24
    
    @property
    def can_be_cancelled(self):
        """Kontrollo nëse mund të anulohet"""
        if self.status in ["cancelled", "completed", "no_show"]:
            return False
        
        tour_datetime = timezone.make_aware(
            timezone.datetime.combine(self.tour.date, self.tour.time_start)
        )
        
        # Duhet të jetë ndonjë orë përpara turit
        hours_until = (tour_datetime - timezone.now()).total_seconds() / 3600
        return hours_until > self.tour.cancellation_deadline_hours
    
    @property
    def refund_amount(self):
        """Llogarit shumën e rimburses"""
        if not self.can_be_cancelled:
            return Decimal('0.00')
        
        refund_percentage = Decimal(str(self.tour.refund_percentage)) / Decimal('100')
        return self.final_price * refund_percentage
    
    @property
    def days_until_tour(self):
        """Ditët deri në tur"""
        tour_datetime = timezone.make_aware(
            timezone.datetime.combine(self.tour.date, self.tour.time_start)
        )
        return (tour_datetime - timezone.now()).days


# ==================== PAYMENT MODEL ====================

class Payment(models.Model):
    """Model për pagesa"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Shuma e paguar"
    )
    
    currency = models.CharField(
        max_length=3,
        default="ALL",
        help_text="Valuta"
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD,
        default="card"
    )
    
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending"
    )
    
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID i transaksionit nga provider"
    )
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pagesa"
        verbose_name_plural = "Pagesat"
    
    def __str__(self):
        return f"Payment {self.id} - {self.booking} - {self.status}"
    
    def mark_as_paid(self, transaction_id=None):
        """Marko si paguar"""
        self.status = "paid"
        self.paid_at = timezone.now()
        
        if transaction_id:
            self.transaction_id = transaction_id
        
        self.save(update_fields=['status', 'paid_at', 'transaction_id'])
        
        # Konfirmo prenotimin automatikisht
        if self.booking.status == "pending":
            self.booking.confirm()
    
    def mark_as_failed(self):
        """Marko si dështoi"""
        self.status = "failed"
        self.save(update_fields=['status'])
    
    def refund(self):
        """Kthe paratë"""
        self.status = "refunded"
        self.save(update_fields=['status'])


# ==================== REVIEW MODEL ====================

class BookingReview(models.Model):
    """Vlerësim i prenotimit/tur-it"""
    
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="booking_review"
    )
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Vlerësim Prenotimi"
        verbose_name_plural = "Vlerësimet e Prenotimeve"
    
    def __str__(self):
        return f"Review për {self.booking}"