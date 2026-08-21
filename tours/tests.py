from datetime import timedelta
import base64
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking, BookingReview, Payment
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


class TourPublicListingTests(TestCase):
    """Workflow i turistit: shfletimi i tureve publike, filtra dhe detaje."""

    def setUp(self):
        self.guide_user = User.objects.create_user(
            username="pub_guide", password="secret123"
        )
        self.guide = GuideProfile.objects.create(user=self.guide_user, location="Tiranë")
        self.tour_type = TourType.objects.create(name="Hiking", description="Test")

        self.published = self._make_tour("published-tour", "Tiranë", date="2030-05-01")
        self.draft = self._make_tour("draft-tour", "Tiranë", status="draft")
        self.inactive = self._make_tour("inactive-tour", "Tiranë", is_active=False)
        self.past = self._make_tour("past-tour", "Durrës", date="2020-01-01")
        self.upcoming_durres = self._make_tour("upcoming-durres", "Durrës")

    def _make_tour(self, slug, city, status="published", date="2030-06-01", is_active=True):
        return Tour.objects.create(
            guide=self.guide,
            title=f"Tour {slug}",
            slug=slug,
            short_description="Short description",
            full_description="Full description",
            tour_type=self.tour_type,
            difficulty="easy",
            age_group="all",
            languages="sq",
            meeting_point="Qendra",
            location_city=city,
            location_region=city,
            duration_hours=4,
            date=date,
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            min_participants=2,
            status=status,
            is_active=is_active,
        )

    def test_list_only_shows_published_active_upcoming_tours(self):
        response = self.client.get(reverse("tours:tour_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "published-tour")
        self.assertContains(response, "upcoming-durres")
        self.assertNotContains(response, "draft-tour")
        self.assertNotContains(response, "inactive-tour")
        self.assertNotContains(response, "past-tour")

    def test_list_filters_by_location(self):
        response = self.client.get(reverse("tours:tour_list"), {"location": "Durrës"})
        self.assertContains(response, "upcoming-durres")
        self.assertNotContains(response, "published-tour")

    def test_list_filters_by_search_term(self):
        response = self.client.get(reverse("tours:tour_list"), {"search": "published"})
        self.assertContains(response, "published-tour")
        self.assertNotContains(response, "upcoming-durres")

    def test_search_excludes_past_tours(self):
        # Konsistente me listën: kërkimi nuk duhet të shfaqë ture të kaluar.
        response = self.client.get(reverse("tours:tour_search"), {"search": "tour"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "published-tour")
        self.assertContains(response, "upcoming-durres")
        self.assertNotContains(response, "past-tour")

    def test_public_cannot_view_draft_tour_detail(self):
        response = self.client.get(reverse("tours:tour_detail", args=["draft-tour"]))
        self.assertEqual(response.status_code, 404)

    def test_guide_owner_can_view_own_draft_tour_detail(self):
        self.client.force_login(self.guide_user)
        response = self.client.get(reverse("tours:tour_detail", args=["draft-tour"]))
        self.assertEqual(response.status_code, 200)

    def test_other_guide_cannot_view_draft_tour_detail(self):
        other = User.objects.create_user(username="pub_other_guide", password="secret123")
        GuideProfile.objects.create(user=other, location="Vlorë")
        self.client.force_login(other)
        response = self.client.get(reverse("tours:tour_detail", args=["draft-tour"]))
        self.assertEqual(response.status_code, 404)

    def test_tour_by_location_filters_by_city(self):
        response = self.client.get(reverse("tours:tour_by_location", args=["Tiranë"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "published-tour")
        self.assertNotContains(response, "upcoming-durres")

    def test_featured_tours_shows_only_featured(self):
        self.published.is_featured = True
        self.published.featured_until = timezone.now().date() + timedelta(days=10)
        self.published.save(update_fields=["is_featured", "featured_until"])
        response = self.client.get(reverse("tours:featured_tours"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "published-tour")
        self.assertNotContains(response, "upcoming-durres")


class GuideTourManagementTests(TestCase):
    """Workflow i guide-it: krijim, redaktim, fshirje, çmime dhe lista e tureve."""

    @staticmethod
    def _png_image(name="pic.jpg"):
        return SimpleUploadedFile(
            name,
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
            ),
            content_type="image/png",
        )

    def setUp(self):
        self.guide_user = User.objects.create_user(
            username="mgmt_guide", email="mgmt@example.com", password="secret123"
        )
        self.guide = GuideProfile.objects.create(user=self.guide_user, location="Tiranë")

        self.other_guide_user = User.objects.create_user(
            username="mgmt_other", email="other@example.com", password="secret123"
        )
        self.other_guide = GuideProfile.objects.create(user=self.other_guide_user, location="Vlorë")

        self.tourist_user = User.objects.create_user(
            username="mgmt_tourist", password="secret123"
        )
        TouristProfile.objects.create(user=self.tourist_user)

        self.tour_type = TourType.objects.create(name="Hiking", description="Test")
        self.tour = Tour.objects.create(
            guide=self.guide,
            title="Mgmt Tour",
            slug="mgmt-tour",
            short_description="Short description",
            full_description="Full description",
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
            currency="ALL",
            max_participants=10,
            min_participants=2,
            status="published",
            is_active=True,
            main_image=SimpleUploadedFile("mgmt.jpg", b"data", content_type="image/jpeg"),
        )

    def _create_payload(self, **overrides):
        data = {
            "title": "New Tour",
            "short_description": "Short description",
            "full_description": "Full description",
            "tour_type": self.tour_type.id,
            "difficulty": "easy",
            "age_group": "all",
            "languages": "sq",
            "meeting_point": "Qendra",
            "location_city": "Tiranë",
            "location_region": "Tiranë",
            "duration_hours": 4,
            "duration_days": 0,
            "price_per_person": 100,
            "currency": "ALL",
            "max_participants": 10,
            "min_participants": 2,
            "date": "2030-06-01",
            "time_start": "10:00",
            "time_end": "14:00",
            "main_image": self._png_image(),
        }
        data.update(overrides)
        return data

    def test_guide_can_create_published_tour(self):
        self.client.force_login(self.guide_user)
        response = self.client.post(reverse("tours:create_tour"), self._create_payload())
        self.assertEqual(response.status_code, 302)
        tour = Tour.objects.get(title="New Tour")
        self.assertEqual(tour.guide, self.guide)
        self.assertEqual(tour.status, "published")

    def test_tourist_cannot_create_tour(self):
        self.client.force_login(self.tourist_user)
        response = self.client.post(reverse("tours:create_tour"), self._create_payload())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:guide_profile_edit"), response.url)
        self.assertFalse(Tour.objects.filter(title="New Tour").exists())

    def test_anonymous_cannot_create_tour(self):
        response = self.client.post(reverse("tours:create_tour"), self._create_payload())
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Tour.objects.filter(title="New Tour").exists())

    def test_create_tour_rejects_past_date(self):
        self.client.force_login(self.guide_user)
        response = self.client.post(
            reverse("tours:create_tour"), self._create_payload(date="2020-01-01")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tour.objects.filter(title="New Tour").exists())

    def test_edit_tour_without_slug_does_not_crash(self):
        # REGRESSION: fusha 'slug' është disabled; një POST që nuk e përfshin
        # nuk duhet ta zbrazë slug-un as të kthejë 500 në ri-rendim.
        self.client.force_login(self.guide_user)
        payload = {
            "title": "Updated Tour",
            "short_description": "Short",
            "full_description": "Full",
            "tour_type": self.tour_type.id,
            "difficulty": "moderate",
            "age_group": "all",
            "languages": "sq",
            "meeting_point": "Qendra",
            "location_city": "Tiranë",
            "location_region": "Tiranë",
            "duration_hours": 5,
            "duration_days": 0,
            "price_per_person": 120,
            "currency": "ALL",
            "max_participants": 12,
            "min_participants": 2,
            "date": "2030-01-01",
            "time_start": "10:00",
            "time_end": "15:00",
            "cancellation_deadline_hours": 48,
            "refund_percentage": 100,
            "status": "published",
        }
        response = self.client.post(
            reverse("tours:edit_tour", args=[self.tour.slug]), payload
        )
        self.assertEqual(response.status_code, 302)
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.slug, "mgmt-tour")

    def test_guide_can_edit_own_tour(self):
        self.client.force_login(self.guide_user)
        response = self.client.post(
            reverse("tours:edit_tour", args=[self.tour.slug]),
            {
                "title": "Updated Tour",
                "short_description": "Short",
                "full_description": "Full",
                "tour_type": self.tour_type.id,
                "difficulty": "moderate",
                "age_group": "all",
                "languages": "sq",
                "meeting_point": "Qendra",
                "location_city": "Tiranë",
                "location_region": "Tiranë",
                "duration_hours": 5,
                "duration_days": 0,
                "price_per_person": 120,
                "currency": "ALL",
                "max_participants": 12,
                "min_participants": 2,
                "date": "2030-01-01",
                "time_start": "10:00",
                "time_end": "15:00",
                "cancellation_deadline_hours": 48,
                "refund_percentage": 100,
                "status": "published",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.title, "Updated Tour")
        self.assertEqual(self.tour.difficulty, "moderate")

    def test_guide_cannot_edit_other_guides_tour(self):
        self.client.force_login(self.other_guide_user)
        response = self.client.post(
            reverse("tours:edit_tour", args=[self.tour.slug]),
            {"title": "Hacked"},
        )
        self.assertEqual(response.status_code, 403)

    def test_tourist_cannot_edit_tour(self):
        self.client.force_login(self.tourist_user)
        response = self.client.get(reverse("tours:edit_tour", args=[self.tour.slug]))
        self.assertEqual(response.status_code, 403)

    def test_guide_can_delete_own_tour(self):
        self.client.force_login(self.guide_user)
        response = self.client.post(reverse("tours:delete_tour", args=[self.tour.slug]))
        self.assertRedirects(response, reverse("tours:my_tours"))
        self.assertFalse(Tour.objects.filter(slug="mgmt-tour").exists())

    def test_guide_cannot_delete_other_guides_tour(self):
        self.client.force_login(self.other_guide_user)
        response = self.client.post(reverse("tours:delete_tour", args=[self.tour.slug]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Tour.objects.filter(slug="mgmt-tour").exists())

    def test_my_tours_lists_only_own_tours(self):
        Tour.objects.create(
            guide=self.other_guide,
            title="Other Guide Tour",
            slug="other-guide-tour",
            short_description="Short",
            full_description="Full",
            tour_type=self.tour_type,
            difficulty="easy",
            age_group="all",
            languages="sq",
            meeting_point="Qendra",
            location_city="Vlorë",
            location_region="Vlorë",
            duration_hours=4,
            date="2030-02-01",
            time_start="10:00:00",
            price_per_person=80,
            max_participants=8,
            min_participants=1,
            status="published",
            is_active=True,
        )
        self.client.force_login(self.guide_user)
        response = self.client.get(reverse("tours:my_tours"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mgmt Tour")
        self.assertNotContains(response, "Other Guide Tour")

    def test_guide_can_update_pricing(self):
        self.client.force_login(self.guide_user)
        response = self.client.post(
            reverse("tours:edit_tour_pricing", args=[self.tour.slug]),
            {
                "price_per_person": 150,
                "currency": "ALL",
                "max_participants": 10,
                "min_participants": 2,
                "early_bird_days": 0,
                "early_bird_discount": 0,
            },
        )
        self.assertRedirects(response, reverse("tours:tour_detail", args=[self.tour.slug]))
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.price_per_person, 150)

    def test_other_guide_cannot_update_pricing(self):
        self.client.force_login(self.other_guide_user)
        response = self.client.post(
            reverse("tours:edit_tour_pricing", args=[self.tour.slug]),
            {"price_per_person": 150, "currency": "ALL"},
        )
        self.assertEqual(response.status_code, 403)


class TourRepublishTests(TestCase):
    """Ripublikimi i një turi të përfunduar për datë të re.

    Nga realizimi i mëparshëm duhen ruajtur vetëm vlerësimet (reviews):
    prenotimet dhe pagesat fshihen, vendet dhe numëruesit rikthehen.
    """

    def setUp(self):
        self.guide_user = User.objects.create_user(
            username="repub_guide", email="repub@example.com", password="secret123"
        )
        self.guide = GuideProfile.objects.create(user=self.guide_user, location="Tiranë")

        self.other_guide_user = User.objects.create_user(
            username="repub_other", email="repub_other@example.com", password="secret123"
        )
        GuideProfile.objects.create(user=self.other_guide_user, location="Vlorë")

        self.tourist_user = User.objects.create_user(
            username="repub_tourist", email="repub_tourist@example.com", password="secret123"
        )
        self.tourist = TouristProfile.objects.create(user=self.tourist_user)

        self.second_tourist_user = User.objects.create_user(
            username="repub_tourist2", email="repub_tourist2@example.com", password="secret123"
        )
        self.second_tourist = TouristProfile.objects.create(user=self.second_tourist_user)

        self.tour_type = TourType.objects.create(name="Repub Type", description="Test")
        self.past_date = timezone.now().date() - timedelta(days=7)
        self.new_date = timezone.now().date() + timedelta(days=30)

        self.tour = Tour.objects.create(
            guide=self.guide,
            title="Repub Tour",
            slug="repub-tour",
            short_description="Short description",
            full_description="Full description",
            tour_type=self.tour_type,
            difficulty="easy",
            age_group="all",
            languages="sq",
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date=self.past_date,
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            min_participants=2,
            status="completed",
            is_active=True,
            main_image=SimpleUploadedFile("repub.jpg", b"data", content_type="image/jpeg"),
        )

        # Prenotim i konfirmuar nga realizimi i mëparshëm (+ review mbi prenotim)
        self.booking = Booking.objects.create(
            tourist=self.tourist,
            tour=self.tour,
            num_people=2,
        )
        self.booking.confirm()
        self.booking_review = BookingReview.objects.create(
            booking=self.booking,
            rating=5,
            comment="Eksperiencë e mrekullueshme!",
        )

        # Review direkt mbi tur nga një turist tjetër
        self.tour_review = TourReview.objects.create(
            tour=self.tour,
            tourist=self.second_tourist,
            rating=4,
            comment="Shumë mirë",
        )

    def test_model_republish_keeps_only_reviews(self):
        result = self.tour.republish_for_new_date(self.new_date)

        self.assertEqual(result.status, "published")
        self.assertEqual(result.date, self.new_date)
        self.assertTrue(result.is_active)

        # Prenotimet (dhe pagesat) e realizimit të vjetër fshihen
        self.assertEqual(self.tour.bookings.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)

        # Review-et e turit ruhen
        self.assertTrue(
            TourReview.objects.filter(pk=self.tour_review.pk).exists()
        )

        # Review-i i bërë mbi prenotim transferohet si review turi
        transferred = TourReview.objects.filter(tourist=self.tourist).first()
        self.assertIsNotNone(transferred)
        self.assertEqual(transferred.rating, 5)
        self.assertEqual(transferred.comment, "Eksperiencë e mrekullueshme!")
        self.assertTrue(transferred.is_verified)
        self.assertFalse(BookingReview.objects.exists())

        # Vendet rikthehen, numëruesit zerojohen
        self.assertEqual(self.tour.available_spots, 10)
        self.assertEqual(self.tour.booking_count, 0)
        self.assertIsNone(self.tour.last_booking_at)

    def test_model_republish_updates_start_time(self):
        from datetime import time

        result = self.tour.republish_for_new_date(self.new_date, new_time_start=time(9, 30))
        self.assertEqual(result.time_start, time(9, 30))

    def test_model_republish_rejects_past_new_date(self):
        past = timezone.now().date() - timedelta(days=1)
        with self.assertRaises(ValueError):
            self.tour.republish_for_new_date(past)

    def test_model_republish_rejects_unfinished_tour(self):
        self.tour.status = "published"
        self.tour.date = timezone.now().date() + timedelta(days=5)
        self.tour.save(update_fields=["status", "date"])

        with self.assertRaises(ValueError):
            self.tour.republish_for_new_date(self.new_date)

    def test_api_republish_success(self):
        self.client.force_login(self.guide_user)
        response = self.client.post(
            reverse("tours:republish_tour"),
            data=json.dumps({"tour_id": self.tour.id, "new_date": self.new_date.isoformat()}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["new_date"], self.new_date.isoformat())

        self.tour.refresh_from_db()
        self.assertEqual(self.tour.status, "published")
        self.assertEqual(self.tour.date, self.new_date)
        self.assertEqual(self.tour.bookings.count(), 0)
        self.assertEqual(TourReview.objects.count(), 2)

    def test_api_republish_requires_authentication(self):
        response = self.client.post(
            reverse("tours:republish_tour"),
            data=json.dumps({"tour_id": self.tour.id, "new_date": self.new_date.isoformat()}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_api_republish_forbidden_for_non_guide(self):
        self.client.force_login(self.tourist_user)
        response = self.client.post(
            reverse("tours:republish_tour"),
            data=json.dumps({"tour_id": self.tour.id, "new_date": self.new_date.isoformat()}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_api_republish_cannot_touch_other_guides_tour(self):
        self.client.force_login(self.other_guide_user)
        response = self.client.post(
            reverse("tours:republish_tour"),
            data=json.dumps({"tour_id": self.tour.id, "new_date": self.new_date.isoformat()}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.status, "completed")

    def test_api_republish_rejects_missing_or_bad_date(self):
        self.client.force_login(self.guide_user)

        missing = self.client.post(
            reverse("tours:republish_tour"),
            data=json.dumps({"tour_id": self.tour.id}),
            content_type="application/json",
        )
        self.assertEqual(missing.status_code, 400)

        bad_format = self.client.post(
            reverse("tours:republish_tour"),
            data=json.dumps({"tour_id": self.tour.id, "new_date": "01-02-2030"}),
            content_type="application/json",
        )
        self.assertEqual(bad_format.status_code, 400)
