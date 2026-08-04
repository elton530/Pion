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

    def test_guide_dashboard_shows_quick_actions(self):
        user = User.objects.create_user(
            username="guide_dashboard_user",
            password="testpass123",
            first_name="Ardi",
        )
        GuideProfile.objects.create(user=user, location="Tiranë")

        self.client.login(username="guide_dashboard_user", password="testpass123")
        response = self.client.get(reverse("users:guide_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Veprime të shpejta")


class ApprovalAndPasswordTests(TestCase):
    def test_guide_signup_requires_admin_approval(self):
        response = self.client.post(
            reverse("users:signup"),
            {
                "username": "new_guide",
                "first_name": "Dritan",
                "last_name": "Mulla",
                "email": "guide@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": "guide",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="new_guide")
        profile = GuideProfile.objects.get(user=user)
        self.assertEqual(profile.status, "pending")
        self.assertFalse(self.client.login(username="new_guide", password="StrongPass123!"))

    def test_admin_dashboard_lists_pending_guides(self):
        admin = User.objects.create_superuser(
            username="admin_user",
            email="admin@example.com",
            password="AdminPass123!",
        )
        guide_user = User.objects.create_user(
            username="pending_guide",
            email="pending@example.com",
            password="GuidePass123!",
            first_name="Luan",
            last_name="Shala",
        )
        GuideProfile.objects.create(user=guide_user, location="Shkodër", status="pending")

        self.client.force_login(admin)
        response = self.client.get(reverse("users:admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pending_guide")
        self.assertContains(response, "Në pritje")

    def test_user_can_change_password(self):
        user = User.objects.create_user(
            username="password_user",
            email="pw@example.com",
            password="OldPass123!",
            first_name="Mira",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("users:password_change"),
            {
                "old_password": "OldPass123!",
                "new_password1": "NewPass123!",
                "new_password2": "NewPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPass123!"))
