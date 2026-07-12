from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.contrib.admin import site

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
