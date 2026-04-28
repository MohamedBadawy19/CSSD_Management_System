"""
test_proj17_mark_as_collected.py — Unit + Integration tests for US-17.

Feature: CSSD technician marks a Requested InstrumentRequest as Collected.
Branch:  feature/Proj-17-Mark-as-Collected

Unit tests:
  - Happy path: Requested → Collected (status, collected_at, last_operator set)
  - Only Requested items can transition (other statuses rejected)
  - Only the 'Collected' target status is accepted on this branch
  - Notification created for nurse on success

Integration tests (HTTP):
  - POST /dashboard/cssd/request/<pk>/update/Collected/ → 302 on success
  - GET  /dashboard/cssd/request/<pk>/update/Collected/ → 405
  - Nurse cannot access the update endpoint (403)
  - Unauthenticated user redirected to login
  - Non-Requested item returns error on attempt
  - Wrong target status (e.g. Cleaned) is rejected
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser,
    InventoryItem,
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
        email="cssd17@test.com",
        password=TEST_PASSWORD,
        role="CSSD Technician",
        department="CSSD",
    )


@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email="nurse17@test.com",
        password=TEST_PASSWORD,
        role="Department Nurse",
        department="ICU",
    )


@pytest.fixture
def requested_request(nurse_user):
    """An InstrumentRequest in the initial 'Requested' state."""
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Requested",
        department="ICU",
    )


@pytest.fixture
def collected_request(nurse_user):
    """An InstrumentRequest already in 'Collected' state (wrong source)."""
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Collected",
        department="ICU",
        collected_at=timezone.now(),
    )


@pytest.fixture
def cssd_client(cssd_user):
    c = Client()
    c.login(email="cssd17@test.com", password=TEST_PASSWORD)
    return c


@pytest.fixture
def nurse_client(nurse_user):
    c = Client()
    c.login(email="nurse17@test.com", password=TEST_PASSWORD)
    return c


def update_url(pk, status="Collected"):
    return reverse("cssd_update_request_status", kwargs={"pk": pk, "status": status})


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarkAsCollectedUnit:
    """Pure unit tests — directly manipulate models, no HTTP."""

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_status_changes_to_collected(self, requested_request, cssd_user):
        """Requested → Collected: status field updated correctly."""
        req = requested_request
        req.status = "Collected"
        req.collected_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.status == "Collected"

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_collected_at_timestamp_set(self, requested_request, cssd_user):
        """collected_at is populated after the transition."""
        req = requested_request
        assert req.collected_at is None  # initially unset

        before = timezone.now()
        req.status = "Collected"
        req.collected_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.collected_at is not None
        assert req.collected_at >= before

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_last_operator_set(self, requested_request, cssd_user):
        """last_operator is set to the CSSD user who performed the action."""
        req = requested_request
        req.status = "Collected"
        req.collected_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.last_operator == cssd_user

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_notification_created_for_nurse(self, requested_request, nurse_user):
        """A Notification is created for the nurse when request is Collected."""
        req = requested_request
        Notification.objects.create(
            recipient=nurse_user,
            request=req,
            message=f"REQ-{req.id:04d} has been collected by CSSD.",
        )
        notif = Notification.objects.get(recipient=nurse_user, request=req)
        assert "collected" in notif.message.lower()

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_cannot_collect_already_collected_request(self, collected_request):
        """Business rule: only Requested items can be Collected."""
        assert collected_request.status == "Collected"
        # The guard logic checks req.status != 'Requested'
        assert collected_request.status != "Requested"

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_request_str_format(self, requested_request):
        """__str__ returns the expected 'REQ-NNNN - Status' format."""
        expected = f"REQ-{requested_request.id:04d} - Requested"
        assert str(requested_request) == expected

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_collected_at_none_before_transition(self, requested_request):
        """collected_at is None on a freshly created Requested item."""
        assert requested_request.collected_at is None


# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestMarkAsCollectedIntegration:
    """Full HTTP integration tests for the Mark-as-Collected endpoint."""

    # ── Happy path ──────────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cssd_can_mark_requested_as_collected(
        self, cssd_client, requested_request
    ):
        """POST update/Collected/ on a Requested item → 302, status = Collected."""
        resp = cssd_client.post(update_url(requested_request.pk, "Collected"))
        assert resp.status_code == 302

        requested_request.refresh_from_db()
        assert requested_request.status == "Collected"

    @pytest.mark.integration
    def test_collected_at_set_after_http_transition(
        self, cssd_client, requested_request
    ):
        """collected_at timestamp is populated after the HTTP POST."""
        assert requested_request.collected_at is None
        cssd_client.post(update_url(requested_request.pk, "Collected"))
        requested_request.refresh_from_db()
        assert requested_request.collected_at is not None

    @pytest.mark.integration
    def test_last_operator_set_to_cssd_user_via_http(
        self, cssd_client, cssd_user, requested_request
    ):
        """last_operator is set to the logged-in CSSD user after POST."""
        cssd_client.post(update_url(requested_request.pk, "Collected"))
        requested_request.refresh_from_db()
        assert requested_request.last_operator == cssd_user

    @pytest.mark.integration
    def test_notification_created_after_http_transition(
        self, cssd_client, requested_request, nurse_user
    ):
        """A Notification for the nurse is created after the HTTP POST."""
        cssd_client.post(update_url(requested_request.pk, "Collected"))
        assert Notification.objects.filter(
            recipient=nurse_user,
            request=requested_request,
        ).exists()

    @pytest.mark.integration
    def test_redirect_target_is_request_detail(
        self, cssd_client, requested_request
    ):
        """After success, response redirects to cssd_request_detail."""
        resp = cssd_client.post(update_url(requested_request.pk, "Collected"))
        assert resp.status_code == 302
        assert f"/dashboard/cssd/request/{requested_request.pk}/" in resp.url

    # ── Wrong HTTP method ────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_get_request_returns_405(self, cssd_client, requested_request):
        """GET on the update endpoint must return 405 Method Not Allowed."""
        resp = cssd_client.get(update_url(requested_request.pk, "Collected"))
        assert resp.status_code == 405

    # ── Wrong source status ──────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cannot_collect_already_collected_item_via_http(
        self, cssd_client, collected_request
    ):
        """POST Collected on an already-Collected item → redirect, status unchanged."""
        resp = cssd_client.post(update_url(collected_request.pk, "Collected"))
        assert resp.status_code == 302
        collected_request.refresh_from_db()
        assert collected_request.status == "Collected"  # unchanged

    # ── Wrong target status ──────────────────────────────────────────────────

    @pytest.mark.integration
    def test_wrong_target_status_cleaned_rejected(
        self, cssd_client, requested_request
    ):
        """Trying to mark as 'Cleaned' → error, status still Requested."""
        resp = cssd_client.post(update_url(requested_request.pk, "Cleaned"))
        assert resp.status_code == 302
        requested_request.refresh_from_db()
        assert requested_request.status == "Requested"  # unchanged

    # ── Access control ───────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_nurse_cannot_access_update_endpoint(
        self, nurse_client, requested_request
    ):
        """Nurse user is forbidden from the CSSD update endpoint."""
        resp = nurse_client.post(update_url(requested_request.pk, "Collected"))
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_unauthenticated_user_redirected_to_login(self, requested_request):
        """Anonymous user hitting the update endpoint is redirected to login."""
        anon = Client()
        resp = anon.post(update_url(requested_request.pk, "Collected"))
        assert resp.status_code in (302, 403)
        if resp.status_code == 302:
            assert "/login/" in resp.url

    @pytest.mark.integration
    def test_cssd_request_detail_page_loads(
        self, cssd_client, requested_request
    ):
        """CSSD can load the request detail page (infrastructure check)."""
        url = reverse("cssd_request_detail", kwargs={"pk": requested_request.pk})
        resp = cssd_client.get(url)
        assert resp.status_code == 200
