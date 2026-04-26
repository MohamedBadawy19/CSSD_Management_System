from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .forms import EmailLoginForm
from .views import logout_view


class AuthenticationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            email="nurse@example.com",
            password="password123",
            role="Department Nurse",
            department="ER",
        )

    @patch.object(EmailLoginForm, "is_valid", return_value=True)
    def test_login_posts_valid_form_redirects(self, _):
        with patch.object(EmailLoginForm, "get_user", return_value=self.user):
            response = self.client.post(
                reverse("login"),
                {"username": "nurse@example.com", "password": "password123"},
            )
        self.assertRedirects(
            response, reverse("dashboard_router"), fetch_redirect_response=False
        )

    @patch("authentication.views.logout")
    def test_logout_view_calls_django_logout(self, mocked_logout):
        request = self.factory.get(reverse("logout"))
        request.user = self.user
        response = logout_view(request)
        mocked_logout.assert_called_once_with(request)
        self.assertEqual(response.status_code, 302)

# Create your tests here.
