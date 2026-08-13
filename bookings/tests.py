import threading
from concurrent.futures import ThreadPoolExecutor

from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError
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


class BookingConcurrencyTests(TransactionTestCase):
	def setUp(self):
		self.user_guide = User.objects.create_user(
			username="guide_concurrency",
			password="pass1234",
			first_name="Guide",
			email="guide_concurrency@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.user_guide, location="Tiranë")

		self.tour_type = TourType.objects.create(name="Nature", description="Test")
		image = SimpleUploadedFile(
			"tour.jpg",
			b"fake-image-content",
			content_type="image/jpeg",
		)
		self.tour = Tour.objects.create(
			guide=self.guide_profile,
			title="Concurrency Tour",
			slug="concurrency-tour",
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
			max_participants=1,
			main_image=image,
			status="published",
			is_active=True,
		)
		self.tour.available_spots = 1
		self.tour.save(update_fields=['available_spots'])

	def test_only_one_booking_can_use_the_last_available_spot(self):
		barrier = threading.Barrier(2)
		results = []

		def create_booking_for_user(username):
			user = User.objects.create_user(
				username=username,
				password="pass1234",
				first_name="Tourist",
				email=f"{username}@example.com",
			)
			tourist = TouristProfile.objects.create(user=user)
			barrier.wait()
			try:
				Booking.objects.create(
					tourist=tourist,
					tour=self.tour,
					num_people=1,
				)
				results.append("success")
			except ValueError:
				results.append("failed")

		with ThreadPoolExecutor(max_workers=2) as executor:
			executor.submit(create_booking_for_user, "tourist_one")
			executor.submit(create_booking_for_user, "tourist_two")

		self.assertEqual(results.count("success"), 1)
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 0)


