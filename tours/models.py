from django.db import models
from django.db.models import Sum
from users.models import GuideProfile, TouristProfile
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

# ==================== CHOICES ====================

TOUR_TYPES = [
    ("nature_walk", "Ecje në Natyrë"),
    ("alpine_guide", "Guide Alpinistike"),
    ("bike_tour", "Tur me Biçikletë"),
    ("rural_cultural_food", "Përvojë Rurale, Kulturore dhe Kulinarie"),
    ("cultural", "Tur Kulturor"),
    ("adventure", "Tur Aventure"),
    ("historical", "Tur Historik"),
    ("food", "Tur Kulinarik"),
    ("photography", "Tur Fotografik"),
    ("wellness", "Tur Wellness dhe Relaksimi"),
    ("family", "Tur Familjar"),
    ("custom", "Personalizuar/Tjetër")
]

DIFFICULTY_LEVELS = [
    ("very_easy", "Shumë e Lehtë (Për të gjitha moshat)"),
    ("easy", "Lehtë (Fillestar)"),
    ("moderate", "Mesatare (Kërkon kondite)"),
    ("hard", "E vështirë (Eksperience e nevojshme)"),
    ("expert", "Vetëm për ekspertë"),
]

TOUR_STATUS = [
    ("draft", "Draft"),
    ("published", "Publikuar"),
    ("hidden", "I fshehur"),
    ("cancelled", "Anuluar"),
    ("completed", "Përfunduar"),
]

CURRENCY_CHOICES = [
    ("ALL", "Lekë"),
    ("EUR", "Euro"),
    ("USD", "Dollarë Amerikan"),
]

AGE_GROUP_CHOICES = [
    ("all", "Për të gjitha moshat"),
    ("adults", "Vetëm të rritur"),
    ("families", "Familje"),
    ("seniors", "Seniorë"),
    ("youth", "Rinia (18-25)"),
    ("children", "Fëmijë (pranë prindërve)"),
]

LANGUAGE_CHOICES = [
    ("sq", "Shqip"),
    ("en", "Anglisht"),
    ("it", "Italisht"),
    ("de", "Gjermansht"),
    ("fr", "Frengjishtë"),
]

# ==================== CUSTOM MANAGERS ====================

class TourQuerySet(models.QuerySet):
    """Custom QuerySet për Tour model"""
    
    def active(self):
        """Turet aktive dhe të publikuara"""
        return self.filter(
            is_active=True,
            status="published",
            date__gte=timezone.now().date()
        )
    
    def upcoming(self):
        """Turet e ardhshëm"""
        return self.filter(
            is_active=True,
            status="published",
            date__gte=timezone.now().date()
        ).order_by('date')
    
    def past(self):
        """Turet e kaluar"""
        return self.filter(
            date__lt=timezone.now().date()
        ).order_by('-date')
    
    def by_guide(self, guide):
        """Turet e një udhëzuesi specifik"""
        return self.filter(guide=guide)
    
    def by_type(self, tour_type):
        """Turet sipas llojit"""
        return self.filter(is_active=True, status="published", tour_type=tour_type)
    
    def by_location(self, location):
        """Turet sipas lokacionit"""
        return self.filter(
            is_active=True,
            status="published",
            location_city__icontains=location
        )
    
    def by_difficulty(self, difficulty):
        """Turet sipas nivelit të vështirësisë"""
        return self.filter(
            is_active=True,
            status="published",
            difficulty=difficulty
        )
    
    def featured(self):
        """Turet e veçuar"""
        return self.filter(
            is_active=True,
            status="published",
            is_featured=True,
            featured_until__gte=timezone.now().date()
        )
    
    def available(self):
        """Turet me vende të lira"""
        return self.filter(
            is_active=True,
            status="published",
            available_spots__gt=0
        )
    
    def price_range(self, min_price, max_price):
        """Turet në një gamë çmimesh"""
        return self.filter(
            is_active=True,
            status="published",
            price_per_person__gte=min_price,
            price_per_person__lte=max_price
        )
    
    def top_rated(self, limit=10):
        """Turet më të vlerësuar"""
        return self.filter(
            is_active=True,
            status="published",
            reviews_count__gt=0
        ).order_by('-average_rating', '-reviews_count')[:limit]


# ==================== TOUR TYPE MODEL ====================

