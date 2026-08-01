from django.test import TestCase
from django.urls import reverse


class FooterLinkTests(TestCase):
    def test_footer_blog_link_points_to_faq_page(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(response, 'href="/pyetje-te-shpeshta/"')
        self.assertNotContains(response, 'href="#"')
