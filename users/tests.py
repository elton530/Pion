from django.core import mail
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import override_settings
from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import re
import time

from tours.models import Tour, TourType
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


@override_settings(LOGIN_RATE_LIMIT_MAX_ATTEMPTS=3, LOGIN_RATE_LIMIT_WINDOW_SECONDS=60)
class LoginRateLimitingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="login_limit_user",
            email="login_limit_user@example.com",
            password=self.password,
            first_name="Arta",
        )
        self.login_url = reverse("users:login")
        self.safe_error = "Kredencialet janë të pasakta ose hyrja është përkohësisht e kufizuar"

    def _login(self, username, password):
        return self.client.post(
            self.login_url,
            {"username": username, "password": password},
            REMOTE_ADDR="10.10.10.10",
        )

    def test_blocks_login_after_repeated_failed_attempts(self):
        for _ in range(3):
            response = self._login("login_limit_user", "wrong-password")
            self.assertEqual(response.status_code, 200)

        blocked_response = self._login("login_limit_user", self.password)

        self.assertEqual(blocked_response.status_code, 200)
        self.assertContains(blocked_response, self.safe_error)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(LOGIN_RATE_LIMIT_MAX_ATTEMPTS=2, LOGIN_RATE_LIMIT_WINDOW_SECONDS=1)
    def test_limit_expires_and_login_recovers(self):
        self._login("login_limit_user", "wrong-password")
        self._login("login_limit_user", "wrong-password")

        blocked_response = self._login("login_limit_user", self.password)
        self.assertEqual(blocked_response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        time.sleep(1.1)

        success_response = self._login("login_limit_user", self.password)
        self.assertEqual(success_response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_existing_and_non_existing_accounts_get_same_safe_message(self):
        existing = self._login("login_limit_user", "wrong-password")
        unknown = self._login("unknown_user", "wrong-password")

        self.assertEqual(existing.status_code, 200)
        self.assertEqual(unknown.status_code, 200)
        self.assertContains(existing, self.safe_error)
        self.assertContains(unknown, self.safe_error)


class GuideProfilePublicVisibilityTests(TestCase):
    """Regression: profili publik i guide-it nuk duhet të shfaqë ture draft/hidden."""

    def setUp(self):
        self.guide_user = User.objects.create_user(
            username="public_guide",
            password="secret123",
            first_name="Public",
            last_name="Guide",
        )
        self.guide = GuideProfile.objects.create(
            user=self.guide_user,
            location="Tiranë",
            status="verified",
            is_active=True,
        )
        self.tour_type = TourType.objects.create(name="Visibility Type", description="Test")

        self.published_tour = Tour.objects.create(
            guide=self.guide,
            title="Published Public Tour",
            slug="published-public-tour",
            short_description="Description",
            full_description="Full description",
            tour_type=self.tour_type,
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            main_image=SimpleUploadedFile(
                "published-public.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="published",
            is_active=True,
        )
        self.draft_tour = Tour.objects.create(
            guide=self.guide,
            title="Secret Draft Tour",
            slug="secret-draft-tour",
            short_description="Description",
            full_description="Full description",
            tour_type=self.tour_type,
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            main_image=SimpleUploadedFile(
                "secret-draft.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="draft",
            is_active=True,
        )
        self.hidden_tour = Tour.objects.create(
            guide=self.guide,
            title="Hidden Tour",
            slug="hidden-tour",
            short_description="Description",
            full_description="Full description",
            tour_type=self.tour_type,
            meeting_point="Qendra",
            location_city="Tiranë",
            location_region="Tiranë",
            duration_hours=4,
            date="2030-01-01",
            time_start="10:00:00",
            price_per_person=100,
            max_participants=10,
            main_image=SimpleUploadedFile(
                "hidden-tour.jpg",
                b"fake-image-data",
                content_type="image/jpeg",
            ),
            status="hidden",
            is_active=True,
        )

    def _public_profile_url(self):
        return reverse(
            "users:guide_profile_public",
            kwargs={"username": self.guide_user.username},
        )

    def test_public_profile_only_lists_published_tours(self):
        response = self.client.get(self._public_profile_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Public Tour")
        self.assertNotContains(response, "Secret Draft Tour")
        self.assertNotContains(response, "Hidden Tour")

    def test_public_profile_tour_links_only_point_to_published_tours(self):
        response = self.client.get(self._public_profile_url())

        tours = response.context["tours"]
        tour_slugs = [tour.slug for tour in tours]
        self.assertIn(self.published_tour.slug, tour_slugs)
        self.assertNotIn(self.draft_tour.slug, tour_slugs)
        self.assertNotIn(self.hidden_tour.slug, tour_slugs)


class EmailFlowTests(TestCase):
    """Teste për dërgimin e email-eve në flukset kryesore të users."""

    def setUp(self):
        mail.outbox.clear()

    def test_guide_signup_sends_welcome_email(self):
        response = self.client.post(
            reverse("users:signup"),
            {
                "username": "new_guide_email",
                "first_name": "Dritan",
                "last_name": "Mulla",
                "email": "guide_welcome@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": "guide",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("guide_welcome@example.com", email.to)
        self.assertIn("Mirëseerdhët", email.subject)

    def test_tourist_signup_sends_welcome_email(self):
        response = self.client.post(
            reverse("users:signup"),
            {
                "username": "new_tourist_email",
                "first_name": "Ana",
                "last_name": "Kola",
                "email": "tourist_welcome@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": "tourist",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("tourist_welcome@example.com", email.to)
        self.assertIn("Mirëseerdhët", email.subject)

    def test_password_reset_sends_email_with_link(self):
        User.objects.create_user(
            username="reset_email_user",
            email="reset@example.com",
            password="OldPass123!",
        )

        response = self.client.post(
            reverse("users:password_reset"),
            {"email": "reset@example.com"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("reset@example.com", email.to)
        self.assertIn("/users/reset/", email.body)

    def test_password_reset_unknown_email_sends_nothing(self):
        response = self.client.post(
            reverse("users:password_reset"),
            {"email": "nobody@example.com"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_guide_profile_creation_sends_welcome_email(self):
        user = User.objects.create_user(
            username="direct_guide",
            email="direct_guide@example.com",
            password="testpass123",
        )

        GuideProfile.objects.create(user=user, location="Tiranë")

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("direct_guide@example.com", email.to)
        self.assertIn("Mirëseerdhët", email.subject)


class LoginFlowTests(TestCase):
    """Teste për rrjedhën e login-it: kredenciale, redirect sipas rolit, bllokimi."""

    def setUp(self):
        cache.clear()
        self.password = "StrongPass123!"
        self.login_url = reverse("users:login")

        self.admin = User.objects.create_superuser(
            username="login_admin", email="admin@login.com", password=self.password
        )
        self.guide_user = User.objects.create_user(
            username="login_guide", email="guide@login.com", password=self.password
        )
        GuideProfile.objects.create(
            user=self.guide_user, location="Tiranë", status="verified"
        )
        self.tourist_user = User.objects.create_user(
            username="login_tourist", email="tourist@login.com", password=self.password
        )
        TouristProfile.objects.create(user=self.tourist_user)

    def _login(self, username, password):
        return self.client.post(
            self.login_url,
            {"username": username, "password": password},
            REMOTE_ADDR="10.10.10.11",
        )

    def test_login_redirects_admin_to_admin_dashboard(self):
        response = self._login("login_admin", self.password)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("users:admin_dashboard"))

    def test_login_redirects_guide_to_guide_dashboard(self):
        response = self._login("login_guide", self.password)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("users:guide_dashboard"))

    def test_login_redirects_tourist_to_tourist_dashboard(self):
        response = self._login("login_tourist", self.password)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("users:tourist_dashboard"))

    def test_login_with_email_authenticates_user(self):
        response = self._login("tourist@login.com", self.password)
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_wrong_password_does_not_create_session(self):
        response = self._login("login_tourist", "WrongPass123!")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_unknown_user_does_not_create_session(self):
        response = self._login("ghost_user", self.password)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_user_cannot_login(self):
        inactive = User.objects.create_user(
            username="inactive_user", email="inactive@login.com", password=self.password
        )
        inactive.is_active = False
        inactive.save()

        response = self._login("inactive_user", self.password)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_pending_guide_cannot_login(self):
        pending = User.objects.create_user(
            username="pending_guide_login", email="pending@login.com", password=self.password
        )
        pending.is_active = False
        pending.save()
        GuideProfile.objects.create(user=pending, location="Vlorë", status="pending")

        response = self._login("pending_guide_login", self.password)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


class LogoutTests(TestCase):
    """Teste për daljen nga llogaria dhe mbrojtjen pas saj."""

    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="logout_user", email="logout@example.com", password=self.password
        )
        TouristProfile.objects.create(user=self.user)
        self.client.login(username="logout_user", password=self.password)

    def test_logout_clears_session_and_redirects_home(self):
        self.assertIn("_auth_user_id", self.client.session)
        response = self.client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_rejects_get_requests(self):
        response = self.client.get(reverse("users:logout"))
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_protected_page_inaccessible_after_logout(self):
        self.client.post(reverse("users:logout"))
        response = self.client.get(reverse("users:tourist_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)


class PasswordResetFullFlowTests(TestCase):
    """Rrjedhë e plotë e rivendosjes së fjalëkalimit: kërkesë -> email -> fjalëkalim i ri."""

    def test_full_password_reset_flow(self):
        user = User.objects.create_user(
            username="reset_full", email="resetfull@example.com", password="OldPass123!"
        )

        self.client.post(
            reverse("users:password_reset"), {"email": "resetfull@example.com"}
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        match = re.search(r"/users/reset/([0-9A-Za-z_-]+)/([0-9A-Za-z_-]+)/", email.body)
        self.assertIsNotNone(match)
        reset_url = reverse(
            "users:password_reset_confirm",
            args=[match.group(1), match.group(2)],
        )

        # Django 5.x redirects the emailed token URL to a token-free "set-password" URL.
        get_response = self.client.get(reset_url, follow=True)
        self.assertEqual(get_response.status_code, 200)
        self.assertIn("set-password", get_response.redirect_chain[-1][0])

        set_password_url = reset_url.replace(
            match.group(2), "set-password"
        )
        post_response = self.client.post(
            set_password_url,
            {"new_password1": "NewPass456!", "new_password2": "NewPass456!"},
        )
        self.assertEqual(post_response.status_code, 302)
        self.assertIn("reset/done/", post_response.url)

        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPass456!"))

        self.client.post(
            reverse("users:login"),
            {"username": "reset_full", "password": "NewPass456!"},
            REMOTE_ADDR="10.10.10.12",
        )
        self.assertIn("_auth_user_id", self.client.session)


class PasswordResetLinkRenderingTests(TestCase):
    """Faqja e linkut të reset-it: formë vetëm kur linku është i vlefshëm."""

    def test_valid_reset_link_renders_password_fields(self):
        user = User.objects.create_user(
            username="reset_valid", email="resetvalid@example.com", password="OldPass123!"
        )
        mail.outbox.clear()
        self.client.post(
            reverse("users:password_reset"), {"email": "resetvalid@example.com"}
        )
        email = mail.outbox[0]
        match = re.search(r"/users/reset/([0-9A-Za-z_-]+)/([0-9A-Za-z_-]+)/", email.body)
        reset_url = reverse(
            "users:password_reset_confirm",
            args=[match.group(1), match.group(2)],
        )

        response = self.client.get(reset_url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="new_password1"')
        self.assertContains(response, 'name="new_password2"')
        self.assertContains(response, "type=\"password\"", count=2)
        self.assertNotContains(response, "Link i Pavlefshëm")

    def test_invalid_reset_link_shows_message_and_no_password_fields(self):
        user = User.objects.create_user(
            username="reset_invalid", email="resetinvalid@example.com", password="OldPass123!"
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        set_password_url = reverse(
            "users:password_reset_confirm", args=[uidb64, "set-password"]
        )

        response = self.client.get(set_password_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Link i Pavlefshëm")
        self.assertContains(response, "Kërko një Link të Ri")
        self.assertNotContains(response, "name=\"new_password1\"")
        self.assertNotContains(response, "type=\"password\"")


class RoleAccessTests(TestCase):
    """Autorizimi sipas rolit: anonimë, turistë, guida dhe admin."""

    def setUp(self):
        cache.clear()
        self.password = "StrongPass123!"
        self.admin = User.objects.create_superuser(
            username="role_admin", email="roleadmin@example.com", password=self.password
        )
        self.guide_user = User.objects.create_user(
            username="role_guide", email="roleguide@example.com", password=self.password
        )
        GuideProfile.objects.create(
            user=self.guide_user, location="Tiranë", status="verified"
        )
        self.tourist_user = User.objects.create_user(
            username="role_tourist", email="roletourist@example.com", password=self.password
        )
        TouristProfile.objects.create(user=self.tourist_user)

    def test_anonymous_redirected_to_login_for_guide_dashboard(self):
        response = self.client.get(reverse("users:guide_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_anonymous_redirected_to_login_for_tourist_dashboard(self):
        response = self.client.get(reverse("users:tourist_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_anonymous_redirected_to_login_for_admin_dashboard(self):
        response = self.client.get(reverse("users:admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_tourist_cannot_access_guide_dashboard(self):
        self.client.force_login(self.tourist_user)
        response = self.client.get(reverse("users:guide_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("core:home"))

    def test_guide_cannot_access_tourist_dashboard(self):
        self.client.force_login(self.guide_user)
        response = self.client.get(reverse("users:tourist_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("core:home"))

    def test_non_admin_cannot_access_any_admin_page(self):
        admin_pages = [
            reverse("users:admin_dashboard"),
            reverse("users:admin_guides"),
            reverse("users:admin_guide_detail", args=[999]),
        ]
        for user in (self.tourist_user, self.guide_user):
            self.client.force_login(user)
            for url in admin_pages:
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    302,
                    f"{url} duhet të refuzojë përdoruesin e parregullt",
                )
                self.assertIn(reverse("users:login"), response.url)

    def test_admin_can_access_admin_pages(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("users:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("users:admin_guides"))
        self.assertEqual(response.status_code, 200)


class SessionHandlingTests(TestCase):
    """Teste për sesionet: cookie, HttpOnly, shkatërrim pas logout."""

    def setUp(self):
        cache.clear()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="session_user", email="session@example.com", password=self.password
        )
        TouristProfile.objects.create(user=self.user)
        self.login_url = reverse("users:login")

    def test_anonymous_user_has_no_session_cookie(self):
        self.client.get(reverse("core:home"))
        self.assertNotIn("sessionid", self.client.cookies)

    def test_login_creates_httponly_session_cookie(self):
        self.client.post(
            self.login_url,
            {"username": "session_user", "password": self.password},
            REMOTE_ADDR="10.10.10.13",
        )
        self.assertIn("sessionid", self.client.cookies)
        self.assertIn("HttpOnly", self.client.cookies["sessionid"].output())

    def test_logout_destroys_session(self):
        self.client.post(
            self.login_url,
            {"username": "session_user", "password": self.password},
            REMOTE_ADDR="10.10.10.14",
        )
        self.assertIn("_auth_user_id", self.client.session)

        self.client.post(reverse("users:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_distinct_users_get_distinct_sessions(self):
        other = User.objects.create_user(
            username="session_other", email="session2@example.com", password=self.password
        )
        TouristProfile.objects.create(user=other)

        client_a = Client()
        client_a.post(
            self.login_url,
            {"username": "session_user", "password": self.password},
            REMOTE_ADDR="10.10.10.15",
        )
        client_b = Client()
        client_b.post(
            self.login_url,
            {"username": "session_other", "password": self.password},
            REMOTE_ADDR="10.10.10.16",
        )

        self.assertIn("_auth_user_id", client_a.session)
        self.assertIn("_auth_user_id", client_b.session)
        self.assertNotEqual(
            client_a.session["_auth_user_id"], client_b.session["_auth_user_id"]
        )


class SessionCookieSecuritySettingsTests(TestCase):
    """Konfigurimi i sigurisë së sesioneve në dev dhe prod."""

    def test_session_cookie_httponly_enabled_in_base(self):
        from django.conf import settings as s
        self.assertTrue(s.SESSION_COOKIE_HTTPONLY)

    def test_production_requires_secure_session_cookie(self):
        from django.conf import settings as s
        self.assertFalse(s.SESSION_COOKIE_SECURE)

    def test_production_security_settings(self):
        import importlib
        prod = importlib.import_module("tour_platform.settings.production")
        self.assertFalse(prod.DEBUG)
        self.assertTrue(prod.SESSION_COOKIE_SECURE)
        self.assertTrue(prod.CSRF_COOKIE_SECURE)
        self.assertTrue(prod.SECURE_SSL_REDIRECT)
        self.assertGreaterEqual(prod.SECURE_HSTS_SECONDS, 31536000)
