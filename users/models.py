from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count
from django.utils import timezone
from decimal import Decimal

# ==================== CHOICES ====================

TOUR_TYPES = [
    ("nature_walk", "Ecje në Natyrë"),
    ("alpine", "Guide Alpinistike"),
    ("bike_tour", "Tur me Biçikletë"),
    ("rural", "Zona Rurale"),
    ("cultural", "Tur Kulturor"),
    ("adventure", "Aventurë"),
    ("historical", "Tur Historik"),
    ("food", "Tur Kulinarik"),
    ("photography", "Tur Fotografik"),
    ("wellness", "Tur Wellness"),
    ("family", "Tur Familjar"),
    ("other", "Tjetër"),
]

LANGUAGE_CHOICES = [
    ("sq", "Shqip"),
    ("en", "Anglisht"),
    ("it", "Italisht"),
    ("de", "Gjermansht"),
    ("fr", "Frengjishtë"),
    ("es", "Spanjisht"),
]

CERTIFICATION_TYPES = [
    ("alpine_guide", "Alpine Guide"),
    ("hiking_guide", "Hiking Guide"),
    ("first_aid", "First Aid/CPR"),
    ("mountain_rescue", "Mountain Rescue"),
    ("wilderness_first_responder", "Wilderness First Responder"),
    ("mountaineering", "Mountaineering"),
    ("rock_climbing", "Rock Climbing"),
    ("ski_guide", "Ski Guide"),
    ("cycling_guide", "Cycling Guide"),
    ("other", "Tjetër"),
]

EXPERIENCE_LEVELS = [
    ("beginner", "Fillestar (1-2 vjet)"),
    ("intermediate", "Mesatar (2-5 vjet)"),
    ("advanced", "Advanced (5-10 vjet)"),
    ("expert", "Ekspert (10+ vjet)"),
]

GUIDE_STATUS = [
    ("pending", "Pendent"),
    ("verified", "Verifikuar"),
    ("rejected", "Refuzuar"),
    ("suspended", "Pezulluar"),
]


# ==================== GUIDE PROFILE MODEL ====================

class GuideProfile(models.Model):
    """Model për profilin e udhëzuesit"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="guide_profile"
    )
    
    # ===== PERSONAL INFORMATION =====
    photo = models.ImageField(
        upload_to="guides/photos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Foto profilit (rekomanduese 400x400px)"
    )
    bio = models.TextField(
        max_length=1000,
        blank=True,
        help_text="Rreth teje dhe përvojës sate"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Numër kontakti"
    )
    location = models.CharField(
        max_length=100,
        help_text="Qyteti ose zona ku operon"
    )
    
    # ===== PROFESSIONAL INFORMATION =====
    languages = models.CharField(
        max_length=200,
        blank=True,
        help_text="Gjuhët e foluara, të ndara me presje (p.sh. Shqip, Anglisht, Italisht)"
    )
    
    specialty = models.CharField(
        max_length=50,
        choices=TOUR_TYPES,
        default="other",
        help_text="Lloji kryesor i turit"
    )
    
    specialties = models.CharField(
        max_length=500,
        blank=True,
        help_text="Llojet e tureve që ofron (të ndara me presje)"
    )
    
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS,
        default="beginner"
    )
    
    years_experience = models.PositiveIntegerField(
        default=0,
        help_text="Numri i viteve të përvojës"
    )
    
    # ===== CERTIFICATIONS =====
    certifications = models.TextField(
        blank=True,
        help_text="Certifikime, ndihma e parë, etj. (një për rresht)"
    )
    
    certification_document = models.FileField(
        upload_to="guides/certifications/%Y/%m/",
        blank=True,
        null=True,
        help_text="Dokumenti i certifikimit (PDF)"
    )
    
    # ===== GUIDE STATUS & VERIFICATION =====
    status = models.CharField(
        max_length=20,
        choices=GUIDE_STATUS,
        default="pending",
        help_text="Statusi i verifikimit të guide-it"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="A është verifikuar guide-i?"
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data e verifikimit"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="A është aktiv guide-i?"
    )
    
    # ===== RATINGS & STATISTICS =====
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    reviews_count = models.PositiveIntegerField(default=0)
    
    total_tours = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Numri total i tureve të ofruar"
    )
    
    total_tourists = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Numri total i turistëve"
    )
    
    total_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.0,
        editable=False,
        help_text="Fitim total nga turet"
    )
    
    # ===== CONTACT & SOCIAL =====
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    website = models.URLField(
        blank=True,
        help_text="Faqja juaj personale ose blog"
    )
    
    instagram = models.CharField(max_length=100, blank=True)
    facebook = models.CharField(max_length=100, blank=True)
    
    # ===== SYSTEM FIELDS =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['is_active', 'is_verified']),
            models.Index(fields=['status']),
            models.Index(fields=['average_rating', 'reviews_count']),
        ]
        verbose_name = "Profili i Guide-it"
        verbose_name_plural = "Profelet e Guide-ve"
    
    def __str__(self):
        return f"Guide: {self.user.get_full_name() or self.user.username} - {self.location}"
    
    @property
    def full_name(self):
        """Emri i plotë ose username"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def certifications_list(self):
        """Certifikime si listë"""
        if not self.certifications:
            return []
        return [c.strip() for c in self.certifications.split('\n') if c.strip()]
    
    @property
    def specialties_list(self):
        """Specializimet si listë"""
        if not self.specialties:
            return []
        return [s.strip() for s in self.specialties.split(',') if s.strip()]
    
    @property
    def languages_list(self):
        """Gjuhët si listë"""
        if not self.languages:
            return []
        return [l.strip() for l in self.languages.split(',') if l.strip()]
    
    def update_rating(self):
        """Përditëso vlerësimin e guide-it bazuar në reviews"""
        from tours.models import TourReview
        
        reviews = TourReview.objects.filter(
            tour__guide=self,
            is_approved=True
        )
        
        if reviews.exists():
            stats = reviews.aggregate(
                avg=Avg('rating'),
                cnt=Count('id')
            )
            self.average_rating = stats['avg'] or Decimal('0.00')
            self.reviews_count = stats['cnt'] or 0
        else:
            self.average_rating = Decimal('0.00')
            self.reviews_count = 0
        
        self.save(update_fields=['average_rating', 'reviews_count', 'updated_at'])
    
    def update_tour_count(self):
        """Përditëso numrin e tureve"""
        self.total_tours = self.tours.filter(is_active=True).count()
        self.save(update_fields=['total_tours', 'updated_at'])
    
    def update_earnings(self):
        """Përditëso fitimin total"""
        from bookings.models import Booking
        
        bookings = Booking.objects.filter(
            tour__guide=self,
            status='completed'
        )
        
        total = Decimal('0.00')
        for booking in bookings:
            commission_rate = Decimal('0.80')  # 80% për guide, 20% platform
            total += booking.total_price * commission_rate
        
        self.total_earnings = total
        self.save(update_fields=['total_earnings', 'updated_at'])


