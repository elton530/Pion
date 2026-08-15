import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.contrib.admin import site
from django.urls import reverse
from django.utils import timezone

from bookings.admin import PaymentAdmin
from bookings.models import Booking, Payment, BookingReview
from bookings.views import (
    send_booking_confirmation_email_to_tourist,
    send_cancellation_email,
    send_new_booking_email_to_guide,
)
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
	"""Test që verifikojnë lidhjen backend ↔ frontend të flow-ve të prenotimeve"""

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


class BookingEmailTests(TestCase):
	"""Teste për email-et e prenotimeve, pagesave dhe anulimeve."""

	def setUp(self):
		mail.outbox.clear()

		self.user_guide = User.objects.create_user(
			username="guide_email",
			password="pass1234",
			first_name="Guide",
			email="guide_email@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.user_guide, location="Tiranë")

		self.user_tourist = User.objects.create_user(
			username="tourist_email",
			password="pass1234",
			first_name="Tourist",
			email="tourist_email@example.com",
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
			title="Email Tour",
			slug="email-tour",
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

	def _create_booking(self):
		return Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=2,
		)

	def test_new_booking_sends_email_to_guide(self):
		booking = self._create_booking()
		mail.outbox.clear()

		send_new_booking_email_to_guide(booking)

		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertIn("guide_email@example.com", email.to)
		self.assertIn("Prenotim i ri", email.subject)

	def test_new_booking_sends_confirmation_email_to_tourist(self):
		booking = self._create_booking()
		mail.outbox.clear()

		send_booking_confirmation_email_to_tourist(booking)

		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertIn("tourist_email@example.com", email.to)
		self.assertIn("Prenotimit", email.subject)

	def test_cancellation_sends_email_to_tourist(self):
		booking = self._create_booking()
		mail.outbox.clear()

		# Real flow: the booking is cancelled first, then the email is sent.
		booking.cancel(cancelled_by="tourist")
		send_cancellation_email(booking)

		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertIn("tourist_email@example.com", email.to)
		self.assertIn("Anulim", email.subject)

	def test_paid_payment_sends_confirmation_email(self):
		booking = self._create_booking()
		payment = Payment.objects.get(booking=booking)
		mail.outbox.clear()

		payment.mark_as_paid(transaction_id="txn-email-1")

		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertIn("tourist_email@example.com", email.to)
		self.assertIn("Pagesa u konfirmua", email.subject)

	def test_failed_payment_sends_failure_email(self):
		booking = self._create_booking()
		payment = Payment.objects.get(booking=booking)
		mail.outbox.clear()

		payment.mark_as_failed()

		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertIn("tourist_email@example.com", email.to)
		self.assertIn("Pagesa dështoi", email.subject)

	def test_booking_helpers_do_not_send_real_emails(self):
		# The locmem backend collects emails locally; no real SMTP connection
		# is attempted during tests.
		from django.core.mail.backends.locmem import EmailBackend

		self.assertIsInstance(mail.get_connection(), EmailBackend)


class TouristBookingWorkflowTests(TestCase):
	"""Workflow i turistit: krijimi, shikimi, anulimi i prenotimeve, gabime e skaje."""

	def setUp(self):
		mail.outbox.clear()

		self.user_guide = User.objects.create_user(
			username="guide_wf", password="pass1234", email="guide_wf@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.user_guide, location="Tiranë")

		self.user_tourist = User.objects.create_user(
			username="tourist_wf", password="pass1234", email="tourist_wf@example.com",
		)
		self.tourist_profile = TouristProfile.objects.create(user=self.user_tourist)

		self.user_other = User.objects.create_user(
			username="other_wf", password="pass1234", email="other_wf@example.com",
		)
		self.other_tourist_profile = TouristProfile.objects.create(user=self.user_other)

		self.tour_type = TourType.objects.create(name="Nature", description="Test")
		self.tour = Tour.objects.create(
			guide=self.guide_profile,
			title="Workflow Tour",
			slug="workflow-tour",
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
			currency="ALL",
			max_participants=10,
			min_participants=2,
			status="published",
			is_active=True,
		)

	def _create_booking(self, num_people=2):
		return Booking.objects.create(
			tourist=self.tourist_profile,
			tour=self.tour,
			num_people=num_people,
		)

	def test_anonymous_redirected_to_login_for_booking(self):
		response = self.client.get(reverse("bookings:create_booking", args=[self.tour.slug]))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse("users:login"), response.url)

	def test_guide_cannot_create_booking(self):
		self.client.login(username="guide_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:create_booking", args=[self.tour.slug]), {"num_people": 1}
		)
		self.assertRedirects(response, reverse("tours:tour_detail", args=[self.tour.slug]))
		self.assertFalse(Booking.objects.filter(tour=self.tour).exists())

	def test_duplicate_booking_redirects_to_existing(self):
		booking = self._create_booking()
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.get(reverse("bookings:create_booking", args=[self.tour.slug]))
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))

	def test_cannot_book_full_tour(self):
		self.tour.available_spots = 0
		self.tour.save(update_fields=["available_spots"])
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.get(reverse("bookings:create_booking", args=[self.tour.slug]))
		self.assertRedirects(response, reverse("tours:tour_detail", args=[self.tour.slug]))
		self.assertFalse(Booking.objects.filter(tour=self.tour).exists())

	def test_cannot_book_draft_tour(self):
		self.tour.status = "draft"
		self.tour.save(update_fields=["status"])
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.get(reverse("bookings:create_booking", args=[self.tour.slug]))
		self.assertEqual(response.status_code, 404)

	def test_cannot_book_past_tour(self):
		self.tour.date = "2020-01-01"
		self.tour.save(update_fields=["date"])
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.get(reverse("bookings:create_booking", args=[self.tour.slug]))
		self.assertRedirects(response, reverse("tours:tour_detail", args=[self.tour.slug]))
		self.assertFalse(Booking.objects.filter(tour=self.tour).exists())

	def test_booking_num_people_exceeding_spots_rejected(self):
		self.tour.available_spots = 2
		self.tour.save(update_fields=["available_spots"])
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:create_booking", args=[self.tour.slug]), {"num_people": 5}
		)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(Booking.objects.filter(tour=self.tour).exists())

	def test_full_booking_creation_flow(self):
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:create_booking", args=[self.tour.slug]),
			{"num_people": 2, "notes": "Shënim test"},
		)
		self.assertEqual(response.status_code, 302)
		booking = Booking.objects.get(tour=self.tour, tourist=self.tourist_profile)
		self.assertEqual(booking.status, "pending")
		self.assertEqual(booking.num_people, 2)
		self.assertEqual(booking.total_price, 200)
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 8)

	def test_booking_creation_sends_notifications(self):
		self.client.login(username="tourist_wf", password="pass1234")
		self.client.post(
			reverse("bookings:create_booking", args=[self.tour.slug]), {"num_people": 2}
		)
		recipients = {email.to[0] for email in mail.outbox}
		self.assertIn("guide_wf@example.com", recipients)
		self.assertIn("tourist_wf@example.com", recipients)

	def test_booking_success_page_denied_for_other_user(self):
		booking = self._create_booking()
		self.client.login(username="other_wf", password="pass1234")
		response = self.client.get(reverse("bookings:booking_success", args=[booking.id]))
		self.assertEqual(response.status_code, 403)

	def test_booking_detail_denied_for_third_party(self):
		booking = self._create_booking()
		self.client.login(username="other_wf", password="pass1234")
		response = self.client.get(reverse("bookings:booking_detail", args=[booking.id]))
		self.assertEqual(response.status_code, 403)

	def test_booking_cancel_full_flow(self):
		booking = self._create_booking()
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:booking_cancel", args=[booking.id]),
			{"cancellation_reason": "personal", "notes": "Nuk mundem", "confirm": "on"},
		)
		self.assertRedirects(response, reverse("users:tourist_dashboard"))
		booking.refresh_from_db()
		self.assertEqual(booking.status, "cancelled")
		self.assertEqual(booking.cancelled_by, "tourist")
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 10)

	def test_booking_cancel_rejected_after_deadline(self):
		booking = self._create_booking()
		self.tour.cancellation_deadline_hours = 72
		self.tour.date = timezone.now().date() + timedelta(days=2)
		self.tour.save(update_fields=["cancellation_deadline_hours", "date"])
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:booking_cancel", args=[booking.id]),
			{"cancellation_reason": "personal"},
		)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))
		booking.refresh_from_db()
		self.assertEqual(booking.status, "pending")

	def test_booking_edit_only_for_own_pending_booking(self):
		booking = self._create_booking()
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:booking_edit", args=[booking.id]),
			{"num_people": 3, "notes": "Shënim i ri", "special_requirements": "Në dietë"},
		)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))
		booking.refresh_from_db()
		self.assertEqual(booking.num_people, 2)
		self.assertEqual(booking.notes, "Shënim i ri")
		self.assertEqual(booking.special_requirements, "Në dietë")

		booking.confirm()
		response = self.client.post(
			reverse("bookings:booking_edit", args=[booking.id]),
			{"notes": "Nuk duhej aplikuar"},
		)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))
		booking.refresh_from_db()
		self.assertEqual(booking.notes, "Shënim i ri")

	def test_booking_edit_denied_for_other_tourist(self):
		booking = self._create_booking()
		self.client.login(username="other_wf", password="pass1234")
		response = self.client.get(reverse("bookings:booking_edit", args=[booking.id]))
		self.assertEqual(response.status_code, 403)

	def test_booking_list_denied_for_guide(self):
		self.client.login(username="guide_wf", password="pass1234")
		response = self.client.get(reverse("bookings:booking_list"))
		self.assertRedirects(response, reverse("core:home"))

	def test_booking_review_requires_completed_own_booking(self):
		booking = self._create_booking()
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:create_booking_review", args=[booking.id]),
			{"rating": 5, "comment": "Komenti"},
		)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))
		self.assertFalse(BookingReview.objects.filter(booking=booking).exists())

	def test_booking_review_after_completed_tour(self):
		booking = self._create_booking()
		booking.confirm()
		booking.complete()
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:create_booking_review", args=[booking.id]),
			{"rating": 5, "comment": "Tur i shkëlqyer"},
		)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))
		self.assertTrue(BookingReview.objects.filter(booking=booking, rating=5).exists())

	def test_booking_review_denied_for_other_tourist(self):
		booking = self._create_booking()
		booking.confirm()
		booking.complete()
		self.client.login(username="other_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:create_booking_review", args=[booking.id]),
			{"rating": 5, "comment": "Hacked"},
		)
		self.assertEqual(response.status_code, 403)
		self.assertFalse(BookingReview.objects.filter(booking=booking).exists())

	def test_confirm_participation_requires_confirmed_booking(self):
		booking = self._create_booking()
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:booking_confirm_participation", args=[booking.id])
		)
		self.assertRedirects(response, reverse("bookings:booking_detail", args=[booking.id]))
		self.assertFalse(booking.is_confirmed_24h)

	def test_confirm_participation_within_24h(self):
		booking = self._create_booking()
		booking.confirm()
		self.tour.date = timezone.now().date()
		self.tour.time_start = (timezone.now() + timedelta(hours=3)).time()
		self.tour.save(update_fields=["date", "time_start"])

		mail.outbox.clear()
		self.client.login(username="tourist_wf", password="pass1234")
		response = self.client.post(
			reverse("bookings:booking_confirm_participation", args=[booking.id]),
			{"confirm": "on"},
		)
		self.assertEqual(response.status_code, 302)
		booking.refresh_from_db()
		self.assertTrue(booking.is_confirmed_24h)
		recipients = {email.to[0] for email in mail.outbox}
		self.assertIn("guide_wf@example.com", recipients)


