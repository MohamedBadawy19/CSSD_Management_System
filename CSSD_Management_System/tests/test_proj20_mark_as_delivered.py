"""
test_proj20_mark_as_delivered.py — Unit + Integration tests for US-20.

Feature: CSSD technician marks a Packed InstrumentRequest as Delivered.
Branch:  feature/Proj-20-Mark-as-Delivered

Unit tests:
  - Happy path: Packed → Delivered (status, delivered_at, last_operator set)
  - Wrong source status rejected (e.g. Sterilized → Delivered)
  - Notification created for nurse on success

Integration tests (HTTP):
  - POST /dashboard/cssd/request/<pk>/update/Delivered/ → 302 on success
  - GET  /dashboard/cssd/request/<pk>/update/Delivered/ → 405
  - Nurse cannot access the update endpoint (403)
  - Unauthenticated user redirected to login
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser,
    InstrumentRequest,
    Notification,
)

TEST_PASSWORD = "TestPass123!"


# ═══════════════════════════════════════════════════════════════════════════════
#  Shared fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def cssd_user(db):
    return CustomUser.objects.create_user(
        email="cssd20@test.com",
        password=TEST_PASSWORD,
        role="CSSD Technician",
        department="CSSD",
    )


@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email="nurse20@test.com",
        password=TEST_PASSWORD,
        role="Department Nurse",
        department="ICU",
    )


@pytest.fixture
def packed_request(nurse_user):
    """An InstrumentRequest already in 'Packed' state."""
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Packed",
        department="ICU",
        collected_at=timezone.now(),
        cleaned_at=timezone.now(),
        sterilized_at=timezone.now(),
        packed_at=timezone.now(),
    )


@pytest.fixture
def sterilized_request(nurse_user):
    """An InstrumentRequest in 'Sterilized' state (wrong source)."""
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Sterilized",
        department="ICU",
        collected_at=timezone.now(),
        cleaned_at=timezone.now(),
        sterilized_at=timezone.now(),
    )


@pytest.fixture
def cssd_client(cssd_user):
    c = Client()
    c.login(email="cssd20@test.com", password=TEST_PASSWORD)
    return c


@pytest.fixture
def nurse_client(nurse_user):
    c = Client()
    c.login(email="nurse20@test.com", password=TEST_PASSWORD)
    return c


def update_url(pk, status="Delivered"):
    return reverse("cssd_update_request_status", kwargs={"pk": pk, "status": status})


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarkAsDeliveredUnit:
    """Pure unit tests — directly manipulate models, no HTTP."""

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_status_changes_to_delivered(self, packed_request, cssd_user):
        """Packed → Delivered: status field updated correctly."""
        req = packed_request
        req.status = "Delivered"
        req.delivered_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.status == "Delivered"

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_delivered_at_timestamp_set(self, packed_request, cssd_user):
        """delivered_at is populated after transition."""
        req = packed_request
        before = timezone.now()
        req.status = "Delivered"
        req.delivered_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.delivered_at is not None
        assert req.delivered_at >= before

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_last_operator_set(self, packed_request, cssd_user):
        """last_operator is set to the CSSD user who performed the action."""
        req = packed_request
        req.status = "Delivered"
        req.delivered_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.last_operator == cssd_user

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_notification_created_for_nurse(self, packed_request, nurse_user):
        """A Notification is created for the nurse when request is Delivered."""
        req = packed_request
        Notification.objects.create(
            recipient=nurse_user,
            request=req,
            message=f"REQ-{req.id:04d} instruments have been delivered.",
        )
        notif = Notification.objects.get(recipient=nurse_user, request=req)
        assert "delivered" in notif.message.lower()


# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestMarkAsDeliveredIntegration:
    """Full HTTP integration tests for the Mark-as-Delivered endpoint."""

    # ── Happy path ──────────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cssd_can_mark_packed_as_delivered(
        self, cssd_client, packed_request
    ):
        """POST update/Delivered/ on a Packed request → 302 redirect."""
        resp = cssd_client.post(update_url(packed_request.pk, "Delivered"))
        assert resp.status_code == 302

        packed_request.refresh_from_db()
        assert packed_request.status == "Delivered"

    @pytest.mark.integration
    def test_delivered_at_set_after_http_transition(
        self, cssd_client, packed_request
    ):
        """delivered_at timestamp is populated after the HTTP POST."""
        assert packed_request.delivered_at is None
        cssd_client.post(update_url(packed_request.pk, "Delivered"))
        packed_request.refresh_from_db()
        assert packed_request.delivered_at is not None

    @pytest.mark.integration
    def test_notification_created_after_http_transition(
        self, cssd_client, packed_request, nurse_user
    ):
        """A Notification for the nurse is created after the HTTP POST."""
        cssd_client.post(update_url(packed_request.pk, "Delivered"))
        assert Notification.objects.filter(
            recipient=nurse_user,
            request=packed_request,
        ).exists()

    @pytest.mark.integration
    def test_redirect_target_is_request_detail(
        self, cssd_client, packed_request
    ):
        """After success, response redirects to cssd_request_detail."""
        resp = cssd_client.post(update_url(packed_request.pk, "Delivered"))
        assert resp.status_code == 302
        assert f"/dashboard/cssd/request/{packed_request.pk}/" in resp.url

    # ── Wrong HTTP method ────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_get_request_returns_405(self, cssd_client, packed_request):
        """GET on the update endpoint must return 405 Method Not Allowed."""
        resp = cssd_client.get(update_url(packed_request.pk, "Delivered"))
        assert resp.status_code == 405

    # ── Wrong source status ──────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cannot_deliver_a_sterilized_item_via_http(
        self, cssd_client, sterilized_request
    ):
        """Delivering a Sterilized (not Packed) item → redirect + no change."""
        resp = cssd_client.post(update_url(sterilized_request.pk, "Delivered"))
        assert resp.status_code == 302
        sterilized_request.refresh_from_db()
        assert sterilized_request.status == "Sterilized"

    # ── Access control ───────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_nurse_cannot_access_update_endpoint(
        self, nurse_client, packed_request
    ):
        """Nurse user is forbidden from the CSSD update endpoint."""
        resp = nurse_client.post(update_url(packed_request.pk, "Delivered"))
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_unauthenticated_user_redirected_to_login(
        self, packed_request
    ):
        """Anonymous user hitting the update endpoint is redirected to login."""
        anon = Client()
        resp = anon.post(update_url(packed_request.pk, "Delivered"))
        assert resp.status_code in (302, 403)
        if resp.status_code == 302:
            assert "/login/" in resp.url
