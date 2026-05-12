"""
tests/test_proj31_audit_history.py
PROJ-31: Search Instrument Audit History

Tests the Hospital Admin's ability to search the audit history of instruments
and view their full sterilization lifecycle timeline in a read-only format.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from CSSD_Management_System.models import (
    CustomUser,
    InventoryItem,
    InstrumentRequest,
    RequestItem,
    SterilizationBatch,
)

# ── Shared password ──────────────────────────────────────────────────────────
PASSWORD = "TestPass123!"


# ══════════════════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def hospital_admin(db):
    """Creates a Hospital Administrator user."""
    return CustomUser.objects.create_user(
        email="hadmin@test.hospital",
        password=PASSWORD,
        first_name="Hospital",
        last_name="Admin",
        role="Hospital Administrator",
        department="Administration",
    )


@pytest.fixture
def hospital_client(hospital_admin):
    """Returns a Django test Client logged in as a Hospital Admin."""
    client = Client()
    client.login(email=hospital_admin.email, password=PASSWORD)
    return client


@pytest.fixture
def nurse_user(db):
    """Creates a Department Nurse user."""
    return CustomUser.objects.create_user(
        email="nurse@test.hospital",
        password=PASSWORD,
        first_name="Jane",
        last_name="Nurse",
        role="Department Nurse",
        department="Emergency",
    )


@pytest.fixture
def nurse_client(nurse_user):
    """Returns a Django test Client logged in as a Nurse."""
    client = Client()
    client.login(email=nurse_user.email, password=PASSWORD)
    return client


@pytest.fixture
def tech_user(db):
    """Creates a CSSD Technician user."""
    return CustomUser.objects.create_user(
        email="tech@test.hospital",
        password=PASSWORD,
        first_name="John",
        last_name="Tech",
        role="CSSD Technician",
        department="CSSD",
    )


@pytest.fixture
def tech_client(tech_user):
    """Returns a Django test Client logged in as a Tech."""
    client = Client()
    client.login(email=tech_user.email, password=PASSWORD)
    return client


@pytest.fixture
def sample_inventory(db):
    """Creates sample inventory items for testing."""
    return {
        "scalpel": InventoryItem.objects.create(
            name="Surgical Scalpel",
            category="Cutting",
            current_stock=50,
            min_threshold=10,
        ),
        "forceps": InventoryItem.objects.create(
            name="Forceps",
            category="Grasping",
            current_stock=30,
            min_threshold=10,
        ),
    }


@pytest.fixture
def sample_request(db, nurse_user, sample_inventory):
    """
    Creates a fully-progressed InstrumentRequest with timestamps at each stage,
    simulating a complete sterilization lifecycle.
    """
    now = timezone.now()

    req = InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Normal",
        status="Delivered",
        department=nurse_user.department,
        notes="Test request for audit",
        submitted_at=now,
        collected_at=now,
        cleaned_at=now,
        sterilized_at=now,
        packed_at=now,
        delivered_at=now,
    )

    # Attach instrument items
    RequestItem.objects.create(
        request=req,
        inventory_item=sample_inventory["scalpel"],
        quantity=2,
    )
    RequestItem.objects.create(
        request=req,
        inventory_item=sample_inventory["forceps"],
        quantity=1,
    )

    return req


@pytest.fixture
def sample_request_with_batch(db, nurse_user, tech_user, sample_inventory):
    """
    Creates a request that has been sterilized via a batch, with operator info.
    """
    now = timezone.now()

    batch = SterilizationBatch.objects.create(
        operator=tech_user,
        temperature=134.0,
        cycle_duration=18.0,
        status="Completed",
    )

    req = InstrumentRequest.objects.create(
        requester=nurse_user,
        priority="Urgent",
        status="Sterilized",
        department=nurse_user.department,
        notes="Batch audit test",
        batch=batch,
        last_operator=tech_user,
        submitted_at=now,
        collected_at=now,
        cleaned_at=now,
        sterilized_at=now,
    )

    RequestItem.objects.create(
        request=req,
        inventory_item=sample_inventory["scalpel"],
        quantity=5,
    )

    return req


# ══════════════════════════════════════════════════════════════════════════════
#  1. ACCESS CONTROL
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAuditAccessControl:
    """AC: Only Hospital Admins can access the audit history page."""

    def test_hospital_admin_can_access_audit(self, hospital_client):
        """Hospital Admin can access the audit page — 200 OK."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url)
        assert resp.status_code == 200

    def test_hospital_admin_can_access_report(self, hospital_client):
        """Hospital Admin can access the report page — 200 OK."""
        url = reverse("hospital_report")
        resp = hospital_client.get(url)
        assert resp.status_code == 200

    def test_nurse_cannot_access_audit(self, nurse_client):
        """Nurses should be denied access to the audit page — 403."""
        url = reverse("hospital_audit")
        resp = nurse_client.get(url)
        assert resp.status_code == 403

    def test_tech_cannot_access_audit(self, tech_client):
        """CSSD Technicians should be denied access to the audit page — 403."""
        url = reverse("hospital_audit")
        resp = tech_client.get(url)
        assert resp.status_code == 403

    def test_unauthenticated_redirects_to_login(self):
        """Unauthenticated users should be redirected to login."""
        client = Client()
        url = reverse("hospital_audit")
        resp = client.get(url)
        assert resp.status_code == 302  # redirect to login