# ==================== TOURIST PROFILE MODEL ====================

class TouristProfile(models.Model):
    """Model për profilin e turistit"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="tourist_profile"
    )
    
    # ===== PERSONAL INFORMATION =====
    photo = models.ImageField(
        upload_to="tourists/photos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Foto profilit"
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Rreth teje"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Numër kontakti"
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Data e lindjes"
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text="Vendi i origjinës"
    )
    
    # ===== PREFERENCES =====
    preferred_tour_types = models.CharField(
        max_length=500,
        blank=True,
        help_text="Llojet e tureve të preferuar (të ndara me presje)"
    )
    
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS,
        default="beginner",
        help_text="Niveli i përvojës në outdoor activities"
    )
    
    languages = models.CharField(
        max_length=200,
        blank=True,
        help_text="Gjuhët e foluara"
    )
    
    # ===== HEALTH & SAFETY =====
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Emri i kontaktit në rast emergjence"
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Numri i kontaktit në rast emergjence"
    )
    
    health_conditions = models.TextField(
        blank=True,
        help_text="Kushtet shëndetësore të rëndësishme (nëse ka)"
    )
    
    allergies = models.TextField(
        blank=True,
        help_text="Alergji ose ushqimet e ndaluara"
    )
    
    # ===== STATISTICS =====
    total_bookings = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    # ===== PREFERENCES SETTINGS =====
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    newsletter = models.BooleanField(default=False)
    
    # ===== VERIFICATION =====
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # ===== SYSTEM FIELDS =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Profili i Turistit"
        verbose_name_plural = "Profelet e Turistëve"
    
    def __str__(self):
        return f"Tourist: {self.user.get_full_name() or self.user.username}"
    
    @property
    def full_name(self):
        """Emri i plotë"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def age(self):
        """Mosha e turistit"""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def preferred_tour_types_list(self):
        """Llojet e tureve të preferuar si listë"""
        if not self.preferred_tour_types:
            return []
        return [t.strip() for t in self.preferred_tour_types.split(',') if t.strip()]
    
    @property
    def languages_list(self):
        """Gjuhët si listë"""
        if not self.languages:
            return []
        return [l.strip() for l in self.languages.split(',') if l.strip()]
    
    def update_statistics(self):
        """Përditëso statistikat e turistit"""
        from bookings.models import Booking
        
        bookings = Booking.objects.filter(
            tourist=self,
            status='completed'
        )
        
        self.total_bookings = bookings.count()
        self.total_spent = sum(b.total_price for b in bookings) or Decimal('0.00')
        self.save(update_fields=['total_bookings', 'total_spent', 'updated_at'])


# ==================== SIGNALS ====================

@receiver(post_save, sender=GuideProfile)
def update_guide_on_status_change(sender, instance, created, **kwargs):
    """Përditëso guide kur statusi ndryshon"""
    # Avoid calling instance.save() inside a post_save handler because that
    # would emit post_save again and can lead to recursive save loops.
    # Use QuerySet.update() to perform a direct DB update without sending signals.
    try:
        if created:
            # On creation, status may be the default; handle explicitly if needed
            if instance.status == "verified" and not instance.is_verified:
                GuideProfile.objects.filter(pk=instance.pk).update(
                    is_verified=True, verified_at=timezone.now()
                )
            return

        if instance.status == "verified" and not instance.is_verified:
            GuideProfile.objects.filter(pk=instance.pk).update(
                is_verified=True, verified_at=timezone.now()
            )
        elif instance.status != "verified" and instance.is_verified:
            GuideProfile.objects.filter(pk=instance.pk).update(is_verified=False)
    except Exception:
        # Swallow exceptions to avoid breaking the save flow
        pass