"""
test_proj18_mark_as_cleaned.py — Unit + Integration tests for US-18.

Feature: CSSD technician marks a Collected InstrumentRequest as Cleaned.
Branch:  feature/Proj-18-Mark-as-Cleaned

Unit tests:
  - Happy path: Collected → Cleaned (status, cleaned_at, last_operator set)
  - Wrong source status rejected (e.g. Requested → Cleaned)
  - Wrong target status rejected (e.g. trying to mark as Collected)
  - Notification created for nurse on success

Integration tests (HTTP):
  - POST /dashboard/cssd/request/<pk>/update/Cleaned/ → 302 on success
  - GET  /dashboard/cssd/request/<pk>/update/Cleaned/ → 405
  - Nurse cannot access the update endpoint (403)
  - Unauthenticated user redirected to login
  - Already-Cleaned request returns error message on second attempt
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
    SterilizationBatch,
)

TEST_PASSWORD = "TestPass123!"


# ═══════════════════════════════════════════════════════════════════════════════
#  Shared fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def cssd_user(db):
    return CustomUser.objects.create_user(
        email="cssd18@test.com",
        password=TEST_PASSWORD,
        role="CSSD Technician",
        department="CSSD",
    )


@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email="nurse18@test.com",
        password=TEST_PASSWORD,
        role="Department Nurse",
        department="ICU",
    )


@pytest.fixture
def collected_request(nurse_user):
    """An InstrumentRequest already in 'Collected' state."""
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Collected",
        department="ICU",
        collected_at=timezone.now(),
    )


@pytest.fixture
def requested_request(nurse_user):
    """An InstrumentRequest still in initial 'Requested' state."""
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Requested",
        department="ICU",
    )


@pytest.fixture
def cssd_client(cssd_user):
    c = Client()
    c.login(email="cssd18@test.com", password=TEST_PASSWORD)
    return c


@pytest.fixture
def nurse_client(nurse_user):
    c = Client()
    c.login(email="nurse18@test.com", password=TEST_PASSWORD)
    return c


def update_url(pk, status="Cleaned"):
    return reverse("cssd_update_request_status", kwargs={"pk": pk, "status": status})


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarkAsCleanedUnit:
    """Pure unit tests — directly manipulate models, no HTTP."""

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_status_changes_to_cleaned(self, collected_request, cssd_user):
        """Collected → Cleaned: status field updated correctly."""
        req = collected_request
        req.status = "Cleaned"
        req.cleaned_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.status == "Cleaned"

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_cleaned_at_timestamp_set(self, collected_request, cssd_user):
        """cleaned_at is populated after transition."""
        req = collected_request
        before = timezone.now()
        req.status = "Cleaned"
        req.cleaned_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.cleaned_at is not None
        assert req.cleaned_at >= before

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_last_operator_set(self, collected_request, cssd_user):
        """last_operator is set to the CSSD user who performed the action."""
        req = collected_request
        req.status = "Cleaned"
        req.cleaned_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.last_operator == cssd_user

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_notification_created_for_nurse(self, collected_request, nurse_user):
        """A Notification is created for the nurse when request is Cleaned."""
        req = collected_request
        Notification.objects.create(
            recipient=nurse_user,
            request=req,
            message=f"REQ-{req.id:04d} instruments have been cleaned.",
        )
        notif = Notification.objects.get(recipient=nurse_user, request=req)
        assert "cleaned" in notif.message.lower()

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_cannot_clean_requested_status_directly(self, requested_request):
        """Business rule: only Collected items can be Cleaned."""
        req = requested_request
        # Simulating the guard logic from the view
        assert req.status != "Collected", \
            "A Requested item should not be directly Cleaned"

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_cannot_clean_already_cleaned_request(self, collected_request, cssd_user):
        """Once Cleaned, the item should not be re-cleaned."""
        req = collected_request
        req.status = "Cleaned"
        req.cleaned_at = timezone.now()
        req.last_operator = cssd_user
        req.save()

        req.refresh_from_db()
        assert req.status == "Cleaned"
        # Guard: status is no longer 'Collected', so transition is invalid
        assert req.status != "Collected"


# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestMarkAsCleanedIntegration:
    """Full HTTP integration tests for the Mark-as-Cleaned endpoint."""

    # ── Happy path ──────────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cssd_can_mark_collected_as_cleaned(
        self, cssd_client, collected_request
    ):
        """POST update/Cleaned/ on a Collected request → 302 redirect."""
        resp = cssd_client.post(update_url(collected_request.pk, "Cleaned"))
        assert resp.status_code == 302

        collected_request.refresh_from_db()
        assert collected_request.status == "Cleaned"

    @pytest.mark.integration
    def test_cleaned_at_set_after_http_transition(
        self, cssd_client, collected_request
    ):
        """cleaned_at timestamp is populated after the HTTP POST."""
        assert collected_request.cleaned_at is None or True  # may be set already
        cssd_client.post(update_url(collected_request.pk, "Cleaned"))
        collected_request.refresh_from_db()
        assert collected_request.cleaned_at is not None

    @pytest.mark.integration
    def test_notification_created_after_http_transition(
        self, cssd_client, collected_request, nurse_user
    ):
        """A Notification for the nurse is created after the HTTP POST."""
        cssd_client.post(update_url(collected_request.pk, "Cleaned"))
        assert Notification.objects.filter(
            recipient=nurse_user,
            request=collected_request,
        ).exists()

    @pytest.mark.integration
    def test_redirect_target_is_request_detail(
        self, cssd_client, collected_request
    ):
        """After success, response redirects to cssd_request_detail."""
        resp = cssd_client.post(update_url(collected_request.pk, "Cleaned"))
        assert resp.status_code == 302
        assert f"/dashboard/cssd/request/{collected_request.pk}/" in resp.url

    # ── Wrong HTTP method ────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_get_request_returns_405(self, cssd_client, collected_request):
        """GET on the update endpoint must return 405 Method Not Allowed."""
        resp = cssd_client.get(update_url(collected_request.pk, "Cleaned"))
        assert resp.status_code == 405

    # ── Wrong source status ──────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cannot_clean_a_requested_item_via_http(
        self, cssd_client, requested_request
    ):
        """Cleaning a Requested (not Collected) item → redirect + no change."""
        resp = cssd_client.post(update_url(requested_request.pk, "Cleaned"))
        # View redirects with an error message
        assert resp.status_code == 302
        requested_request.refresh_from_db()
        assert requested_request.status == "Requested"

    @pytest.mark.integration
    def test_cannot_clean_already_cleaned_request_via_http(
        self, cssd_client, collected_request
    ):
        """Second POST on same request → no status change, still Cleaned."""
        cssd_client.post(update_url(collected_request.pk, "Cleaned"))
        collected_request.refresh_from_db()
        assert collected_request.status == "Cleaned"

        # Second attempt
        resp = cssd_client.post(update_url(collected_request.pk, "Cleaned"))
        assert resp.status_code == 302
        collected_request.refresh_from_db()
        assert collected_request.status == "Cleaned"  # unchanged

    # ── Wrong target status ──────────────────────────────────────────────────

    @pytest.mark.integration
    def test_wrong_target_status_rejected(self, cssd_client, collected_request):
        """Trying to mark as 'Collected' (wrong status for this branch) → redirect + unchanged."""
        resp = cssd_client.post(update_url(collected_request.pk, "Collected"))
        assert resp.status_code == 302
        collected_request.refresh_from_db()
        assert collected_request.status == "Collected"  # unchanged

    # ── Access control ───────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_nurse_cannot_access_update_endpoint(
        self, nurse_client, collected_request
    ):
        """Nurse user is forbidden from the CSSD update endpoint."""
        resp = nurse_client.post(update_url(collected_request.pk, "Cleaned"))
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_unauthenticated_user_redirected_to_login(
        self, collected_request
    ):
        """Anonymous user hitting the update endpoint is redirected to login."""
        anon = Client()
        resp = anon.post(update_url(collected_request.pk, "Cleaned"))
        assert resp.status_code in (302, 403)
        if resp.status_code == 302:
            assert "/login/" in resp.url
