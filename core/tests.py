from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from tour_platform.security import DEVELOPMENT_SECRET_KEY_FALLBACK, resolve_secret_key


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
