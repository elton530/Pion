from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
import json

from bookings.models import Booking
from tours.forms import TourEditForm
from tours.models import Tour, TourReview, TourStatistic, TourType
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


class TourStatusApiSecurityTests(TestCase):
    def setUp(self):
        self.guide_user = User.objects.create_user(
            username="status_guide",
            email="status_guide@example.com",
            password="secret123",
        )
        self.guide_profile = GuideProfile.objects.create(
            user=self.guide_user,
            location="Tiranë",
        )

        self.other_guide_user = User.objects.create_user(
            username="status_other_guide",
            email="status_other_guide@example.com",
            password="secret123",
        )
        self.other_guide_profile = GuideProfile.objects.create(
            user=self.other_guide_user,
            location="Durrës",
        )

        self.tourist_user = User.objects.create_user(
            username="status_tourist",
            email="status_tourist@example.com",
            password="secret123",
        )
        TouristProfile.objects.create(user=self.tourist_user)

        self.tour_type = TourType.objects.create(name="Status Type", description="Status test")
        self.tour = Tour.objects.create(
            guide=self.guide_profile,
            title="Status Tour",
            slug="status-tour",
            short_description="Status description",
            full_description="Status full description",
            tour_type=self.tour_type,
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=12,
            main_image=SimpleUploadedFile(
                "status-tour.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="draft",
            is_active=True,
        )

        self.other_tour = Tour.objects.create(
            guide=self.other_guide_profile,
            title="Other Status Tour",
            slug="other-status-tour",
            short_description="Other description",
            full_description="Other full description",
            tour_type=self.tour_type,
            meeting_point="Sheshi",
            location_city="Durrës",
            location_region="Durrës",
            duration_hours=5,
            date="2030-01-02",
            time_start="11:00:00",
            price_per_person=90,
            max_participants=8,
            main_image=SimpleUploadedFile(
                "other-status-tour.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="published",
            is_active=True,
        )

    def test_get_tour_status_requires_authentication(self):
        response = self.client.get(reverse("tours:get_tour_status", args=[self.tour.id]))
        self.assertEqual(response.status_code, 302)

    def test_update_tour_status_requires_authentication(self):
        response = self.client.post(
            reverse("tours:update_tour_status"),
            data=json.dumps({"tour_id": self.tour.id, "status": "published"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_non_guide_cannot_access_status_endpoints(self):
        self.client.force_login(self.tourist_user)

        status_response = self.client.get(reverse("tours:get_tour_status", args=[self.tour.id]))
        self.assertEqual(status_response.status_code, 403)

        update_response = self.client.post(
            reverse("tours:update_tour_status"),
            data=json.dumps({"tour_id": self.tour.id, "status": "published"}),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 403)

        bulk_response = self.client.get(reverse("tours:get_guide_tours_status"))
        self.assertEqual(bulk_response.status_code, 403)

    def test_guide_cannot_update_another_guides_tour(self):
        self.client.force_login(self.guide_user)

        response = self.client.post(
            reverse("tours:update_tour_status"),
            data=json.dumps({"tour_id": self.other_tour.id, "status": "hidden"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.other_tour.refresh_from_db()
        self.assertEqual(self.other_tour.status, "published")

    def test_update_tour_status_rejects_invalid_status_value(self):
        self.client.force_login(self.guide_user)

        response = self.client.post(
            reverse("tours:update_tour_status"),
            data=json.dumps({"tour_id": self.tour.id, "status": "archived"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])

    def test_update_tour_status_rejects_invalid_transition(self):
        self.tour.status = "completed"
        self.tour.save(update_fields=["status"])
        self.client.force_login(self.guide_user)

        response = self.client.post(
            reverse("tours:update_tour_status"),
            data=json.dumps({"tour_id": self.tour.id, "status": "published"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.status, "completed")

    def test_update_tour_status_allows_valid_transition(self):
        self.client.force_login(self.guide_user)

        response = self.client.post(
            reverse("tours:update_tour_status"),
            data=json.dumps({"tour_id": self.tour.id, "status": "published"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.status, "published")

    def test_update_tour_status_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username="status_guide", password="secret123")

        response = csrf_client.post(
            reverse("tours:update_tour_status"),
            data=json.dumps({"tour_id": self.tour.id, "status": "published"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)


class TourReviewAuthorizationTests(TestCase):
    """Regression: vlerësimet lejohen vetëm për ture të publikuar dhe jo për turin tënd."""

    def setUp(self):
        self.guide_user = User.objects.create_user(
            username="review_guide",
            email="review_guide@example.com",
            password="secret123",
        )
        self.guide_profile = GuideProfile.objects.create(
            user=self.guide_user,
            location="Tiranë",
        )

        self.tourist_user = User.objects.create_user(
            username="review_tourist",
            email="review_tourist@example.com",
            password="secret123",
        )
        self.tourist_profile = TouristProfile.objects.create(user=self.tourist_user)

        self.tour_type = TourType.objects.create(name="Review Type", description="Test")

        self.published_tour = Tour.objects.create(
            guide=self.guide_profile,
            title="Published Review Tour",
            slug="published-review-tour",
            short_description="Description",
            full_description="Full description",
            tour_type=self.tour_type,
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            main_image=SimpleUploadedFile(
                "published-review.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="published",
            is_active=True,
        )

        self.draft_tour = Tour.objects.create(
            guide=self.guide_profile,
            title="Draft Review Tour",
            slug="draft-review-tour",
            short_description="Description",
            full_description="Full description",
            tour_type=self.tour_type,
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            main_image=SimpleUploadedFile(
                "draft-review.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="draft",
            is_active=True,
        )

    def _post_review(self, tour_slug):
        return self.client.post(
            reverse("tours:create_review", kwargs={"slug": tour_slug}),
            {"rating": 5, "comment": "Një koment mjaft i gjatë për të kaluar validimin."},
            follow=True,
        )

    def test_tourist_can_review_published_tour(self):
        self.client.force_login(self.tourist_user)
        response = self._post_review(self.published_tour.slug)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(TourReview.objects.filter(
            tour=self.published_tour, tourist=self.tourist_profile
        ).exists())

    def test_tourist_cannot_review_draft_tour(self):
        self.client.force_login(self.tourist_user)
        response = self.client.post(
            reverse("tours:create_review", kwargs={"slug": self.draft_tour.slug}),
            {"rating": 5, "comment": "Një koment mjaft i gjatë për të kaluar validimin."},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(TourReview.objects.filter(
            tour=self.draft_tour, tourist=self.tourist_profile
        ).exists())

    def test_unauthenticated_user_cannot_review(self):
        response = self.client.post(
            reverse("tours:create_review", kwargs={"slug": self.published_tour.slug}),
            {"rating": 5, "comment": "Një koment mjaft i gjatë për të kaluar validimin."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(TourReview.objects.filter(tour=self.published_tour).exists())

    def test_guide_cannot_review_own_tour(self):
        guide_tourist_user = User.objects.create_user(
            username="review_dual",
            email="review_dual@example.com",
            password="secret123",
        )
        dual_guide = GuideProfile.objects.create(user=guide_tourist_user, location="Vlorë")
        TouristProfile.objects.create(user=guide_tourist_user)
        own_tour = Tour.objects.create(
            guide=dual_guide,
            title="Own Tour",
            slug="own-tour",
            short_description="Description",
            full_description="Full description",
            tour_type=self.tour_type,
            meeting_point="Qendra",
            location_city="Vlorë",
            location_region="Vlorë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            main_image=SimpleUploadedFile(
                "own-tour.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="published",
            is_active=True,
        )

        self.client.force_login(guide_tourist_user)
        response = self.client.post(
            reverse("tours:create_review", kwargs={"slug": own_tour.slug}),
            {"rating": 5, "comment": "Një koment mjaft i gjatë për të kaluar validimin."},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TourReview.objects.filter(tour=own_tour).exists())
