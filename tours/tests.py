from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking
from tours.forms import TourEditForm
from tours.models import Tour, TourStatistic, TourType
from users.models import GuideProfile, TouristProfile


class TourGuideViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="guide_user",
            email="guide@example.com",
            password="secret123",
        )
        self.guide = GuideProfile.objects.create(
            user=self.user,
            location="Tiranë",
            bio="Guide test",
            phone="0681234567",
        )
        self.tour_type = TourType.objects.create(
            name="Hiking",
            description="Test tour type",
        )
        self.tour = Tour.objects.create(
            guide=self.guide,
            title="Tur test",
            slug="tur-test",
            short_description="Përshkrim i shkurtër",
            full_description="Përshkrim i detajuar",
            tour_type=self.tour_type,
            difficulty="easy",
            age_group="all",
            languages="sq",
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            min_participants=2,
            main_image=SimpleUploadedFile(
                "tour.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
        )

    def test_pricing_page_loads_for_guide(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("tours:edit_tour_pricing", kwargs={"slug": self.tour.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tours/edit_tour_pricing.html")

    def test_edit_page_includes_backend_detail_sections(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("tours:edit_tour", kwargs={"slug": self.tour.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pikat kryesore")
        self.assertContains(response, "Çfarë të marrësh me vete")
        self.assertContains(response, "Detajet e transportit")

    def test_edit_form_uses_only_active_backend_tour_types(self):
        active_type = TourType.objects.create(name="Hiking Active", description="Active", is_active=True)
        inactive_type = TourType.objects.create(name="Hiking Inactive", description="Inactive", is_active=False)

        form = TourEditForm(instance=self.tour)

        self.assertIn(active_type, form.fields["tour_type"].queryset)
        self.assertNotIn(inactive_type, form.fields["tour_type"].queryset)

    def test_statistics_page_includes_confirmed_booking_context(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("tours:tour_statistics", kwargs={"slug": self.tour.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("confirmed_bookings_count", response.context)
        self.assertEqual(response.context["confirmed_bookings_count"], 0)

    def test_tour_detail_creates_statistics_when_missing(self):
        self.tour.status = "published"
        self.tour.save(update_fields=["status"])
        TourStatistic.objects.filter(tour=self.tour).delete()

        response = self.client.get(
            reverse("tours:tour_detail", kwargs={"slug": self.tour.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(TourStatistic.objects.filter(tour=self.tour).exists())

    def test_statistics_page_displays_view_count(self):
        stats = self.tour.statistics
        stats.views = 7
        stats.save(update_fields=["views"])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("tours:tour_statistics", kwargs={"slug": self.tour.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-target="7"')

    def test_booking_cancel_only_returns_spots_once(self):
        tourist_user = User.objects.create_user(
            username="tourist_user",
            email="tourist@example.com",
            password="secret123",
        )
        tourist_profile = TouristProfile.objects.create(user=tourist_user)
        booking = Booking.objects.create(
            tourist=tourist_profile,
            tour=self.tour,
            num_people=2,
        )

        self.assertEqual(self.tour.available_spots, 8)

        booking.cancel(cancelled_by="tourist", notes="")

        self.assertEqual(self.tour.available_spots, 10)
