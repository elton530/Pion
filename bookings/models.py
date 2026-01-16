from django.db import models
from django.contrib.auth.models import User
from tours.models import Tour
from users.models import TouristProfile


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Në pritje"),
        ("confirmed", "Konfirmuar"),
        ("cancelled", "Anulluar"),
    ]

    tourist = models.ForeignKey(
        TouristProfile, on_delete=models.CASCADE, related_name="bookings"
    )
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="bookings")
    num_people = models.PositiveSmallIntegerField(
        help_text="Numri i personave (përfshirë veten)"
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True, help_text="Kërkesa speciale, pyetje, etj.")
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed_24h = models.BooleanField(
        default=False, help_text="Tourist confirmed participation 24h before tour"
    )
    confirmed_24h_at = models.DateTimeField(
        blank=True, null=True, help_text="When tourist confirmed their participation"
    )

    class Meta:
        unique_together = ("tourist", "tour")  # një person një rezervim për tur
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tourist.user.get_full_name()} - {self.tour.title} ({self.num_people} persona)"

    def save(self, *args, **kwargs):
        # Llogarit çmimin total
        self.total_price = self.tour.price_per_person * self.num_people

        # Kontrollo vende të lira vetëm kur krijohet (jo kur ndryshon status)
        if not self.pk:
            if self.tour.available_spots < self.num_people:
                raise ValueError(
                    "Nuk ka vende të mjaftueshme të lira për këtë rezervim."
                )
            self.tour.available_spots -= self.num_people
            self.tour.save(update_fields=["available_spots"])

        super().save(*args, **kwargs)

    def cancel(self):
        if self.status == "pending" or self.status == "confirmed":
            self.status = "cancelled"
            self.tour.available_spots += self.num_people
            self.tour.save(update_fields=["available_spots"])
            self.save(update_fields=["status"])

    def is_24h_before_tour(self):
        """Check if tour starts within 24 hours."""
        from django.utils import timezone
        from datetime import timedelta

        tour_start = (
            timezone.make_aware(
                timezone.datetime.combine(self.tour.date, self.tour.time_start)
            )
            if self.tour.date
            else None
        )

        if not tour_start:
            return False
        now = timezone.now()
        return (tour_start - now).total_seconds() <= 86400 and (
            tour_start - now
        ).total_seconds() >= 0
