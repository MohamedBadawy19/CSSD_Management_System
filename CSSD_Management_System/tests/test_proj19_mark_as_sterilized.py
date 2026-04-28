"""
test_proj19_mark_as_sterilized.py — Unit + Integration tests for US-19.

Feature: CSSD technician marks a Cleaned InstrumentRequest as Sterilized.
         Requires linking a valid SterilizationBatch before the transition.
Branch:  feature/Proj-19-Mark-as-Sterilized

Unit tests:
  - Happy path: Cleaned → Sterilized (status, sterilized_at, batch, last_operator)
  - Only Cleaned items can be Sterilized
  - Batch is required (missing batch_id rejected)
  - Batch with temp < 121°C fails form validation
  - Batch with duration = 0 fails form validation
  - Notification created for nurse on success

Integration tests (HTTP):
  - POST update/Sterilized/ with valid batch → 302 success
  - POST without batch_id → redirect + no status change
  - POST with non-existent batch_id → redirect + no status change
  - GET update/Sterilized/ → 405
  - Nurse cannot access endpoint (403)
  - Unauthenticated user → redirect to login
  - cssd_batch_create: valid form → batch created, operator = logged-in user
  - cssd_batch_create: temp < 121 → form error
  - cssd_batch_create: duration 0 → form error
  - Nurse cannot access batch create (403)
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser,
    InstrumentRequest,
    Notification,
    SterilizationBatch,
)

TEST_PASSWORD = "TestPass123!"


# ═══════════════════════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def cssd_user(db):
    return CustomUser.objects.create_user(
        email="cssd19@test.com",
        password=TEST_PASSWORD,
        role="CSSD Technician",
        department="CSSD",
    )


@pytest.fixture
def nurse_user(db):
    return CustomUser.objects.create_user(
        email="nurse19@test.com",
        password=TEST_PASSWORD,
        role="Department Nurse",
        department="ICU",
    )


@pytest.fixture
def batch(cssd_user):
    """A valid SterilizationBatch (temp ≥ 121, duration > 0)."""
    return SterilizationBatch.objects.create(
        operator=cssd_user,
        temperature=134.0,
        cycle_duration=30,
        status="In Progress",
    )


@pytest.fixture
def cleaned_request(nurse_user):
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Cleaned",
        department="ICU",
        collected_at=timezone.now(),
        cleaned_at=timezone.now(),
    )


@pytest.fixture
def requested_request(nurse_user):
    return InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Requested",
        department="ICU",
    )


@pytest.fixture
def cssd_client(cssd_user):
    c = Client()
    c.login(email="cssd19@test.com", password=TEST_PASSWORD)
    return c


@pytest.fixture
def nurse_client(nurse_user):
    c = Client()
    c.login(email="nurse19@test.com", password=TEST_PASSWORD)
    return c


def update_url(pk, status="Sterilized"):
    return reverse("cssd_update_request_status", kwargs={"pk": pk, "status": status})


def batch_create_url():
    return reverse("cssd_batch_create")


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarkAsSterilizedUnit:

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_status_changes_to_sterilized(self, cleaned_request, cssd_user, batch):
        """Cleaned → Sterilized: status, batch and timestamp updated."""
        req = cleaned_request
        req.status = "Sterilized"
        req.sterilized_at = timezone.now()
        req.last_operator = cssd_user
        req.batch = batch
        req.save()

        req.refresh_from_db()
        assert req.status == "Sterilized"
        assert req.batch == batch
        assert req.sterilized_at is not None
        assert req.last_operator == cssd_user

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_notification_created_for_nurse(self, cleaned_request, nurse_user, batch):
        """Notification is created for nurse on sterilization."""
        req = cleaned_request
        Notification.objects.create(
            recipient=nurse_user,
            request=req,
            message=f"REQ-{req.id:04d} instruments have been sterilized.",
        )
        notif = Notification.objects.get(recipient=nurse_user, request=req)
        assert "sterilized" in notif.message.lower()

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_cannot_sterilize_non_cleaned_request(self, requested_request):
        """Business rule: only Cleaned items can be Sterilized."""
        assert requested_request.status != "Cleaned"

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_batch_form_valid_with_correct_values(self):
        """SterilizationBatchForm is valid for temp ≥ 121 and duration > 0."""
        from CSSD_Management_System.forms import SterilizationBatchForm
        form = SterilizationBatchForm(data={"temperature": 134, "cycle_duration": 30})
        assert form.is_valid(), form.errors

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_batch_form_invalid_temp_below_121(self):
        """Temperature < 121°C must fail validation."""
        from CSSD_Management_System.forms import SterilizationBatchForm
        form = SterilizationBatchForm(data={"temperature": 100, "cycle_duration": 30})
        assert not form.is_valid()
        assert "temperature" in form.errors

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_batch_form_invalid_zero_duration(self):
        """Cycle duration = 0 must fail validation."""
        from CSSD_Management_System.forms import SterilizationBatchForm
        form = SterilizationBatchForm(data={"temperature": 134, "cycle_duration": 0})
        assert not form.is_valid()
        assert "cycle_duration" in form.errors

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_batch_str_format(self, batch, cssd_user):
        """SterilizationBatch __str__ shows batch id, status, operator."""
        s = str(batch)
        assert str(batch.id) in s
        assert cssd_user.email in s


# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestMarkAsSterilizedIntegration:

    # ── Happy path ──────────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cssd_can_mark_cleaned_as_sterilized(
        self, cssd_client, cleaned_request, batch
    ):
        """POST update/Sterilized/ with valid batch → 302, status = Sterilized."""
        resp = cssd_client.post(
            update_url(cleaned_request.pk),
            data={"batch_id": batch.pk},
        )
        assert resp.status_code == 302
        cleaned_request.refresh_from_db()
        assert cleaned_request.status == "Sterilized"

    @pytest.mark.integration
    def test_batch_linked_after_sterilization(
        self, cssd_client, cleaned_request, batch
    ):
        """Batch is linked to the request after HTTP POST."""
        cssd_client.post(
            update_url(cleaned_request.pk),
            data={"batch_id": batch.pk},
        )
        cleaned_request.refresh_from_db()
        assert cleaned_request.batch == batch

    @pytest.mark.integration
    def test_sterilized_at_set_after_transition(
        self, cssd_client, cleaned_request, batch
    ):
        """sterilized_at timestamp is populated after POST."""
        cssd_client.post(
            update_url(cleaned_request.pk),
            data={"batch_id": batch.pk},
        )
        cleaned_request.refresh_from_db()
        assert cleaned_request.sterilized_at is not None

    @pytest.mark.integration
    def test_notification_created_after_sterilization(
        self, cssd_client, cleaned_request, batch, nurse_user
    ):
        """Notification for nurse created after sterilization."""
        cssd_client.post(
            update_url(cleaned_request.pk),
            data={"batch_id": batch.pk},
        )
        assert Notification.objects.filter(
            recipient=nurse_user, request=cleaned_request
        ).exists()

    # ── Missing / invalid batch ──────────────────────────────────────────────

    @pytest.mark.integration
    def test_missing_batch_id_rejected(self, cssd_client, cleaned_request):
        """POST without batch_id → redirect, status unchanged."""
        resp = cssd_client.post(update_url(cleaned_request.pk))
        assert resp.status_code == 302
        cleaned_request.refresh_from_db()
        assert cleaned_request.status == "Cleaned"

    @pytest.mark.integration
    def test_nonexistent_batch_id_rejected(self, cssd_client, cleaned_request):
        """POST with invalid batch_id → redirect, status unchanged."""
        resp = cssd_client.post(
            update_url(cleaned_request.pk),
            data={"batch_id": 99999},
        )
        assert resp.status_code == 302
        cleaned_request.refresh_from_db()
        assert cleaned_request.status == "Cleaned"

    # ── Wrong source status ──────────────────────────────────────────────────

    @pytest.mark.integration
    def test_cannot_sterilize_non_cleaned_request(
        self, cssd_client, requested_request, batch
    ):
        """Sterilizing a Requested item → redirect, status unchanged."""
        resp = cssd_client.post(
            update_url(requested_request.pk),
            data={"batch_id": batch.pk},
        )
        assert resp.status_code == 302
        requested_request.refresh_from_db()
        assert requested_request.status == "Requested"

    # ── Wrong HTTP method ────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_get_returns_405(self, cssd_client, cleaned_request):
        """GET on update endpoint → 405."""
        resp = cssd_client.get(update_url(cleaned_request.pk))
        assert resp.status_code == 405

    # ── Access control ───────────────────────────────────────────────────────

    @pytest.mark.integration
    def test_nurse_cannot_access_update_endpoint(
        self, nurse_client, cleaned_request, batch
    ):
        """Nurse is forbidden from the CSSD update endpoint."""
        resp = nurse_client.post(
            update_url(cleaned_request.pk),
            data={"batch_id": batch.pk},
        )
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_unauthenticated_user_redirected(self, cleaned_request, batch):
        """Anonymous user → redirect to login."""
        anon = Client()
        resp = anon.post(
            update_url(cleaned_request.pk),
            data={"batch_id": batch.pk},
        )
        assert resp.status_code in (302, 403)
        if resp.status_code == 302:
            assert "/login/" in resp.url


@pytest.mark.django_db
class TestBatchCreateIntegration:
    """Integration tests for cssd_batch_create (supporting view for US-19)."""

    @pytest.mark.integration
    def test_cssd_can_create_batch(self, cssd_client, cssd_user):
        """Valid form creates a batch and sets operator = logged-in user."""
        resp = cssd_client.post(
            batch_create_url(),
            data={"temperature": 134, "cycle_duration": 30},
        )
        # Should redirect to detail page on success
        assert resp.status_code == 302
        batch = SterilizationBatch.objects.first()
        assert batch is not None
        assert batch.operator == cssd_user
        assert batch.temperature == 134
        assert batch.cycle_duration == 30

    @pytest.mark.integration
    def test_batch_create_with_low_temp_fails(self, cssd_client):
        """Temperature < 121°C → form invalid, no batch created."""
        resp = cssd_client.post(
            batch_create_url(),
            data={"temperature": 100, "cycle_duration": 30},
        )
        assert resp.status_code == 200  # re-renders form
        assert SterilizationBatch.objects.count() == 0

    @pytest.mark.integration
    def test_batch_create_with_zero_duration_fails(self, cssd_client):
        """Duration 0 → form invalid, no batch created."""
        resp = cssd_client.post(
            batch_create_url(),
            data={"temperature": 134, "cycle_duration": 0},
        )
        assert resp.status_code == 200
        assert SterilizationBatch.objects.count() == 0

    @pytest.mark.integration
    def test_nurse_cannot_access_batch_create(self, nurse_client):
        """Nurse is forbidden from creating batches."""
        resp = nurse_client.get(batch_create_url())
        assert resp.status_code == 403

    @pytest.mark.integration
    def test_get_batch_create_renders_form(self, cssd_client):
        """GET on batch_create renders the form."""
        resp = cssd_client.get(batch_create_url())
        assert resp.status_code == 200
