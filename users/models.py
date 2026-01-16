from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Fusha për llojet e tureve prioritare
TOUR_TYPES = [
    ("nature_walk", "Ecje në Natyrë"),
    ("alpine", "Guide Alpinistike"),
    ("bike_tour", "Tur me Biçikletë"),
    ("rural", "Zona Rurale"),
    ("other", "Tjetër"),
]


class GuideProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="guide_profile"
    )
    photo = models.ImageField(upload_to="guides/photos/", blank=True, null=True)
    bio = models.TextField(max_length=1000, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, help_text="Qyteti ose zona ku operon")
    languages = models.CharField(
        max_length=200, blank=True, help_text="p.sh. Shqip, Anglisht, Italisht"
    )
    certifications = models.TextField(
        blank=True, help_text="Certifikime alpinizmi, ndihma e parë, etj."
    )
    specialty = models.CharField(max_length=50, choices=TOUR_TYPES, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Guide: {self.user.get_full_name() or self.user.username} - {self.location}"


class TouristProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="tourist_profile"
    )
    photo = models.ImageField(upload_to="tourists/photos/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    preferred_types = models.ManyToManyField(
        "tours.TourType", blank=True
    )  # do ta krijojmë më vonë

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tourist: {self.user.get_full_name() or self.user.username}"
