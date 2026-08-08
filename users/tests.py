from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from users.models import GuideProfile, GuideModerationLog, TouristProfile


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


class AdminGuideModerationTests(TestCase):
    """Teste për menaxhimin e guide-ve nga administratori."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_user",
            email="admin@example.com",
            password="AdminPass123!",
        )
        self.guide_user = User.objects.create_user(
            username="mod_guide",
            email="modguide@example.com",
            password="GuidePass123!",
            first_name="Filan",
            last_name="Fisteku",
        )
        self.guide = GuideProfile.objects.create(
            user=self.guide_user,
            location="Vlorë",
            status="pending",
            specialty="nature_walk",
        )

    def test_admin_guides_page_renders_with_filters(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("users:admin_guides"), {"status": "pending", "q": "Filan"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Filan")
        self.assertContains(response, "Menaxho")

    def test_admin_guides_requires_staff(self):
        regular = User.objects.create_user(username="regular", password="pass12345")
        self.client.force_login(regular)
        response = self.client.get(reverse("users:admin_guides"))
        self.assertEqual(response.status_code, 302)

    def test_approve_guide_logs_and_activates(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("users:admin_dashboard"),
            {"guide_id": self.guide.id, "action": "approve"},
        )
        self.assertEqual(response.status_code, 302)

        self.guide.refresh_from_db()
        self.guide_user.refresh_from_db()
        self.assertEqual(self.guide.status, "verified")
        self.assertTrue(self.guide.is_active)
        self.assertTrue(self.guide_user.is_active)
        self.assertTrue(GuideModerationLog.objects.filter(
            guide=self.guide, action="approved", admin=self.admin
        ).exists())

    def test_reject_guide_logs_reason_and_deactivates(self):
        self.client.force_login(self.admin)
        reason = "Dokumenti i certifikimit i pamjaftueshëm"
        response = self.client.post(
            reverse("users:admin_guide_detail", args=[self.guide.id]),
            {"action": "reject", "reason": reason},
        )
        self.assertEqual(response.status_code, 302)

        self.guide.refresh_from_db()
        self.guide_user.refresh_from_db()
        self.assertEqual(self.guide.status, "rejected")
        self.assertFalse(self.guide_user.is_active)
        log = GuideModerationLog.objects.filter(guide=self.guide, action="rejected").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.reason, reason)

    def test_guide_detail_page_shows_history_and_notes(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("users:admin_guide_detail", args=[self.guide.id]),
            {"action": "approve"},
        )
        self.client.post(
            reverse("users:admin_guide_detail", args=[self.guide.id]),
            {"action": "save_notes", "admin_notes": "Guida e besueshme"},
        )

        response = self.client.get(reverse("users:admin_guide_detail", args=[self.guide.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historiku i moderimit")
        self.assertContains(response, "Miratuar")
        self.assertContains(response, "Guida e besueshme")

    def test_feature_toggle_guide(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("users:admin_guide_detail", args=[self.guide.id]),
            {"action": "feature"},
        )
        self.guide.refresh_from_db()
        self.assertTrue(self.guide.is_featured)
        self.assertTrue(GuideModerationLog.objects.filter(
            guide=self.guide, action="featured"
        ).exists())

        self.client.post(
            reverse("users:admin_guide_detail", args=[self.guide.id]),
            {"action": "unfeature"},
        )
        self.guide.refresh_from_db()
        self.assertFalse(self.guide.is_featured)

    def test_suspend_and_reactivate_guide(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("users:admin_guides"),
            {"guide_id": self.guide.id, "action": "approve"},
        )
        self.client.post(
            reverse("users:admin_guides"),
            {"guide_id": self.guide.id, "action": "suspend", "reason": "Ankesë"},
        )
        self.guide.refresh_from_db()
        self.assertEqual(self.guide.status, "suspended")

        self.client.post(
            reverse("users:admin_guides"),
            {"guide_id": self.guide.id, "action": "reactivate"},
        )
        self.guide.refresh_from_db()
        self.assertEqual(self.guide.status, "verified")

    def test_admin_cannot_moderate_own_guide_profile(self):
        """Administratori nuk duhet të çaktivizojë llogarinë e vet duke refuzuar veten."""
        admin_profile = GuideProfile.objects.create(
            user=self.admin, location="Tiranë", status="verified", is_active=True
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("users:admin_guide_detail", args=[admin_profile.id]),
            {"action": "reject", "reason": "Gabim aksidental"},
        )
        self.assertEqual(response.status_code, 302)

        self.admin.refresh_from_db()
        admin_profile.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(admin_profile.status, "verified")
        self.assertFalse(GuideModerationLog.objects.filter(
            guide=admin_profile, action="rejected"
        ).exists())

    def test_admin_guide_detail_hides_actions_on_own_profile(self):
        admin_profile = GuideProfile.objects.create(
            user=self.admin, location="Tiranë", status="verified", is_active=True
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("users:admin_guide_detail", args=[admin_profile.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profil është i yti")
        self.assertNotContains(response, 'value="reject"')