class GuideBookingManagementTests(TestCase):
	"""Workflow i guide-it: shikimi, konfirmimi, anulimi, përfundimi i prenotimeve."""

	def setUp(self):
		mail.outbox.clear()

		self.user_guide = User.objects.create_user(
			username="guide_mgmt", password="pass1234", email="guide_mgmt@example.com",
		)
		self.guide_profile = GuideProfile.objects.create(user=self.user_guide, location="Tiranë")

		self.user_other_guide = User.objects.create_user(
			username="guide_other", password="pass1234",
		)
		self.other_guide_profile = GuideProfile.objects.create(
			user=self.user_other_guide, location="Durrës"
		)

		self.user_tourist = User.objects.create_user(
			username="tourist_mgmt", password="pass1234", email="tourist_mgmt@example.com",
		)
		self.tourist_profile = TouristProfile.objects.create(user=self.user_tourist)

		self.tour_type = TourType.objects.create(name="Culture", description="Test")
		self.tour = Tour.objects.create(
			guide=self.guide_profile,
			title="Mgmt Tour",
			slug="mgmt-tour",
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
			currency="ALL",
			max_participants=10,
			min_participants=2,
			status="published",
			is_active=True,
		)

		self.other_tour = Tour.objects.create(
			guide=self.other_guide_profile,
			title="Other Tour",
			slug="other-tour",
			short_description="Short description",
			full_description="Full description",
			tour_type=self.tour_type,
			meeting_point="Durrës",
			location_city="Durrës",
			location_region="Durrës",
			duration_hours=4,
			date="2030-01-01",
			time_start="08:00:00",
			price_per_person=80,
			currency="ALL",
			max_participants=10,
			min_participants=2,
			status="published",
			is_active=True,
		)

	def _create_booking(self, tour=None):
		return Booking.objects.create(
			tourist=self.tourist_profile,
			tour=tour or self.tour,
			num_people=2,
		)

	def test_guide_booking_detail_denied_for_other_guide(self):
		booking = self._create_booking()
		self.client.login(username="guide_other", password="pass1234")
		response = self.client.get(reverse("users:guide_booking_detail", args=[booking.id]))
		self.assertEqual(response.status_code, 403)

	def test_guide_booking_action_confirm_flow(self):
		booking = self._create_booking()
		mail.outbox.clear()
		self.client.login(username="guide_mgmt", password="pass1234")
		response = self.client.post(
			reverse("users:guide_booking_confirm", args=[booking.id])
		)
		self.assertRedirects(response, reverse("users:guide_dashboard"))
		booking.refresh_from_db()
		self.assertEqual(booking.status, "confirmed")
		recipients = {email.to[0] for email in mail.outbox}
		self.assertIn("tourist_mgmt@example.com", recipients)

	def test_guide_booking_action_complete_requires_confirmed(self):
		booking = self._create_booking()
		self.client.login(username="guide_mgmt", password="pass1234")
		response = self.client.post(
			reverse("users:guide_booking_complete", args=[booking.id])
		)
		booking.refresh_from_db()
		self.assertEqual(booking.status, "pending")

		booking.confirm()
		response = self.client.post(
			reverse("users:guide_booking_complete", args=[booking.id])
		)
		booking.refresh_from_db()
		self.assertEqual(booking.status, "completed")

	def test_guide_booking_action_cancel_sends_email_and_restores_spots(self):
		booking = self._create_booking()
		booking.confirm()
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 8)

		self.client.login(username="guide_mgmt", password="pass1234")
		response = self.client.post(
			reverse("users:guide_booking_cancel", args=[booking.id])
		)
		self.assertRedirects(response, reverse("users:guide_dashboard"))
		booking.refresh_from_db()
		self.assertEqual(booking.status, "cancelled")
		self.assertEqual(booking.cancelled_by, "guide")
		self.tour.refresh_from_db()
		self.assertEqual(self.tour.available_spots, 10)
		recipients = {email.to[0] for email in mail.outbox}
		self.assertIn("tourist_mgmt@example.com", recipients)

	def test_guide_booking_action_denied_for_other_guide(self):
		booking = self._create_booking()
		self.client.login(username="guide_other", password="pass1234")
		response = self.client.post(
			reverse("users:guide_booking_confirm", args=[booking.id])
		)
		self.assertEqual(response.status_code, 403)
		booking.refresh_from_db()
		self.assertEqual(booking.status, "pending")

	def test_guide_booking_action_get_method_forbidden(self):
		booking = self._create_booking()
		self.client.login(username="guide_mgmt", password="pass1234")
		response = self.client.get(
			reverse("users:guide_booking_confirm", args=[booking.id])
		)
		self.assertEqual(response.status_code, 403)

	def test_guide_dashboard_denied_for_tourist(self):
		self.client.login(username="tourist_mgmt", password="pass1234")
		response = self.client.get(reverse("users:guide_dashboard"))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse("core:home"))


