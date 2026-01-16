from django.db import models
from django.contrib.auth.models import User
from users.models import GuideProfile
from django.utils.text import slugify

TOUR_TYPES = [
    ("nature_walk", "Ecje në Natyrë"),
    ("alpine", "Guide Alpinistike"),
    ("bike_tour", "Tur me Biçikletë"),
    ("rural", "Zona Rurale"),
    ("cultural", "Tur Kulturor"),
    ("adventure", "Aventurë"),
    ("other", "Tjetër"),
]

DIFFICULTY_LEVELS = [
    ("easy", "Lehtë"),
    ("moderate", "Mesatare"),
    ("hard", "E vështirë"),
    ("expert", "Vetëm për ekspertë"),
]


class TourType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tour Type"
        verbose_name_plural = "Tour Types"


class Tour(models.Model):
    guide = models.ForeignKey(
        GuideProfile, on_delete=models.CASCADE, related_name="tours"
    )
    title = models.CharField(
        max_length=200, help_text="p.sh. Ecje në Theth - Liqeni i Komanit"
    )
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(
        help_text="Përshkrim i detajuar i itinerarit, çfarë do të shohim, etj."
    )
    tour_type = models.CharField(
        max_length=50, choices=TOUR_TYPES, default="nature_walk"
    )
    difficulty = models.CharField(
        max_length=20, choices=DIFFICULTY_LEVELS, default="moderate"
    )

    location_start = models.CharField(
        max_length=150, help_text="Vendi i takimit, p.sh. Sheshi Skënderbej, Tiranë"
    )
    duration_hours = models.PositiveIntegerField(
        help_text="Sa orë zgjat turi (p.sh. 6)"
    )
    distance_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Në km, opsionale",
    )

    price_per_person = models.DecimalField(
        max_digits=8, decimal_places=2, help_text="Çmimi në Lekë ose Euro"
    )
    max_participants = models.PositiveSmallIntegerField(default=10)
    available_spots = models.PositiveSmallIntegerField(
        editable=False
    )  # do ta llogarisim automatikisht

    date = models.DateField(help_text="Data kur zhvillohet turi")
    time_start = models.TimeField(help_text="Ora e nisjes")

    main_image = models.ImageField(
        upload_to="tours/main/", help_text="Foto kryesore e turit"
    )
    additional_images = models.ManyToManyField(
        "TourImage", blank=True, related_name="tours"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Rating summary
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    reviews_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.guide.user.get_full_name()} ({self.date})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Siguro unik (shton -1, -2 etj. nëse ekziston)
            original_slug = self.slug
            queryset = Tour.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            counter = 1
            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        if not self.pk:  # kur krijohet për herë të parë
            self.available_spots = self.max_participants
        super().save(*args, **kwargs)


class TourImage(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="tours/additional/")
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Foto për {self.tour.title}"


class TourReview(models.Model):
    """Review left by a Tourist for a Tour. One review per tourist per tour."""

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="reviews")
    tourist = models.ForeignKey(
        "users.TouristProfile", on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()  # 1..5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tour", "tourist")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tourist.user.get_full_name() or self.tourist.user.username} - {self.tour.title} ({self.rating})"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        # Recalculate aggregates on the tour
        from django.db.models import Avg, Count

        stats = self.tour.reviews.aggregate(avg=Avg("rating"), cnt=Count("id"))
        self.tour.average_rating = stats["avg"] or 0.0
        self.tour.reviews_count = stats["cnt"] or 0
        self.tour.save(update_fields=["average_rating", "reviews_count"])

    def delete(self, *args, **kwargs):
        tour = self.tour
        super().delete(*args, **kwargs)
        from django.db.models import Avg, Count

        stats = tour.reviews.aggregate(avg=Avg("rating"), cnt=Count("id"))
        tour.average_rating = stats["avg"] or 0.0
        tour.reviews_count = stats["cnt"] or 0
        tour.save(update_fields=["average_rating", "reviews_count"])
