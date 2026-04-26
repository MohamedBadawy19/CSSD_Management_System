from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from department_requests.models import InstrumentRequest


class StateMachineTests(TestCase):
    def setUp(self):
        self.tech = get_user_model().objects.create_user(
            email="cssd@example.com",
            password="password123",
            role="CSSD Technician",
        )
        self.nurse = get_user_model().objects.create_user(
            email="nurse@example.com",
            password="password123",
            role="Department Nurse",
            department="ER",
        )
        self.request_obj = InstrumentRequest.objects.create(
            requester=self.nurse,
            department="ER",
            status="Requested",
        )
        self.client.login(email="cssd@example.com", password="password123")

    @patch("state_machine.views.Notification.objects.create")
    def test_mark_collected_sends_notification(self, mocked_notify):
        response = self.client.post(reverse("mark_collected", args=[self.request_obj.id]))
        self.assertEqual(response.status_code, 302)
        mocked_notify.assert_called_once()

    def test_mark_collected_requires_post(self):
        response = self.client.get(reverse("mark_collected", args=[self.request_obj.id]))
        self.assertEqual(response.status_code, 403)

# Create your tests here.