class BookingDatabaseIntegrityTests(TransactionTestCase):
	def setUp(self):
		self.user_guide = User.objects.create_user(
			username="guide_db_integrity",
			password="pass1234",
			first_name="Guide",
			email="guide_db_integrity@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.user_guide, location="Tiranë")

		self.tour_type = TourType.objects.create(name="Nature", description="Test")
		image = SimpleUploadedFile(
			"tour.jpg",
			b"fake-image-content",
			content_type="image/jpeg",
		)
		self.tour = Tour.objects.create(
			guide=self.guide_profile,
			title="Integrity Tour",
			slug="integrity-tour",
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
		self.tour.available_spots = 10
		self.tour.save(update_fields=['available_spots'])

	def test_tour_available_spots_cannot_be_negative(self):
		self.tour.available_spots = -1
		with self.assertRaises(IntegrityError):
			self.tour.save(update_fields=['available_spots'])

	def test_booking_num_people_must_be_positive(self):
		user = User.objects.create_user(username="tourist_integrity", password="pass1234", email="tourist_integrity@example.com")
		tourist = TouristProfile.objects.create(user=user)
		with self.assertRaises(IntegrityError):
			Booking.objects.create(
				tourist=tourist,
				tour=self.tour,
				num_people=0,
			)

	def test_duplicate_active_booking_per_tourist_tour_is_rejected(self):
		user = User.objects.create_user(username="tourist_integrity_dupe", password="pass1234", email="tourist_integrity_dupe@example.com")
		tourist = TouristProfile.objects.create(user=user)
		Booking.objects.create(tourist=tourist, tour=self.tour, num_people=1)

		with self.assertRaises(IntegrityError):
			Booking.objects.create(tourist=tourist, tour=self.tour, num_people=1)


class BookingCancellationLogicTests(TestCase):
	def setUp(self):
		self.guide_user = User.objects.create_user(
			username="guide_cancel_test",
			password="pass1234",
			first_name="Guide",
			email="guide_cancel_test@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.guide_user, location="Tiranë")

		self.tourist_user = User.objects.create_user(
			username="tourist_cancel_test",
			password="pass1234",
			first_name="Tourist",
			email="tourist_cancel_test@example.com",
		)
		self.tourist_profile = TouristProfile.objects.create(user=self.tourist_user)

		self.other_tourist_user = User.objects.create_user(
			username="other_tourist_cancel_test",
			password="pass1234",
			first_name="Other",
			email="other_tourist_cancel_test@example.com",
		)
		self.other_tourist_profile = TouristProfile.objects.create(user=self.other_tourist_user)

		self.tour_type = TourType.objects.create(name="Nature", description="Test")
		self.tour = Tour.objects.create(
			guide=self.guide_profile,
			title="Cancellation Logic Tour",
			slug="cancellation-logic-tour",
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
		self.tour.available_spots = 10
		self.tour.save(update_fields=['available_spots'])

	def test_cancelled_booking_does_not_restore_spots_twice(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=2,
		)
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 8)

		booking.cancel(cancelled_by="tourist", notes="")
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 10)

		with self.assertRaises(ValueError):
			booking.cancel(cancelled_by="tourist", notes="")

		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 10)

	def test_delete_active_booking_restores_available_spots(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=3,
		)
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 7)

		booking.delete()
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 10)

	def test_complete_status_requires_confirmed_booking(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=1,
		)

		with self.assertRaises(ValueError):
			booking.complete()

	def test_mark_no_show_requires_confirmed_booking(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=1,
		)

		with self.assertRaises(ValueError):
			booking.mark_no_show()

	def test_pending_to_completed_is_invalid_transition(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=1,
		)

		booking.status = "completed"
		with self.assertRaises(ValueError):
			booking.save(update_fields=['status'])

	def test_cancelled_to_confirmed_is_invalid_transition(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=1,
		)
		booking.cancel(cancelled_by="tourist")

		booking.status = "confirmed"
		with self.assertRaises(ValueError):
			booking.save(update_fields=['status'])

	def test_confirmed_to_completed_is_valid_transition(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=1,
		)
		booking.confirm()
		booking.complete()

		booking.refresh_from_db()
		self.assertEqual(booking.status, "completed")

	def test_tourist_cannot_cancel_another_tourists_booking(self):
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=1,
		)

		self.client.login(username="other_tourist_cancel_test", password="pass1234")
		response = self.client.get(reverse("bookings:booking_cancel", args=[booking.id]))

		self.assertEqual(response.status_code, 403)

	def test_guide_cannot_manage_foreign_booking(self):
		other_guide_user = User.objects.create_user(
			username="other_guide_cancel_test",
			password="pass1234",
			first_name="Other Guide",
			email="other_guide_cancel_test@example.com",
		)
		other_guide_profile = GuideProfile.objects.create(user=other_guide_user, location="Shkodër")
		other_tour = Tour.objects.create(
			guide=other_guide_profile,
			title="Other Guide Tour",
			slug="other-guide-tour",
			short_description="Short description",
			full_description="Full description",
			tour_type=self.tour_type,
			meeting_point="Shkodër",
			location_city="Shkodër",
			location_region="Shkodër",
			duration_hours=4,
			date="2030-01-02",
			time_start="09:00:00",
			price_per_person=100,
			max_participants=8,
			status="published",
			is_active=True,
		)
		booking = Booking.objects.create(
			tourist=self.tourist_profile,
			tour=other_tour,
			num_people=1,
		)

		self.client.login(username="guide_cancel_test", password="pass1234")
		response = self.client.post(reverse("users:guide_booking_cancel", args=[booking.id]))

		self.assertEqual(response.status_code, 403)


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

	def test_guide_complete_action_marks_confirmed_booking_completed(self):
		booking = self._create_booking()
		booking.confirm()

		self.client.login(username="guide_int", password="pass1234")
		url = reverse("users:guide_booking_complete", args=[booking.id])
		response = self.client.post(url, follow=True)

		self.assertEqual(response.status_code, 200)
		booking.refresh_from_db()
		self.assertEqual(booking.status, "completed")

	def test_guide_complete_action_does_not_complete_pending_booking(self):
		booking = self._create_booking()

		self.client.login(username="guide_int", password="pass1234")
		url = reverse("users:guide_booking_complete", args=[booking.id])
		response = self.client.post(url, follow=True)

		self.assertEqual(response.status_code, 200)
		booking.refresh_from_db()
		self.assertEqual(booking.status, "pending")
