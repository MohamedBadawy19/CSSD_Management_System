import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from CSSD_Management_System.models import CustomUser, InstrumentRequest


@pytest.mark.django_db
class TestProj29ETAIntegration:

    def setup_method(self):
        # Create users (NO username!)
        self.nurse1 = CustomUser.objects.create_user(
            email="nurse1@test.com",
            password="pass123",
            role="Department Nurse"
        )

        self.nurse2 = CustomUser.objects.create_user(
            email="nurse2@test.com",
            password="pass123",
            role="Department Nurse"
        )

        # Create a request for nurse1
        self.request = InstrumentRequest.objects.create(
            requester=self.nurse1,
            status="Requested"
        )

    def test_requested_eta_display(self, client):
        client.login(email="nurse1@test.com", password="pass123")

        response = client.get(f"/nurse_request_details/{self.request.id}/")

        assert response.status_code == 200
        assert "Ready by" in response.content.decode()

    def test_eta_updates_on_status_change(self, client):
        client.login(email="nurse1@test.com", password="pass123")

        # Move to Collected
        self.request.status = "Collected"
        self.request.save()

        response = client.get(f"/nurse_request_details/{self.request.id}/")

        assert response.status_code == 200
        assert "Ready by" in response.content.decode()

    def test_delivered_shows_ready(self, client):
        client.login(email="nurse1@test.com", password="pass123")

        self.request.status = "Delivered"
        self.request.save()

        response = client.get(f"/nurse_request_details/{self.request.id}/")

        assert response.status_code == 200
        assert "Ready" in response.content.decode()

    def test_overdue_message(self, client):
        client.login(email="nurse1@test.com", password="pass123")

        # Make request very old
        self.request.submitted_at = timezone.now() - timedelta(hours=5)
        self.request.save()

        response = client.get(f"/nurse_request_details/{self.request.id}/")

        assert response.status_code == 200
        assert "Overdue" in response.content.decode()

    def test_nurse_cannot_view_others_request(self, client):
        client.login(email="nurse2@test.com", password="pass123")

        response = client.get(f"/nurse_request_details/{self.request.id}/")

        # Expect redirect or forbidden
        assert response.status_code in [302, 403]
        assert "You can only view your own requests" in response.content.decode()

    def test_unauthenticated_redirect(self, client):
        response = client.get(f"/nurse_request_details/{self.request.id}/")

        # Should redirect to login
        assert response.status_code == 302
        assert "/login" in response.url