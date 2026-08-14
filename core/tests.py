from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.utils import send_notification_email
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
