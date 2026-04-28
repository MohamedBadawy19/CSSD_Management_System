from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import InventoryItem, InstrumentRequest


class DepartmentRequestsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="nurse@example.com",
            password="password123",
            role="Department Nurse",
            department="ER",
        )
        self.inventory = InventoryItem.objects.create(
            name="Scalpel", category="Surgical", current_stock=10, min_threshold=5
        )
        self.client.login(email="nurse@example.com", password="password123")

    @patch("department_requests.views.get_instruments")
    def test_create_request_page_uses_instrument_provider(self, mocked_get):
        mocked_get.return_value = [{"name": "Mock Item"}]
        response = self.client.get(reverse("nurse_create_request"))
        self.assertEqual(response.status_code, 200)
        mocked_get.assert_called_once()

    def test_submit_request_creates_request(self):
        response = self.client.post(
            reverse("save_instrument_request"),
            {
                "instruments": ["Scalpel"],
                "quantity_Scalpel": 2,
                "priority": "Urgent",
                "notes": "Need ASAP",
            },
        )
        self.assertRedirects(response, reverse("nurse_create_request"))
        self.assertEqual(InstrumentRequest.objects.count(), 1)

# Create your tests here.