class TourType(models.Model):
    """Kategoria/lloji i turit"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Emri i ikonës FontAwesome ose emoji"
    )
    color = models.CharField(
        max_length=7,
        default="#27ae60",
        help_text="Ngjyra në HEX (#27ae60)"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Lloji i Turit"
        verbose_name_plural = "Llojet e Tureve"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def tour_count(self):
        """Numri i tureve aktiv në këtë kategori"""
        return self.tours.filter(is_active=True, status="published").count()


# ==================== MAIN TOUR MODEL ====================

class Tour(models.Model):
    """Modeli kryesor i Turit"""
    
    # ===== INFORMACIONE BAZIKE =====
    guide = models.ForeignKey(
        GuideProfile,
        on_delete=models.CASCADE,
        related_name="tours",
        help_text="Udhëzuesi që ofron turin"
    )
    title = models.CharField(
        max_length=200,
        help_text="Titulli tërheqës, p.sh. 'Ecje në Theth - Liqeni i Komanit'"
    )
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    short_description = models.CharField(
        max_length=300,
        help_text="Përshkrim i shkurtër për listime (max 300 karaktere)"
    )
    full_description = models.TextField(
        help_text="Përshkrim i detajuar i itinerarit, çfarë do të shohim, përvoja, etj."
    )
    
    # ===== KATEGORIZIM =====
    tour_type = models.ForeignKey(
        TourType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tours",
        help_text="Lloji i turit"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default="moderate"
    )
    status = models.CharField(
        max_length=20,
        choices=TOUR_STATUS,
        default="draft"
    )
    age_group = models.CharField(
        max_length=20,
        choices=AGE_GROUP_CHOICES,
        default="all",
        help_text="Grupi moshor i synuar"
    )
    languages = models.CharField(
        max_length=50,
        choices=LANGUAGE_CHOICES,
        default="sq",
        help_text="Gjuhet e ofruara"
    )
    
    # ===== DETAJET E LOKACIONIT =====
    meeting_point = models.CharField(
        max_length=200,
        help_text="Vendi ku takohen pjesëmarrësit për nisjen e turit"
    )
    meeting_point_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude për pikën e takimit 'gjeresia-gjeografike'"
    )
    meeting_point_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude për pikën e takimit 'gjatësia-gjeografike'"
    )
    location_city = models.CharField(
        max_length=100,
        help_text="Qyteti, p.sh. Tiranë"
    )
    location_region = models.CharField(
        max_length=100,
        help_text="Rajoni, p.sh. Dajti, Theth, etj."
    )
    end_point = models.CharField(
        max_length=200,
        blank=True,
        help_text="Vendi ku përfundon turi (nëse është i ndryshëm)"
    )
    
    # ===== KOHËZGJATJA =====
    duration_hours = models.PositiveIntegerField(
        help_text="Sa orë zgjat turi (p.sh. 6)"
    )
    duration_days = models.PositiveIntegerField(
        default=0,
        help_text="Numri i ditëve (për turet shumë-ditore)"
    )
    date = models.DateField(help_text="Data kur zhvillohet turi")
    time_start = models.TimeField(help_text="Ora e nisjes")
    time_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Ora e parashikuar e përfundimit"
    )
    
    # ===== DETAJET FIZIKE =====
    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distanca totale në kilometra"
    )
    elevation_gain = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Fitimi i lartësisë në metra"
    )
    max_altitude = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Lartësia maksimale në metra"
    )
    
    # ===== ÇMIM DHE KAPACITET =====
    price_per_person = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Çmimi për person"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="ALL"
    )
    max_participants = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Kapaciteti maksimal i pjesëmarrësve në tur"
    )
    min_participants = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Numri minimal i pjesëmarrësve për të realizuar turin"
    )
    available_spots = models.PositiveSmallIntegerField(editable=False, default=0)
    
    # ===== ZBRITJE DHE OFERTAT SPECIALE =====
    has_discount = models.BooleanField(default=False)
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Çmimi me zbritje"
    )
    discount_until = models.DateField(
        null=True,
        blank=True,
        help_text="Data deri kur vlen zbritja"
    )
    early_bird_days = models.PositiveIntegerField(
        default=0,
        help_text="Numri i ditëve para turit për të përfituar zbritjen early bird"
    )
    early_bird_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Përqindja e zbritjes për early bird"
    )
    
    # ===== IMAZHET =====
    main_image = models.ImageField(
        upload_to="tours/main/%Y/%m/",
        help_text="Foto kryesore e turit (rekomandohet 1200x800px)"
    )
    thumbnail = models.ImageField(
        upload_to="tours/thumbnails/%Y/%m/",
        null=True,
        blank=True,
        help_text="Miniaturë e turit (p.sh. 400x300px)"
    )
    
    # ===== PËRMBAJTJA DHE DETAJET =====
    highlights = models.TextField(
        blank=True,
        help_text="Pikat kryesore të turit (një për rresht)"
    )
    included = models.TextField(
        blank=True,
        help_text="Çfarë përfshihet në çmim (një për rresht)"
    )
    not_included = models.TextField(
        blank=True,
        help_text="Çfarë NUK përfshihet në çmim (një për rresht)"
    )
    what_to_bring = models.TextField(
        blank=True,
        help_text="Çfarë duhet të merr me vete (një për rresht)"
    )
    
    # ===== KËRKESAT DHE KUFIZIMET =====
    requirements = models.TextField(
        blank=True,
        help_text="Kërkesat për pjesëmarrësit (gjendja shëndetësore, përvoja, etj.)"
    )
    health_warnings = models.TextField(
        blank=True,
        help_text="Paralajmërimet shëndetësore"
    )
    equipment_provided = models.TextField(
        blank=True,
        help_text="Pajisjet që ofrohen nga udhëzuesi"
    )
    
    # ===== LOGJISTIKA =====
    transportation_included = models.BooleanField(
        default=False,
        help_text="Përfshihet transporti në çmim?"
    )
    transportation_details = models.TextField(
        blank=True,
        help_text="Detajet e transportit"
    )
    meal_included = models.BooleanField(
        default=False,
        help_text="Përfshihet vakt në çmim?"
    )
    meal_details = models.TextField(
        blank=True,
        help_text="Detajet për ushqimin (dreke, pije, etj.)"
    )
    accommodation_included = models.BooleanField(
        default=False,
        help_text="Përfshihet akomodimi në çmim?"
    )
    accommodation_details = models.TextField(
        blank=True,
        help_text="Detajet për akomodimin"
    )
    
    # ===== POLITIKA ANULIMI =====
    cancellation_deadline_hours = models.PositiveIntegerField(
        default=48,
        help_text="Sa orë përpara turit mund të anulohet pa ndeshkim"
    )
    cancellation_policy = models.TextField(
        blank=True,
        help_text="Politika e detajuar e anulimit"
    )
    refund_percentage = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Përqindja e rimbursimit nëse anulohet brenda afatit"
    )
    
    # ===== SEO DHE MARKETING =====
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    meta_keywords = models.TextField(
        blank=True,
        help_text="Fjalë kyçe të ndara me presje"
    )
    is_featured = models.BooleanField(default=False)
    featured_until = models.DateField(null=True, blank=True)
    booking_count = models.PositiveIntegerField(default=0, editable=False)
    
    # ===== VLERËSIM DHE KOMENTE =====
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    reviews_count = models.PositiveIntegerField(default=0, editable=False)
    
    # ===== FUSHË SISTEMI =====
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_booking_at = models.DateTimeField(null=True, blank=True, editable=False)
    
    objects = TourQuerySet.as_manager()
    
    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=['is_active', 'status', 'date']),
            models.Index(fields=['guide', 'is_active']),
            models.Index(fields=['tour_type_id', 'is_active']),
            models.Index(fields=['location_city', 'is_active']),
            models.Index(fields=['price_per_person']),
            models.Index(fields=['difficulty', 'is_active']),
            models.Index(fields=['average_rating', 'reviews_count']),
        ]
        verbose_name = "Tur"
        verbose_name_plural = "Turet"
    
    def __str__(self):
        return f"{self.title} - {self.guide.user.get_full_name()} ({self.date})"
    
    def save(self, *args, **kwargs):
        # Gjenerimi i slug-ut nëse nuk ekziston
        if not self.slug:
            self.slug = self.generate_unique_slug()
        
        # Vendosja e vendeve të lira gjatë krijimit
        if not self.pk:
            self.available_spots = self.max_participants
        
        # Auto-plotësimi i meta tageve
        if not self.meta_title and self.title:
            self.meta_title = self.title[:200]
        
        if not self.meta_description and self.short_description:
            self.meta_description = self.short_description[:300]
        
        super().save(*args, **kwargs)
    
    def generate_unique_slug(self):
        """Gjeneroni një slug unik për turin"""
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        
        while Tour.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    # ===== PROPERTIES =====
    
    @property
    def is_upcoming(self):
        """Kontrollo nëse turi është në të ardhmen"""
        return self.date >= timezone.now().date()
    
    @property
    def is_past(self):
        """Kontrollo nëse turi është në të kaluarën"""
        return self.date < timezone.now().date()
    
    @property
    def is_full(self):
        """Kontrollo nëse turi është plotë"""
        return self.available_spots <= 0
    
    @property
    def has_available_spots(self):
        """Kontrollo nëse turi ka vende të lira"""
        return self.available_spots > 0
    
    @property
    def booking_percentage(self):
        """Llogarit përqindjen e prenotimeve"""
        if self.max_participants == 0:
            return 0
        booked = self.max_participants - self.available_spots
        return (booked / self.max_participants) * 100
    
    @property
    def confirmed_booked_spots(self):
        """Numri i vendeve të konfirmuara"""
        return self.bookings.filter(
            status__in=['confirmed', 'completed']
        ).aggregate(total=Sum('num_people'))['total'] or 0
    
    @property
    def confirmed_percentage(self):
        """Përqindja e prenotimeve të konfirmuara"""
        if self.max_participants == 0:
            return 0
        return (self.confirmed_booked_spots / self.max_participants) * 100
    
    @property
    def current_price(self):
        """Merr çmimin aktual (me zbritje nëse zbatohet)"""
        # Prefer discount price when applicable
        if (self.has_discount and self.discount_until and
                self.discount_until >= timezone.now().date()):
            val = self.discount_price if self.discount_price is not None else self.price_per_person
        elif self.is_early_bird:
            val = self.early_bird_price
        else:
            val = self.price_per_person

        # Coerce to Decimal and fallback to 0.00 if missing
        try:
            return Decimal(str(val)) if val is not None else Decimal('0.00')
        except Exception:
            return Decimal('0.00')
    
    @property
    def duration_formatted(self):
        """Formati i kohëzgjatjes në mënyrë të lexueshme"""
        if self.duration_days > 0:
            if self.duration_hours > 0:
                return f"{self.duration_days} ditë {self.duration_hours} orë"
            return f"{self.duration_days} ditë"
        return f"{self.duration_hours} orë"
    
    @property
    def is_early_bird(self):
        """Kontrollo nëse zbatohet early bird discount"""
        if not self.early_bird_days or not self.early_bird_discount:
            return False
        days_until_tour = (self.date - timezone.now().date()).days
        return days_until_tour >= self.early_bird_days
    
    @property
    def early_bird_price(self):
        """Llogarit çmimin e early bird"""
        if self.is_early_bird:
            discount_amount = self.price_per_person * (self.early_bird_discount / 100)
            return self.price_per_person - discount_amount
        return self.price_per_person
    
    @property
    def can_be_booked(self):
        """Kontrollo nëse turi mund të prenohet"""
        return (
            self.is_active and
            self.status == "published" and
            self.is_upcoming and
            self.has_available_spots
        )
    
    @property
    def highlights_list(self):
        """Merr highlights si listë"""
        if not self.highlights:
            return []
        return [h.strip() for h in self.highlights.split('\n') if h.strip()]
    
    @property
    def included_list(self):
        """Merr artikujt e përfshirë si listë"""
        if not self.included:
            return []
        return [i.strip() for i in self.included.split('\n') if i.strip()]
    
    @property
    def not_included_list(self):
        """Merr artikujt e mos-përfshirë si listë"""
        if not self.not_included:
            return []
        return [ni.strip() for ni in self.not_included.split('\n') if ni.strip()]
    
    @property
    def what_to_bring_list(self):
        """Merr çfarë duhet të marrë si listë"""
        if not self.what_to_bring:
            return []
        return [w.strip() for w in self.what_to_bring.split('\n') if w.strip()]
    
    @property
    def requirements_list(self):
        """Merr kërkesat si listë"""
        if not self.requirements:
            return []
        return [r.strip() for r in self.requirements.split('\n') if r.strip()]
    
    def update_available_spots(self):
        """Përditëso numrin e vendeve të lira bazuar në prenotimet e konfirmuara"""
        try:
            confirmed_count = self.bookings.filter(
                status='confirmed'
            ).aggregate(total=Sum('num_people'))['total'] or 0
            self.available_spots = max(0, self.max_participants - confirmed_count)
            self.save(update_fields=['available_spots', 'updated_at'])
        except Exception as e:
            print(f"Error updating available spots: {e}")
    
    def get_absolute_url(self):
        """Merr URL-in absolute të turit"""
        from django.urls import reverse
        return reverse('tours:tour_detail', kwargs={'slug': self.slug})
    
    def get_recommended_tours(self, limit=3):
        """Merr turet e rekomanduar (i njëjtë lloj ose lokacion)"""
        return Tour.objects.filter(
            is_active=True,
            status="published",
            date__gte=timezone.now().date()
        ).exclude(
            pk=self.pk
        ).filter(
            models.Q(tour_type_id=self.tour_type_id) |
            models.Q(location_city=self.location_city)
        ).order_by('?')[:limit]


# ==================== TOUR IMAGE MODEL ====================

class TourImage(models.Model):
    """Modeli për imazhet shtesë të turit"""
    
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="tours/additional/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(
        default=False,
        help_text="Foto kryesore për galeri"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Foto Turi"
        verbose_name_plural = "Foto të Tureve"
    
    def __str__(self):
        return f"Foto për {self.tour.title}"
    
    def save(self, *args, **kwargs):
        # Hiq imazhet e tjera primäre nëse ky është vendosur si primary
        if self.is_primary:
            TourImage.objects.filter(
                tour=self.tour,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


# ==================== TOUR SCHEDULE MODEL ====================

class TourSchedule(models.Model):
    """Modeli për programin e detajuar/itinerarin e tureve shumë-ditore"""
    
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="schedules"
    )
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200, help_text="Titulli i ditës")
    description = models.TextField(help_text="Përshkrim i aktiviteteve për këtë ditë")
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    meals_included = models.CharField(
        max_length=100,
        blank=True,
        help_text="P.sh. Mëngjes, Dreka, Darka"
    )
    accommodation = models.CharField(
        max_length=200,
        blank=True,
        help_text="Detajet e akomodimit për këtë ditë"
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['tour', 'day_number', 'order']
        unique_together = ['tour', 'day_number']
        verbose_name = "Programi i Turit"
        verbose_name_plural = "Programet e Tureve"
    
    def __str__(self):
        return f"Dita {self.day_number}: {self.title} - {self.tour.title}"


# ==================== TOUR FAQ MODEL ====================

class TourFAQ(models.Model):
    """Pyetjet e shpeshta për një tur"""
    
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="faqs"
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Pyetja e Shpeshtë"
        verbose_name_plural = "Pyetjet e Shpeshta"
    
    def __str__(self):
        return f"PY: {self.question[:50]}..."


# ==================== TOUR REVIEW MODELS ====================

class TourReview(models.Model):
    """Vlerësimet dhe komentet e turistëve për një tur"""
    
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    tourist = models.ForeignKey(
        TouristProfile,
        on_delete=models.CASCADE,
        related_name="tour_reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Vlerësimi nga 1 deri në 5 yje"
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Titulli i review-it"
    )
    comment = models.TextField(
        blank=True,
        help_text="Koment i detajuar"
    )
    
    # Vlerësimet e detalizuara (opsionale)
    guide_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Vlerësimi për udhëzuesin"
    )
    value_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Vlerësimi për vlerën për paratë"
    )
    experience_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Vlerësimi për përvojën e përgjithshme"
    )
    
    # Fushat e administrimit
    is_verified = models.BooleanField(
        default=False,
        help_text="Review i verifikuar (turistë i vërtetë)"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Shfaq si featured review në faqen e turit"
    )
    is_approved = models.BooleanField(
        default=True,
        help_text="Aprovo review-in për publikim"
    )
    
    # Fushat e sistemit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    helpful_count = models.PositiveIntegerField(default=0, editable=False)
    
    class Meta:
        unique_together = ("tour", "tourist")
        ordering = ["-created_at", "-is_featured"]
        indexes = [
            models.Index(fields=['tour', 'is_approved']),
            models.Index(fields=['tourist', 'created_at']),
            models.Index(fields=['rating']),
        ]
        verbose_name = "Vlerësimi i Turit"
        verbose_name_plural = "Vlerësimet e Tureve"
    
    def __str__(self):
        username = self.tourist.user.get_full_name() or self.tourist.user.username
        return f"{username} - {self.tour.title} ({self.rating}⭐)"
    
    @property
    def average_rating_detail(self):
        """Llogarit mesataren e vlerësimeve të detalizuara"""
        ratings = [self.rating]
        if self.guide_rating:
            ratings.append(self.guide_rating)
        if self.value_rating:
            ratings.append(self.value_rating)
        if self.experience_rating:
            ratings.append(self.experience_rating)
        return sum(ratings) / len(ratings) if ratings else self.rating
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Përditëso vlerësimet e turit
        try:
            self.update_tour_ratings()
        except Exception as e:
            print(f"Error updating tour ratings: {e}")
        
        # Përditëso vlerësimin e guida-it
        try:
            if hasattr(self.tour.guide, 'update_rating'):
                self.tour.guide.update_rating()
        except Exception as e:
            print(f"Error updating guide rating: {e}")
    
    def delete(self, *args, **kwargs):
        tour = self.tour
        guide = tour.guide
        super().delete(*args, **kwargs)
        
        # Përditëso vlerësimet e turit
        self.update_tour_ratings(tour)
        
        # Përditëso vlerësimin e guida-it
        if hasattr(guide, 'update_rating'):
            guide.update_rating()
    
    def update_tour_ratings(self, tour=None):
        """Përditëso mesataren e vlerësimeve dhe numrin e review-eve për turin"""
        from django.db.models import Avg, Count
        
        tour = tour or self.tour
        reviews = tour.reviews.filter(is_approved=True)
        
        if reviews.exists():
            stats = reviews.aggregate(
                avg=Avg('rating'),
                cnt=Count('id')
            )
            tour.average_rating = stats['avg'] or Decimal('0.00')
            tour.reviews_count = stats['cnt'] or 0
        else:
            tour.average_rating = Decimal('0.00')
            tour.reviews_count = 0
        
        tour.save(update_fields=['average_rating', 'reviews_count', 'updated_at'])


# ==================== TOUR REVIEW IMAGE MODEL ====================

class TourReviewImage(models.Model):
    """Imazhet e ngarkuara nga turistët në review-et e tyre"""
    
    review = models.ForeignKey(
        TourReview,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="tours/reviews/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Foto Review"
        verbose_name_plural = "Fotos Review"
    
    def __str__(self):
        return f"Foto review nga {self.review.tourist.user.username}"


# ==================== TOUR HIGHLIGHT MODEL ====================

class TourHighlight(models.Model):
    """Pikat kryesore të veçanta të turit me ikonë dhe përshkrim"""
    
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="highlights_featured"
    )
    icon = models.CharField(
        max_length=50,
        help_text="Emri i ikonës FontAwesome"
    )
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Pika Kryesore"
        verbose_name_plural = "Pikat Kryesore"
    
    def __str__(self):
        return f"{self.title} - {self.tour.title}"


# ==================== TOUR TAG MODEL ====================

class TourTag(models.Model):
    """Etiketat për kërkime më të mira dhe kategorizim"""
    
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    tours = models.ManyToManyField(Tour, related_name="tags", blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Etiketa"
        verbose_name_plural = "Etiketat"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ==================== TOUR STATISTIC MODEL ====================

class TourStatistic(models.Model):
    """Ndjek statistikat dhe analizat e turit"""
    
    tour = models.OneToOneField(
        Tour,
        on_delete=models.CASCADE,
        related_name="statistics"
    )
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    inquiries = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Statistika Turi"
        verbose_name_plural = "Statistikat e Tureve"
    
    def __str__(self):
        return f"Statistika për {self.tour.title}"
    
    def increment_views(self, unique=False):
        """Shto numrin e këqyrjeve"""
        self.views += 1
        if unique:
            self.unique_views += 1
        self.last_viewed = timezone.now()
        self.save()
    
    def increment_shares(self):
        """Shto numrin e ndarjeve"""
        self.shares += 1
        self.save()
    
    def increment_inquiries(self):
        """Shto numrin e kërkesave"""
        self.inquiries += 1
        self.save()