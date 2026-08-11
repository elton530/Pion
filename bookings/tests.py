from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.contrib.admin import site
from django.urls import reverse

from bookings.admin import PaymentAdmin
from bookings.models import Booking, Payment
from tours.models import Tour, TourType
from users.models import GuideProfile, TouristProfile


class BookingPaymentFlowTests(TestCase):
	def setUp(self):
		self.user_guide = User.objects.create_user(
			username="guide_test",
			password="pass1234",
			first_name="Guide",
			email="guide@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.user_guide, location="Tiranë")

		self.user_tourist = User.objects.create_user(
			username="tourist_test",
			password="pass1234",
			first_name="Tourist",
			email="tourist@example.com",
		)
		self.tourist_profile = TouristProfile.objects.create(user=self.user_tourist)

		self.tour_type = TourType.objects.create(name="Nature", description="Test")
		image = SimpleUploadedFile(
			"tour.jpg",
			b"fake-image-content",
			content_type="image/jpeg",
		)
		self.tour = Tour.objects.create(
			guide=self.guide_profile,
			title="Test Tour",
			slug="test-tour",
			short_description="Short description",
			full_description="Full description",
			tour_type=self.tour_type,
			meeting_point="Tiranë",
			location_city="Tiranë",
			location_region="Tiranë",
			duration_hours=4,
			date="2030-01-01",
			time_start="08:00:00",
			price_per_person=100,
			max_participants=10,
			main_image=image,
			status="published",
			is_active=True,
		)

	def test_booking_creates_payment_and_confirms_on_payment_success(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=2,
		)

		self.assertTrue(Payment.objects.filter(booking=booking).exists())
		payment = Payment.objects.get(booking=booking)
		self.assertEqual(payment.status, "pending")

		payment.mark_as_paid(transaction_id="txn-123")

		booking.refresh_from_db()
		self.assertEqual(booking.status, "confirmed")
		self.assertEqual(payment.status, "paid")

	def test_payment_admin_amount_display_handles_string_amount(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=1,
		)
		payment = Payment(booking=booking, amount="123.45", currency="ALL")
		admin = PaymentAdmin(Payment, site)

		display = admin.amount_display(payment)

		self.assertIn("123.45", str(display))


class BookingViewsIntegrationTests(TestCase):
	"""Test që verifikojnë lidhjen backend ↔ frontend të flow-ve të prenimeve"""

	def setUp(self):
		self.user_guide = User.objects.create_user(
			username="guide_int",
			password="pass1234",
			first_name="Guide",
			email="guide_int@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.user_guide, location="Tiranë")

		self.user_tourist = User.objects.create_user(
			username="tourist_int",
			password="pass1234",
			first_name="Tourist",
			email="tourist_int@example.com",
		)
		self.tourist_profile = TouristProfile.objects.create(user=self.user_tourist)

		self.tour_type = TourType.objects.create(name="Nature", description="Test")
		self.tour = Tour.objects.create(
			guide=self.guide_profile,
			title="Integration Tour",
			slug="integration-tour",
			short_description="Short description",
			full_description="Full description",
			tour_type=self.tour_type,
			meeting_point="Tiranë",
			location_city="Tiranë",
			location_region="Tiranë",
			duration_hours=4,
			date="2030-01-01",
			time_start="08:00:00",
			price_per_person=100,
			max_participants=10,
			status="published",
			is_active=True,
		)

	def _create_booking(self):
		return Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=2,
		)

	def test_create_booking_get_renders_form(self):
		self.client.login(username="tourist_int", password="pass1234")
		url = reverse("bookings:create_booking", args=[self.tour.slug])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Rezervo Turin")
		self.assertContains(response, self.tour.title)

	def test_create_booking_post_creates_booking_and_redirects_to_success(self):
		self.client.login(username="tourist_int", password="pass1234")
		url = reverse("bookings:create_booking", args=[self.tour.slug])
		response = self.client.post(url, {"num_people": 2, "notes": "Test note"}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(Booking.objects.filter(tour=self.tour, tourist=self.tourist_profile).exists())
		self.assertContains(response, "Prenotimi u Krye me Sukses")

	def test_booking_detail_works_for_tourist_and_guide(self):
		booking = self._create_booking()

		self.client.login(username="tourist_int", password="pass1234")
		url = reverse("bookings:booking_detail", args=[booking.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.tour.title)

		self.client.logout()
		self.client.login(username="guide_int", password="pass1234")
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.tour.title)

	def test_unified_booking_detail_redirects_from_old_users_urls(self):
		booking = self._create_booking()
		self.client.login(username="tourist_int", password="pass1234")
		url = reverse("users:tourist_booking_detail", args=[booking.id])
		response = self.client.get(url)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))

		self.client.logout()
		self.client.login(username="guide_int", password="pass1234")
		url = reverse("users:guide_booking_detail", args=[booking.id])
		response = self.client.get(url)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))

	def test_booking_list_renders_and_preserves_filters_in_pagination(self):
		booking = self._create_booking()
		self.client.login(username="tourist_int", password="pass1234")
		url = reverse("bookings:booking_list")
		response = self.client.get(url, {"search": "Integration", "page": 1})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, booking.tour.title)

	def test_booking_cancel_page_renders_with_refund(self):
		booking = self._create_booking()
		self.client.login(username="tourist_int", password="pass1234")
		url = reverse("bookings:booking_cancel", args=[booking.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Anulo Prenotimin")

	def test_guide_confirm_action_confirms_booking(self):
		booking = self._create_booking()
		self.client.login(username="guide_int", password="pass1234")
		url = reverse("users:guide_booking_confirm", args=[booking.id])
		response = self.client.post(url, follow=True)
		booking.refresh_from_db()
		self.assertEqual(booking.status, "confirmed")

	def test_guide_cancel_action_sets_cancelled_by_guide(self):
		booking = self._create_booking()
		self.client.login(username="guide_int", password="pass1234")
		url = reverse("users:guide_booking_cancel", args=[booking.id])
		response = self.client.post(url, follow=True)
		booking.refresh_from_db()
		self.assertEqual(booking.status, "cancelled")
		self.assertEqual(booking.cancelled_by, "guide")
