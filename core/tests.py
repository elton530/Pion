import logging
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.utils import send_notification_email
from tour_platform.logging_config import SensitiveDataFilter
from tour_platform.security import DEVELOPMENT_SECRET_KEY_FALLBACK, resolve_secret_key


class SendNotificationEmailTests(TestCase):
    def setUp(self):
        mail.outbox.clear()

    def test_email_is_sent_through_configured_backend(self):
        # Django's test runner sets the locmem backend; the email must end up
        # in mail.outbox (not short-circuited by the helper).
        result = send_notification_email(
            "recipient@example.com",
            "Test Subject",
            message="Test message body",
        )

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Test Subject")
        self.assertIn("recipient@example.com", email.to)
        self.assertIn("Test message body", email.body)

    def test_email_accepts_recipient_list(self):
        result = send_notification_email(
            ["a@example.com", "b@example.com"],
            "Multi-recipient",
            message="Hello",
        )

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertCountEqual(mail.outbox[0].to, ["a@example.com", "b@example.com"])

    def test_email_with_html_template(self):
        user = User.objects.create_user(
            username="ardi", password="x", email="guide@example.com"
        )
        result = send_notification_email(
            "guide@example.com",
            "Template email",
            context={
                "user": user,
                "uid": "abc",
                "token": "token123",
                "protocol": "http",
                "domain": "testserver",
            },
            template_name="users/password_reset_email.html",
        )

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].body)

    def test_email_with_console_backend_does_not_send(self):
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
        ):
            result = send_notification_email(
                "console@example.com",
                "Console only",
                message="Should print to stdout, not send.",
            )

        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_returns_false(self):
        # A recipient with a newline is rejected (BadHeaderError) and the
        # helper must return False instead of raising.
        result = send_notification_email(
            "nobody@example.com\r\nBcc: attacker@example.com",
            "Subject",
            message="Body",
        )

        self.assertFalse(result)
        self.assertEqual(len(mail.outbox), 0)


class FooterLinkTests(TestCase):
    def test_footer_blog_link_points_to_faq_page(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(response, 'href="/pyetje-te-shpeshta/"')
        self.assertNotContains(response, 'href="#"')


class SecretKeyResolutionTests(SimpleTestCase):
    def test_production_requires_secret_key(self):
        with self.assertRaises(ImproperlyConfigured):
            resolve_secret_key(secret_key="", debug=False, environment="production")

    def test_development_allows_fallback_when_secret_key_missing(self):
        key = resolve_secret_key(secret_key="", debug=True, environment="development")
        self.assertEqual(key, DEVELOPMENT_SECRET_KEY_FALLBACK)

    def test_explicit_secret_key_is_used(self):
        key = resolve_secret_key(secret_key="custom-secret", debug=False, environment="production")
        self.assertEqual(key, "custom-secret")


class HealthEndpointTests(TestCase):
    def test_health_returns_200_when_application_works(self):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_does_not_require_authentication(self):
        # Test client is anonymous by default.
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("login", response["Content-Type"])

    @mock.patch("core.views.connection")
    def test_health_returns_503_when_database_unreachable(self, mock_connection):
        mock_connection.cursor.side_effect = OperationalError(
            "Database is unavailable"
        )

        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "error"})

    @mock.patch("core.views.connection")
    def test_health_does_not_expose_internal_details_on_failure(self, mock_connection):
        mock_connection.cursor.side_effect = OperationalError(
            "Database is unavailable"
        )

        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Database is unavailable", response.content.decode())
        self.assertNotIn("OperationalError", response.content.decode())


class SensitiveDataFilterTests(SimpleTestCase):
    def setUp(self):
        self._filter = SensitiveDataFilter()

    def _record(self, msg, args=()):
        logger = logging.getLogger("test.sensitive")
        record = logger.makeRecord(
            logger.name, logging.INFO, __file__, 1, msg, args, None
        )
        return record

    def test_redacts_key_value_pairs_in_message(self):
        record = self._record("Login failed password=supersecret for user x")

        self._filter.filter(record)

        self.assertNotIn("supersecret", record.getMessage())
        self.assertIn("[REDACTED]", record.getMessage())

    def test_redacts_sensitive_named_arguments(self):
        record = self._record(
            "stored credentials: %(password)s",
            ({"password": "hunter2"},),
        )

        self._filter.filter(record)

        self.assertNotIn("hunter2", record.getMessage())

    def test_redacts_positional_args_when_format_names_the_key(self):
        record = self._record("token=%s", ("abc123token",))

        self._filter.filter(record)

        self.assertNotIn("abc123token", record.getMessage())
        self.assertIn("[REDACTED]", record.getMessage())

    def test_redacts_compound_key_names(self):
        record = self._record("user tried secret_key=hunter2 and failed")

        self._filter.filter(record)

        self.assertNotIn("hunter2", record.getMessage())
        self.assertIn("[REDACTED]", record.getMessage())

    def test_redacts_multiple_positional_args(self):
        record = self._record("oauth token=%s for password=%s", ("abc", "xyz"))

        self._filter.filter(record)

        message = record.getMessage()
        self.assertNotIn("abc", message)
        self.assertNotIn("xyz", message)
        self.assertEqual(message.count("[REDACTED]"), 2)

    def test_redacts_sensitive_extra_attributes(self):
        record = self._record("some log line")
        record.password = "hunter2"
        record.secret_key = "very-secret"

        self._filter.filter(record)

        self.assertEqual(record.password, "[REDACTED]")
        self.assertEqual(record.secret_key, "[REDACTED]")

    def test_non_sensitive_messages_are_unchanged(self):
        record = self._record("Booking %s created for tour %s", (42, "Alps hike"))

        self._filter.filter(record)

        self.assertEqual(record.getMessage(), "Booking 42 created for tour Alps hike")
