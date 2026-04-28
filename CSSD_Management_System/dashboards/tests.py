from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from department_requests.models import InstrumentRequest


class DashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="cssd@example.com",
            password="password123",
            role="CSSD Technician",
        )
        self.client.login(email="cssd@example.com", password="password123")
        InstrumentRequest.objects.create(requester=self.user, status="Requested")

    @patch("dashboards.views.InventoryItem.objects.filter")
    def test_cssd_dashboard_uses_inventory_alert_filter(self, mocked_filter):
        mocked_filter.return_value.count.return_value = 2
        response = self.client.get(reverse("dashboard_router"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stat_alerts"], 2)

    def test_nurse_role_redirected_to_nurse_dashboard(self):
        get_user_model().objects.create_user(
            email="nurse@example.com",
            password="password123",
            role="Department Nurse",
            department="ER",
        )
        self.client.login(email="nurse@example.com", password="password123")
        response = self.client.get(reverse("dashboard_router"))
        self.assertRedirects(response, reverse("nurse_dashboard"))

# Create your tests here.