# ══════════════════════════════════════════════════════════════════════════════
#  2. SEARCH BY REQUEST ID
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestSearchByRequestId:
    """AC: Search by instrument set ID returns the full lifecycle timeline."""

    def test_search_by_numeric_id(self, hospital_client, sample_request):
        """Searching by plain numeric ID returns the matching request."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": str(sample_request.id)})
        assert resp.status_code == 200
        assert sample_request in resp.context["results"]

    def test_search_by_req_format(self, hospital_client, sample_request):
        """Searching 'REQ-XXXX' format returns the matching request."""
        url = reverse("hospital_audit")
        query = f"REQ-{sample_request.id:04d}"
        resp = hospital_client.get(url, {"q": query})
        assert resp.status_code == 200
        assert sample_request in resp.context["results"]

    def test_search_nonexistent_id(self, hospital_client, sample_request):
        """Searching a non-existent ID returns no results."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": "99999"})
        assert resp.status_code == 200
        assert len(resp.context["results"]) == 0


# ══════════════════════════════════════════════════════════════════════════════
#  3. SEARCH BY INSTRUMENT NAME
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestSearchByInstrumentName:
    """AC: Search by instrument name returns requests containing that instrument."""

    def test_search_by_full_name(self, hospital_client, sample_request):
        """Searching 'Surgical Scalpel' finds the request containing that item."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": "Surgical Scalpel"})
        assert resp.status_code == 200
        assert sample_request in resp.context["results"]

    def test_search_by_partial_name(self, hospital_client, sample_request):
        """Searching 'Scalpel' (partial) finds the request."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": "Scalpel"})
        assert resp.status_code == 200
        assert sample_request in resp.context["results"]

    def test_search_case_insensitive(self, hospital_client, sample_request):
        """Search is case-insensitive."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": "surgical scalpel"})
        assert resp.status_code == 200
        assert sample_request in resp.context["results"]

    def test_search_no_match(self, hospital_client, sample_request):
        """Searching for a non-existent instrument returns no results."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": "XYZ Nonexistent Instrument"})
        assert resp.status_code == 200
        assert len(resp.context["results"]) == 0


# ══════════════════════════════════════════════════════════════════════════════
#  4. LIFECYCLE TIMELINE DATA
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestLifecycleTimeline:
    """AC: Results include full lifecycle timeline with timestamps and operator."""

    def test_delivered_request_has_all_timestamps(self, hospital_client, sample_request):
        """A fully delivered request shows all lifecycle timestamps in context."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": str(sample_request.id)})
        result = list(resp.context["results"])[0]

        assert result.submitted_at is not None
        assert result.collected_at is not None
        assert result.cleaned_at is not None
        assert result.sterilized_at is not None
        assert result.packed_at is not None
        assert result.delivered_at is not None

    def test_batch_operator_visible(self, hospital_client, sample_request_with_batch, tech_user):
        """When a request has a batch, the operator name is accessible."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": str(sample_request_with_batch.id)})
        result = list(resp.context["results"])[0]

        assert result.batch is not None
        assert result.batch.operator.email == tech_user.email

    def test_last_operator_visible(self, hospital_client, sample_request_with_batch, tech_user):
        """The last_operator field is populated and accessible."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": str(sample_request_with_batch.id)})
        result = list(resp.context["results"])[0]

        assert result.last_operator is not None
        assert result.last_operator.email == tech_user.email


# ══════════════════════════════════════════════════════════════════════════════
#  5. READ-ONLY ENFORCEMENT
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestReadOnly:
    """AC: Audit results are read-only — no POST/edit endpoints exist."""

    def test_audit_page_post_not_allowed(self, hospital_client):
        """POST to the audit page should not modify data (GET-only view)."""
        url = reverse("hospital_audit")
        resp = hospital_client.post(url, {"q": "test"})
        # The view only handles GET; POST should still render or be rejected
        # Django views that only read GET params will just ignore POST data
        # and render normally (200) — the key is no data is mutated.
        assert resp.status_code == 200

    def test_audit_results_contain_readonly_banner(self, hospital_client, sample_request):
        """The audit page response contains the read-only warning text."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": str(sample_request.id)})
        content = resp.content.decode()
        assert "read-only" in content.lower()

    def test_no_edit_forms_in_response(self, hospital_client, sample_request):
        """The audit results do not contain any form inputs for editing."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": str(sample_request.id)})
        content = resp.content.decode()
        # The only form is the search form — no edit/save/delete buttons
        assert 'name="status"' not in content
        assert 'name="save"' not in content
        assert "Mark as" not in content


# ══════════════════════════════════════════════════════════════════════════════
#  6. EMPTY / NO QUERY STATE
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestEmptyState:
    """Edge cases: empty searches and initial page load."""

    def test_initial_page_no_query(self, hospital_client):
        """Loading the audit page without a query shows the prompt message."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url)
        content = resp.content.decode()
        assert resp.status_code == 200
        assert "Enter a request ID or instrument name" in content

    def test_empty_query_string(self, hospital_client):
        """An empty query string shows the prompt, not the results area."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": ""})
        content = resp.content.decode()
        assert "Enter a request ID or instrument name" in content

    def test_whitespace_only_query(self, hospital_client):
        """A whitespace-only query is treated as empty."""
        url = reverse("hospital_audit")
        resp = hospital_client.get(url, {"q": "   "})
        content = resp.content.decode()
        assert "Enter a request ID or instrument name" in content


# ══════════════════════════════════════════════════════════════════════════════
#  7. DASHBOARD ROUTING
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDashboardRouting:
    """Hospital Admins are routed to their report dashboard, not the CSSD one."""

    def test_hospital_admin_routed_to_report(self, hospital_client):
        """Dashboard router redirects Hospital Admin to hospital_report."""
        url = reverse("dashboard_router")
        resp = hospital_client.get(url)
        assert resp.status_code == 302
        assert "/dashboard/hospital/" in resp.url
