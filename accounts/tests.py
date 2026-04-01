from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Organization, SpendingTier, User


class AuthenticationTests(TestCase):
    def setUp(self) -> None:
        self.tier = SpendingTier.objects.create(name="Free", token_limit=1000)
        self.org = Organization.objects.create(name="Test Org", spending_tier=self.tier)
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            organization=self.org,
        )
        self.client = Client()

    def test_login_view_renders(self) -> None:
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in to Finis")

    def test_successful_login_and_session_persistence(self) -> None:
        # Check that we can login successfully
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "test@example.com", "password": "testpassword123"},
        )
        # Login should redirect
        self.assertEqual(response.status_code, 302)

        # Verify session backend is our custom backend
        self.assertEqual(settings.SESSION_ENGINE, "accounts.session_backend")

        # Verify session exists and we are authenticated
        self.assertTrue(self.client.session.session_key)
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(self.user.pk))

        # Check session key length to verify custom 20-byte backend (40 hex chars)
        session_key = self.client.session.session_key
        if session_key is not None:
            self.assertEqual(len(session_key), 40)
        else:
            self.fail("Session key is None")

        # Access a protected view to ensure it works
        protected_response = self.client.get(reverse("scanning:receipt-list"))
        self.assertEqual(protected_response.status_code, 200)

    def test_failed_login(self) -> None:
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "test@example.com", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email or password.")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_logout(self) -> None:
        self.client.login(username="test@example.com", password="testpassword123")
        self.assertTrue(self.client.session.get("_auth_user_id"))

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))

        # Check that session is cleared
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_scanning_views_require_login(self) -> None:
        # Test an unauthenticated user attempting to access a protected view
        response = self.client.get(reverse("scanning:receipt-list"))
        self.assertEqual(response.status_code, 302)

        # Check that it redirects to login
        url = getattr(response, "url", "")
        self.assertTrue(url.startswith(reverse("accounts:login")))