class AdminWorkflowTests(TestCase):
	"""Workflow i adminit: regjistrimet në admin dhe aksesi."""

	def setUp(self):
		self.admin_user = User.objects.create_user(
			username="root_admin", password="pass1234", is_staff=True, is_superuser=True
		)
		self.normal_user = User.objects.create_user(
			username="normal_user", password="pass1234",
		)

	def test_booking_admin_registered(self):
		self.assertIn(Booking, site._registry)

	def test_payment_admin_registered(self):
		self.assertIn(Payment, site._registry)

	def test_booking_review_admin_registered(self):
		self.assertIn(BookingReview, site._registry)

	def test_admin_index_requires_staff(self):
		self.client.login(username="normal_user", password="pass1234")
		response = self.client.get(reverse("admin:index"))
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse("admin:login"), response.url)

	def test_admin_index_accessible_for_staff(self):
		self.client.force_login(self.admin_user)
		response = self.client.get(reverse("admin:index"))
		self.assertEqual(response.status_code, 200)

	def test_admin_booking_changelist_accessible(self):
		self.client.force_login(self.admin_user)
		response = self.client.get(reverse("admin:bookings_booking_changelist"))
		self.assertEqual(response.status_code, 200)

	def test_admin_payment_changelist_accessible(self):
		self.client.force_login(self.admin_user)
		response = self.client.get(reverse("admin:bookings_payment_changelist"))
		self.assertEqual(response.status_code, 200)
