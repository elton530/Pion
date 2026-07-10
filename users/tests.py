from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from users.models import GuideProfile, TouristProfile


class ActivityPagesTests(TestCase):
    def test_tourist_saved_tours_page_renders(self):
        user = User.objects.create_user(
            username="tourist_user",
            password="testpass123",
            first_name="Ana",
        )
        TouristProfile.objects.create(user=user)

        self.client.login(username="tourist_user", password="testpass123")
        response = self.client.get(reverse("users:saved_tours"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ture të ruajtura")

    def test_guide_history_page_renders(self):
        user = User.objects.create_user(
            username="guide_user",
            password="testpass123",
            first_name="Genti",
        )
        GuideProfile.objects.create(user=user, location="Tiranë")

        self.client.login(username="guide_user", password="testpass123")
        response = self.client.get(reverse("users:history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historiku")
