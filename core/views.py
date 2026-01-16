from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils import timezone

from tours.models import Tour
from bookings.models import Booking
from users.models import GuideProfile, TouristProfile


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        ctx.update(
            {
                "tours_count": Tour.objects.filter(is_active=True).count(),
                "upcoming_tours": Tour.objects.filter(date__gte=today)
                .order_by("date")
                .select_related("guide")[:4],
                "top_rated_tours": Tour.objects.filter(is_active=True)
                .order_by("-average_rating", "-reviews_count")
                .select_related("guide")[:6],
                "bookings_count": Booking.objects.count(),
                "guides_count": GuideProfile.objects.count(),
                "tourists_count": TouristProfile.objects.count(),
            }
        )
        return ctx
